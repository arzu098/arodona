"""Notification system schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    ORDER_STATUS = "order_status"
    PAYMENT_UPDATE = "payment_update"
    VENDOR_APPROVAL = "vendor_approval"
    PRODUCT_APPROVED = "product_approved"
    LOW_STOCK = "low_stock"
    NEW_MESSAGE = "new_message"
    SYSTEM_ALERT = "system_alert"
    PROMOTIONAL = "promotional"

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"

class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationCreate(BaseModel):
    user_id: str
    type: NotificationType
    title: str
    message: str
    channels: List[NotificationChannel]
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    channels: List[NotificationChannel]
    priority: NotificationPriority
    data: Optional[Dict[str, Any]] = None
    read: bool = False
    sent: bool = False
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class NotificationPreferences(BaseModel):
    user_id: str
    email_enabled: bool = True
    sms_enabled: bool = True
    in_app_enabled: bool = True
    push_enabled: bool = True
    order_updates: bool = True
    payment_updates: bool = True
    promotional: bool = False
    system_alerts: bool = True

class EmailTemplate(BaseModel):
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    variables: List[str] = []

class SMSTemplate(BaseModel):
    name: str
    content: str
    variables: List[str] = []

class BulkNotification(BaseModel):
    user_ids: List[str]
    type: NotificationType
    title: str
    message: str
    channels: List[NotificationChannel]
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None