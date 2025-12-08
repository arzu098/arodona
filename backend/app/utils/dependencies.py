"""User auth and database dependencies."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
from typing import Dict, Any, Optional
from app.utils.security import get_current_user, verify_token
from app.db.connection import get_database
from app.databases.repositories.user import UserRepository
from app.databases.repositories.vendor import VendorRepository
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that support both guest and authenticated users.
    """
    if credentials is None:
        logger.debug("No credentials provided")
        return None
    
    try:
        token = credentials.credentials
        logger.debug(f"Verifying token (first 20 chars): {token[:20]}...")
        payload = verify_token(token, "access")
        logger.debug(f"Token verified successfully, payload: {payload}")
        
        user_id = payload.get("user_id")
        email = payload.get("sub")  # JWT uses "sub" field for email, not "email"
        
        if user_id is None or email is None:
            logger.warning(f"Token missing user_id or email: user_id={user_id}, email={email}")
            return None
        
        return {
            "user_id": user_id,
            "email": email,
            "role": payload.get("role", "buyer"),
            "session_id": payload.get("session_id")
        }
    except Exception as e:
        # If token is invalid, return None instead of raising an error
        logger.error(f"Token verification failed: {type(e).__name__}: {str(e)}")
        return None

def admin_required(func):
    """Decorator for admin-only endpoints"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper

async def get_admin_user(current_user: Dict = Depends(get_current_user)):
    """Dependency for admin-only endpoints"""
    allowed_roles = ["admin", "super_admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_business_user(current_user: Dict = Depends(get_current_user)):
    """Dependency for business-only endpoints"""
    if not current_user.get("business_details"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business registration required"
        )
    return current_user

async def get_verified_business_user(current_user: Dict = Depends(get_business_user)):
    """Dependency for verified business-only endpoints"""
    business_details = current_user.get("business_details", {})
    if business_details.get("status") != "verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business verification required"
        )
    return current_user

async def get_user_repository(db = Depends(get_database)) -> UserRepository:
    """Get user repository dependency"""
    return UserRepository(db)

async def get_vendor_repository(db = Depends(get_database)) -> VendorRepository:
    """Get vendor repository dependency"""
    return VendorRepository(db)