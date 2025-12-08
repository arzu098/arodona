from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Session(BaseModel):
    """Schema for user session"""
    user_id: str
    token: str
    device: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    is_active: bool = True

class SessionResponse(BaseModel):
    """Schema for session response"""
    id: str
    device: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    is_active: bool