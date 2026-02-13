"""
Ingestion Service FastAPI Application
Provides REST API endpoints for case law document ingestion
"""

from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from loguru import logger
import sys
import time
import os
import tempfile

from ingestion_service.service import get_ingestion_service, IngestionService
from shared.models import IngestionResult
from shared.security import verify_token, require_role, validate_path, validate_pdf_file
from shared.middleware import setup_middleware
from shared.rate_limiter import RateLimitMiddleware
from shared.cors_config import get_cors_config
from shared.config import get_security_settings, log_configuration

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>ingestion_service</cyan> - <level>{message}</level>",
    level="INFO"
)

# Initialize FastAPI app
app = FastAPI(
    title="Legal LLM Ingestion Service",
    description="Case law document ingestion and processing service",
    version="1.0.0"
)

# Setup CORS with secure configuration
app.add_middleware(CORSMiddleware, **get_cors_config())

# Setup rate limiting (lower limit for ingestion)
settings = get_security_settings()
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=20,  # Lower limit for resource-intensive operations
    burst_size=5
)

# Setup security middleware
setup_middleware(app)

# Request/Response models
class BatchIngestionRequest(BaseModel):
    """Request model for batch ingestion"""
    directory_path: str = Field(..., description="Path to directory containing PDFs")
    batch_size: int = Field(default=10, ge=1, le=100, description="Batch processing size")


class IngestionStatsResponse(BaseModel):
    """Response model for ingestion statistics"""
    total_documents_ingested: int
    successful_ingestions: int
    failed_ingestions: int
    average_processing_time_seconds: float
    total_vectors_stored: int


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    service: str
    ingestion_service_ready: bool
    ocr_service_available: bool
    embedding_service_available: bool
    vector_index_available: bool


# Initialize ingestion service on startup
ingestion_service: Optional[IngestionService] = None
ingestion_stats = {
    "total_documents": 0,
    "successful": 0,
    "failed": 0,
    "total_time": 0.0,
    "total_vectors": 0
}


@app.on_event("startup")
async def startup_event():
    """Initialize the ingestion service on startup"""
    global ingestion_service
    try:
        logger.info("Starting Ingestion Service...")
        
        # Log configuration
        log_configuration()
        
        # Import dependencies
        from embedding_service.service import get_embedding_service
        from vector_index.service import get_vector_index_service
        
        # Initialize dependencies
        embedding_service = get_embedding_service()
        vector_service = get_vector_index_service()
        
        # Initialize ingestion service
        ingestion_service = get_ingestion_service(
            embedding_service=embedding_service,
            vector_service=vector_service
        )
        
        logger.success("Ingestion Service started successfully")
    except Exception as e:
        logger.error(f"Failed to start Ingestion Service: {e}")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        service="ingestion-service",
        ingestion_service_ready=ingestion_service is not None,
        ocr_service_available=True,  # Assume available
        embedding_service_available=ingestion_service.embedding_service is not None if ingestion_service else False,
        vector_index_available=ingestion_service.vector_service is not None if ingestion_service else False
    )


