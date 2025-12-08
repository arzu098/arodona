"""Order management schemas."""

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float
    total: float

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v

    @validator('price', 'total')
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError('Amounts cannot be negative')
        return v

class OrderTotals(BaseModel):
    subtotal: float
    tax: float
    shipping: float
    commission: float
    total: float

class ShippingAddress(BaseModel):
    name: str
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    phone: str

    @validator('name', 'street', 'city', 'state', 'country')
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError('Required address field cannot be empty')
        return v.strip()

class PaymentInfo(BaseModel):
    status: PaymentStatus = PaymentStatus.PENDING
    method: Optional[PaymentMethod] = None
    transaction_id: Optional[str] = None
    gateway_response: Optional[dict] = None

class ShippingInfo(BaseModel):
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

class OrderTimeline(BaseModel):
    status: str
    timestamp: datetime
    note: Optional[str] = None

class OrderCreate(BaseModel):
    items: List[OrderItem]
    shipping_address: ShippingAddress
    billing_address: Optional[ShippingAddress] = None
    payment_method: PaymentMethod
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('Order must contain at least one item')
        return v

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    payment: Optional[PaymentInfo] = None
    shipping: Optional[ShippingInfo] = None

class OrderResponse(BaseModel):
    id: str
    order_number: str
    buyer_id: str
    vendor_id: str
    items: List[OrderItem]
    totals: OrderTotals
    shipping_address: ShippingAddress
    billing_address: ShippingAddress
    status: OrderStatus
    payment: PaymentInfo
    shipping: ShippingInfo
    timeline: List[OrderTimeline]
    created_at: datetime
    updated_at: datetime