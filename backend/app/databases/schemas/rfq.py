"""Request for Quotation (RFQ) schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, conint

class RFQStatus(str, Enum):
    """RFQ status enum."""
    DRAFT = "draft"
    PUBLISHED = "published"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    AWARDED = "awarded"

class QuoteStatus(str, Enum):
    """Quote status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class RFQItemCreate(BaseModel):
    """Schema for RFQ item creation."""
    name: str = Field(..., description="Item name")
    description: str = Field(..., description="Item description")
    quantity: conint(gt=0) = Field(..., description="Required quantity")
    unit: str = Field(..., description="Unit of measurement")
    specifications: Optional[Dict[str, Any]] = Field(None, description="Technical specifications")
    category_id: Optional[str] = Field(None, description="Product category ID")

class QuoteItemCreate(BaseModel):
    """Schema for quote item creation."""
    rfq_item_id: str = Field(..., description="RFQ item ID")
    unit_price: float = Field(..., gt=0, description="Price per unit")
    total_price: float = Field(..., gt=0, description="Total price for quantity")
    delivery_time: int = Field(..., gt=0, description="Delivery time in days")
    notes: Optional[str] = Field(None, description="Additional notes")

class RFQCreate(BaseModel):
    """Schema for creating a new RFQ."""
    title: str = Field(..., description="RFQ title")
    description: str = Field(..., description="RFQ description")
    items: List[RFQItemCreate] = Field(..., min_items=1, description="Items to quote")
    delivery_location: str = Field(..., description="Delivery location")
    deadline: datetime = Field(..., description="Quote submission deadline")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    additional_terms: Optional[str] = Field(None, description="Additional terms")
    category_ids: Optional[List[str]] = Field(None, description="Target product categories")

class QuoteCreate(BaseModel):
    """Schema for creating a new quote."""
    rfq_id: str = Field(..., description="RFQ ID")
    items: List[QuoteItemCreate] = Field(..., min_items=1, description="Quoted items")
    total_amount: float = Field(..., gt=0, description="Total quote amount")
    validity_period: int = Field(..., gt=0, description="Quote validity in days")
    terms_accepted: bool = Field(..., description="RFQ terms acceptance")
    notes: Optional[str] = Field(None, description="Additional notes")

class RFQResponse(BaseModel):
    """Schema for RFQ response."""
    id: str = Field(..., alias="_id")
    buyer_id: str
    title: str
    description: str
    items: List[Dict[str, Any]]
    delivery_location: str
    deadline: datetime
    payment_terms: Optional[str]
    additional_terms: Optional[str]
    category_ids: Optional[List[str]]
    status: RFQStatus
    created_at: datetime
    updated_at: datetime
    total_quotes: int
    awarded_quote_id: Optional[str]

    class Config:
        allow_population_by_field_name = True

class QuoteResponse(BaseModel):
    """Schema for quote response."""
    id: str = Field(..., alias="_id")
    rfq_id: str
    vendor_id: str
    items: List[Dict[str, Any]]
    total_amount: float
    validity_period: int
    terms_accepted: bool
    notes: Optional[str]
    status: QuoteStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True

class RFQList(BaseModel):
    """Schema for list of RFQs."""
    rfqs: List[RFQResponse]
    total: int
    skip: int
    limit: int

class QuoteList(BaseModel):
    """Schema for list of quotes."""
    quotes: List[QuoteResponse]
    total: int
    skip: int
    limit: int