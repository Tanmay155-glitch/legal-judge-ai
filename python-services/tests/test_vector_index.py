"""
Unit tests for Vector Index Service.
Tests Qdrant integration, vector storage, and similarity search.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from qdrant_client.http import models


class TestVectorIndexService:
    """Tests for VectorIndexService class"""
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant client"""
        client = Mock()
        client.get_collections = Mock(return_value=Mock(collections=[]))
        client.create_collection = Mock()
        client.upsert = Mock()
        client.search = Mock(return_value=[])
        client.delete = Mock()
        client.get_collection = Mock(return_value=Mock(
            vectors_count=100,
            points_count=100,
            status="green"
        ))
        client.scroll = Mock(return_value=([], None))
        return client
    
    @pytest.fixture
    def vector_index_service(self, mock_qdrant_client):
        """Create VectorIndexService with mocked client"""
        with patch('vector_index.service.QdrantClient', return_value=mock_qdrant_client):
            from vector_index.service import VectorIndexService
            service = VectorIndexService(
                qdrant_url="http://localhost:6333",
                collection_name="test_collection"
            )
            return service
    
    def test_initialization(self, vector_index_service):
        """Test service initializes correctly"""
        assert vector_index_service is not None
        assert vector_index_service.collection_name == "test_collection"
        assert vector_index_service.vector_size == 768
        assert vector_index_service.distance == "Cosine"
    
    def test_create_collection_new(self, vector_index_service, mock_qdrant_client):
        """Test creating a new collection"""
        mock_qdrant_client.get_collections.return_value = Mock(collections=[])
        
        result = vector_index_service.create_collection()
        
        assert result is True
        mock_qdrant_client.create_collection.assert_called_once()
    
    def test_create_collection_exists(self, vector_index_service, mock_qdrant_client):
        """Test creating collection when it already exists"""
        existing_collection = Mock()
        existing_collection.name = "test_collection"
        mock_qdrant_client.get_collections.return_value = Mock(
            collections=[existing_collection]
        )
        
        result = vector_index_service.create_collection()
        
        assert result is False
        mock_qdrant_client.create_collection.assert_not_called()
    
    def test_create_collection_recreate(self, vector_index_service, mock_qdrant_client):
        """Test recreating an existing collection"""
        existing_collection = Mock()
        existing_collection.name = "test_collection"
        mock_qdrant_client.get_collections.return_value = Mock(
            collections=[existing_collection]
        )
        
        result = vector_index_service.create_collection(recreate=True)
        
        assert result is True
        mock_qdrant_client.delete_collection.assert_called_once_with("test_collection")
        mock_qdrant_client.create_collection.assert_called_once()
    
    def test_index_document_valid(self, vector_index_service, mock_qdrant_client, sample_vector):
        """Test indexing a document with multiple vectors"""
        vectors = {
            "facts": np.array(sample_vector),
            "issue": np.array(sample_vector),
            "reasoning": np.array(sample_vector)
        }
        metadata = {
            "case_name": "Doe v. Smith",
            "year": 2023,
            "court": "Supreme Court"
        }
        
        vector_ids = vector_index_service.index_document(
            doc_id="test-doc-1",
            vectors=vectors,
            metadata=metadata
        )
        
        assert len(vector_ids) == 3
        assert "test-doc-1_facts" in vector_ids
        assert "test-doc-1_issue" in vector_ids
        assert "test-doc-1_reasoning" in vector_ids
        mock_qdrant_client.upsert.assert_called_once()
    
    def test_index_document_empty_vectors(self, vector_index_service):
        """Test that empty vectors dict raises ValueError"""
        with pytest.raises(ValueError, match="Vectors dictionary cannot be empty"):
            vector_index_service.index_document(
                doc_id="test-doc",
                vectors={},
                metadata={}
            )
    
    def test_index_document_wrong_dimension(self, vector_index_service):
        """Test that wrong vector dimension raises ValueError"""
        vectors = {
            "facts": np.random.randn(100)  # Wrong dimension
        }
        
        with pytest.raises(ValueError, match="Vector dimension mismatch"):
            vector_index_service.index_document(
                doc_id="test-doc",
                vectors=vectors,
                metadata={}
            )
    
    def test_index_document_with_none_vector(self, vector_index_service, mock_qdrant_client, sample_vector):
        """Test indexing with some None vectors"""
        vectors = {
            "facts": np.array(sample_vector),
            "issue": None,  # None vector
            "reasoning": np.array(sample_vector)
        }
        metadata = {"case_name": "Test"}
        
        vector_ids = vector_index_service.index_document(
            doc_id="test-doc",
            vectors=vectors,
            metadata=metadata
        )
        
        # Should only index non-None vectors
        assert len(vector_ids) == 2
        assert "test-doc_facts" in vector_ids
        assert "test-doc_reasoning" in vector_ids
        assert "test-doc_issue" not in vector_ids
    
    def test_search_similar_valid(self, vector_index_service, mock_qdrant_client, sample_vector):
        """Test similarity search"""
        # Mock search results
        mock_hit = Mock()
        mock_hit.id = "doc1_facts"
        mock_hit.score = 0.95
        mock_hit.payload = {
            "case_name": "Doe v. Smith",
            "year": 2023,
            "section_type": "facts"
        }
        mock_qdrant_client.search.return_value = [mock_hit]
        
        results = vector_index_service.search_similar(
            query_vector=np.array(sample_vector),
            top_k=10
        )
        
        assert len(results) == 1
        assert results[0]["id"] == "doc1_facts"
        assert results[0]["score"] == 0.95
        assert results[0]["payload"]["case_name"] == "Doe v. Smith"
        mock_qdrant_client.search.assert_called_once()
    
    def test_search_similar_with_filters(self, vector_index_service, mock_qdrant_client, sample_vector):
        """Test similarity search with metadata filters"""
        mock_qdrant_client.search.return_value = []
        
        filters = {
            "section_type": "reasoning",
            "year": 2023
        }
        
        results = vector_index_service.search_similar(
            query_vector=np.array(sample_vector),
            top_k=10,
            filters=filters
        )
        
        assert results == []
        # Verify filters were passed
        call_kwargs = mock_qdrant_client.search.call_args[1]
        assert call_kwargs['query_filter'] is not None
    
    def test_search_similar_wrong_dimension(self, vector_index_service):
        """Test that wrong query vector dimension raises ValueError"""
        wrong_vector = np.random.randn(100)  # Wrong dimension
        
        with pytest.raises(ValueError, match="Query vector dimension mismatch"):
            vector_index_service.search_similar(
                query_vector=wrong_vector,
                top_k=10
            )
    
    def test_search_similar_with_score_threshold(self, vector_index_service, mock_qdrant_client, sample_vector):
        """Test similarity search with score threshold"""
        mock_qdrant_client.search.return_value = []
        
        results = vector_index_service.search_similar(
            query_vector=np.array(sample_vector),
            top_k=10,
            score_threshold=0.8
        )
        
        # Verify score_threshold was passed
        call_kwargs = mock_qdrant_client.search.call_args[1]
        assert call_kwargs['score_threshold'] == 0.8
    
    def test_delete_document(self, vector_index_service, mock_qdrant_client):
        """Test deleting a document"""
        mock_qdrant_client.delete.return_value = 3  # 3 vectors deleted
        
        result = vector_index_service.delete_document("test-doc-1")
        
        assert result == 3
        mock_qdrant_client.delete.assert_called_once()
    
    def test_get_collection_info(self, vector_index_service, mock_qdrant_client):
        """Test getting collection information"""
        info = vector_index_service.get_collection_info()
        
        assert info["name"] == "test_collection"
        assert info["vectors_count"] == 100
        assert info["points_count"] == 100
        assert info["status"] == "green"
        assert info["vector_size"] == 768
        mock_qdrant_client.get_collection.assert_called_once()
    
    def test_check_duplicate_found(self, vector_index_service, mock_qdrant_client):
        """Test checking for duplicate when one exists"""
        mock_point = Mock()
        mock_point.payload = {"document_id": "existing-doc-123"}
        mock_qdrant_client.scroll.return_value = ([mock_point], None)
        
        doc_id = vector_index_service.check_duplicate("Doe v. Smith", 2023)
        
        assert doc_id == "existing-doc-123"
        mock_qdrant_client.scroll.assert_called_once()
    
    def test_check_duplicate_not_found(self, vector_index_service, mock_qdrant_client):
        """Test checking for duplicate when none exists"""
        mock_qdrant_client.scroll.return_value = ([], None)
        
        doc_id = vector_index_service.check_duplicate("New Case v. Someone", 2023)
        
        assert doc_id is None
        mock_qdrant_client.scroll.assert_called_once()


