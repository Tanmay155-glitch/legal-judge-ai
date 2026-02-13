"""
Unit tests for Embedding Service.
Tests Legal-BERT embedding generation, batch processing, and edge cases.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Note: These tests will run when dependencies are installed
# For now, we'll structure them to be ready


class TestEmbeddingService:
    """Tests for EmbeddingService class"""
    
    @pytest.fixture
    def mock_model(self):
        """Mock SentenceTransformer model"""
        model = Mock()
        model.encode = Mock(return_value=np.random.randn(768))
        model.max_seq_length = 512
        return model
    
    @pytest.fixture
    def embedding_service(self, mock_model):
        """Create EmbeddingService with mocked model"""
        with patch('embedding_service.service.SentenceTransformer', return_value=mock_model):
            with patch('embedding_service.service.torch.cuda.is_available', return_value=False):
                from embedding_service.service import EmbeddingService
                service = EmbeddingService(model_name="test-model")
                return service
    
    def test_initialization(self, embedding_service):
        """Test service initializes correctly"""
        assert embedding_service is not None
        assert embedding_service.model_name == "test-model"
        assert embedding_service.embedding_dim == 768
        assert embedding_service.device in ["cpu", "cuda"]
    
    def test_encode_text_valid(self, embedding_service, mock_model):
        """Test encoding valid text"""
        mock_model.encode.return_value = np.random.randn(768)
        
        text = "The Court holds that the landlord breached the warranty."
        embedding = embedding_service.encode_text(text)
        
        assert embedding is not None
        assert len(embedding) == 768
        assert isinstance(embedding, np.ndarray)
        mock_model.encode.assert_called_once()
    
    def test_encode_text_empty_string(self, embedding_service):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedding_service.encode_text("")
    
    def test_encode_text_none(self, embedding_service):
        """Test that None raises ValueError"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedding_service.encode_text(None)
    
    def test_encode_text_whitespace_only(self, embedding_service):
        """Test that whitespace-only string raises ValueError"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedding_service.encode_text("   \n\t  ")
    
    def test_encode_batch_valid(self, embedding_service, mock_model):
        """Test encoding batch of texts"""
        texts = [
            "Text 1",
            "Text 2",
            "Text 3"
        ]
        mock_model.encode.return_value = np.random.randn(3, 768)
        
        embeddings = embedding_service.encode_batch(texts)
        
        assert embeddings is not None
        assert embeddings.shape == (3, 768)
        assert isinstance(embeddings, np.ndarray)
        mock_model.encode.assert_called_once()
    
    def test_encode_batch_empty_list(self, embedding_service):
        """Test that empty list raises ValueError"""
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            embedding_service.encode_batch([])
    
    def test_encode_batch_with_empty_texts(self, embedding_service, mock_model):
        """Test batch encoding filters out empty texts"""
        texts = [
            "Valid text 1",
            "",  # Empty
            "Valid text 2",
            "   ",  # Whitespace only
            "Valid text 3"
        ]
        # Mock should only be called with 3 valid texts
        mock_model.encode.return_value = np.random.randn(3, 768)
        
        embeddings = embedding_service.encode_batch(texts)
        
        # Should return array with NaN for invalid indices
        assert embeddings.shape == (5, 768)
        assert not np.isnan(embeddings[0]).any()  # Valid
        assert np.isnan(embeddings[1]).all()  # Empty
        assert not np.isnan(embeddings[2]).any()  # Valid
        assert np.isnan(embeddings[3]).all()  # Whitespace
        assert not np.isnan(embeddings[4]).any()  # Valid
    
    def test_encode_batch_custom_batch_size(self, embedding_service, mock_model):
        """Test batch encoding with custom batch size"""
        texts = ["Text"] * 10
        mock_model.encode.return_value = np.random.randn(10, 768)
        
        embeddings = embedding_service.encode_batch(texts, batch_size=5)
        
        assert embeddings.shape == (10, 768)
        # Verify batch_size was passed to model
        call_kwargs = mock_model.encode.call_args[1]
        assert call_kwargs['batch_size'] == 5
    
    def test_encode_sections_valid(self, embedding_service, mock_model):
        """Test encoding document sections"""
        sections = {
            "facts": "The plaintiff entered into a lease agreement.",
            "issue": "Whether the landlord breached the warranty.",
            "reasoning": "The Court has consistently held that residential leases contain an implied warranty."
        }
        mock_model.encode.return_value = np.random.randn(768)
        
        section_embeddings = embedding_service.encode_sections(sections)
        
        assert len(section_embeddings) == 3
        assert "facts" in section_embeddings
        assert "issue" in section_embeddings
        assert "reasoning" in section_embeddings
        assert all(emb is not None for emb in section_embeddings.values())
        assert mock_model.encode.call_count == 3
    
    def test_encode_sections_with_empty_section(self, embedding_service, mock_model):
        """Test encoding sections with some empty sections"""
        sections = {
            "facts": "Valid facts text",
            "issue": "",  # Empty
            "reasoning": "Valid reasoning text"
        }
        mock_model.encode.return_value = np.random.randn(768)
        
        section_embeddings = embedding_service.encode_sections(sections)
        
        assert len(section_embeddings) == 3
        assert section_embeddings["facts"] is not None
        assert section_embeddings["issue"] is None  # Should be None for empty
        assert section_embeddings["reasoning"] is not None
        assert mock_model.encode.call_count == 2  # Only called for valid sections
    
    def test_encode_sections_empty_dict(self, embedding_service):
        """Test that empty sections dict raises ValueError"""
        with pytest.raises(ValueError, match="Sections dictionary cannot be empty"):
            embedding_service.encode_sections({})
    
    def test_get_embedding_dimension(self, embedding_service):
        """Test getting embedding dimension"""
        dim = embedding_service.get_embedding_dimension()
        assert dim == 768
        assert isinstance(dim, int)
    
    def test_get_model_info(self, embedding_service):
        """Test getting model information"""
        info = embedding_service.get_model_info()
        
        assert "model_name" in info
        assert "embedding_dimension" in info
        assert "device" in info
        assert "batch_size" in info
        assert "max_seq_length" in info
        
        assert info["model_name"] == "test-model"
        assert info["embedding_dimension"] == 768
        assert info["max_seq_length"] == 512
    
    def test_long_text_handling(self, embedding_service, mock_model):
        """Test handling of very long text (>512 tokens)"""
        # Create a very long text
        long_text = "word " * 1000  # Much longer than 512 tokens
        mock_model.encode.return_value = np.random.randn(768)
        
        # Should not raise error, model will truncate
        embedding = embedding_service.encode_text(long_text)
        
        assert embedding is not None
        assert len(embedding) == 768
    
    def test_normalization_parameter(self, embedding_service, mock_model):
        """Test that normalization parameter is passed correctly"""
        text = "Test text"
        mock_model.encode.return_value = np.random.randn(768)
        
        # Test with normalization
        embedding_service.encode_text(text, normalize=True)
        call_kwargs = mock_model.encode.call_args[1]
        assert call_kwargs['normalize_embeddings'] is True
        
        # Test without normalization
        embedding_service.encode_text(text, normalize=False)
        call_kwargs = mock_model.encode.call_args[1]
        assert call_kwargs['normalize_embeddings'] is False


class TestEmbeddingServiceSingleton:
    """Tests for singleton pattern"""
    
    def test_get_embedding_service_singleton(self):
        """Test that get_embedding_service returns singleton"""
        with patch('embedding_service.service.SentenceTransformer'):
            with patch('embedding_service.service.torch.cuda.is_available', return_value=False):
                from embedding_service.service import get_embedding_service
                
                # Reset singleton
                import embedding_service.service
                embedding_service.service._embedding_service_instance = None
                
                service1 = get_embedding_service()
                service2 = get_embedding_service()
                
                assert service1 is service2


class TestEmbeddingAPI:
    """Tests for FastAPI endpoints"""
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service"""
        service = Mock()
        service.model_name = "test-model"
        service.device = "cpu"
        service.embedding_dim = 768
        service.encode_text = Mock(return_value=np.random.randn(768))
        service.encode_batch = Mock(return_value=np.random.randn(3, 768))
        service.encode_sections = Mock(return_value={
            "facts": np.random.randn(768),
            "issue": np.random.randn(768)
        })
        service.get_model_info = Mock(return_value={
            "model_name": "test-model",
            "embedding_dimension": 768,
            "device": "cpu",
            "batch_size": 32,
            "max_seq_length": 512
        })
        return service
    
    def test_health_endpoint(self, mock_embedding_service):
        """Test health check endpoint"""
        # This would require TestClient from fastapi.testclient
        # Placeholder for when dependencies are installed
        pass
    
    def test_embed_text_endpoint(self, mock_embedding_service):
        """Test /embed/text endpoint"""
        # Placeholder for integration test
        pass
    
    def test_embed_batch_endpoint(self, mock_embedding_service):
        """Test /embed/batch endpoint"""
        # Placeholder for integration test
        pass
    
    def test_embed_sections_endpoint(self, mock_embedding_service):
        """Test /embed/sections endpoint"""
        # Placeholder for integration test
        pass


# Property-based tests (Task 3.2 - optional)
# These would use Hypothesis library for property testing
# Example structure:

# from hypothesis import given, strategies as st
# 
# @given(st.text(min_size=1))
# def test_embedding_dimension_consistency(text):
#     """Property: All embeddings should have dimension 768"""
#     service = get_embedding_service()
#     embedding = service.encode_text(text)
#     assert len(embedding) == 768
# 
# @given(st.lists(st.text(min_size=1), min_size=1))
# def test_batch_embedding_count(texts):
#     """Property: Batch encoding should return same number of embeddings as inputs"""
#     service = get_embedding_service()
#     embeddings = service.encode_batch(texts)
#     assert len(embeddings) == len(texts)
