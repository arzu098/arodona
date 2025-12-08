from datetime import datetime, timedelta
from typing import Optional
import jwt
from app.config import SECRET_KEY, PASSWORD_RESET_EXPIRE_MINUTES

def create_password_reset_token(email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create password reset token"""
    to_encode = {"sub": email, "type": "password_reset"}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY + "_reset", algorithm="HS256")
    return encoded_jwt

def verify_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email"""
    try:
        payload = jwt.decode(token, SECRET_KEY + "_reset", algorithms=["HS256"])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None