class TestVectorIndexServiceSingleton:
    """Tests for singleton pattern"""
    
    def test_get_vector_index_service_singleton(self):
        """Test that get_vector_index_service returns singleton"""
        with patch('vector_index.service.QdrantClient'):
            from vector_index.service import get_vector_index_service
            
            # Reset singleton
            import vector_index.service
            vector_index.service._vector_index_service_instance = None
            
            service1 = get_vector_index_service()
            service2 = get_vector_index_service()
            
            assert service1 is service2


class TestVectorIndexIntegration:
    """Integration tests (require running Qdrant instance)"""
    
    @pytest.mark.integration
    def test_full_workflow(self):
        """Test complete workflow: create, index, search, delete"""
        # This test requires a running Qdrant instance
        # Skip if Qdrant is not available
        pytest.skip("Integration test - requires running Qdrant")
    
    @pytest.mark.integration
    def test_duplicate_prevention(self):
        """Test that duplicate documents are prevented"""
        pytest.skip("Integration test - requires running Qdrant")


# Property-based tests (Task 4.2 - optional)
# These would use Hypothesis library for property testing
# Example structure:

# from hypothesis import given, strategies as st
# 
# @given(st.lists(st.floats(min_value=-1, max_value=1), min_size=768, max_size=768))
# def test_vector_storage_round_trip(vector):
#     """Property: Stored vectors should be retrievable with minimal loss"""
#     service = get_vector_index_service()
#     vector_array = np.array(vector)
#     
#     # Store vector
#     service.index_document("test", {"section": vector_array}, {})
#     
#     # Retrieve vector
#     results = service.search_similar(vector_array, top_k=1)
#     
#     # Should find the same vector with high similarity
#     assert len(results) > 0
#     assert results[0]["score"] > 0.99
