"""
Product & Catalog Management API endpoints.
Handles advanced product operations and catalog management.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File
from typing import List, Optional
from datetime import datetime
from app.databases.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductCreateResponse,
    ProductListResponse, ProductDeleteResponse, ProductSearchRequest,
    ProductBulkUpload, ProductInventoryUpdate, ProductPricingTier,
    ProductTag, CollectionCreate, CollectionUpdate, CollectionResponse
)
from app.databases.repositories.product import ProductRepository
from app.db.connection import get_database
from app.utils.security import get_current_user
from app.utils.database_image_storage import DatabaseImageService

router = APIRouter(prefix="/api/admin/products", tags=["Product Management"])

async def get_product_repository() -> ProductRepository:
    """Dependency to get product repository"""
    db = get_database()
    return ProductRepository(db)

@router.post("/bulk", response_model=List[ProductCreateResponse], status_code=status.HTTP_201_CREATED)
async def bulk_upload_products(
    bulk_data: ProductBulkUpload,
    current_user: dict = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    Bulk upload multiple products (Admin only)
    """
    try:
        # Check if current user is admin
        is_admin = current_user.get("role") == "admin"
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Prepare products data
        products_data = []
        for product_create in bulk_data.products:
            product_data = {
                "name": product_create.name,
                "description": product_create.description,
                "price": product_create.price,
                "category": product_create.category,
                "images": []
            }
            
            # Save images if provided
            if product_create.images:
                # Store images in database
                db = get_database()
                image_service = DatabaseImageService(db)
                image_ids = await image_service.store_multiple_images(product_create.images, None)
                # Generate image URLs pointing to our image serving endpoint
                from app.config import BACKEND_URL, ENVIRONMENT
                import os
                backend_url = os.getenv("BACKEND_URL", "http://localhost:5858" if ENVIRONMENT == "development" else "https://adorona.onrender.com")
                image_paths = [f"{backend_url}/api/images/{image_id}" for image_id in image_ids]
                product_data["images"] = image_paths
                
            products_data.append(product_data)
        
        # Create products in bulk
        created_products = await repo.bulk_create_products(products_data)
        
        return [
            {
                "message": "Product created successfully",
                "product": repo.format_product_response(product)
            }
            for product in created_products
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error bulk uploading products: {str(e)}"
        )

@router.post("/{product_id}/images", response_model=ProductCreateResponse)
async def upload_product_images(
    product_id: str,
    images: List[str],  # Base64 encoded images
    current_user: dict = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    Upload images to an existing product (Admin only)
    """
    try:
        # Check if current user is admin
        is_admin = current_user.get("role") == "admin"
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Check if product exists
        product = await repo.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Save images
        # Store images in database
        db = get_database()
        image_service = DatabaseImageService(db)
        image_ids = await image_service.store_multiple_images(images, None)
        # Generate image URLs pointing to our image serving endpoint
        from app.config import BACKEND_URL, ENVIRONMENT
        import os
        backend_url = os.getenv("BACKEND_URL", "http://localhost:5858" if ENVIRONMENT == "development" else "https://adorona.onrender.com")
        image_paths = [f"{backend_url}/api/images/{image_id}" for image_id in image_ids]
        
        # Add images to product
        updated_product = await repo.add_images_to_product(product_id, image_paths)
        
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add images to product"
            )
        
        return {
            "message": "Images uploaded successfully",
            "product": repo.format_product_response(updated_product)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading images: {str(e)}"
        )

@router.put("/{product_id}/inventory", response_model=ProductCreateResponse)
async def update_product_inventory(
    product_id: str,
    inventory_data: ProductInventoryUpdate,
    current_user: dict = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    Update product inventory (Admin only)
    """
    try:
        # Check if current user is admin
        is_admin = current_user.get("role") == "admin"
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Check if product exists
        product = await repo.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Update inventory
        updated_product = await repo.update_inventory(
            product_id,
            inventory_data.sku,
            inventory_data.quantity,
            inventory_data.reserved_quantity or 0
        )
        
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update product inventory"
            )
        
        return {
            "message": "Product inventory updated successfully",
            "product": repo.format_product_response(updated_product)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating inventory: {str(e)}"
        )

