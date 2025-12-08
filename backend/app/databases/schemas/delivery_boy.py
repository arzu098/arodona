"""Delivery Boy Schema for Database Operations"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum

class DeliveryBoyStatus(str, Enum):
    """Delivery boy status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class DeliveryBoyCreate(BaseModel):
    """Schema for creating a delivery boy"""
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    email: EmailStr = Field(..., description="Email is required for login")
    password: str = Field(..., min_length=6, description="Password for login")
    address: Optional[str] = None
    zone: Optional[str] = None
    license_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    vendor_id: str = Field(..., description="ID of the vendor this delivery boy belongs to")

class DeliveryBoyUpdate(BaseModel):
    """Schema for updating a delivery boy"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, description="New password")
    address: Optional[str] = None
    zone: Optional[str] = None
    license_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    status: Optional[DeliveryBoyStatus] = None

class DeliveryBoyResponse(BaseModel):
    """Schema for delivery boy response"""
    id: str
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    zone: Optional[str] = None
    license_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    status: DeliveryBoyStatus
    vendor_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class DeliveryBoyListResponse(BaseModel):
    """Schema for delivery boy list response"""
    delivery_boys: List[DeliveryBoyResponse]
    total: int
    page: int
    per_page: int