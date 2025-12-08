from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal

class OrderStatus(str, Enum):
    """Order status enumeration for jewelry e-commerce"""
    PENDING_PAYMENT = "pending_payment"
    PAYMENT_CONFIRMED = "payment_confirmed"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    CRAFTING = "crafting"  # For custom jewelry
    QUALITY_CHECK = "quality_check"
    SHIPPED = "shipped"
    PICKED_UP = "picked_up"  # When delivery boy picks up the order
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DELIVERY_FAILED = "delivery_failed"  # When delivery attempt fails
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    RETURNED = "returned"
    EXCHANGE_REQUESTED = "exchange_requested"
    EXCHANGE_APPROVED = "exchange_approved"
    ASSIGNED = "assigned"
    ASSIGNED_TO_DELIVERY = "assigned_to_delivery"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class FulfillmentStatus(str, Enum):
    """Fulfillment status enumeration"""
    UNFULFILLED = "unfulfilled"
    PARTIAL = "partial"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"

class OrderItemCustomization(BaseModel):
    """Jewelry customization details"""
    size: Optional[str] = None
    engraving: Optional[str] = None
    metal_type: Optional[str] = None
    stone_type: Optional[str] = None
    personalization: Optional[str] = None
    special_instructions: Optional[str] = None


class OrderItem(BaseModel):
    """Schema for an item in an order with jewelry-specific features"""
    product_id: str = Field(..., description="Product ID or slug")
    product_name: str
    product_sku: Optional[str] = None
    product_slug: Optional[str] = None
    product_image: Optional[str] = None
    vendor_id: str
    vendor_name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    
    # Pricing
    unit_price: Decimal = Field(..., description="Original unit price")
    sale_price: Optional[Decimal] = Field(None, description="Sale price if applicable")
    final_price: Decimal = Field(..., description="Final price per unit")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    line_total: Decimal = Field(..., description="Total for this line item")
    
    # Jewelry-specific
    customization: Optional[OrderItemCustomization] = None
    is_custom: bool = Field(False, description="Whether this is a custom order")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    
    # Gift options
    is_gift: bool = Field(False)
    gift_message: Optional[str] = None
    gift_wrapping: bool = Field(False)
    
    # Fulfillment
    fulfillment_status: FulfillmentStatus = Field(FulfillmentStatus.UNFULFILLED)
    tracking_number: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

class CustomerAddress(BaseModel):
    """Schema for customer address"""
    type: str = Field(..., description="billing or shipping")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    company: Optional[str] = Field(None, max_length=100)
    address_line1: str = Field(..., min_length=1, max_length=100)
    address_line2: Optional[str] = Field(None, max_length=100)
    city: str = Field(..., min_length=1, max_length=50)
    state_province: str = Field(..., min_length=1, max_length=50)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country_code: str = Field(..., min_length=2, max_length=3)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Invalid phone number format')
        return v


class ShippingDetails(BaseModel):
    """Comprehensive shipping information"""
    method: str = Field(..., description="standard, express, overnight")
    carrier: Optional[str] = Field(None, description="FedEx, UPS, DHL, etc.")
    service_level: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    cost: Decimal = Field(0.0, description="Shipping cost")
    insurance_value: Optional[Decimal] = None
    signature_required: bool = Field(False)
    
    # Packaging
    packaging_type: Optional[str] = Field(None, description="jewelry_box, gift_box, envelope")
    special_handling: Optional[str] = None

class PaymentDetails(BaseModel):
    """Payment information"""
    method: str = Field(..., description="credit_card, paypal, bank_transfer")
    provider: Optional[str] = Field(None, description="stripe, paypal")
    transaction_id: Optional[str] = None
    payment_intent_id: Optional[str] = None
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field("USD", description="Payment currency")
    status: PaymentStatus = Field(PaymentStatus.PENDING)
    processed_at: Optional[datetime] = None
    
    # For installment payments
    installments: Optional[int] = Field(None, ge=1, le=12)
    installment_amount: Optional[Decimal] = None


class OrderPricing(BaseModel):
    """Comprehensive order pricing breakdown"""
    subtotal: Decimal = Field(..., description="Sum of all line items")
    tax_amount: Decimal = Field(0.0, description="Total tax amount")
    tax_rate: Optional[Decimal] = Field(None, description="Applied tax rate")
    shipping_cost: Decimal = Field(0.0, description="Shipping charges")
    handling_fee: Optional[Decimal] = Field(None, description="Handling charges")
    insurance_fee: Optional[Decimal] = Field(None, description="Insurance charges")
    
    # Discounts
    discount_amount: Decimal = Field(0.0, description="Total discount applied")
    coupon_code: Optional[str] = None
    coupon_discount: Optional[Decimal] = None
    loyalty_discount: Optional[Decimal] = None
    bulk_discount: Optional[Decimal] = None
    
    # Totals
    total_before_tax: Decimal = Field(..., description="Total before tax")
    grand_total: Decimal = Field(..., description="Final total amount")
    
    # Currency
    currency: str = Field("USD")
    exchange_rate: Optional[Decimal] = Field(None, description="If different from base currency")


