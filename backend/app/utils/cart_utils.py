"""
Cart utility functions for product resolution, total calculation, and validation.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Dict, Optional
from app.databases.repositories.product import ProductRepository


async def resolve_product_id(db: AsyncIOMotorDatabase, identifier: str) -> Dict:
    """
    Resolve product by ID or slug to product document.
    Raises ValueError if not found.
    """
    products_collection = db["products"]
    
    # Try as ObjectId first
    try:
        obj_id = ObjectId(identifier)
        product = await products_collection.find_one({"_id": obj_id})
        if product:
            return product
    except Exception:
        pass
    
    # Try as slug
    product = await products_collection.find_one({"slug": identifier})
    if product:
        return product
    
    raise ValueError(f"Product not found: {identifier}")


def compute_item_total(price: float, quantity: int) -> float:
    """
    Compute item total (price * quantity) rounded to 2 decimals.
    """
    return round(price * quantity, 2)


async def get_or_create_cart(user_id: str, db: AsyncIOMotorDatabase) -> Dict:
    """
    Get existing cart or create new one for user.
    """
    from app.databases.repositories.cart import CartRepository
    cart_repo = CartRepository(db)
    return await cart_repo.get_or_create_cart(user_id)


async def find_item_index(cart_doc: Dict, product_id: str, variant_id: Optional[str] = None) -> Optional[int]:
    """
    Find item index in cart document.
    """
    if not cart_doc or "items" not in cart_doc:
        return None
        
    for i, item in enumerate(cart_doc["items"]):
        if (str(item["product_id"]) == str(product_id) and 
            item.get("variant_id") == variant_id):
            return i
            
    return None


async def validate_stock(product_doc: Dict, requested_quantity: int) -> bool:
    """
    Validate that requested quantity is available in stock.
    """
    # For this implementation, we'll assume products have a 'stock' field
    # In the existing product model, there doesn't seem to be a stock field
    # So we'll return True for now, but in a real implementation you would check stock
    stock = product_doc.get("stock", 999999)  # Default to large number if no stock field
    return stock >= requested_quantity


async def recalc_cart_totals(cart_doc: Dict) -> Dict:
    """
    Recalculate cart totals.
    """
    # Calculate subtotal (sum of item totals)
    subtotal = sum(item["item_total"] for item in cart_doc["items"])
    
    # Apply coupon discount if exists
    discount = 0.0
    if cart_doc.get("coupon"):
        coupon = cart_doc["coupon"]
        if "discount_amount" in coupon:
            discount = coupon["discount_amount"]
        elif "discount_percent" in coupon:
            discount = round(subtotal * (coupon["discount_percent"] / 100), 2)
    
    # Calculate tax (simple 10% for now)
    tax_rate = 0.10
    tax = round((subtotal - discount) * tax_rate, 2)
    
    # Delivery fee (free for orders over $100)
    delivery_fee = 0.0 if subtotal >= 100 else 5.99
    
    # Calculate final total
    total_amount = round(subtotal - discount + tax + delivery_fee, 2)
    
    # Ensure total doesn't go negative
    total_amount = max(0.0, total_amount)
    
    cart_doc["subtotal"] = round(subtotal, 2)
    cart_doc["discount"] = round(discount, 2)
    cart_doc["tax"] = round(tax, 2)
    cart_doc["delivery_fee"] = round(delivery_fee, 2)
    cart_doc["total_amount"] = round(total_amount, 2)
    
    return cart_doc