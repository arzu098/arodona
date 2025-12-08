"""Enhanced authentication routes with 2FA support."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from app.databases.schemas.auth import (
    UserLogin, UserRegister, TokenResponse, TokenRefresh,
    PasswordResetRequest, PasswordReset, EmailVerification,
    TwoFactorSetup, TwoFactorVerify, TwoFactorEnable
)
from app.databases.schemas.users import UserResponse
from app.databases.repositories.user import UserRepository
from app.databases.repositories.session import SessionRepository
from app.utils.security import (
    create_access_token, create_refresh_token, verify_password, 
    get_current_user, hash_password, verify_token,
    generate_2fa_secret, generate_qr_code, verify_totp_code,
    generate_backup_codes, generate_reset_token, generate_verification_token,
    is_strong_password
)
from app.db.connection import get_database
from typing import Dict
from datetime import datetime, timedelta
import secrets

router = APIRouter(prefix="/api/auth/v2", tags=["Authentication V2"])

async def get_user_repository() -> UserRepository:
    """Dependency to get user repository"""
    db = get_database()
    return UserRepository(db)

async def get_session_repository() -> SessionRepository:
    """Dependency to get session repository"""
    db = get_database()
    return SessionRepository(db)

def get_client_info(request: Request) -> Dict[str, str]:
    """Extract client information from request."""
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "device_info": request.headers.get("user-agent", "unknown")
    }

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Enhanced user registration endpoint."""
    
    # Check if user already exists
    existing_user = await user_repo.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Validate password strength
    is_valid, issues = is_strong_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password requirements not met: {'; '.join(issues)}"
        )
    
    # Create user
    user_create_data = {
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "phone": user_data.phone,
        "role": user_data.role
    }
    
    user = await user_repo.create_user(user_create_data)
    
    # Generate email verification token
    verification_token = generate_verification_token()
    # TODO: Store verification token and send email
    
    return user_repo.format_user_response(user)

@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    user_repo: UserRepository = Depends(get_user_repository),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """Enhanced user login endpoint with 2FA support."""
    
    # Get user by email
    user = await user_repo.get_user_by_email(user_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(user_data.password, user.get("password_hash", user.get("password", ""))):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if 2FA is enabled
    two_factor = user.get("two_factor", {})
    if two_factor.get("enabled"):
        if not user_data.totp_code:
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="2FA code required",
                headers={"X-2FA-Required": "true"}
            )
        
        # Verify 2FA code
        if not verify_totp_code(two_factor["secret"], user_data.totp_code):
            # Check backup codes
            backup_valid = False
            if user_data.totp_code in two_factor.get("backup_codes", []):
                backup_valid = True
                await user_repo.use_backup_code(str(user["_id"]), user_data.totp_code)
            
            if not backup_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid 2FA code"
                )
    
    # Create tokens
    client_info = get_client_info(request)
    session_id = secrets.token_urlsafe(32)
    
    token_data = {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user.get("role", "buyer"),
        "session_id": session_id
    }
    
    expires_delta = timedelta(days=30) if user_data.remember_me else timedelta(days=1)
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Create session
    session_data = {
        "user_id": str(user["_id"]),
        "refresh_token": refresh_token,
        "ip_address": client_info["ip_address"],
        "device_info": client_info["device_info"],
        "expires_at": datetime.utcnow() + expires_delta
    }
    
    created_session_id = await session_repo.create_session(session_data)
    
    # Update last login
    await user_repo.update_last_login(str(user["_id"]))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800  # 30 minutes
    )

@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_2fa(
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Setup 2FA for user."""
    
    secret = generate_2fa_secret()
    qr_code = generate_qr_code(secret, current_user["email"])
    backup_codes = generate_backup_codes()
    
    # Store 2FA setup (not enabled yet)
    await user_repo.setup_2fa(current_user["user_id"], secret, backup_codes)
    
    return TwoFactorSetup(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes
    )

@router.post("/2fa/enable")
async def enable_2fa(
    verify_data: TwoFactorEnable,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Enable 2FA after verification."""
    
    # Verify password
    user = await user_repo.get_user_by_id(current_user["user_id"])
    if not user or not verify_password(verify_data.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Get 2FA secret
    secret = await user_repo.get_2fa_secret(current_user["user_id"])
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not set up. Please run setup first."
        )
    
    # Verify TOTP code
    if not verify_totp_code(secret, verify_data.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA code"
        )
    
    # Enable 2FA
    await user_repo.enable_2fa(current_user["user_id"])
    
    return {"message": "2FA enabled successfully"}

@router.post("/2fa/verify")
async def verify_2fa(
    verify_data: TwoFactorVerify,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Verify 2FA code."""
    
    user = await user_repo.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    two_factor = user.get("two_factor", {})
    if not two_factor.get("enabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not enabled"
        )
    
    # Verify TOTP code
    if verify_totp_code(two_factor["secret"], verify_data.code):
        return {"message": "2FA code verified"}
    
    # Check backup codes
    if await user_repo.verify_backup_code(current_user["user_id"], verify_data.code):
        return {"message": "Backup code verified"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid 2FA code"
    )

@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """Logout user and revoke session."""
    
    session_id = current_user.get("session_id")
    if session_id:
        await session_repo.revoke_session(session_id)
    
    return {"message": "Successfully logged out"}

@router.post("/logout-all")
async def logout_all(
    current_user: dict = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """Logout from all devices."""
    
    revoked_count = await session_repo.revoke_all_user_sessions(current_user["user_id"])
    
    return {"message": f"Logged out from {revoked_count} sessions"}