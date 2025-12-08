"""
Avatar utility functions for user profile avatars.
Handles avatar upload, storage, and management.
"""

import os
import base64
import re
from pathlib import Path
from fastapi import HTTPException, status
from typing import Optional

# Define avatar directory (relative to project root)
# avatar_utils.py is in: app/utils/avatar_utils.py
# So we go up: utils -> app -> project_root, then into uploads/avatar
AVATAR_DIR = Path(__file__).parent.parent.parent / "uploads" / "avatar"

# Create avatar directory if it doesn't exist (including parent directories)
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

# Default avatar path
DEFAULT_AVATAR_PATH = "/uploads/avatar/default.png"

async def save_user_avatar(base64_string: str, user_id: str) -> str:
    """
    Save base64 encoded avatar image for a user.
    Replaces existing avatar for the user.
    
    Args:
        base64_string: Base64 encoded image string (with or without data URI prefix)
        user_id: User ID for filename
        
    Returns:
        Relative path to the saved avatar (e.g., /uploads/avatar/user_id.png)
    """
    try:
        # Extract base64 data from data URI if present
        if base64_string.startswith('data:image'):
            # Format: data:image/png;base64,<base64_string>
            base64_data = base64_string.split(',')[1]
            # Extract image type from data URI
            image_type = base64_string.split('/')[1].split(';')[0]
        else:
            base64_data = base64_string
            image_type = 'png'  # Default to png for avatars
        
        # Validate image type
        allowed_types = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        if image_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image type '{image_type}' is not allowed. Allowed types: {allowed_types}"
            )
        
        # Decode base64
        try:
            image_data = base64.b64decode(base64_data)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 image format"
            )
        
        # Generate filename with user_id
        filename = f"{user_id}.{image_type}"
        file_path = AVATAR_DIR / filename
        
        # Delete existing avatar for this user if it exists
        if file_path.exists():
            file_path.unlink()
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        # Return relative path
        return f"/uploads/avatar/{filename}"
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save avatar: {str(e)}"
        )

def get_user_avatar_path(user_id: str) -> str:
    """
    Get the avatar path for a user.
    Checks if user has a custom avatar, otherwise returns default.
    
    Args:
        user_id: User ID
        
    Returns:
        Relative path to avatar
    """
    # Check for user-specific avatars with different extensions
    for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
        file_path = AVATAR_DIR / f"{user_id}.{ext}"
        if file_path.exists():
            return f"/uploads/avatar/{user_id}.{ext}"
    
    # Return default avatar if no custom avatar found
    return DEFAULT_AVATAR_PATH

def delete_user_avatar(user_id: str) -> bool:
    """
    Delete a user's avatar.
    
    Args:
        user_id: User ID
        
    Returns:
        True if successful or no avatar existed, False on error
    """
    try:
        # Check for user-specific avatars with different extensions
        deleted = False
        for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
            file_path = AVATAR_DIR / f"{user_id}.{ext}"
            if file_path.exists():
                file_path.unlink()
                deleted = True
        
        return True
    except Exception:
        return False
