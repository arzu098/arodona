"""
Favorite repository for database operations.
Handles CRUD operations for favorites (wishlist) collection.

Collection Schema:
- _id: ObjectId
- user_id: ObjectId (required)
- product_id: ObjectId (required)
- created_at: datetime
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import Optional, List, Tuple, Dict
from pymongo.errors import DuplicateKeyError


class FavoriteRepository:
    """Repository for favorite-related database operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["favorites"]
        self.products_collection = db["products"]
    
    async def toggle_favorite(self, user_id: str, product_id: ObjectId) -> Dict:
        """
        Toggle favorite: remove if exists, add if doesn't.
        Returns: {"action": "added|removed", "product_id": str, "favorite_id": str}
        """
        # Try to find and delete existing favorite
        result = await self.collection.find_one_and_delete({
            "user_id": user_id,
            "product_id": product_id
        })
        
        if result:
            # Successfully removed
            return {
                "action": "removed",
                "product_id": str(product_id),
                "favorite_id": str(result["_id"])
            }
        
        # Not found, try to insert new favorite
        try:
            favorite_data = {
                "user_id": user_id,
                "product_id": product_id,
                "created_at": datetime.utcnow()
            }
            
            insert_result = await self.collection.insert_one(favorite_data)
            
            return {
                "action": "added",
                "product_id": str(product_id),
                "favorite_id": str(insert_result.inserted_id)
            }
        
        except DuplicateKeyError:
            # Race condition: another process inserted between our delete attempt and insert
            # Find the existing favorite and return it
            existing = await self.collection.find_one({
                "user_id": user_id,
                "product_id": product_id
            })
            
            if existing:
                return {
                    "action": "exists",
                    "product_id": str(product_id),
                    "favorite_id": str(existing["_id"])
                }
            else:
                # Very rare edge case, retry the toggle
                return await self.toggle_favorite(user_id, product_id)
    
    async def check_favorite(self, user_id: str, product_id: ObjectId) -> bool:
        """Check if a product is in user's favorites"""
        favorite = await self.collection.find_one({
            "user_id": user_id,
            "product_id": product_id
        })
        return favorite is not None
    
    async def list_user_favorites(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[int, List[Dict]]:
        """
        Get user's favorites with embedded product details.
        Returns: (total_count, list_of_favorites_with_products)
        """
        # Count total favorites for this user
        total = await self.collection.count_documents({"user_id": user_id})
        
        # Aggregate favorites with product details
        pipeline = [
            {"$match": {"user_id": user_id}},
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
                    "favorite_id": {"$toString": "$_id"},
                    "created_at": 1,
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
        
        favorites = await self.collection.aggregate(pipeline).to_list(None)
        
        return total, favorites
    
    async def remove_favorite(self, favorite_id: str, user_id: str) -> Optional[Dict]:
        """
        Remove a favorite by its ID.
        Ensures the favorite belongs to the user.
        Returns the deleted favorite or None if not found/unauthorized.
        """
        try:
            result = await self.collection.find_one_and_delete({
                "_id": ObjectId(favorite_id),
                "user_id": user_id
            })
            return result
        except Exception:
            return None
    
    async def get_favorite_by_id(self, favorite_id: str) -> Optional[Dict]:
        """Get a favorite by its ID"""
        try:
            return await self.collection.find_one({"_id": ObjectId(favorite_id)})
        except Exception:
            return None
    
    async def create_indexes(self) -> None:
        """Create necessary indexes for performance and uniqueness"""
        # Unique compound index to prevent duplicate favorites
        await self.collection.create_index(
            [("user_id", 1), ("product_id", 1)],
            unique=True
        )
        
        # Index on user_id for fast listing
        await self.collection.create_index("user_id")
        
        # Optional: index on product_id for analytics
        await self.collection.create_index("product_id")
