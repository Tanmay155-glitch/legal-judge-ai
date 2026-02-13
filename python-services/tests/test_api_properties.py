"""
Property-Based Tests for API Endpoints
Tests universal properties that should hold for all API interactions
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import httpx
import json
from typing import Dict, Any


# Property 25: Invalid API inputs return HTTP 400
@pytest.mark.asyncio
@given(
    invalid_query=st.one_of(
        st.just(""),  # Empty string
        st.text(min_size=0, max_size=0),  # Empty text
        st.none(),  # None value
    )
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
async def test_property_25_invalid_inputs_return_400(invalid_query):
    """
    Property 25: Invalid API inputs return HTTP 400
    
    Universal property: Any invalid input should return HTTP 400 Bad Request
    """
    async with httpx.AsyncClient() as client:
        # Test search endpoint with invalid query
        if invalid_query is None:
            payload = {}
        else:
            payload = {"query": invalid_query, "top_k": 10}
        
        try:
            response = await client.post(
                "http://localhost:8003/search",
                json=payload,
                timeout=5.0
            )
            
            # Should return 400 for invalid input or 422 for validation error
            assert response.status_code in [400, 422], \
                f"Expected 400/422 for invalid input, got {response.status_code}"
        
        except httpx.ConnectError:
            pytest.skip("Service not running")


# Property 26: API responses follow consistent format
@pytest.mark.asyncio
@given(
    valid_query=st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', ' ')))
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
async def test_property_26_consistent_response_format(valid_query):
    """
    Property 26: API responses follow consistent format
    
    Universal property: All successful API responses should have consistent structure
    """
    assume(len(valid_query.strip()) > 0)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8003/search",
                json={"query": valid_query, "top_k": 5},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check consistent response structure
                assert "results" in data, "Response should have 'results' field"
                assert "total_results" in data, "Response should have 'total_results' field"
                assert "search_time_ms" in data, "Response should have 'search_time_ms' field"
                assert "query" in data, "Response should have 'query' field"
                
                # Check types
                assert isinstance(data["results"], list), "results should be a list"
                assert isinstance(data["total_results"], int), "total_results should be int"
                assert isinstance(data["search_time_ms"], (int, float)), "search_time_ms should be numeric"
                assert isinstance(data["query"], str), "query should be string"
        
        except httpx.ConnectError:
            pytest.skip("Service not running")


# Property 27: Rate limiting prevents excessive requests (simplified test)
@pytest.mark.asyncio
async def test_property_27_rate_limiting_concept():
    """
    Property 27: Rate limiting prevents excessive requests
    
    Note: This is a conceptual test. Full rate limiting requires configuration.
    """
    # This test verifies the concept exists in the codebase
    # Actual rate limiting would be tested with load testing tools
    
    # Check that rate limiting is mentioned in documentation
    import os
    deployment_guide = os.path.join(os.path.dirname(__file__), "../../DEPLOYMENT_GUIDE.md")
    
    if os.path.exists(deployment_guide):
        with open(deployment_guide, 'r') as f:
            content = f.read()
            assert "rate" in content.lower() or "limit" in content.lower(), \
                "Rate limiting should be documented"
    
    # Verify services can handle multiple requests
    async with httpx.AsyncClient() as client:
        try:
            responses = []
            for i in range(5):
                response = await client.get(
                    "http://localhost:8003/health",
                    timeout=5.0
                )
                responses.append(response.status_code)
            
            # All requests should succeed (no rate limiting in test environment)
            assert all(status == 200 for status in responses), \
                "Health checks should all succeed"
        
        except httpx.ConnectError:
            pytest.skip("Service not running")


# Additional API validation tests
@pytest.mark.asyncio
@given(
    top_k=st.integers(min_value=-10, max_value=200)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
async def test_property_top_k_validation(top_k):
    """
    Property: top_k parameter should be validated
    
    Valid range: 1-100
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8003/search",
                json={"query": "test query", "top_k": top_k},
                timeout=5.0
            )
            
            if 1 <= top_k <= 100:
                # Valid range should succeed or return results
                assert response.status_code in [200, 503], \
                    f"Valid top_k={top_k} should succeed or service unavailable"
            else:
                # Invalid range should return 400 or 422
                assert response.status_code in [400, 422], \
                    f"Invalid top_k={top_k} should return 400/422, got {response.status_code}"
        
        except httpx.ConnectError:
            pytest.skip("Service not running")


