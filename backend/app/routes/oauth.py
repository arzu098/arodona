"""
OAuth Authentication endpoints.
Handles social login with various providers.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
from app.databases.schemas.oauth import OAuthRequest, OAuthResponse
from app.databases.repositories.user import UserRepository
from app.db.connection import get_database
from app.utils.security import create_access_token
from datetime import timedelta
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth/oauth", tags=["OAuth"])

SUPPORTED_PROVIDERS = ["google", "facebook", "github"]

async def get_user_repository() -> UserRepository:
    """Dependency to get user repository"""
    db = get_database()
    return UserRepository(db)

@router.post("/{provider}", response_model=OAuthResponse)
async def oauth_login(
    provider: str,
    oauth_data: OAuthRequest,
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Handle OAuth login for various providers
    - Supports Google, Facebook, GitHub
    - Creates new user if not exists
    - Returns JWT token on success
    """
    try:
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )
        
        # Verify token with provider
        # TODO: Implement actual OAuth verification
        # For now, assume token is valid and contains user info
        
        # Example user info structure (this would come from OAuth provider)
        user_info = {
            "email": oauth_data.email,
            "first_name": oauth_data.first_name,
            "last_name": oauth_data.last_name,
            "avatar_url": oauth_data.avatar_url,
            "provider": provider,
            "provider_id": oauth_data.provider_id
        }
        
        # Get or create user
        user = await repo.get_or_create_oauth_user(
            provider=provider,
            provider_id=user_info["provider_id"],
            email=user_info["email"],
            first_name=user_info["first_name"],
            last_name=user_info["last_name"],
            avatar_url=user_info["avatar_url"]
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create/get user"
            )
        
        # Generate access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"], "user_id": str(user["_id"])},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": repo.format_user_response(user)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth error: {str(e)}"
        )