"""
Comprehensive shopping cart schemas with jewelry-specific features.
Supports size variations, guest checkout, and advanced pricing calculations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

class CartItemType(str, Enum):
    """Enum for cart item types"""
    PRODUCT = "product"
    GIFT_CARD = "gift_card"
    SHIPPING = "shipping"
    TAX = "tax"
    DISCOUNT = "discount"

class CheckoutStep(str, Enum):
    """Enum for checkout steps"""
    CART = "cart"
    SHIPPING = "shipping"
    PAYMENT = "payment"
    CONFIRMATION = "confirmation"
    COMPLETE = "complete"

class DiscountType(str, Enum):
    """Enum for discount types"""
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_SHIPPING = "free_shipping"
    BUY_X_GET_Y = "buy_x_get_y"


class CartItemCreate(BaseModel):
    """Schema for adding items to cart with jewelry-specific options"""
    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(..., ge=1, le=10, description="Quantity (max 10 per item)")
    size: Optional[str] = Field(None, description="Size selection (for rings, bracelets, etc.)")
    variant_id: Optional[str] = Field(None, description="Product variant ID (color, material, etc.)")
    personalization: Optional[Dict[str, str]] = Field(None, description="Personalization options (engraving, etc.)")
    gift_message: Optional[str] = Field(None, max_length=500, description="Gift message")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 10:
            raise ValueError('Maximum quantity per item is 10')
        return v


class CartItemUpdate(BaseModel):
    """Schema for updating cart item"""
    quantity: int = Field(..., ge=0, le=10, description="New quantity (0 to remove)")
    size: Optional[str] = Field(None, description="Update size selection")
    personalization: Optional[Dict[str, str]] = Field(None, description="Update personalization")
    gift_message: Optional[str] = Field(None, max_length=500, description="Update gift message")

class CartItemRemove(BaseModel):
    """Schema for removing specific cart item"""
    cart_item_id: str = Field(..., description="Cart item ID to remove")

class CouponApplication(BaseModel):
    """Schema for applying coupon/discount code"""
    code: str = Field(..., min_length=3, max_length=50, description="Coupon code")
    
    @validator('code')
    def validate_code(cls, v):
        return v.upper().strip()

# Alias for backward compatibility
DiscountApplication = CouponApplication

class ShippingAddress(BaseModel):
    """Schema for shipping address"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=200)
    address_line_1: str = Field(..., min_length=5, max_length=200)
    address_line_2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    state_province: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field(..., min_length=2, max_length=3, description="Country code (ISO 2 or 3 letter)")
    phone: Optional[str] = Field(None, max_length=20)
    is_business_address: bool = Field(False, description="Whether this is a business address")

