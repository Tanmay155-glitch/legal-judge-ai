"""
Embedding Service FastAPI Application
Provides REST API endpoints for Legal-BERT embedding generation
"""

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import numpy as np
from loguru import logger
import sys

from embedding_service.service import get_embedding_service, EmbeddingService
from shared.security import verify_token
from shared.middleware import setup_middleware
from shared.rate_limiter import RateLimitMiddleware
from shared.cors_config import get_cors_config
from shared.config import get_security_settings, log_configuration

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>embedding_service</cyan> - <level>{message}</level>",
    level="INFO"
)

# Initialize FastAPI app
app = FastAPI(
    title="Legal LLM Embedding Service",
    description="Legal-BERT embedding generation service for Supreme Court case laws",
    version="1.0.0"
)

# Setup CORS with secure configuration
app.add_middleware(CORSMiddleware, **get_cors_config())

# Setup rate limiting
settings = get_security_settings()
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_per_minute,
    burst_size=settings.rate_limit_burst
)

# Setup security middleware (headers, error handling, logging)
setup_middleware(app)

# Request/Response models
class EmbedTextRequest(BaseModel):
    """Request model for single text embedding"""
    text: str = Field(..., min_length=1, description="Text to encode")
    normalize: bool = Field(default=True, description="Whether to normalize the embedding")


class EmbedBatchRequest(BaseModel):
    """Request model for batch text embedding"""
    texts: List[str] = Field(..., min_items=1, description="List of texts to encode")
    batch_size: Optional[int] = Field(default=None, description="Batch size for processing")
    normalize: bool = Field(default=True, description="Whether to normalize embeddings")
    show_progress: bool = Field(default=False, description="Whether to show progress bar")


class EmbedSectionsRequest(BaseModel):
    """Request model for document sections embedding"""
    sections: Dict[str, str] = Field(..., description="Dictionary of section name to text")
    normalize: bool = Field(default=True, description="Whether to normalize embeddings")


class EmbeddingResponse(BaseModel):
    """Response model for single embedding"""
    embedding: List[float] = Field(..., description="768-dimensional embedding vector")
    dimension: int = Field(..., description="Embedding dimension")
    model: str = Field(..., description="Model used for encoding")


class BatchEmbeddingResponse(BaseModel):
    """Response model for batch embeddings"""
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    count: int = Field(..., description="Number of embeddings")
    dimension: int = Field(..., description="Embedding dimension")
    model: str = Field(..., description="Model used for encoding")


class SectionEmbeddingResponse(BaseModel):
    """Response model for section embeddings"""
    section_embeddings: Dict[str, Optional[List[float]]] = Field(
        ...,
        description="Dictionary mapping section names to embeddings"
    )
    dimension: int = Field(..., description="Embedding dimension")
    model: str = Field(..., description="Model used for encoding")


class ModelInfoResponse(BaseModel):
    """Response model for model information"""
    model_name: str
    embedding_dimension: int
    device: str
    batch_size: int
    max_seq_length: int


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    service: str
    model_loaded: bool
    device: str


# Initialize embedding service on startup
embedding_service: Optional[EmbeddingService] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the embedding service on startup"""
    global embedding_service
    try:
        logger.info("Starting Embedding Service...")
        
        # Log configuration
        log_configuration()
        
        embedding_service = get_embedding_service()
        logger.success("Embedding Service started successfully")
    except Exception as e:
        logger.error(f"Failed to start Embedding Service: {e}")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        service="embedding-service",
        model_loaded=embedding_service is not None,
        device=embedding_service.device if embedding_service else "unknown"
    )


@app.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """Get information about the loaded model"""
    if embedding_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service not initialized"
        )
    
    info = embedding_service.get_model_info()
    return ModelInfoResponse(**info)


@app.post("/embed/text", response_model=EmbeddingResponse)
async def embed_text(
    request: EmbedTextRequest,
    user: dict = Depends(verify_token)
):
    """
    Generate embedding for a single text.
    
    Requires authentication.
    
    Example:
        POST /embed/text
        Authorization: Bearer <token>
        {
            "text": "The Court holds that...",
            "normalize": true
        }
    """
    if embedding_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service not initialized"
        )
    
    try:
        embedding = embedding_service.encode_text(
            text=request.text,
            normalize=request.normalize
        )
        
        return EmbeddingResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding),
            model=embedding_service.model_name
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error encoding text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encode text: {str(e)}"
        )


@app.post("/embed/batch", response_model=BatchEmbeddingResponse)
async def embed_batch(
    request: EmbedBatchRequest,
    user: dict = Depends(verify_token)
):
    """
    Generate embeddings for a batch of texts.
    
    Requires authentication.
    
    Example:
        POST /embed/batch
        Authorization: Bearer <token>
        {
            "texts": ["Text 1", "Text 2", "Text 3"],
            "batch_size": 32,
            "normalize": true
        }
    """
    if embedding_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service not initialized"
        )
    
    try:
        embeddings = embedding_service.encode_batch(
            texts=request.texts,
            batch_size=request.batch_size,
            normalize=request.normalize,
            show_progress=request.show_progress
        )
        
        return BatchEmbeddingResponse(
            embeddings=embeddings.tolist(),
            count=len(embeddings),
            dimension=embeddings.shape[1],
            model=embedding_service.model_name
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error encoding batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encode batch: {str(e)}"
        )


@app.post("/embed/sections", response_model=SectionEmbeddingResponse)
async def embed_sections(
    request: EmbedSectionsRequest,
    user: dict = Depends(verify_token)
):
    """
    Generate embeddings for document sections.
    
    Requires authentication.
    
    Example:
        POST /embed/sections
        Authorization: Bearer <token>
        {
            "sections": {
                "facts": "The plaintiff entered into a lease...",
                "issue": "Whether the landlord breached...",
                "reasoning": "The Court has consistently held..."
            },
            "normalize": true
        }
    """
    if embedding_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service not initialized"
        )
    
    try:
        section_embeddings = embedding_service.encode_sections(
            sections=request.sections,
            normalize=request.normalize
        )
        
        # Convert numpy arrays to lists
        section_embeddings_list = {
            name: emb.tolist() if emb is not None else None
            for name, emb in section_embeddings.items()
        }
        
        return SectionEmbeddingResponse(
            section_embeddings=section_embeddings_list,
            dimension=embedding_service.embedding_dim,
            model=embedding_service.model_name
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error encoding sections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encode sections: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
