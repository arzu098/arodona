"""
Pydantic schemas for review validation and serialization.
All endpoints accept and return JSON only (no images, no form-data).
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime


class ReviewCreate(BaseModel):
    """Schema for creating a review (JSON only)"""
    product: str = Field(..., description="Product ID or slug")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    title: Optional[str] = Field(None, max_length=200)
    body: Optional[str] = Field(None, max_length=2000)
    images: Optional[List[str]] = Field(None, description="List of uploaded image URLs")
    
    @validator('body')
    def validate_body_length(cls, v):
        if v and len(v) > 2000:
            raise ValueError('Review body cannot exceed 2000 characters')
        return v


class ReviewUpdate(BaseModel):
    """Schema for updating a review"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    body: Optional[str] = Field(None, max_length=2000)
    
    @validator('body')
    def validate_body_length(cls, v):
        if v and len(v) > 2000:
            raise ValueError('Review body cannot exceed 2000 characters')
        return v


class ReviewResponse(BaseModel):
    """Schema for review response"""
    id: str
    product_id: str
    user_id: str
    full_name: Optional[str] = None
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    images: List[str] = Field(default_factory=list, description="List of review image URLs")
    is_verified_buyer: bool = False
    approved: bool = True
    helpful_count: int = 0
    created_at: datetime
    updated_at: datetime
    deleted: bool = False


class ReviewListResponse(BaseModel):
    """Schema for review list response with metadata"""
    meta: Dict = Field(default_factory=dict)
    items: list
    count: int


class ReviewApprovalRequest(BaseModel):
    """Schema for approving/rejecting reviews"""
    approved: bool


class ReviewHelpfulRequest(BaseModel):
    """Schema for marking review as helpful"""
    action: str = Field("increment", pattern="^(increment|decrement)$")


class RatingsBreakdown(BaseModel):
    """Ratings breakdown by star count"""
    one: int = Field(0, alias="1")
    two: int = Field(0, alias="2")
    three: int = Field(0, alias="3")
    four: int = Field(0, alias="4")
    five: int = Field(0, alias="5")
    
    class Config:
        populate_by_name = True


class ProductInReview(BaseModel):
    """Product information in review response"""
    id: str
    name: str
    slug: Optional[str] = None
    price: float
    images: list = []


class UserReviewWithProduct(BaseModel):
    """Schema for user review with product details"""
    review_id: str
    product: ProductInReview
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    images: List[str] = Field(default_factory=list, description="List of review image URLs")
    created_at: datetime
    updated_at: datetime


class UserReviewsResponse(BaseModel):
    """Schema for user's reviews list response"""
    count: int
    items: List[UserReviewWithProduct]
