"""Notification schemas."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class NotificationBase(BaseModel):
    """Base notification schema."""
    type: str = Field(..., description="Type of notification")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    user_id: str = Field(..., description="Target user ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")

class NotificationCreate(NotificationBase):
    """Schema for creating a new notification."""
    pass

class NotificationResponse(NotificationBase):
    """Schema for notification response."""
    id: str = Field(..., alias="_id")
    created_at: datetime
    read_at: Optional[datetime]
    delivered_at: Optional[datetime]

    class Config:
        allow_population_by_field_name = True

class NotificationSettings(BaseModel):
    """User notification preferences."""
    email_enabled: bool = True
    push_enabled: bool = True
    preferences: Dict[str, Dict[str, bool]] = Field(
        default_factory=lambda: {
            "orders": {
                "status_updates": True,
                "delivery_updates": True,
                "payment_updates": True
            },
            "account": {
                "security_alerts": True,
                "profile_updates": True
            },
            "marketing": {
                "promotions": True,
                "newsletters": True
            }
        }
    )

class NotificationList(BaseModel):
    """Schema for list of notifications."""
    notifications: List[NotificationResponse]
    total: int
    unread: int
    skip: int
    limit: int