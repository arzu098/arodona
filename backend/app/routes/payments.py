"""
Comprehensive Payment API for Jewelry E-commerce.
Handles payment processing, Stripe integration, refunds, 
vendor payouts, payment methods, and analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, Header, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import stripe
import os

from app.databases.schemas.payments import (
    PaymentInitiateRequest, PaymentResponse, WebhookPayload, RefundRequest, RefundResponse,
    PaymentMethodSaveRequest, PaymentMethodResponse, VendorPayoutRequest, VendorPayout,
    PaymentAnalytics, PaymentStatus, PaymentGateway, Currency, RefundStatus,
    PayoutStatus, PayoutMethod, PaymentMethodType
)
from app.databases.repositories.payment import PaymentRepository
from app.databases.repositories.order import OrderRepository
from app.db.connection import get_database
from app.utils.dependencies import get_current_user_optional
from app.utils.security import get_current_user
from app.utils.errors import ErrorCode, AppError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")


# Dependency functions
async def get_payment_repository() -> PaymentRepository:
    """Get payment repository instance"""
    db = get_database()
    return PaymentRepository(db)

async def get_order_repository() -> OrderRepository:
    """Get order repository instance"""
    db = get_database()
    return OrderRepository(db)


@router.post("/initiate", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    request: PaymentInitiateRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    order_repo: OrderRepository = Depends(get_order_repository)
):
    """Initiate payment for an order with Stripe integration"""
    try:
        # Get order details
        order = await order_repo.get_order_by_id(request.order_id)
        if not order:
            raise AppError(
                message="Order not found",
                error_code=ErrorCode.ORDER_NOT_FOUND,
                status_code=404
            )
        
        # Validate order ownership
        customer_id = None
        if current_user:
            customer_id = current_user.get("user_id") or current_user.get("sub")
            if order["customer_id"] != customer_id:
                raise AppError(
                    message="Access denied to this order",
                    error_code=ErrorCode.ACCESS_DENIED,
                    status_code=403
                )
        else:
            # Guest checkout - validate with order details
            customer_id = order["customer_id"]
            if not request.customer_email or order.get("customer_email") != request.customer_email:
                raise AppError(
                    message="Invalid customer email for order",
                    error_code=ErrorCode.ACCESS_DENIED,
                    status_code=403
                )
        
        # Create payment record
        payment_data = {
            "order_id": request.order_id,
            "customer_id": customer_id,
            "amount": order["pricing"]["grand_total"],
            "currency": order["pricing"]["currency"],
            "gateway": request.gateway.value,
            "metadata": {
                "order_number": order["order_number"],
                **request.metadata
            }
        }
        
        payment = await payment_repo.create_payment(payment_data)
        
        # Create Stripe Payment Intent
        if request.gateway == PaymentGateway.STRIPE:
            try:
                stripe_intent = stripe.PaymentIntent.create(
                    amount=int(float(order["pricing"]["grand_total"]) * 100),  # Stripe expects cents
                    currency=order["pricing"]["currency"].lower(),
                    customer=customer_id if current_user else None,
                    payment_method_types=["card", "apple_pay", "google_pay"],
                    capture_method=request.capture_method,
                    setup_future_usage="on_session" if request.save_payment_method else None,
                    metadata={
                        "payment_id": payment["payment_id"],
                        "order_id": request.order_id,
                        "customer_id": customer_id
                    }
                )
                
                # Update payment with Stripe details
                await payment_repo.update_payment(
                    payment["payment_id"],
                    {
                        "gateway_payment_id": stripe_intent.id,
                        "client_secret": stripe_intent.client_secret,
                        "status": PaymentStatus.PENDING.value
                    }
                )
                
                payment.update({
                    "gateway_payment_id": stripe_intent.id,
                    "client_secret": stripe_intent.client_secret,
                    "status": PaymentStatus.PENDING.value
                })
                
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error: {str(e)}")
                raise AppError(
                    message="Payment processing error",
                    error_code=ErrorCode.PAYMENT_PROCESSING_ERROR,
                    details={"stripe_error": str(e)}
                )
        
        return PaymentResponse(
            id=str(payment["_id"]),
            payment_id=payment["payment_id"],
            order_id=payment["order_id"],
            order_number=order["order_number"],
            customer_id=payment["customer_id"],
            amount=payment["amount"],
            currency=Currency(payment["currency"]),
            status=PaymentStatus(payment["status"]),
            gateway=PaymentGateway(payment["gateway"]),
            gateway_payment_id=payment.get("gateway_payment_id"),
            client_secret=payment.get("client_secret"),
            payment_url=payment.get("payment_url"),
            created_at=payment["created_at"],
            updated_at=payment["updated_at"],
            metadata=payment.get("metadata", {})
        )
    
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}")
        raise AppError(
            message="Failed to initiate payment",
            error_code=ErrorCode.PAYMENT_PROCESSING_ERROR,
            details={"error": str(e)}
        )


@router.post("/webhook")
async def payment_webhook(payload: WebhookPayload, request: Request):
    """Receive webhooks from payment providers.

    This endpoint verifies/records provider status changes and updates internal payment records.
    For simplicity we accept a JSON payload in a generic schema.
    """
    try:
        # Optionally verify signature here (payload.signature)
        payment = await PaymentRepository.get_payment(payload.payment_id)
        if not payment:
            # Log and return 404 to provider if needed
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

        updated = await PaymentRepository.update_payment(payload.payment_id, {"status": payload.status})

        return {"ok": True, "payment_id": payload.payment_id, "status": updated.get("status")}

    except HTTPException:
        raise
    except Exception as e:
        # Avoid raising 500 to payment provider if unexpected — return 200 with error details minimized
        return {"ok": False, "error": "processing_error"}


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    payment = await PaymentRepository.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    # Basic ownership check
    user_id = current_user.get("user_id") or current_user.get("sub")
    if payment.get("user_id") != user_id and current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return PaymentResponse(
        payment_id=payment["payment_id"],
        order_id=payment["order_id"],
        amount=payment["amount"],
        currency=payment.get("currency", "INR"),
        status=payment.get("status", "pending"),
        payment_url=payment.get("payment_url"),
        created_at=payment.get("created_at")
    )


@router.post("/{payment_id}/refund", response_model=RefundResponse)
async def refund_payment(
    payment_id: str,
    request: RefundRequest,
    current_user: dict = Depends(get_current_user),
    payment_repo: PaymentRepository = Depends(get_payment_repository)
):
    """Process payment refund"""
    try:
        # Get payment record
        payment = await payment_repo.get_payment_by_id(payment_id)
        if not payment:
            raise AppError(
                message="Payment not found",
                error_code=ErrorCode.PAYMENT_NOT_FOUND,
                status_code=404
            )
        
        # Validate ownership or admin access
        user_id = current_user.get("user_id") or current_user.get("sub")
        is_admin = current_user.get("role") == "admin"
        
        if payment["customer_id"] != user_id and not is_admin:
            raise AppError(
                message="Access denied to this payment",
                error_code=ErrorCode.ACCESS_DENIED,
                status_code=403
            )
        
        # Validate payment status
        if payment["status"] not in [PaymentStatus.COMPLETED.value, PaymentStatus.PARTIALLY_REFUNDED.value]:
            raise AppError(
                message="Payment cannot be refunded",
                error_code=ErrorCode.INVALID_PAYMENT_STATUS,
                status_code=400,
                details={"current_status": payment["status"]}
            )
        
        # Validate refund amount
        refund_amount = request.amount or payment["amount"]
        if refund_amount <= 0:
            raise AppError(
                message="Refund amount must be greater than 0",
                error_code=ErrorCode.INVALID_AMOUNT,
                status_code=400
            )
        
        if refund_amount > payment["amount"]:
            raise AppError(
                message="Refund amount cannot exceed payment amount",
                error_code=ErrorCode.INVALID_AMOUNT,
                status_code=400
            )
        
        # Check existing refunds
        existing_refunds = await payment_repo.get_refunds_by_payment_id(payment_id)
        total_refunded = sum(r["amount"] for r in existing_refunds if r["status"] != RefundStatus.FAILED.value)
        
        if total_refunded + refund_amount > payment["amount"]:
            raise AppError(
                message="Total refund amount would exceed payment amount",
                error_code=ErrorCode.INVALID_AMOUNT,
                status_code=400,
                details={
                    "payment_amount": payment["amount"],
                    "already_refunded": total_refunded,
                    "requested_refund": refund_amount
                }
            )
        
        # Create refund record
        refund_data = {
            "payment_id": payment_id,
            "order_id": payment["order_id"],
            "amount": refund_amount,
            "currency": payment["currency"],
            "reason": request.reason,
            "requested_by": user_id,
            "gateway": payment["gateway"]
        }
        
        refund = await payment_repo.create_refund(refund_data)
        
        # Process refund with gateway
        if payment["gateway"] == PaymentGateway.STRIPE.value and payment.get("gateway_payment_id"):
            try:
                stripe_refund = stripe.Refund.create(
                    payment_intent=payment["gateway_payment_id"],
                    amount=int(refund_amount * 100),  # Stripe expects cents
                    reason=request.reason if request.reason in ["duplicate", "fraudulent", "requested_by_customer"] else "requested_by_customer",
                    metadata={
                        "refund_id": refund["refund_id"],
                        "payment_id": payment_id,
                        "requested_by": user_id
                    }
                )
                
                # Update refund with Stripe details
                await payment_repo.update_refund(
                    refund["refund_id"],
                    {
                        "gateway_refund_id": stripe_refund.id,
                        "status": RefundStatus.PROCESSING.value,
                        "gateway_response": {
                            "status": stripe_refund.status,
                            "receipt_number": stripe_refund.receipt_number
                        }
                    }
                )
                
                refund.update({
                    "gateway_refund_id": stripe_refund.id,
                    "status": RefundStatus.PROCESSING.value
                })
                
            except stripe.error.StripeError as e:
                logger.error(f"Stripe refund error: {str(e)}")
                await payment_repo.update_refund(
                    refund["refund_id"],
                    {
                        "status": RefundStatus.FAILED.value,
                        "gateway_response": {"error": str(e)}
                    }
                )
                raise AppError(
                    message="Refund processing failed",
                    error_code=ErrorCode.REFUND_PROCESSING_ERROR,
                    details={"stripe_error": str(e)}
                )
        
        return RefundResponse(
            id=str(refund["_id"]),
            refund_id=refund["refund_id"],
            payment_id=refund["payment_id"],
            order_id=refund["order_id"],
            amount=refund["amount"],
            currency=Currency(refund["currency"]),
            status=RefundStatus(refund["status"]),
            reason=refund.get("reason"),
            gateway_refund_id=refund.get("gateway_refund_id"),
            requested_by=refund["requested_by"],
            created_at=refund["created_at"],
            processed_at=refund.get("processed_at"),
            metadata=refund.get("metadata", {})
        )
    
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        raise AppError(
            message="Failed to process refund",
            error_code=ErrorCode.REFUND_PROCESSING_ERROR,
            details={"error": str(e)}
        )


@router.post("/methods/save", response_model=PaymentMethodResponse)
async def save_payment_method(
    request: PaymentMethodSaveRequest,
    current_user: dict = Depends(get_current_user),
    payment_repo: PaymentRepository = Depends(get_payment_repository)
):
    """Save payment method for future use"""
    try:
        customer_id = current_user.get("user_id") or current_user.get("sub")
        
        # Create Stripe customer if doesn't exist
        if request.gateway == PaymentGateway.STRIPE:
            try:
                # Check for existing customer
                customers = stripe.Customer.list(metadata={"customer_id": customer_id})
                
                if customers.data:
                    stripe_customer = customers.data[0]
                else:
                    # Create new Stripe customer
                    stripe_customer = stripe.Customer.create(
                        email=current_user.get("email"),
                        metadata={"customer_id": customer_id}
                    )
                
                # Attach payment method to customer
                stripe.PaymentMethod.attach(
                    request.payment_method_token,
                    customer=stripe_customer.id
                )
                
                # Save payment method record
                method_data = {
                    "customer_id": customer_id,
                    "gateway": request.gateway.value,
                    "gateway_method_id": request.payment_method_token,
                    "gateway_customer_id": stripe_customer.id,
                    "type": request.method_type.value,
                    "last_four": request.last_four,
                    "brand": request.brand,
                    "is_default": request.is_default
                }
                
                method = await payment_repo.save_payment_method(method_data)
                
                return PaymentMethodResponse(
                    id=str(method["_id"]),
                    method_id=method["method_id"],
                    customer_id=method["customer_id"],
                    gateway=PaymentGateway(method["gateway"]),
                    gateway_method_id=method["gateway_method_id"],
                    type=PaymentMethodType(method["type"]),
                    last_four=method["last_four"],
                    brand=method.get("brand"),
                    is_default=method["is_default"],
                    created_at=method["created_at"]
                )
                
            except stripe.error.StripeError as e:
                logger.error(f"Stripe payment method error: {str(e)}")
                raise AppError(
                    message="Failed to save payment method",
                    error_code=ErrorCode.PAYMENT_METHOD_ERROR,
                    details={"stripe_error": str(e)}
                )
    
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error saving payment method: {str(e)}")
        raise AppError(
            message="Failed to save payment method",
            error_code=ErrorCode.PAYMENT_METHOD_ERROR,
            details={"error": str(e)}
        )


@router.get("/methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    current_user: dict = Depends(get_current_user),
    payment_repo: PaymentRepository = Depends(get_payment_repository)
):
    """Get customer's saved payment methods"""
    try:
        customer_id = current_user.get("user_id") or current_user.get("sub")
        methods = await payment_repo.get_payment_methods(customer_id)
        
        return [
            PaymentMethodResponse(
                id=str(method["_id"]),
                method_id=method["method_id"],
                customer_id=method["customer_id"],
                gateway=PaymentGateway(method["gateway"]),
                gateway_method_id=method["gateway_method_id"],
                type=PaymentMethodType(method["type"]),
                last_four=method["last_four"],
                brand=method.get("brand"),
                is_default=method["is_default"],
                created_at=method["created_at"]
            )
            for method in methods
        ]
    
    except Exception as e:
        logger.error(f"Error fetching payment methods: {str(e)}")
        raise AppError(
            message="Failed to fetch payment methods",
            error_code=ErrorCode.PAYMENT_METHOD_ERROR,
            details={"error": str(e)}
        )


