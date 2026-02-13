"""
Embedding Service - Legal-BERT vector generation
Converts legal text into 768-dimensional embeddings using Legal-BERT
"""

import os
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
import torch
from loguru import logger


class EmbeddingService:
    """
    Service for generating legal text embeddings using Legal-BERT.
    
    Features:
    - Legal-BERT (nlpaueb/legal-bert-base-uncased) for domain-specific encoding
    - Batch processing support
    - GPU acceleration when available
    - Consistent 768-dimensional vectors
    """
    
    def __init__(
        self,
        model_name: str = "nlpaueb/legal-bert-base-uncased",
        device: str = None,
        batch_size: int = 32
    ):
        """
        Initialize the embedding service with Legal-BERT model.
        
        Args:
            model_name: HuggingFace model identifier (default: Legal-BERT)
            device: Device to use ('cuda', 'cpu', or None for auto-detect)
            batch_size: Default batch size for batch encoding
        """
        self.model_name = model_name
        self.batch_size = batch_size
        
        # Auto-detect device if not specified
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"Initializing EmbeddingService with model: {model_name}")
        logger.info(f"Using device: {self.device}")
        
        try:
            # Load the sentence-transformers model
            self.model = SentenceTransformer(model_name, device=self.device)
            logger.success(f"Successfully loaded model: {model_name}")
            
            # Verify embedding dimension
            test_embedding = self.model.encode("test", convert_to_numpy=True)
            self.embedding_dim = len(test_embedding)
            
            # Fail fast if dimension is wrong
            if self.embedding_dim != 768:
                raise ValueError(
                    f"Model produces {self.embedding_dim}-dimensional embeddings, "
                    f"but system requires 768 dimensions. "
                    f"Please use a compatible model or update EMBEDDING_DIMENSION config."
                )
            
            logger.success(f"Verified embedding dimension: {self.embedding_dim}")
        
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def encode_text(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to encode
            normalize: Whether to normalize the embedding vector
        
        Returns:
            768-dimensional numpy array
        
        Raises:
            ValueError: If text is empty or None
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            
            return embedding
        
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            raise
    
    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = None,
        normalize: bool = True,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for processing (uses default if None)
            normalize: Whether to normalize embedding vectors
            show_progress: Whether to show progress bar
        
        Returns:
            numpy array of shape (len(texts), 768)
        
        Raises:
            ValueError: If texts list is empty
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        # Filter out empty texts and track indices
        valid_texts = []
        valid_indices = []
        for idx, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(idx)
        
        if not valid_texts:
            raise ValueError("All texts are empty")
        
        if len(valid_texts) < len(texts):
            logger.warning(
                f"Filtered out {len(texts) - len(valid_texts)} empty texts. "
                f"Processing {len(valid_texts)} valid texts."
            )
        
        batch_size = batch_size or self.batch_size
        
        try:
            logger.info(f"Encoding {len(valid_texts)} texts with batch size {batch_size}")
            
            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress
            )
            
            logger.success(f"Successfully encoded {len(valid_texts)} texts")
            
            # If we filtered out texts, create full array with None for invalid indices
            if len(valid_texts) < len(texts):
                full_embeddings = np.full((len(texts), self.embedding_dim), np.nan)
                for valid_idx, orig_idx in enumerate(valid_indices):
                    full_embeddings[orig_idx] = embeddings[valid_idx]
                return full_embeddings
            
            return embeddings
        
        except Exception as e:
            logger.error(f"Failed to encode batch: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimensionality of embeddings produced by this model.
        
        Returns:
            Embedding dimension (typically 768 for Legal-BERT)
        """
        return self.embedding_dim
    
    def encode_sections(
        self,
        sections: dict,
        normalize: bool = True
    ) -> dict:
        """
        Encode multiple sections of a document (e.g., facts, issue, reasoning).
        
        Args:
            sections: Dictionary mapping section names to text content
            normalize: Whether to normalize embedding vectors
        
        Returns:
            Dictionary mapping section names to embedding vectors
        
        Example:
            sections = {
                "facts": "The plaintiff entered into a lease...",
                "issue": "Whether the landlord breached...",
                "reasoning": "The Court has consistently held..."
            }
            embeddings = service.encode_sections(sections)
        """
        if not sections:
            raise ValueError("Sections dictionary cannot be empty")
        
        section_embeddings = {}
        
        for section_name, text in sections.items():
            if text and text.strip():
                try:
                    embedding = self.encode_text(text, normalize=normalize)
                    section_embeddings[section_name] = embedding
                    logger.debug(f"Encoded section '{section_name}' ({len(text)} chars)")
                except Exception as e:
                    logger.error(f"Failed to encode section '{section_name}': {e}")
                    section_embeddings[section_name] = None
            else:
                logger.warning(f"Section '{section_name}' is empty, skipping")
                section_embeddings[section_name] = None
        
        return section_embeddings
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dim,
            "device": self.device,
            "batch_size": self.batch_size,
            "max_seq_length": self.model.max_seq_length,
        }


# Singleton instance for the service
_embedding_service_instance = None


def get_embedding_service(
    model_name: str = None,
    device: str = None,
    batch_size: int = 32
) -> EmbeddingService:
    """
    Get or create the singleton EmbeddingService instance.
    
    Args:
        model_name: Model to use (only used on first call)
        device: Device to use (only used on first call)
        batch_size: Batch size (only used on first call)
    
    Returns:
        EmbeddingService instance
    """
    global _embedding_service_instance
    
    if _embedding_service_instance is None:
        model_name = model_name or os.getenv(
            "EMBEDDING_MODEL",
            "nlpaueb/legal-bert-base-uncased"
        )
        batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", batch_size))
        
        _embedding_service_instance = EmbeddingService(
            model_name=model_name,
            device=device,
            batch_size=batch_size
        )
    
    return _embedding_service_instance
