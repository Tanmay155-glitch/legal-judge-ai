"""
Centralized Configuration for Legal LLM Supreme Court System
Includes all security settings
"""

import os
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import secrets


def generate_secure_secret() -> str:
    """Generate cryptographically secure random secret"""
    return secrets.token_urlsafe(64)


class SecuritySettings(BaseSettings):
    """Security-related settings"""
    
    # JWT Settings
    jwt_secret_key: str = Field(
        default_factory=generate_secure_secret,
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=30, env="JWT_EXPIRATION_MINUTES")
    
    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v, values):
        environment = values.get('environment', os.getenv('ENVIRONMENT', 'development'))
        if environment == 'production':
            # Check if it's one of the old default secrets
            weak_secrets = [
                'your-secret-key-change-in-production',
                'change-this-secret-key-in-production'
            ]
            if v in weak_secrets:
                raise ValueError(
                    "JWT_SECRET_KEY must be set via environment variable in production. "
                    "Generate a secure secret with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            # Check minimum length
            if len(v) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
        return v
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=20, env="RATE_LIMIT_BURST")
    
    # File Upload
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    allowed_file_types: list = Field(default=[".pdf"], env="ALLOWED_FILE_TYPES")
    
    # Request Limits
    max_request_size_mb: int = Field(default=10, env="MAX_REQUEST_SIZE_MB")
    request_timeout_seconds: int = Field(default=60, env="REQUEST_TIMEOUT_SECONDS")
    
    # CORS
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        env="ALLOWED_ORIGINS"
    )
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_pii_redaction: bool = Field(default=True, env="ENABLE_PII_REDACTION")
    
    # Audit
    audit_log_dir: str = Field(default="./audit_logs", env="AUDIT_LOG_DIR")
    audit_retention_days: int = Field(default=90, env="AUDIT_RETENTION_DAYS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class ServiceSettings(BaseSettings):
    """Service-related settings"""
    
    # Service Ports
    embedding_service_port: int = Field(default=8001, env="EMBEDDING_SERVICE_PORT")
    ingestion_service_port: int = Field(default=8002, env="INGESTION_SERVICE_PORT")
    search_service_port: int = Field(default=8003, env="SEARCH_SERVICE_PORT")
    prediction_service_port: int = Field(default=8004, env="PREDICTION_SERVICE_PORT")
    opinion_service_port: int = Field(default=8005, env="OPINION_SERVICE_PORT")
    
    # External Services
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_collection_name: str = Field(
        default="supreme_court_cases",
        env="QDRANT_COLLECTION_NAME"
    )
    
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    enable_redis_cache: bool = Field(default=False, env="ENABLE_REDIS_CACHE")
    
    ocr_service_url: str = Field(
        default="http://localhost:8000",
        env="OCR_SERVICE_URL"
    )
    
    # ML Models
    embedding_model: str = Field(
        default="nlpaueb/legal-bert-base-uncased",
        env="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=768, env="EMBEDDING_DIMENSION")
    embedding_batch_size: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    llm_model: str = Field(default="gpt-4", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.3, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2048, env="LLM_MAX_TOKENS")
    
    # Search Configuration
    default_top_k: int = Field(default=10, env="DEFAULT_TOP_K")
    min_similarity_threshold: float = Field(default=0.6, env="MIN_SIMILARITY_THRESHOLD")
    
    # Prediction Configuration
    prediction_top_k: int = Field(default=20, env="PREDICTION_TOP_K")
    confidence_threshold: float = Field(default=0.6, env="CONFIDENCE_THRESHOLD")
    
    # Opinion Generation
    max_precedents: int = Field(default=5, env="MAX_PRECEDENTS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instances
security_settings = SecuritySettings()
service_settings = ServiceSettings()


def get_security_settings() -> SecuritySettings:
    """Get security settings"""
    return security_settings


def get_service_settings() -> ServiceSettings:
    """Get service settings"""
    return service_settings


def validate_production_config():
    """
    Validate configuration for production deployment.
    Raises ValueError if configuration is insecure.
    """
    if security_settings.environment == "production":
        errors = []
        
        # Check JWT secret
        if security_settings.jwt_secret_key == "change-this-secret-key-in-production":
            errors.append("JWT_SECRET_KEY must be changed in production")
        
        # Check allowed origins
        if "localhost" in security_settings.allowed_origins:
            errors.append("ALLOWED_ORIGINS should not include localhost in production")
        
        # Check OpenAI API key for opinion service
        if not service_settings.openai_api_key:
            errors.append("OPENAI_API_KEY should be set for opinion generation")
        
        if errors:
            raise ValueError(
                "Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            )


def log_configuration():
    """Log current configuration (without sensitive data)"""
    from loguru import logger
    
    logger.info("=== Configuration ===")
    logger.info(f"Environment: {security_settings.environment}")
    logger.info(f"Log Level: {security_settings.log_level}")
    logger.info(f"Rate Limit: {security_settings.rate_limit_per_minute}/min")
    logger.info(f"Max File Size: {security_settings.max_file_size_mb}MB")
    logger.info(f"Request Timeout: {security_settings.request_timeout_seconds}s")
    logger.info(f"PII Redaction: {security_settings.enable_pii_redaction}")
    logger.info(f"Qdrant: {service_settings.qdrant_host}:{service_settings.qdrant_port}")
    logger.info(f"Redis Cache: {service_settings.enable_redis_cache}")
    logger.info("====================")
