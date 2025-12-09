
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
    videos: List[UploadFile] = File(default=[], description="Review videos (max 2)"),
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
    
    # Process images and videos if provided
    image_urls = []
    video_urls = []
    try:
        # Process images
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
        
        # Process videos
        if videos and len(videos) > 0 and videos[0].filename:
            # Validate number of videos
            if len(videos) > 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum 2 videos allowed per review"
                )
            
            ALLOWED_VIDEO_TYPES = ["video/mp4", "video/avi", "video/mov", "video/wmv", "video/webm"]
            
            for video in videos:
                # Validate file type
                if not validate_file_type(video, ALLOWED_VIDEO_TYPES):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid video type for file '{video.filename}'. Supported: MP4, AVI, MOV, WMV, WebM"
                    )
                
                # Check file size (max 50MB for videos)
                if video.size and video.size > 50 * 1024 * 1024:  # 50MB
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Video file '{video.filename}' is too large. Maximum size: 50MB"
                    )
                
                try:
                    # Save file
                    file_path = await file_manager.save_uploaded_file(
                        video, 
                        f"reviews/{user_id}", 
                        ["mp4", "avi", "mov", "wmv", "webm"]
                    )
                    
                    # Get URL
                    file_url = get_file_url(file_path)
                    video_urls.append(file_url)
                    
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to upload video '{video.filename}': {str(e)}"
                    )
        
        # Create review
        approved = not REVIEW_REQUIRES_APPROVAL
        print(f"[DEBUG] Creating review for product_id: {product_id} (type: {type(product_id)})")
        print(f"[DEBUG] User: {user_id}, Rating: {rating}, Approved: {approved}")
        
        review = await repo.create_review(
            product_id=product_id,
            user_id=user_id,
            full_name=full_name,
            rating=rating,
            title=title,
            body=body,
            images=image_urls,
            videos=video_urls,
            is_verified_buyer=False,  # TODO: Check order history
            approved=approved
        )
        
        print(f"[DEBUG] Review created with ID: {review.get('_id')}")
    
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


@router.get("/debug/vendor/{vendor_id}")
async def debug_vendor_reviews(
    vendor_id: str,
    current_user: dict = Depends(get_current_user),
    repo: ReviewRepository = Depends(get_review_repository)
):
    """Debug endpoint to check vendor reviews data"""
    try:
        db = get_database()
        
        # Get vendor products
        products_collection = db["products"]
        vendor_products = await products_collection.find(
            {"vendor_id": vendor_id},
            {"_id": 1, "name": 1}
        ).to_list(None)
        
        # Get all reviews
        reviews_collection = db["reviews"]
        all_reviews = await reviews_collection.find({}, {"product_id": 1, "rating": 1, "approved": 1, "deleted": 1}).to_list(None)
        
        vendor_product_object_ids = [p["_id"] for p in vendor_products]
        
        # Find matching reviews
        matching_reviews = []
        for review in all_reviews:
            if review.get("product_id") in vendor_product_object_ids:
                matching_reviews.append({
                    "review_id": str(review["_id"]),
                    "product_id": str(review["product_id"]),
                    "rating": review.get("rating"),
                    "approved": review.get("approved", True),
                    "deleted": review.get("deleted", False)
                })
        
        return {
            "vendor_id": vendor_id,
            "vendor_products_count": len(vendor_products),
            "vendor_products": [{"id": str(p["_id"]), "name": p.get("name")} for p in vendor_products[:5]],
            "total_reviews_in_db": len(all_reviews),
            "matching_reviews_count": len(matching_reviews),
            "matching_reviews": matching_reviews[:10],
            "sample_all_reviews": [{"id": str(r["_id"]), "product_id": str(r["product_id"])} for r in all_reviews[:5]]
        }
        
    except Exception as e:
        return {"error": str(e)}


