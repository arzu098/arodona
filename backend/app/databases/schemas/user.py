from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str
    first_name: str
    last_name: Optional[str] = ""  # Optional field
    phone: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[str] = "customer"  # Default to customer, only super_admin can create other roles

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[str] = "customer"  # customer, vendor, admin, super_admin
    created_at: datetime

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str
    user: UserResponse

class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    user: Optional[UserResponse] = None
    require_2fa: Optional[bool] = False
    temp_token: Optional[str] = None

class RegisterResponse(BaseModel):
    """Schema for register response (without token)"""
    message: str
    user: UserResponse

class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None


class AvatarUpdate(BaseModel):
    """Schema for updating user avatar"""
    avatar: str  # Base64 encoded image string

class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    message: str
    user: UserResponse

class UserListResponse(BaseModel):
    """Schema for user list response"""
    total: int
    skip: int
    limit: int
    users: List[UserResponse]

class UserSearchRequest(BaseModel):
    """Schema for user search request"""
    query: str
    skip: int = 0
    limit: int = 10

class UserUpdateAdmin(BaseModel):
    """Schema for admin updating user profile"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class SuperAdminCreateUser(BaseModel):
    """Schema for super admin creating any user type"""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str  # super_admin can create: admin, vendor, customer
    avatar: Optional[str] = None

class SuperAdminInitialSetup(BaseModel):
    """Schema for creating the first super admin"""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    secret_key: str  # Special key to prevent unauthorized super admin creation

class AdminCreateVendor(BaseModel):
    """Schema for admin creating vendor accounts"""
    email: EmailStr
    password: str
    first_name: str
    last_name: Optional[str] = ""  # Optional field
    phone: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    