class OrderCreateRequest(BaseModel):
    """Schema for creating an order from cart"""
    # Customer information
    billing_address: CustomerAddress
    shipping_address: CustomerAddress
    shipping_method: str = Field(..., description="standard, express, overnight")
    
    # Payment
    payment_method: str = Field(..., description="credit_card, paypal, bank_transfer")
    payment_details: Optional[Dict[str, Any]] = None
    
    # Order options
    notes: Optional[str] = Field(None, max_length=500)
    special_instructions: Optional[str] = Field(None, max_length=500)
    gift_message: Optional[str] = Field(None, max_length=200)
    marketing_consent: bool = Field(False)
    
    # Promo codes
    coupon_code: Optional[str] = None
    
    @validator('notes', 'special_instructions', 'gift_message')
    def validate_text_fields(cls, v):
        if v:
            v = v.strip()
            if not v:
                return None
        return v

class OrderUpdateRequest(BaseModel):
    """Schema for updating an order"""
    status: Optional[OrderStatus] = None
    fulfillment_status: Optional[FulfillmentStatus] = None
    payment_status: Optional[PaymentStatus] = None
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class OrderStatusHistory(BaseModel):
    """Order status change history"""
    status: OrderStatus
    changed_by: Optional[str] = None  # user_id or system
    changed_by_type: str = Field("system")  # system, customer, vendor, admin
    timestamp: datetime
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Comprehensive order response schema"""
    id: str = Field(..., description="Order ID")
    order_number: str = Field(..., description="Human-readable order number")
    customer_id: str
    customer_email: Optional[str] = None
    
    # Order items and vendors
    items: List[OrderItem]
    vendor_orders: Optional[Dict[str, List[str]]] = Field(None, description="Items grouped by vendor")
    
    # Addresses
    billing_address: CustomerAddress
    shipping_address: CustomerAddress
    
    # Pricing
    pricing: OrderPricing
    total: Optional[float] = Field(None, description="Total amount for frontend compatibility")
    
    # Status and fulfillment
    status: OrderStatus
    payment_status: PaymentStatus
    fulfillment_status: FulfillmentStatus
    status_history: List[OrderStatusHistory] = Field(default_factory=list)
    
    # Shipping and delivery
    shipping_details: ShippingDetails
    
    # Delivery boy information
    assigned_delivery_boy: Optional[str] = Field(None, description="Delivery boy ID")
    delivery_boy_name: Optional[str] = Field(None, description="Delivery boy name")
    delivery_boy_phone: Optional[str] = Field(None, description="Delivery boy phone")
    delivery_partner: Optional[str] = Field(None, description="Delivery company name")
    delivery_boy_vehicle: Optional[str] = Field(None, description="Vehicle type")
    address: Optional[str] = Field(None, description="Formatted delivery address")
    delivery_address: Optional[str] = Field(None, description="Delivery address")
    
    # Payment
    payment_details: PaymentDetails
    payment_method: Optional[str] = Field(None, description="Payment method used")
    
    # Metadata
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Analytics
    source: Optional[str] = Field(None, description="web, mobile, api")
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None

class OrderSummary(BaseModel):
    """Simplified order summary for lists"""
    id: str
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: Decimal
    currency: str
    item_count: int
    customer_name: str
    created_at: datetime
    estimated_delivery: Optional[datetime] = None


class OrderListResponse(BaseModel):
    """Schema for paginated order list response"""
    total: int
    page: int
    per_page: int
    total_pages: int
    orders: List[OrderSummary]


class OrderCancelRequest(BaseModel):
    """Schema for cancelling an order"""
    reason: str = Field(..., min_length=10, max_length=500)
    refund_method: Optional[str] = Field(None, description="original_payment, store_credit")
    
    @validator('reason')
    def validate_reason(cls, v):
        return v.strip()


class OrderReturnItem(BaseModel):
    """Individual item return details"""
    item_id: str
    product_id: str
    quantity: int = Field(..., ge=1)
    reason: str = Field(..., description="defective, wrong_item, not_as_described, changed_mind")
    condition: str = Field(..., description="unopened, opened, damaged")
    photos: Optional[List[str]] = Field(None, description="Photo evidence URLs")


class OrderReturnRequest(BaseModel):
    """Schema for creating a return request"""
    order_id: str
    items: List[OrderReturnItem]
    overall_reason: str = Field(..., min_length=10, max_length=500)
    preferred_resolution: str = Field(..., description="refund, exchange, store_credit")
    additional_comments: Optional[str] = Field(None, max_length=1000)
    
    @validator('overall_reason', 'additional_comments')
    def validate_text_fields(cls, v):
        if v:
            v = v.strip()
            if not v:
                return None
        return v


class OrderReturnResponse(BaseModel):
    """Schema for return request response"""
    id: str
    return_number: str
    order_id: str
    order_number: str
    customer_id: str
    items: List[OrderReturnItem]
    overall_reason: str
    preferred_resolution: str
    status: str = Field(..., description="pending, approved, rejected, processed")
    
    # Resolution details
    approved_amount: Optional[Decimal] = None
    refund_method: Optional[str] = None
    replacement_order_id: Optional[str] = None
    store_credit_amount: Optional[Decimal] = None
    
    # Processing
    processed_by: Optional[str] = None
    processed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    
    # Logistics
    return_shipping_label: Optional[str] = None
    return_tracking_number: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class OrderAnalytics(BaseModel):
    """Order analytics data"""
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    orders_by_status: Dict[str, int]
    top_products: List[Dict[str, Any]]
    top_vendors: List[Dict[str, Any]]
    conversion_metrics: Dict[str, Any]