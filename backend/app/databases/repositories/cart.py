"""
Enhanced cart repository for comprehensive e-commerce functionality.
Supports jewelry-specific features, guest checkout, inventory management, and advanced pricing.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
import uuid
import logging

from app.databases.schemas.cart import (
    CartResponse, CartItemResponse, CartSummary, PricingBreakdown, 
    AppliedDiscount, CheckoutStep, DiscountType, ShippingAddress, 
    BillingAddress, ShippingOption, CheckoutValidation
)

logger = logging.getLogger(__name__)


class CartRepository:
    """Enhanced repository for comprehensive cart management"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["carts"]
        self.products_collection = db["products"]
        self.vendors_collection = db["vendors"]
        self.discounts_collection = db["discounts"]
        self.shipping_rates_collection = db["shipping_rates"]
        self.tax_rates_collection = db["tax_rates"]
        
        # Cart settings
        self.cart_expiry_hours = 24 * 7  # 7 days for registered users
        self.guest_cart_expiry_hours = 24 * 3  # 3 days for guest users
        self.max_items_per_cart = 50
        self.max_quantity_per_item = 10

    async def get_cart_by_user_id(self, user_id: str, create_if_not_exists: bool = True) -> Optional[Dict[str, Any]]:
        """Get cart by user ID with optional auto-creation"""
        try:
            cart = await self.collection.find_one({"user_id": user_id, "is_active": True})
            
            if not cart and create_if_not_exists:
                cart = await self.create_user_cart(user_id)
            elif cart:
                # Check if cart is expired
                if self._is_cart_expired(cart):
                    await self._expire_cart(cart["_id"])
                    cart = await self.create_user_cart(user_id) if create_if_not_exists else None
                else:
                    # Update last_accessed
                    await self.collection.update_one(
                        {"_id": cart["_id"]},
                        {"$set": {"last_accessed": datetime.utcnow()}}
                    )
            
            return cart
        except Exception:
            return None
    
    async def get_cart_by_session_id(self, session_id: str, create_if_not_exists: bool = True) -> Optional[Dict[str, Any]]:
        """Get cart by session ID for guest users"""
        try:
            cart = await self.collection.find_one({"session_id": session_id, "is_active": True})
            
            if not cart and create_if_not_exists:
                cart = await self.create_guest_cart(session_id)
            elif cart:
                # Check if cart is expired
                if self._is_cart_expired(cart):
                    await self._expire_cart(cart["_id"])
                    cart = await self.create_guest_cart(session_id) if create_if_not_exists else None
                else:
                    # Update last_accessed
                    await self.collection.update_one(
                        {"_id": cart["_id"]},
                        {"$set": {"last_accessed": datetime.utcnow()}}
                    )
            
            return cart
        except Exception:
            return None
    
    # Alias methods for compatibility with cart routes
    async def get_user_cart(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Alias for get_cart_by_user_id"""
        return await self.get_cart_by_user_id(user_id, create_if_not_exists=False)
    
    async def get_guest_cart(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Alias for get_cart_by_session_id"""
        return await self.get_cart_by_session_id(session_id, create_if_not_exists=False)
    
    def _is_cart_expired(self, cart: Dict[str, Any]) -> bool:
        """Check if cart is expired"""
        if not cart.get("expires_at"):
            return False
        
        return datetime.utcnow() > cart["expires_at"]
    
    async def _expire_cart(self, cart_id: ObjectId):
        """Mark cart as expired"""
        await self.collection.update_one(
            {"_id": cart_id},
            {"$set": {"is_active": False, "expired_at": datetime.utcnow()}}
        )

    async def format_cart_response(self, cart: Dict[str, Any]) -> CartResponse:
        """Format cart document to comprehensive CartResponse schema"""
        if not cart:
            return None
        
        # Format cart items
        cart_items = []
        for item in cart["items"]:
            cart_items.append(CartItemResponse(
                id=item["id"],
                product_id=item["product_id"],
                product_name=item["product_name"],
                product_slug=item.get("product_slug"),
                vendor_id=item["vendor_id"],
                vendor_name=item["vendor_name"],
                sku=item.get("sku"),
                image_url=item.get("image_url"),
                unit_price=item["unit_price"],
                compare_at_price=item.get("compare_at_price"),
                quantity=item["quantity"],
                line_total=item["line_total"],
                size=item.get("size"),
                variant_id=item.get("variant_id"),
                variant_name=item.get("variant_name"),
                jewelry_type=item.get("jewelry_type"),
                metal_type=item.get("metal_type"),
                personalization=item.get("personalization", {}),
                gift_message=item.get("gift_message"),
                in_stock=item.get("in_stock", True),
                stock_quantity=item.get("stock_quantity"),
                available_quantity=item["available_quantity"],
                is_available=item.get("is_available", True),
                availability_message=item.get("availability_message"),
                added_at=item["added_at"]
            ))
        
        # Format applied discounts
        applied_discounts = []
        for discount in cart.get("applied_discounts", []):
            applied_discounts.append(AppliedDiscount(
                code=discount["code"],
                description=discount["description"],
                discount_type=DiscountType(discount["discount_type"]),
                discount_value=discount["discount_value"],
                discount_amount=discount["discount_amount"],
                minimum_order=discount.get("minimum_order"),
                maximum_discount=discount.get("maximum_discount"),
                applies_to=discount.get("applies_to", "cart")
            ))
        
        # Generate summary
        summary = await self.get_cart_summary(cart)
        
        # Format pricing
        pricing = PricingBreakdown(
            subtotal=cart["subtotal"],
            item_discount=cart["item_discount"],
            shipping_cost=cart["shipping_cost"],
            shipping_discount=cart["shipping_discount"],
            tax_amount=cart["tax_amount"],
            total_discount=cart["total_discount"],
            total_amount=cart["total_amount"],
            currency=cart.get("currency", "USD"),
            you_save=cart["item_discount"] + cart["shipping_discount"]
        )
        
        return CartResponse(
            id=str(cart["_id"]),
            user_id=cart.get("user_id"),
            session_id=cart.get("session_id"),
            items=cart_items,
            summary=summary,
            pricing=pricing,
            applied_discounts=applied_discounts,
            checkout_step=CheckoutStep(cart.get("checkout_step", CheckoutStep.CART.value)),
            shipping_address=ShippingAddress(**cart["shipping_address"]) if cart.get("shipping_address") else None,
            billing_address=BillingAddress(**cart["billing_address"]) if cart.get("billing_address") else None,
            selected_shipping=ShippingOption(**cart["selected_shipping"]) if cart.get("selected_shipping") else None,
            is_valid=cart.get("is_valid", True),
            validation_errors=cart.get("validation_errors", []),
            expires_at=cart.get("expires_at"),
            created_at=cart["created_at"],
            updated_at=cart["updated_at"]
        )
    
    async def apply_discount_code(self, cart: Dict[str, Any], discount_code: str) -> Tuple[Dict[str, Any], List[str]]:
        """Apply discount code to cart"""
        errors = []
        
        # Check if discount already applied
        for existing_discount in cart.get("applied_discounts", []):
            if existing_discount["code"].upper() == discount_code.upper():
                errors.append("Discount code already applied")
                return cart, errors
        
        # Look up discount
        discount = await self.discounts_collection.find_one({
            "code": discount_code.upper(),
            "is_active": True,
            "starts_at": {"$lte": datetime.utcnow()},
            "ends_at": {"$gte": datetime.utcnow()}
        })
        
        if not discount:
            errors.append("Invalid or expired discount code")
            return cart, errors
        
        # Check minimum order requirements
        if discount.get("minimum_order") and cart["subtotal"] < discount["minimum_order"]:
            errors.append(f"Minimum order of ${discount['minimum_order']} required for this discount")
            return cart, errors
        
        # Calculate discount amount
        discount_amount = 0.0
        if discount["discount_type"] == DiscountType.PERCENTAGE.value:
            discount_amount = cart["subtotal"] * (discount["discount_value"] / 100)
            if discount.get("maximum_discount"):
                discount_amount = min(discount_amount, discount["maximum_discount"])
        elif discount["discount_type"] == DiscountType.FIXED_AMOUNT.value:
            discount_amount = min(discount["discount_value"], cart["subtotal"])
        elif discount["discount_type"] == DiscountType.FREE_SHIPPING.value:
            discount_amount = 0.0  # Handled in shipping calculation
        
        # Add to applied discounts
        applied_discount = {
            "code": discount["code"],
            "description": discount["description"],
            "discount_type": discount["discount_type"],
            "discount_value": discount["discount_value"],
            "discount_amount": discount_amount,
            "minimum_order": discount.get("minimum_order"),
            "maximum_discount": discount.get("maximum_discount"),
            "applies_to": discount.get("applies_to", "cart")
        }
        
        cart.setdefault("applied_discounts", []).append(applied_discount)
        
        # Recalculate cart
        cart = await self._recalculate_cart(cart)
        
        return cart, errors
    
    async def remove_discount_code(self, cart: Dict[str, Any], discount_code: str) -> Dict[str, Any]:
        """Remove discount code from cart"""
        if not cart.get("applied_discounts"):
            return cart
        
        cart["applied_discounts"] = [
            d for d in cart["applied_discounts"] 
            if d["code"].upper() != discount_code.upper()
        ]
        
        # Recalculate cart
        cart = await self._recalculate_cart(cart)
        
        return cart
    
    async def update_item_quantity(self, cart: Dict[str, Any], cart_item_id: str, new_quantity: int) -> Tuple[Dict[str, Any], List[str]]:
        """Update quantity of specific cart item"""
        errors = []
        
        # Find item
        item_index = None
        for i, item in enumerate(cart["items"]):
            if item["id"] == cart_item_id:
                item_index = i
                break
        
        if item_index is None:
            errors.append("Cart item not found")
            return cart, errors
        
        item = cart["items"][item_index]
        
        if new_quantity == 0:
            # Remove item
            cart["items"].pop(item_index)
        else:
            # Validate new quantity
            product = await self.products_collection.find_one({"_id": ObjectId(item["product_id"])})
            if not product:
                errors.append("Product no longer available")
                return cart, errors
            
            available_quantity = await self._get_available_quantity(product, item.get("size"), item.get("variant_id"))
            
            if new_quantity > available_quantity:
                errors.append(f"Only {available_quantity} items available")
                return cart, errors
            
            if new_quantity > self.max_quantity_per_item:
                errors.append(f"Maximum {self.max_quantity_per_item} items per product")
                return cart, errors
            
            # Update quantity
            cart["items"][item_index]["quantity"] = new_quantity
            cart["items"][item_index]["line_total"] = item["unit_price"] * new_quantity
        
        # Recalculate cart
        cart = await self._recalculate_cart(cart)
        
        return cart, errors
    
    async def validate_checkout_readiness_old(self, cart: Dict[str, Any]) -> CheckoutValidation:
        """Validate cart readiness for checkout"""
        errors = []
        warnings = []
        
        # Check if cart has items
        if not cart.get("items") or len(cart["items"]) == 0:
            errors.append("Cart is empty")
        
        # Validate all items
        inventory_issues = []
        for item in cart["items"]:
            if not item.get("is_available", True):
                errors.append(f"{item['product_name']} is no longer available")
                inventory_issues.append({
                    "item_id": item["id"],
                    "product_name": item["product_name"],
                    "issue": "not_available"
                })
            elif not item.get("in_stock", True):
                errors.append(f"{item['product_name']} is out of stock")
                inventory_issues.append({
                    "item_id": item["id"],
                    "product_name": item["product_name"],
                    "issue": "out_of_stock"
                })
        
        # Check address requirements
        requires_shipping_address = True
        requires_billing_address = True
        requires_shipping_method = True
        requires_payment_method = True
        
        if not cart.get("shipping_address"):
            errors.append("Shipping address required")
        
        if not cart.get("billing_address"):
            errors.append("Billing address required")
        
        if not cart.get("selected_shipping"):
            warnings.append("Shipping method not selected")
        
        # Check total amount
        if cart.get("total_amount", 0) <= 0:
            errors.append("Invalid cart total")
        
        return CheckoutValidation(
            is_valid=len(errors) == 0,
            can_checkout=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            requires_shipping_address=requires_shipping_address,
            requires_billing_address=requires_billing_address,
            requires_shipping_method=requires_shipping_method,
            requires_payment_method=requires_payment_method,
            inventory_issues=inventory_issues
        )
    
    async def cleanup_expired_carts(self) -> int:
        """Clean up expired carts"""
        result = await self.collection.update_many(
            {
                "expires_at": {"$lt": datetime.utcnow()},
                "is_active": True
            },
            {
                "$set": {
                    "is_active": False,
                    "expired_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count
    
    async def create_indexes(self) -> None:
        """Create necessary indexes for performance"""
        from pymongo.errors import OperationFailure
        import logging
        
        try:
            # Partial unique index on user_id (only for registered users, allows multiple null values for guests)
            await self.collection.create_index(
                [("user_id", 1)],
                unique=True,
                partialFilterExpression={"user_id": {"$type": "string"}},
                name="user_id_partial_unique"
            )
        except OperationFailure as e:
            if "already exists" not in str(e).lower():
                logging.warning(f"Failed to create user_id index: {e}")
        
        try:
            # Index on session_id for guest carts
            await self.collection.create_index("session_id")
        except OperationFailure as e:
            if "already exists" not in str(e).lower():
                logging.warning(f"Failed to create session_id index: {e}")
        
        try:
            # Index on is_active for filtering
            await self.collection.create_index("is_active")
        except OperationFailure as e:
            if "already exists" not in str(e).lower():
                logging.warning(f"Failed to create is_active index: {e}")
        
        try:
            # Index on items.product_id for analytics
            await self.collection.create_index("items.product_id")
        except OperationFailure as e:
            if "already exists" not in str(e).lower():
                logging.warning(f"Failed to create items.product_id index: {e}")

    async def create_user_cart(self, user_id: str) -> Dict[str, Any]:
        """Create a new cart for registered user"""
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.cart_expiry_hours)
        
        cart_data = {
            "user_id": user_id,
            "session_id": None,
            "items": [],
            "checkout_step": CheckoutStep.CART.value,
            "is_active": True,
            
            # Addresses and shipping
            "shipping_address": None,
            "billing_address": None,
            "selected_shipping": None,
            
            # Pricing
            "subtotal": 0.0,
            "item_discount": 0.0,
            "shipping_cost": 0.0,
            "shipping_discount": 0.0,
            "tax_amount": 0.0,
            "total_discount": 0.0,
            "total_amount": 0.0,
            "currency": "USD",
            
            # Discounts
            "applied_discounts": [],
            
            # Validation
            "is_valid": True,
            "validation_errors": [],
            
            # Metadata
            "expires_at": expires_at,
            "created_at": now,
            "updated_at": now,
            "last_accessed": now
        }
        
        result = await self.collection.insert_one(cart_data)
        cart_data["_id"] = result.inserted_id
        return cart_data
    
    async def create_guest_cart(self, session_id: str = None) -> Dict[str, Any]:
        """Create a new cart for guest user"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.guest_cart_expiry_hours)
        
        cart_data = {
            "user_id": None,
            "session_id": session_id,
            "items": [],
            "checkout_step": CheckoutStep.CART.value,
            "is_active": True,
            
            # Guest checkout info
            "guest_email": None,
            "guest_phone": None,
            
            # Addresses and shipping
            "shipping_address": None,
            "billing_address": None,
            "selected_shipping": None,
            
            # Pricing
            "subtotal": 0.0,
            "item_discount": 0.0,
            "shipping_cost": 0.0,
            "shipping_discount": 0.0,
            "tax_amount": 0.0,
            "total_discount": 0.0,
            "total_amount": 0.0,
            "currency": "USD",
            
            # Discounts
            "applied_discounts": [],
            
            # Validation
            "is_valid": True,
            "validation_errors": [],
            
            # Metadata
            "expires_at": expires_at,
            "created_at": now,
            "updated_at": now,
            "last_accessed": now
        }
        
        result = await self.collection.insert_one(cart_data)
        cart_data["_id"] = result.inserted_id
        return cart_data



    async def add_item_to_cart(
        self,
        cart_id: str = None,
        user_id: str = None,
        session_id: str = None,
        product_id: str = None,
        quantity: int = 1,
        size: str = None,
        variant_id: str = None,
        personalization: Dict[str, str] = None,
        gift_message: str = None
    ) -> CartResponse:
        """Add item to cart with comprehensive validation"""
        errors = []
        
        # Get cart
        if cart_id:
            cart = await self.collection.find_one({"_id": ObjectId(cart_id), "is_active": True})
        elif user_id:
            cart = await self.get_cart_by_user_id(user_id)
        elif session_id:
            cart = await self.get_cart_by_session_id(session_id)
        else:
            raise ValueError("Cart identification required (cart_id, user_id, or session_id)")
        
        if not cart:
            raise ValueError("Cart not found")
        
        # Validate cart limits
        if len(cart["items"]) >= self.max_items_per_cart:
            raise ValueError(f"Cart cannot exceed {self.max_items_per_cart} items")
        
        # Get and validate product
        product = await self.products_collection.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise ValueError("Product not found")
        
        if product.get("status") != "active":
            raise ValueError("Product is not available")
        
        # Validate inventory
        available_quantity = await self._get_available_quantity(product, size, variant_id)
        if available_quantity == 0:
            raise ValueError("Product is out of stock")
        
        # Check current quantity in cart
        current_quantity = await self._get_item_quantity_in_cart(cart, product_id, size, variant_id)
        total_requested = current_quantity + quantity
        
        if total_requested > available_quantity:
            raise ValueError(f"Only {available_quantity} items available (you already have {current_quantity} in cart)")
        
        if total_requested > self.max_quantity_per_item:
            raise ValueError(f"Maximum {self.max_quantity_per_item} items per product")
        
        # Skip vendor validation for now to allow cart functionality
        # TODO: Re-enable proper vendor validation after fixing vendor data
        try:
            vendor_id = product.get("vendor_id")
            logger.info(f"Product {product.get('name')} has vendor_id: {vendor_id}")
            
            # For now, just create a mock vendor to allow the cart to work
            vendor = {
                "_id": ObjectId(),
                "business_name": "Store",
                "status": "active"
            }
            
            logger.info("Using mock vendor for cart functionality")
        except Exception as e:
            logger.warning(f"Vendor check failed, using fallback: {str(e)}")
            vendor = {"_id": ObjectId(), "business_name": "Store", "status": "active"}
        
        # Create cart item
        now = datetime.utcnow()
        # Safely get product slug
        seo_data = product.get("seo")
        if isinstance(seo_data, dict):
            product_slug = seo_data.get("slug", product.get("slug"))
        else:
            product_slug = product.get("slug")
        
        cart_item = {
            "id": str(ObjectId()),
            "product_id": product_id,
            "product_name": product["name"],
            "product_slug": product_slug,
            "vendor_id": product.get("vendor_id", str(vendor["_id"])),
            "vendor_name": vendor.get("business_name", "Store"),
            "sku": product.get("sku"),
            "image_url": self._get_primary_image_url(product),
            
            # Pricing
            "unit_price": float(product["price"]),
            "compare_at_price": float(product.get("compare_at_price")) if product.get("compare_at_price") else None,
            "quantity": quantity,
            "line_total": float(product["price"]) * quantity,
            
            # Product specifics
            "size": size,
            "variant_id": variant_id,
            "variant_name": await self._get_variant_name(product, variant_id),
            "jewelry_type": product.get("jewelry_type"),
            "metal_type": product.get("metal_type"),
            
            # Customization
            "personalization": personalization or {},
            "gift_message": gift_message,
            
            # Inventory status
            "in_stock": True,
            "stock_quantity": available_quantity,
            "available_quantity": available_quantity,
            
            # Item status
            "is_available": True,
            "availability_message": None,
            
            "added_at": now
        }
        
        # Check if similar item exists (same product, size, variant)
        existing_item_index = await self._find_existing_item_index(cart, product_id, size, variant_id)
        
        if existing_item_index is not None:
            # Update existing item
            existing_item = cart["items"][existing_item_index]
            new_quantity = existing_item["quantity"] + quantity
            cart["items"][existing_item_index]["quantity"] = new_quantity
            cart["items"][existing_item_index]["line_total"] = existing_item["unit_price"] * new_quantity
            cart["items"][existing_item_index]["updated_at"] = now
        else:
            # Add new item
            cart["items"].append(cart_item)
        
        # Recalculate cart totals
        cart = await self._recalculate_cart(cart)
        
        # Update cart in database
        await self.collection.update_one(
            {"_id": cart["_id"]},
            {
                "$set": {
                    "items": cart["items"],
                    "subtotal": cart["subtotal"],
                    "item_discount": cart["item_discount"],
                    "tax_amount": cart["tax_amount"],
                    "total_amount": cart["total_amount"],
                    "updated_at": now,
                    "last_accessed": now
                }
            }
        )
        
        # Return formatted cart response
        return await self.format_cart_response(cart)
    
    async def _get_available_quantity(self, product: Dict[str, Any], size: str = None, variant_id: str = None) -> int:
        """Get available quantity for product/size/variant combination"""
        if not product.get("track_inventory", True):
            return 999  # Unlimited if inventory tracking is disabled
        
        # Check size-specific inventory
        if size and product.get("sizes"):
            for size_variation in product["sizes"]:
                if size_variation["size"] == size:
                    return size_variation.get("stock_quantity", 0)
        
        # Check variant-specific inventory
        if variant_id and product.get("variants"):
            for variant in product["variants"]:
                if variant.get("sku") == variant_id or str(variant.get("id")) == variant_id:
                    return variant.get("stock_quantity", 0)
        
        # Default to main product stock
        return product.get("stock_quantity", 0)
    
    async def _get_item_quantity_in_cart(self, cart: Dict[str, Any], product_id: str, size: str = None, variant_id: str = None) -> int:
        """Get current quantity of specific item in cart"""
        for item in cart["items"]:
            if (item["product_id"] == product_id and 
                item.get("size") == size and 
                item.get("variant_id") == variant_id):
                return item["quantity"]
        return 0
    
    def _get_primary_image_url(self, product: Dict[str, Any]) -> str:
        """Get primary image URL for product"""
        images = product.get("images", [])
        for image in images:
            if image.get("is_primary"):
                return image.get("url")
        # Return first image if no primary
        if images:
            return images[0].get("url")
        return None
    
    async def _get_variant_name(self, product: Dict[str, Any], variant_id: str = None) -> str:
        """Get human-readable variant name"""
        if not variant_id or not product.get("variants"):
            return None
        
        for variant in product["variants"]:
            if variant.get("sku") == variant_id or str(variant.get("id")) == variant_id:
                return f"{variant.get('type', '')}: {variant.get('value', '')}"
        
        return None
    
    async def _find_existing_item_index(self, cart: Dict[str, Any], product_id: str, size: str = None, variant_id: str = None) -> Optional[int]:
        """Find index of existing item in cart"""
        for i, item in enumerate(cart["items"]):
            if (item["product_id"] == product_id and 
                item.get("size") == size and 
                item.get("variant_id") == variant_id):
                return i
        return None

    async def update_item_quantity(
        self,
        user_id: str,
        product_id: ObjectId,
        quantity: int,
        variant_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Update item quantity in cart"""
        if quantity <= 0:
            return None
            
        cart = await self.get_cart_by_user_id(user_id)
        if not cart:
            return None
            
        # Find item and update quantity
        item_index = None
        for i, item in enumerate(cart["items"]):
            if (str(item["product_id"]) == str(product_id) and 
                item.get("variant_id") == variant_id):
                item_index = i
                break
                
        if item_index is None:
            return None
            
        # Update quantity and item_total
        cart["items"][item_index]["quantity"] = quantity
        price = cart["items"][item_index]["price"]
        cart["items"][item_index]["item_total"] = round(price * quantity, 2)
        
        # Recalculate totals
        cart = await self.recalc_cart_totals(cart)
        
        # Prepare update data - only include the fields we want to update
        update_data = {
            "items": cart["items"],
            "subtotal": cart["subtotal"],
            "discount": cart["discount"],
            "tax": cart["tax"],
            "delivery_fee": cart["delivery_fee"],
            "total_amount": cart["total_amount"],
            "coupon": cart.get("coupon"),
            "updated_at": datetime.utcnow()
        }
        
        # Update cart in database
        return await self.update_cart(user_id, update_data)

    async def remove_item_from_cart(
        self,
        user_id: str,
        product_id: ObjectId,
        variant_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Remove item from cart"""
        cart = await self.get_cart_by_user_id(user_id)
        if not cart:
            return None
            
        # Find and remove item
        item_index = None
        for i, item in enumerate(cart["items"]):
            if (str(item["product_id"]) == str(product_id) and 
                item.get("variant_id") == variant_id):
                item_index = i
                break
                
        if item_index is None:
            return cart  # Item not found, return cart as is
            
        # Remove item
        cart["items"].pop(item_index)
        
        # Recalculate totals
        cart = await self.recalc_cart_totals(cart)
        
        # Prepare update data - only include the fields we want to update
        update_data = {
            "items": cart["items"],
            "subtotal": cart["subtotal"],
            "discount": cart["discount"],
            "tax": cart["tax"],
            "delivery_fee": cart["delivery_fee"],
            "total_amount": cart["total_amount"],
            "coupon": cart.get("coupon"),
            "updated_at": datetime.utcnow()
        }
        
        # Update cart in database
        return await self.update_cart(user_id, update_data)

    async def apply_coupon(self, user_id: str, coupon_data: Dict) -> Optional[Dict]:
        """Apply coupon to cart"""
        cart = await self.get_cart_by_user_id(user_id)
        if not cart:
            return None
            
        # For now, just store the coupon data
        # In a real implementation, you would validate the coupon
        update_data = {
            "coupon": coupon_data
        }
        
        # Recalculate totals with coupon
        updated_cart = await self.update_cart(user_id, update_data)
        if updated_cart:
            updated_cart = await self.recalc_cart_totals(updated_cart)
            # Prepare update data - only include the fields we want to update
            final_update_data = {
                "subtotal": updated_cart["subtotal"],
                "discount": updated_cart["discount"],
                "tax": updated_cart["tax"],
                "delivery_fee": updated_cart["delivery_fee"],
                "total_amount": updated_cart["total_amount"],
                "coupon": updated_cart.get("coupon"),
                "updated_at": datetime.utcnow()
            }
            return await self.update_cart(user_id, final_update_data)
        return updated_cart

    async def remove_coupon(self, user_id: str) -> Optional[Dict]:
        """Remove coupon from cart"""
        update_data = {
            "coupon": None
        }
        updated_cart = await self.update_cart(user_id, update_data)
        if updated_cart:
            updated_cart = await self.recalc_cart_totals(updated_cart)
            # Prepare update data - only include the fields we want to update
            final_update_data = {
                "subtotal": updated_cart["subtotal"],
                "discount": updated_cart["discount"],
                "tax": updated_cart["tax"],
                "delivery_fee": updated_cart["delivery_fee"],
                "total_amount": updated_cart["total_amount"],
                "coupon": updated_cart.get("coupon"),
                "updated_at": datetime.utcnow()
            }
            return await self.update_cart(user_id, final_update_data)
        return updated_cart

    async def _recalculate_cart(self, cart: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate comprehensive cart totals and validate items"""
        # Validate all items first
        cart = await self._validate_cart_items(cart)
        
        # Calculate subtotal
        subtotal = sum(item["line_total"] for item in cart["items"] if item.get("is_available", True))
        
        # Calculate item discounts
        item_discount = await self._calculate_item_discounts(cart, subtotal)
        
        # Calculate shipping
        shipping_cost, shipping_discount = await self._calculate_shipping(cart, subtotal - item_discount)
        
        # Calculate tax
        tax_amount = await self._calculate_tax(cart, subtotal - item_discount)
        
        # Calculate total discount
        total_discount = item_discount + shipping_discount
        
        # Calculate final total
        total_amount = max(0.0, subtotal - total_discount + shipping_cost + tax_amount)
        
        # Update cart totals
        cart.update({
            "subtotal": round(subtotal, 2),
            "item_discount": round(item_discount, 2),
            "shipping_cost": round(shipping_cost, 2),
            "shipping_discount": round(shipping_discount, 2),
            "tax_amount": round(tax_amount, 2),
            "total_discount": round(total_discount, 2),
            "total_amount": round(total_amount, 2),
            "updated_at": datetime.utcnow()
        })
        
        return cart
    
    async def _validate_cart_items(self, cart: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all cart items for availability and pricing"""
        updated_items = []
        validation_errors = []
        
        for item in cart["items"]:
            # Get current product data
            product = await self.products_collection.find_one({"_id": ObjectId(item["product_id"])})
            
            if not product:
                validation_errors.append(f"Product {item['product_name']} is no longer available")
                continue
            
            if product.get("status") != "active":
                item["is_available"] = False
                item["availability_message"] = "Product is no longer available"
                validation_errors.append(f"Product {item['product_name']} is no longer available")
            
            # Check inventory
            available_quantity = await self._get_available_quantity(product, item.get("size"), item.get("variant_id"))
            
            if available_quantity == 0:
                item["is_available"] = False
                item["availability_message"] = "Out of stock"
                validation_errors.append(f"Product {item['product_name']} is out of stock")
            elif item["quantity"] > available_quantity:
                # Adjust quantity to available stock
                item["quantity"] = available_quantity
                item["line_total"] = item["unit_price"] * available_quantity
                validation_errors.append(f"Quantity adjusted for {item['product_name']} (only {available_quantity} available)")
            
            # Update pricing if changed
            current_price = float(product["price"])
            if abs(item["unit_price"] - current_price) > 0.01:  # Price changed
                item["unit_price"] = current_price
                item["line_total"] = current_price * item["quantity"]
                validation_errors.append(f"Price updated for {item['product_name']}")
            
            # Update stock information
            item["stock_quantity"] = available_quantity
            item["available_quantity"] = available_quantity
            
            updated_items.append(item)
        
        cart["items"] = updated_items
        cart["validation_errors"] = validation_errors
        cart["is_valid"] = len(validation_errors) == 0
        
        return cart
    
    async def _calculate_item_discounts(self, cart: Dict[str, Any], subtotal: float) -> float:
        """Calculate discounts applied to items"""
        total_discount = 0.0
        
        # Process applied discount codes
        for discount in cart.get("applied_discounts", []):
            if discount["discount_type"] == DiscountType.PERCENTAGE.value:
                discount_amount = subtotal * (discount["discount_value"] / 100)
                if discount.get("maximum_discount"):
                    discount_amount = min(discount_amount, discount["maximum_discount"])
                total_discount += discount_amount
            elif discount["discount_type"] == DiscountType.FIXED_AMOUNT.value:
                total_discount += min(discount["discount_value"], subtotal)
        
        return total_discount
    
    async def _calculate_shipping(self, cart: Dict[str, Any], discounted_subtotal: float) -> Tuple[float, float]:
        """Calculate shipping cost and discounts"""
        shipping_cost = 0.0
        shipping_discount = 0.0
        
        # Free shipping threshold (configurable)
        free_shipping_threshold = 100.0
        
        if discounted_subtotal >= free_shipping_threshold:
            shipping_discount = 0.0  # Already free
        else:
            # Check for free shipping discounts
            for discount in cart.get("applied_discounts", []):
                if discount["discount_type"] == DiscountType.FREE_SHIPPING.value:
                    shipping_discount = 15.0  # Standard shipping cost
                    break
            else:
                # Calculate standard shipping
                if cart.get("selected_shipping"):
                    shipping_cost = cart["selected_shipping"]["cost"]
                else:
                    # Default shipping estimate
                    shipping_cost = 15.0 if discounted_subtotal < free_shipping_threshold else 0.0
        
        return shipping_cost, shipping_discount
    
    async def _calculate_tax(self, cart: Dict[str, Any], taxable_amount: float) -> float:
        """Calculate tax based on shipping address"""
        # For now, simplified tax calculation
        # In production, integrate with tax service (Avalara, TaxJar, etc.)
        
        if not cart.get("shipping_address"):
            return 0.0  # Can't calculate without address
        
        # Simple rate lookup by state/country
        tax_rate = 0.0
        shipping_address = cart["shipping_address"]
        
        # US tax rates (simplified example)
        us_tax_rates = {
            "CA": 0.0875,  # California
            "NY": 0.08,    # New York
            "TX": 0.0625,  # Texas
            "FL": 0.06,    # Florida
        }
        
        if shipping_address.get("country", "").upper() in ["US", "USA"]:
            state = shipping_address.get("state_province", "").upper()
            tax_rate = us_tax_rates.get(state, 0.0)
        
        return taxable_amount * tax_rate
    
    async def get_cart_summary(self, cart: Dict[str, Any]) -> CartSummary:
        """Generate cart summary information"""
        total_items = len(cart["items"])
        total_quantity = sum(item["quantity"] for item in cart["items"] if item.get("is_available", True))
        
        # Count unique vendors
        vendors = set()
        estimated_weight = 0.0
        
        for item in cart["items"]:
            if item.get("is_available", True):
                vendors.add(item["vendor_id"])
                # Add weight calculation if product has weight info
                product = await self.products_collection.find_one({"_id": ObjectId(item["product_id"])})
                if product:
                    weight_data = product.get("weight")
                    if isinstance(weight_data, dict) and weight_data.get("total_weight"):
                        estimated_weight += weight_data["total_weight"] * item["quantity"]
        
        return CartSummary(
            total_items=total_items,
            total_quantity=total_quantity,
            unique_vendors=len(vendors),
            estimated_weight=estimated_weight if estimated_weight > 0 else None,
            requires_shipping=total_quantity > 0  # Simplified check
        )

    async def find_item_in_cart(
        self,
        user_id: str,
        product_id: ObjectId,
        variant_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Find specific item in cart"""
        cart = await self.get_cart_by_user_id(user_id)
        if not cart:
            return None
            
        for item in cart["items"]:
            if (str(item["product_id"]) == str(product_id) and 
                item.get("variant_id") == variant_id):
                return item
                
        return None
    
    # =============================================================================
    # Extended wrapper methods for cart routes compatibility
    # =============================================================================
    
    async def clear_cart(self, user_id: str = None, session_id: str = None) -> Optional[Dict]:
        """Clear all items from cart (supports both user and guest carts)"""
        if user_id:
            cart = await self.get_cart_by_user_id(user_id)
        elif session_id:
            cart = await self.get_cart_by_session_id(session_id)
        else:
            return None
        
        if not cart:
            return None
        
        # Clear all items and reset totals
        cart["items"] = []
        cart["pricing_breakdown"] = {
            "subtotal": 0.0,
            "shipping_cost": 0.0,
            "tax_amount": 0.0,
            "discount_amount": 0.0,
            "total": 0.0
        }
        cart["applied_discounts"] = []
        cart["updated_at"] = datetime.utcnow()
        
        # Update in database
        await self.collection.update_one(
            {"_id": cart["_id"]},
            {"$set": cart}
        )
        
        return await self.format_cart_response(cart)
    
    async def remove_item(self, user_id: str = None, item_id: str = None, session_id: str = None) -> Optional[Dict]:
        """Remove item from cart (supports both user and guest carts)"""
        if user_id:
            cart = await self.get_cart_by_user_id(user_id)
        elif session_id:
            cart = await self.get_cart_by_session_id(session_id)
        else:
            return None
        
        if not cart:
            return None
        
        # Find and remove the item
        cart["items"] = [item for item in cart["items"] if str(item.get("id", item.get("_id"))) != item_id]
        cart["updated_at"] = datetime.utcnow()
        
        # Recalculate pricing
        cart = await self._recalculate_cart_pricing(cart)
        
        # Update in database
        await self.collection.update_one(
            {"_id": cart["_id"]},
            {"$set": cart}
        )
        
        return await self.format_cart_response(cart)
    
    async def update_item_quantity(self, user_id: str = None, item_id: str = None, quantity: int = 0, session_id: str = None) -> Optional[Dict]:
        """Update item quantity in cart (supports both user and guest carts)"""
        if user_id:
            cart = await self.get_cart_by_user_id(user_id)
        elif session_id:
            cart = await self.get_cart_by_session_id(session_id)
        else:
            return None
        
        if not cart:
            return None
        
        # Find and update the item
        for item in cart["items"]:
            if str(item.get("id", item.get("_id"))) == item_id:
                item["quantity"] = quantity
                item["line_total"] = item.get("price", 0.0) * quantity
                break
        
        cart["updated_at"] = datetime.utcnow()
        
        # Recalculate pricing
        cart = await self._recalculate_cart_pricing(cart)
        
        # Update in database
        await self.collection.update_one(
            {"_id": cart["_id"]},
            {"$set": cart}
        )
        
        return await self.format_cart_response(cart)
    
    async def apply_discount_code(self, user_id: str = None, code: str = None, session_id: str = None) -> Optional[Dict]:
        """Apply discount code to cart (supports both user and guest carts)"""
        if user_id:
            cart = await self.get_cart_by_user_id(user_id)
        elif session_id:
            cart = await self.get_cart_by_session_id(session_id)
        else:
            return None
        
        if not cart:
            return None
        
        # Here you would validate the discount code against a discounts collection
        # For now, we'll just add it to the cart
        if not cart.get("applied_discounts"):
            cart["applied_discounts"] = []
        
        cart["applied_discounts"].append({
            "code": code,
            "applied_at": datetime.utcnow()
        })
        cart["updated_at"] = datetime.utcnow()
        
        # Recalculate pricing with discount
        cart = await self._recalculate_cart_pricing(cart)
        
        # Update in database
        await self.collection.update_one(
            {"_id": cart["_id"]},
            {"$set": cart}
        )
        
        return await self.format_cart_response(cart)
    
    async def remove_discount_code(self, user_id: str = None, session_id: str = None) -> Optional[Dict]:
        """Remove discount code from cart (supports both user and guest carts)"""
        if user_id:
            cart = await self.get_cart_by_user_id(user_id)
        elif session_id:
            cart = await self.get_cart_by_session_id(session_id)
        else:
            return None
        
        if not cart:
            return None
        
        # Remove all applied discounts
        cart["applied_discounts"] = []
        cart["updated_at"] = datetime.utcnow()
        
        # Recalculate pricing without discount
        cart = await self._recalculate_cart_pricing(cart)
        
        # Update in database
        await self.collection.update_one(
            {"_id": cart["_id"]},
            {"$set": cart}
        )
        
        return await self.format_cart_response(cart)
    
    async def validate_checkout_readiness(self, user_id: str = None, session_id: str = None) -> CheckoutValidation:
        """Validate cart is ready for checkout (supports both user and guest carts)"""
        if user_id:
            cart = await self.get_cart_by_user_id(user_id)
        elif session_id:
            cart = await self.get_cart_by_session_id(session_id)
        else:
            return CheckoutValidation(
                is_valid=False,
                can_checkout=False,
                errors=["No cart found"],
                warnings=[]
            )
        
        if not cart:
            return CheckoutValidation(
                is_valid=False,
                can_checkout=False,
                errors=["Cart not found"],
                warnings=[]
            )
        
        issues = []
        warnings = []
        
        # Check if cart has items
        if not cart.get("items") or len(cart["items"]) == 0:
            issues.append("Cart is empty")
        
        # Check each item for availability
        for item in cart.get("items", []):
            if not item.get("is_available", True):
                issues.append(f"Item '{item.get('name', 'Unknown')}' is no longer available")
        
        # Check for minimum order amount (if applicable)
        if cart.get("pricing_breakdown", {}).get("subtotal", 0) < 10.0:
            warnings.append("Minimum order amount is $10")
        
        return CheckoutValidation(
            is_valid=len(issues) == 0,
            can_checkout=len(issues) == 0,
            errors=issues,
            warnings=warnings
        )
    
    async def _recalculate_cart_pricing(self, cart: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate cart pricing breakdown"""
        subtotal = sum(item.get("line_total", 0.0) for item in cart.get("items", []))
        
        # Calculate discount
        discount_amount = 0.0
        if cart.get("applied_discounts"):
            # Simple flat discount for now - you'd implement actual discount logic here
            discount_amount = subtotal * 0.1  # 10% discount example
        
        # Calculate tax (simplified)
        tax_amount = (subtotal - discount_amount) * 0.08  # 8% tax example
        
        # Shipping cost (simplified)
        shipping_cost = 0.0 if subtotal > 50 else 5.0
        
        # Total
        total = subtotal - discount_amount + tax_amount + shipping_cost
        
        cart["pricing_breakdown"] = {
            "subtotal": round(subtotal, 2),
            "shipping_cost": round(shipping_cost, 2),
            "tax_amount": round(tax_amount, 2),
            "discount_amount": round(discount_amount, 2),
            "total": round(total, 2)
        }
        
        return cart
    
    async def merge_carts(self, guest_session_id: str = None, user_id: str = None, user_cart: Dict[str, Any] = None, guest_cart: Dict[str, Any] = None, strategy: str = "combine") -> Dict[str, Any]:
        """Merge guest cart with user cart (supports both cart objects and IDs)"""
        # If cart objects not provided, fetch them
        if not user_cart and user_id:
            user_cart = await self.get_cart_by_user_id(user_id, create_if_not_exists=True)
        if not guest_cart and guest_session_id:
            guest_cart = await self.get_cart_by_session_id(guest_session_id, create_if_not_exists=False)
        
        if not user_cart or not guest_cart:
            return user_cart or guest_cart or None
        
        # Merge items from guest cart to user cart
        for guest_item in guest_cart.get("items", []):
            # Check if item already exists in user cart
            exists = False
            for user_item in user_cart.get("items", []):
                if (user_item.get("product_id") == guest_item.get("product_id") and
                    user_item.get("size") == guest_item.get("size") and
                    user_item.get("variant_id") == guest_item.get("variant_id")):
                    # Item exists, increase quantity
                    if strategy == "combine":
                        user_item["quantity"] += guest_item.get("quantity", 1)
                        user_item["line_total"] = user_item["quantity"] * user_item.get("price", 0.0)
                    elif strategy == "replace":
                        user_item["quantity"] = guest_item.get("quantity", 1)
                        user_item["line_total"] = user_item["quantity"] * user_item.get("price", 0.0)
                    exists = True
                    break
            
            if not exists:
                # Add new item to user cart
                user_cart["items"].append(guest_item)
        
        # Recalculate pricing
        user_cart = await self._recalculate_cart_pricing(user_cart)
        user_cart["updated_at"] = datetime.utcnow()
        
        # Update user cart in database
        await self.collection.update_one(
            {"_id": user_cart["_id"]},
            {"$set": user_cart}
        )
        
        # Deactivate guest cart
        await self.collection.update_one(
            {"_id": guest_cart["_id"]},
            {"$set": {"is_active": False, "merged_at": datetime.utcnow()}}
        )
        
        return await self.format_cart_response(user_cart)

    async def create_indexes(self) -> None:
        """Create necessary indexes for performance"""
        # Partial unique index on user_id (one cart per user, allows multiple null values for guest carts)
        # This uses a partial filter to only enforce uniqueness when user_id is not null
        try:
            await self.collection.create_index(
                "user_id", 
                unique=True,
                partialFilterExpression={"user_id": {"$type": "string"}},
                name="user_id_partial_unique"
            )
        except Exception as e:
            # Index might already exist, log and continue
            import logging
            logging.warning(f"Could not create user_id index: {e}")
        
        # Index on session_id for guest carts
        await self.collection.create_index("session_id")
        
        # Index on is_active for filtering active carts
        await self.collection.create_index("is_active")
        
        # Index on items.product_id for analytics
        await self.collection.create_index("items.product_id")