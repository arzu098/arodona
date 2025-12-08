"""Schemas for jewelry products."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

class JewelryAttributes(BaseModel):
    """Jewelry attributes schema."""
    metal: str
    purity: str
    diamond_carat: Optional[str] = None
    diamond_clarity: Optional[str] = None
    diamond_color: Optional[str] = None
    diamond_cut: Optional[str] = None
    ring_size: Optional[str] = None
    certification: Optional[str] = None

class JewelrySpecifications(BaseModel):
    """Jewelry specifications schema."""
    weight_grams: float
    dimensions: Dict[str, float]

class JewelryMetadata(BaseModel):
    """Jewelry metadata schema."""
    is_customizable: bool = False
    available_sizes: Optional[List[str]] = None
    customization_options: Optional[List[str]] = None

class JewelryBase(BaseModel):
    """Base schema for jewelry products."""
    name: str
    description: str
    price: float
    category_id: str
    sku: str
    attributes: JewelryAttributes
    specifications: Optional[JewelrySpecifications] = None
    stock_quantity: int = Field(default=0, ge=0)
    images: List[str] = []
    meta: Optional[JewelryMetadata] = None

class JewelryCreate(JewelryBase):
    """Schema for creating jewelry products."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    @field_validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return v
    
    @field_validator('attributes')
    def validate_attributes(cls, v):
        if not v or not isinstance(v, dict):
            raise ValueError("Attributes must be a non-empty dictionary")
        required = ['metal', 'purity']
        missing = [field for field in required if field not in v]
        if missing:
            raise ValueError(f"Missing required attributes: {', '.join(missing)}")
        return v

class JewelryOut(JewelryBase):
    """Schema for jewelry product output."""
    product_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class JewelryCollection(BaseModel):
    """Schema for jewelry collections."""
    name: str
    description: str
    attributes: Dict[str, Any]
    meta: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class JewelryVariant(BaseModel):
    """Schema for jewelry variants."""
    attributes: Dict[str, Any]
    sku: str
    price_adjustment: float = 0.0

    model_config = ConfigDict(from_attributes=True)

class JewelryInventoryUpdate(BaseModel):
    """Schema for updating jewelry inventory."""
    size: str
    quantity: int = Field(ge=0)

class JewelryInventoryUpdateBulk(BaseModel):
    """Schema for bulk updating jewelry inventory."""
    stock_updates: List[JewelryInventoryUpdate]
    low_stock_threshold: Optional[int] = None

class JewelryCertification(BaseModel):
    """Schema for jewelry certification."""
    type: str
    number: str
    issue_date: str
    details: Dict[str, Any]
    document_url: str

    model_config = ConfigDict(from_attributes=True)

class JewelryCustomization(BaseModel):
    """Schema for jewelry customization options."""
    options: Dict[str, Any]
    price_adjustments: Dict[str, Dict[str, float]]

    model_config = ConfigDict(from_attributes=True)