"""Business repository handling business profiles and KYC."""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId

class BusinessRepository:
    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db
        self.business_collection = db["business_profiles"]
        self.kyc_collection = db["kyc_documents"]
        self.activities_collection = db["user_activities"]
        self.preferences_collection = db["user_preferences"]

    async def create_business_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new business profile."""
        data.update({
            "user_id": user_id,
            "status": "pending",
            "created_at": datetime.utcnow(),
        })
        
        await self.business_collection.insert_one(data)
        return data

    async def get_business_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get business profile by user ID."""
        return await self.business_collection.find_one({"user_id": user_id})

    async def update_business_profile(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update business profile."""
        data["updated_at"] = datetime.utcnow()
        await self.business_collection.update_one(
            {"user_id": user_id},
            {"$set": data}
        )
        return await self.get_business_profile(user_id)

    async def submit_kyc_documents(self, user_id: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Submit KYC documents."""
        kyc_data = {
            "user_id": user_id,
            "documents": documents,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        await self.kyc_collection.insert_one(kyc_data)
        return kyc_data

    async def get_kyc_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get KYC status."""
        return await self.kyc_collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )

    async def update_kyc_status(self, user_id: str, status: str, reviewed_by: str) -> Optional[Dict[str, Any]]:
        """Update KYC verification status."""
        update_data = {
            "status": status,
            "reviewed_by": reviewed_by,
            "updated_at": datetime.utcnow()
        }
        
        await self.kyc_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        return await self.get_kyc_status(user_id)

    async def set_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Set user preferences."""
        preferences["user_id"] = user_id
        preferences["updated_at"] = datetime.utcnow()
        
        await self.preferences_collection.update_one(
            {"user_id": user_id},
            {"$set": preferences},
            upsert=True
        )
        return preferences

    async def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences."""
        return await self.preferences_collection.find_one({"user_id": user_id})

    async def log_activity(self, user_id: str, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Log user activity."""
        activity.update({
            "user_id": user_id,
            "created_at": datetime.utcnow()
        })
        
        await self.activities_collection.insert_one(activity)
        return activity

    async def get_activities(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        activity_type: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get user activities with pagination."""
        query = {"user_id": user_id}
        if activity_type:
            query["activity_type"] = activity_type
            
        cursor = self.activities_collection.find(query)
        total = await cursor.count()
        
        activities = await cursor.sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        return activities, total

    async def create_indexes(self):
        """Create necessary indexes."""
        await self.business_collection.create_index("user_id", unique=True)
        await self.kyc_collection.create_index([("user_id", 1), ("created_at", -1)])
        await self.activities_collection.create_index([("user_id", 1), ("created_at", -1)])
        await self.preferences_collection.create_index("user_id", unique=True)