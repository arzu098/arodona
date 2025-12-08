"""Request for Quotation (RFQ) repository."""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from bson import ObjectId

class RFQRepository:
    def __init__(self, db):
        self.db = db
        self.rfqs_collection = db["rfqs"]
        self.quotes_collection = db["quotes"]

    async def create_rfq(self, rfq_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new RFQ."""
        now = datetime.utcnow()
        rfq_data.update({
            "created_at": now,
            "updated_at": now,
            "status": "draft",
            "total_quotes": 0,
            "awarded_quote_id": None
        })
        await self.rfqs_collection.insert_one(rfq_data)
        return rfq_data

    async def get_rfq(self, rfq_id: str) -> Optional[Dict[str, Any]]:
        """Get RFQ by ID."""
        return await self.rfqs_collection.find_one({"_id": ObjectId(rfq_id)})

    async def list_rfqs(
        self,
        skip: int = 0,
        limit: int = 50,
        buyer_id: Optional[str] = None,
        status: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List RFQs with filters."""
        query = {}
        if buyer_id:
            query["buyer_id"] = buyer_id
        if status:
            query["status"] = status
        if category_id:
            query["category_ids"] = category_id

        cursor = self.rfqs_collection.find(query)
        total = await cursor.count()
        rfqs = await cursor.sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        return rfqs, total

    async def update_rfq(
        self,
        rfq_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update RFQ."""
        data["updated_at"] = datetime.utcnow()
        await self.rfqs_collection.update_one(
            {"_id": ObjectId(rfq_id)},
            {"$set": data}
        )
        return await self.get_rfq(rfq_id)

    async def publish_rfq(self, rfq_id: str) -> Optional[Dict[str, Any]]:
        """Publish RFQ."""
        return await self.update_rfq(rfq_id, {"status": "published"})

    async def close_rfq(self, rfq_id: str) -> Optional[Dict[str, Any]]:
        """Close RFQ."""
        return await self.update_rfq(rfq_id, {"status": "closed"})

    async def cancel_rfq(self, rfq_id: str) -> Optional[Dict[str, Any]]:
        """Cancel RFQ."""
        return await self.update_rfq(rfq_id, {"status": "cancelled"})

    async def create_quote(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new quote for RFQ."""
        now = datetime.utcnow()
        quote_data.update({
            "created_at": now,
            "updated_at": now,
            "status": "draft"
        })
        
        # Increment RFQ quote count
        await self.rfqs_collection.update_one(
            {"_id": ObjectId(quote_data["rfq_id"])},
            {"$inc": {"total_quotes": 1}}
        )
        
        await self.quotes_collection.insert_one(quote_data)
        return quote_data

    async def get_quote(self, quote_id: str) -> Optional[Dict[str, Any]]:
        """Get quote by ID."""
        return await self.quotes_collection.find_one({"_id": ObjectId(quote_id)})

    async def list_quotes(
        self,
        skip: int = 0,
        limit: int = 50,
        rfq_id: Optional[str] = None,
        vendor_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List quotes with filters."""
        query = {}
        if rfq_id:
            query["rfq_id"] = rfq_id
        if vendor_id:
            query["vendor_id"] = vendor_id
        if status:
            query["status"] = status

        cursor = self.quotes_collection.find(query)
        total = await cursor.count()
        quotes = await cursor.sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        return quotes, total

    async def update_quote(
        self,
        quote_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update quote."""
        data["updated_at"] = datetime.utcnow()
        await self.quotes_collection.update_one(
            {"_id": ObjectId(quote_id)},
            {"$set": data}
        )
        return await self.get_quote(quote_id)

    async def submit_quote(self, quote_id: str) -> Optional[Dict[str, Any]]:
        """Submit quote."""
        return await self.update_quote(quote_id, {"status": "submitted"})

    async def award_quote(
        self,
        rfq_id: str,
        quote_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Award quote and update RFQ."""
        # Update quote status
        quote = await self.update_quote(quote_id, {"status": "accepted"})
        
        # Update RFQ
        rfq = await self.update_rfq(rfq_id, {
            "status": "awarded",
            "awarded_quote_id": quote_id
        })
        
        # Reject other quotes
        await self.quotes_collection.update_many(
            {
                "rfq_id": rfq_id,
                "_id": {"$ne": ObjectId(quote_id)}
            },
            {"$set": {"status": "rejected"}}
        )
        
        return rfq, quote

    async def reject_quote(self, quote_id: str) -> Optional[Dict[str, Any]]:
        """Reject quote."""
        return await self.update_quote(quote_id, {"status": "rejected"})

    async def withdraw_quote(self, quote_id: str) -> Optional[Dict[str, Any]]:
        """Withdraw quote."""
        return await self.update_quote(quote_id, {"status": "withdrawn"})

    async def create_indexes(self):
        """Create necessary indexes."""
        await self.rfqs_collection.create_index([("created_at", -1)])
        await self.rfqs_collection.create_index("buyer_id")
        await self.rfqs_collection.create_index("status")
        await self.rfqs_collection.create_index("category_ids")
        await self.quotes_collection.create_index([("created_at", -1)])
        await self.quotes_collection.create_index("rfq_id")
        await self.quotes_collection.create_index("vendor_id")
        await self.quotes_collection.create_index("status")