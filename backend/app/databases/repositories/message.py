"""Message repository."""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from bson import ObjectId

class MessageRepository:
    def __init__(self, db):
        self.db = db
        self.messages_collection = db["messages"]
        self.threads_collection = db["message_threads"]
        self.users_collection = db["users"]

    async def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new message."""
        message_data["created_at"] = datetime.utcnow()
        message_data["delivered_at"] = None
        message_data["read_at"] = None
        
        # Insert message
        await self.messages_collection.insert_one(message_data)
        
        # Update thread
        if message_data.get("thread_id"):
            await self.threads_collection.update_one(
                {"_id": ObjectId(message_data["thread_id"])},
                {
                    "$set": {
                        "updated_at": datetime.utcnow(),
                        "last_message": message_data
                    },
                    "$inc": {"unread_count": 1}
                }
            )
        
        return message_data

    async def create_thread(self, thread_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new message thread."""
        now = datetime.utcnow()
        thread_data.update({
            "created_at": now,
            "updated_at": now,
            "last_message": None,
            "unread_count": 0
        })
        await self.threads_collection.insert_one(thread_data)
        return thread_data

    async def get_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get thread by ID."""
        return await self.threads_collection.find_one({"_id": ObjectId(thread_id)})

    async def get_user_threads(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get threads for a user."""
        query = {"participants": user_id}
        cursor = self.threads_collection.find(query)
        total = await cursor.count()
        threads = await cursor.sort("updated_at", -1).skip(skip).limit(limit).to_list(length=limit)
        return threads, total

    async def get_thread_messages(
        self,
        thread_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get messages in a thread."""
        query = {"thread_id": thread_id}
        cursor = self.messages_collection.find(query)
        total = await cursor.count()
        messages = await cursor.sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        return messages, total

    async def mark_messages_read(
        self,
        thread_id: str,
        user_id: str
    ) -> int:
        """Mark all messages in thread as read for user."""
        now = datetime.utcnow()
        result = await self.messages_collection.update_many(
            {
                "thread_id": thread_id,
                "recipient_id": user_id,
                "read_at": None
            },
            {"$set": {"read_at": now}}
        )
        
        if result.modified_count > 0:
            await self.threads_collection.update_one(
                {"_id": ObjectId(thread_id)},
                {"$set": {"unread_count": 0}}
            )
            
        return result.modified_count

    async def mark_messages_delivered(
        self,
        thread_id: str,
        user_id: str
    ) -> int:
        """Mark all messages in thread as delivered for user."""
        now = datetime.utcnow()
        result = await self.messages_collection.update_many(
            {
                "thread_id": thread_id,
                "recipient_id": user_id,
                "delivered_at": None
            },
            {"$set": {"delivered_at": now}}
        )
        return result.modified_count

    async def delete_message(self, message_id: str, user_id: str) -> bool:
        """Delete a message (soft delete)."""
        result = await self.messages_collection.update_one(
            {"_id": ObjectId(message_id), "sender_id": user_id},
            {"$set": {"deleted": True, "deleted_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def get_unread_count(self, user_id: str) -> int:
        """Get total unread messages for user."""
        cursor = self.messages_collection.find({
            "recipient_id": user_id,
            "read_at": None,
            "deleted": {"$ne": True}
        })
        return await cursor.count()

    async def create_indexes(self):
        """Create necessary indexes."""
        await self.messages_collection.create_index([
            ("thread_id", 1),
            ("created_at", -1)
        ])
        await self.messages_collection.create_index("sender_id")
        await self.messages_collection.create_index("recipient_id")
        await self.threads_collection.create_index("participants")
        await self.threads_collection.create_index("updated_at")