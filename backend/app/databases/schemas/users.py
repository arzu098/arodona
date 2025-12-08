"""Enhanced user schemas with comprehensive fields."""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    VENDOR = "vendor"
    CUSTOMER = "customer"
    BUYER = "buyer"  # Legacy support

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class KYCStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class NotificationPreferences(BaseModel):
    email: bool = True
    sms: bool = True
    in_app: bool = True

class UserPreferences(BaseModel):
    notifications: NotificationPreferences = NotificationPreferences()
    language: str = "en"
    currency: str = "USD"

class KYCInfo(BaseModel):
    status: KYCStatus = KYCStatus.PENDING
    documents: List[str] = []
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    rejection_reason: Optional[str] = None

class TwoFactorAuth(BaseModel):
    enabled: bool = False
    secret: Optional[str] = None
    backup_codes: List[str] = []

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    preferences: Optional[UserPreferences] = None

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole
    status: UserStatus
    email_verified: bool = False
    phone_verified: bool = False
    avatar: Optional[str] = None
    preferences: UserPreferences
    kyc: KYCInfo
    two_factor: TwoFactorAuth
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class UserPasswordReset(BaseModel):
    token: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v