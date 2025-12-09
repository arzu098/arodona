"""File handling utilities for uploads and media processing."""

import os
import uuid
from typing import List, Optional
from fastapi import UploadFile, HTTPException
import aiofiles
from PIL import Image
import mimetypes

# Configuration
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
ALLOWED_DOCUMENT_TYPES = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]


def validate_file_type(file: UploadFile, allowed_types: List[str]) -> bool:
    """Validate if file type is allowed."""
    if not file.content_type:
        return False
    
    # Check MIME type
    if file.content_type in allowed_types:
        return True
    
    # Check file extension as fallback
    if file.filename:
        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type and mime_type in allowed_types:
            return True
    
    return False


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    if not filename:
        return ""
    return filename.split('.')[-1].lower()


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """Generate unique filename to prevent conflicts."""
    extension = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())
    
    if prefix:
        return f"{prefix}_{unique_id}.{extension}"
    return f"{unique_id}.{extension}"


async def save_uploaded_file(
    file: UploadFile, 
    subdirectory: str, 
    allowed_extensions: Optional[List[str]] = None
) -> str:
    """Save uploaded file to disk and return file path."""
    
    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Validate extension if provided
    if allowed_extensions:
        extension = get_file_extension(file.filename)
        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
            )
    
    # Create directory if it doesn't exist
    upload_path = os.path.join(UPLOAD_DIR, subdirectory)
    os.makedirs(upload_path, exist_ok=True)
    
    # Generate unique filename
    filename = generate_unique_filename(file.filename, subdirectory.replace('/', '_'))
    file_path = os.path.join(upload_path, filename)
    
    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return file_path
    except Exception as e:
        # Clean up partial file if error occurred
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


async def process_image(
    file_path: str, 
    max_width: int = 1920, 
    max_height: int = 1920, 
    quality: int = 85,
    crop_to_square: bool = False
) -> str:
    """Process and optimize image file with optional square cropping."""
    try:
        with Image.open(file_path) as img:
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                else:
                    background.paste(img)
                img = background
            
            # Crop to square if requested (center crop)
            if crop_to_square:
                width, height = img.size
                min_dimension = min(width, height)
                left = (width - min_dimension) // 2
                top = (height - min_dimension) // 2
                right = left + min_dimension
                bottom = top + min_dimension
                img = img.crop((left, top, right, bottom))
            
            # Resize if needed while maintaining aspect ratio
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            img.save(file_path, 'JPEG', quality=quality, optimize=True)
            
        return file_path
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")


def get_file_url(file_path: str, base_url: str = "/uploads") -> str:
    """Convert file path to URL."""
    
    # If it's already a full URL (cloud storage), return as is
    if file_path.startswith(('http://', 'https://')):
        return file_path
    
    # Normalize the path separators to forward slashes for URLs
    file_path = file_path.replace('\\', '/')
    
    # Remove the upload directory prefix if present
    if file_path.startswith(UPLOAD_DIR):
        relative_path = file_path[len(UPLOAD_DIR):].lstrip('/')
    elif file_path.startswith(f'./{UPLOAD_DIR}'):
        relative_path = file_path[len(f'./{UPLOAD_DIR}'):].lstrip('/')
    elif file_path.startswith(f'../{UPLOAD_DIR}'):
        relative_path = file_path[len(f'../{UPLOAD_DIR}'):].lstrip('/')
    else:
        relative_path = file_path.lstrip('/')
    
    # Ensure base_url starts with / and doesn't end with /
    if not base_url.startswith('/'):
        base_url = f'/{base_url}'
    base_url = base_url.rstrip('/')
    
    # Check environment configuration
    from app.config import ENVIRONMENT
    backend_url = os.getenv("BACKEND_URL", "")
    
    # For development environment, use local backend URL
    if ENVIRONMENT == "development":
        domain = backend_url or "http://localhost:5858"
        domain = domain.rstrip('/')
        final_url = f"{domain}{base_url}/{relative_path}"
        return final_url
    else:
        final_url = f"{base_url}/{relative_path}"
        return final_url


