"""Enhanced vendor repository with application workflow and storefront management."""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from ..schemas.vendor import (
    VendorCreate, VendorUpdate, VendorResponse, VendorStatus, VendorApprovalStatus,
    BusinessType
)

class VendorRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.users  # Vendors are stored in users collection
        self.activities_collection = db.vendor_activities

    async def get_vendor(self, vendor_id: str) -> Optional[dict]:
        """Get vendor by ID"""
        vendor = await self.collection.find_one({"_id": ObjectId(vendor_id)})
        return vendor

    async def get_vendor_by_user(self, user_id: str) -> Optional[dict]:
        """Get vendor by user ID"""
        vendor = await self.collection.find_one({"user_id": user_id})
        return vendor
    
    async def get_vendor_by_user_id(self, user_id: str) -> Optional[VendorResponse]:
        """Get vendor by user ID and return as VendorResponse"""
        # In this system, vendors are stored in the users collection with role='vendor'
        try:
            object_id = ObjectId(user_id)
        except:
            return None
        
        vendor = await self.collection.find_one({"_id": object_id, "role": "vendor"})
        if vendor:
            return self._convert_to_response(vendor)
        return None
    
    async def get_vendor_by_id(self, vendor_id: str, admin_id: Optional[str] = None) -> Optional[VendorResponse]:
        """Get vendor by vendor ID and return as VendorResponse"""
        try:
            object_id = ObjectId(vendor_id)
        except:
            return None
        
        query = {"_id": object_id}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        vendor = await self.collection.find_one(query)
        if vendor:
            return self._convert_to_response(vendor)
        return None

    async def update_vendor(self, vendor_id: str, data: VendorUpdate) -> bool:
        """Update vendor"""
        # Convert Pydantic model to dict, excluding None values
        update_data = data.dict(exclude_none=True, exclude_unset=True)
        
        # Remove fields that shouldn't be updated directly
        update_data.pop("status", None)
        
        if "storefront" in update_data:
            update_data["storefront"] = update_data["storefront"]
        
        if "business_address" in update_data:
            update_data["business_address"] = update_data["business_address"]
        
        if "bank_details" in update_data:
            update_data["bank_details"] = update_data["bank_details"]
        
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(vendor_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except:
            return False

    async def update_vendor_status(self, vendor_id: str, status: VendorStatus, admin_id: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Update vendor status"""
        try:
            object_id = ObjectId(vendor_id)
        except:
            return False
        
        query = {"_id": object_id}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        if status == VendorStatus.ACTIVE:
            update_data["approval_date"] = datetime.utcnow()
        
        if notes:
            update_data["status_notes"] = notes
            
        result = await self.collection.update_one(query, {"$set": update_data})
        return result.modified_count > 0

    async def get_vendors(self, 
                         skip: int = 0, 
                         limit: int = 10, 
                         status: Optional[VendorStatus] = None,
                         approval_status: Optional[VendorApprovalStatus] = None,
                         business_type: Optional[BusinessType] = None,
                         admin_id: Optional[str] = None,
                         search: Optional[str] = None) -> List[VendorResponse]:
        """Get vendors with filters and pagination"""
        filter_query = {}
        
        if status:
            filter_query["status"] = status.value
        
        if approval_status:
            filter_query["approval_status"] = approval_status.value
        
        if business_type:
            filter_query["business_type"] = business_type.value
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            filter_query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
            
        if search:
            filter_query["$or"] = [
                {"business_name": {"$regex": search, "$options": "i"}},
                {"storefront.store_name": {"$regex": search, "$options": "i"}}
            ]
        
        cursor = self.collection.find(filter_query)
        cursor.skip(skip).limit(limit)
        vendors = await cursor.to_list(limit)
        
        return [self._convert_to_response(vendor) for vendor in vendors]
    
    async def count_vendors(self,
                           status: Optional[VendorStatus] = None,
                           approval_status: Optional[VendorApprovalStatus] = None,
                           business_type: Optional[BusinessType] = None,
                           admin_id: Optional[str] = None) -> int:
        """Count vendors with filters"""
        filter_query = {}
        
        if status:
            filter_query["status"] = status.value
        
        if approval_status:
            filter_query["approval_status"] = approval_status.value
        
        if business_type:
            filter_query["business_type"] = business_type.value
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            filter_query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        return await self.collection.count_documents(filter_query)

    
    # Enhanced vendor application workflow methods
    async def create_vendor_application(self, user_id: str, vendor_data: VendorCreate) -> str:
        """Create a new vendor application."""
        # Check if user already has a vendor application
        existing_vendor = await self.collection.find_one({"user_id": user_id})
        if existing_vendor:
            raise DuplicateKeyError("User already has a vendor application")
        
        # Prepare vendor document
        vendor_doc = {
            "user_id": user_id,
            "business_name": vendor_data.business_name,
            "business_type": vendor_data.business_type.value,
            "business_description": vendor_data.business_description,
            "business_registration_number": vendor_data.business_registration_number,
            "tax_id": vendor_data.tax_id,
            "contact_person": vendor_data.contact_person,
            "contact_email": vendor_data.contact_email,
            "contact_phone": vendor_data.contact_phone,
            "business_address": vendor_data.business_address.dict(),
            "bank_details": vendor_data.bank_details.dict() if vendor_data.bank_details else None,
            "status": VendorStatus.PENDING.value,
            "approval_status": VendorApprovalStatus.PENDING.value,
            "application_date": datetime.utcnow(),
            "documents": [],
            "storefront": {
                "store_name": vendor_data.business_name,
                "store_description": vendor_data.business_description,
                "logo": None,
                "banner": None,
                "theme_color": "#000000",
                "social_links": {},
                "business_hours": {},
                "return_policy": "",
                "shipping_policy": "",
                "is_active": False
            },
            "performance": {
                "total_sales": 0.0,
                "total_orders": 0,
                "average_rating": 0.0,
                "total_reviews": 0,
                "response_time_hours": 0.0,
                "fulfillment_rate": 0.0,
                "commission_rate": 0.05  # Default 5%
            },
            "settings": {
                "auto_accept_orders": False,
                "max_processing_time_days": 7,
                "min_order_amount": 0.0,
                "free_shipping_threshold": 0.0,
                "notifications": {
                    "new_orders": True,
                    "low_inventory": True,
                    "reviews": True,
                    "payments": True
                }
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "approved_at": None,
            "approved_by": None,
            "rejection_reason": None,
            "managed_by": None  # For admin isolation
        }
        
        # Insert vendor
        result = await self.collection.insert_one(vendor_doc)
        
        # Log activity
        await self.log_vendor_activity(
            str(result.inserted_id),
            "application_submitted",
            {"business_name": vendor_data.business_name}
        )
        
        return str(result.inserted_id)
    
    async def approve_vendor(self, vendor_id: str, approved_by: str, admin_id: Optional[str] = None) -> bool:
        """Approve vendor application."""
        try:
            object_id = ObjectId(vendor_id)
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
                "status": VendorStatus.ACTIVE.value,
                "approval_status": VendorApprovalStatus.APPROVED.value,
                "approved_at": datetime.utcnow(),
                "approved_by": approved_by,
                "rejection_reason": None,
                "storefront.is_active": True,
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await self.collection.update_one(query, update_doc)
        
        if result.modified_count > 0:
            # Log activity
            await self.log_vendor_activity(
                vendor_id,
                "application_approved",
                {"approved_by": approved_by}
            )
        
        return result.modified_count > 0
    
    async def reject_vendor(self, vendor_id: str, rejection_reason: str, rejected_by: str, admin_id: Optional[str] = None) -> bool:
        """Reject vendor application."""
        try:
            object_id = ObjectId(vendor_id)
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
                "status": VendorStatus.REJECTED.value,
                "approval_status": VendorApprovalStatus.REJECTED.value,
                "rejection_reason": rejection_reason,
                "approved_at": None,
                "approved_by": None,
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await self.collection.update_one(query, update_doc)
        
        if result.modified_count > 0:
            # Log activity
            await self.log_vendor_activity(
                vendor_id,
                "application_rejected",
                {
                    "rejected_by": rejected_by,
                    "reason": rejection_reason
                }
            )
        
        return result.modified_count > 0
    
    async def update_storefront_settings(self, vendor_id: str, settings: dict, admin_id: Optional[str] = None) -> bool:
        """Update vendor storefront settings."""
        try:
            object_id = ObjectId(vendor_id)
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
                "storefront": settings,
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await self.collection.update_one(query, update_doc)
        
        if result.modified_count > 0:
            # Log activity
            await self.log_vendor_activity(
                vendor_id,
                "storefront_updated",
                {"store_name": settings.get("store_name", "Unknown")}
            )
        
        return result.modified_count > 0
    
    async def add_vendor_document(self, vendor_id: str, document_url: str, document_type: str, admin_id: Optional[str] = None) -> bool:
        """Add document to vendor application."""
        try:
            object_id = ObjectId(vendor_id)
        except:
            return False
        
        query = {"_id": object_id}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        document = {
            "type": document_type,
            "url": document_url,
            "uploaded_at": datetime.utcnow()
        }
        
        update_doc = {
            "$push": {"documents": document},
            "$set": {"updated_at": datetime.utcnow()}
        }
        
        result = await self.collection.update_one(query, update_doc)
        
        if result.modified_count > 0:
            # Log activity
            await self.log_vendor_activity(
                vendor_id,
                "document_uploaded",
                {"document_type": document_type}
            )
        
        return result.modified_count > 0
    
    async def get_pending_applications(self, admin_id: Optional[str] = None) -> List[VendorResponse]:
        """Get vendors with pending approval status."""
        query = {"approval_status": VendorApprovalStatus.PENDING.value}
        
        # Apply admin isolation if admin_id provided
        if admin_id:
            query["$or"] = [
                {"managed_by": admin_id},
                {"managed_by": None}
            ]
        
        cursor = self.collection.find(query).sort("application_date", 1)
        vendors = await cursor.to_list(length=None)
        
        return [self._convert_to_response(vendor) for vendor in vendors]
    
    async def assign_vendor_to_admin(self, vendor_id: str, admin_id: str) -> bool:
        """Assign vendor to admin for management (admin isolation)."""
        try:
            object_id = ObjectId(vendor_id)
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
    
    async def log_vendor_activity(self, vendor_id: str, activity_type: str, details: Dict[str, Any]) -> None:
        """Log vendor activity."""
        activity = {
            "vendor_id": vendor_id,
            "type": activity_type,
            "details": details,
            "timestamp": datetime.utcnow()
        }
        await self.activities_collection.insert_one(activity)
    
    async def get_vendor_activities(self, vendor_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get vendor activity logs."""
        try:
            activities = await self.activities_collection.find(
                {"vendor_id": vendor_id}
            ).sort("timestamp", -1).limit(limit).to_list(limit)
            
            return activities
        except Exception:
            return []
    
    async def get_vendor_analytics(self, vendor_id: str, days: int = 30) -> Dict[str, Any]:
        """Get vendor analytics for the specified number of days."""
        try:
            object_id = ObjectId(vendor_id)
        except:
            return {}
        
        # Get vendor
        vendor = await self.collection.find_one({"_id": object_id})
        if not vendor:
            return {}
        
        # Calculate date range
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Aggregate order data
        pipeline = [
            {
                "$match": {
                    "vendor_id": vendor_id,
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_orders": {"$sum": 1},
                    "total_revenue": {"$sum": "$total"},
                    "completed_orders": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    },
                    "cancelled_orders": {
                        "$sum": {"$cond": [{"$eq": ["$status", "cancelled"]}, 1, 0]}
                    },
                    "pending_orders": {
                        "$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}
                    }
                }
            }
        ]
        
        orders_stats = await self.db.orders.aggregate(pipeline).to_list(1)
        
        if orders_stats:
            stats = orders_stats[0]
        else:
            stats = {
                "total_orders": 0,
                "total_revenue": 0,
                "completed_orders": 0,
                "cancelled_orders": 0,
                "pending_orders": 0
            }
        
        # Calculate fulfillment rate
        fulfillment_rate = 0.0
        if stats["total_orders"] > 0:
            fulfillment_rate = (stats["completed_orders"] / stats["total_orders"]) * 100
        
        return {
            "period_days": days,
            "total_orders": stats["total_orders"],
            "total_revenue": stats["total_revenue"],
            "completed_orders": stats["completed_orders"],
            "cancelled_orders": stats["cancelled_orders"],
            "pending_orders": stats["pending_orders"],
            "fulfillment_rate": fulfillment_rate,
            "average_order_value": stats["total_revenue"] / stats["total_orders"] if stats["total_orders"] > 0 else 0
        }
    
    async def delete_vendor(self, vendor_id: str, admin_id: Optional[str] = None) -> bool:
        """Soft delete vendor by setting deleted flag."""
        try:
            object_id = ObjectId(vendor_id)
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
                "deleted": True,
                "deleted_at": datetime.utcnow(),
                "status": VendorStatus.INACTIVE.value,
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await self.collection.update_one(query, update_doc)
        
        if result.modified_count > 0:
            # Log activity
            await self.log_vendor_activity(
                vendor_id,
                "vendor_deleted",
                {}
            )
        
        return result.modified_count > 0
    
    def _convert_to_response(self, vendor_doc: Dict[str, Any]) -> VendorResponse:
        """Convert MongoDB document to VendorResponse."""
        # Convert ObjectId to string and map user fields to vendor fields
        vendor_doc["id"] = str(vendor_doc["_id"])
        vendor_doc["user_id"] = str(vendor_doc["_id"])  # user_id is same as _id
        
        # Map email to contact_email if not present
        if "contact_email" not in vendor_doc and "email" in vendor_doc:
            vendor_doc["contact_email"] = vendor_doc["email"]
        
        # Map phone to contact_phone if not present
        if "contact_phone" not in vendor_doc and "phone" in vendor_doc:
            vendor_doc["contact_phone"] = vendor_doc["phone"]
        
        # Map first_name and last_name to contact_person if not present
        if "contact_person" not in vendor_doc:
            first_name = vendor_doc.get("first_name", "")
            last_name = vendor_doc.get("last_name", "")
            vendor_doc["contact_person"] = f"{first_name} {last_name}".strip() or None
        
        # Map business_status to approval_status
        if "business_status" in vendor_doc:
            business_status = vendor_doc["business_status"]
            if business_status == "approved":
                vendor_doc["approval_status"] = "approved"
            elif business_status == "rejected":
                vendor_doc["approval_status"] = "rejected"
            else:
                vendor_doc["approval_status"] = "pending"
        
        # Ensure business_type is a BusinessType enum
        if isinstance(vendor_doc.get("business_type"), str):
            try:
                vendor_doc["business_type"] = BusinessType(vendor_doc["business_type"])
            except ValueError:
                # Default to OTHER if unknown type
                vendor_doc["business_type"] = BusinessType.OTHER
        
        # Ensure status is a VendorStatus enum
        if isinstance(vendor_doc.get("status"), str):
            try:
                vendor_doc["status"] = VendorStatus(vendor_doc["status"])
            except ValueError:
                vendor_doc["status"] = VendorStatus.PENDING
        
        # Ensure approval_status is a VendorApprovalStatus enum
        if isinstance(vendor_doc.get("approval_status"), str):
            try:
                vendor_doc["approval_status"] = VendorApprovalStatus(vendor_doc["approval_status"])
            except ValueError:
                vendor_doc["approval_status"] = VendorApprovalStatus.PENDING
        
        # Handle nested objects with defaults
        if "business_address" not in vendor_doc:
            vendor_doc["business_address"] = {
                "street": "",
                "city": "",
                "state": "",
                "postal_code": "",
                "country": ""
            }
        
        if "storefront" not in vendor_doc:
            vendor_doc["storefront"] = {
                "store_name": vendor_doc.get("business_name", ""),
                "store_description": "",
                "logo": None,
                "banner": None,
                "theme_color": "#000000",
                "social_links": {},
                "business_hours": {},
                "return_policy": "",
                "shipping_policy": "",
                "is_active": vendor_doc.get("status") == "active"
            }
        
        if "performance" not in vendor_doc:
            vendor_doc["performance"] = {
                "total_sales": 0.0,
                "total_orders": 0,
                "average_rating": 0.0,
                "total_reviews": 0,
                "response_time_hours": 0.0,
                "fulfillment_rate": 0.0,
                "commission_rate": 0.05
            }
        
        if "settings" not in vendor_doc:
            vendor_doc["settings"] = {
                "auto_accept_orders": False,
                "max_processing_time_days": 7,
                "min_order_amount": 0.0,
                "free_shipping_threshold": 0.0,
                "notifications": {
                    "new_orders": True,
                    "low_inventory": True,
                    "reviews": True,
                    "payments": True
                }
            }
        
        # Ensure required datetime fields exist
        if "created_at" not in vendor_doc:
            vendor_doc["created_at"] = datetime.utcnow()
        if "updated_at" not in vendor_doc:
            vendor_doc["updated_at"] = datetime.utcnow()
        
        # Map approved_at to application_date if not exists
        if "application_date" not in vendor_doc and "created_at" in vendor_doc:
            vendor_doc["application_date"] = vendor_doc["created_at"]
        
        return VendorResponse(**vendor_doc)