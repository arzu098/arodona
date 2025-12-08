"""Authentication and authorization schemas."""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False
    totp_code: Optional[str] = None

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str = "buyer"

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    user_id: str
    email: EmailStr
    role: str
    session_id: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class EmailVerification(BaseModel):
    token: str

class TwoFactorSetup(BaseModel):
    secret: str
    qr_code: str
    backup_codes: list[str]

class TwoFactorVerify(BaseModel):
    code: str

class TwoFactorEnable(BaseModel):
    code: str
    password: str