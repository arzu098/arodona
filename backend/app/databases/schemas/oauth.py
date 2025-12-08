from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class OAuthRequest(BaseModel):
    """Request model for OAuth login"""
    email: EmailStr
    first_name: str
    last_name: str
    provider_id: str
    avatar_url: Optional[str] = None
    access_token: str

class OAuthResponse(BaseModel):
    """Response model for OAuth login"""
    access_token: str
    token_type: str
    user: dict