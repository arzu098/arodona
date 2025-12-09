"""
Image serving endpoint for database-stored images
"""
from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import StreamingResponse
from app.utils.database_image_storage import DatabaseImageService
from app.db.connection import get_database
import base64
import io

router = APIRouter(prefix="/api/images", tags=["Images"])

async def get_image_service():
    """Get database image service instance"""
    db = get_database()
    return DatabaseImageService(db)

@router.get("/{image_id}")
async def serve_image(
    image_id: str,
    image_service: DatabaseImageService = Depends(get_image_service)
):
    """
    Serve image from database by image ID
    Returns the actual image binary data with proper content type
    """
    try:
        # Get image from database
        image_data = await image_service.get_image(image_id)
        
        # Decode base64 to binary
        binary_data = base64.b64decode(image_data["image_data"])
        
        # Create BytesIO stream
        image_stream = io.BytesIO(binary_data)
        
        # Return as streaming response with proper content type
        return StreamingResponse(
            io.BytesIO(binary_data),
            media_type=image_data["content_type"],
            headers={
                "Content-Length": str(len(binary_data)),
                "Cache-Control": "public, max-age=86400"  # Cache for 24 hours
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve image: {str(e)}"
        )

@router.get("/{image_id}/info")
async def get_image_info(
    image_id: str,
    image_service: DatabaseImageService = Depends(get_image_service)
):
    """Get image metadata without downloading the image"""
    try:
        image_data = await image_service.get_image(image_id)
        
        return {
            "image_id": image_id,
            "content_type": image_data["content_type"],
            "file_extension": image_data["file_extension"],
            "file_size": image_data["file_size"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get image info: {str(e)}"
        )