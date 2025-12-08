
"""
Simplified Review API endpoints with image support.
Only essential endpoints for creating and viewing reviews with images.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.databases.schemas.review import ReviewResponse, ReviewListResponse
from app.databases.repositories.review import ReviewRepository
from app.db.connection import get_database
from app.utils.security import get_current_user
from app.utils.review_utils import resolve_product_id, incremental_update_on_create
from app.utils.file_utils import file_manager, get_file_url, validate_file_type, ALLOWED_IMAGE_TYPES
import os

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])

# Configuration
REVIEW_REQUIRES_APPROVAL = os.getenv("REVIEW_REQUIRES_APPROVAL", "false").lower() == "true"
ONE_REVIEW_PER_USER = os.getenv("ONE_REVIEW_PER_USER", "true").lower() == "true"


async def get_review_repository() -> ReviewRepository:
    db = get_database()
    return ReviewRepository(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_review(
    product: str = Form(..., description="Product ID or slug"),
    rating: int = Form(..., description="Rating 1-5"),
    title: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    images: List[UploadFile] = File(default=[], description="Review images (max 5)"),
    current_user: dict = Depends(get_current_user),
    repo: ReviewRepository = Depends(get_review_repository)
):
    """Create a review with optional images"""
    # Basic validation
    if not (1 <= rating <= 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    if title and len(title) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot exceed 200 characters"
        )
    
    if body and len(body) > 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review body cannot exceed 2000 characters"
        )
    
    db = get_database()
    
    # Resolve product ID
    try:
        product_id = await resolve_product_id(db, product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # Check for existing review (one-review-per-user policy)
    user_id = current_user.get("user_id") or current_user.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )
    if ONE_REVIEW_PER_USER:
        existing = await repo.check_existing_review(product_id, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reviewed this product"
            )
    
    # Fetch user details from database to get full name
    users_collection = db["users"]
    from bson import ObjectId as BsonObjectId
    try:
        user_obj_id = BsonObjectId(user_id)
    except:
        # If user_id is not ObjectId, try to find by email
        user_email = current_user.get("sub")
        user_doc = await users_collection.find_one({"email": user_email})
    else:
        user_doc = await users_collection.find_one({"_id": user_obj_id})
    
    # Get full name from user document
    full_name = None
    if user_doc:
        first_name = user_doc.get("first_name", "")
        last_name = user_doc.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() if first_name or last_name else None
    
    # Process images if provided
    image_urls = []
    try:
        if images and len(images) > 0 and images[0].filename:
            # Validate number of images
            if len(images) > 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum 5 images allowed per review"
                )
            
            for image in images:
                # Validate file type
                if not validate_file_type(image, ALLOWED_IMAGE_TYPES):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid image type for file '{image.filename}'. Supported: JPEG, PNG, WebP, GIF"
                    )
                
                try:
                    # Save file
                    file_path = await file_manager.save_uploaded_file(
                        image, 
                        f"reviews/{user_id}", 
                        ["jpg", "jpeg", "png", "webp", "gif"]
                    )
                    
                    # Process and optimize image
                    from app.utils.file_utils import process_image
                    await process_image(file_path, max_width=1200, max_height=1200, quality=85)
                    
                    # Get URL
                    file_url = get_file_url(file_path)
                    image_urls.append(file_url)
                    
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to upload image '{image.filename}': {str(e)}"
                    )
        
        # Create review
        approved = not REVIEW_REQUIRES_APPROVAL
        review = await repo.create_review(
            product_id=product_id,
            user_id=user_id,
            full_name=full_name,
            rating=rating,
            title=title,
            body=body,
            images=image_urls,
            is_verified_buyer=False,  # TODO: Check order history
            approved=approved
        )
    
        # Update product rating aggregates (only if auto-approved)
        if approved:
            await incremental_update_on_create(db, product_id, rating)
    
        return repo.format_review_response(review)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating review: {str(e)}"
        )


@router.get("/product/{product_id_or_slug}", response_model=ReviewListResponse)
async def get_product_reviews(
    product_id_or_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    repo: ReviewRepository = Depends(get_review_repository)
):
    """Get reviews for a product"""
    try:
        db = get_database()
        product_id = await resolve_product_id(db, product_id_or_slug)
        
        reviews, total = await repo.get_reviews_by_product(
            product_id=product_id,
            skip=skip,
            limit=limit,
            sort_by="newest",
            approved_only=True
        )
        
        aggregates = await repo.get_rating_aggregates(product_id)
        
        return {
            "meta": aggregates,
            "items": [repo.format_review_response(r) for r in reviews],
            "count": total
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching reviews: {str(e)}"
        )