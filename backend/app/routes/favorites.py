"""
Favorites (wishlist) API endpoints (JSON only).
Handles toggle, list, check, and remove operations for user favorites.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from bson import ObjectId
from app.databases.schemas.favorite import (
    FavoriteToggleRequest,
    FavoriteToggleResponse,
    FavoriteCheckResponse,
    FavoriteListResponse,
    FavoriteRemoveResponse
)
from app.databases.repositories.favorite import FavoriteRepository
from app.db.connection import get_database
from app.utils.security import get_current_user
from app.utils.favorite_utils import (
    resolve_product_id,
    validate_product_exists
)

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])


async def get_favorite_repository() -> FavoriteRepository:
    """Dependency to get favorite repository"""
    db = get_database()
    return FavoriteRepository(db)


@router.post("/toggle", status_code=status.HTTP_200_OK)
async def toggle_favorite(
    request: FavoriteToggleRequest,
    current_user: dict = Depends(get_current_user),
    repo: FavoriteRepository = Depends(get_favorite_repository)
):
    """
    Toggle favorite for a product (add if not favorited, remove if favorited).
    
    JSON Body:
    {
      "product": "product_id_or_slug"
    }
    
    Returns:
    - 201 with {"action": "added", "product_id": "...", "favorite_id": "..."} if added
    - 200 with {"action": "removed", "product_id": "..."} if removed
    - 200 with {"action": "exists", "product_id": "...", "favorite_id": "..."} if race condition
    """
    try:
        db = get_database()
        
        # Resolve product ID from slug or ObjectId string
        try:
            product_id = await resolve_product_id(db, request.product)
        except HTTPException as e:
            raise e
        
        # Validate product exists
        await validate_product_exists(db, product_id)
        
        # Get user ID from token
        user_id = current_user.get("user_id") or current_user.get("sub") or current_user.get("email")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )
        
        # Toggle favorite
        result = await repo.toggle_favorite(user_id, product_id)
        
        # Set appropriate status code
        if result["action"] == "added":
            return HTTPException(
                status_code=status.HTTP_201_CREATED,
                detail=result
            ).detail if False else result  # Return result with 201 status
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling favorite: {str(e)}"
        )


@router.get("/", response_model=FavoriteListResponse)
async def list_favorites(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    repo: FavoriteRepository = Depends(get_favorite_repository)
):
    """
    Get current user's favorites with embedded product details.
    
    Query params:
    - skip: Number of items to skip (default: 0)
    - limit: Maximum items to return (default: 20, max: 100)
    
    Returns:
    {
      "count": total_favorites,
      "items": [
        {
          "favorite_id": "...",
          "created_at": "...",
          "product": {
            "id": "...",
            "name": "...",
            "slug": "...",
            "price": 123.45,
            "images": [...]
          }
        }
      ]
    }
    """
    try:
        # Get user ID from token
        user_id = current_user.get("user_id") or current_user.get("sub") or current_user.get("email")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )
        
        # Get favorites with product details
        total, favorites = await repo.list_user_favorites(user_id, skip, limit)
        
        # Ensure all data is properly serialized
        serialized_favorites = []
        for favorite in favorites:
            # Make sure all fields are properly converted
            serialized_favorite = {
                "favorite_id": str(favorite.get("favorite_id", "")),
                "created_at": favorite.get("created_at"),
                "product": {
                    "id": str(favorite.get("product", {}).get("id", "")),
                    "name": favorite.get("product", {}).get("name", ""),
                    "slug": favorite.get("product", {}).get("slug"),
                    "price": favorite.get("product", {}).get("price", 0.0),
                    "images": favorite.get("product", {}).get("images", [])
                }
            }
            serialized_favorites.append(serialized_favorite)
        
        return {
            "count": total,
            "items": serialized_favorites
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing favorites: {str(e)}"
        )


@router.get("/check/{product_id_or_slug}", response_model=FavoriteCheckResponse)
async def check_favorite(
    product_id_or_slug: str,
    current_user: dict = Depends(get_current_user),
    repo: FavoriteRepository = Depends(get_favorite_repository)
):
    """
    Check if a product is in current user's favorites.
    
    Returns:
    {
      "favorited": true|false
    }
    """
    try:
        db = get_database()
        
        # Resolve product ID
        try:
            product_id = await resolve_product_id(db, product_id_or_slug)
        except HTTPException:
            # Product not found, return favorited: false
            return {"favorited": False}
        
        # Get user ID from token
        user_id = current_user.get("user_id") or current_user.get("sub") or current_user.get("email")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )
        
        # Check if favorited
        is_favorited = await repo.check_favorite(user_id, product_id)
        
        return {"favorited": is_favorited}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking favorite: {str(e)}"
        )


@router.delete("/{favorite_id}", response_model=FavoriteRemoveResponse)
async def remove_favorite(
    favorite_id: str,
    current_user: dict = Depends(get_current_user),
    repo: FavoriteRepository = Depends(get_favorite_repository)
):
    """
    Remove a favorite by its ID.
    
    Only the owner of the favorite can remove it.
    
    Returns:
    {
      "action": "removed",
      "favorite_id": "..."
    }
    """
    try:
        # Get user ID from token
        user_id = current_user.get("user_id") or current_user.get("sub") or current_user.get("email")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )
        
        # First check if favorite exists and belongs to user
        favorite = await repo.get_favorite_by_id(favorite_id)
        
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found"
            )
        
        # Check ownership
        if favorite["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only remove your own favorites"
            )
        
        # Remove the favorite
        deleted = await repo.remove_favorite(favorite_id, user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found"
            )
        
        return {
            "action": "removed",
            "favorite_id": favorite_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing favorite: {str(e)}"
        )
