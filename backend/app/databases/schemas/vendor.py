from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class VendorStatus(str, Enum):
    """Enum for vendor status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"
    INACTIVE = "inactive"

class VendorApprovalStatus(str, Enum):
    """Enum for vendor approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class BusinessType(str, Enum):
    """Enum for business types"""
    MANUFACTURER = "manufacturer"
    WHOLESALER = "wholesaler"
    RETAILER = "retailer"
    DESIGNER = "designer"
    ARTISAN = "artisan"
    DISTRIBUTOR = "distributor"
    JEWELRY = "jewelry"
    ACCESSORIES = "accessories"
    LUXURY = "luxury"
    CUSTOM = "custom"
    OTHER = "other"

class DocumentType(str, Enum):
    """Enum for document types"""
    BUSINESS_LICENSE = "business_license"
    TAX_CERTIFICATE = "tax_certificate"
    INSURANCE_CERTIFICATE = "insurance_certificate"
    PRODUCT_CATALOG = "product_catalog"
    QUALITY_CERTIFICATE = "quality_certificate"
    OTHER = "other"

class Address(BaseModel):
    """Schema for address"""
    street: str
    city: str
    state: str
    postal_code: str
    country: str

class VendorStorefront(BaseModel):
    """Schema for vendor storefront"""
    store_name: str
    description: str
    logo: Optional[str] = None
    banner: Optional[str] = None
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

class VendorDocument(BaseModel):
    """Schema for vendor documents"""
    type: DocumentType
    url: str
    upload_date: datetime
    verified: bool = False
    notes: Optional[str] = None

class VendorCreate(BaseModel):
    """Schema for creating vendor application"""
    business_name: str = Field(..., min_length=2, max_length=200)
    business_type: BusinessType
    business_description: str = Field(..., min_length=10, max_length=1000)
    business_registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: str = Field(..., min_length=5, max_length=50)
    contact_person: str = Field(..., min_length=2, max_length=100)
    contact_email: EmailStr
    contact_phone: str = Field(..., max_length=20)
    business_address: Address
    bank_details: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "business_name": "Elegant Jewelry Co.",
                "business_type": "retailer",
                "business_description": "Premium handcrafted jewelry with modern designs",
                "business_registration_number": "REG123456",
                "tax_id": "123456789",
                "contact_person": "John Doe",
                "contact_email": "contact@elegantjewelry.com",
                "contact_phone": "+1-555-0123",
                "business_address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA"
                }
            }
        }

class VendorApplication(BaseModel):
    """Schema for vendor application"""
    business_name: str
    business_type: BusinessType
    tax_id: str
    registration_number: Optional[str] = None
    storefront: VendorStorefront
    documents: Optional[List[VendorDocument]] = None

class VendorResponse(BaseModel):
    """Schema for vendor response"""
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
    approval_status: VendorApprovalStatus = VendorApprovalStatus.PENDING
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
        populate_by_name = True
        extra = "ignore"  # Ignore extra fields from MongoDB
        use_enum_values = True  # Serialize enums as their values

class VendorUpdate(BaseModel):
    """Schema for updating vendor"""
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

class VendorApproval(BaseModel):
    """Schema for vendor approval/rejection"""
    status: VendorStatus
    notes: Optional[str] = None

class VendorAsset(BaseModel):
    """Schema for vendor asset upload"""
    type: str  # logo, banner, document
    file: str  # Base64 encoded file

class VendorRating(BaseModel):
    """Schema for vendor rating"""
    rating: float
    total_orders: int
    fulfilled_orders: int
    cancelled_orders: int
    total_revenue: float
    avg_fulfillment_time: Optional[float] = None
    reviews: List[dict]  # Simplified for now

class VendorDashboard(BaseModel):
    """Schema for vendor dashboard"""
    total_orders: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    total_revenue: float
    today_revenue: float
    today_orders: int
    recent_orders: List[dict]  # Simplified for now
    revenue_chart: List[dict]  # Simplified for now
    top_products: List[dict]  # Simplified for now

class VendorPayout(BaseModel):
    """Schema for vendor payout request"""
    amount: float
    currency: str = "USD"
    bank_account: str
    notes: Optional[str] = None

class VendorListResponse(BaseModel):
    """Schema for vendor list response"""
    total: int
    page: int
    limit: int
    vendors: List[VendorResponse]