"""Enhanced session repository for JWT session management."""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.utils.security import hash_token, verify_hashed_token

class SessionRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["sessions"]

    async def create_session(self, session_data: Dict[str, Any]) -> str:
        """Create a new session."""
        session_data["created_at"] = datetime.utcnow()
        session_data["revoked"] = False
        session_data["last_activity"] = datetime.utcnow()
        
        # Hash the refresh token for storage
        if "refresh_token" in session_data:
            session_data["refresh_token_hash"] = hash_token(session_data["refresh_token"])
            del session_data["refresh_token"]  # Don't store plain token
        
        result = await self.collection.insert_one(session_data)
        return str(result.inserted_id)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(session_id)})
        except:
            return None

    async def verify_refresh_token(self, session_id: str, refresh_token: str) -> bool:
        """Verify refresh token against stored hash."""
        try:
            session = await self.get_session(session_id)
            if not session or session.get("revoked"):
                return False
            
            # Check if session is expired
            if session.get("expires_at") and session["expires_at"] < datetime.utcnow():
                await self.revoke_session(session_id)
                return False
                
            return verify_hashed_token(refresh_token, session.get("refresh_token_hash", ""))
        except:
            return False

    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a session."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {"revoked": True, "revoked_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except:
            return False

    async def revoke_all_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user."""
        try:
            result = await self.collection.update_many(
                {"user_id": user_id, "revoked": False},
                {"$set": {"revoked": True, "revoked_at": datetime.utcnow()}}
            )
            return result.modified_count
        except:
            return 0

    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        try:
            query = {"user_id": user_id}
            if active_only:
                query["revoked"] = False
                query["expires_at"] = {"$gt": datetime.utcnow()}
            
            cursor = self.collection.find(query).sort("created_at", -1)
            return await cursor.to_list(length=100)
        except:
            return []

    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions."""
        try:
            result = await self.collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            return result.deleted_count
        except:
            return 0

    async def update_session_activity(self, session_id: str, ip_address: str, device_info: str) -> bool:
        """Update session with latest activity."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {
                    "last_activity": datetime.utcnow(),
                    "ip_address": ip_address,
                    "device_info": device_info
                }}
            )
            return result.modified_count > 0
        except:
            return False

    async def get_session_stats(self, user_id: str) -> Dict[str, Any]:
        """Get session statistics for a user."""
        try:
            total_sessions = await self.collection.count_documents({"user_id": user_id})
            active_sessions = await self.collection.count_documents({
                "user_id": user_id,
                "revoked": False,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            # Get latest session
            latest_session = await self.collection.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "latest_activity": latest_session.get("last_activity") if latest_session else None
            }
        except:
            return {"total_sessions": 0, "active_sessions": 0, "latest_activity": None}

    # Legacy methods for backward compatibility
    async def revoke_user_sessions(self, user_id: str) -> int:
        """Legacy method - revoke all sessions for a user."""
        return await self.revoke_all_user_sessions(user_id)

    async def get_active_sessions(self, user_id: str) -> List[dict]:
        """Legacy method - get active sessions."""
        return await self.get_user_sessions(user_id, active_only=True)

    async def check_token_revoked(self, token: str) -> bool:
        """Legacy method - check if a token has been revoked."""
        session = await self.collection.find_one({
            "token": token,
            "revoked": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        return session is None