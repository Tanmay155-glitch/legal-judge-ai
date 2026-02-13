"""
Secure CORS Configuration
FIX VULN-009: CORS Misconfiguration
"""

import os
from typing import List

# Get allowed origins from environment variable
ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", "")

# Default allowed origins for development
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]

# Parse allowed origins from environment
if ALLOWED_ORIGINS_ENV:
    ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_ENV.split(",")]
else:
    ALLOWED_ORIGINS = DEFAULT_ALLOWED_ORIGINS

# Production check
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

if IS_PRODUCTION and not ALLOWED_ORIGINS_ENV:
    raise ValueError(
        "ALLOWED_ORIGINS environment variable must be set in production"
    )


def get_cors_config() -> dict:
    """
    Get secure CORS configuration.
    
    Returns:
        Dictionary with CORS configuration
    """
    return {
        "allow_origins": ALLOWED_ORIGINS,  # ✓ Specific origins only
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # ✓ Specific methods
        "allow_headers": [
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-API-Key"
        ],  # ✓ Specific headers
        "expose_headers": [
            "X-Request-ID",
            "X-Process-Time",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining"
        ],
        "max_age": 3600,  # Cache preflight requests for 1 hour
    }


def log_cors_config():
    """Log CORS configuration for debugging"""
    from loguru import logger
    
    logger.info(f"CORS Configuration:")
    logger.info(f"  Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"  Allowed Origins: {ALLOWED_ORIGINS}")
    logger.info(f"  Allow Credentials: True")
