"""Vendor management schemas."""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class BusinessType(str, Enum):
    JEWELRY = "jewelry"
    ACCESSORIES = "accessories"
    LUXURY = "luxury"
    CUSTOM = "custom"

class VendorStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    REJECTED = "rejected"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# Alias for backward compatibility
VendorApprovalStatus = ApprovalStatus

class Address(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str

class ContactInfo(BaseModel):
    phone: str
    email: EmailStr
    website: Optional[str] = None

class StorefrontSettings(BaseModel):
    logo: Optional[str] = None
    banner: Optional[str] = None
    description: Optional[str] = None
    theme: Optional[Dict[str, Any]] = None

# Alias for backward compatibility
VendorStorefront = StorefrontSettings

class VendorApproval(BaseModel):
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

class VendorApplication(BaseModel):
    """Vendor application data"""
    business_name: str
    business_type: BusinessType
    business_registration: Optional[str] = None
    tax_id: Optional[str] = None
    address: Address
    contact: ContactInfo
    status: ApprovalStatus = ApprovalStatus.PENDING
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None

class VendorRatings(BaseModel):
    average: float = 0.0
    count: int = 0

class VendorPerformance(BaseModel):
    total_sales: float = 0.0
    orders_fulfilled: int = 0
    response_time_hours: float = 24.0

class VendorCreate(BaseModel):
    business_name: str
    business_type: BusinessType
    business_description: str
    business_registration_number: Optional[str] = None
    tax_id: str
    contact_person: str
    contact_email: EmailStr
    contact_phone: str
    business_address: Address
    bank_details: Optional[Dict[str, Any]] = None
    
    @validator('business_name')
    def validate_business_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Business name must be at least 2 characters')
        return v.strip()

class VendorUpdate(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[BusinessType] = None
    business_description: Optional[str] = None
    business_registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    business_address: Optional[Dict[str, Any]] = None
    bank_details: Optional[Dict[str, Any]] = None
    storefront: Optional[Dict[str, Any]] = None

class VendorResponse(BaseModel):
    id: str
    user_id: str
    business_name: str
    business_type: BusinessType
    business_description: Optional[str] = None
    business_registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    business_address: Optional[Dict[str, Any]] = None
    bank_details: Optional[Dict[str, Any]] = None
    status: VendorStatus = VendorStatus.PENDING
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    application_date: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    documents: Optional[list] = []
    storefront: Optional[Dict[str, Any]] = None
    performance: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    managed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VendorApprovalUpdate(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None