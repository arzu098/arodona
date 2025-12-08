"""
Comprehensive Cart API with guest and user cart support.
Handles shopping cart operations with jewelry-specific features, 
inventory validation, and advanced e-commerce functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, Response, Header
from typing import Optional, Union
from uuid import uuid4
import json
from datetime import datetime, timedelta
from bson import ObjectId
from app.databases.schemas.cart import (
    CartItemCreate, CartResponse, CheckoutValidation,
    DiscountApplication, CartSummary, PricingBreakdown
)
from app.databases.repositories.cart import CartRepository
from app.databases.repositories.product import ProductRepository
from app.db.connection import get_database
from app.utils.dependencies import get_current_user_optional
from app.utils.errors import ErrorCode, AppError
import logging

# Set up logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cart", tags=["Cart"])


# Dependency functions
async def get_cart_repository() -> CartRepository:
    """Get cart repository instance"""
    db = get_database()
    return CartRepository(db)


def get_session_id(request: Request, response: Response) -> str:
    """Get or create session ID for guest cart"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid4())
        # Set session cookie for 30 days
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=30 * 24 * 60 * 60,  # 30 days
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
    return session_id


# User Cart Routes
@router.get("/", response_model=CartResponse)
async def get_cart(
    request: Request,
    response: Response,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    cart_repo: CartRepository = Depends(get_cart_repository)
):
    """Get cart for authenticated user or guest"""
    try:
        if current_user:
            # User cart
            user_id = current_user.get("user_id") or current_user.get("sub")
            cart = await cart_repo.get_user_cart(user_id)
            if not cart:
                cart = await cart_repo.create_user_cart(user_id)
        else:
            # Guest cart
            session_id = get_session_id(request, response)
            cart = await cart_repo.get_guest_cart(session_id)
            if not cart:
                cart = await cart_repo.create_guest_cart(session_id)
        
        # Format cart response
        return await cart_repo.format_cart_response(cart)
    except Exception as e:
        logger.error(f"Error fetching cart: {str(e)}")
        raise AppError(
            message="Failed to fetch cart",
            error_code=ErrorCode.CART_OPERATION_FAILED,
            details={"error": str(e)}
        )


@router.post("/add", response_model=CartResponse)
async def add_to_cart(
    item_data: CartItemCreate,
    request: Request,
    response: Response,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    cart_repo: CartRepository = Depends(get_cart_repository)
):
    """Add product to cart with jewelry-specific options"""
    try:
        # Validate and get product
        db = get_database()
        products = db.products
        
        product = None
        if ObjectId.is_valid(item_data.product_id):
            product = await products.find_one({"_id": ObjectId(item_data.product_id)})
        
        if not product:
            product = await products.find_one({"slug": item_data.product_id})
        
        if not product:
            raise AppError(
                message="Product not found",
                error_code=ErrorCode.PRODUCT_NOT_FOUND,
                status_code=404
            )
        
        # Add to appropriate cart
        if current_user:
            user_id = current_user.get("user_id") or current_user.get("sub")
            cart = await cart_repo.add_item_to_cart(
                user_id=user_id,
                product_id=str(product["_id"]),
                quantity=item_data.quantity,
                size=item_data.size,
                variant_id=item_data.variant_id,
                personalization=item_data.personalization,
                gift_message=item_data.gift_message
            )
        else:
            session_id = get_session_id(request, response)
            cart = await cart_repo.add_item_to_cart(
                session_id=session_id,
                product_id=str(product["_id"]),
                quantity=item_data.quantity,
                size=item_data.size,
                variant_id=item_data.variant_id,
                personalization=item_data.personalization,
                gift_message=item_data.gift_message
            )
        
        return cart
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}")
        raise AppError(
            message="Failed to add item to cart",
            error_code=ErrorCode.CART_OPERATION_FAILED,
            details={"error": str(e)}
        )


