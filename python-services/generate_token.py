#!/usr/bin/env python3
"""
JWT Token Generator for Legal LLM Supreme Court System

Usage:
    python generate_token.py --user-id user123 --username john.doe --role user
    python generate_token.py --user-id admin123 --username admin --role admin
"""

import argparse
import sys
from datetime import datetime, timedelta
from jose import jwt
import os

# Default settings (can be overridden by environment variables)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here-change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))


def create_access_token(user_id: str, username: str, role: str = "user", expires_minutes: int = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: Unique user identifier
        username: Username
        role: User role (user, admin)
        expires_minutes: Token expiration time in minutes (default: from env)
    
    Returns:
        JWT token string
    """
    if expires_minutes is None:
        expires_minutes = JWT_EXPIRATION_MINUTES
    
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def main():
    parser = argparse.ArgumentParser(
        description="Generate JWT tokens for Legal LLM Supreme Court System"
    )
    parser.add_argument(
        "--user-id",
        required=True,
        help="Unique user identifier"
    )
    parser.add_argument(
        "--username",
        required=True,
        help="Username"
    )
    parser.add_argument(
        "--role",
        choices=["user", "admin"],
        default="user",
        help="User role (default: user)"
    )
    parser.add_argument(
        "--expires",
        type=int,
        default=JWT_EXPIRATION_MINUTES,
        help=f"Token expiration in minutes (default: {JWT_EXPIRATION_MINUTES})"
    )
    
    args = parser.parse_args()
    
    # Check if JWT_SECRET_KEY is the default (insecure)
    if JWT_SECRET_KEY == "your-secret-key-here-change-this-in-production":
        print("⚠️  WARNING: Using default JWT_SECRET_KEY. Set JWT_SECRET_KEY environment variable for production!")
        print()
    
    # Generate token
    token = create_access_token(
        user_id=args.user_id,
        username=args.username,
        role=args.role,
        expires_minutes=args.expires
    )
    
    # Display token information
    print("=" * 80)
    print("JWT Token Generated Successfully")
    print("=" * 80)
    print()
    print(f"User ID:   {args.user_id}")
    print(f"Username:  {args.username}")
    print(f"Role:      {args.role}")
    print(f"Expires:   {args.expires} minutes")
    print()
    print("Token:")
    print("-" * 80)
    print(token)
    print("-" * 80)
    print()
    print("Usage Example:")
    print("-" * 80)
    print(f'curl -X POST http://localhost:8003/search \\')
    print(f'  -H "Authorization: Bearer {token}" \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -d \'{{"query": "breach of contract"}}\'')
    print("-" * 80)
    print()
    
    # Role-specific examples
    if args.role == "admin":
        print("Admin Operations:")
        print("-" * 80)
        print("# Batch ingestion (admin only)")
        print(f'curl -X POST http://localhost:8002/ingest/batch \\')
        print(f'  -H "Authorization: Bearer {token}" \\')
        print(f'  -H "Content-Type: application/json" \\')
        print(f'  -d \'{{"directory_path": "/app/uploads/cases", "batch_size": 10}}\'')
        print()
        print("# Delete document (admin only)")
        print(f'curl -X DELETE http://localhost:8002/documents/abc-123 \\')
        print(f'  -H "Authorization: Bearer {token}"')
        print("-" * 80)
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
