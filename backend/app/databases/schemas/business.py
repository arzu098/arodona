from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class BusinessType(str, Enum):
    """Business types"""
    RETAIL = "retail"
    WHOLESALE = "wholesale"
    MANUFACTURER = "manufacturer"
    SERVICE = "service"
    OTHER = "other"

class BusinessAddress(BaseModel):
    """Business address model"""
    street_address: str
    city: str
    state: str
    country: str
    postal_code: str
    is_primary: bool = True

class BusinessRegistration(BaseModel):
    """Business registration request model"""
    business_name: str
    business_type: BusinessType
    registration_number: str
    tax_id: str
    addresses: List[BusinessAddress]
    phone: str
    email: EmailStr
    website: Optional[str] = None
    description: Optional[str] = None

class BusinessResponse(BaseModel):
    """Business registration response model"""
    message: str
    business: dict

class DocumentType(str, Enum):
    """KYC document types"""
    ID_PROOF = "id_proof"
    ADDRESS_PROOF = "address_proof"
    BUSINESS_LICENSE = "business_license"
    TAX_CERTIFICATE = "tax_certificate"
    OTHER = "other"

class KYCDocumentUpload(BaseModel):
    """KYC document upload request model"""
    document_type: DocumentType
    file: str  # Base64 encoded file
    description: Optional[str] = None

class KYCStatusResponse(BaseModel):
    """KYC status response model"""
    user_id: str
    documents: List[dict]
    status: str
    last_updated: Optional[datetime] = None