@router.put("/items/{item_id}/quantity", response_model=CartResponse)
async def update_item_quantity(
    item_id: str,
    quantity: int,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    cart_repo: CartRepository = Depends(get_cart_repository)
):
    """Update quantity of specific cart item"""
    try:
        if quantity < 0:
            raise AppError(
                message="Quantity must be non-negative",
                error_code=ErrorCode.INVALID_INPUT,
                status_code=400
            )
        
        if current_user:
            user_id = current_user.get("user_id") or current_user.get("sub")
            if quantity == 0:
                cart = await cart_repo.remove_item(user_id, item_id)
            else:
                cart = await cart_repo.update_item_quantity(user_id, item_id, quantity)
        else:
            session_id = request.cookies.get("session_id")
            if not session_id:
                raise AppError(
                    message="No cart session found",
                    error_code=ErrorCode.CART_NOT_FOUND,
                    status_code=404
                )
            
            if quantity == 0:
                cart = await cart_repo.remove_item(session_id=session_id, item_id=item_id)
            else:
                cart = await cart_repo.update_item_quantity(session_id=session_id, item_id=item_id, quantity=quantity)
        
        return cart
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error updating item quantity: {str(e)}")
        raise AppError(
            message="Failed to update item quantity",
            error_code=ErrorCode.CART_OPERATION_FAILED,
            details={"error": str(e)}
        )


@router.delete("/items/{item_id}", response_model=CartResponse)
async def remove_item(
    item_id: str,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    cart_repo: CartRepository = Depends(get_cart_repository)
):
    """Remove item from cart"""
    try:
        if current_user:
            user_id = current_user.get("user_id") or current_user.get("sub")
            cart = await cart_repo.remove_item(user_id, item_id)
        else:
            session_id = request.cookies.get("session_id")
            if not session_id:
                raise AppError(
                    message="No cart session found",
                    error_code=ErrorCode.CART_NOT_FOUND,
                    status_code=404
                )
            cart = await cart_repo.remove_item(session_id=session_id, item_id=item_id)
        
        return cart
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error removing item: {str(e)}")
        raise AppError(
            message="Failed to remove item from cart",
            error_code=ErrorCode.CART_OPERATION_FAILED,
            details={"error": str(e)}
        )


@router.delete("/clear", response_model=CartResponse)
async def clear_cart(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    cart_repo: CartRepository = Depends(get_cart_repository)
):
    """Clear all items from cart"""
    try:
        if current_user:
            user_id = current_user.get("user_id") or current_user.get("sub")
            cart = await cart_repo.clear_cart(user_id)
        else:
            session_id = request.cookies.get("session_id")
            if not session_id:
                raise AppError(
                    message="No cart session found",
                    error_code=ErrorCode.CART_NOT_FOUND,
                    status_code=404
                )
            cart = await cart_repo.clear_cart(session_id=session_id)
        
        return cart
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        raise AppError(
            message="Failed to clear cart",
            error_code=ErrorCode.CART_OPERATION_FAILED,
            details={"error": str(e)}
        )


@router.post("/apply-discount", response_model=CartResponse)
async def apply_discount_code(
    discount_data: DiscountApplication,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    cart_repo: CartRepository = Depends(get_cart_repository)
):
    """Apply discount code to cart"""
    try:
        if current_user:
            user_id = current_user.get("user_id") or current_user.get("sub")
            cart = await cart_repo.apply_discount_code(user_id, discount_data.code)
        else:
            session_id = request.cookies.get("session_id")
            if not session_id:
                raise AppError(
                    message="No cart session found",
                    error_code=ErrorCode.CART_NOT_FOUND,
                    status_code=404
                )
            cart = await cart_repo.apply_discount_code(session_id=session_id, code=discount_data.code)
        
        return cart
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error applying discount: {str(e)}")
        raise AppError(
            message="Failed to apply discount code",
            error_code=ErrorCode.CART_OPERATION_FAILED,
            details={"error": str(e)}
        )


