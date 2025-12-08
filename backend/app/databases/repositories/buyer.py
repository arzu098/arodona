from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from app.databases.schemas.buyer import (
    BuyerType,
    BuyerVerificationStatus,
    BuyerResponse,
    BuyerPreferences,
    BuyerBusiness,
    BuyerCreditStatus
)

class BuyerRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["buyers"]

    def format_buyer_response(self, buyer: Dict) -> BuyerResponse:
        """Format buyer document to BuyerResponse schema"""
        return BuyerResponse(
            id=str(buyer["_id"]),
            user_id=buyer["user_id"],
            type=BuyerType(buyer["type"]),
            business=BuyerBusiness(**buyer["business"]) if buyer.get("business") else None,
            verification_status=BuyerVerificationStatus(buyer["verification_status"]) if buyer.get("verification_status") else None,
            preferences=BuyerPreferences(**buyer["preferences"]),
            credit_status=BuyerCreditStatus(**buyer["credit_status"]) if buyer.get("credit_status") else None,
            total_orders=buyer.get("total_orders", 0),
            total_spent=buyer.get("total_spent", 0.0),
            created_at=buyer["created_at"],
            updated_at=buyer["updated_at"]
        )

    async def create_buyer(self, user_id: str, data: dict) -> dict:
        """Create a new buyer"""
        buyer_data = {
            "user_id": user_id,
            "type": data["type"],
            "business": data.get("business"),
            "preferences": data.get("preferences", BuyerPreferences().dict()),
            "verification_status": BuyerVerificationStatus.PENDING.value if data.get("business") else None,
            "total_orders": 0,
            "total_spent": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.insert_one(buyer_data)
        buyer_data["_id"] = result.inserted_id
        return buyer_data

    async def get_buyer(self, buyer_id: str) -> Optional[dict]:
        """Get buyer by ID"""
        buyer = await self.collection.find_one({"_id": ObjectId(buyer_id)})
        return buyer

    async def get_buyer_by_user(self, user_id: str) -> Optional[dict]:
        """Get buyer by user ID"""
        buyer = await self.collection.find_one({"user_id": user_id})
        return buyer

    async def update_buyer(self, buyer_id: str, data: dict) -> Optional[dict]:
        """Update buyer"""
        update_data = {k: v for k, v in data.items() if v is not None}
        if "business" in update_data:
            update_data["business"] = update_data["business"].dict()
        if "preferences" in update_data:
            update_data["preferences"] = update_data["preferences"].dict()
            
        update_data["updated_at"] = datetime.utcnow()
        
        buyer = await self.collection.find_one_and_update(
            {"_id": ObjectId(buyer_id)},
            {"$set": update_data},
            return_document=True
        )
        return buyer

    async def verify_buyer(self, buyer_id: str, status: BuyerVerificationStatus, notes: Optional[str] = None) -> Optional[dict]:
        """Update buyer verification status"""
        update_data = {
            "verification_status": status.value,
            "verification_notes": notes,
            "updated_at": datetime.utcnow()
        }
        
        buyer = await self.collection.find_one_and_update(
            {"_id": ObjectId(buyer_id)},
            {"$set": update_data},
            return_document=True
        )
        return buyer

    async def update_buyer_credit(self, buyer_id: str, credit_data: dict) -> bool:
        """Update buyer credit information"""
        update_data = {
            "credit_status": credit_data,
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {"_id": ObjectId(buyer_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def get_buyers(self, 
                        skip: int = 0, 
                        limit: int = 10,
                        type: Optional[BuyerType] = None,
                        verification_status: Optional[BuyerVerificationStatus] = None,
                        search: Optional[str] = None) -> Tuple[List[dict], int]:
        """Get buyers with filters and pagination"""
        filter_query = {}
        
        if type:
            filter_query["type"] = type.value
            
        if verification_status:
            filter_query["verification_status"] = verification_status.value
            
        if search:
            filter_query["$or"] = [
                {"business.company_name": {"$regex": search, "$options": "i"}}
            ]
            
        total = await self.collection.count_documents(filter_query)
        cursor = self.collection.find(filter_query)
        cursor.skip(skip).limit(limit)
        buyers = await cursor.to_list(limit)
        
        return buyers, total

    async def update_buyer_stats(self, buyer_id: str, order_amount: float) -> bool:
        """Update buyer order statistics"""
        result = await self.collection.update_one(
            {"_id": ObjectId(buyer_id)},
            {
                "$inc": {
                    "total_orders": 1,
                    "total_spent": order_amount
                },
                "$set": {
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0