"""
Enhanced security and authentication utilities.
Handles JWT tokens, password hashing, RBAC, 2FA, and security checks.
"""

import jwt
import pyotp
import qrcode
import io
import base64
import hashlib
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
import secrets
import string
import os
from bson import ObjectId

# Password hashing with bcrypt - configured to handle longer passwords
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer()

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    Pre-hash with SHA256 to handle passwords longer than 72 bytes (bcrypt limit).
    """
    # Pre-hash with SHA256 to handle any length password
    # This ensures we never exceed bcrypt's 72 byte limit
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(password_hash)

# Alias for backward compatibility
def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt. (Alias for hash_password)"""
    return hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    Pre-hash with SHA256 to match the hashing process.
    Falls back to direct verification for legacy passwords.
    """
    try:
        # Try with SHA256 pre-hash (new method)
        password_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        return pwd_context.verify(password_hash, hashed_password)
    except (ValueError, Exception):
        # Fallback to direct verification for legacy passwords
        # or if the password is too long
        try:
            # Truncate if necessary for bcrypt's 72-byte limit
            if len(plain_password.encode('utf-8')) > 72:
                plain_password = plain_password[:72]
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    # Extract user info from payload
    user_id = payload.get("user_id")
    email = payload.get("sub")  # JWT standard uses "sub" for subject (email in our case)
    
    if user_id is None or email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    return {
        "user_id": user_id,
        "email": email,
        "role": payload.get("role", "customer"),  # Default to customer, not buyer
        "session_id": payload.get("session_id")
    }

def require_roles(allowed_roles: List[str]):
    """Dependency to require specific roles."""
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Alias for backward compatibility
verify_admin = require_admin

def require_vendor(current_user: dict = Depends(get_current_user)) -> dict:
    """Require vendor role."""
    if current_user.get("role") != "vendor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor access required"
        )
    return current_user

# Two-Factor Authentication utilities
def generate_2fa_secret() -> str:
    """Generate a new TOTP secret."""
    return pyotp.random_base32()

def generate_qr_code(secret: str, user_email: str, app_name: str = "Adorona") -> str:
    """Generate QR code for TOTP setup."""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email,
        issuer_name=app_name
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def verify_totp_code(secret: str, code: str) -> bool:
    """Verify TOTP code."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)

def generate_backup_codes(count: int = 10) -> List[str]:
    """Generate backup codes for 2FA."""
    codes = []
    for _ in range(count):
        code = ''.join(secrets.choice(string.digits) for _ in range(8))
        codes.append(f"{code[:4]}-{code[4:]}")
    return codes

# Token and session utilities
def generate_reset_token() -> str:
    """Generate a secure random token for password reset."""
    return secrets.token_urlsafe(32)

def generate_verification_token() -> str:
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    """Hash a token for secure storage."""
    return pwd_context.hash(token)

def verify_hashed_token(plain_token: str, hashed_token: str) -> bool:
    """Verify a token against its hash."""
    return pwd_context.verify(plain_token, hashed_token)

# Security checks
def is_strong_password(password: str) -> tuple[bool, List[str]]:
    """Check if password meets security requirements."""
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        issues.append("Password must contain at least one special character")
    
    return len(issues) == 0, issues

def validate_object_id(obj_id: str) -> bool:
    """Validate MongoDB ObjectId format."""
    try:
        ObjectId(obj_id)
        return True
    except:
        return False

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove path separators and dangerous characters
    unsafe_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

# Rate limiting helpers
def generate_rate_limit_key(user_id: str, endpoint: str) -> str:
    """Generate rate limiting key."""
    return f"rate_limit:{user_id}:{endpoint}"
