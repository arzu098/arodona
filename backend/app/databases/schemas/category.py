"""
Pydantic schemas for category validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CategoryCreate(BaseModel):
    """Schema for creating a category"""
    name: str = Field(..., min_length=1, max_length=100)
    slug: Optional[str] = Field(None, max_length=150)
    parent_id: Optional[str] = None  # Category ID or slug
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, max_length=150)
    parent_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CategoryOut(BaseModel):
    """Schema for category response"""
    id: str = Field(..., alias='_id')
    name: str
    slug: str
    parent_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class CategoryWithChildren(CategoryOut):
    """Schema for nested category with children"""
    children: Optional[List['CategoryOut']] = None
    product_count: Optional[int] = None


class CategoryListOut(BaseModel):
    """Schema for category list response"""
    total: int
    skip: int
    limit: int
    categories: List[CategoryOut]


# Forward reference for recursive type
CategoryWithChildren.model_rebuild()


class CategoryProductsOut(BaseModel):
    """Category with basic info and product count"""
    id: str
    name: str
    slug: str
    product_count: Optional[int] = None
