import os
import base64
import re
from pathlib import Path
from fastapi import HTTPException, status
from typing import List

# Define upload directory (relative to project root)
# image_upload.py is in: app/utils/image_upload.py
# So we go up: utils -> app -> project_root, then into uploads
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"

# Create uploads directory if it doesn't exist
UPLOAD_DIR.mkdir(exist_ok=True)

async def save_base64_image(base64_string: str) -> str:
    """
    Save base64 encoded image to disk and return the relative path
    Args:
        base64_string: Base64 encoded image string (with or without data URI prefix)
    Returns:
        Relative path to the saved file (e.g., /uploads/filename.jpg)
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
            image_type = 'jpg'  # Default to jpg if no format specified
        
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
        
        # Generate unique filename
        timestamp = str(int(__import__('time').time() * 1000))
        filename = f"{timestamp}.{image_type}"
        file_path = UPLOAD_DIR / filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        # Return relative path
        return f"/uploads/{filename}"
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image: {str(e)}"
        )

async def save_multiple_base64_images(base64_strings: List[str]) -> List[str]:
    """
    Save multiple base64 encoded images to disk
    Args:
        base64_strings: List of base64 encoded image strings
    Returns:
        List of relative paths to saved files
    """
    uploaded_paths = []
    
    for base64_string in base64_strings:
        try:
            path = await save_base64_image(base64_string)
            uploaded_paths.append(path)
        except HTTPException as e:
            # Delete previously uploaded files if error occurs
            for uploaded_path in uploaded_paths:
                try:
                    file_to_delete = UPLOAD_DIR / uploaded_path.replace("/uploads/", "")
                    if file_to_delete.exists():
                        file_to_delete.unlink()
                except Exception:
                    pass
            raise e
    
    return uploaded_paths

def delete_file(file_path: str) -> bool:
    """
    Delete a file from the uploads directory
    Args:
        file_path: Relative path (e.g., /uploads/filename.jpg)
    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract filename from path
        filename = file_path.replace("/uploads/", "").replace("\\uploads\\", "")
        file_to_delete = UPLOAD_DIR / filename
        
        if file_to_delete.exists():
            file_to_delete.unlink()
            return True
        return False
    except Exception:
        return False

def delete_multiple_files(file_paths: List[str]) -> bool:
    """
    Delete multiple files from the uploads directory
    Args:
        file_paths: List of relative paths
    Returns:
        True if all files were deleted successfully
    """
    all_deleted = True
    
    for file_path in file_paths:
        if not delete_file(file_path):
            all_deleted = False
    
    return all_deleted
