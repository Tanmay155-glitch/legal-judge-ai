"""
Security utilities for Legal LLM Supreme Court System
Implements authentication, authorization, and security controls
"""

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import re
import hashlib
from pathlib import Path
from loguru import logger

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()


# ============================================================================
# FIX VULN-001: Authentication
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Verify JWT token and return user information.
    Raises HTTPException if token is invalid.
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check token expiration
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
            "exp": exp
        }
    
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(required_role: str):
    """
    Dependency to require specific role.
    Usage: user = Depends(require_role("admin"))
    """
    async def role_checker(user: Dict = Depends(verify_token)):
        if required_role not in user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return user
    return role_checker


# ============================================================================
# FIX VULN-004: Path Traversal Protection
# ============================================================================

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
        ValueError: If path is outside allowed base or invalid
    """
    try:
        # Resolve to absolute path
        path = Path(directory_path).resolve()
        base = Path(allowed_base).resolve()
        
        # Check if path is within allowed base
        try:
            path.relative_to(base)
        except ValueError:
            raise ValueError(f"Path traversal detected: {directory_path}")
        
        # Additional security checks
        if not path.exists():
            raise ValueError(f"Path does not exist: {directory_path}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        # Check for symlinks (potential security risk)
        if path.is_symlink():
            raise ValueError(f"Symlinks not allowed: {directory_path}")
        
        return path
    
    except Exception as e:
        logger.warning(f"Path validation failed: {e}")
        raise ValueError(f"Invalid path: {str(e)}")


# ============================================================================
# FIX VULN-013: PII Redaction in Logs
# ============================================================================

def redact_pii(text: str) -> str:
    """
    Redact personally identifiable information from text.
    
    Redacts:
    - Email addresses
    - Phone numbers
    - SSN
    - Credit card numbers
    - IP addresses
    """
    if not text:
        return text
    
    # Email addresses
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL_REDACTED]',
        text
    )
    
    # Phone numbers (various formats)
    text = re.sub(
        r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
        '[PHONE_REDACTED]',
        text
    )
    
    # SSN
    text = re.sub(
        r'\b\d{3}-\d{2}-\d{4}\b',
        '[SSN_REDACTED]',
        text
    )
    
    # Credit card numbers
    text = re.sub(
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        '[CARD_REDACTED]',
        text
    )
    
    # IP addresses
    text = re.sub(
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        '[IP_REDACTED]',
        text
    )
    
    return text


def safe_log(message: str, data: Dict[str, Any] = None, level: str = "info"):
    """
    Log message with PII redaction.
    
    Args:
        message: Log message
        data: Optional data dictionary
        level: Log level (info, warning, error)
    """
    safe_message = redact_pii(message)
    
    if data:
        safe_data = {
            k: redact_pii(str(v)) if isinstance(v, str) else v
            for k, v in data.items()
        }
        log_msg = f"{safe_message} | Data: {safe_data}"
    else:
        log_msg = safe_message
    
    if level == "info":
        logger.info(log_msg)
    elif level == "warning":
        logger.warning(log_msg)
    elif level == "error":
        logger.error(log_msg)
    else:
        logger.debug(log_msg)


# ============================================================================
# FIX VULN-006: Prompt Injection Protection
# ============================================================================

def sanitize_llm_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize input for LLM to prevent prompt injection.
    
    Args:
        text: User input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'ignore\s+previous\s+instructions',
        r'ignore\s+all\s+previous',
        r'disregard\s+previous',
        r'forget\s+previous',
        r'system\s*:',
        r'<\|im_start\|>',
        r'<\|im_end\|>',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


# ============================================================================
# FIX VULN-008: File Upload Validation
# ============================================================================

async def validate_pdf_file(file_content: bytes, filename: str) -> bytes:
    """
    Validate uploaded PDF file.
    
    Args:
        file_content: File content bytes
        filename: Original filename
        
    Returns:
        Validated file content
        
    Raises:
        HTTPException: If file is invalid
    """
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Check file size
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Check file extension
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Check PDF magic number (file signature)
    if not file_content.startswith(b'%PDF'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file format"
        )
    
    # Check for embedded executables (basic check)
    dangerous_signatures = [
        b'MZ',  # Windows executable
        b'\x7fELF',  # Linux executable
        b'#!/',  # Script
    ]
    
    for sig in dangerous_signatures:
        if sig in file_content[:1024]:  # Check first 1KB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File contains potentially dangerous content"
            )
    
    return file_content


# ============================================================================
# FIX VULN-011: Secure Error Messages
# ============================================================================

def get_safe_error_message(error: Exception, include_details: bool = False) -> str:
    """
    Get user-safe error message.
    
    Args:
        error: Original exception
        include_details: Whether to include details (only for development)
        
    Returns:
        Safe error message for users
    """
    # Log full error internally
    logger.error(f"Error occurred: {str(error)}", exc_info=True)
    
    # Return generic message to users
    if include_details and os.getenv("ENVIRONMENT") == "development":
        return f"An error occurred: {str(error)}"
    else:
        return "An internal error occurred. Please contact support with your request ID."


# ============================================================================
# Request ID Generation (for error tracking)
# ============================================================================

def generate_request_id() -> str:
    """Generate unique request ID for tracking"""
    import uuid
    return str(uuid.uuid4())


# ============================================================================
# Input Sanitization
# ============================================================================

def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    General input sanitization.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Truncate
    text = text[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '{', '}', '|', '\\', '^', '`', '\x00']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


# ============================================================================
# Authorization Helpers
# ============================================================================

def check_document_ownership(user_id: str, document_id: str) -> bool:
    """
    Check if user owns the document.
    
    Args:
        user_id: User ID
        document_id: Document ID
        
    Returns:
        True if user owns document, False otherwise
    """
    # TODO: Implement actual ownership check with database
    # For now, return True (implement with your database)
    return True


async def require_document_ownership(
    document_id: str,
    user: Dict = Depends(verify_token)
) -> Dict:
    """
    Dependency to require document ownership.
    """
    if not check_document_ownership(user["user_id"], document_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this document"
        )
    return user


# ============================================================================
# FIX VULN-005: SQL/NoSQL Injection Protection
# ============================================================================

def sanitize_query_filter(filter_value: str) -> str:
    """
    Sanitize filter values for database queries to prevent injection.
    
    Args:
        filter_value: Filter value from user input
        
    Returns:
        Sanitized filter value
    """
    if not filter_value:
        return ""
    
    # Remove potentially dangerous characters for NoSQL injection
    dangerous_patterns = [
        r'\$',  # MongoDB operators
        r'\{',  # JSON injection
        r'\}',
        r'\[',
        r'\]',
        r';',   # SQL injection
        r'--',  # SQL comments
        r'/\*',  # SQL comments
        r'\*/',
        r'xp_',  # SQL Server extended procedures
        r'sp_',  # SQL Server stored procedures
    ]
    
    sanitized = filter_value
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized)
    
    # Limit length
    sanitized = sanitized[:100]
    
    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def sanitize_search_query(query: str, max_length: int = 1000) -> str:
    """
    Sanitize search query to prevent injection attacks.
    
    Args:
        query: Search query from user
        max_length: Maximum query length
        
    Returns:
        Sanitized query
    """
    if not query:
        return ""
    
    # Truncate to max length
    query = query[:max_length]
    
    # Remove SQL/NoSQL injection patterns
    injection_patterns = [
        r';\s*DROP\s+TABLE',
        r';\s*DELETE\s+FROM',
        r';\s*UPDATE\s+',
        r';\s*INSERT\s+INTO',
        r'UNION\s+SELECT',
        r'\$where',
        r'\$regex',
        r'\$ne',
        r'\$gt',
        r'\$lt',
    ]
    
    for pattern in injection_patterns:
        query = re.sub(pattern, '', query, flags=re.IGNORECASE)
    
    # Remove control characters
    query = ''.join(char for char in query if ord(char) >= 32 or char in '\n\r\t')
    
    # Normalize whitespace
    query = re.sub(r'\s+', ' ', query).strip()
    
    return query


def validate_year_range(year_range: Optional[tuple]) -> Optional[tuple]:
    """
    Validate year range to prevent injection.
    
    Args:
        year_range: Tuple of (start_year, end_year)
        
    Returns:
        Validated year range or None
    """
    if not year_range:
        return None
    
    try:
        start_year, end_year = year_range
        
        # Validate years are integers
        start_year = int(start_year)
        end_year = int(end_year)
        
        # Validate reasonable range
        if start_year < 1900 or start_year > 2100:
            raise ValueError("Invalid start year")
        if end_year < 1900 or end_year > 2100:
            raise ValueError("Invalid end year")
        if start_year > end_year:
            raise ValueError("Start year must be before end year")
        
        return (start_year, end_year)
    
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid year range: {year_range}, error: {e}")
        return None