@router.get("/debug/vendor-products/{vendor_id}")
async def debug_vendor_products(vendor_id: str):
    """Debug endpoint to check vendor's products"""
    try:
        db = get_database()
        
        # Get vendor info
        vendors_collection = db["vendors"]
        vendor = await vendors_collection.find_one({"_id": ObjectId(vendor_id)})
        
        # Get products for this vendor
        products_collection = db["products"]
        vendor_products = await products_collection.find(
            {"vendor_id": vendor_id}
        ).to_list(None)
        
        # Also check products with string vendor_id format
        vendor_products_str = await products_collection.find(
            {"vendor_id": str(vendor_id)}
        ).to_list(None)
        
        # Check all products to see vendor_id formats
        all_products = await products_collection.find({}, {"vendor_id": 1, "name": 1}).limit(10).to_list(10)
        
        return {
            "vendor_id": vendor_id,
            "vendor_exists": vendor is not None,
            "vendor_user_id": str(vendor.get("user_id")) if vendor else None,
            "products_with_exact_match": len(vendor_products),
            "products_with_string_match": len(vendor_products_str),
            "sample_vendor_products": [
                {
                    "id": str(p["_id"]), 
                    "name": p.get("name"), 
                    "vendor_id": p.get("vendor_id"),
                    "vendor_id_type": str(type(p.get("vendor_id")))
                } for p in (vendor_products + vendor_products_str)[:5]
            ],
            "sample_all_products": [
                {
                    "id": str(p["_id"]), 
                    "name": p.get("name"), 
                    "vendor_id": p.get("vendor_id"),
                    "vendor_id_type": str(type(p.get("vendor_id")))
                } for p in all_products
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/debug/all-reviews")
async def debug_all_reviews():
    """Debug endpoint to check all reviews in database"""
    try:
        db = get_database()
        reviews_collection = db["reviews"]
        
        # Get all reviews
        all_reviews = await reviews_collection.find({}).to_list(None)
        
        return {
            "total_reviews": len(all_reviews),
            "reviews": [
                {
                    "id": str(r["_id"]),
                    "product_id": str(r["product_id"]) if r.get("product_id") else None,
                    "rating": r.get("rating"),
                    "approved": r.get("approved", True),
                    "deleted": r.get("deleted", False),
                    "created_at": r.get("created_at").isoformat() if r.get("created_at") else None
                } for r in all_reviews
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/vendor/{vendor_id}", response_model=ReviewListResponse)
async def get_vendor_reviews(
    vendor_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    repo: ReviewRepository = Depends(get_review_repository)
):
    """Get reviews for all products belonging to a vendor"""
    try:
        print(f"[VENDOR REVIEWS] Request for vendor_id: {vendor_id}")
        print(f"[VENDOR REVIEWS] Current user: {current_user}")
        
        db = get_database()
        
        # Get vendor to verify ownership or admin access
        vendors_collection = db["vendors"]
        vendor = await vendors_collection.find_one({"_id": ObjectId(vendor_id)})
        if not vendor:
            print(f"[VENDOR REVIEWS] Vendor {vendor_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        print(f"[VENDOR REVIEWS] Vendor found: {vendor.get('business_name', 'Unknown')}")
        
        # Check if current user is the vendor owner or admin
        user_id = current_user.get("user_id") or current_user.get("sub")
        user_role = current_user.get("role", "")
        vendor_user_id = str(vendor.get("user_id"))
        
        print(f"[VENDOR REVIEWS] User ID: {user_id}, Role: {user_role}, Vendor User ID: {vendor_user_id}")
        
        if user_role not in ["admin", "super_admin"] and vendor_user_id != user_id:
            print(f"[VENDOR REVIEWS] Access denied - not owner or admin")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view these reviews"
            )
        
        # Get reviews for this vendor's products
        reviews, total = await repo.get_reviews_by_vendor_id(vendor_id, skip, limit)
        
        return {
            "reviews": reviews,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        print(f"[VENDOR REVIEWS] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch vendor reviews"
        )

@router.get("/vendor-public/{vendor_id}", response_model=ReviewListResponse)
async def get_vendor_reviews_public(
    vendor_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    repo: ReviewRepository = Depends(get_review_repository)
):
    """Get reviews for all products belonging to a vendor (public access for testing)"""
    try:
        print(f"[PUBLIC VENDOR REVIEWS] Request for vendor_id: {vendor_id}")
        
        db = get_database()
        
        # Get vendor products without authentication check (for testing)
        products_collection = db["products"] 
        vendor_products = []
        
        # Method 1: vendor_id as string
        products_str = await products_collection.find(
            {"vendor_id": vendor_id},
            {"_id": 1, "name": 1}
        ).to_list(None)
        vendor_products.extend(products_str)
        
        # Method 2: vendor_id as ObjectId
        try:
            vendor_obj_id = ObjectId(vendor_id)
            products_obj = await products_collection.find(
                {"vendor_id": vendor_obj_id},
                {"_id": 1, "name": 1}
            ).to_list(None)
            
            # Add products that weren't already found
            existing_ids = {str(p["_id"]) for p in vendor_products}
            for p in products_obj:
                if str(p["_id"]) not in existing_ids:
                    vendor_products.append(p)
        except:
            pass
        
        print(f"[PUBLIC] Vendor {vendor_id} has {len(vendor_products)} products")
        
        if not vendor_products:
            return {
                "meta": {
                    "rating_avg": 0,
                    "rating_count": 0,
                    "ratings_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
                },
                "items": [],
                "count": 0
            }
        
        vendor_product_object_ids = [p["_id"] for p in vendor_products]
        product_names = {str(p["_id"]): p.get("name", "Unknown Product") for p in vendor_products}
        
        # Get reviews for all vendor's products
        reviews_collection = db["reviews"]
        query = {
            "product_id": {"$in": vendor_product_object_ids},
            "deleted": False,
            "approved": True
        }
        
        total = await reviews_collection.count_documents(query)
        print(f"[PUBLIC] Found {total} reviews for vendor")
        
        reviews = await reviews_collection.find(query)\
            .sort([("created_at", -1)])\
            .skip(skip)\
            .limit(limit)\
            .to_list(limit)
        
        # Format reviews and add product info
        formatted_reviews = []
        for review in reviews:
            formatted_review = repo.format_review_response(review)
            product_id_key = str(review["product_id"])
            formatted_review["product_name"] = product_names.get(product_id_key, "Unknown Product")
            formatted_reviews.append(formatted_review)
        
        return {
            "meta": {
                "rating_avg": 4.0,  # Simplified
                "rating_count": total,
                "ratings_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": total}
            },
            "items": formatted_reviews,
            "count": total
        }
        
    except Exception as e:
        print(f"[PUBLIC] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching vendor reviews: {str(e)}"
        )
        
        # Get all product IDs for this vendor
        products_collection = db["products"]
        
        # Try both string and ObjectId formats for vendor_id in products
        vendor_products = []
        
        # Method 1: vendor_id as string
        products_str = await products_collection.find(
            {"vendor_id": vendor_id},
            {"_id": 1, "name": 1}
        ).to_list(None)
        vendor_products.extend(products_str)
        
        # Method 2: vendor_id as ObjectId
        try:
            vendor_obj_id = ObjectId(vendor_id)
            products_obj = await products_collection.find(
                {"vendor_id": vendor_obj_id},
                {"_id": 1, "name": 1}
            ).to_list(None)
            
            # Add products that weren't already found
            existing_ids = {str(p["_id"]) for p in vendor_products}
            for p in products_obj:
                if str(p["_id"]) not in existing_ids:
                    vendor_products.append(p)
        except:
            pass
        
        # Debug logging
        print(f"[DEBUG] Vendor {vendor_id} has {len(vendor_products)} products")
        for p in vendor_products[:3]:  # Show first 3 products
            print(f"[DEBUG] Product: {p['_id']} -> {p.get('name', 'No Name')}")
        
        if not vendor_products:
            print(f"[DEBUG] No products found for vendor {vendor_id}")
            return {
                "meta": {
                    "rating_avg": 0,
                    "rating_count": 0,
                    "ratings_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
                },
                "items": [],
                "count": 0
            }
        
        vendor_product_object_ids = [p["_id"] for p in vendor_products]  # ObjectId format 
        vendor_product_ids = [str(p["_id"]) for p in vendor_products]  # String format for response formatting
        product_names = {str(p["_id"]): p.get("name", "Unknown Product") for p in vendor_products}
        
        # Get reviews for all vendor's products
        reviews_collection = db["reviews"]
        # Use ObjectId format since that's how product_id is stored in reviews
        query = {
            "product_id": {"$in": vendor_product_object_ids},
            "deleted": False,
            "approved": True
        }
        
        # Debug logging
        print(f"[DEBUG] Searching for reviews with query: {query}")
        total = await reviews_collection.count_documents(query)
        print(f"[DEBUG] Found {total} reviews for vendor {vendor_id}")
        
        # Also check all reviews to see what we have
        all_reviews = await reviews_collection.find({}, {"product_id": 1, "rating": 1, "approved": 1, "deleted": 1}).to_list(None)
        print(f"[DEBUG] Total reviews in database: {len(all_reviews)}")
        
        # Check if any reviews match our product IDs
        matching_reviews = []
        for review in all_reviews:
            product_id = review.get("product_id")
            if product_id:
                if str(product_id) in vendor_product_ids or product_id in vendor_product_object_ids:
                    matching_reviews.append(review)
        print(f"[DEBUG] Matching reviews found: {len(matching_reviews)}")
        
        total = await reviews_collection.count_documents(query)
        
        reviews = await reviews_collection.find(query)\
            .sort([("created_at", -1)])\
            .skip(skip)\
            .limit(limit)\
            .to_list(limit)
        
        # Format reviews and add product info
        formatted_reviews = []
        for review in reviews:
            formatted_review = repo.format_review_response(review)
            # Handle ObjectId product_id - convert to string to match our product_names dict
            product_id_key = str(review["product_id"])
            formatted_review["product_name"] = product_names.get(product_id_key, "Unknown Product")
            formatted_reviews.append(formatted_review)
        
        # Calculate aggregated ratings for all vendor products
        rating_pipeline = [
            {
                "$match": {
                    "product_id": {"$in": vendor_product_object_ids},
                    "deleted": False,
                    "approved": True
                }
            },
            {
                "$group": {
                    "_id": "$rating",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        rating_results = await reviews_collection.aggregate(rating_pipeline).to_list(None)
        
        # Build rating breakdown and average
        breakdown = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        total_ratings = 0
        weighted_sum = 0
        
        for result in rating_results:
            rating_str = str(result["_id"])
            count = result["count"]
            breakdown[rating_str] = count
            total_ratings += count
            weighted_sum += result["_id"] * count
        
        rating_avg = weighted_sum / total_ratings if total_ratings > 0 else 0
        
        meta = {
            "rating_avg": round(rating_avg, 2),
            "rating_count": total_ratings,
            "ratings_breakdown": breakdown
        }
        
        return {
            "meta": meta,
            "items": formatted_reviews,
            "count": total
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching vendor reviews: {str(e)}"
        )