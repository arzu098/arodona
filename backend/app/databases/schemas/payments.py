"""Comprehensive Payment Processing Schemas for Jewelry E-commerce."""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from decimal import Decimal

class PaymentGateway(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    RAZORPAY = "razorpay"
    SQUARE = "square"
    AUTHORIZE_NET = "authorize_net"

class PaymentStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    PROCESSING = "processing"
    REQUIRES_ACTION = "requires_action"
    REQUIRES_CAPTURE = "requires_capture"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"
    CHARGEBACK = "chargeback"

class PaymentMethodType(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    PAYPAL = "paypal"
    UPI = "upi"
    KLARNA = "klarna"
    AFTERPAY = "afterpay"
    INSTALLMENTS = "installments"

class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"

class PaymentAddress(BaseModel):
    """Billing address for payment processing"""
    first_name: str
    last_name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str


class PaymentMethodDetails(BaseModel):
    """Payment method specific details"""
    type: PaymentMethodType
    card_number: Optional[str] = Field(None, description="Card number (will be tokenized)")
    exp_month: Optional[int] = Field(None, ge=1, le=12)
    exp_year: Optional[int] = Field(None, ge=2023)
    cvc: Optional[str] = Field(None, min_length=3, max_length=4)
    cardholder_name: Optional[str] = None
    
    # Digital wallet details
    wallet_type: Optional[str] = None
    wallet_token: Optional[str] = None
    
    # Bank transfer details
    bank_account: Optional[str] = None
    routing_number: Optional[str] = None
    
    # Buy now pay later details
    installment_plan: Optional[int] = Field(None, ge=3, le=24)


class PaymentInitiateRequest(BaseModel):
    """Request to initiate a payment"""
    order_id: str = Field(..., description="Order ID to process payment for")
    gateway: PaymentGateway = Field(PaymentGateway.STRIPE, description="Payment gateway to use")
    payment_method: Optional[PaymentMethodDetails] = None
    saved_payment_method_id: Optional[str] = None
    
    # Payment options
    capture_method: str = Field("automatic", description="automatic or manual")
    save_payment_method: bool = Field(False, description="Save payment method for future use")
    
    # Customer details for guest checkout
    customer_email: Optional[str] = None
    billing_address: Optional[PaymentAddress] = None
    
    # Return URLs
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None
    
    # Metadata
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    @validator('order_id')
    def validate_order_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Order ID is required')
        return v.strip()

class PaymentResponse(BaseModel):
    """Comprehensive payment response"""
    id: str = Field(..., description="Internal payment ID")
    payment_id: str = Field(..., description="Payment ID")
    order_id: str
    order_number: Optional[str] = None
    customer_id: str
    
    # Amount details
    amount: Decimal
    currency: Currency
    amount_captured: Optional[Decimal] = None
    amount_refunded: Optional[Decimal] = None
    
    # Status and processing
    status: PaymentStatus
    gateway: PaymentGateway
    gateway_payment_id: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    
    # Payment method information
    payment_method: Optional[Dict[str, Any]] = None
    
    # Client integration
    client_secret: Optional[str] = None
    payment_url: Optional[str] = None
    next_action: Optional[Dict[str, Any]] = None
    
    # Fees and commissions
    platform_fee: Optional[Decimal] = None
    gateway_fee: Optional[Decimal] = None
    vendor_payouts: Optional[List[Dict[str, Any]]] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    authorized_at: Optional[datetime] = None
    captured_at: Optional[datetime] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Risk assessment
    risk_score: Optional[float] = None
    fraud_details: Optional[Dict[str, Any]] = None

class WebhookPayload(BaseModel):
    """Payment gateway webhook payload"""
    event_type: str = Field(..., description="Type of webhook event")
    payment_id: Optional[str] = None
    gateway_payment_id: str = Field(..., description="Gateway's payment ID")
    status: str
    gateway: PaymentGateway
    
    # Signature verification
    signature: Optional[str] = None
    timestamp: Optional[int] = None
    
    # Event data
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Metadata
    created: Optional[int] = None
    livemode: Optional[bool] = None


class RefundReason(str, Enum):
    DUPLICATE = "duplicate"
    FRAUDULENT = "fraudulent"
    REQUESTED_BY_CUSTOMER = "requested_by_customer"
    PROCESSING_ERROR = "processing_error"
    PRODUCT_NOT_RECEIVED = "product_not_received"
    PRODUCT_DEFECTIVE = "product_defective"
    OTHER = "other"


class RefundRequest(BaseModel):
    """Request to refund a payment"""
    payment_id: str
    amount: Optional[Decimal] = Field(None, description="Partial refund amount, full if not specified")
    reason: RefundReason
    description: Optional[str] = Field(None, max_length=500, description="Additional refund details")
    refund_application_fee: bool = Field(False, description="Whether to refund application fee")
    reverse_transfer: bool = Field(True, description="Whether to reverse transfer to vendor")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Refund amount must be positive')
        return v


class RefundStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RefundResponse(BaseModel):
    """Refund processing response"""
    id: str
    refund_id: str
    payment_id: str
    order_id: str
    
    # Amount details
    amount: Decimal
    currency: Currency
    
    # Status and processing
    status: RefundStatus
    gateway: PaymentGateway
    gateway_refund_id: Optional[str] = None
    
    # Details
    reason: RefundReason
    description: Optional[str] = None
    
    # Fees
    fee_refunded: Optional[Decimal] = None
    
    # Processing info
    processed_by: Optional[str] = None
    failure_reason: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PaymentMethodSaveRequest(BaseModel):
    """Request to save a payment method"""
    type: PaymentMethodType
    gateway: PaymentGateway = PaymentGateway.STRIPE
    
    # Card details (will be tokenized)
    card_number: Optional[str] = None
    exp_month: Optional[int] = Field(None, ge=1, le=12)
    exp_year: Optional[int] = Field(None, ge=2023)
    cvc: Optional[str] = None
    cardholder_name: Optional[str] = None
    
    # Bank account details
    account_number: Optional[str] = None
    routing_number: Optional[str] = None
    account_holder_name: Optional[str] = None
    
    # Billing address
    billing_address: Optional[PaymentAddress] = None
    
    # Preferences
    is_default: bool = Field(False)
    nickname: Optional[str] = Field(None, max_length=50)


class PaymentMethodResponse(BaseModel):
    """Saved payment method response"""
    id: str
    customer_id: str
    type: PaymentMethodType
    gateway: PaymentGateway
    gateway_method_id: str
    
    # Masked details
    last_four: Optional[str] = None
    brand: Optional[str] = None
    funding: Optional[str] = None
    expires_month: Optional[int] = None
    expires_year: Optional[int] = None
    
    # Bank account details
    bank_name: Optional[str] = None
    account_type: Optional[str] = None
    
    # Status and preferences
    is_default: bool = False
    is_verified: bool = False
    nickname: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None


class VendorPayoutStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

# Alias for backward compatibility
PayoutStatus = VendorPayoutStatus

class PayoutMethod(str, Enum):
    BANK_ACCOUNT = "bank_account"
    PAYPAL = "paypal"
    WIRE_TRANSFER = "wire_transfer"
    CHECK = "check"
    DIGITAL_WALLET = "digital_wallet"


class VendorPayoutRequest(BaseModel):
    """Request for vendor payout"""
    vendor_id: str
    payout_method: str = Field("bank_account", description="bank_account, paypal, etc.")
    currency: Currency = Currency.USD
    
    # Optional filters for calculating payout
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    order_ids: Optional[List[str]] = None


class VendorPayout(BaseModel):
    """Vendor payout details"""
    id: str
    payout_id: str
    vendor_id: str
    vendor_name: str
    
    # Calculation breakdown
    gross_sales: Decimal
    commission_rate: float
    commission_amount: Decimal
    platform_fee: Decimal
    gateway_fees: Decimal
    adjustments: Decimal
    net_amount: Decimal
    currency: Currency
    
    # Processing
    status: VendorPayoutStatus
    gateway: Optional[PaymentGateway] = None
    gateway_payout_id: Optional[str] = None
    payout_method: str
    
    # Bank details (masked)
    bank_account_last_four: Optional[str] = None
    
    # Order details
    order_ids: List[str]
    order_count: int
    
    # Timestamps
    period_start: datetime
    period_end: datetime
    scheduled_at: datetime
    processed_at: Optional[datetime] = None
    created_at: datetime
    
    # Processing details
    processed_by: Optional[str] = None
    failure_reason: Optional[str] = None
    notes: Optional[str] = None


class PaymentAnalytics(BaseModel):
    """Payment analytics and metrics"""
    total_revenue: Decimal
    total_transactions: int
    successful_payments: int
    failed_payments: int
    refunded_amount: Decimal
    average_transaction_value: Decimal
    
    # By payment method
    payment_methods: Dict[str, Dict[str, Any]]
    
    # By currency
    currency_breakdown: Dict[str, Decimal]
    
    # Fees
    total_gateway_fees: Decimal
    total_platform_fees: Decimal
    
    # Vendor payouts
    total_vendor_payouts: Decimal
    pending_vendor_payouts: Decimal
    
    # Date range
    period_start: datetime
    period_end: datetime


class PaymentIntent(BaseModel):
    """Payment intent for processing"""
    id: str
    amount: Decimal
    currency: Currency
    status: PaymentStatus
    client_secret: str
    payment_method_types: List[str]
    
    # Customer details
    customer_id: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, str]
    
    # Processing details
    capture_method: str
    confirmation_method: str
    
    # Timestamps
    created_at: datetime
    
    # Next action for 3D Secure etc.
    next_action: Optional[Dict[str, Any]] = None


class DisputeStatus(str, Enum):
    WARNING_NEEDS_RESPONSE = "warning_needs_response"
    WARNING_UNDER_REVIEW = "warning_under_review"
    WARNING_CLOSED = "warning_closed"
    NEEDS_RESPONSE = "needs_response"
    UNDER_REVIEW = "under_review"
    CHARGE_REFUNDED = "charge_refunded"
    WON = "won"
    LOST = "lost"


class PaymentDispute(BaseModel):
    """Payment dispute/chargeback details"""
    id: str
    payment_id: str
    amount: Decimal
    currency: Currency
    reason: str
    status: DisputeStatus
    
    # Evidence and response
    evidence_due_by: Optional[datetime] = None
    evidence_submitted: bool = False
    
    # Dispute details
    created: datetime
    gateway_dispute_id: str
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
