"""
Security Fixes - Code Examples for Legal LLM Supreme Court System

This file contains working code examples to fix the critical security vulnerabilities.
Copy and adapt these examples to your services.
"""

# ============================================================================
# FIX 1: Implement JWT Authentication
# ============================================================================

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

# Configuration
SECRET_KEY = "your-secret-key-here"  # Store in environment variable!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Usage in endpoint:
# @app.post("/search")
# async def search(
#     request: SearchRequest,
#     user_id: str = Depends(verify_token)
# ):
#     # user_id is now verified
#     pass


# ============================================================================
# FIX 2: Implement Rate Limiting
# ============================================================================

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Usage in endpoint:
# @app.post("/search")
# @limiter.limit("100/minute")
# async def search(request: Request, search_request: SearchRequest):
#     pass


# ============================================================================
# FIX 3: Fix Path Traversal Vulnerability
# ============================================================================

import os
from pathlib import Path
from typing import Union

def validate_path(
    directory_path: str,
    allowed_base: str = "/app/data"
) -> Path:
    """
    Validate path to prevent path traversal attacks.
    
    Args:
        directory_path: User-provided path
        allowed_base: Base directory that paths must be within
        
    Returns:
        Validated Path object
        
    Raises:
        ValueError: If path is outside allowed base
    """
    # Resolve to absolute path
    path = Path(directory_path).resolve()
    base = Path(allowed_base).resolve()
    
    # Check if path is within allowed base
    try:
        path.relative_to(base)
    except ValueError:
        raise ValueError(f"Path traversal detected: {directory_path}")
    
    # Additional checks
    if not path.exists():
        raise ValueError(f"Path does not exist: {directory_path}")
    
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")
    
    return path

# Usage:
# @app.post("/ingest/batch")
# async def ingest_batch(request: BatchIngestionRequest):
#     try:
#         validated_path = validate_path(
#             request.directory_path,
#             allowed_base="/app/uploads"
#         )
#         # Use validated_path for processing
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# FIX 4: Fix CORS Configuration
# ============================================================================

from fastapi.middleware.cors import CORSMiddleware

# SECURE CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com",
        "https://admin.yourdomain.com"
    ],  # ✓ Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # ✓ Specific methods
    allow_headers=["Authorization", "Content-Type"],  # ✓ Specific headers
    max_age=3600,  # Cache preflight requests
)


# ============================================================================
# FIX 5: Sanitize Sensitive Data in Logs
# ============================================================================

import re
from typing import Any, Dict

def redact_pii(text: str) -> str:
    """Redact PII from text"""
    # Redact email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Redact phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    
    # Redact SSN
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
    
    # Redact credit card numbers
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', text)
    
    return text

def safe_log(message: str, data: Dict[str, Any] = None):
    """Log with PII redaction"""
    safe_message = redact_pii(message)
    
    if data:
        safe_data = {k: redact_pii(str(v)) if isinstance(v, str) else v 
                     for k, v in data.items()}
        logger.info(f"{safe_message} | Data: {safe_data}")
    else:
        logger.info(safe_message)

# Usage:
# safe_log(f"Processing case: {case_name}", {"facts": facts})


# ============================================================================
# FIX 6: Input Validation with Length Limits
# ============================================================================

from pydantic import BaseModel, Field, validator

class SecurePredictionRequest(BaseModel):
    """Secure prediction request with proper validation"""
    facts: str = Field(
        ...,
        min_length=20,
        max_length=10000,  # ✓ Add max length
        description="Case facts"
    )
    issue: str = Field(
        ...,
        min_length=10,
        max_length=1000,  # ✓ Add max length
        description="Legal issue"
    )
    
    @validator('facts', 'issue')
    def sanitize_input(cls, v):
        """Sanitize input to prevent injection"""
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '{', '}', '|', '\\', '^', '`']
        for char in dangerous_chars:
            v = v.replace(char, '')
        return v.strip()


# ============================================================================
# FIX 7: File Upload Validation
# ============================================================================

import magic
from fastapi import UploadFile

async def validate_pdf_file(file: UploadFile) -> bytes:
    """
    Validate uploaded PDF file.
    
    Returns file content if valid, raises HTTPException otherwise.
    """
    # Check file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE} bytes"
        )
    
    # Check file extension
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    # Check magic number (file signature)
    file_type = magic.from_buffer(content, mime=True)
    if file_type != 'application/pdf':
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Expected PDF, got {file_type}"
        )
    
    # Check PDF header
    if not content.startswith(b'%PDF'):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file format"
        )
    
    return content

# Usage:
# @app.post("/ingest/pdf")
# async def ingest_pdf(file: UploadFile = File(...)):
#     content = await validate_pdf_file(file)
#     # Process validated content


# ============================================================================
# FIX 8: Secure Error Handling
# ============================================================================

from fastapi import Request
from fastapi.responses import JSONResponse

class SecureException(Exception):
    """Base exception with safe error messages"""
    def __init__(self, message: str, internal_message: str = None):
        self.message = message  # User-facing message
        self.internal_message = internal_message or message  # Internal log
        super().__init__(self.message)

@app.exception_handler(Exception)
async def secure_exception_handler(request: Request, exc: Exception):
    """Handle exceptions securely"""
    # Log detailed error internally
    logger.error(f"Error processing request: {str(exc)}", exc_info=True)
    
    # Return generic error to user
    return JSONResponse(
        status_code=500,
        content={
            "error": "An internal error occurred",
            "error_code": "INTERNAL_ERROR",
            "request_id": request.state.request_id  # For support
        }
    )


# ============================================================================
# FIX 9: Implement Request Timeouts
# ============================================================================

import httpx
import asyncio

async def call_external_service_with_timeout(
    url: str,
    data: dict,
    timeout: float = 30.0
) -> dict:
    """Call external service with timeout"""
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="External service timeout"
            )
        except httpx.HTTPError as e:
            logger.error(f"External service error: {e}")
            raise HTTPException(
                status_code=502,
                detail="External service unavailable"
            )


# ============================================================================
# FIX 10: Add Security Headers
# ============================================================================

from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

# Add to app
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "*.yourdomain.com"])


# ============================================================================
# COMPLETE SECURE ENDPOINT EXAMPLE
# ============================================================================

@app.post("/api/v1/search")
@limiter.limit("100/minute")  # Rate limiting
async def secure_search(
    request: Request,
    search_request: SearchRequest,
    user_id: str = Depends(verify_token)  # Authentication
):
    """
    Secure search endpoint with all protections enabled.
    """
    try:
        # Validate input
        if len(search_request.query) > 1000:
            raise HTTPException(400, "Query too long")
        
        # Sanitize input
        safe_query = redact_pii(search_request.query)
        
        # Log safely
        safe_log(f"Search request from user {user_id}", {"query": safe_query})
        
        # Call service with timeout
        results = await call_external_service_with_timeout(
            url="http://search-service:8003/search",
            data=search_request.dict(),
            timeout=30.0
        )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(500, "Search failed")


# ============================================================================
# INSTALLATION REQUIREMENTS
# ============================================================================

"""
Add these to requirements.txt:

python-jose[cryptography]==3.3.0  # JWT
slowapi==0.1.9  # Rate limiting
python-multipart==0.0.9  # File uploads
python-magic==0.4.27  # File type detection
httpx==0.26.0  # Async HTTP client
"""

