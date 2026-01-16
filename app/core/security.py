"""
Security utilities for API authentication.
"""
from fastapi import HTTPException, status
from app.core.config import Settings


def require_api_key(header_value: str | None, settings: Settings) -> None:
    """
    Validate the API key from the request header.
    
    Args:
        header_value: The X-API-Key header value from the request
        settings: Application settings containing the valid API key
        
    Raises:
        HTTPException: 401 Unauthorized if the API key is missing or invalid
    """
    if header_value is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header"
        )
    
    if header_value != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
