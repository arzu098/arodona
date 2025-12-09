"""
Database Image Storage Service
Stores images directly in MongoDB as Base64 data
"""
import base64
import uuid
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from datetime import datetime
import re

class DatabaseImageService:
    """Service for storing images directly in database"""
    
    def __init__(self, db):
        self.db = db
        self.images_collection = db.images
    
    async def store_image(self, 
                         image_file = None,
                         base64_string: str = None, 
                         product_id: str = None,
                         vendor_id: str = None,
                         image_type: str = "product") -> Dict[str, Any]:
        """
        Store image in database and return image document
        
        Args:
            image_file: UploadFile object (FastAPI)
            base64_string: Base64 encoded image (alternative to image_file)
            product_id: Associated product ID (optional)
            vendor_id: Associated vendor ID (optional)
            image_type: Type of image (product, avatar, etc.)
            
        Returns:
            Dictionary with image_id and metadata
        """
        try:
            # Handle UploadFile object
            if image_file is not None:
                # Read file content
                content = await image_file.read()
                # Convert to base64
                base64_data = base64.b64encode(content).decode('utf-8')
                content_type = image_file.content_type or 'image/jpeg'
                
                # Create data URI format
                base64_string = f"data:{content_type};base64,{base64_data}"
                
                # Reset file pointer for any subsequent reads
                await image_file.seek(0)
            
            if not base64_string:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either image_file or base64_string must be provided"
                )
            
            # Extract base64 data and metadata
            image_data = self._process_base64_image(base64_string)
            
            # Create image document
            image_doc = {
                "_id": str(uuid.uuid4()),
                "product_id": product_id,
                "vendor_id": vendor_id,
                "image_type": image_type,
                "image_data": image_data["base64"],
                "content_type": image_data["content_type"],
                "file_extension": image_data["extension"],
                "file_size": len(base64.b64decode(image_data["base64"])),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Store in database
            await self.images_collection.insert_one(image_doc)
            
            return {
                "image_id": image_doc["_id"],
                "content_type": image_doc["content_type"],
                "file_size": image_doc["file_size"]
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store image: {str(e)}"
            )
    
    async def get_image(self, image_id: str) -> Dict[str, Any]:
        """Get image data from database"""
        try:
            image_doc = await self.images_collection.find_one({"_id": image_id})
            
            if not image_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Image not found"
                )
            
            return {
                "image_data": image_doc["image_data"],
                "content_type": image_doc["content_type"],
                "file_extension": image_doc["file_extension"],
                "file_size": image_doc["file_size"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve image: {str(e)}"
            )
    
    async def delete_image(self, image_id: str) -> bool:
        """Delete image from database"""
        try:
            result = await self.images_collection.delete_one({"_id": image_id})
            return result.deleted_count > 0
        except:
            return False
    
    async def store_multiple_images(self, base64_images: list, product_id: str = None) -> list:
        """Store multiple images and return list of image IDs"""
        image_ids = []
        
        for base64_string in base64_images:
            try:
                result = await self.store_image(base64_string, product_id)
                image_ids.append(result["image_id"])
            except Exception as e:
                # Log error but continue with other images
                print(f"Failed to store image: {e}")
                continue
        
        return image_ids
    
    def _process_base64_image(self, base64_string: str) -> Dict[str, str]:
        """Process base64 image string and extract metadata"""
        
        # Handle data URI format: data:image/png;base64,<data>
        if base64_string.startswith('data:image'):
            # Extract content type and base64 data
            header, base64_data = base64_string.split(',', 1)
            content_type_match = re.search(r'data:(image/\w+)', header)
            
            if content_type_match:
                content_type = content_type_match.group(1)
                extension = content_type.split('/')[1]
            else:
                content_type = 'image/jpeg'
                extension = 'jpg'
        else:
            # Plain base64 string
            base64_data = base64_string
            content_type = 'image/jpeg'  # Default
            extension = 'jpg'
        
        # Validate image type
        allowed_types = {'image/jpg', 'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
        if content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image type '{content_type}' not allowed"
            )
        
        # Validate base64 data
        try:
            base64.b64decode(base64_data)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 image data"
            )
        
        return {
            "base64": base64_data,
            "content_type": content_type,
            "extension": extension
        }