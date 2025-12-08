from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class AdminCreateUser(BaseModel):
    email: EmailStr
    password: str
    role: str = Field(pattern="^(buyer|vendor|admin|customer)$")
    first_name: str
    last_name: Optional[str] = None
    phone: Optional[str] = None
    business_details: Optional[Dict[str, Any]] = None

class AdminUpdateUser(BaseModel):
    role: Optional[str] = Field(None, pattern="^(buyer|vendor|admin|customer)$")
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")
    business_status: Optional[str] = Field(None, pattern="^(pending|approved|rejected)$")
    email_verified: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class AdminSettings(BaseModel):
    commission_rate: float = Field(ge=0, le=100)
    payment_gateway_config: Dict[str, Any]
    tax_rates: Dict[str, float]
    min_withdrawal: float
    platform_fees: Dict[str, float]
    kyc_required: bool = True
    auto_approve_vendors: bool = False

class Region(BaseModel):
    name: str
    code: str
    country: Optional[str] = None
    tax_rate: float = Field(ge=0, le=100)
    currency: str = Field(default="INR")
    timezone: Optional[str] = Field(default="UTC")
    is_active: bool = True

class AuditLog(BaseModel):
    action: str
    entity_type: str
    entity_id: str
    changes: Dict[str, Any]
    performed_by: str
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None