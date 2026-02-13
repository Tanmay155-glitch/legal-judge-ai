"""
Security Middleware for Legal LLM Supreme Court System
FIX VULN-012: Adds security headers
FIX VULN-011: Secure error handling
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
import time
import uuid


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    FIX VULN-012: Missing Security Headers
    """
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Enforce HTTPS (in production)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]
        
        # Remove X-Powered-By header
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request for tracking.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Add request ID to request state and response headers"""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests with PII redaction.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response"""
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log request (with PII redaction)
        from .security import redact_pii
        
        path = redact_pii(str(request.url.path))
        method = request.method
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info(
            f"Request started | "
            f"ID: {request_id} | "
            f"Method: {method} | "
            f"Path: {path} | "
            f"Client: {client_ip}"
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Request completed | "
                f"ID: {request_id} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
        
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed | "
                f"ID: {request_id} | "
                f"Error: {str(e)} | "
                f"Time: {process_time:.3f}s",
                exc_info=True
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling with secure error messages.
    FIX VULN-011: Verbose Error Messages
    """
    
    async def dispatch(self, request: Request, call_next):
        """Handle errors securely"""
        try:
            return await call_next(request)
        
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            
            # Log full error internally
            logger.error(
                f"Unhandled exception | "
                f"Request ID: {request_id} | "
                f"Error: {str(e)}",
                exc_info=True
            )
            
            # Return generic error to user
            return JSONResponse(
                status_code=500,
                content={
                    "error": "An internal error occurred",
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "request_id": request_id,
                    "message": "Please contact support with this request ID"
                }
            )


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Limit request body size to prevent memory exhaustion.
    FIX VULN-010: No Request Size Limits
    """
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        """
        Initialize middleware.
        
        Args:
            app: FastAPI application
            max_size: Maximum request size in bytes
        """
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        """Check request size"""
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        
        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "Request entity too large",
                        "max_size_mb": self.max_size / 1024 / 1024,
                        "your_size_mb": content_length / 1024 / 1024
                    }
                )
        
        return await call_next(request)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Add timeout to requests to prevent hanging.
    FIX VULN-027: No Timeout on External Calls
    """
    
    def __init__(self, app, timeout: float = 60.0):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI application
            timeout: Request timeout in seconds
        """
        super().__init__(app)
        self.timeout = timeout
    
    async def dispatch(self, request: Request, call_next):
        """Apply timeout to request"""
        import asyncio
        
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(
                f"Request timeout | "
                f"Request ID: {request_id} | "
                f"Timeout: {self.timeout}s"
            )
            
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Request timeout",
                    "timeout_seconds": self.timeout,
                    "request_id": request_id
                }
            )


def setup_middleware(app):
    """
    Setup all security middleware for the application.
    
    Args:
        app: FastAPI application
    """
    # Add middleware in reverse order (last added = first executed)
    
    # 1. Error handling (outermost)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 2. Request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # 3. Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 4. Request ID
    app.add_middleware(RequestIDMiddleware)
    
    # 5. Request size limit
    app.add_middleware(RequestSizeLimitMiddleware, max_size=10 * 1024 * 1024)
    
    # 6. Timeout
    app.add_middleware(TimeoutMiddleware, timeout=60.0)
    
    logger.info("Security middleware configured successfully")