def delete_file(file_path: str) -> bool:
    """Delete file from disk."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False


async def create_thumbnail(
    file_path: str, 
    size: tuple = (300, 300),
    crop_to_square: bool = True
) -> str:
    """Create thumbnail for image file with optional square crop."""
    try:
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                img = background
            
            # Crop to square (center crop) for thumbnails
            if crop_to_square:
                width, height = img.size
                min_dimension = min(width, height)
                left = (width - min_dimension) // 2
                top = (height - min_dimension) // 2
                right = left + min_dimension
                bottom = top + min_dimension
                img = img.crop((left, top, right, bottom))
            
            # Create thumbnail maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            name, ext = os.path.splitext(file_path)
            thumb_path = f"{name}_thumb{ext}"
            img.save(thumb_path, 'JPEG', quality=85, optimize=True)
            
        return thumb_path
    except Exception as e:
        print(f"Error creating thumbnail: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create thumbnail: {str(e)}")


def get_file_info(file_path: str) -> dict:
    """Get file information."""
    if not os.path.exists(file_path):
        return {}
    
    stat = os.stat(file_path)
    return {
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "mime_type": mimetypes.guess_type(file_path)[0]
    }


class FileManager:
    """File management class for handling uploads and storage."""
    
    def __init__(self, base_upload_dir: str = UPLOAD_DIR):
        self.base_upload_dir = base_upload_dir
    
    async def save_avatar(self, file: UploadFile, user_id: str) -> str:
        """Save user avatar image."""
        if not validate_file_type(file, ALLOWED_IMAGE_TYPES):
            raise HTTPException(status_code=400, detail="Invalid image type")
        
        file_path = await save_uploaded_file(
            file, 
            f"avatars/{user_id}", 
            ["jpg", "jpeg", "png", "webp", "gif"]
        )
        
        # Process and optimize image
        await process_image(file_path, max_width=500, max_height=500)
        
        return file_path
    
    async def save_kyc_document(self, file: UploadFile, user_id: str, doc_type: str) -> str:
        """Save KYC document."""
        allowed_types = ALLOWED_IMAGE_TYPES + ALLOWED_DOCUMENT_TYPES
        
        if not validate_file_type(file, allowed_types):
            raise HTTPException(status_code=400, detail="Invalid document type")
        
        file_path = await save_uploaded_file(
            file, 
            f"kyc/{user_id}/{doc_type}", 
            ["jpg", "jpeg", "png", "pdf", "doc", "docx"]
        )
        
        # Process image if it's an image file
        if file.content_type in ALLOWED_IMAGE_TYPES:
            await process_image(file_path, max_width=1920, max_height=1920)
        
        return file_path
    
    async def save_product_image(self, file: UploadFile, vendor_id: str, product_id: str) -> dict:
        """Save product image and create thumbnail."""
        if not validate_file_type(file, ALLOWED_IMAGE_TYPES):
            raise HTTPException(status_code=400, detail="Invalid image type")
        
        try:
            file_path = await save_uploaded_file(
                file, 
                f"products/{vendor_id}/{product_id}", 
                ["jpg", "jpeg", "png", "webp"]
            )
            
            # Process and optimize image
            await process_image(file_path, max_width=1920, max_height=1920, quality=85)
            
            # Create thumbnail with square crop
            thumb_path = await create_thumbnail(file_path, (300, 300), crop_to_square=True)
            
            return {
                "original": get_file_url(file_path),
                "thumbnail": get_file_url(thumb_path)
            }
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error in save_product_image: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to save product image: {str(e)}")
    
    async def save_uploaded_file(
        self, 
        file: UploadFile, 
        subdirectory: str, 
        allowed_extensions: Optional[List[str]] = None
    ) -> str:
        """Save uploaded file to disk and return file path."""
        return await save_uploaded_file(file, subdirectory, allowed_extensions)
    
    def cleanup_user_files(self, user_id: str) -> bool:
        """Clean up all files for a user."""
        import shutil
        try:
            user_dirs = [
                os.path.join(self.base_upload_dir, "avatars", user_id),
                os.path.join(self.base_upload_dir, "kyc", user_id),
                os.path.join(self.base_upload_dir, "reviews", user_id)
            ]
            
            for dir_path in user_dirs:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
            
            return True
        except Exception:
            return False


# Global file manager instance
file_manager = FileManager()