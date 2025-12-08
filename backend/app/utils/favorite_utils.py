"""
Favorite utility functions for product resolution and helper operations.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from fastapi import HTTPException, status
from typing import Dict, Tuple, List


async def resolve_product_id(db: AsyncIOMotorDatabase, identifier: str) -> ObjectId:
    """
    Resolve product by ID or slug to ObjectId.
    
    Args:
        db: Database instance
        identifier: Product ID (ObjectId string) or slug
        
    Returns:
        ObjectId of the product
        
    Raises:
        HTTPException 404 if product not found
    """
    products_collection = db["products"]
    
    # Try as ObjectId first
    try:
        obj_id = ObjectId(identifier)
        product = await products_collection.find_one({"_id": obj_id})
        if product:
            return obj_id
    except Exception:
        pass
    
    # Try as slug (if you have slug field in products)
    product = await products_collection.find_one({"slug": identifier})
    if product:
        return product["_id"]
    
    # Try as category or name (fallback for compatibility)
    product = await products_collection.find_one({"category": identifier.lower()})
    if product:
        return product["_id"]
    
    # Not found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product not found: {identifier}"
    )


async def validate_product_exists(db: AsyncIOMotorDatabase, product_id: ObjectId) -> bool:
    """
    Validate that a product exists.
    
    Args:
        db: Database instance
        product_id: Product ObjectId
        
    Returns:
        True if product exists, raises HTTPException 404 otherwise
    """
    products_collection = db["products"]
    product = await products_collection.find_one({"_id": product_id})
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product not found: {str(product_id)}"
        )
    
    return True


async def toggle_favorite(
    db: AsyncIOMotorDatabase,
    user_id: str,
    product_id: ObjectId
) -> Dict:
    """
    Toggle favorite: remove if exists, add if doesn't.
    
    This is a convenience wrapper around the repository method.
    
    Args:
        db: Database instance
        user_id: User identifier
        product_id: Product ObjectId
        
    Returns:
        {"action": "added|removed|exists", "product_id": str, "favorite_id": str}
    """
    from app.databases.repositories.favorite import FavoriteRepository
    
    repo = FavoriteRepository(db)
    return await repo.toggle_favorite(user_id, product_id)


async def list_user_favorites(
    db: AsyncIOMotorDatabase,
    user_id: str,
    skip: int = 0,
    limit: int = 20
) -> Tuple[int, List[Dict]]:
    """
    Get user's favorites with embedded product details.
    
    Args:
        db: Database instance
        user_id: User identifier
        skip: Number of items to skip (pagination)
        limit: Maximum number of items to return
        
    Returns:
        Tuple of (total_count, list_of_favorites)
    """
    from app.databases.repositories.favorite import FavoriteRepository
    
    repo = FavoriteRepository(db)
    return await repo.list_user_favorites(user_id, skip, limit)


async def check_is_favorited(
    db: AsyncIOMotorDatabase,
    user_id: str,
    product_id: ObjectId
) -> bool:
    """
    Check if a product is in user's favorites.
    
    Args:
        db: Database instance
        user_id: User identifier
        product_id: Product ObjectId
        
    Returns:
        True if favorited, False otherwise
    """
    from app.databases.repositories.favorite import FavoriteRepository
    
    repo = FavoriteRepository(db)
    return await repo.check_favorite(user_id, product_id)
