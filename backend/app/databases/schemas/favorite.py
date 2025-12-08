"""
Pydantic schemas for favorites (wishlist) validation and serialization.
All endpoints accept and return JSON only.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class FavoriteToggleRequest(BaseModel):
    """Schema for toggling a favorite (add/remove)"""
    product: str = Field(..., description="Product ID or slug")


class FavoriteToggleResponse(BaseModel):
    """Schema for toggle response"""
    action: str = Field(..., description="'added', 'removed', or 'exists'")
    product_id: str
    favorite_id: Optional[str] = None


class FavoriteCheckResponse(BaseModel):
    """Schema for checking if product is favorited"""
    favorited: bool


class ProductInFavorite(BaseModel):
    """Embedded product info in favorite response"""
    id: str
    name: str
    slug: Optional[str] = None
    price: float
    images: list = []


class FavoriteItemResponse(BaseModel):
    """Schema for a single favorite item with product details"""
    favorite_id: str
    created_at: datetime
    product: ProductInFavorite


class FavoriteListResponse(BaseModel):
    """Schema for favorite list response"""
    count: int
    items: List[FavoriteItemResponse]


class FavoriteRemoveResponse(BaseModel):
    """Schema for favorite removal response"""
    action: str = "removed"
    favorite_id: str
