"""Enhanced user repository with KYC workflows and activity tracking."""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from ..schemas.users import UserCreate, UserUpdate, UserResponse, UserRole, UserStatus, KYCStatus, KYCInfo
from ...utils.security import get_password_hash, verify_password


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.users
        self.activities_collection = db.user_activities

    async def create_user(self, 
                         email: Optional[str] = None,
                         password: Optional[str] = None,
                         first_name: Optional[str] = None,
                         last_name: Optional[str] = None,
                         phone: Optional[str] = None,
                         role: Optional[str] = None,
                         user_data: Optional[UserCreate] = None) -> Union[str, dict]:
        """
        Create a new user with hashed password.
        Can accept either individual parameters OR a UserCreate object.
        """
        # Handle both calling conventions
        if user_data is not None:
            email = user_data.email
            password = user_data.password
            first_name = user_data.first_name
            last_name = user_data.last_name
            phone = user_data.phone
            role_value = user_data.role.value if hasattr(user_data.role, 'value') else user_data.role
        else:
            role_value = role
        
        # Check if user already exists
        existing_user = await self.collection.find_one({"email": email})
        if existing_user:
            raise DuplicateKeyError("Email already registered")
        
        # Hash password
        hashed_password = get_password_hash(password)
        
        # Determine initial status based on role
        # Vendors should start as inactive until approved by admin
        if role_value == "vendor":
            initial_status = UserStatus.INACTIVE.value
        else:
            initial_status = UserStatus.ACTIVE.value
        
        # Prepare user document
        user_doc = {
            "email": email,
            "password_hash": hashed_password,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "role": role_value,
            "status": initial_status,
            "email_verified": False,
            "phone_verified": False,
            "avatar": None,
            "preferences": {
                "notifications": {
                    "email": True,
                    "sms": True,
                    "in_app": True
                },
                "language": "en",
                "currency": "USD"
            },
            "kyc": {
                "status": KYCStatus.PENDING.value,
                "documents": [],
                "verified_at": None,
                "verified_by": None,
                "rejection_reason": None
            },
            "two_factor": {
                "enabled": False,
                "secret": None,
                "backup_codes": []
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "managed_by": None  # For admin isolation
        }
        
        # Insert user
        result = await self.collection.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        
        # Return based on how it was called
        if user_data is not None:
            return str(result.inserted_id)
        else:
            return user_doc

    async def get_user_by_id(self, user_id: str, admin_id: Optional[str] = None) -> Optional[UserResponse]:
        """Get user by ID with optional admin isolation."""
        try:
            object_id = ObjectId(user_id)
        except:
            return None
            
        query = {"_id": object_id}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        user = await self.collection.find_one(query)
        if not user:
            return None
            
        return self._convert_to_response(user)
    
    async def get_user_by_email(self, email: str, admin_id: Optional[str] = None) -> Optional[UserResponse]:
        """Get user by email with optional admin isolation."""
        query = {"email": email}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        user = await self.collection.find_one(query)
        if not user:
            return None
            
        return self._convert_to_response(user)
    
    async def get_user_for_auth(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user document for authentication (returns raw dict with password hash)."""
        return await self.collection.find_one({"email": email})

    async def update_user(self, user_id: str, update_data: UserUpdate, admin_id: Optional[str] = None) -> bool:
        """Update user profile with optional admin isolation."""
        try:
            object_id = ObjectId(user_id)
        except:
            return False
        
        query = {"_id": object_id}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        # Prepare update document
        update_doc = {"$set": {"updated_at": datetime.utcnow()}}
        
        if update_data.first_name is not None:
            update_doc["$set"]["first_name"] = update_data.first_name
        if update_data.last_name is not None:
            update_doc["$set"]["last_name"] = update_data.last_name
        if update_data.phone is not None:
            update_doc["$set"]["phone"] = update_data.phone
        if update_data.avatar is not None:
            update_doc["$set"]["avatar"] = update_data.avatar
        if update_data.preferences is not None:
            update_doc["$set"]["preferences"] = update_data.preferences.dict()
        
        result = await self.collection.update_one(query, update_doc)
        return result.modified_count > 0
    
    async def update_user_status(self, user_id: str, status: UserStatus, admin_id: Optional[str] = None) -> bool:
        """Update user status (admin operation)."""
        try:
            object_id = ObjectId(user_id)
        except:
            return False
        
        query = {"_id": object_id}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        update_doc = {
            "$set": {
                "status": status.value,
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await self.collection.update_one(query, update_doc)
        return result.modified_count > 0

    async def verify_email(self, user_id: str, admin_id: Optional[str] = None) -> bool:
        """Mark user email as verified."""
        try:
            object_id = ObjectId(user_id)
        except:
            return False
        
        query = {"_id": object_id}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        update_doc = {
            "$set": {
                "email_verified": True,
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await self.collection.update_one(query, update_doc)
        return result.modified_count > 0
    
    async def verify_phone(self, user_id: str, admin_id: Optional[str] = None) -> bool:
        """Mark user phone as verified."""
        try:
            object_id = ObjectId(user_id)
        except:
            return False
        
        query = {"_id": object_id}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        update_doc = {
            "$set": {
                "phone_verified": True,
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await self.collection.update_one(query, update_doc)
        return result.modified_count > 0
    
    async def update_kyc_status(self, user_id: str, status: KYCStatus, 
                               verified_by: Optional[str] = None, 
                               rejection_reason: Optional[str] = None,
                               admin_id: Optional[str] = None) -> bool:
        """Update KYC status."""
        try:
            object_id = ObjectId(user_id)
        except:
            return False
        
        query = {"_id": object_id}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        kyc_update = {
            "status": status.value,
        }
        
        if status == KYCStatus.VERIFIED:
            kyc_update["verified_at"] = datetime.utcnow()
            kyc_update["verified_by"] = verified_by
            kyc_update["rejection_reason"] = None
        elif status == KYCStatus.REJECTED:
            kyc_update["rejection_reason"] = rejection_reason
            kyc_update["verified_at"] = None
            kyc_update["verified_by"] = None
        
        update_doc = {
            "$set": {
                "kyc": kyc_update,
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await self.collection.update_one(query, update_doc)
        return result.modified_count > 0
    
    async def add_kyc_document(self, user_id: str, document_url: str, admin_id: Optional[str] = None) -> bool:
        """Add KYC document to user."""
        try:
            object_id = ObjectId(user_id)
        except:
            return False
        
        query = {"_id": object_id}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        update_doc = {
            "$push": {"kyc.documents": document_url},
            "$set": {"updated_at": datetime.utcnow()}
        }
        
        result = await self.collection.update_one(query, update_doc)
        return result.modified_count > 0
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        try:
            object_id = ObjectId(user_id)
        except:
            return False
        
        update_doc = {
            "$set": {
                "last_login": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await self.collection.update_one({"_id": object_id}, update_doc)
        return result.modified_count > 0
    
    async def update_password(self, user_id: str, new_password_hash: str, admin_id: Optional[str] = None) -> bool:
        """Update user password hash."""
        try:
            object_id = ObjectId(user_id)
        except:
            return False
        
        query = {"_id": object_id}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        update_doc = {
            "$set": {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await self.collection.update_one(query, update_doc)
        return result.modified_count > 0
    
    async def get_users(self, skip: int = 0, limit: int = 20, 
                       role: Optional[UserRole] = None, 
                       status: Optional[UserStatus] = None,
                       admin_id: Optional[str] = None) -> List[UserResponse]:
        """Get paginated list of users with optional filters and admin isolation."""
        query = {}
        
        if role:
            query["role"] = role.value
        if status:
            query["status"] = status.value
            
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        users = await cursor.to_list(length=None)
        
        return [self._convert_to_response(user) for user in users]
    
    async def count_users(self, role: Optional[UserRole] = None, 
                         status: Optional[UserStatus] = None,
                         admin_id: Optional[str] = None) -> int:
        """Count users with optional filters and admin isolation."""
        query = {}
        
        if role:
            query["role"] = role.value
        if status:
            query["status"] = status.value
            
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        return await self.collection.count_documents(query)
    
    async def get_kyc_pending_users(self, admin_id: Optional[str] = None) -> List[UserResponse]:
        """Get users with pending KYC status."""
        query = {"kyc.status": KYCStatus.PENDING.value}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        cursor = self.collection.find(query).sort("created_at", 1)
        users = await cursor.to_list(length=None)
        
        return [self._convert_to_response(user) for user in users]
    
    async def assign_user_to_admin(self, user_id: str, admin_id: str) -> bool:
        """Assign user to admin for management (admin isolation)."""
        try:
            object_id = ObjectId(user_id)
        except:
            return False
        
        update_doc = {
            "$set": {
                "managed_by": admin_id,
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await self.collection.update_one({"_id": object_id}, update_doc)
        return result.modified_count > 0
    
    async def delete_user(self, user_id: str, admin_id: Optional[str] = None) -> bool:
        """Soft delete user by setting status to inactive."""
        return await self.update_user_status(user_id, UserStatus.INACTIVE, admin_id)
    async def setup_2fa(self, user_id: str, secret: str, backup_codes: List[str]) -> bool:
        """Setup 2FA for user"""
        try:
            # Hash backup codes for storage
            hashed_backup_codes = [get_password_hash(code) for code in backup_codes]
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "two_factor": {
                            "secret": secret,
                            "enabled": False,
                            "backup_codes": hashed_backup_codes,
                            "setup_at": datetime.utcnow()
                        },
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def enable_2fa(self, user_id: str) -> bool:
        """Enable 2FA after successful verification"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "two_factor.enabled": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def get_2fa_secret(self, user_id: str) -> Optional[str]:
        """Get user's 2FA secret"""
        user_doc = await self.collection.find_one({"_id": ObjectId(user_id)})
        if user_doc and "two_factor" in user_doc:
            return user_doc["two_factor"].get("secret")
        return None

    async def verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify and consume a backup code"""
        user_doc = await self.collection.find_one({"_id": ObjectId(user_id)})
        if not user_doc or "two_factor" not in user_doc:
            return False

        backup_codes = user_doc["two_factor"].get("backup_codes", [])
        for hashed_code in backup_codes:
            if verify_password(code, hashed_code):
                # Remove used backup code
                await self.collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$pull": {"two_factor.backup_codes": hashed_code}}
                )
                return True
        return False

    async def log_activity(self, user_id: str, activity_type: str, details: Dict[str, Any]) -> None:
        """Log user activity"""
        activity = {
            "user_id": user_id,
            "type": activity_type,
            "details": details,
            "timestamp": datetime.utcnow()
        }
        await self.activities_collection.insert_one(activity)

    async def get_user_activities(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user activity logs"""
        try:
            activities = await self.activities_collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit).to_list(limit)
            
            # Add session activities
            sessions = await self.db["sessions"].find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit).to_list(limit)
            
            session_activities = [{
                "type": "session",
                "timestamp": session["created_at"],
                "details": {
                    "ip": session.get("ip_address"),
                    "device": session.get("user_agent"),
                    "status": "active" if not session.get("revoked_at") else "revoked"
                }
            } for session in sessions]
            
            # Combine and sort all activities
            all_activities = activities + session_activities
            all_activities.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return all_activities[:limit]
        except Exception:
            return []
    
    def _convert_to_response(self, user_doc: Dict[str, Any]) -> UserResponse:
        """Convert MongoDB document to UserResponse."""
        # Convert ObjectId to string
        user_doc["id"] = str(user_doc["_id"])
        
        # Handle missing updated_at field (for legacy users)
        if "updated_at" not in user_doc:
            user_doc["updated_at"] = user_doc.get("created_at", datetime.utcnow())
        
        # Handle nested objects
        if "preferences" not in user_doc:
            user_doc["preferences"] = {
                "notifications": {"email": True, "sms": True, "in_app": True},
                "language": "en",
                "currency": "USD"
            }
        
        if "kyc" not in user_doc:
            user_doc["kyc"] = {
                "status": KYCStatus.PENDING.value,
                "documents": [],
                "verified_at": None,
                "verified_by": None,
                "rejection_reason": None
            }
        
        if "two_factor" not in user_doc:
            user_doc["two_factor"] = {
                "enabled": False,
                "secret": None,
                "backup_codes": []
            }
        
        return UserResponse(**user_doc)
    
    async def user_exists(self, email: str) -> bool:
        """Check if a user with the given email exists."""
        user = await self.collection.find_one({"email": email})
        return user is not None
    
    async def count_users_by_role(self, role: str) -> int:
        """Count users with a specific role."""
        return await self.collection.count_documents({"role": role})
    
    async def get_users_by_role(self, role: str, skip: int = 0, limit: int = 10):
        """Get users filtered by role."""
        cursor = self.collection.find({"role": role}).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        total = await self.collection.count_documents({"role": role})
        return users, total
    
    async def get_all_users(self, skip: int = 0, limit: int = 10):
        """Get all users."""
        cursor = self.collection.find({}).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        total = await self.collection.count_documents({})
        return users, total

    async def count_all_users(self) -> int:
        """Count all users in the system."""
        return await self.collection.count_documents({})

    async def get_recent_users(self, limit: int = 5):
        """Get recently created users (most recent first)."""
        cursor = self.collection.find({}).sort("created_at", -1).limit(limit)
        users = await cursor.to_list(length=limit)
        # Return raw user documents (routes will format as needed)
        return [self._convert_to_response(user) for user in users]
    
    def format_user_response(self, user: dict) -> dict:
        """Format user document for API response."""
        return {
            "id": str(user.get("_id")),
            "email": user.get("email"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "phone": user.get("phone"),
            "role": user.get("role"),
            "avatar": user.get("avatar"),
            "created_at": user.get("created_at"),
            "status": user.get("status", "active")
        }