@router.delete("/methods/{method_id}")
async def delete_payment_method(
    method_id: str,
    current_user: dict = Depends(get_current_user),
    payment_repo: PaymentRepository = Depends(get_payment_repository)
):
    """Delete saved payment method"""
    try:
        customer_id = current_user.get("user_id") or current_user.get("sub")
        
        # Get payment method
        method = await payment_repo.get_payment_method(method_id)
        if not method:
            raise AppError(
                message="Payment method not found",
                error_code=ErrorCode.PAYMENT_METHOD_NOT_FOUND,
                status_code=404
            )
        
        # Validate ownership
        if method["customer_id"] != customer_id:
            raise AppError(
                message="Access denied to this payment method",
                error_code=ErrorCode.ACCESS_DENIED,
                status_code=403
            )
        
        # Detach from gateway
        if method["gateway"] == PaymentGateway.STRIPE.value:
            try:
                stripe.PaymentMethod.detach(method["gateway_method_id"])
            except stripe.error.StripeError as e:
                logger.error(f"Stripe detach error: {str(e)}")
                # Continue with deletion even if Stripe detach fails
        
        # Delete from database
        await payment_repo.delete_payment_method(method_id)
        
        return {"success": True, "message": "Payment method deleted successfully"}
    
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error deleting payment method: {str(e)}")
        raise AppError(
            message="Failed to delete payment method",
            error_code=ErrorCode.PAYMENT_METHOD_ERROR,
            details={"error": str(e)}
        )