class BillingAddress(BaseModel):
    """Schema for billing address"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=200)
    address_line_1: str = Field(..., min_length=5, max_length=200)
    address_line_2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    state_province: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field(..., min_length=2, max_length=3)
    same_as_shipping: bool = Field(False, description="Use shipping address for billing")

class ShippingOption(BaseModel):
    """Schema for shipping method selection"""
    carrier: str = Field(..., description="Shipping carrier (UPS, FedEx, USPS, etc.)")
    service_code: str = Field(..., description="Service code (Ground, Express, etc.)")
    service_name: str = Field(..., description="Human-readable service name")
    estimated_days: int = Field(..., ge=1, le=30, description="Estimated delivery days")
    cost: float = Field(..., ge=0, description="Shipping cost")
    is_insured: bool = Field(False, description="Whether shipping is insured")
    tracking_available: bool = Field(True, description="Whether tracking is available")


class CartItemResponse(BaseModel):
    """Schema for cart item in responses"""
    id: str = Field(..., description="Cart item ID")
    product_id: str
    product_name: str
    product_slug: Optional[str] = None
    vendor_id: str
    vendor_name: str
    sku: Optional[str] = None
    image_url: Optional[str] = None
    
    # Pricing
    unit_price: float = Field(..., description="Price per unit")
    compare_at_price: Optional[float] = None
    quantity: int
    line_total: float = Field(..., description="Total for this line item")
    
    # Product specifics
    size: Optional[str] = None
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None
    jewelry_type: Optional[str] = None
    metal_type: Optional[str] = None
    
    # Customization
    personalization: Optional[Dict[str, str]] = None
    gift_message: Optional[str] = None
    
    # Inventory status
    in_stock: bool = True
    stock_quantity: Optional[int] = None
    available_quantity: int = Field(..., description="Max quantity that can be added")
    
    # Item status
    is_available: bool = True
    availability_message: Optional[str] = None
    
    added_at: datetime

class PricingBreakdown(BaseModel):
    """Schema for detailed pricing breakdown"""
    subtotal: float = Field(..., description="Sum of all line totals")
    item_discount: float = Field(0, description="Discount on items")
    shipping_cost: float = Field(0, description="Shipping and handling")
    shipping_discount: float = Field(0, description="Shipping discount")
    tax_amount: float = Field(0, description="Tax amount")
    total_discount: float = Field(0, description="Total discounts applied")
    total_amount: float = Field(..., description="Final total amount")
    
    # Currency
    currency: str = Field("USD", description="Currency code")
    
    # Savings summary
    you_save: float = Field(0, description="Total amount saved")

class AppliedDiscount(BaseModel):
    """Schema for applied discounts/coupons"""
    code: str
    description: str
    discount_type: DiscountType
    discount_value: float
    discount_amount: float
    minimum_order: Optional[float] = None
    maximum_discount: Optional[float] = None
    applies_to: str = Field("cart", description="What the discount applies to")

class CartSummary(BaseModel):
    """Schema for cart summary information"""
    total_items: int = Field(..., description="Total number of items")
    total_quantity: int = Field(..., description="Total quantity of all items")
    unique_vendors: int = Field(..., description="Number of different vendors")
    estimated_weight: Optional[float] = Field(None, description="Estimated total weight in grams")
    requires_shipping: bool = Field(True, description="Whether cart requires shipping")

class CartResponse(BaseModel):
    """Schema for comprehensive cart response"""
    id: str = Field(..., description="Cart ID")
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Cart contents
    items: List[CartItemResponse] = []
    summary: CartSummary
    pricing: PricingBreakdown
    applied_discounts: List[AppliedDiscount] = []
    
    # Checkout information
    checkout_step: CheckoutStep = CheckoutStep.CART
    shipping_address: Optional[ShippingAddress] = None
    billing_address: Optional[BillingAddress] = None
    selected_shipping: Optional[ShippingOption] = None
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = []
    
    # Metadata
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class CartItemCheck(BaseModel):
    """Schema for checking if specific item is in cart"""
    in_cart: bool
    quantity: int = 0
    cart_item_id: Optional[str] = None
    max_quantity: Optional[int] = None

class AddToCartResponse(BaseModel):
    """Schema for add to cart response"""
    success: bool
    message: str
    cart_item_id: Optional[str] = None
    cart_summary: Optional[CartSummary] = None
    suggested_items: Optional[List[Dict[str, Any]]] = None

class CheckoutValidation(BaseModel):
    """Schema for checkout validation"""
    is_valid: bool
    can_checkout: bool
    errors: List[str] = []
    warnings: List[str] = []
    
    # Requirements
    requires_shipping_address: bool = False
    requires_billing_address: bool = False
    requires_shipping_method: bool = False
    requires_payment_method: bool = False
    
    # Inventory validation
    inventory_issues: List[Dict[str, Any]] = []

class GuestCheckoutInfo(BaseModel):
    """Schema for guest checkout information"""
    email: str = Field(..., description="Guest email for order updates")
    phone: Optional[str] = Field(None, description="Guest phone number")
    subscribe_newsletter: bool = Field(False, description="Subscribe to newsletter")
    create_account: bool = Field(False, description="Create account after checkout")

class CartMergeRequest(BaseModel):
    """Schema for merging guest cart with user account"""
    guest_cart_id: str = Field(..., description="Guest cart session ID")
    merge_strategy: str = Field("combine", pattern="^(combine|replace|keep_user)$")