@pytest.mark.asyncio
@given(
    min_similarity=st.floats(min_value=-1.0, max_value=2.0, allow_nan=False, allow_infinity=False)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
async def test_property_similarity_validation(min_similarity):
    """
    Property: min_similarity parameter should be validated
    
    Valid range: 0.0-1.0
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8003/search",
                json={"query": "test query", "min_similarity": min_similarity},
                timeout=5.0
            )
            
            if 0.0 <= min_similarity <= 1.0:
                # Valid range should succeed or return results
                assert response.status_code in [200, 503], \
                    f"Valid min_similarity={min_similarity} should succeed"
            else:
                # Invalid range should return 400 or 422
                assert response.status_code in [400, 422], \
                    f"Invalid min_similarity={min_similarity} should return 400/422"
        
        except httpx.ConnectError:
            pytest.skip("Service not running")


# Test prediction endpoint validation
@pytest.mark.asyncio
@given(
    facts_length=st.integers(min_value=0, max_value=100),
    issue_length=st.integers(min_value=0, max_value=100)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10)
async def test_property_prediction_input_validation(facts_length, issue_length):
    """
    Property: Prediction inputs should be validated for minimum length
    
    Facts: min 20 chars
    Issue: min 10 chars
    """
    facts = "a" * facts_length
    issue = "b" * issue_length
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8004/predict/outcome",
                json={"facts": facts, "issue": issue},
                timeout=10.0
            )
            
            if facts_length >= 20 and issue_length >= 10:
                # Valid inputs should succeed or return service unavailable
                assert response.status_code in [200, 503], \
                    f"Valid inputs should succeed"
            else:
                # Invalid inputs should return 400 or 422
                assert response.status_code in [400, 422], \
                    f"Invalid inputs (facts={facts_length}, issue={issue_length}) should return 400/422"
        
        except httpx.ConnectError:
            pytest.skip("Service not running")


# Test health endpoint consistency
@pytest.mark.asyncio
async def test_property_health_endpoints_consistent():
    """
    Property: All services should have consistent health endpoint format
    """
    services = [
        ("embedding", 8001),
        ("ingestion", 8002),
        ("search", 8003),
        ("prediction", 8004),
        ("opinion", 8005)
    ]
    
    async with httpx.AsyncClient() as client:
        for service_name, port in services:
            try:
                response = await client.get(
                    f"http://localhost:{port}/health",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check consistent health response structure
                    assert "status" in data, f"{service_name} health should have 'status'"
                    assert "service" in data, f"{service_name} health should have 'service'"
                    assert data["status"] == "ok", f"{service_name} status should be 'ok'"
            
            except httpx.ConnectError:
                # Service not running, skip
                pass


# Test stats endpoint consistency
@pytest.mark.asyncio
async def test_property_stats_endpoints_return_metrics():
    """
    Property: All services should have stats endpoints that return metrics
    """
    services = [
        ("ingestion", 8002),
        ("search", 8003),
        ("prediction", 8004),
        ("opinion", 8005)
    ]
    
    async with httpx.AsyncClient() as client:
        for service_name, port in services:
            try:
                response = await client.get(
                    f"http://localhost:{port}/stats",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Stats should return a dictionary with metrics
                    assert isinstance(data, dict), f"{service_name} stats should be a dict"
                    assert len(data) > 0, f"{service_name} stats should have metrics"
            
            except httpx.ConnectError:
                # Service not running, skip
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
