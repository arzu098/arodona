from pydantic import BaseModel

class TwoFactorSetupResponse(BaseModel):
    """Schema for 2FA setup response"""
    secret: str
    qr_code: str
    backup_codes: list[str]

class TwoFactorVerify(BaseModel):
    """Schema for 2FA verification"""
    code: str

class TwoFactorBackupCode(BaseModel):
    """Schema for 2FA backup code usage"""
    code: str