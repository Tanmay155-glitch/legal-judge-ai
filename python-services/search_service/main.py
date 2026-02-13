"""
Search Service FastAPI Application
Provides REST API endpoints for semantic legal search
"""

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from loguru import logger
import sys
import time

from search_service.service import get_search_engine, SemanticSearchEngine
from shared.models import SearchRequest, SearchResult
from shared.security import verify_token
from shared.middleware import setup_middleware
from shared.rate_limiter import RateLimitMiddleware
from shared.cors_config import get_cors_config
from shared.config import get_security_settings, log_configuration

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>search_service</cyan> - <level>{message}</level>",
    level="INFO"
)

# Initialize FastAPI app
app = FastAPI(
    title="Legal LLM Search Service",
    description="Semantic search service for Supreme Court case laws",
    version="1.0.0"
)

# Setup CORS with secure configuration
app.add_middleware(CORSMiddleware, **get_cors_config())

# Setup rate limiting (moderate limit for search)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    burst_size=10
)

# Setup security middleware
setup_middleware(app)

# Response models
class SearchResponse(BaseModel):
    """Response model for search results"""
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    query: str


class SearchStatsResponse(BaseModel):
    """Response model for search statistics"""
    total_searches: int
    total_documents_indexed: int
    average_search_time_ms: float
    cache_hit_rate: float


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    service: str
    search_engine_ready: bool
    embedding_service_url: str
    vector_index_url: str


# Initialize search engine on startup
search_engine: Optional[SemanticSearchEngine] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the search engine on startup"""
    global search_engine
    try:
        logger.info("Starting Search Service...")
        
        # Log configuration
        log_configuration()
        
        search_engine = get_search_engine()
        logger.success("Search Service started successfully")
    except Exception as e:
        logger.error(f"Failed to start Search Service: {e}")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        service="search-service",
        search_engine_ready=search_engine is not None,
        embedding_service_url=search_engine.embedding_service_url if search_engine else "unknown",
        vector_index_url=search_engine.vector_index_url if search_engine else "unknown"
    )


@app.get("/stats", response_model=SearchStatsResponse)
async def get_stats():
    """Get search statistics"""
    if search_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search engine not initialized"
        )
    
    try:
        stats = search_engine.get_search_stats()
        return SearchStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@app.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    user: dict = Depends(verify_token)
):
    """
    Perform semantic search on case laws.
    
    Requires authentication.
    
    Example:
        POST /search
        Authorization: Bearer <token>
        {
            "query": "breach of contract in lease agreements",
            "top_k": 10,
            "min_similarity": 0.6
        }
    """
    if search_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search engine not initialized"
        )
    
    try:
        start_time = time.time()
        
        results = await search_engine.search(
            query=request.query,
            top_k=request.top_k,
            section_filter=request.section_filter,
            year_range=request.year_range,
            min_similarity=request.min_similarity
        )
        
        search_time_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_time_ms=round(search_time_ms, 2),
            query=request.query
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@app.post("/search/facts", response_model=SearchResponse)
async def search_by_facts(
    request: SearchRequest,
    user: dict = Depends(verify_token)
):
    """
    Search specifically in the facts sections of case laws.
    
    Requires authentication.
    
    Example:
        POST /search/facts
        Authorization: Bearer <token>
        {
            "query": "plaintiff entered into a lease agreement",
            "top_k": 5
        }
    """
    if search_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search engine not initialized"
        )
    
    try:
        start_time = time.time()
        
        results = await search_engine.search_by_facts(
            query=request.query,
            top_k=request.top_k,
            year_range=request.year_range,
            min_similarity=request.min_similarity
        )
        
        search_time_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_time_ms=round(search_time_ms, 2),
            query=request.query
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error performing facts search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Facts search failed: {str(e)}"
        )


@app.post("/search/reasoning", response_model=SearchResponse)
async def search_by_reasoning(
    request: SearchRequest,
    user: dict = Depends(verify_token)
):
    """
    Search specifically in the reasoning sections of case laws.
    
    Requires authentication.
    
    Example:
        POST /search/reasoning
        Authorization: Bearer <token>
        {
            "query": "strict scrutiny analysis",
            "top_k": 5
        }
    """
    if search_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search engine not initialized"
        )
    
    try:
        start_time = time.time()
        
        results = await search_engine.search_by_reasoning(
            query=request.query,
            top_k=request.top_k,
            year_range=request.year_range,
            min_similarity=request.min_similarity
        )
        
        search_time_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            search_time_ms=round(search_time_ms, 2),
            query=request.query
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error performing reasoning search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reasoning search failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
