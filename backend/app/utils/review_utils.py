"""
Review utility functions for aggregation and product rating updates.
Handles recalculation and incremental updates of product rating fields.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import Dict


async def recalc_product_rating(db: AsyncIOMotorDatabase, product_id: ObjectId) -> Dict:
    """
    Full recalculation of product rating from reviews collection.
    Returns and updates: rating_avg, rating_count, ratings_breakdown
    """
    reviews_collection = db["reviews"]
    products_collection = db["products"]
    
    # Aggregate approved, non-deleted reviews
    pipeline = [
        {
            "$match": {
                "product_id": product_id,
                "deleted": False,
                "approved": True
            }
        },
        {
            "$group": {
                "_id": "$rating",
                "count": {"$sum": 1}
            }
        }
    ]
    
    results = await reviews_collection.aggregate(pipeline).to_list(None)
    
    # Build breakdown
    breakdown = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    total_count = 0
    total_rating = 0
    
    for item in results:
        rating = str(item["_id"])
        count = item["count"]
        breakdown[rating] = count
        total_count += count
        total_rating += item["_id"] * count
    
    rating_avg = round(total_rating / total_count, 2) if total_count > 0 else 0.0
    
    # Update product document
    await products_collection.update_one(
        {"_id": product_id},
        {
            "$set": {
                "rating_avg": rating_avg,
                "rating_count": total_count,
                "ratings_breakdown": breakdown,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "rating_avg": rating_avg,
        "rating_count": total_count,
        "ratings_breakdown": breakdown
    }


async def incremental_update_on_create(
    db: AsyncIOMotorDatabase,
    product_id: ObjectId,
    new_rating: int
) -> Dict:
    """
    Incremental update when a new review is created.
    More efficient than full recalculation for single additions.
    """
    products_collection = db["products"]
    
    # Get current product stats
    product = await products_collection.find_one({"_id": product_id})
    
    if not product:
        # Product doesn't exist, shouldn't happen
        return await recalc_product_rating(db, product_id)
    
    current_avg = product.get("rating_avg", 0.0)
    current_count = product.get("rating_count", 0)
    current_breakdown = product.get("ratings_breakdown", {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0})
    
    # Calculate new stats
    new_count = current_count + 1
    new_total = (current_avg * current_count) + new_rating
    new_avg = round(new_total / new_count, 2)
    
    # Update breakdown
    new_breakdown = current_breakdown.copy()
    new_breakdown[str(new_rating)] = new_breakdown.get(str(new_rating), 0) + 1
    
    # Update product
    await products_collection.update_one(
        {"_id": product_id},
        {
            "$set": {
                "rating_avg": new_avg,
                "rating_count": new_count,
                "ratings_breakdown": new_breakdown,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "rating_avg": new_avg,
        "rating_count": new_count,
        "ratings_breakdown": new_breakdown
    }


async def update_on_update(
    db: AsyncIOMotorDatabase,
    product_id: ObjectId,
    old_rating: int,
    new_rating: int
) -> Dict:
    """
    Update product stats when a review rating is changed.
    """
    if old_rating == new_rating:
        # No change needed
        products_collection = db["products"]
        product = await products_collection.find_one({"_id": product_id})
        return {
            "rating_avg": product.get("rating_avg", 0.0),
            "rating_count": product.get("rating_count", 0),
            "ratings_breakdown": product.get("ratings_breakdown", {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0})
        }
    
    products_collection = db["products"]
    product = await products_collection.find_one({"_id": product_id})
    
    if not product:
        return await recalc_product_rating(db, product_id)
    
    current_avg = product.get("rating_avg", 0.0)
    current_count = product.get("rating_count", 0)
    current_breakdown = product.get("ratings_breakdown", {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0})
    
    if current_count == 0:
        # Shouldn't happen, but recalculate to be safe
        return await recalc_product_rating(db, product_id)
    
    # Calculate new stats
    new_total = (current_avg * current_count) - old_rating + new_rating
    new_avg = round(new_total / current_count, 2)
    
    # Update breakdown
    new_breakdown = current_breakdown.copy()
    new_breakdown[str(old_rating)] = max(0, new_breakdown.get(str(old_rating), 0) - 1)
    new_breakdown[str(new_rating)] = new_breakdown.get(str(new_rating), 0) + 1
    
    # Update product
    await products_collection.update_one(
        {"_id": product_id},
        {
            "$set": {
                "rating_avg": new_avg,
                "rating_count": current_count,
                "ratings_breakdown": new_breakdown,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "rating_avg": new_avg,
        "rating_count": current_count,
        "ratings_breakdown": new_breakdown
    }


async def update_on_delete(
    db: AsyncIOMotorDatabase,
    product_id: ObjectId,
    deleted_rating: int
) -> Dict:
    """
    Update product stats when a review is deleted.
    """
    products_collection = db["products"]
    product = await products_collection.find_one({"_id": product_id})
    
    if not product:
        return await recalc_product_rating(db, product_id)
    
    current_avg = product.get("rating_avg", 0.0)
    current_count = product.get("rating_count", 0)
    current_breakdown = product.get("ratings_breakdown", {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0})
    
    if current_count <= 1:
        # Last review deleted, reset to zero
        await products_collection.update_one(
            {"_id": product_id},
            {
                "$set": {
                    "rating_avg": 0.0,
                    "rating_count": 0,
                    "ratings_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return {
            "rating_avg": 0.0,
            "rating_count": 0,
            "ratings_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        }
    
    # Calculate new stats
    new_count = current_count - 1
    new_total = (current_avg * current_count) - deleted_rating
    new_avg = round(new_total / new_count, 2)
    
    # Update breakdown
    new_breakdown = current_breakdown.copy()
    new_breakdown[str(deleted_rating)] = max(0, new_breakdown.get(str(deleted_rating), 0) - 1)
    
    # Update product
    await products_collection.update_one(
        {"_id": product_id},
        {
            "$set": {
                "rating_avg": new_avg,
                "rating_count": new_count,
                "ratings_breakdown": new_breakdown,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "rating_avg": new_avg,
        "rating_count": new_count,
        "ratings_breakdown": new_breakdown
    }


async def resolve_product_id(db: AsyncIOMotorDatabase, identifier: str) -> ObjectId:
    """
    Resolve product by ID or slug to ObjectId.
    Raises ValueError if not found.
    """
    products_collection = db["products"]
    
    # Try as ObjectId first
    try:
        obj_id = ObjectId(identifier)
        product = await products_collection.find_one({"_id": obj_id})
        if product:
            return obj_id
    except Exception:
        pass
    
    # Try as slug (if you have slug field)
    product = await products_collection.find_one({"slug": identifier})
    if product:
        return product["_id"]
    
    # Try as category or name (fallback)
    product = await products_collection.find_one({"category": identifier})
    if product:
        return product["_id"]
    
    raise ValueError(f"Product not found: {identifier}")
