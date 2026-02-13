"""
Opinion Service FastAPI Application
Provides REST API endpoints for judicial opinion generation
"""

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict
from loguru import logger
import sys
import time

from opinion_service.service import get_opinion_generator, OpinionGenerator
from shared.models import OpinionRequest, GeneratedOpinion
from shared.security import verify_token, sanitize_llm_input
from shared.middleware import setup_middleware
from shared.rate_limiter import RateLimitMiddleware
from shared.cors_config import get_cors_config
from shared.config import get_security_settings, log_configuration

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>opinion_service</cyan> - <level>{message}</level>",
    level="INFO"
)

# Initialize FastAPI app
app = FastAPI(
    title="Legal LLM Opinion Service",
    description="Judicial opinion generation service using RAG pipeline",
    version="1.0.0"
)

# Setup CORS with secure configuration
app.add_middleware(CORSMiddleware, **get_cors_config())

# Setup rate limiting (lowest limit for expensive LLM operations)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=10,
    burst_size=2
)

# Setup security middleware
setup_middleware(app)

# Response models
class OpinionResponse(BaseModel):
    """Response model for opinion generation"""
    opinion: GeneratedOpinion
    processing_time_ms: float


class OpinionStatsResponse(BaseModel):
    """Response model for opinion generation statistics"""
    total_opinions_generated: int
    average_generation_time_ms: float
    total_precedents_retrieved: int
    opinion_types: Dict[str, int]


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    service: str
    generator_ready: bool
    llm_configured: bool
    search_engine_available: bool


# Initialize opinion service on startup
opinion_generator: Optional[OpinionGenerator] = None
opinion_stats = {
    "total_opinions": 0,
    "total_time_ms": 0.0,
    "total_precedents": 0,
    "opinion_types": {"per_curiam": 0, "majority": 0, "other": 0}
}


@app.on_event("startup")
async def startup_event():
    """Initialize the opinion service on startup"""
    global opinion_generator
    try:
        logger.info("Starting Opinion Service...")
        
        # Log configuration
        log_configuration()
        
        # Import dependencies
        from search_service.service import get_search_engine
        from vector_index.service import get_vector_index_service
        
        # Initialize dependencies
        vector_service = get_vector_index_service()
        search_engine = get_search_engine(vector_index_service=vector_service)
        
        # Initialize opinion generator
        opinion_generator = get_opinion_generator(search_engine=search_engine)
        
        logger.success("Opinion Service started successfully")
    except Exception as e:
        logger.error(f"Failed to start Opinion Service: {e}")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        service="opinion-service",
        generator_ready=opinion_generator is not None,
        llm_configured=bool(opinion_generator.llm_api_key) if opinion_generator else False,
        search_engine_available=opinion_generator.search_engine is not None if opinion_generator else False
    )


@app.get("/stats", response_model=OpinionStatsResponse)
async def get_stats():
    """Get opinion generation statistics"""
    if opinion_generator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Opinion service not initialized"
        )
    
    try:
        total = opinion_stats["total_opinions"]
        avg_time = (
            opinion_stats["total_time_ms"] / total
            if total > 0 else 0.0
        )
        
        return OpinionStatsResponse(
            total_opinions_generated=total,
            average_generation_time_ms=round(avg_time, 2),
            total_precedents_retrieved=opinion_stats["total_precedents"],
            opinion_types=opinion_stats["opinion_types"]
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@app.post("/generate/opinion", response_model=OpinionResponse)
async def generate_opinion(
    request: OpinionRequest,
    user: dict = Depends(verify_token)
):
    """
    Generate a judicial opinion using RAG pipeline.
    
    Requires authentication. Inputs are sanitized to prevent prompt injection.
    
    Example:
        POST /generate/opinion
        Authorization: Bearer <token>
        {
            "case_context": {
                "facts": "The landlord failed to repair the heating system...",
                "issue": "Whether the landlord breached the warranty of habitability",
                "case_name": "Smith v. Jones",
                "petitioner": "Smith",
                "respondent": "Jones"
            },
            "opinion_type": "per_curiam",
            "max_precedents": 5
        }
    """
    if opinion_generator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Opinion service not initialized"
        )
    
    try:
        start_time = time.time()
        
        # Validate case context
        if 'facts' not in request.case_context or 'issue' not in request.case_context:
            raise ValueError("case_context must include 'facts' and 'issue'")
        
        # Sanitize inputs to prevent prompt injection
        sanitized_context = {
            key: sanitize_llm_input(value) if isinstance(value, str) else value
            for key, value in request.case_context.items()
        }
        
        # Generate opinion with sanitized inputs
        opinion = await opinion_generator.generate_opinion(
            case_context=sanitized_context,
            opinion_type=request.opinion_type,
            max_precedents=request.max_precedents
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Update statistics
        opinion_stats["total_opinions"] += 1
        opinion_stats["total_time_ms"] += processing_time_ms
        opinion_stats["total_precedents"] += opinion.generation_metadata.get('precedents_used', 0)
        
        opinion_type_key = request.opinion_type if request.opinion_type in opinion_stats["opinion_types"] else "other"
        opinion_stats["opinion_types"][opinion_type_key] += 1
        
        logger.info(f"Opinion generated: {request.opinion_type} "
                   f"(time: {processing_time_ms:.0f}ms, "
                   f"precedents: {opinion.generation_metadata.get('precedents_used', 0)})")
        
        return OpinionResponse(
            opinion=opinion,
            processing_time_ms=round(processing_time_ms, 2)
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating opinion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Opinion generation failed: {str(e)}"
        )


@app.post("/generate/section")
async def generate_section(
    section_type: str = Field(..., description="Section type to generate"),
    context: Dict = Field(..., description="Context for section generation")
):
    """
    Generate a specific section of an opinion.
    
    Example:
        POST /generate/section
        {
            "section_type": "reasoning",
            "context": {
                "facts": "...",
                "issue": "...",
                "precedents": [...]
            }
        }
    """
    if opinion_generator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Opinion service not initialized"
        )
    
    try:
        # This is a simplified endpoint for generating individual sections
        # For now, we'll return a placeholder
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Section generation not yet implemented. Use /generate/opinion for full opinions."
        )
    
    except Exception as e:
        logger.error(f"Error generating section: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Section generation failed: {str(e)}"
        )


@app.get("/templates/{opinion_type}")
async def get_opinion_template(opinion_type: str):
    """
    Get the template structure for a specific opinion type.
    
    Example:
        GET /templates/per_curiam
    """
    templates = {
        "per_curiam": {
            "sections": [
                "procedural_history",
                "facts",
                "issue",
                "reasoning",
                "holding",
                "judgment"
            ],
            "format": "Supreme Court Per Curiam Opinion",
            "description": "Institutional opinion without individual attribution"
        },
        "majority": {
            "sections": [
                "procedural_history",
                "facts",
                "issue",
                "reasoning",
                "holding",
                "judgment"
            ],
            "format": "Supreme Court Majority Opinion",
            "description": "Opinion representing the majority of the Court"
        }
    }
    
    if opinion_type not in templates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template for opinion type '{opinion_type}' not found"
        )
    
    return templates[opinion_type]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
