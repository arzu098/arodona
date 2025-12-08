"""Session management schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SessionCreate(BaseModel):
    user_id: str
    refresh_token: str
    device_info: Optional[str] = None
    ip_address: str
    expires_at: datetime

class SessionResponse(BaseModel):
    id: str
    user_id: str
    device_info: Optional[str] = None
    ip_address: str
    expires_at: datetime
    revoked: bool = False
    created_at: datetime

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds