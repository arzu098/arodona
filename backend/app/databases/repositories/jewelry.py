"""Repository for jewelry products."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.databases.schemas.jewelry import (
    JewelryCreate,
    JewelryOut,
    JewelryCollection,
    JewelryVariant,
    JewelryInventoryUpdateBulk,
    JewelryCertification,
    JewelryCustomization
)

class JewelryRepository:
    """Repository for handling jewelry product operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["jewelry_products"]
        self.collections = db["jewelry_collections"]

    async def create_product(self, product: JewelryCreate) -> JewelryOut:
        """Create a new jewelry product."""
        product_dict = product.model_dump()
        product_dict["created_at"] = datetime.now()
        
        result = await self.collection.insert_one(product_dict)
        
        return await self.get_product(str(result.inserted_id))

    async def get_product(self, product_id: str) -> Optional[JewelryOut]:
        """Get a jewelry product by ID."""
        if not ObjectId.is_valid(product_id):
            return None
            
        product = await self.collection.find_one({"_id": ObjectId(product_id)})
        if product:
            product["product_id"] = str(product.pop("_id"))
            return JewelryOut(**product)
        return None

    async def search_products(
        self,
        metal: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        diamond_carat_min: Optional[float] = None,
        diamond_clarity: Optional[str] = None,
        sort: str = "price_desc",
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search jewelry products with filters."""
        query = {}
        if metal:
            query["attributes.metal"] = metal
        if min_price is not None:
            query["price"] = {"$gte": min_price}
        if max_price is not None:
            query.setdefault("price", {}).update({"$lte": max_price})
        if diamond_carat_min is not None:
            query["attributes.diamond_carat"] = {"$gte": str(diamond_carat_min)}
        if diamond_clarity:
            query["attributes.diamond_clarity"] = {"$in": diamond_clarity.split(",")}

        sort_direction = -1 if sort.endswith("_desc") else 1
        sort_field = sort.replace("_desc", "").replace("_asc", "")
        
        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query)
        cursor.sort(sort_field, sort_direction)
        cursor.skip(offset).limit(limit)
        
        products = []
        async for product in cursor:
            product["product_id"] = str(product.pop("_id"))
            products.append(JewelryOut(**product))
        
        return {
            "products": products,
            "total": total,
            "offset": offset,
            "limit": limit
        }

    async def create_collection(self, collection: JewelryCollection) -> Dict[str, Any]:
        """Create a new jewelry collection."""
        collection_dict = collection.model_dump()
        collection_dict["created_at"] = datetime.now()
        
        result = await self.collections.insert_one(collection_dict)
        collection_dict["collection_id"] = str(result.inserted_id)
        return collection_dict

    async def create_product_variants(self, product_id: str, variants: List[JewelryVariant]) -> Dict[str, Any]:
        """Create variants for a jewelry product."""
        if not ObjectId.is_valid(product_id):
            return None

        variant_docs = []
        for variant in variants:
            variant_dict = variant.model_dump()
            variant_dict["product_id"] = product_id
            variant_dict["created_at"] = datetime.now()
            variant_docs.append(variant_dict)

        if variant_docs:
            result = await self.collection.insert_many(variant_docs)
            return {
                "variants": [str(id) for id in result.inserted_ids],
                "count": len(result.inserted_ids)
            }
        return {"variants": [], "count": 0}

    async def update_inventory(self, product_id: str, update: JewelryInventoryUpdateBulk) -> Dict[str, Any]:
        """Update inventory for a jewelry product."""
        if not ObjectId.is_valid(product_id):
            return None

        total_quantity = 0
        stock_by_size = {}
        
        for item in update.stock_updates:
            stock_by_size[item.size] = item.quantity
            total_quantity += item.quantity

        update_data = {
            "stock_quantity": total_quantity,
            "stock_by_size": stock_by_size,
            "updated_at": datetime.now()
        }
        
        if update.low_stock_threshold is not None:
            update_data["low_stock_threshold"] = update.low_stock_threshold

        result = await self.collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            return {
                "total_stock": total_quantity,
                "stock_by_size": stock_by_size,
                "low_stock_threshold": update.low_stock_threshold
            }
        return None

    async def add_certification(self, product_id: str, cert: JewelryCertification) -> Dict[str, Any]:
        """Add certification details to a jewelry product."""
        if not ObjectId.is_valid(product_id):
            return None

        cert_dict = cert.model_dump()
        cert_dict["added_at"] = datetime.now()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "certification": cert_dict,
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.modified_count:
            return {
                "certification": cert_dict,
                "verification_url": f"https://example.com/verify/{cert.number}"
            }
        return None

    async def set_customization_options(
        self, product_id: str, options: JewelryCustomization
    ) -> Dict[str, Any]:
        """Set customization options for a jewelry product."""
        if not ObjectId.is_valid(product_id):
            return None

        options_dict = options.model_dump()
        options_dict["updated_at"] = datetime.now()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "customization": options_dict,
                    "meta.is_customizable": True,
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.modified_count:
            return options_dict
        return None

    async def bulk_create_products(self, products: List[JewelryCreate]) -> Dict[str, Any]:
        """Bulk create jewelry products."""
        product_docs = []
        for product in products:
            product_dict = product.model_dump()
            product_dict["created_at"] = datetime.now()
            product_docs.append(product_dict)

        if product_docs:
            result = await self.collection.insert_many(product_docs)
            return {
                "created": [str(id) for id in result.inserted_ids],
                "count": len(result.inserted_ids),
                "errors": []
            }
        return {"created": [], "count": 0, "errors": []}