"""Notification repository."""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from bson import ObjectId

class NotificationRepository:
    def __init__(self, db):
        self.db = db
        self.notifications_collection = db["notifications"]
        self.settings_collection = db["notification_settings"]

    async def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new notification."""
        notification_data["created_at"] = datetime.utcnow()
        notification_data["read_at"] = None
        notification_data["delivered_at"] = None
        await self.notifications_collection.insert_one(notification_data)
        return notification_data

    async def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get notification by ID."""
        return await self.notifications_collection.find_one({"_id": ObjectId(notification_id)})

    async def list_notifications(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """List notifications for a user."""
        query = {"user_id": user_id}
        if unread_only:
            query["read_at"] = None

        cursor = self.notifications_collection.find(query)
        total = await cursor.count()
        unread = await self.notifications_collection.count_documents({
            "user_id": user_id,
            "read_at": None
        })
        
        notifications = await cursor.sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        return notifications, total, unread

    async def mark_read(
        self,
        notification_ids: List[str],
        user_id: str
    ) -> int:
        """Mark notifications as read."""
        now = datetime.utcnow()
        result = await self.notifications_collection.update_many(
            {
                "_id": {"$in": [ObjectId(id) for id in notification_ids]},
                "user_id": user_id,
                "read_at": None
            },
            {"$set": {"read_at": now}}
        )
        return result.modified_count

    async def mark_delivered(
        self,
        notification_ids: List[str],
        user_id: str
    ) -> int:
        """Mark notifications as delivered."""
        now = datetime.utcnow()
        result = await self.notifications_collection.update_many(
            {
                "_id": {"$in": [ObjectId(id) for id in notification_ids]},
                "user_id": user_id,
                "delivered_at": None
            },
            {"$set": {"delivered_at": now}}
        )
        return result.modified_count

    async def delete_notifications(
        self,
        notification_ids: List[str],
        user_id: str
    ) -> int:
        """Delete notifications."""
        result = await self.notifications_collection.delete_many({
            "_id": {"$in": [ObjectId(id) for id in notification_ids]},
            "user_id": user_id
        })
        return result.deleted_count

    async def get_user_settings(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user's notification settings."""
        return await self.settings_collection.find_one({"user_id": user_id})

    async def update_user_settings(
        self,
        user_id: str,
        settings: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update user's notification settings."""
        settings["updated_at"] = datetime.utcnow()
        await self.settings_collection.update_one(
            {"user_id": user_id},
            {"$set": settings},
            upsert=True
        )
        return await self.get_user_settings(user_id)

    async def create_indexes(self):
        """Create necessary indexes."""
        await self.notifications_collection.create_index([("user_id", 1), ("created_at", -1)])
        await self.notifications_collection.create_index("read_at")
        await self.settings_collection.create_index("user_id", unique=True)