@router.get("/analytics", response_model=PaymentAnalytics)
async def get_payment_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    vendor_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    payment_repo: PaymentRepository = Depends(get_payment_repository)
):
    """Get payment analytics (admin/vendor only)"""
    try:
        user_role = current_user.get("role")
        user_id = current_user.get("user_id") or current_user.get("sub")
        
        # Access control
        if user_role not in ["admin", "vendor"]:
            raise AppError(
                message="Access denied - admin or vendor role required",
                error_code=ErrorCode.ACCESS_DENIED,
                status_code=403
            )
        
        # Vendor can only see their own analytics
        if user_role == "vendor":
            vendor_id = user_id
        
        # Set default date range (last 30 days)
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        analytics = await payment_repo.get_payment_analytics(
            start_date=start_date,
            end_date=end_date,
            vendor_id=vendor_id
        )
        
        return analytics
    
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error fetching payment analytics: {str(e)}")
        raise AppError(
            message="Failed to fetch payment analytics",
            error_code=ErrorCode.ANALYTICS_ERROR,
            details={"error": str(e)}
        )


@router.get("/vendor-payouts", response_model=List[VendorPayout])
async def get_vendor_payouts(
    status: Optional[PayoutStatus] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user),
    payment_repo: PaymentRepository = Depends(get_payment_repository)
):
    """Get vendor payouts (admin/vendor only)"""
    try:
        user_role = current_user.get("role")
        user_id = current_user.get("user_id") or current_user.get("sub")
        
        # Access control
        if user_role not in ["admin", "vendor"]:
            raise AppError(
                message="Access denied - admin or vendor role required",
                error_code=ErrorCode.ACCESS_DENIED,
                status_code=403
            )
        
        # Build filter
        filters = {}
        if user_role == "vendor":
            filters["vendor_id"] = user_id
        if status:
            filters["status"] = status.value
        if start_date:
            filters["created_at"] = {"$gte": start_date}
        if end_date:
            filters.setdefault("created_at", {})["$lte"] = end_date
        
        payouts = await payment_repo.get_vendor_payouts(filters)
        
        return [
            VendorPayout(
                id=str(payout["_id"]),
                payout_id=payout["payout_id"],
                vendor_id=payout["vendor_id"],
                payment_id=payout["payment_id"],
                order_id=payout["order_id"],
                gross_amount=payout["gross_amount"],
                commission_amount=payout["commission_amount"],
                platform_fee=payout["platform_fee"],
                gateway_fee=payout["gateway_fee"],
                net_amount=payout["net_amount"],
                currency=Currency(payout["currency"]),
                status=PayoutStatus(payout["status"]),
                payout_method=PayoutMethod(payout["payout_method"]),
                gateway_payout_id=payout.get("gateway_payout_id"),
                created_at=payout["created_at"],
                processed_at=payout.get("processed_at"),
                metadata=payout.get("metadata", {})
            )
            for payout in payouts
        ]
    
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error fetching vendor payouts: {str(e)}")
        raise AppError(
            message="Failed to fetch vendor payouts",
            error_code=ErrorCode.PAYOUT_ERROR,
            details={"error": str(e)}
        )
