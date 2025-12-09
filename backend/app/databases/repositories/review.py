"""
Review repository for database operations.
Handles CRUD operations for reviews collection.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import Optional, List, Tuple, Dict


class ReviewRepository:
    """Repository for review-related database operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["reviews"]
        self.products_collection = db["products"]
    
    async def create_review(
        self,
        product_id: ObjectId,
        user_id: str,
        full_name: Optional[str],
        rating: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        is_verified_buyer: bool = False,
        approved: bool = True
    ) -> dict:
        """Create a new review"""
        review_data = {
            "product_id": product_id,
            "user_id": user_id,
            "full_name": full_name,
            "rating": rating,
            "title": title,
            "body": body,
            "images": images or [],
            "videos": videos or [],
            "is_verified_buyer": is_verified_buyer,
            "approved": approved,
            "helpful_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deleted": False
        }
        
        result = await self.collection.insert_one(review_data)
        review_data["_id"] = result.inserted_id
        return review_data
    
    async def get_review_by_id(self, review_id: str) -> Optional[dict]:
        """Get review by MongoDB ID"""
        try:
            return await self.collection.find_one({"_id": ObjectId(review_id)})
        except Exception:
            return None
    
    async def check_existing_review(self, product_id: ObjectId, user_id: str) -> Optional[dict]:
        """Check if user already reviewed this product"""
        return await self.collection.find_one({
            "product_id": product_id,
            "user_id": user_id,
            "deleted": False
        })
    
    async def get_reviews_by_product(
        self,
        product_id: ObjectId,
        skip: int = 0,
        limit: int = 10,
        sort_by: str = "newest",
        approved_only: bool = True
    ) -> Tuple[List[dict], int]:
        """Get reviews for a product with pagination and sorting"""
        query = {"product_id": product_id, "deleted": False}
        if approved_only:
            query["approved"] = True
        
        # Determine sort order
        sort_field = [("created_at", -1)]  # Default: newest
        if sort_by == "oldest":
            sort_field = [("created_at", 1)]
        elif sort_by == "rating_desc":
            sort_field = [("rating", -1), ("created_at", -1)]
        elif sort_by == "rating_asc":
            sort_field = [("rating", 1), ("created_at", -1)]
        elif sort_by == "helpful":
            sort_field = [("helpful_count", -1), ("created_at", -1)]
        
        total = await self.collection.count_documents(query)
        reviews = await self.collection.find(query).sort(sort_field).skip(skip).limit(limit).to_list(limit)
        return reviews, total
    
    async def get_reviews_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[dict], int]:
        """Get reviews by user"""
        query = {"user_id": user_id, "deleted": False}
        total = await self.collection.count_documents(query)
        reviews = await self.collection.find(query).sort([("created_at", -1)]).skip(skip).limit(limit).to_list(limit)
        return reviews, total
    
    async def get_user_reviews_with_products(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[int, List[dict]]:
        """
        Get user's reviews with embedded product details.
        Returns: (total_count, list_of_reviews_with_products)
        """
        # Count total reviews for this user
        total = await self.collection.count_documents({"user_id": user_id, "deleted": False})
        
        # Aggregate reviews with product details
        pipeline = [
            {"$match": {"user_id": user_id, "deleted": False}},
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "products",
                    "localField": "product_id",
                    "foreignField": "_id",
                    "as": "product_details"
                }
            },
            {"$unwind": "$product_details"},
            {
                "$project": {
                    "_id": 0,  # Exclude the original _id field
                    "review_id": {"$toString": "$_id"},
                    "rating": 1,
                    "title": 1,
                    "body": 1,
                    "images": {"$ifNull": ["$images", []]},
                    "created_at": 1,
                    "updated_at": 1,
                    "product": {
                        "id": {"$toString": "$product_details._id"},
                        "name": "$product_details.name",
                        "slug": {"$ifNull": ["$product_details.slug", None]},
                        "price": "$product_details.price",
                        "images": {"$ifNull": ["$product_details.images", []]}
                    }
                }
            }
        ]
        
        reviews = await self.collection.aggregate(pipeline).to_list(None)
        
        return total, reviews
    
    async def update_review(
        self,
        review_id: str,
        update_data: dict
    ) -> Optional[dict]:
        """Update review details"""
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return await self.get_review_by_id(review_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(review_id)},
                {"$set": update_data},
                return_document=True
            )
            return result
        except Exception:
            return None
    
    async def soft_delete_review(self, review_id: str) -> Optional[dict]:
        """Soft delete a review (set deleted=True)"""
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(review_id)},
                {"$set": {"deleted": True, "updated_at": datetime.utcnow()}},
                return_document=True
            )
            return result
        except Exception:
            return None
    
    async def increment_helpful_count(self, review_id: str, increment: int = 1) -> Optional[dict]:
        """Increment or decrement helpful count"""
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(review_id)},
                {"$inc": {"helpful_count": increment}},
                return_document=True
            )
            return result
        except Exception:
            return None
    
    async def get_pending_reviews(self, skip: int = 0, limit: int = 10) -> Tuple[List[dict], int]:
        """Get reviews pending approval"""
        query = {"approved": False, "deleted": False}
        total = await self.collection.count_documents(query)
        reviews = await self.collection.find(query).sort([("created_at", -1)]).skip(skip).limit(limit).to_list(limit)
        return reviews, total
    
    async def approve_review(self, review_id: str, approved: bool) -> Optional[dict]:
        """Approve or reject a review"""
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(review_id)},
                {"$set": {"approved": approved, "updated_at": datetime.utcnow()}},
                return_document=True
            )
            return result
        except Exception:
            return None
    
    async def get_rating_aggregates(self, product_id: ObjectId) -> Dict:
        """
        Get rating aggregates for a product.
        Returns: { "rating_avg": float, "rating_count": int, "ratings_breakdown": {"1": n1, ...} }
        """
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
        
        results = await self.collection.aggregate(pipeline).to_list(None)
        
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
        
        return {
            "rating_avg": rating_avg,
            "rating_count": total_count,
            "ratings_breakdown": breakdown
        }
    
    def format_review_response(self, review: dict) -> dict:
        """Format review document for response"""
        return {
            "id": str(review["_id"]),
            "product_id": str(review["product_id"]),
            "user_id": review["user_id"],
            "full_name": review.get("full_name"),
            "rating": review["rating"],
            "title": review.get("title"),
            "body": review.get("body"),
            "images": review.get("images", []),
            "is_verified_buyer": review.get("is_verified_buyer", False),
            "approved": review.get("approved", True),
            "helpful_count": review.get("helpful_count", 0),
            "created_at": review["created_at"],
            "updated_at": review["updated_at"],
            "deleted": review.get("deleted", False)
        }