"""
Admin API endpoints for platform management.
Handles user management, settings, regions, and auditing.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from datetime import datetime, timedelta

from app.databases.schemas.admin import (
    AdminCreateUser, AdminUpdateUser, AdminSettings,
    Region, AuditLog
)
from app.databases.repositories.admin import AdminRepository
from app.databases.repositories.user import UserRepository
from app.utils.security import get_current_user, hash_password
from app.db.connection import get_database

router = APIRouter(prefix="/api/admin", tags=["Admin"])

async def get_admin_repository() -> AdminRepository:
    """Dependency to get admin repository"""
    db = get_database()
    return AdminRepository(db)

async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Check if user has admin or super_admin role."""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminCreateUser,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Create a new user (admin operation)."""
    try:
        user = await repo.create_user(user_data.dict())
        
        # Log audit
        await repo.log_audit({
            "action": "create_user",
            "entity_type": "user",
            "entity_id": user.get("id"),
            "changes": {k: v for k, v in user_data.dict().items() if k != "password"},
            "performed_by": current_user["user_id"]
        })
        
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: AdminUpdateUser,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Update user details (admin operation)."""
    try:
        updated = await repo.update_user(user_id, update_data.dict(exclude_unset=True))
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log audit (exclude sensitive data)
        changes = {k: v for k, v in update_data.dict(exclude_unset=True).items() if k != "password"}
        await repo.log_audit({
            "action": "update_user",
            "entity_type": "user",
            "entity_id": user_id,
            "changes": changes,
            "performed_by": current_user["user_id"]
        })
        
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """List users with filters (excludes admin accounts)."""
    try:
        users, total = await repo.list_users(skip, limit, role, status)
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "users": users
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/vendors")
async def list_vendors(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """List vendors for admin management."""
    try:
        vendors, total = await repo.list_vendors(skip, limit, status)
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "vendors": vendors
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Get system audit logs."""
    try:
        print(f"[AUDIT_LOGS] Starting request - skip={skip}, limit={limit}")
        print(f"[AUDIT_LOGS] Current user: {current_user.get('id')}")
        
        logs, total = await repo.get_audit_logs(
            skip, limit, action, entity_type, from_date, to_date
        )
        
        print(f"[AUDIT_LOGS] Retrieved {len(logs)} logs, total={total}")
        
        result = {
            "total": total,
            "skip": skip,
            "limit": limit,
            "logs": logs
        }
        
        print(f"[AUDIT_LOGS] Returning response successfully")
        return result
    except Exception as e:
        print(f"[AUDIT_LOGS] ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/settings")
async def get_settings(
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Get platform settings."""
    try:
        return await repo.get_settings()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/settings")
async def update_settings(
    settings: AdminSettings,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Update platform settings."""
    try:
        updated = await repo.update_settings(settings.dict())
        
        # Log audit
        await repo.log_audit({
            "action": "update_settings",
            "entity_type": "settings",
            "entity_id": "default",
            "changes": settings.dict(),
            "performed_by": current_user["user_id"]
        })
        
        return updated
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/regions")
async def create_region(
    region: Region,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Create a new region configuration."""
    try:
        created = await repo.create_region(region.dict())
        
        # Log audit
        await repo.log_audit({
            "action": "create_region",
            "entity_type": "region",
            "entity_id": region.code,
            "changes": region.dict(),
            "performed_by": current_user["user_id"]
        })
        
        return created
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/vendors/{vendor_id}/approve")
async def approve_vendor(
    vendor_id: str,
    approved: bool,
    remarks: Optional[str] = None,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Approve or reject vendor application."""
    try:
        updated = await repo.approve_vendor(
            vendor_id,
            approved,
            current_user["user_id"],
            remarks
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        # Log audit
        await repo.log_audit({
            "action": "vendor_approval",
            "entity_type": "vendor",
            "entity_id": vendor_id,
            "changes": {"approved": approved, "remarks": remarks},
            "performed_by": current_user["user_id"]
        })
        
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/content/{content_type}/{content_id}/moderate")
async def moderate_content(
    content_type: str,
    content_id: str,
    action: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Moderate platform content."""
    try:
        success = await repo.moderate_content(
            content_type,
            content_id,
            action,
            current_user["user_id"],
            reason
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{content_type} not found"
            )
        
        # Log audit
        await repo.log_audit({
            "action": "moderate_content",
            "entity_type": content_type,
            "entity_id": content_id,
            "changes": {"action": action, "reason": reason},
            "performed_by": current_user["user_id"]
        })
        
        return {"message": "Content moderated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Get admin dashboard statistics."""
    try:
        db = get_database()
        
        # Get basic statistics
        total_users = await repo.get_total_users()
        total_vendors = await repo.get_total_vendors()
        pending_vendor_approvals = await repo.get_pending_vendor_approvals()
        recent_users = await repo.get_recent_users(limit=5)
        
        # Get order statistics
        orders_collection = db["orders"]
        total_orders = await orders_collection.count_documents({})
        pending_orders = await orders_collection.count_documents({
            "order_status": {"$in": ["pending", "processing"]}
        })
        
        # Get revenue statistics
        pipeline = [
            {
                "$match": {
                    "payment_status": "completed"
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$totals.grand_total"}
                }
            }
        ]
        revenue_result = await orders_collection.aggregate(pipeline).to_list(length=1)
        total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0
        
        return {
            "total_users": total_users,
            "total_vendors": total_vendors,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "pending_vendor_approvals": pending_vendor_approvals,
            "pending_orders": pending_orders,
            "recent_users": recent_users
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/create-vendor", status_code=status.HTTP_201_CREATED)
async def create_vendor_account(
    vendor_data: dict,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Create a new vendor account (admin operation)."""
    try:
        # Validate required fields (last_name is optional)
        required_fields = ['email', 'password', 'first_name']
        for field in required_fields:
            if field not in vendor_data or not vendor_data[field]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Set default for optional fields
        if 'last_name' not in vendor_data:
            vendor_data['last_name'] = ''
        
        # Check if email already exists
        db = get_database()
        existing_user = await db["users"].find_one({"email": vendor_data["email"]})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password and store in password_hash field
        password_hash = hash_password(vendor_data.pop("password"))
        vendor_data["password_hash"] = password_hash
        vendor_data["role"] = "vendor"
        vendor_data["is_active"] = False  # Vendors start inactive
        vendor_data["status"] = "inactive"  # Vendors start inactive
        vendor_data["business_status"] = "pending"  # Awaiting approval
        vendor_data["created_at"] = datetime.utcnow()
        vendor_data["updated_at"] = datetime.utcnow()
        
        # Set created_by to track who created this vendor
        from bson import ObjectId
        vendor_data["created_by"] = ObjectId(current_user["user_id"])
        
        # Insert vendor
        result = await db["users"].insert_one(vendor_data)
        vendor_data["_id"] = result.inserted_id
        
        # Log audit
        await repo.log_audit({
            "action": "create_vendor",
            "entity_type": "user",
            "entity_id": str(result.inserted_id),
            "changes": {k: v for k, v in vendor_data.items() if k != "password"},
            "performed_by": current_user["user_id"]
        })
        
        # Return formatted response
        return {
            "id": str(result.inserted_id),
            "email": vendor_data["email"],
            "first_name": vendor_data["first_name"],
            "last_name": vendor_data["last_name"],
            "phone": vendor_data.get("phone"),
            "role": "vendor",
            "status": "inactive",
            "business_name": vendor_data.get("business_name"),
            "business_type": vendor_data.get("business_type"),
            "business_status": "pending",
            "created_at": vendor_data["created_at"].isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/orders")
async def get_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Get all orders for admin management."""
    try:
        db = get_database()
        orders_collection = db["orders"]
        
        # Build query
        query = {}
        if status:
            query["order_status"] = status
        if payment_status:
            query["payment_status"] = payment_status
        if from_date or to_date:
            query["created_at"] = {}
            if from_date:
                query["created_at"]["$gte"] = from_date
            if to_date:
                query["created_at"]["$lte"] = to_date
        
        # Get orders
        cursor = orders_collection.find(query).sort("created_at", -1)
        total = await orders_collection.count_documents(query)
        orders = await cursor.skip(skip).limit(limit).to_list(length=limit)
        
        # Format orders
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                "id": str(order["_id"]),
                "order_number": order.get("order_number"),
                "customer_email": order.get("customer_email"),
                "order_status": order.get("order_status"),
                "payment_status": order.get("payment_status"),
                "total_amount": order.get("totals", {}).get("grand_total", 0),
                "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
                "items_count": len(order.get("items", []))
            })
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "orders": formatted_orders
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/orders/{order_id}")
async def get_order_details(
    order_id: str,
    current_user: dict = Depends(get_admin_user)
):
    """Get detailed order information."""
    try:
        from bson import ObjectId
        db = get_database()
        orders_collection = db["orders"]
        
        order = await orders_collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Format order details
        return {
            "id": str(order["_id"]),
            "order_number": order.get("order_number"),
            "customer_id": order.get("customer_id"),
            "customer_email": order.get("customer_email"),
            "order_status": order.get("order_status"),
            "payment_status": order.get("payment_status"),
            "fulfillment_status": order.get("fulfillment_status"),
            "items": order.get("items", []),
            "shipping_address": order.get("shipping_address"),
            "billing_address": order.get("billing_address"),
            "totals": order.get("totals"),
            "timeline": order.get("timeline", []),
            "created_at": order.get("created_at").isoformat() if order.get("created_at") else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_data: dict,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Update order status (admin operation)."""
    try:
        from bson import ObjectId
        db = get_database()
        orders_collection = db["orders"]
        
        # Validate status
        valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled", "refunded"]
        new_status = status_data.get("status")
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Update order
        update_data = {
            "order_status": new_status,
            "updated_at": datetime.utcnow()
        }
        
        # Add to timeline
        timeline_entry = {
            "status": new_status,
            "timestamp": datetime.utcnow(),
            "updated_by": current_user["user_id"],
            "notes": status_data.get("notes", "")
        }
        
        result = await orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": update_data,
                "$push": {"timeline": timeline_entry}
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Log audit
        await repo.log_audit({
            "action": "update_order_status",
            "entity_type": "order",
            "entity_id": order_id,
            "changes": {"status": new_status, "notes": status_data.get("notes")},
            "performed_by": current_user["user_id"]
        })
        
        return {"message": "Order status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/analytics/overview")
async def get_analytics_overview(
    period: str = Query("month", regex="^(day|week|month|year)$"),
    current_user: dict = Depends(get_admin_user)
):
    """Get analytics overview for dashboard."""
    try:
        db = get_database()
        
        # Calculate date range
        now = datetime.utcnow()
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:  # year
            start_date = now - timedelta(days=365)
        
        # Get orders analytics
        orders_collection = db["orders"]
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_orders": {"$sum": 1},
                    "total_revenue": {"$sum": "$totals.grand_total"},
                    "completed_orders": {
                        "$sum": {
                            "$cond": [{"$eq": ["$payment_status", "completed"]}, 1, 0]
                        }
                    },
                    "pending_orders": {
                        "$sum": {
                            "$cond": [{"$eq": ["$order_status", "pending"]}, 1, 0]
                        }
                    }
                }
            }
        ]
        
        result = await orders_collection.aggregate(pipeline).to_list(length=1)
        analytics = result[0] if result else {
            "total_orders": 0,
            "total_revenue": 0,
            "completed_orders": 0,
            "pending_orders": 0
        }
        
        # Get user growth
        users_collection = db["users"]
        new_users = await users_collection.count_documents({
            "created_at": {"$gte": start_date},
            "role": {"$nin": ["admin", "super_admin"]}
        })
        
        # Get products count
        products_collection = db["products"]
        total_products = await products_collection.count_documents({"is_active": True})
        
        return {
            "period": period,
            "total_orders": analytics.get("total_orders", 0),
            "total_revenue": analytics.get("total_revenue", 0),
            "completed_orders": analytics.get("completed_orders", 0),
            "pending_orders": analytics.get("pending_orders", 0),
            "new_users": new_users,
            "total_products": total_products
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Delete user account (soft delete)."""
    try:
        from bson import ObjectId
        db = get_database()
        
        # Check if user exists and is not admin
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.get("role") in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete admin accounts"
            )
        
        # Soft delete
        await db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "status": "deleted",
                    "deleted_at": datetime.utcnow(),
                    "deleted_by": current_user["user_id"]
                }
            }
        )
        
        # Log audit
        await repo.log_audit({
            "action": "delete_user",
            "entity_type": "user",
            "entity_id": user_id,
            "changes": {"status": "deleted"},
            "performed_by": current_user["user_id"]
        })
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/products")
async def get_all_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    vendor_id: Optional[str] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Get all products for admin management."""
    try:
        db = get_database()
        products_collection = db["products"]
        
        # Build query
        query = {}
        if status == "active":
            query["is_active"] = True
        elif status == "inactive":
            query["is_active"] = False
        if category:
            query["categories"] = category
        if vendor_id:
            query["vendor_id"] = vendor_id
        
        # Get products
        cursor = products_collection.find(query).sort("created_at", -1)
        total = await products_collection.count_documents(query)
        products = await cursor.skip(skip).limit(limit).to_list(length=limit)
        
        # Format products
        formatted_products = []
        for product in products:
            formatted_products.append({
                "id": str(product["_id"]),
                "name": product.get("name"),
                "sku": product.get("sku"),
                "price": product.get("price"),
                "stock_quantity": product.get("stock_quantity"),
                "is_active": product.get("is_active", True),
                "vendor_id": product.get("vendor_id"),
                "categories": product.get("categories", []),
                "created_at": product.get("created_at").isoformat() if product.get("created_at") else None
            })
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "products": formatted_products
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/products/{product_id}/status")
async def update_product_status(
    product_id: str,
    status_data: dict,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Update product status (activate/deactivate)."""
    try:
        from bson import ObjectId
        db = get_database()
        products_collection = db["products"]
        
        is_active = status_data.get("is_active")
        if is_active is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="is_active field is required"
            )
        
        result = await products_collection.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "is_active": is_active,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Log audit
        await repo.log_audit({
            "action": "update_product_status",
            "entity_type": "product",
            "entity_id": product_id,
            "changes": {"is_active": is_active},
            "performed_by": current_user["user_id"]
        })
        
        return {"message": "Product status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Delete product (soft delete)."""
    try:
        from bson import ObjectId
        db = get_database()
        products_collection = db["products"]
        
        result = await products_collection.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "is_active": False,
                    "deleted_at": datetime.utcnow(),
                    "deleted_by": current_user["user_id"]
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Log audit
        await repo.log_audit({
            "action": "delete_product",
            "entity_type": "product",
            "entity_id": product_id,
            "changes": {"deleted": True},
            "performed_by": current_user["user_id"]
        })
        
        return {"message": "Product deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/categories")
async def get_all_categories(
    current_user: dict = Depends(get_admin_user)
):
    """Get all categories."""
    try:
        db = get_database()
        categories_collection = db["categories"]
        
        categories = await categories_collection.find({}).to_list(length=None)
        
        formatted_categories = []
        for category in categories:
            formatted_categories.append({
                "id": str(category["_id"]),
                "name": category.get("name"),
                "slug": category.get("slug"),
                "parent_id": category.get("parent_id"),
                "level": category.get("level", 0),
                "is_active": category.get("is_active", True),
                "product_count": category.get("product_count", 0)
            })
        
        return {
            "total": len(formatted_categories),
            "categories": formatted_categories
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/categories")
async def create_category(
    category_data: dict,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Create new category."""
    try:
        db = get_database()
        categories_collection = db["categories"]
        
        # Validate required fields
        if not category_data.get("name"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name is required"
            )
        
        # Generate slug
        from slugify import slugify
        category_data["slug"] = slugify(category_data["name"])
        category_data["created_at"] = datetime.utcnow()
        category_data["is_active"] = True
        category_data["product_count"] = 0
        
        result = await categories_collection.insert_one(category_data)
        
        # Log audit
        await repo.log_audit({
            "action": "create_category",
            "entity_type": "category",
            "entity_id": str(result.inserted_id),
            "changes": category_data,
            "performed_by": current_user["user_id"]
        })
        
        return {
            "id": str(result.inserted_id),
            "name": category_data["name"],
            "slug": category_data["slug"],
            "message": "Category created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/categories/{category_id}")
async def update_category(
    category_id: str,
    category_data: dict,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Update category."""
    try:
        from bson import ObjectId
        db = get_database()
        categories_collection = db["categories"]
        
        category_data["updated_at"] = datetime.utcnow()
        
        result = await categories_collection.update_one(
            {"_id": ObjectId(category_id)},
            {"$set": category_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Log audit
        await repo.log_audit({
            "action": "update_category",
            "entity_type": "category",
            "entity_id": category_id,
            "changes": category_data,
            "performed_by": current_user["user_id"]
        })
        
        return {"message": "Category updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Delete category."""
    try:
        from bson import ObjectId
        db = get_database()
        categories_collection = db["categories"]
        
        # Check if category has products
        products_collection = db["products"]
        product_count = await products_collection.count_documents({
            "categories": category_id
        })
        
        if product_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category with {product_count} products. Please reassign products first."
            )
        
        result = await categories_collection.delete_one({"_id": ObjectId(category_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Log audit
        await repo.log_audit({
            "action": "delete_category",
            "entity_type": "category",
            "entity_id": category_id,
            "changes": {"deleted": True},
            "performed_by": current_user["user_id"]
        })
        
        return {"message": "Category deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/vendors/{vendor_id}")
async def get_vendor_details(
    vendor_id: str,
    current_user: dict = Depends(get_admin_user)
):
    """Get detailed vendor information."""
    try:
        from bson import ObjectId
        db = get_database()
        users_collection = db["users"]
        
        vendor = await users_collection.find_one({
            "_id": ObjectId(vendor_id),
            "role": "vendor"
        })
        
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        # Get vendor's products count
        products_collection = db["products"]
        products_count = await products_collection.count_documents({
            "vendor_id": vendor_id
        })
        
        # Get vendor's orders count
        orders_collection = db["orders"]
        orders_count = await orders_collection.count_documents({
            "items.vendor_id": vendor_id
        })
        
        return {
            "id": str(vendor["_id"]),
            "email": vendor.get("email"),
            "first_name": vendor.get("first_name"),
            "last_name": vendor.get("last_name"),
            "phone": vendor.get("phone"),
            "business_name": vendor.get("business_name"),
            "business_type": vendor.get("business_type"),
            "business_status": vendor.get("business_status", "pending"),
            "status": vendor.get("status", "active"),
            "created_at": vendor.get("created_at").isoformat() if vendor.get("created_at") else None,
            "products_count": products_count,
            "orders_count": orders_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/vendors/{vendor_id}/status")
async def update_vendor_status(
    vendor_id: str,
    status_data: dict,
    current_user: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository)
):
    """Update vendor account status."""
    try:
        from bson import ObjectId
        db = get_database()
        users_collection = db["users"]
        
        new_status = status_data.get("new_status") or status_data.get("status")
        notes = status_data.get("notes", "")
        
        # Map status values for approval/rejection
        if new_status == "approved":
            actual_status = "active"
            is_active = True
            business_status = "approved"
        elif new_status == "rejected":
            actual_status = "inactive"
            is_active = False
            business_status = "rejected"
        else:
            # Direct status update
            valid_statuses = ["active", "inactive", "suspended"]
            if new_status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: approved, rejected, active, inactive, suspended"
                )
            actual_status = new_status
            is_active = (new_status == "active")
            business_status = new_status
        
        # Update vendor status
        update_fields = {
            "status": actual_status,
            "is_active": is_active,
            "business_status": business_status,
            "updated_at": datetime.utcnow()
        }
        
        if notes:
            update_fields["approval_notes"] = notes
            
        if new_status == "approved":
            update_fields["approved_at"] = datetime.utcnow()
            update_fields["approved_by"] = current_user["user_id"]
        
        result = await users_collection.update_one(
            {"_id": ObjectId(vendor_id), "role": "vendor"},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        # Log audit
        await repo.log_audit({
            "action": "update_vendor_status",
            "entity_type": "vendor",
            "entity_id": vendor_id,
            "changes": update_fields,
            "performed_by": current_user["user_id"]
        })
        
        return {"message": f"Vendor {new_status} successfully", "status": actual_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )