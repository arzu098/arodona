"""Analytics repository."""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from bson import ObjectId

class AnalyticsRepository:
    def __init__(self, db):
        self.db = db
        self.orders_collection = db["orders"]
        self.products_collection = db["products"]
        self.users_collection = db["users"]
        self.vendors_collection = db["vendors"]
        self.categories_collection = db["categories"]

    def _get_date_boundaries(self, start_date: datetime, end_date: datetime, interval: str) -> Dict[str, Any]:
        """Get MongoDB date aggregation boundaries based on interval."""
        intervals = {
            "hour": {"format": "%Y-%m-%d-%H", "add": timedelta(hours=1)},
            "day": {"format": "%Y-%m-%d", "add": timedelta(days=1)},
            "week": {"format": "%Y-W%U", "add": timedelta(weeks=1)},
            "month": {"format": "%Y-%m", "add": timedelta(months=1)}
        }
        return intervals.get(interval, intervals["day"])

    async def get_sales_report(
        self,
        start_date: datetime,
        end_date: datetime,
        interval: str = "day",
        vendor_id: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate sales analytics report."""
        match_stage = {
            "created_at": {"$gte": start_date, "$lte": end_date},
            "status": {"$in": ["completed", "delivered"]}
        }
        if vendor_id:
            match_stage["vendor_id"] = vendor_id
        if category_id:
            match_stage["category_id"] = category_id

        # Basic metrics
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$total_amount"},
                "total_orders": {"$sum": 1},
                "refunded_orders": {
                    "$sum": {"$cond": [{"$eq": ["$status", "refunded"]}, 1, 0]}
                }
            }}
        ]
        
        basic_metrics = await self.orders_collection.aggregate(pipeline).to_list(length=1)
        basic_metrics = basic_metrics[0] if basic_metrics else {
            "total_revenue": 0,
            "total_orders": 0,
            "refunded_orders": 0
        }
        
        # Time series data
        time_boundaries = self._get_date_boundaries(start_date, end_date, interval)
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": time_boundaries["format"],
                        "date": "$created_at"
                    }
                },
                "value": {"$sum": "$total_amount"}
            }},
            {"$sort": {"_id": 1}}
        ]
        sales_by_time = await self.orders_collection.aggregate(pipeline).to_list(length=None)
        
        # Category distribution
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": "$category_id",
                "total": {"$sum": "$total_amount"}
            }},
            {"$sort": {"total": -1}}
        ]
        sales_by_category = await self.orders_collection.aggregate(pipeline).to_list(length=None)
        
        # Convert category IDs to names
        category_map = {}
        if sales_by_category:
            category_ids = [doc["_id"] for doc in sales_by_category]
            categories = await self.categories_collection.find(
                {"_id": {"$in": [ObjectId(id) for id in category_ids]}}
            ).to_list(length=None)
            category_map = {str(cat["_id"]): cat["name"] for cat in categories}
        
        # Top products
        pipeline = [
            {"$match": match_stage},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.product_id",
                "total_quantity": {"$sum": "$items.quantity"},
                "total_revenue": {"$sum": {"$multiply": ["$items.price", "$items.quantity"]}}
            }},
            {"$sort": {"total_revenue": -1}},
            {"$limit": 10}
        ]
        top_products = await self.orders_collection.aggregate(pipeline).to_list(length=None)
        
        # Get product details
        if top_products:
            product_ids = [ObjectId(doc["_id"]) for doc in top_products]
            products = await self.products_collection.find(
                {"_id": {"$in": product_ids}}
            ).to_list(length=None)
            product_map = {str(prod["_id"]): prod for prod in products}
            
            for product in top_products:
                prod_data = product_map.get(product["_id"], {})
                product["name"] = prod_data.get("name", "Unknown Product")
                product["sku"] = prod_data.get("sku", "")
                
        return {
            "total_revenue": basic_metrics["total_revenue"],
            "total_orders": basic_metrics["total_orders"],
            "average_order_value": basic_metrics["total_revenue"] / basic_metrics["total_orders"] if basic_metrics["total_orders"] > 0 else 0,
            "sales_by_day": [{"timestamp": doc["_id"], "value": doc["value"]} for doc in sales_by_time],
            "sales_by_category": {category_map.get(doc["_id"], "Unknown"): doc["total"] for doc in sales_by_category},
            "top_products": top_products,
            "refund_rate": basic_metrics["refunded_orders"] / basic_metrics["total_orders"] if basic_metrics["total_orders"] > 0 else 0
        }

    async def get_vendor_performance(
        self,
        vendor_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate vendor performance analytics."""
        match_stage = {
            "vendor_id": vendor_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }

        # Basic metrics
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$total_amount"},
                "total_orders": {"$sum": 1},
                "fulfilled_orders": {
                    "$sum": {"$cond": [{"$in": ["$status", ["completed", "delivered"]]}, 1, 0]}
                },
                "avg_shipping_time": {"$avg": {
                    "$divide": [
                        {"$subtract": ["$delivered_at", "$created_at"]},
                        1000 * 60 * 60 * 24  # Convert to days
                    ]
                }}
            }}
        ]
        
        metrics = await self.orders_collection.aggregate(pipeline).to_list(length=1)
        metrics = metrics[0] if metrics else {
            "total_revenue": 0,
            "total_orders": 0,
            "fulfilled_orders": 0,
            "avg_shipping_time": 0
        }
        
        # Get vendor rating
        pipeline = [
            {"$match": {"vendor_id": vendor_id}},
            {"$group": {
                "_id": None,
                "average_rating": {"$avg": "$rating"},
                "total_ratings": {"$sum": 1}
            }}
        ]
        ratings = await self.db.vendor_ratings.aggregate(pipeline).to_list(length=1)
        ratings = ratings[0] if ratings else {"average_rating": 0, "total_ratings": 0}
        
        # Category performance
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": "$category_id",
                "revenue": {"$sum": "$total_amount"},
                "orders": {"$sum": 1}
            }},
            {"$sort": {"revenue": -1}}
        ]
        categories = await self.orders_collection.aggregate(pipeline).to_list(length=None)
        
        return {
            "total_revenue": metrics["total_revenue"],
            "total_orders": metrics["total_orders"],
            "order_fulfillment_rate": metrics["fulfilled_orders"] / metrics["total_orders"] if metrics["total_orders"] > 0 else 0,
            "average_shipping_time": metrics["avg_shipping_time"],
            "rating": ratings["average_rating"],
            "customer_satisfaction": ratings["average_rating"],
            "revenue_trend": [],  # Implement time series aggregation as needed
            "category_performance": categories
        }

    async def get_customer_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate customer behavior analytics."""
        # Total unique customers
        total_customers = await self.users_collection.count_documents({
            "role": "customer",
            "created_at": {"$lte": end_date}
        })
        
        # New customers in period
        new_customers = await self.users_collection.count_documents({
            "role": "customer",
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Orders analysis
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "status": {"$in": ["completed", "delivered"]}
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "order_count": {"$sum": 1},
                    "total_spent": {"$sum": "$total_amount"}
                }
            }
        ]
        
        customer_orders = await self.orders_collection.aggregate(pipeline).to_list(length=None)
        
        # Calculate metrics
        repeat_customers = len([c for c in customer_orders if c["order_count"] > 1])
        total_customers_ordered = len(customer_orders)
        total_spent = sum(c["total_spent"] for c in customer_orders)
        
        return {
            "total_customers": total_customers,
            "new_customers": new_customers,
            "repeat_customers": repeat_customers,
            "average_lifetime_value": total_spent / total_customers_ordered if total_customers_ordered > 0 else 0,
            "retention_rate": repeat_customers / total_customers_ordered if total_customers_ordered > 0 else 0,
            "acquisition_channels": {},  # Implement if tracking acquisition source
            "customer_segments": []  # Implement customer segmentation as needed
        }

    async def get_marketplace_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate overall marketplace performance metrics."""
        # Basic metrics
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "status": {"$in": ["completed", "delivered"]}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "gmv": {"$sum": "$total_amount"},
                    "total_transactions": {"$sum": 1},
                    "avg_basket_size": {"$avg": "$total_amount"}
                }
            }
        ]
        
        basic_metrics = await self.orders_collection.aggregate(pipeline).to_list(length=1)
        basic_metrics = basic_metrics[0] if basic_metrics else {
            "gmv": 0,
            "total_transactions": 0,
            "avg_basket_size": 0
        }
        
        # Active vendors and buyers
        active_vendors = await self.vendors_collection.count_documents({
            "last_active": {"$gte": start_date}
        })
        
        active_buyers = await self.orders_collection.aggregate([
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$user_id"
                }
            },
            {
                "$count": "count"
            }
        ]).to_list(length=1)
        active_buyers = active_buyers[0]["count"] if active_buyers else 0
        
        # Category distribution
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "status": {"$in": ["completed", "delivered"]}
                }
            },
            {
                "$group": {
                    "_id": "$category_id",
                    "total": {"$sum": "$total_amount"}
                }
            },
            {"$sort": {"total": -1}}
        ]
        
        category_sales = await self.orders_collection.aggregate(pipeline).to_list(length=None)
        total_sales = sum(cat["total"] for cat in category_sales)
        
        category_distribution = {}
        if category_sales:
            category_ids = [ObjectId(doc["_id"]) for doc in category_sales]
            categories = await self.categories_collection.find(
                {"_id": {"$in": category_ids}}
            ).to_list(length=None)
            category_map = {str(cat["_id"]): cat["name"] for cat in categories}
            
            for cat in category_sales:
                name = category_map.get(cat["_id"], "Unknown")
                category_distribution[name] = cat["total"] / total_sales if total_sales > 0 else 0
        
        return {
            "gross_merchandise_value": basic_metrics["gmv"],
            "total_transactions": basic_metrics["total_transactions"],
            "active_vendors": active_vendors,
            "active_buyers": active_buyers,
            "conversion_rate": 0,  # Implement if tracking sessions/views
            "average_basket_size": basic_metrics["avg_basket_size"],
            "category_distribution": category_distribution,
            "top_search_terms": []  # Implement if tracking search queries
        }

    async def get_inventory_analytics(self) -> Dict[str, Any]:
        """Generate inventory and product analytics."""
        # Basic product metrics
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_products": {"$sum": 1},
                    "active_products": {
                        "$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}
                    },
                    "out_of_stock": {
                        "$sum": {"$cond": [{"$eq": ["$stock_quantity", 0]}, 1, 0]}
                    },
                    "low_stock": {
                        "$sum": {
                            "$cond": [
                                {"$and": [
                                    {"$gt": ["$stock_quantity", 0]},
                                    {"$lt": ["$stock_quantity", "$low_stock_threshold"]}
                                ]},
                                1,
                                0
                            ]
                        }
                    }
                }
            }
        ]
        
        product_metrics = await self.products_collection.aggregate(pipeline).to_list(length=1)
        product_metrics = product_metrics[0] if product_metrics else {
            "total_products": 0,
            "active_products": 0,
            "out_of_stock": 0,
            "low_stock": 0
        }
        
        # Category performance
        pipeline = [
            {
                "$group": {
                    "_id": "$category_id",
                    "product_count": {"$sum": 1},
                    "total_stock": {"$sum": "$stock_quantity"},
                    "avg_price": {"$avg": "$price"}
                }
            },
            {"$sort": {"product_count": -1}}
        ]
        
        categories = await self.products_collection.aggregate(pipeline).to_list(length=10)
        
        if categories:
            category_ids = [ObjectId(doc["_id"]) for doc in categories]
            category_docs = await self.categories_collection.find(
                {"_id": {"$in": category_ids}}
            ).to_list(length=None)
            category_map = {str(cat["_id"]): cat["name"] for cat in category_docs}
            
            for cat in categories:
                cat["name"] = category_map.get(cat["_id"], "Unknown")
        
        return {
            "total_products": product_metrics["total_products"],
            "active_products": product_metrics["active_products"],
            "out_of_stock_products": product_metrics["out_of_stock"],
            "low_stock_products": product_metrics["low_stock"],
            "top_performing_categories": categories,
            "inventory_turnover": 0,  # Implement if tracking historical inventory levels
            "stock_metrics": {
                "out_of_stock_rate": product_metrics["out_of_stock"] / product_metrics["total_products"] if product_metrics["total_products"] > 0 else 0,
                "low_stock_rate": product_metrics["low_stock"] / product_metrics["total_products"] if product_metrics["total_products"] > 0 else 0
            }
        }

    async def create_indexes(self):
        """Create necessary indexes."""
        await self.orders_collection.create_index([("created_at", -1)])
        await self.orders_collection.create_index("vendor_id")
        await self.orders_collection.create_index("user_id")
        await self.orders_collection.create_index("category_id")
        await self.products_collection.create_index([("created_at", -1)])
        await self.products_collection.create_index("vendor_id")
        await self.products_collection.create_index("category_id")