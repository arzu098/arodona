"""User Management API routes with KYC workflows and profile management."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer
from typing import Optional, List, Dict, Any
import os
from datetime import datetime

from ..databases.repositories.user import UserRepository
from ..databases.schemas.users import (
    UserResponse, UserUpdate, UserRole, UserStatus, KYCStatus, 
    UserPasswordChange, NotificationPreferences
)
from ..utils.dependencies import get_current_user, get_admin_user, get_database, admin_required
from ..utils.errors import UserError, ValidationError
from ..utils.security import get_password_hash, verify_password, is_strong_password
from ..utils.file_utils import validate_file_type, save_uploaded_file, get_file_url, file_manager

router = APIRouter(prefix="/api/users", tags=["users"])
security = HTTPBearer()


@router.get("/profile", response_model=UserResponse)
async def get_my_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get current user's profile."""
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_id(current_user["id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/profile", response_model=Dict[str, str])
async def update_my_profile(
    profile_data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update current user's profile."""
    user_repo = UserRepository(db)
    
    success = await user_repo.update_user(current_user["id"], profile_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update profile"
        )
    
    # Log activity
    await user_repo.log_activity(
        current_user["id"], 
        "profile_update", 
        profile_data.dict(exclude_none=True)
    )
    
    return {"message": "Profile updated successfully"}


@router.post("/change-password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Change user password."""
    user_repo = UserRepository(db)
    
    # Get user with password hash
    user_doc = await user_repo.get_user_for_auth(current_user["email"])
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, user_doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    if not is_strong_password(password_data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password does not meet security requirements"
        )
    
    # Hash and update password
    new_password_hash = get_password_hash(password_data.new_password)
    success = await user_repo.update_password(current_user["id"], new_password_hash)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update password"
        )
    
    # Log activity
    await user_repo.log_activity(
        current_user["id"], 
        "password_change", 
        {"timestamp": datetime.utcnow()}
    )
    
    return {"message": "Password changed successfully"}


@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Upload user avatar image."""
    # Validate file type
    if not validate_file_type(file, ["image/jpeg", "image/png", "image/webp"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG and WebP images are allowed"
        )
    
    # Validate file size (5MB max)
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB"
        )
    
    # Save file using file manager
    try:
        file_path = await file_manager.save_avatar(file, current_user["id"])
        avatar_url = get_file_url(file_path)
        
        # Update user avatar
        user_repo = UserRepository(db)
        update_data = UserUpdate(avatar=avatar_url)
        success = await user_repo.update_user(current_user["id"], update_data)
        
        if not success:
            # Clean up uploaded file if update failed
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update avatar"
            )
        
        # Log activity
        await user_repo.log_activity(
            current_user["id"], 
            "avatar_upload", 
            {"avatar_url": avatar_url}
        )
        
        return {
            "message": "Avatar uploaded successfully",
            "avatar_url": avatar_url
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}"
        )


@router.post("/kyc/upload-document")
async def upload_kyc_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Upload KYC document."""
    # Validate document type
    valid_types = ["passport", "national_id", "driving_license", "utility_bill", "bank_statement"]
    if document_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Validate file type
    if not validate_file_type(file, ["image/jpeg", "image/png", "application/pdf"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG images and PDF files are allowed"
        )
    
    # Validate file size (10MB max)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB"
        )
    
    # Save file using file manager
    try:
        file_path = await file_manager.save_kyc_document(file, current_user["id"], document_type)
        document_url = get_file_url(file_path)
        
        # Add document to user
        user_repo = UserRepository(db)
        success = await user_repo.add_kyc_document(current_user["id"], document_url)
        
        if not success:
            # Clean up uploaded file if update failed
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save KYC document"
            )
        
        # Log activity
        await user_repo.log_activity(
            current_user["id"], 
            "kyc_document_upload", 
            {
                "document_type": document_type,
                "document_url": document_url
            }
        )
        
        return {
            "message": "KYC document uploaded successfully",
            "document_url": document_url
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/kyc/status")
async def get_kyc_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get current user's KYC status."""
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_id(current_user["id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "status": user.kyc.status,
        "documents": user.kyc.documents,
        "verified_at": user.kyc.verified_at,
        "rejection_reason": user.kyc.rejection_reason
    }


@router.put("/preferences")
async def update_preferences(
    preferences: NotificationPreferences,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update notification preferences."""
    user_repo = UserRepository(db)
    
    # Get current user to preserve other preference settings
    user = await user_repo.get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update only notifications in preferences
    updated_preferences = user.preferences.dict()
    updated_preferences["notifications"] = preferences.dict()
    
    from ..databases.schemas.users import UserPreferences
    update_data = UserUpdate(preferences=UserPreferences(**updated_preferences))
    
    success = await user_repo.update_user(current_user["id"], update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update preferences"
        )
    
    # Log activity
    await user_repo.log_activity(
        current_user["id"], 
        "preferences_update", 
        preferences.dict()
    )
    
    return {"message": "Preferences updated successfully"}


@router.get("/activities")
async def get_my_activities(
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get current user's activity history."""
    user_repo = UserRepository(db)
    activities = await user_repo.get_user_activities(current_user["id"], limit)
    
    return {"activities": activities}

# Admin endpoints
@router.get("", response_model=Dict[str, Any])
@admin_required
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = Query(None),
    status: Optional[UserStatus] = Query(None),
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db = Depends(get_database)
):
    """Get paginated list of users (admin only)."""
    user_repo = UserRepository(db)
    
    # Apply admin isolation
    admin_id = current_user["id"] if current_user["role"] != "super_admin" else None
    
    users = await user_repo.get_users(skip, limit, role, status, admin_id)
    total = await user_repo.count_users(role, status, admin_id)
    
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{user_id}", response_model=UserResponse)
@admin_required
async def get_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db = Depends(get_database)
):
    """Get specific user details (admin only)."""
    user_repo = UserRepository(db)
    
    # Apply admin isolation
    admin_id = current_user["id"] if current_user["role"] != "super_admin" else None
    
    user = await user_repo.get_user_by_id(user_id, admin_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/{user_id}/status")
@admin_required
async def update_user_status(
    user_id: str,
    new_status: UserStatus,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db = Depends(get_database)
):
    """Update user status (admin only)."""
    user_repo = UserRepository(db)
    
    # Apply admin isolation
    admin_id = current_user["id"] if current_user["role"] != "super_admin" else None
    
    success = await user_repo.update_user_status(user_id, new_status, admin_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user status"
        )
    
    # Log admin activity
    await user_repo.log_activity(
        current_user["id"], 
        "admin_user_status_update", 
        {"target_user": user_id, "new_status": new_status.value}
    )
    
    return {"message": f"User status updated to {new_status.value}"}


@router.put("/{user_id}/kyc/status")
@admin_required
async def update_kyc_status(
    user_id: str,
    new_status: KYCStatus,
    rejection_reason: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db = Depends(get_database)
):
    """Update user KYC status (admin only)."""
    user_repo = UserRepository(db)
    
    # Apply admin isolation
    admin_id = current_user["id"] if current_user["role"] != "super_admin" else None
    
    success = await user_repo.update_kyc_status(
        user_id, 
        new_status, 
        current_user["id"] if new_status == KYCStatus.VERIFIED else None,
        rejection_reason,
        admin_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update KYC status"
        )
    
    # Log admin activity
    await user_repo.log_activity(
        current_user["id"], 
        "admin_kyc_status_update", 
        {
            "target_user": user_id, 
            "new_status": new_status.value,
            "rejection_reason": rejection_reason
        }
    )
    
    return {"message": f"KYC status updated to {new_status.value}"}


@router.get("/kyc/pending", response_model=List[UserResponse])
@admin_required
async def get_pending_kyc_users(
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db = Depends(get_database)
):
    """Get users with pending KYC status (admin only)."""
    user_repo = UserRepository(db)
    
    # Apply admin isolation
    admin_id = current_user["id"] if current_user["role"] != "super_admin" else None
    
    users = await user_repo.get_kyc_pending_users(admin_id)
    return users


@router.get("/{user_id}/activities")
@admin_required
async def get_user_activities(
    user_id: str,
    limit: int = Query(100, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db = Depends(get_database)
):
    """Get user activity history (admin only)."""
    user_repo = UserRepository(db)
    
    # Apply admin isolation - check if admin can access this user
    admin_id = current_user["id"] if current_user["role"] != "super_admin" else None
    user = await user_repo.get_user_by_id(user_id, admin_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    activities = await user_repo.get_user_activities(user_id, limit)
    return {"activities": activities}


@router.delete("/{user_id}")
@admin_required
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db = Depends(get_database)
):
    """Soft delete user (admin only)."""
    user_repo = UserRepository(db)
    
    # Apply admin isolation
    admin_id = current_user["id"] if current_user["role"] != "super_admin" else None
    
    success = await user_repo.delete_user(user_id, admin_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user"
        )
    
    # Log admin activity
    await user_repo.log_activity(
        current_user["id"], 
        "admin_user_delete", 
        {"target_user": user_id}
    )
    
    return {"message": "User deleted successfully"}