@app.get("/stats", response_model=IngestionStatsResponse)
async def get_stats():
    """Get ingestion statistics"""
    if ingestion_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion service not initialized"
        )
    
    try:
        total = ingestion_stats["total_documents"]
        avg_time = (
            ingestion_stats["total_time"] / total
            if total > 0 else 0.0
        )
        
        return IngestionStatsResponse(
            total_documents_ingested=total,
            successful_ingestions=ingestion_stats["successful"],
            failed_ingestions=ingestion_stats["failed"],
            average_processing_time_seconds=round(avg_time, 2),
            total_vectors_stored=ingestion_stats["total_vectors"]
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@app.post("/ingest/pdf", response_model=IngestionResult)
async def ingest_pdf(
    file: UploadFile = File(..., description="PDF file to ingest"),
    case_name: Optional[str] = Form(None, description="Optional case name override"),
    user: dict = Depends(verify_token)
):
    """
    Ingest a single PDF case law document.
    
    Requires authentication.
    
    The PDF will be:
    1. Validated for file type and content
    2. Extracted using OCR service
    3. Parsed into structured sections
    4. Validated against schema
    5. Embedded using Legal-BERT
    6. Stored in vector index
    
    Example:
        POST /ingest/pdf
        Authorization: Bearer <token>
        Content-Type: multipart/form-data
        
        file: <PDF file>
        case_name: "Smith v. Jones" (optional)
    """
    if ingestion_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion service not initialized"
        )
    
    try:
        start_time = time.time()
        
        # Read file content
        content = await file.read()
        
        # Validate PDF file (checks magic number, size, malicious content)
        validated_content = await validate_pdf_file(content, file.filename)
        
        # Save validated file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(validated_content)
            temp_path = temp_file.name
        
        try:
            # Ingest the PDF
            result = await ingestion_service.ingest_pdf(
                pdf_path=temp_path,
                case_name_override=case_name
            )
            
            processing_time = time.time() - start_time
            result.processing_time_seconds = processing_time
            
            # Update statistics
            ingestion_stats["total_documents"] += 1
            ingestion_stats["total_time"] += processing_time
            ingestion_stats["total_vectors"] += len(result.vector_ids)
            
            if result.status == "success":
                ingestion_stats["successful"] += 1
            else:
                ingestion_stats["failed"] += 1
            
            logger.info(f"Ingested: {result.case_name} "
                       f"(status: {result.status}, time: {processing_time:.2f}s)")
            
            return result
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except ValueError as e:
        ingestion_stats["total_documents"] += 1
        ingestion_stats["failed"] += 1
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        ingestion_stats["total_documents"] += 1
        ingestion_stats["failed"] += 1
        logger.error(f"Error ingesting PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.post("/ingest/batch")
async def ingest_batch(
    request: BatchIngestionRequest,
    user: dict = Depends(require_role("admin"))
):
    """
    Ingest multiple PDF documents from a directory.
    
    Requires admin role for batch operations.
    
    Example:
        POST /ingest/batch
        Authorization: Bearer <admin_token>
        {
            "directory_path": "/app/uploads/cases",
            "batch_size": 10
        }
    """
    if ingestion_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion service not initialized"
        )
    
    try:
        # Validate and sanitize path (prevents path traversal)
        validated_path = validate_path(
            request.directory_path,
            allowed_base="/app/uploads"
        )
        
        # Check if directory exists
        if not validated_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Directory not found: {request.directory_path}"
            )
        
        if not validated_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is not a directory: {request.directory_path}"
            )
        
        start_time = time.time()
        
        # Get list of PDF files (using validated path)
        pdf_files = [
            str(f) for f in validated_path.glob("*.pdf")
        ]
        
        # Limit batch size
        if len(pdf_files) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size too large: {len(pdf_files)} files. Maximum is 100."
            )
        
        if not pdf_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No PDF files found in directory"
            )
        
        logger.info(f"Starting batch ingestion of {len(pdf_files)} PDFs")
        
        # Process batch
        results = await ingestion_service.batch_ingest(
            pdf_paths=pdf_files,
            batch_size=request.batch_size
        )
        
        processing_time = time.time() - start_time
        
        # Update statistics
        for result in results:
            ingestion_stats["total_documents"] += 1
            ingestion_stats["total_vectors"] += len(result.vector_ids)
            
            if result.status == "success":
                ingestion_stats["successful"] += 1
            else:
                ingestion_stats["failed"] += 1
        
        ingestion_stats["total_time"] += processing_time
        
        # Summarize results
        successful = sum(1 for r in results if r.status == "success")
        failed = len(results) - successful
        
        logger.info(f"Batch ingestion complete: {successful} successful, "
                   f"{failed} failed, time: {processing_time:.2f}s")
        
        return {
            "total_files": len(pdf_files),
            "successful": successful,
            "failed": failed,
            "processing_time_seconds": round(processing_time, 2),
            "results": results
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in batch ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch ingestion failed: {str(e)}"
        )


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user: dict = Depends(require_role("admin"))
):
    """
    Delete a document from the vector index.
    
    Requires admin role.
    
    Example:
        DELETE /documents/abc-123-def-456
        Authorization: Bearer <admin_token>
    """
    if ingestion_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion service not initialized"
        )
    
    try:
        # Delete from vector index
        ingestion_service.vector_service.delete_document(document_id)
        
        logger.info(f"Deleted document: {document_id}")
        
        return {
            "status": "success",
            "message": f"Document {document_id} deleted successfully"
        }
    
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
