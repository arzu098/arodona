"""
Cloud Storage Service for handling image uploads
Supports Cloudinary, AWS S3, and other cloud storage providers
"""
import os
import base64
import cloudinary
import cloudinary.uploader
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import uuid
from datetime import datetime

class CloudStorageService:
    """Service for handling cloud storage operations"""
    
    def __init__(self):
        # Initialize Cloudinary (you can extend this for other providers)
        self.setup_cloudinary()
    
    def setup_cloudinary(self):
        """Setup Cloudinary configuration"""
        try:
            cloudinary.config(
                cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
                api_key=os.getenv("CLOUDINARY_API_KEY"), 
                api_secret=os.getenv("CLOUDINARY_API_SECRET"),
                secure=True
            )
            self.provider = "cloudinary"
        except Exception as e:
            print(f"Cloudinary setup failed: {e}")
            self.provider = None
    
    async def upload_image(self, base64_string: str, folder: str = "products") -> str:
        """
        Upload image to cloud storage and return public URL
        
        Args:
            base64_string: Base64 encoded image
            folder: Folder name in cloud storage
            
        Returns:
            Public URL of uploaded image
        """
        try:
            # Extract base64 data from data URI if present
            if base64_string.startswith('data:image'):
                base64_data = base64_string.split(',')[1]
                # Extract image type
                image_type = base64_string.split('/')[1].split(';')[0]
            else:
                base64_data = base64_string
                image_type = 'jpg'
            
            # Validate image type
            allowed_types = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
            if image_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image type '{image_type}' not allowed. Allowed: {allowed_types}"
                )
            
            # Generate unique filename
            unique_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            public_id = f"{folder}/{timestamp}_{unique_id}"
            
            if self.provider == "cloudinary":
                return await self._upload_to_cloudinary(base64_data, public_id)
            else:
                # Fallback to local storage if cloud storage not configured
                return await self._fallback_local_upload(base64_data, image_type, unique_id)
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Image upload failed: {str(e)}"
            )
    
    async def _upload_to_cloudinary(self, base64_data: str, public_id: str) -> str:
        """Upload to Cloudinary and return URL"""
        try:
            # Convert base64 to data URI for Cloudinary
            data_uri = f"data:image/jpeg;base64,{base64_data}"
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                data_uri,
                public_id=public_id,
                overwrite=True,
                resource_type="image",
                format="jpg",  # Convert all to jpg for consistency
                quality="auto:good",
                fetch_format="auto"
            )
            
            return result.get("secure_url")
            
        except Exception as e:
            raise Exception(f"Cloudinary upload failed: {str(e)}")
    
    async def _fallback_local_upload(self, base64_data: str, image_type: str, unique_id: str) -> str:
        """Fallback to local storage if cloud storage fails"""
        try:
            from pathlib import Path
            import base64 as b64
            
            # Create uploads directory
            upload_dir = Path(__file__).parent.parent.parent / "uploads" / "products"
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"{unique_id}.{image_type}"
            file_path = upload_dir / filename
            
            # Decode and save
            image_data = b64.b64decode(base64_data)
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            # Return relative URL (will be served by FastAPI StaticFiles)
            return f"/uploads/products/{filename}"
            
        except Exception as e:
            raise Exception(f"Local upload failed: {str(e)}")
    
    async def delete_image(self, image_url: str) -> bool:
        """Delete image from cloud storage"""
        try:
            if self.provider == "cloudinary" and "cloudinary.com" in image_url:
                # Extract public_id from Cloudinary URL
                public_id = image_url.split("/")[-1].split(".")[0]
                result = cloudinary.uploader.destroy(public_id)
                return result.get("result") == "ok"
            return True  # For local files, we don't delete automatically
        except:
            return False

# Global instance
cloud_storage = CloudStorageService()