@router.post("/{product_id}/pricing-tiers", response_model=ProductCreateResponse)
async def manage_pricing_tiers(
    product_id: str,
    pricing_tiers: List[ProductPricingTier],
    current_user: dict = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    Manage pricing tiers for a product (Admin only)
    """
    try:
        # Check if current user is admin
        is_admin = current_user.get("role") == "admin"
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Check if product exists
        product = await repo.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Convert pricing tiers to dict format
        pricing_tiers_dict = [
            {
                "tier_name": tier.tier_name,
                "min_quantity": tier.min_quantity,
                "price": tier.price,
                "description": tier.description
            }
            for tier in pricing_tiers
        ]
        
        # Add pricing tiers to product
        updated_product = await repo.add_pricing_tiers(product_id, pricing_tiers_dict)
        
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add pricing tiers to product"
            )
        
        return {
            "message": "Pricing tiers updated successfully",
            "product": repo.format_product_response(updated_product)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error managing pricing tiers: {str(e)}"
        )

@router.get("/search", response_model=ProductListResponse)
async def search_products(
    query: str = Query(..., min_length=1),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    Search products by query, category, and price range
    """
    try:
        products, total = await repo.search_products(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price,
            skip=skip,
            limit=limit
        )
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "products": [repo.format_product_response(p) for p in products]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching products: {str(e)}"
        )

@router.post("/tags", response_model=ProductTag, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: ProductTag,
    current_user: dict = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    Create a new product tag (Admin only)
    """
    try:
        # Check if current user is admin
        is_admin = current_user.get("role") == "admin"
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # In a real implementation, you would save the tag to a tags collection
        # For now, we'll just return the tag data
        return tag_data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tag: {str(e)}"
        )

@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection_data: CollectionCreate,
    current_user: dict = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    Create a new product collection (Admin only)
    """
    try:
        # Check if current user is admin
        is_admin = current_user.get("role") == "admin"
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Create collection
        collection = await repo.create_collection(
            name=collection_data.name,
            slug=collection_data.slug,
            description=collection_data.description,
            product_ids=collection_data.product_ids,
            metadata=collection_data.metadata
        )
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create collection"
            )
        
        return repo.format_collection_response(collection)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating collection: {str(e)}"
        )

@router.get("/collections/{collection_id_or_slug}", response_model=CollectionResponse)
async def get_collection(
    collection_id_or_slug: str,
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    Get a collection by ID or slug
    """
    try:
        # Try as ObjectId first
        collection = None
        try:
            collection = await repo.get_collection_by_id(collection_id_or_slug)
        except Exception:
            pass
        
        # Try as slug
        if not collection:
            collection = await repo.get_collection_by_slug(collection_id_or_slug)
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection not found: {collection_id_or_slug}"
            )
        
        return repo.format_collection_response(collection)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving collection: {str(e)}"
        )

@router.put("/collections/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    collection_update: CollectionUpdate,
    current_user: dict = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    Update a collection (Admin only)
    """
    try:
        # Check if current user is admin
        is_admin = current_user.get("role") == "admin"
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Check if collection exists
        collection = await repo.get_collection_by_id(collection_id)
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )
        
        # Prepare update data
        update_data = collection_update.dict(exclude_unset=True)
        
        # Update collection
        updated_collection = await repo.update_collection(collection_id, update_data)
        
        if not updated_collection:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update collection"
            )
        
        return repo.format_collection_response(updated_collection)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating collection: {str(e)}"
        )

@router.delete("/collections/{collection_id}")
async def delete_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    Delete a collection (Admin only)
    """
    try:
        # Check if current user is admin
        is_admin = current_user.get("role") == "admin"
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Check if collection exists
        collection = await repo.get_collection_by_id(collection_id)
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )
        
        # Delete collection
        deleted = await repo.delete_collection(collection_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete collection"
            )
        
        return {
            "message": "Collection deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting collection: {str(e)}"
        )

@router.get("/collections", response_model=ProductListResponse)
async def list_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    repo: ProductRepository = Depends(get_product_repository)
):
    """
    List all collections
    """
    try:
        collections, total = await repo.get_all_collections(skip, limit)
        
        formatted_collections = []
        for collection in collections:
            formatted_collection = repo.format_collection_response(collection)
            # Convert to ProductResponse format for consistency
            # Use current time as fallback if datetime fields are missing
            created_at = formatted_collection.get("created_at")
            updated_at = formatted_collection.get("updated_at")
            
            # If datetime fields are not datetime objects, use current time
            if not isinstance(created_at, datetime):
                created_at = datetime.utcnow()
            if not isinstance(updated_at, datetime):
                updated_at = datetime.utcnow()
            
            formatted_collections.append(ProductResponse(
                id=formatted_collection.get("id", ""),
                name=formatted_collection.get("name", ""),
                description=formatted_collection.get("description", ""),
                price=0.0,  # Collections don't have a price
                images=[],  # Collections don't have images
                created_at=created_at,
                updated_at=updated_at
            ))
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "products": formatted_collections
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing collections: {str(e)}"
        )