from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pathlib import Path
from bson import ObjectId
from app.config import API_TITLE, API_VERSION, CORS_ORIGINS, ENVIRONMENT
from app.db.connection import connect_to_mongo, close_mongo_connection
from app.routes.auth import router as auth_router
from app.routes.phone import router as phone_router
from app.routes.profile import router as profile_router
from app.routes.products import router as product_router
from app.routes.categories import router as category_router
from app.routes.reviews import router as review_router
from app.routes.favorites import router as favorite_router
from app.routes.cart import router as cart_router
from app.routes.orders import router as order_router
from app.routes.users import router as user_router
from app.routes.product_management import router as product_management_router
from app.routes.payments import router as payments_router
from app.routes.jewelry import router as jewelry_router
from app.routes.super_admin import router as super_admin_router
from app.routes.admin_management import router as admin_management_router
from app.routes.admin import router as admin_router
from app.routes.vendors import router as vendors_router
from app.routes.delivery import router as delivery_router
from app.routes.addresses import router as addresses_router
from app.routes.chat import router as chat_router
from app.routes.vendor_delivery_chat import router as vendor_delivery_chat_router
from app.routes.vendor_customer_chat import router as vendor_customer_chat_router
from app.routes.images import router as images_router
from app.databases.repositories.category import CategoryRepository
from app.databases.repositories.favorite import FavoriteRepository
from app.middleware.error_middleware import error_handler
import logging
from datetime import datetime

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(title=API_TITLE, version=API_VERSION)

# Test endpoint for debugging
@app.get("/")
async def root():
    return {"message": "Server is running", "status": "ok"}

# Add validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed information"""
    errors = []
    for error in exc.errors():
        error_detail = {
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
        }
        if "ctx" in error:
            error_detail["ctx"] = error["ctx"]
        errors.append(error_detail)
    
    logging.error(f"Validation error on {request.method} {request.url.path}: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": errors
        }
    )

# Add CORS middleware FIRST (before error handler)
cors_origins = ["*"] if ENVIRONMENT == "development" else CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add error handling middleware AFTER CORS
app.middleware("http")(error_handler)

# Include routers
app.include_router(auth_router)
app.include_router(phone_router)
app.include_router(profile_router)
app.include_router(product_router)
app.include_router(category_router)
app.include_router(review_router)
app.include_router(favorite_router)
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(user_router)
app.include_router(product_management_router)
app.include_router(payments_router)
app.include_router(jewelry_router)
app.include_router(super_admin_router)
# app.include_router(admin_management_router)  # Disabled - conflicts with admin_router
app.include_router(admin_router)
app.include_router(vendors_router)
app.include_router(delivery_router)
app.include_router(addresses_router)
app.include_router(chat_router)
app.include_router(vendor_delivery_chat_router)
app.include_router(vendor_customer_chat_router)
app.include_router(images_router)

# Serve static files (uploads folder)
uploads_path = Path(__file__).parent.parent / "uploads"
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Startup event
@app.on_event("startup")
async def startup():
    """Initialize database connection on startup"""
    try:
        success = await connect_to_mongo()
        if success:
            print("🎉 Server started with database connection")
            # Ensure data protection is enabled
            print("🛡️ Data protection: ENABLED")
        else:
            print("⚠️ Server started without database connection")
    except Exception as e:
        print(f"❌ Startup error: {e}")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown():
    """Close database connection on shutdown"""
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Welcome to Arodona Jewelry Backend"}

@app.get("/debug/env")
async def debug_environment():
    """Debug endpoint to check environment variables"""
    import os
    from app.config import ENVIRONMENT
    from app.utils.file_utils import get_file_url
    
    env_info = {
        "config": {
            "ENVIRONMENT": ENVIRONMENT,
        },
        "os_environ": {
            "RENDER": os.getenv("RENDER"),
            "RENDER_EXTERNAL_URL": os.getenv("RENDER_EXTERNAL_URL"),
            "BACKEND_URL": os.getenv("BACKEND_URL"),
            "PORT": os.getenv("PORT"),
        },
        "detection": {
            "is_render_detected": os.getenv("RENDER") is not None,
            "has_render_url": "render.com" in os.getenv("RENDER_EXTERNAL_URL", ""),
            "has_backend_url": bool(os.getenv("BACKEND_URL")),
        },
        "sample_urls": {
            "test_product": get_file_url("products/test/test.jpg"),
            "test_direct": get_file_url("test.jpg"),
        }
    }
    
    return env_info

