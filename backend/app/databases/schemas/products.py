"""Product and catalog schemas."""

from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"

class ModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class MetalType(str, Enum):
    GOLD = "gold"
    SILVER = "silver"
    PLATINUM = "platinum"
    OTHER = "other"

class ProductPrice(BaseModel):
    retail: float
    wholesale: Optional[float] = None
    cost: Optional[float] = None

    @validator('retail')
    def validate_retail_price(cls, v):
        if v <= 0:
            raise ValueError('Retail price must be positive')
        return v

class ProductInventory(BaseModel):
    quantity: int = 0
    reserved: int = 0
    low_stock_threshold: int = 5

    @validator('quantity', 'reserved')
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError('Inventory quantities cannot be negative')
        return v

class Gemstone(BaseModel):
    type: str
    carat: Optional[float] = None
    clarity: Optional[str] = None
    color: Optional[str] = None

class ProductDimensions(BaseModel):
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None

class ProductAttributes(BaseModel):
    material: Optional[str] = None
    metal_type: Optional[MetalType] = None
    metal_purity: Optional[str] = None
    gemstones: List[Gemstone] = []
    weight: Optional[float] = None
    dimensions: Optional[ProductDimensions] = None

class ProductModeration(BaseModel):
    status: ModerationStatus = ModerationStatus.PENDING
    moderated_by: Optional[str] = None
    moderated_at: Optional[datetime] = None
    reason: Optional[str] = None

class ProductSEO(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = []

class ProductCreate(BaseModel):
    name: str
    description: str
    category_id: str
    subcategory_id: Optional[str] = None
    sku: str
    images: List[str] = []
    price: ProductPrice
    inventory: ProductInventory = ProductInventory()
    attributes: ProductAttributes = ProductAttributes()
    tags: List[str] = []
    collections: List[str] = []
    seo: Optional[ProductSEO] = None

    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Product name must be at least 2 characters')
        return v.strip()

    @validator('sku')
    def validate_sku(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('SKU must be at least 3 characters')
        return v.strip().upper()

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    images: Optional[List[str]] = None
    price: Optional[ProductPrice] = None
    inventory: Optional[ProductInventory] = None
    attributes: Optional[ProductAttributes] = None
    tags: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    status: Optional[ProductStatus] = None
    seo: Optional[ProductSEO] = None

class ProductResponse(BaseModel):
    id: str
    vendor_id: str
    name: str
    description: str
    category_id: str
    subcategory_id: Optional[str] = None
    sku: str
    images: List[str] = []
    price: ProductPrice
    inventory: ProductInventory
    attributes: ProductAttributes
    tags: List[str] = []
    collections: List[str] = []
    status: ProductStatus
    moderation: ProductModeration
    seo: Optional[ProductSEO] = None
    created_at: datetime
    updated_at: datetime

# Category schemas
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    image: Optional[str] = None
    sort_order: int = 0

    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Category name must be at least 2 characters')
        return v.strip()

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    image: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class CategoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    image: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    product_count: int = 0
    created_at: datetime
    updated_at: datetime