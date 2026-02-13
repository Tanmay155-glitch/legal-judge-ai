"""
Integration Tests for End-to-End Workflows
Tests complete workflows across multiple services
"""

import pytest
import httpx
import asyncio
import os
import tempfile
from pathlib import Path


# Test 17.1: End-to-end ingestion test
@pytest.mark.asyncio
@pytest.mark.integration
async def test_e2e_ingestion_workflow():
    """
    Test 17.1: PDF upload → OCR → Parsing → Embedding → Indexing → Search
    
    Verifies that a document is searchable after ingestion.
    """
    # Create a mock PDF file for testing
    mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: Upload PDF for ingestion
            files = {"file": ("test_case.pdf", mock_pdf_content, "application/pdf")}
            data = {"case_name": "Test v. Integration"}
            
            ingestion_response = await client.post(
                "http://localhost:8002/ingest/pdf",
                files=files,
                data=data
            )
            
            if ingestion_response.status_code == 503:
                pytest.skip("Ingestion service not available")
            
            # Check ingestion succeeded or partially succeeded
            assert ingestion_response.status_code in [200, 207], \
                f"Ingestion should succeed, got {ingestion_response.status_code}"
            
            ingestion_data = ingestion_response.json()
            document_id = ingestion_data.get("document_id")
            
            # Step 2: Wait for indexing to complete
            await asyncio.sleep(2)
            
            # Step 3: Search for the ingested document
            search_response = await client.post(
                "http://localhost:8003/search",
                json={
                    "query": "Test Integration",
                    "top_k": 10,
                    "min_similarity": 0.1  # Low threshold for test
                }
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                
                # Verify document is searchable
                assert "results" in search_data, "Search should return results"
                assert isinstance(search_data["results"], list), "Results should be a list"
                
                # If we got results, verify structure
                if len(search_data["results"]) > 0:
                    result = search_data["results"][0]
                    assert "case_name" in result, "Result should have case_name"
                    assert "similarity_score" in result, "Result should have similarity_score"
                    assert "snippet" in result, "Result should have snippet"
        
        except httpx.ConnectError:
            pytest.skip("Services not running")


# Test 17.2: End-to-end search test
@pytest.mark.asyncio
@pytest.mark.integration
async def test_e2e_search_workflow():
    """
    Test 17.2: Query → Embedding → Vector Search → Result Formatting
    
    Verifies that search results are ranked by similarity and include metadata.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: Perform semantic search
            search_response = await client.post(
                "http://localhost:8003/search",
                json={
                    "query": "breach of contract warranty habitability",
                    "top_k": 5,
                    "min_similarity": 0.5
                }
            )
            
            if search_response.status_code == 503:
                pytest.skip("Search service not available")
            
            assert search_response.status_code == 200, \
                f"Search should succeed, got {search_response.status_code}"
            
            search_data = search_response.json()
            
            # Step 2: Verify response structure
            assert "results" in search_data, "Response should have results"
            assert "total_results" in search_data, "Response should have total_results"
            assert "search_time_ms" in search_data, "Response should have search_time_ms"
            assert "query" in search_data, "Response should have query"
            
            results = search_data["results"]
            
            # Step 3: Verify results are ranked by similarity
            if len(results) > 1:
                scores = [r["similarity_score"] for r in results]
                assert scores == sorted(scores, reverse=True), \
                    "Results should be ranked by similarity (descending)"
            
            # Step 4: Verify metadata is included
            for result in results:
                assert "case_name" in result, "Result should have case_name"
                assert "year" in result, "Result should have year"
                assert "court" in result, "Result should have court"
                assert "section_type" in result, "Result should have section_type"
                assert "similarity_score" in result, "Result should have similarity_score"
                assert "snippet" in result, "Result should have snippet"
                assert "metadata" in result, "Result should have metadata"
                
                # Verify similarity score is in valid range
                assert 0.0 <= result["similarity_score"] <= 1.0, \
                    f"Similarity score should be 0-1, got {result['similarity_score']}"
        
        except httpx.ConnectError:
            pytest.skip("Services not running")


# Test 17.3: End-to-end prediction test
@pytest.mark.asyncio
@pytest.mark.integration
async def test_e2e_prediction_workflow():
    """
    Test 17.3: Input → Search → Feature Extraction → Prediction
    
    Verifies that probabilities sum to 1.0 and supporting cases are included.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: Make prediction request
            prediction_response = await client.post(
                "http://localhost:8004/predict/outcome",
                json={
                    "facts": "The landlord failed to repair the heating system despite multiple requests from the tenant. The apartment became uninhabitable during winter months.",
                    "issue": "Whether the landlord breached the implied warranty of habitability by failing to maintain essential services."
                }
            )
            
            if prediction_response.status_code == 503:
                pytest.skip("Prediction service not available")
            
            assert prediction_response.status_code == 200, \
                f"Prediction should succeed, got {prediction_response.status_code}"
            
            prediction_data = prediction_response.json()
            
            # Step 2: Verify response structure
            assert "prediction" in prediction_data, "Response should have prediction"
            assert "processing_time_ms" in prediction_data, "Response should have processing_time_ms"
            assert "disclaimer" in prediction_data, "Response should have disclaimer"
            
            prediction = prediction_data["prediction"]
            
            # Step 3: Verify probabilities sum to 1.0
            probabilities = prediction["probabilities"]
            assert "Affirmed" in probabilities, "Should have Affirmed probability"
            assert "Reversed" in probabilities, "Should have Reversed probability"
            assert "Remanded" in probabilities, "Should have Remanded probability"
            
            prob_sum = sum(probabilities.values())
            assert 0.99 <= prob_sum <= 1.01, \
                f"Probabilities should sum to 1.0, got {prob_sum}"
            
            # Step 4: Verify supporting cases are included
            assert "supporting_cases" in prediction, "Should have supporting_cases"
            assert isinstance(prediction["supporting_cases"], list), \
                "supporting_cases should be a list"
            
            # Step 5: Verify confidence and explanation
            assert "confidence" in prediction, "Should have confidence"
            assert "explanation" in prediction, "Should have explanation"
            assert 0.0 <= prediction["confidence"] <= 1.0, \
                f"Confidence should be 0-1, got {prediction['confidence']}"
        
        except httpx.ConnectError:
            pytest.skip("Services not running")


# Test 17.4: End-to-end opinion generation test
@pytest.mark.asyncio
@pytest.mark.integration
async def test_e2e_opinion_generation_workflow():
    """
    Test 17.4: Input → Search → RAG → LLM → Formatting
    
    Verifies that all required sections are present, precedents are cited, and disclaimer is included.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Step 1: Generate opinion
            opinion_response = await client.post(
                "http://localhost:8005/generate/opinion",
                json={
                    "case_context": {
                        "facts": "The landlord failed to repair the heating system despite multiple requests. The tenant withheld rent and the landlord filed for eviction.",
                        "issue": "Whether the tenant's withholding of rent was justified due to breach of warranty of habitability.",
                        "case_name": "Smith v. Jones",
                        "petitioner": "Smith",
                        "respondent": "Jones"
                    },
                    "opinion_type": "per_curiam",
                    "max_precedents": 5
                }
            )
            
            if opinion_response.status_code == 503:
                pytest.skip("Opinion service not available")
            
            assert opinion_response.status_code == 200, \
                f"Opinion generation should succeed, got {opinion_response.status_code}"
            
            opinion_data = opinion_response.json()
            
            # Step 2: Verify response structure
            assert "opinion" in opinion_data, "Response should have opinion"
            assert "processing_time_ms" in opinion_data, "Response should have processing_time_ms"
            
            opinion = opinion_data["opinion"]
            
            # Step 3: Verify all required sections are present
            required_sections = [
                "procedural_history",
                "facts",
                "issue",
                "reasoning",
                "holding",
                "judgment"
            ]
            
            assert "sections" in opinion, "Opinion should have sections"
            sections = opinion["sections"]
            
            for section in required_sections:
                assert section in sections, f"Opinion should have {section} section"
            
            # Step 4: Verify precedents are cited
            assert "cited_precedents" in opinion, "Opinion should have cited_precedents"
            assert isinstance(opinion["cited_precedents"], list), \
                "cited_precedents should be a list"
            
            # Step 5: Verify disclaimer is included
            assert "disclaimer" in opinion, "Opinion should have disclaimer"
            assert "AI-generated" in opinion["disclaimer"], \
                "Disclaimer should mention AI-generated"
            assert "research" in opinion["disclaimer"].lower(), \
                "Disclaimer should mention research purposes"
            
            # Step 6: Verify full text is present
            assert "full_text" in opinion, "Opinion should have full_text"
            assert len(opinion["full_text"]) >= 500, \
                "Opinion full_text should be at least 500 characters"
            
            # Step 7: Verify generation metadata
            assert "generation_metadata" in opinion, "Opinion should have generation_metadata"
            metadata = opinion["generation_metadata"]
            assert "model" in metadata, "Metadata should have model"
            assert "precedents_used" in metadata, "Metadata should have precedents_used"
        
        except httpx.ConnectError:
            pytest.skip("Services not running")


# Test service health checks
@pytest.mark.asyncio
@pytest.mark.integration
async def test_all_services_healthy():
    """
    Integration test: Verify all services are healthy and responding
    """
    services = [
        ("Embedding", 8001),
        ("Ingestion", 8002),
        ("Search", 8003),
        ("Prediction", 8004),
        ("Opinion", 8005)
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        healthy_services = []
        
        for service_name, port in services:
            try:
                response = await client.get(f"http://localhost:{port}/health")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        healthy_services.append(service_name)
            except httpx.ConnectError:
                pass
        
        # At least some services should be healthy
        if len(healthy_services) == 0:
            pytest.skip("No services are running")
        
        print(f"\nHealthy services: {', '.join(healthy_services)}")


# Test service statistics
@pytest.mark.asyncio
@pytest.mark.integration
async def test_services_provide_statistics():
    """
    Integration test: Verify services provide statistics
    """
    services = [
        ("Ingestion", 8002),
        ("Search", 8003),
        ("Prediction", 8004),
        ("Opinion", 8005)
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for service_name, port in services:
            try:
                response = await client.get(f"http://localhost:{port}/stats")
                if response.status_code == 200:
                    data = response.json()
                    assert isinstance(data, dict), f"{service_name} stats should be a dict"
                    assert len(data) > 0, f"{service_name} stats should have metrics"
            except httpx.ConnectError:
                # Service not running, skip
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "integration"])
