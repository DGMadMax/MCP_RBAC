"""
JWT Token Management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


def create_access_token(user_id: int, role: str, department: str) -> str:
    """
    Create JWT access token
    
    Args:
        user_id: User ID
        role: User role
        department: User department
    
    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    payload = {
        "sub": str(user_id),
        "role": role,
        "department": department,
        "exp": expire,
        "type": "access"
    }
    
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed: {str(e)}")
        raise


def create_refresh_token(user_id: int) -> str:
    """
    Create JWT refresh token (longer expiration)
    
    Args:
        user_id: User ID
    
    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(days=7)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh"
    }
    
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token
