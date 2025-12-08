"""Delivery Boy Repository for Database Operations"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
import logging

from ..schemas.delivery_boy import DeliveryBoyCreate, DeliveryBoyUpdate, DeliveryBoyStatus
from app.utils.security import hash_password

logger = logging.getLogger(__name__)

class DeliveryBoyRepository:
    """Repository for delivery boy operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.delivery_boys_collection

    async def create_delivery_boy(self, vendor_id: str, delivery_boy_data: DeliveryBoyCreate) -> str:
        """Create a new delivery boy"""
        try:
            delivery_boy_dict = delivery_boy_data.dict()
            
            # Hash the password before storing
            if 'password' in delivery_boy_dict:
                delivery_boy_dict['hashed_password'] = hash_password(delivery_boy_dict['password'])
                del delivery_boy_dict['password']  # Remove plain text password
            
            delivery_boy_dict.update({
                "_id": ObjectId(),
                "vendor_id": vendor_id,
                "status": DeliveryBoyStatus.ACTIVE,
                "created_at": datetime.utcnow(),
                "updated_at": None
            })

            result = await self.collection.insert_one(delivery_boy_dict)
            logger.info(f"Created delivery boy with ID: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error creating delivery boy: {str(e)}")
            raise

    async def get_delivery_boy_by_id(self, delivery_boy_id: str) -> Optional[Dict]:
        """Get delivery boy by ID"""
        try:
            if not ObjectId.is_valid(delivery_boy_id):
                return None
            
            delivery_boy = await self.collection.find_one({"_id": ObjectId(delivery_boy_id)})
            if delivery_boy:
                delivery_boy["id"] = str(delivery_boy["_id"])
            return delivery_boy

        except Exception as e:
            logger.error(f"Error fetching delivery boy: {str(e)}")
            return None

    async def get_vendor_delivery_boys(
        self, 
        vendor_id: str, 
        status: Optional[DeliveryBoyStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        """Get all delivery boys for a vendor"""
        try:
            query = {"vendor_id": vendor_id}
            if status:
                query["status"] = status

            cursor = self.collection.find(query).skip(skip).limit(limit)
            delivery_boys = []
            
            async for delivery_boy in cursor:
                delivery_boy["id"] = str(delivery_boy["_id"])
                delivery_boys.append(delivery_boy)
            
            return delivery_boys

        except Exception as e:
            logger.error(f"Error fetching vendor delivery boys: {str(e)}")
            return []

    async def update_delivery_boy(
        self, 
        delivery_boy_id: str, 
        update_data: DeliveryBoyUpdate,
        vendor_id: str = None
    ) -> bool:
        """Update delivery boy"""
        try:
            if not ObjectId.is_valid(delivery_boy_id):
                return False

            query = {"_id": ObjectId(delivery_boy_id)}
            if vendor_id:
                query["vendor_id"] = vendor_id

            update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
            
            # Hash password if being updated
            if 'password' in update_dict:
                update_dict['hashed_password'] = hash_password(update_dict['password'])
                del update_dict['password']  # Remove plain text password
                
            if update_dict:
                update_dict["updated_at"] = datetime.utcnow()
                result = await self.collection.update_one(query, {"$set": update_dict})
                return result.modified_count > 0

            return False

        except Exception as e:
            logger.error(f"Error updating delivery boy: {str(e)}")
            return False

    async def delete_delivery_boy(self, delivery_boy_id: str, vendor_id: str = None) -> bool:
        """Delete delivery boy (soft delete by setting status to inactive)"""
        try:
            if not ObjectId.is_valid(delivery_boy_id):
                return False

            query = {"_id": ObjectId(delivery_boy_id)}
            if vendor_id:
                query["vendor_id"] = vendor_id

            result = await self.collection.update_one(
                query,
                {
                    "$set": {
                        "status": DeliveryBoyStatus.INACTIVE,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error deleting delivery boy: {str(e)}")
            return False

    async def get_delivery_boys_count(self, vendor_id: str, status: Optional[DeliveryBoyStatus] = None) -> int:
        """Get count of delivery boys for a vendor"""
        try:
            query = {"vendor_id": vendor_id}
            if status:
                query["status"] = status
            
            return await self.collection.count_documents(query)

        except Exception as e:
            logger.error(f"Error counting delivery boys: {str(e)}")
            return 0

    def format_delivery_boy_response(self, delivery_boy: Dict) -> Dict:
        """Format delivery boy for API response"""
        return {
            "id": str(delivery_boy["_id"]),
            "name": delivery_boy.get("name"),
            "phone": delivery_boy.get("phone"),
            "email": delivery_boy.get("email"),
            "address": delivery_boy.get("address"),
            "zone": delivery_boy.get("zone"),
            "license_number": delivery_boy.get("license_number"),
            "vehicle_type": delivery_boy.get("vehicle_type"),
            "status": delivery_boy.get("status", DeliveryBoyStatus.ACTIVE),
            "vendor_id": delivery_boy.get("vendor_id"),
            "created_at": delivery_boy.get("created_at"),
            "updated_at": delivery_boy.get("updated_at")
        }