"""Admin repository for platform administration."""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from bson import ObjectId

class AdminRepository:
    def __init__(self, db):
        self.db = db
        self.users_collection = db["users"]
        self.settings_collection = db["platform_settings"]
        self.regions_collection = db["regions"]
        self.audit_logs_collection = db["audit_logs"]

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user (admin operation) - cannot create other admin accounts."""
        from app.utils.security import get_password_hash
        
        # Prevent admins from creating other admin accounts
        if user_data.get("role") in ["admin", "super_admin"]:
            raise ValueError("Cannot create admin accounts through this endpoint")
        
        # Hash password if provided
        if "password" in user_data:
            user_data["password_hash"] = get_password_hash(user_data.pop("password"))
        
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        
        # Set appropriate status based on role
        if user_data.get("role") == "vendor":
            user_data["status"] = "inactive"  # Vendors start inactive until approved
        else:
            user_data["status"] = "active"
        
        result = await self.users_collection.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        
        # Return formatted response without sensitive data
        return self.format_user_response(user_data)

    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user details (admin operation) - cannot modify admin accounts."""
        from app.utils.security import get_password_hash
        
        # First check if the target user is an admin
        existing_user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            return None
        
        if existing_user.get("role") in ["admin", "super_admin"]:
            raise ValueError("Cannot modify admin accounts")
        
        # Prevent role escalation to admin
        if update_data.get("role") in ["admin", "super_admin"]:
            raise ValueError("Cannot promote users to admin role")
        
        # Hash password if being updated
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        
        update_data["updated_at"] = datetime.utcnow()
        result = await self.users_collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True
        )
        
        return self.format_user_response(result) if result else None

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        role: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List non-admin users with filters."""
        # Base query to exclude admin accounts
        query = {"role": {"$nin": ["admin", "super_admin"]}}
        
        # Add role filter if specified (but still exclude admin roles)
        if role and role not in ["admin", "super_admin"]:
            query["role"] = role
        if status:
            query["status"] = status

        cursor = self.users_collection.find(query)
        total = await self.users_collection.count_documents(query)
        users = await cursor.skip(skip).limit(limit).to_list(length=limit)
        
        # Format users and remove sensitive information
        formatted_users = []
        for user in users:
            formatted_user = self.format_user_response(user)
            formatted_users.append(formatted_user)
        
        return formatted_users, total

    async def get_settings(self) -> Dict[str, Any]:
        """Get platform settings."""
        settings = await self.settings_collection.find_one({"_id": "default"})
        if not settings:
            # Initialize default settings
            settings = {
                "_id": "default",
                "commission_rate": 10.0,
                "payment_gateway_config": {},
                "tax_rates": {"default": 18.0},
                "min_withdrawal": 1000.0,
                "platform_fees": {"transaction": 2.0},
                "kyc_required": True,
                "auto_approve_vendors": False
            }
            await self.settings_collection.insert_one(settings)
        return settings

    async def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update platform settings."""
        settings["updated_at"] = datetime.utcnow()
        await self.settings_collection.update_one(
            {"_id": "default"},
            {"$set": settings},
            upsert=True
        )
        return settings

    async def create_region(self, region_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new region."""
        region_data["created_at"] = datetime.utcnow()
        result = await self.regions_collection.insert_one(region_data)
        
        # Convert ObjectId to string for JSON serialization
        region_data["_id"] = str(result.inserted_id)
        return region_data

    async def get_region(self, region_code: str) -> Optional[Dict[str, Any]]:
        """Get region by code."""
        region = await self.regions_collection.find_one({"code": region_code})
        if region and "_id" in region:
            region["_id"] = str(region["_id"])
        return region

    async def list_regions(
        self,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = True
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List regions."""
        query = {"is_active": True} if active_only else {}
        cursor = self.regions_collection.find(query)
        total = await self.regions_collection.count_documents(query)
        regions = await cursor.skip(skip).limit(limit).to_list(length=limit)
        
        # Convert ObjectIds to strings for JSON serialization
        for region in regions:
            if "_id" in region:
                region["_id"] = str(region["_id"])
        
        return regions, total

    async def approve_vendor(
        self,
        vendor_id: str,
        approved: bool,
        admin_id: str,
        remarks: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Approve or reject vendor application."""
        approval_status = "approved" if approved else "rejected"
        update_data = {
            "business_status": approval_status,
            "business_status_updated_at": datetime.utcnow(),
            "business_status_updated_by": admin_id,
            "business_status_remarks": remarks,
            "is_active": approved,  # Activate vendor if approved
            "status": "active" if approved else "inactive"
        }
        
        # Also update vendor_profile if it exists
        vendor_profiles_collection = self.db["vendor_profiles"]
        await vendor_profiles_collection.update_one(
            {"user_id": ObjectId(vendor_id)},
            {
                "$set": {
                    "approval_status": approval_status,
                    "approval_remarks": remarks,
                    "approved_by": admin_id,
                    "approved_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return await self.update_user(vendor_id, update_data)

    async def moderate_content(
        self,
        content_type: str,
        content_id: str,
        action: str,
        admin_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Moderate platform content (products/reviews)."""
        collection = self.db[content_type]
        update_data = {
            "moderation_status": action,
            "moderated_at": datetime.utcnow(),
            "moderated_by": admin_id,
            "moderation_reason": reason
        }
        result = await collection.update_one(
            {"_id": ObjectId(content_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def log_audit(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create audit log entry."""
        log_data["created_at"] = datetime.utcnow()
        result = await self.audit_logs_collection.insert_one(log_data)
        
        # Convert ObjectId to string for JSON serialization
        log_data["_id"] = str(result.inserted_id)
        return log_data

    def _convert_objectids_to_str(self, data: Any) -> Any:
        """Recursively convert ObjectIds to strings in any data structure."""
        from bson import ObjectId
        
        if isinstance(data, ObjectId):
            return str(data)
        elif isinstance(data, dict):
            return {key: self._convert_objectids_to_str(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_objectids_to_str(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
    
    async def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get audit logs with filters."""
        try:
            query = {}
            if action:
                query["action"] = action
            if entity_type:
                query["entity_type"] = entity_type
            if from_date or to_date:
                query["created_at"] = {}
                if from_date:
                    query["created_at"]["$gte"] = from_date
                if to_date:
                    query["created_at"]["$lte"] = to_date

            cursor = self.audit_logs_collection.find(query)
            total = await self.audit_logs_collection.count_documents(query)
            logs = await cursor.sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
            
            # Format logs for JSON serialization
            formatted_logs = []
            for log in logs:
                formatted_log = {
                    "id": str(log.get("_id", "")),
                    "action": log.get("action", ""),
                    "entity_type": log.get("entity_type", ""),
                    "entity_id": str(log.get("entity_id", "")) if log.get("entity_id") else "",
                    "performed_by": log.get("performed_by", ""),
                    "changes": self._convert_objectids_to_str(log.get("changes", {})),
                    "timestamp": log.get("created_at").isoformat() if log.get("created_at") else None,
                    "ip_address": log.get("ip_address", ""),
                    "user_agent": log.get("user_agent", "")
                }
                formatted_logs.append(formatted_log)
            
            return formatted_logs, total
        except Exception as e:
            print(f"Error in get_audit_logs: {str(e)}")
            import traceback
            traceback.print_exc()
            # Return empty list if there's an error
            return [], 0

    async def create_indexes(self):
        """Create necessary indexes."""
        await self.audit_logs_collection.create_index([("created_at", -1)])
        await self.audit_logs_collection.create_index("action")
        await self.audit_logs_collection.create_index("entity_type")
        await self.audit_logs_collection.create_index("performed_by")
        await self.regions_collection.create_index("code", unique=True)
    
    def format_user_response(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Format user document for API response - excludes sensitive data."""
        if not user:
            return None
        
        # Never include password or other sensitive fields
        created_at = user.get("created_at")
        updated_at = user.get("updated_at")
        response = {
            "id": str(user.get("_id", "")),
            "email": user.get("email", ""),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "phone": user.get("phone"),
            "avatar": user.get("avatar", "/uploads/avatar/default.png"),
            "role": user.get("role", "customer"),
            "status": user.get("status", "active"),
            "created_at": created_at.isoformat() if created_at else None,
            "updated_at": updated_at.isoformat() if updated_at else (created_at.isoformat() if created_at else None)
        }
        
        # Add business-related fields only for vendors
        if user.get("role") == "vendor":
            business_status_updated_at = user.get("business_status_updated_at")
            response.update({
                "business_name": user.get("business_name"),
                "business_type": user.get("business_type"),
                "business_status": user.get("business_status", "pending"),
                "business_status_updated_at": business_status_updated_at.isoformat() if business_status_updated_at else None
            })
        
        return response

    async def get_total_users(self) -> int:
        """Get total number of non-admin users."""
        # Exclude admin and super_admin roles from count
        return await self.users_collection.count_documents({
            "role": {"$nin": ["admin", "super_admin"]}
        })

    async def get_total_vendors(self) -> int:
        """Get total number of vendors."""
        return await self.users_collection.count_documents({"role": "vendor"})

    async def get_pending_vendor_approvals(self) -> int:
        """Get number of pending vendor approvals."""
        return await self.users_collection.count_documents({
            "role": "vendor",
            "business_status": {"$in": ["pending", None]}
        })

    async def get_recent_users(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recently created non-admin users."""
        # Only show customers and vendors, not other admins
        cursor = self.users_collection.find({
            "role": {"$nin": ["admin", "super_admin"]}
        }).sort("created_at", -1).limit(limit)
        users = await cursor.to_list(length=limit)
        return [self.format_user_response(user) for user in users]

    async def list_vendors(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List vendors for admin management."""
        query = {"role": "vendor"}
        
        if status:
            if status == "pending":
                query["business_status"] = {"$in": ["pending", None]}
            else:
                query["business_status"] = status

        cursor = self.users_collection.find(query)
        total = await self.users_collection.count_documents(query)
        vendors = await cursor.skip(skip).limit(limit).to_list(length=limit)
        
        # Format vendors with business information
        formatted_vendors = []
        for vendor in vendors:
            formatted_vendor = self.format_user_response(vendor)
            formatted_vendors.append(formatted_vendor)
        
        return formatted_vendors, total