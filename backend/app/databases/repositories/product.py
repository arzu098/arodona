from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from app.databases.schemas.product import (
    ProductResponse, ProductCreate, ProductUpdate, ProductStatus,
    JewelryType, MetalType, GemstoneType, ProductCondition
)
import asyncio
from collections import defaultdict

class ProductRepository:
    """Enhanced repository for jewelry product management"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["products"]
        self.categories_collection = db["categories"]
        self.vendors_collection = db["vendors"]
        self.analytics_collection = db["product_analytics"]

    async def create_product(self, vendor_id: str, product_data: ProductCreate) -> Dict[str, Any]:
        """Create a comprehensive jewelry product"""
        now = datetime.utcnow()
        
        # Generate SKU if not provided
        if not product_data.sku:
            product_data.sku = await self._generate_sku(vendor_id, product_data.jewelry_type, product_data.metal_type)
        
        # Validate SKU uniqueness
        existing_product = await self.collection.find_one({"sku": product_data.sku, "vendor_id": vendor_id})
        if existing_product:
            raise ValueError(f"SKU {product_data.sku} already exists for this vendor")
        
        # Generate SEO slug if not provided
        if not (product_data.seo and product_data.seo.slug):
            slug = await self._generate_slug(product_data.name, vendor_id)
            if not product_data.seo:
                product_data.seo = {}
            product_data.seo.slug = slug
        
        # Prepare product document
        product_doc = {
            "vendor_id": vendor_id,
            "name": product_data.name,
            "description": product_data.description,
            "short_description": product_data.short_description,
            "price": float(product_data.price),
            "compare_at_price": float(product_data.compare_at_price) if product_data.compare_at_price else None,
            "cost_price": float(product_data.cost_price) if product_data.cost_price else None,
            
            # Jewelry-specific attributes
            "jewelry_type": product_data.jewelry_type.value,
            "metal_type": product_data.metal_type.value,
            "metal_purity": product_data.metal_purity,
            "gemstones": [gemstone.dict() for gemstone in (product_data.gemstones or [])],
            
            # Physical attributes
            "dimensions": product_data.dimensions.dict() if product_data.dimensions else None,
            "weight": product_data.weight.dict() if product_data.weight else None,
            
            # Variations
            "sizes": [size.dict() for size in (product_data.sizes or [])],
            "variants": [variant.dict() for variant in (product_data.variants or [])],
            
            # Inventory
            "sku": product_data.sku,
            "stock_quantity": product_data.stock_quantity,
            "low_stock_threshold": product_data.low_stock_threshold,
            "track_inventory": product_data.track_inventory,
            "is_in_stock": product_data.stock_quantity > 0 if product_data.track_inventory else True,
            
            # Categorization
            "categories": product_data.categories or [],
            "tags": product_data.tags or [],
            "brand": product_data.brand,
            "collection": product_data.collection,
            
            # Status
            "status": product_data.status.value,
            "condition": product_data.condition.value,
            
            # Media
            "images": [img.dict() for img in (product_data.images or [])],
            
            # SEO
            "seo": product_data.seo.dict() if product_data.seo else None,
            "featured": product_data.featured,
            
            # Additional attributes
            "care_instructions": product_data.care_instructions,
            "materials": product_data.materials or [],
            "origin_country": product_data.origin_country,
            "warranty_info": product_data.warranty_info,
            "custom_attributes": product_data.custom_attributes or {},
            
            # Analytics and engagement
            "view_count": 0,
            "favorite_count": 0,
            "purchase_count": 0,
            
            # Ratings (initialized)
            "rating_avg": 0.0,
            "rating_count": 0,
            "ratings_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            
            # Timestamps
            "created_at": now,
            "updated_at": now,
            "last_viewed_at": None,
            
            # Search optimization
            "search_keywords": await self._generate_search_keywords(product_data),
        }
        
        # Insert product
        result = await self.collection.insert_one(product_doc)
        product_doc["_id"] = result.inserted_id
        
        # Update vendor product count
        await self.vendors_collection.update_one(
            {"_id": ObjectId(vendor_id)},
            {"$inc": {"statistics.total_products": 1}}
        )
        
        # Track analytics
        await self._track_product_event(str(result.inserted_id), vendor_id, "product_created")
        
        return product_doc

    async def _generate_sku(self, vendor_id: str, jewelry_type: JewelryType, metal_type: MetalType) -> str:
        """Generate unique SKU for product"""
        # Get vendor prefix (first 3 characters of vendor ID)
        vendor_prefix = vendor_id[:3].upper()
        
        # Get jewelry type code
        jewelry_code = jewelry_type.value[:3].upper()
        
        # Get metal type code
        metal_code = metal_type.value[:3].upper()
        
        # Get sequential number for this vendor
        count = await self.collection.count_documents({"vendor_id": vendor_id}) + 1
        
        return f"{vendor_prefix}-{jewelry_code}-{metal_code}-{count:04d}"
    
    async def _generate_slug(self, name: str, vendor_id: str) -> str:
        """Generate SEO-friendly slug"""
        import re
        
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        
        # Check for uniqueness
        count = 1
        original_slug = slug
        while await self.collection.find_one({"vendor_id": vendor_id, "seo.slug": slug}):
            slug = f"{original_slug}-{count}"
            count += 1
        
        return slug
    
    async def _generate_search_keywords(self, product_data: ProductCreate) -> List[str]:
        """Generate search keywords from product attributes"""
        keywords = set()
        
        # Add basic info
        keywords.update(product_data.name.lower().split())
        keywords.update(product_data.description.lower().split())
        
        # Add jewelry attributes
        keywords.add(product_data.jewelry_type.value)
        keywords.add(product_data.metal_type.value)
        
        if product_data.metal_purity:
            keywords.add(product_data.metal_purity.lower())
        
        # Add gemstone keywords
        if product_data.gemstones:
            for gemstone in product_data.gemstones:
                keywords.add(gemstone.type.value)
                if gemstone.cut:
                    keywords.add(gemstone.cut.value)
        
        # Add tags and brand
        if product_data.tags:
            keywords.update([tag.lower() for tag in product_data.tags])
        
        if product_data.brand:
            keywords.update(product_data.brand.lower().split())
        
        # Filter out common stop words and short words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'a', 'an'}
        filtered_keywords = [kw for kw in keywords if len(kw) > 2 and kw not in stop_words]
        
        return filtered_keywords
    
    async def _track_product_event(self, product_id: str, vendor_id: str, event_type: str, metadata: Dict = None):
        """Track product-related events for analytics"""
        event_doc = {
            "product_id": product_id,
            "vendor_id": vendor_id,
            "event_type": event_type,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        }
        
        try:
            await self.analytics_collection.insert_one(event_doc)
        except Exception:
            pass  # Don't fail product operations due to analytics issues

    async def get_product_by_id(self, product_id: str, increment_views: bool = False, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get product by MongoDB ID with optional view tracking"""
        try:
            product = await self.collection.find_one({
                "_id": ObjectId(product_id),
                "deleted": {"$ne": True}
            })
            
            if product and increment_views:
                # Increment view count
                await self.collection.update_one(
                    {"_id": ObjectId(product_id)},
                    {
                        "$inc": {"view_count": 1},
                        "$set": {"last_viewed_at": datetime.utcnow()}
                    }
                )
                product["view_count"] = product.get("view_count", 0) + 1
                
                # Track analytics
                await self._track_product_event(
                    product_id, 
                    product["vendor_id"], 
                    "product_viewed",
                    {"user_id": user_id} if user_id else None
                )
            
            return product
        except Exception:
            return None
    
    async def get_product_by_sku(self, sku: str, vendor_id: str = None) -> Optional[Dict[str, Any]]:
        """Get product by SKU"""
        try:
            query = {"sku": sku}
            if vendor_id:
                query["vendor_id"] = vendor_id
            
            product = await self.collection.find_one(query)
            return product
        except Exception:
            return None

    async def get_products(
        self,
        skip: int = 0,
        limit: int = 20,
        vendor_id: Optional[str] = None,
        status: Optional[ProductStatus] = None,
        jewelry_type: Optional[JewelryType] = None,
        metal_type: Optional[MetalType] = None,
        categories: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        featured_only: bool = False,
        in_stock_only: bool = False,
        sort_by: str = "created_at",
        sort_order: int = -1,
        search_query: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get products with comprehensive filtering and sorting"""
        
        # Build filter query
        filter_query = {
            "deleted": {"$ne": True}  # Always exclude deleted products
        }
        
        if vendor_id:
            filter_query["vendor_id"] = vendor_id
        
        if status:
            filter_query["status"] = status.value
        else:
            # Default to active products for public queries
            if not vendor_id:  # Public listing
                filter_query["status"] = ProductStatus.ACTIVE.value
        
        if jewelry_type:
            filter_query["jewelry_type"] = jewelry_type.value
        
        if metal_type:
            filter_query["metal_type"] = metal_type.value
        
        if categories:
            # Support both singular 'category' field and plural 'categories' array
            filter_query["$or"] = [
                {"category": {"$in": categories}},
                {"categories": {"$in": categories}}
            ]
        
        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            filter_query["price"] = price_filter
        
        if featured_only:
            filter_query["featured"] = True
        
        if in_stock_only:
            # Use $and to combine with existing $or filters (like category filter)
            stock_filter = {
                "$or": [
                    {"track_inventory": False},
                    {"$and": [{"track_inventory": True}, {"stock_quantity": {"$gt": 0}}]}
                ]
            }
            
            # If there's already an $or filter (e.g., for categories), wrap both in $and
            if "$or" in filter_query:
                existing_or = filter_query.pop("$or")
                filter_query["$and"] = [
                    {"$or": existing_or},
                    stock_filter
                ]
            else:
                filter_query.update(stock_filter)
        
        if search_query:
            filter_query["$or"] = [
                {"name": {"$regex": search_query, "$options": "i"}},
                {"description": {"$regex": search_query, "$options": "i"}},
                {"search_keywords": {"$in": [search_query.lower()]}},
                {"tags": {"$in": [search_query.lower()]}},
                {"brand": {"$regex": search_query, "$options": "i"}}
            ]
        
        # Get total count
        total = await self.collection.count_documents(filter_query)
        
        # Build sort options
        sort_options = [(sort_by, sort_order)]
        
        # Get products
        products = await self.collection.find(filter_query).sort(sort_options).skip(skip).limit(limit).to_list(limit)
        
        return products, total
    
    async def get_featured_products(self, limit: int = 10, jewelry_type: Optional[JewelryType] = None) -> List[Dict[str, Any]]:
        """Get featured products"""
        filter_query = {
            "status": ProductStatus.ACTIVE.value,
            "featured": True
        }
        
        if jewelry_type:
            filter_query["jewelry_type"] = jewelry_type.value
        
        products = await self.collection.find(filter_query).sort([("rating_avg", -1), ("created_at", -1)]).limit(limit).to_list(limit)
        return products
    
    async def get_trending_products(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending products based on recent views and purchases"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Aggregate products by recent activity
        pipeline = [
            {
                "$match": {
                    "status": ProductStatus.ACTIVE.value,
                    "$or": [
                        {"last_viewed_at": {"$gte": since_date}},
                        {"updated_at": {"$gte": since_date}}
                    ]
                }
            },
            {
                "$addFields": {
                    "trending_score": {
                        "$add": [
                            {"$multiply": ["$view_count", 1]},
                            {"$multiply": ["$purchase_count", 5]},
                            {"$multiply": ["$favorite_count", 2]},
                            {"$multiply": ["$rating_avg", 3]}
                        ]
                    }
                }
            },
            {"$sort": {"trending_score": -1}},
            {"$limit": limit}
        ]
        
        products = await self.collection.aggregate(pipeline).to_list(limit)
        return products

    async def get_products_by_category(self, category: str, skip: int = 0, limit: int = 10) -> tuple:
        """Get products filtered by category"""
        total = await self.collection.count_documents({"category": category})
        products = await self.collection.find({"category": category}).skip(skip).limit(limit).to_list(limit)
        return products, total

    async def update_product(self, product_id: str, vendor_id: str, update_data: ProductUpdate) -> Optional[Dict[str, Any]]:
        """Update product with comprehensive validation"""
        try:
            # Verify ownership
            existing_product = await self.collection.find_one({
                "_id": ObjectId(product_id),
                "vendor_id": vendor_id
            })
            
            if not existing_product:
                return None
            
            # Build update document
            update_doc = {}
            
            # Basic fields
            if update_data.name is not None:
                update_doc["name"] = update_data.name
                # Regenerate search keywords if name changes
                update_doc["search_keywords"] = await self._generate_search_keywords_from_existing(existing_product, update_data)
            
            if update_data.description is not None:
                update_doc["description"] = update_data.description
            
            if update_data.short_description is not None:
                update_doc["short_description"] = update_data.short_description
            
            if update_data.price is not None:
                update_doc["price"] = float(update_data.price)
            
            if update_data.compare_at_price is not None:
                update_doc["compare_at_price"] = float(update_data.compare_at_price)
            
            if update_data.cost_price is not None:
                update_doc["cost_price"] = float(update_data.cost_price)
            
            # Jewelry-specific attributes
            if update_data.jewelry_type is not None:
                update_doc["jewelry_type"] = update_data.jewelry_type.value
            
            if update_data.metal_type is not None:
                update_doc["metal_type"] = update_data.metal_type.value
            
            if update_data.metal_purity is not None:
                update_doc["metal_purity"] = update_data.metal_purity
            
            if update_data.gemstones is not None:
                update_doc["gemstones"] = [gemstone.dict() for gemstone in update_data.gemstones]
            
            # Physical attributes
            if update_data.dimensions is not None:
                update_doc["dimensions"] = update_data.dimensions.dict()
            
            if update_data.weight is not None:
                update_doc["weight"] = update_data.weight.dict()
            
            # Variations
            if update_data.sizes is not None:
                update_doc["sizes"] = [size.dict() for size in update_data.sizes]
            
            if update_data.variants is not None:
                update_doc["variants"] = [variant.dict() for variant in update_data.variants]
            
            # Inventory
            if update_data.sku is not None:
                # Check SKU uniqueness
                existing_sku = await self.collection.find_one({
                    "sku": update_data.sku,
                    "vendor_id": vendor_id,
                    "_id": {"$ne": ObjectId(product_id)}
                })
                if existing_sku:
                    raise ValueError(f"SKU {update_data.sku} already exists for this vendor")
                update_doc["sku"] = update_data.sku
            
            if update_data.stock_quantity is not None:
                update_doc["stock_quantity"] = update_data.stock_quantity
                if update_data.track_inventory != False:  # Default to tracking if not explicitly disabled
                    update_doc["is_in_stock"] = update_data.stock_quantity > 0
            
            if update_data.low_stock_threshold is not None:
                update_doc["low_stock_threshold"] = update_data.low_stock_threshold
            
            if update_data.track_inventory is not None:
                update_doc["track_inventory"] = update_data.track_inventory
                # Update stock status if tracking changes
                if not update_data.track_inventory:
                    update_doc["is_in_stock"] = True
                elif update_data.stock_quantity is not None:
                    update_doc["is_in_stock"] = update_data.stock_quantity > 0
            
            # Categorization
            if update_data.categories is not None:
                update_doc["categories"] = update_data.categories
            
            if update_data.tags is not None:
                update_doc["tags"] = update_data.tags
            
            if update_data.brand is not None:
                update_doc["brand"] = update_data.brand
            
            if update_data.collection is not None:
                update_doc["collection"] = update_data.collection
            
            # Status
            if update_data.status is not None:
                update_doc["status"] = update_data.status.value
            
            if update_data.condition is not None:
                update_doc["condition"] = update_data.condition.value
            
            # Media
            if update_data.images is not None:
                update_doc["images"] = [img.dict() for img in update_data.images]
            
            # SEO
            if update_data.seo is not None:
                update_doc["seo"] = update_data.seo.dict()
            
            if update_data.featured is not None:
                update_doc["featured"] = update_data.featured
            
            # Additional attributes
            if update_data.care_instructions is not None:
                update_doc["care_instructions"] = update_data.care_instructions
            
            if update_data.materials is not None:
                update_doc["materials"] = update_data.materials
            
            if update_data.origin_country is not None:
                update_doc["origin_country"] = update_data.origin_country
            
            if update_data.warranty_info is not None:
                update_doc["warranty_info"] = update_data.warranty_info
            
            if update_data.custom_attributes is not None:
                update_doc["custom_attributes"] = update_data.custom_attributes
            
            # Always update timestamp
            update_doc["updated_at"] = datetime.utcnow()
            
            if not update_doc:
                return existing_product
            
            # Perform update
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(product_id), "vendor_id": vendor_id},
                {"$set": update_doc},
                return_document=True
            )
            
            if result:
                await self._track_product_event(product_id, vendor_id, "product_updated", update_doc)
            
            return result
            
        except Exception as e:
            raise e
    
    async def _generate_search_keywords_from_existing(self, existing_product: Dict, update_data: ProductUpdate) -> List[str]:
        """Generate search keywords from updated product data"""
        # Combine existing and new data
        name = update_data.name if update_data.name is not None else existing_product.get("name", "")
        description = update_data.description if update_data.description is not None else existing_product.get("description", "")
        jewelry_type = update_data.jewelry_type if update_data.jewelry_type is not None else JewelryType(existing_product.get("jewelry_type", "other"))
        metal_type = update_data.metal_type if update_data.metal_type is not None else MetalType(existing_product.get("metal_type", "other"))
        
        keywords = set()
        
        # Add basic info
        keywords.update(name.lower().split())
        keywords.update(description.lower().split())
        
        # Add jewelry attributes
        keywords.add(jewelry_type.value)
        keywords.add(metal_type.value)
        
        # Add tags and brand
        tags = update_data.tags if update_data.tags is not None else existing_product.get("tags", [])
        keywords.update([tag.lower() for tag in tags])
        
        brand = update_data.brand if update_data.brand is not None else existing_product.get("brand")
        if brand:
            keywords.update(brand.lower().split())
        
        # Filter keywords
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'a', 'an'}
        filtered_keywords = [kw for kw in keywords if len(kw) > 2 and kw not in stop_words]
        
        return filtered_keywords
    
    async def update_inventory(self, product_id: str, vendor_id: str, stock_quantity: int, size: str = None, variant_id: str = None) -> Optional[Dict[str, Any]]:
        """Update product inventory for specific size/variant or overall stock"""
        try:
            if size or variant_id:
                # Update specific variation inventory
                if size:
                    result = await self.collection.find_one_and_update(
                        {
                            "_id": ObjectId(product_id),
                            "vendor_id": vendor_id,
                            "sizes.size": size
                        },
                        {
                            "$set": {
                                "sizes.$.stock_quantity": stock_quantity,
                                "sizes.$.is_available": stock_quantity > 0,
                                "updated_at": datetime.utcnow()
                            }
                        },
                        return_document=True
                    )
                elif variant_id:
                    result = await self.collection.find_one_and_update(
                        {
                            "_id": ObjectId(product_id),
                            "vendor_id": vendor_id,
                            "variants.sku": variant_id
                        },
                        {
                            "$set": {
                                "variants.$.stock_quantity": stock_quantity,
                                "updated_at": datetime.utcnow()
                            }
                        },
                        return_document=True
                    )
            else:
                # Update overall inventory
                result = await self.collection.find_one_and_update(
                    {"_id": ObjectId(product_id), "vendor_id": vendor_id},
                    {
                        "$set": {
                            "stock_quantity": stock_quantity,
                            "is_in_stock": stock_quantity > 0,
                            "updated_at": datetime.utcnow()
                        }
                    },
                    return_document=True
                )
            
            if result:
                await self._track_product_event(product_id, vendor_id, "inventory_updated", {
                    "stock_quantity": stock_quantity,
                    "size": size,
                    "variant_id": variant_id
                })
            
            return result
            
        except Exception:
            return None

    async def add_images_to_product(self, product_id: str, image_paths: List[str]) -> Optional[dict]:
        """Add images to an existing product"""
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(product_id)},
                {
                    "$push": {"images": {"$each": image_paths}},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                return_document=True
            )
            return result
        except Exception:
            return None

    async def delete_product(self, product_id: str) -> bool:
        """Delete product from database"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(product_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    def format_product_response(self, product: Dict[str, Any], include_vendor_info: bool = False) -> ProductResponse:
        """Format product document to comprehensive ProductResponse schema"""
        from app.databases.schemas.product import (
            ProductImage, ProductDimensions, ProductWeight, SizeVariation, 
            ProductVariant, GemstoneInfo, SEOInfo, CategoryInfo
        )
        
        # Format images
        images = None
        if product.get("images"):
            try:
                print(f"[format_product_response] Formatting {len(product['images'])} images")
                print(f"[format_product_response] Raw images: {product['images']}")
                
                # Fix image URLs - convert backslashes to forward slashes
                formatted_images = []
                for img in product["images"]:
                    img_data = img.copy()
                    # Fix URL paths - replace backslashes with forward slashes
                    if img_data.get("url"):
                        original_url = img_data["url"]
                        img_data["url"] = img_data["url"].replace("\\", "/")
                        if original_url != img_data["url"]:
                            print(f"[format_product_response] Fixed URL: {original_url} -> {img_data['url']}")
                    if img_data.get("thumbnail_url"):
                        img_data["thumbnail_url"] = img_data["thumbnail_url"].replace("\\", "/")
                    formatted_images.append(ProductImage(**img_data))
                
                images = formatted_images
                if images:
                    print(f"[format_product_response] Formatted {len(images)} images, first URL: {images[0].url}")
            except Exception as e:
                print(f"[format_product_response] Error formatting images: {e}")
                import traceback
                traceback.print_exc()
                images = None
        
        # Format dimensions - handle both dict and string formats
        dimensions = None
        if product.get("dimensions"):
            dim_data = product["dimensions"]
            if isinstance(dim_data, dict):
                dimensions = ProductDimensions(**dim_data)
            # If it's a string, leave as None (simple products store dimensions as strings)
        
        # Format weight - handle both dict and number formats
        weight = None
        if product.get("weight"):
            weight_data = product["weight"]
            if isinstance(weight_data, dict):
                weight = ProductWeight(**weight_data)
            # If it's a number, leave as None (simple products store weight as numbers)
        
        # Format sizes
        sizes = None
        if product.get("sizes"):
            sizes = [SizeVariation(**size) for size in product["sizes"]]
        
        # Format variants
        variants = None
        if product.get("variants"):
            variants = [ProductVariant(**variant) for variant in product["variants"]]
        
        # Format gemstones
        gemstones = None
        if product.get("gemstones"):
            gemstones = [GemstoneInfo(**gem) for gem in product["gemstones"]]
        
        # Format SEO
        seo = None
        if product.get("seo"):
            seo = SEOInfo(**product["seo"])
        
        # Format categories (would need category lookup for full info)
        categories = None
        if product.get("categories"):
            # For now, just return category IDs - in a full implementation,
            # you'd look up category details from categories collection
            categories = [
                CategoryInfo(id=cat, name=cat, slug=cat) 
                for cat in product["categories"]
            ]
        
        # Handle jewelry_type - use category as fallback or default to 'other'
        jewelry_type_value = product.get("jewelry_type") or product.get("category") or "other"
        try:
            jewelry_type = JewelryType(jewelry_type_value)
        except (ValueError, KeyError):
            jewelry_type = JewelryType.OTHER
        
        # Handle metal_type - default to None for optional field
        metal_type = None
        if product.get("metal_type"):
            try:
                metal_type = MetalType(product["metal_type"])
            except (ValueError, KeyError):
                metal_type = None
        
        response = ProductResponse(
            id=str(product["_id"]),
            vendor_id=product["vendor_id"],
            name=product["name"],
            description=product["description"],
            short_description=product.get("short_description"),
            price=product["price"],
            compare_at_price=product.get("compare_at_price"),
            cost_price=product.get("cost_price") if include_vendor_info else None,
            
            # Jewelry-specific
            jewelry_type=jewelry_type,
            metal_type=metal_type,
            metal_purity=product.get("metal_purity"),
            gemstones=gemstones,
            
            # Physical attributes
            dimensions=dimensions,
            weight=weight,
            
            # Variations
            sizes=sizes,
            variants=variants,
            
            # Inventory
            sku=product.get("sku"),
            stock_quantity=product.get("stock_quantity", product.get("stock", 0)),
            stock=product.get("stock_quantity", product.get("stock", 0)),  # Backward compatibility
            low_stock_threshold=product.get("low_stock_threshold"),
            track_inventory=product.get("track_inventory", True),
            is_in_stock=product.get("is_in_stock", True),
            is_active=product.get("is_active", product.get("status") == "active"),  # Backward compatibility
            
            # Categorization
            category=product.get("category"),  # Primary category (string)
            categories=categories,
            tags=product.get("tags", []),
            brand=product.get("brand"),
            collection=product.get("collection"),
            
            # Status
            status=ProductStatus(product.get("status", "draft")),
            condition=ProductCondition(product.get("condition", "new")),
            
            # Media
            images=images,
            
            # SEO
            seo=seo,
            featured=product.get("featured", False),
            
            # Ratings
            rating_avg=product.get("rating_avg", 0.0),
            rating_count=product.get("rating_count", 0),
            ratings_breakdown=product.get("ratings_breakdown", {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}),
            
            # Additional
            care_instructions=product.get("care_instructions"),
            materials=product.get("materials", []),
            origin_country=product.get("origin_country"),
            warranty_info=product.get("warranty_info"),
            custom_attributes=product.get("custom_attributes", {}),
            
            # Analytics
            view_count=product.get("view_count", 0),
            favorite_count=product.get("favorite_count", 0),
            
            # Timestamps
            created_at=product.get("created_at", datetime.utcnow()),
            updated_at=product.get("updated_at", datetime.utcnow()),
            
            # Backward compatibility
            original_price=product.get("compare_at_price")  # Backward compatibility
        )
        
        # Debug: Check if images are in the response
        print(f"[format_product_response] ProductResponse created with {len(response.images) if response.images else 0} images")
        if response.images:
            print(f"[format_product_response] First image URL: {response.images[0].url}")
        
        return response
    
    async def delete_product(self, product_id: str, vendor_id: str) -> bool:
        """Soft delete product (update status to discontinued)"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(product_id), "vendor_id": vendor_id},
                {
                    "$set": {
                        "status": ProductStatus.DISCONTINUED.value,
                        "deleted": True,
                        "deleted_at": datetime.utcnow(),
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Update vendor product count
                await self.vendors_collection.update_one(
                    {"_id": ObjectId(vendor_id)},
                    {"$inc": {"statistics.total_products": -1}}
                )
                
                await self._track_product_event(product_id, vendor_id, "product_deleted")
                return True
                
            return False
        except Exception:
            return False
    
    async def get_vendor_products(self, vendor_id: str, skip: int = 0, limit: int = 20, status: Optional[ProductStatus] = None) -> Tuple[List[Dict[str, Any]], int]:
        """Get products for a specific vendor"""
        filter_query = {
            "vendor_id": vendor_id,
            "deleted": {"$ne": True}  # Exclude deleted products
        }
        
        if status:
            filter_query["status"] = status.value
        
        total = await self.collection.count_documents(filter_query)
        products = await self.collection.find(filter_query).sort([("created_at", -1)]).skip(skip).limit(limit).to_list(limit)
        
        return products, total
    
    async def get_low_stock_products(self, vendor_id: str = None) -> List[Dict[str, Any]]:
        """Get products with low stock levels"""
        filter_query = {
            "track_inventory": True,
            "$expr": {"$lte": ["$stock_quantity", "$low_stock_threshold"]}
        }
        
        if vendor_id:
            filter_query["vendor_id"] = vendor_id
        
        products = await self.collection.find(filter_query).to_list(None)
        return products

    async def search_products(self, query: str, category: Optional[str] = None, 
                            min_price: Optional[float] = None, max_price: Optional[float] = None,
                            skip: int = 0, limit: int = 10) -> tuple:
        """Search products by name, description, category and price range"""
        search_filter: Dict = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]
        }
        
        # Add category filter if provided
        if category:
            search_filter["category"] = {"$eq": category}
            
        # Add price range filters if provided
        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            if price_filter:
                search_filter["price"] = price_filter
        
        total = await self.collection.count_documents(search_filter)
        products = await self.collection.find(search_filter).skip(skip).limit(limit).to_list(limit)
        return products, total

    async def bulk_create_products(self, products_data: List[dict]) -> List[dict]:
        """Create multiple products in bulk"""
        # Add timestamps to all products
        for product_data in products_data:
            product_data["created_at"] = datetime.utcnow()
            product_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_many(products_data)
        # Add inserted IDs to the products data
        for i, product_data in enumerate(products_data):
            product_data["_id"] = result.inserted_ids[i]
        return products_data

    async def update_inventory(self, product_id: str, sku: str, quantity: int, 
                             reserved_quantity: int = 0) -> Optional[dict]:
        """Update product inventory information"""
        update_data = {
            "sku": sku,
            "inventory_quantity": quantity,
            "reserved_quantity": reserved_quantity,
            "updated_at": datetime.utcnow()
        }
        
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(product_id)},
                {"$set": update_data},
                return_document=True
            )
            return result
        except Exception:
            return None

    async def add_pricing_tiers(self, product_id: str, pricing_tiers: List[dict]) -> Optional[dict]:
        """Add pricing tiers to a product"""
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(product_id)},
                {
                    "$set": {
                        "pricing_tiers": pricing_tiers,
                        "updated_at": datetime.utcnow()
                    }
                },
                return_document=True
            )
            return result
        except Exception:
            return None

    async def add_tags(self, product_id: str, tags: List[str]) -> Optional[dict]:
        """Add tags to a product"""
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(product_id)},
                {
                    "$addToSet": {"tags": {"$each": tags}},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                return_document=True
            )
            return result
        except Exception:
            return None

    async def create_collection(self, name: str, slug: str, description: Optional[str] = None,
                              product_ids: Optional[List[str]] = None, metadata: Optional[dict] = None) -> dict:
        """Create a new product collection"""
        collection_data = {
            "name": name,
            "slug": slug,
            "description": description,
            "product_ids": product_ids or [],
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Get collections collection
        collections_collection = self.db["collections"]
        result = await collections_collection.insert_one(collection_data)
        collection_data["_id"] = result.inserted_id
        return collection_data

    async def get_collection_by_id(self, collection_id: str) -> Optional[dict]:
        """Get collection by MongoDB ID"""
        try:
            collections_collection = self.db["collections"]
            collection = await collections_collection.find_one({"_id": ObjectId(collection_id)})
            return collection
        except Exception:
            return None

    async def get_collection_by_slug(self, slug: str) -> Optional[dict]:
        """Get collection by slug"""
        try:
            collections_collection = self.db["collections"]
            collection = await collections_collection.find_one({"slug": slug})
            return collection
        except Exception:
            return None

    async def update_collection(self, collection_id: str, update_data: dict) -> Optional[dict]:
        """Update collection details"""
        # Remove None values from update_data
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return await self.get_collection_by_id(collection_id)
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            collections_collection = self.db["collections"]
            result = await collections_collection.find_one_and_update(
                {"_id": ObjectId(collection_id)},
                {"$set": update_data},
                return_document=True
            )
            return result
        except Exception:
            return None

    async def delete_collection(self, collection_id: str) -> bool:
        """Delete collection from database"""
        try:
            collections_collection = self.db["collections"]
            result = await collections_collection.delete_one({"_id": ObjectId(collection_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def get_all_collections(self, skip: int = 0, limit: int = 10) -> tuple:
        """Get all collections with pagination"""
        collections_collection = self.db["collections"]
        total = await collections_collection.count_documents({})
        collections = await collections_collection.find({}).skip(skip).limit(limit).to_list(limit)
        return collections, total

    def format_collection_response(self, collection: dict) -> dict:
        """Format collection document for response"""
        if not collection:
            return collection
            
        # Convert collection _id to string
        if "_id" in collection and collection["_id"] is not None:
            collection["_id"] = str(collection["_id"])
            
        return collection