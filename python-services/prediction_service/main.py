"""
Prediction Service FastAPI Application
Provides REST API endpoints for judicial outcome prediction
"""

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from loguru import logger
import sys
import time

from prediction_service.service import get_outcome_predictor, OutcomePredictor
from shared.models import PredictionRequest, OutcomePrediction
from shared.security import verify_token
from shared.middleware import setup_middleware
from shared.rate_limiter import RateLimitMiddleware
from shared.cors_config import get_cors_config
from shared.config import get_security_settings, log_configuration

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>prediction_service</cyan> - <level>{message}</level>",
    level="INFO"
)

# Initialize FastAPI app
app = FastAPI(
    title="Legal LLM Prediction Service",
    description="Judicial outcome prediction service for Supreme Court cases",
    version="1.0.0"
)

# Setup CORS with secure configuration
app.add_middleware(CORSMiddleware, **get_cors_config())

# Setup rate limiting (lower limit for predictions)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=30,
    burst_size=5
)

# Setup security middleware
setup_middleware(app)

# Response models
class PredictionResponse(BaseModel):
    """Response model for outcome prediction"""
    prediction: OutcomePrediction
    processing_time_ms: float
    disclaimer: str = (
        "This prediction is AI-generated for research and academic purposes only. "
        "It does not constitute legal advice and should not be relied upon for "
        "actual legal proceedings."
    )


class PredictionStatsResponse(BaseModel):
    """Response model for prediction statistics"""
    total_predictions: int
    average_confidence: float
    low_confidence_rate: float
    outcome_distribution: dict


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    service: str
    predictor_ready: bool
    search_engine_available: bool


# Initialize prediction service on startup
outcome_predictor: Optional[OutcomePredictor] = None
prediction_stats = {
    "total_predictions": 0,
    "confidence_sum": 0.0,
    "low_confidence_count": 0,
    "outcome_counts": {"Affirmed": 0, "Reversed": 0, "Remanded": 0}
}


@app.on_event("startup")
async def startup_event():
    """Initialize the prediction service on startup"""
    global outcome_predictor
    try:
        logger.info("Starting Prediction Service...")
        
        # Log configuration
        log_configuration()
        
        # Import search engine
        from search_service.service import get_search_engine
        from vector_index.service import get_vector_index_service
        
        # Initialize dependencies
        vector_service = get_vector_index_service()
        search_engine = get_search_engine(vector_index_service=vector_service)
        
        # Initialize predictor
        outcome_predictor = get_outcome_predictor(search_engine=search_engine)
        
        logger.success("Prediction Service started successfully")
    except Exception as e:
        logger.error(f"Failed to start Prediction Service: {e}")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        service="prediction-service",
        predictor_ready=outcome_predictor is not None,
        search_engine_available=outcome_predictor.search_engine is not None if outcome_predictor else False
    )


@app.get("/stats", response_model=PredictionStatsResponse)
async def get_stats():
    """Get prediction statistics"""
    if outcome_predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction service not initialized"
        )
    
    try:
        total = prediction_stats["total_predictions"]
        avg_confidence = (
            prediction_stats["confidence_sum"] / total
            if total > 0 else 0.0
        )
        low_conf_rate = (
            prediction_stats["low_confidence_count"] / total
            if total > 0 else 0.0
        )
        
        return PredictionStatsResponse(
            total_predictions=total,
            average_confidence=round(avg_confidence, 3),
            low_confidence_rate=round(low_conf_rate, 3),
            outcome_distribution=prediction_stats["outcome_counts"]
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@app.post("/predict/outcome", response_model=PredictionResponse)
async def predict_outcome(
    request: PredictionRequest,
    user: dict = Depends(verify_token)
):
    """
    Predict judicial outcome based on case facts and legal issue.
    
    Requires authentication.
    
    Example:
        POST /predict/outcome
        Authorization: Bearer <token>
        {
            "facts": "The landlord failed to repair the heating system...",
            "issue": "Whether the landlord breached the warranty of habitability"
        }
    """
    if outcome_predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction service not initialized"
        )
    
    try:
        start_time = time.time()
        
        # Make prediction
        prediction = await outcome_predictor.predict_outcome(
            facts=request.facts,
            issue=request.issue,
            year_range=(2022, 2023)  # Default to our corpus range
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Update statistics
        prediction_stats["total_predictions"] += 1
        prediction_stats["confidence_sum"] += prediction.confidence
        prediction_stats["outcome_counts"][prediction.outcome] += 1
        
        if outcome_predictor.is_low_confidence(prediction):
            prediction_stats["low_confidence_count"] += 1
        
        logger.info(f"Prediction: {prediction.outcome} "
                   f"(confidence: {prediction.confidence:.2f}, "
                   f"time: {processing_time_ms:.0f}ms)")
        
        return PredictionResponse(
            prediction=prediction,
            processing_time_ms=round(processing_time_ms, 2)
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error making prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/predict/batch")
async def predict_batch(
    requests: List[PredictionRequest],
    user: dict = Depends(verify_token)
):
    """
    Predict outcomes for multiple cases in batch.
    
    Requires authentication. Maximum 50 requests per batch.
    
    Example:
        POST /predict/batch
        Authorization: Bearer <token>
        [
            {
                "facts": "Case 1 facts...",
                "issue": "Case 1 issue..."
            },
            {
                "facts": "Case 2 facts...",
                "issue": "Case 2 issue..."
            }
        ]
    """
    if outcome_predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction service not initialized"
        )
    
    if len(requests) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size limited to 50 requests"
        )
    
    try:
        start_time = time.time()
        predictions = []
        
        for req in requests:
            prediction = await outcome_predictor.predict_outcome(
                facts=req.facts,
                issue=req.issue,
                year_range=(2022, 2023)
            )
            predictions.append(prediction)
            
            # Update statistics
            prediction_stats["total_predictions"] += 1
            prediction_stats["confidence_sum"] += prediction.confidence
            prediction_stats["outcome_counts"][prediction.outcome] += 1
            
            if outcome_predictor.is_low_confidence(prediction):
                prediction_stats["low_confidence_count"] += 1
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Batch prediction: {len(predictions)} cases "
                   f"(time: {processing_time_ms:.0f}ms)")
        
        return {
            "predictions": predictions,
            "total_cases": len(predictions),
            "processing_time_ms": round(processing_time_ms, 2),
            "disclaimer": (
                "These predictions are AI-generated for research and academic purposes only. "
                "They do not constitute legal advice."
            )
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