@router.delete("/discount", response_model=CartResponse)
async def remove_discount_code(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    cart_repo: CartRepository = Depends(get_cart_repository)
):
    """Remove applied discount code"""
    try:
        if current_user:
            user_id = current_user.get("user_id") or current_user.get("sub")
            cart = await cart_repo.remove_discount_code(user_id)
        else:
            session_id = request.cookies.get("session_id")
            if not session_id:
                raise AppError(
                    message="No cart session found",
                    error_code=ErrorCode.CART_NOT_FOUND,
                    status_code=404
                )
            cart = await cart_repo.remove_discount_code(session_id=session_id)
        
        return cart
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error removing discount: {str(e)}")
        raise AppError(
            message="Failed to remove discount code",
            error_code=ErrorCode.CART_OPERATION_FAILED,
            details={"error": str(e)}
        )


@router.get("/summary", response_model=CartSummary)
async def get_cart_summary(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    cart_repo: CartRepository = Depends(get_cart_repository)
):
    """Get cart summary with pricing breakdown"""
    try:
        if current_user:
            user_id = current_user.get("user_id") or current_user.get("sub")
            cart = await cart_repo.get_user_cart(user_id)
        else:
            session_id = request.cookies.get("session_id")
            if not session_id:
                return CartSummary(
                    total_items=0,
                    subtotal=0.0,
                    pricing_breakdown=PricingBreakdown(
                        subtotal=0.0,
                        shipping_cost=0.0,
                        tax_amount=0.0,
                        discount_amount=0.0,
                        total=0.0
                    )
                )
            cart = await cart_repo.get_guest_cart(session_id)
        
        if not cart:
            return CartSummary(
                total_items=0,
                subtotal=0.0,
                pricing_breakdown=PricingBreakdown(
                    subtotal=0.0,
                    shipping_cost=0.0,
                    tax_amount=0.0,
                    discount_amount=0.0,
                    total=0.0
                )
            )
        
        return CartSummary(
            total_items=len(cart.items),
            subtotal=cart.pricing_breakdown.subtotal,
            pricing_breakdown=cart.pricing_breakdown
        )
    except Exception as e:
        logger.error(f"Error getting cart summary: {str(e)}")
        raise AppError(
            message="Failed to get cart summary",
            error_code=ErrorCode.CART_OPERATION_FAILED,
            details={"error": str(e)}
        )


@router.post("/validate-checkout", response_model=CheckoutValidation)
async def validate_checkout(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    cart_repo: CartRepository = Depends(get_cart_repository)
):
    """Validate cart is ready for checkout"""
    try:
        if current_user:
            user_id = current_user.get("user_id") or current_user.get("sub")
            validation = await cart_repo.validate_checkout_readiness(user_id)
        else:
            session_id = request.cookies.get("session_id")
            if not session_id:
                raise AppError(
                    message="No cart session found",
                    error_code=ErrorCode.CART_NOT_FOUND,
                    status_code=404
                )
            validation = await cart_repo.validate_checkout_readiness(session_id=session_id)
        
        return validation
    except AppError:
        raise
    except Exception as e:
        logger.error(f"Error validating checkout: {str(e)}")
        raise AppError(
            message="Failed to validate checkout",
            error_code=ErrorCode.CART_OPERATION_FAILED,
            details={"error": str(e)}
        )


@router.post("/merge")
async def merge_guest_cart_on_login(
    request: Request,
    current_user: dict = Depends(get_current_user_optional),
    cart_repo: CartRepository = Depends(get_cart_repository)
):
    """Merge guest cart with user cart when user logs in"""
    if not current_user:
        raise AppError(
            message="User must be authenticated",
            error_code=ErrorCode.AUTHENTICATION_REQUIRED,
            status_code=401
        )
    
    try:
        session_id = request.cookies.get("session_id")
        if session_id:
            user_id = current_user.get("user_id") or current_user.get("sub")
            merged_cart = await cart_repo.merge_carts(guest_session_id=session_id, user_id=user_id)
            return {"message": "Cart merged successfully", "cart": merged_cart}
        
        return {"message": "No guest cart to merge"}
    except Exception as e:
        logger.error(f"Error merging carts: {str(e)}")
        raise AppError(
            message="Failed to merge carts",
            error_code=ErrorCode.CART_OPERATION_FAILED,
            details={"error": str(e)}
        )