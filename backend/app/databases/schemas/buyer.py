from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class BuyerType(str, Enum):
    """Enum for buyer type"""
    INDIVIDUAL = "individual"
    BUSINESS = "business"

class BuyerVerificationStatus(str, Enum):
    """Enum for buyer verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class BuyerBusiness(BaseModel):
    """Schema for buyer business details"""
    company_name: str
    registration_number: str
    tax_id: str
    industry: str
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    website: Optional[str] = None

class BuyerPreferences(BaseModel):
    """Schema for buyer preferences"""
    preferred_categories: List[str] = []
    preferred_vendors: List[str] = []
    newsletter_subscription: bool = False
    order_notifications: bool = True
    price_alerts: bool = False
    promotion_emails: bool = True
    language: str = "en"
    currency: str = "USD"

class BuyerCredit(BaseModel):
    """Schema for buyer credit application"""
    requested_amount: float
    purpose: str
    business_age: int
    monthly_revenue: float
    existing_credit: Optional[float] = None
    bank_statements: List[str] = []  # Document URLs
    tax_returns: List[str] = []  # Document URLs

class BuyerCreditStatus(BaseModel):
    """Schema for buyer credit status"""
    credit_limit: float
    available_credit: float
    used_credit: float
    last_review_date: datetime
    next_review_date: datetime
    status: str
    notes: Optional[str] = None

class BuyerResponse(BaseModel):
    """Schema for buyer response"""
    id: str
    user_id: str
    type: BuyerType
    business: Optional[BuyerBusiness] = None
    verification_status: Optional[BuyerVerificationStatus] = None
    preferences: BuyerPreferences
    credit_status: Optional[BuyerCreditStatus] = None
    total_orders: int
    total_spent: float
    created_at: datetime
    updated_at: datetime

class BuyerCreate(BaseModel):
    """Schema for creating a buyer"""
    type: BuyerType
    business: Optional[BuyerBusiness] = None
    preferences: Optional[BuyerPreferences] = None

class BuyerUpdate(BaseModel):
    """Schema for updating a buyer"""
    business: Optional[BuyerBusiness] = None
    preferences: Optional[BuyerPreferences] = None

class BuyerDocument(BaseModel):
    """Schema for buyer document upload"""
    type: str  # business_registration, tax_document, bank_statement, etc.
    file: str  # Base64 encoded file

class BuyerVerification(BaseModel):
    """Schema for buyer verification update"""
    status: BuyerVerificationStatus
    notes: Optional[str] = None

class BuyerListResponse(BaseModel):
    """Schema for buyer list response"""
    total: int
    page: int
    limit: int
    buyers: List[BuyerResponse]