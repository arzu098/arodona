from fastapi import APIRouter, HTTPException, Depends, status
from datetime import timedelta
from datetime import datetime
from fastapi import Request
from app.databases.schemas.user import UserRegister, UserLogin, LoginResponse, RegisterResponse
from app.databases.schemas.auth import (
    TokenRefresh,
    TokenResponse,
    PasswordReset,
    PasswordResetRequest,
)
from app.databases.schemas.two_factor import TwoFactorSetupResponse, TwoFactorVerify, TwoFactorBackupCode
from app.utils.password_reset import create_password_reset_token, verify_reset_token
from app.utils.two_factor import (
    generate_totp_secret,
    generate_backup_codes,
    get_totp_uri,
    generate_qr_code,
    verify_totp_code
)
from app.databases.schemas.session import SessionResponse
from app.databases.repositories.user import UserRepository
from app.databases.repositories.session import SessionRepository
from app.db.connection import get_database
from app.utils.security import create_access_token, get_current_user, verify_token
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

async def get_user_repository() -> UserRepository:
    """Dependency to get user repository"""
    db = get_database()
    return UserRepository(db)

async def get_session_repository() -> SessionRepository:
    """Dependency to get session repository"""
    db = get_database()
    return SessionRepository(db)

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, repo: UserRepository = Depends(get_user_repository)):
    """
    Register a new customer user (public registration)
    - **email**: User email
    - **password**: User password
    - **first_name**: User first name
    - **last_name**: User last name
    - **phone**: User phone number (optional)
    
    Note: Public registration only allows customer accounts.
    Admin accounts must be created by Super Admin.
    Vendor accounts must be created by Admin or Super Admin.
    """
    # Check if user already exists
    if await repo.user_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Restrict public registration to customer role only
    if user_data.role and user_data.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration only allows customer accounts. Contact administrator for other account types."
        )

    # Create new customer user
    user = await repo.create_user(
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role="customer"  # Force customer role for public registration
    )

    return {
        "message": "Customer account registered successfully",
        "user": repo.format_user_response(user)
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token: TokenRefresh, current_user: dict = Depends(get_current_user)):
    """
    Refresh access token
    - **access_token**: Current access token to refresh
    """
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": current_user["sub"], 
            "user_id": current_user["user_id"],
            "role": current_user.get("role")
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Logout user by revoking all their active sessions
    """
    # Revoke all sessions for the user
    await session_repo.revoke_user_sessions(current_user["user_id"])
    
    return {"message": "Successfully logged out"}

@router.post("/password/forgot")
async def forgot_password(
    request: PasswordResetRequest,
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Request a password reset token
    - **email**: User's email address
    """
    user = await repo.get_user_by_email(request.email)
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link will be sent"}

    # Generate password reset token
    reset_token = create_password_reset_token(request.email)

    # TODO: Send email with reset token
    # For development, just return the token
    return {"message": "Reset token generated", "token": reset_token}

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user: dict = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Setup 2FA for user
    - Generates secret
    - Creates QR code
    - Generates backup codes
    User must verify a code to enable 2FA
    """
    # Generate secret and backup codes
    secret = generate_totp_secret()
    backup_codes = generate_backup_codes()

    # Get user email
    user = await repo.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Generate QR code
    uri = get_totp_uri(secret, user["email"])
    qr_code = generate_qr_code(uri)

    # Save 2FA data
    if not await repo.setup_2fa(current_user["user_id"], secret, backup_codes):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup 2FA"
        )

    return {
        "secret": secret,
        "qr_code": qr_code,
        "backup_codes": backup_codes
    }

@router.post("/2fa/verify")
async def verify_2fa(
    request: TwoFactorVerify,
    current_user: dict = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Verify 2FA code and enable 2FA
    - **code**: Current TOTP code
    """
    secret = await repo.get_2fa_secret(current_user["user_id"])
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not setup"
        )

    if not verify_totp_code(secret, request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code"
        )

    if not await repo.enable_2fa(current_user["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable 2FA"
        )

    return {"message": "2FA enabled successfully"}

@router.post("/2fa/backup")
async def use_backup_code(
    request: TwoFactorBackupCode,
    current_user: dict = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Use 2FA backup code
    - **code**: Backup code
    """
    if not await repo.verify_backup_code(current_user["user_id"], request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup code"
        )

    # Generate new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user["sub"], "user_id": current_user["user_id"]},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/password/reset")
async def reset_password(
    request: PasswordReset,
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Reset password using the reset token
    - **token**: Password reset token
    - **new_password**: New password
    """
    email = verify_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

    # Update password
    user = await repo.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password and revoke all sessions
    updated = await repo.update_password(str(user["_id"]), request.new_password)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )

    # Revoke all sessions for security
    session_repo = SessionRepository(get_database())
    await session_repo.revoke_user_sessions(str(user["_id"]))

    return {"message": "Password updated successfully"}

@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    current_user: dict = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    List all active sessions for the current user
    """
    sessions = await session_repo.get_active_sessions(current_user["user_id"])
    return [await session_repo.format_session_response(session) for session in sessions]

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Revoke a specific session
    """
    success = await session_repo.revoke_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already revoked"
        )
    return {"message": "Session successfully revoked"}