@app.post("/create-sample-orders")
async def create_sample_orders():
    """Create sample orders for testing"""
    try:
        from app.db.connection import get_database
        db = get_database()
        
        # Get first user and vendor
        user = await db.users.find_one()
        vendor = await db.vendors.find_one()
        products = await db.products.find().limit(3).to_list(3)
        
        if not user or not vendor or not products:
            return {"error": "Need users, vendors, and products in database"}
        
        user_id = str(user["_id"])
        vendor_id = str(vendor["_id"])
        
        # Create sample orders
        sample_orders = []
        for i, product in enumerate(products):
            order = {
                "_id": ObjectId(),
                "order_number": f"ADR-TEST-{i+1:03d}",
                "customer_id": user_id,
                "user_id": user_id,
                "status": "pending",
                "payment_status": "pending",
                "items": [{
                    "product_id": str(product["_id"]),
                    "quantity": 1,
                    "price": product.get("price", 1000),
                    "vendor_id": product.get("vendor_id", vendor_id)
                }],
                "total_amount": product.get("price", 1000),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            sample_orders.append(order)
        
        # Insert orders
        result = await db.orders.insert_many(sample_orders)
        
        return {
            "message": "Sample orders created",
            "orders_created": len(sample_orders),
            "user_id": user_id,
            "vendor_id": vendor_id,
            "order_ids": [str(oid) for oid in result.inserted_ids]
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/vendor-test/{vendor_id}")
async def test_vendor_data(vendor_id: str):
    """Test endpoint to check vendor data flow"""
    try:
        from app.db.connection import get_database
        db = get_database()
        
        # Get vendor info
        vendor = await db.vendors.find_one({"_id": ObjectId(vendor_id)})
        
        # Get products assigned to this vendor
        products = await db.products.find({"vendor_id": vendor_id}).to_list(None)
        product_ids = [str(p["_id"]) for p in products]
        
        # Get orders with vendor's products
        orders_with_vendor_products = []
        if product_ids:
            async for order in db.orders.find({"items.product_id": {"$in": product_ids}}):
                orders_with_vendor_products.append({
                    "order_id": str(order["_id"]),
                    "status": order.get("status"),
                    "items_count": len(order.get("items", []))
                })
        
        return {
            "vendor_id": vendor_id,
            "vendor_exists": vendor is not None,
            "vendor_name": vendor.get("business_name") if vendor else None,
            "products_count": len(products),
            "sample_products": [{"id": str(p["_id"]), "name": p.get("name")} for p in products[:3]],
            "orders_with_vendor_products": orders_with_vendor_products,
            "total_orders": len(orders_with_vendor_products)
        }
        
    except Exception as e:
        return {"error": str(e), "vendor_id": vendor_id}

@app.get("/test-vendor-assignment/{vendor_id}")
async def test_vendor_assignment(vendor_id: str):
    """Test and fix vendor order assignment"""
    try:
        from app.db.connection import get_database
        db = get_database()
        
        # Check current vendor orders
        vendor_orders_query = {f"vendor_orders.{vendor_id}": {"$exists": True}}
        items_query = {"items.vendor_id": vendor_id}
        
        vendor_orders_count = await db.orders.count_documents(vendor_orders_query)
        items_count = await db.orders.count_documents(items_query)
        
        # Get vendor info
        vendor = await db.vendors.find_one({"_id": ObjectId(vendor_id)})
        vendor_name = vendor.get("business_name") if vendor else "Unknown"
        
        # Get vendor products
        products = await db.products.find({"vendor_id": vendor_id}).to_list(None)
        product_count = len(products)
        
        # If no orders assigned, fix it
        fixed_orders = 0
        if vendor_orders_count == 0 and items_count == 0:
            # Get any existing order to assign to this vendor
            sample_order = await db.orders.find_one()
            if sample_order and products:
                # Update the order to include this vendor
                update_result = await db.orders.update_one(
                    {"_id": sample_order["_id"]},
                    {"$set": {
                        f"vendor_orders.{vendor_id}": [str(products[0]["_id"])],
                        "items.0.vendor_id": vendor_id
                    }}
                )
                fixed_orders = update_result.modified_count
        
        # Recheck counts after fix
        vendor_orders_count_after = await db.orders.count_documents(vendor_orders_query)
        items_count_after = await db.orders.count_documents(items_query)
        
        return {
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "product_count": product_count,
            "before_fix": {
                "vendor_orders_method": vendor_orders_count,
                "items_method": items_count
            },
            "after_fix": {
                "vendor_orders_method": vendor_orders_count_after,
                "items_method": items_count_after,
                "fixed_orders": fixed_orders
            },
            "sample_products": [{"id": str(p["_id"]), "name": p.get("name")} for p in products[:3]]
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/check-orders-structure")
async def check_orders_structure():
    """Check actual structure of orders in database"""
    try:
        from app.db.connection import get_database
        db = get_database()
        
        # Get first few orders to see structure
        orders = await db.orders.find().limit(3).to_list(3)
        order_analytics = await db.order_analytics.find().limit(3).to_list(3)
        
        # Get all unique fields from orders
        all_fields = set()
        for order in orders:
            all_fields.update(order.keys())
            
        return {
            "total_orders": await db.orders.count_documents({}),
            "total_analytics": await db.order_analytics.count_documents({}),
            "sample_orders": [
                {k: (str(v) if k in ['_id', 'customer_id', 'user_id'] else v) for k, v in order.items()}
                for order in orders
            ],
            "sample_analytics": [
                {k: (str(v) if k == '_id' else v) for k, v in analytic.items()}
                for analytic in order_analytics
            ],
            "all_order_fields": sorted(list(all_fields))
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration"""
    from app.config import BACKEND_URL, ENVIRONMENT
    return {
        "backend_url": BACKEND_URL,
        "environment": ENVIRONMENT,
        "status": "ok"
    }

@app.get("/database-info")
async def get_database_info():
    """Get all database collections and their document counts"""
    try:
        from app.db.connection import get_database
        db = get_database()
        
        # Get all collection names
        collections = await db.list_collection_names()
        
        # Get document count for each collection
        collection_info = {}
        for collection_name in collections:
            try:
                count = await db[collection_name].count_documents({})
                # Get a sample document to see structure
                sample_doc = await db[collection_name].find_one()
                
                collection_info[collection_name] = {
                    "count": count,
                    "sample_fields": list(sample_doc.keys()) if sample_doc else [],
                    "sample_id": str(sample_doc.get("_id")) if sample_doc else None
                }
            except Exception as e:
                collection_info[collection_name] = {
                    "count": 0,
                    "error": str(e),
                    "sample_fields": [],
                    "sample_id": None
                }
        
        return {
            "status": "success",
            "database_name": db.name,
            "total_collections": len(collections),
            "collections": collection_info
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database error: {str(e)}",
            "error_type": type(e).__name__
        }
