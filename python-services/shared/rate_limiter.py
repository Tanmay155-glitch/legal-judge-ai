"""
Rate Limiting Middleware for Legal LLM Supreme Court System
FIX VULN-002: Implements rate limiting to prevent DDoS attacks
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
import time
from collections import defaultdict
import asyncio
from loguru import logger


class RateLimiter:
    """
    Token bucket rate limiter implementation.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 100,
        burst_size: int = 20
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.rate = requests_per_minute / 60.0  # Requests per second
        
        # Storage: {client_id: (tokens, last_update)}
        self.buckets: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (self.burst_size, time.time())
        )
        
        # Cleanup old entries periodically
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to cleanup old entries"""
        async def cleanup():
            while True:
                await asyncio.sleep(300)  # Every 5 minutes
                current_time = time.time()
                # Remove entries older than 10 minutes
                self.buckets = {
                    k: v for k, v in self.buckets.items()
                    if current_time - v[1] < 600
                }
                logger.debug(f"Rate limiter cleanup: {len(self.buckets)} active clients")
        
        # Start cleanup task
        asyncio.create_task(cleanup())
    
    def is_allowed(self, client_id: str) -> Tuple[bool, float]:
        """
        Check if request is allowed.
        
        Args:
            client_id: Client identifier (IP address or user ID)
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        current_time = time.time()
        tokens, last_update = self.buckets[client_id]
        
        # Calculate tokens to add based on time elapsed
        time_elapsed = current_time - last_update
        tokens_to_add = time_elapsed * self.rate
        tokens = min(self.burst_size, tokens + tokens_to_add)
        
        # Check if request is allowed
        if tokens >= 1.0:
            # Allow request and consume token
            tokens -= 1.0
            self.buckets[client_id] = (tokens, current_time)
            return True, 0.0
        else:
            # Deny request and calculate retry time
            tokens_needed = 1.0 - tokens
            retry_after = tokens_needed / self.rate
            self.buckets[client_id] = (tokens, current_time)
            return False, retry_after


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply rate limiting to all requests.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        burst_size: int = 20,
        exempt_paths: list = None
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per client
            burst_size: Maximum burst size
            exempt_paths: List of paths to exempt from rate limiting
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute, burst_size)
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Get client identifier (IP address or user ID from token)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        is_allowed, retry_after = self.rate_limiter.is_allowed(client_id)
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for client {client_id} "
                f"on path {request.url.path}"
            )
            
            return HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after_seconds": round(retry_after, 2),
                    "limit": f"{self.rate_limiter.requests_per_minute} requests per minute"
                },
                headers={
                    "Retry-After": str(int(retry_after) + 1),
                    "X-RateLimit-Limit": str(self.rate_limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_minute)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier from request.
        
        Priority:
        1. User ID from JWT token (if authenticated)
        2. API key (if present)
        3. IP address
        """
        # Try to get user ID from token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from jose import jwt
                token = auth_header.split(" ")[1]
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False}  # Just for ID extraction
                )
                user_id = payload.get("sub")
                if user_id:
                    return f"user:{user_id}"
            except:
                pass
        
        # Try to get API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get first IP in chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"


# ============================================================================
# Endpoint-specific rate limiters
# ============================================================================

class EndpointRateLimiter:
    """
    Rate limiter for specific endpoints with different limits.
    """
    
    def __init__(self):
        self.limiters = {
            "default": RateLimiter(requests_per_minute=100, burst_size=20),
            "search": RateLimiter(requests_per_minute=60, burst_size=10),
            "prediction": RateLimiter(requests_per_minute=30, burst_size=5),
            "opinion": RateLimiter(requests_per_minute=10, burst_size=2),
            "ingestion": RateLimiter(requests_per_minute=20, burst_size=5),
        }
    
    def get_limiter(self, endpoint_type: str) -> RateLimiter:
        """Get rate limiter for specific endpoint type"""
        return self.limiters.get(endpoint_type, self.limiters["default"])


# Global endpoint rate limiter instance
endpoint_rate_limiter = EndpointRateLimiter()


def check_rate_limit(client_id: str, endpoint_type: str = "default") -> None:
    """
    Check rate limit for specific endpoint.
    
    Args:
        client_id: Client identifier
        endpoint_type: Type of endpoint (search, prediction, opinion, etc.)
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    limiter = endpoint_rate_limiter.get_limiter(endpoint_type)
    is_allowed, retry_after = limiter.is_allowed(client_id)
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "retry_after_seconds": round(retry_after, 2),
                "endpoint_type": endpoint_type
            },
            headers={"Retry-After": str(int(retry_after) + 1)}
        )