@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    repo: UserRepository = Depends(get_user_repository),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Login user and return access token
    - **email**: User email
    - **password**: User password
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Find user by email (get raw document with password hash)
    user = await repo.get_user_for_auth(credentials.email)
    
    logger.info(f"Login attempt for email: {credentials.email}")
    logger.info(f"User found: {user is not None}")
    
    if not user:
        logger.warning(f"User not found: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    logger.info(f"User role: {user.get('role')}, status: {user.get('status')}")
    logger.info(f"Has password_hash: {bool(user.get('password_hash'))}")
    logger.info(f"Password received length: {len(credentials.password)}")
    logger.info(f"Password received (first 5 chars): {credentials.password[:5] if len(credentials.password) > 0 else 'EMPTY'}")
    logger.info(f"Password hash (first 30 chars): {user.get('password_hash', '')[:30]}...")
    
    # Verify password
    from app.utils.security import verify_password
    password_valid = verify_password(credentials.password, user.get("password_hash", ""))
    logger.info(f"Password valid: {password_valid}")
    
    if not password_valid:
        logger.warning(f"Invalid password for user: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user account is active
    user_status = user.get("status", "active")
    is_active = user.get("is_active", True)
    
    # For vendors, allow login even if status is inactive (vendor approval is separate from user account)
    # Their vendor status will be checked on the dashboard
    is_vendor_pending = (user.get("role") == "vendor" and user_status == "inactive")
    
    if not is_vendor_pending:
        # Check account status for non-vendors or vendors with other status issues
        if user_status == "inactive" or not is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is inactive. Please contact support."
            )
        
        if user_status == "suspended":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been suspended. Please contact support."
            )

    # Check if 2FA is enabled
    if "two_factor" in user and user["two_factor"].get("enabled"):
        # Generate temporary token for 2FA verification
        temp_token = create_access_token(
            data={
                "sub": user["email"],
                "user_id": str(user["_id"]),
                "temp_auth": True
            },
            expires_delta=timedelta(minutes=5)  # Short-lived token for 2FA
        )
        
        return {
            "require_2fa": True,
            "temp_token": temp_token
        }
    else:
        # Generate full access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user["email"], 
                "user_id": str(user["_id"]),
                "role": user["role"]
            },
            expires_delta=access_token_expires
        )

        # Create session
        session_data = {
            "user_id": str(user["_id"]),
            "token": access_token,
            "device": request.headers.get("User-Agent"),
            "ip_address": request.client.host,
            "expires_at": datetime.utcnow() + access_token_expires
        }
        await session_repo.create_session(session_data)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": repo.format_user_response(user)
        }
