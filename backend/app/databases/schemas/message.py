"""Message schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class MessageBase(BaseModel):
    """Base message schema."""
    content: str = Field(..., description="Message content")
    thread_id: Optional[str] = Field(None, description="Thread/conversation ID")
    recipient_id: str = Field(..., description="Recipient user ID")
    message_type: str = Field("text", description="Message type (text/image)")
    metadata: Optional[dict] = Field(None, description="Additional message metadata")

class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    pass

class MessageResponse(MessageBase):
    """Schema for message response."""
    id: str = Field(..., alias="_id")
    sender_id: str
    created_at: datetime
    read_at: Optional[datetime]
    delivered_at: Optional[datetime]
    attachments: List[str] = []

    class Config:
        allow_population_by_field_name = True

class ThreadCreate(BaseModel):
    """Schema for creating a new message thread."""
    title: Optional[str]
    participants: List[str]
    metadata: Optional[dict]

class ThreadResponse(BaseModel):
    """Schema for thread response."""
    id: str = Field(..., alias="_id")
    title: Optional[str]
    participants: List[str]
    created_at: datetime
    updated_at: datetime
    last_message: Optional[MessageResponse]
    metadata: Optional[dict]
    unread_count: int

    class Config:
        allow_population_by_field_name = True

class ThreadList(BaseModel):
    """Schema for list of threads."""
    threads: List[ThreadResponse]
    total: int
    skip: int
    limit: int