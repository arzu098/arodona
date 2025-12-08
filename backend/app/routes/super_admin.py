from fastapi import APIRouter, HTTPException, Depends, status, Query
from app.databases.schemas.user import (
    SuperAdminInitialSetup, 
    SuperAdminCreateUser, 
    AdminCreateVendor,
    UserResponse,
    RegisterResponse
)
from app.databases.repositories.user import UserRepository
from app.db.connection import get_database
from app.utils.security import get_current_user, get_password_hash
from app.config import SUPER_ADMIN_SECRET_KEY
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from pydantic import BaseModel, EmailStr
import os

router = APIRouter(prefix="/api/super-admin", tags=["Super Admin"])

# Additional Pydantic models for super admin operations
class UserUpdateRequest(BaseModel):
    """Schema for updating user by super admin"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class VendorUpdateRequest(BaseModel):
    """Schema for updating vendor by super admin"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    approval_status: Optional[str] = None
    is_active: Optional[bool] = None

class SystemSettings(BaseModel):
    """Schema for system settings"""
    site_name: Optional[str] = None
    site_description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    tax_rate: Optional[float] = None
    shipping_cost: Optional[float] = None
    free_shipping_threshold: Optional[float] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    allow_registrations: Optional[bool] = None
    require_email_verification: Optional[bool] = None
    max_cart_items: Optional[int] = None
    session_timeout: Optional[int] = None
    enable_vendor_registration: Optional[bool] = None
    vendor_auto_approve: Optional[bool] = None
    min_password_length: Optional[int] = None
    max_upload_size_mb: Optional[int] = None

async def get_user_repository() -> UserRepository:
    """Dependency to get user repository"""
    db = get_database()
    return UserRepository(db)

async def verify_super_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify that the current user has super_admin role"""
    if current_user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin privileges required"
        )
    return current_user

@router.get("/dashboard")
async def get_super_admin_dashboard_stats(
    current_user: dict = Depends(verify_super_admin)
):
    """
    Get comprehensive dashboard statistics for Super Admin
    """
    db = get_database()
    
    try:
        # Count users by role
        total_users = await db.users.count_documents({})
        customers = await db.users.count_documents({"role": "customer"})
        vendors = await db.users.count_documents({"role": "vendor"})
        admins = await db.users.count_documents({"role": "admin"})
        
        # Get recent users (last 10 registrations)
        recent_users_cursor = db.users.find({}).sort("created_at", -1).limit(10)
        recent_users = []
        async for user in recent_users_cursor:
            recent_users.append({
                "id": str(user["_id"]),
                "email": user.get("email"),
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "role": user.get("role", "customer"),
                "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
                "is_active": user.get("is_active", user.get("status") == "active")
            })
        
        return {
            "total_users": total_users,
            "customers": customers,
            "vendors": vendors,
            "admins": admins,
            "recent_users": recent_users
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard stats: {str(e)}"
        )


@router.get("/users")
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(verify_super_admin)
):
    """
    List all users with pagination and filters (Super Admin only)
    """
    db = get_database()
    
    try:
        # Build query
        query = {}
        
        # Role filter
        if role:
            query["role"] = role
        
        # Status filter
        if status:
            if status == "active":
                query["$or"] = [
                    {"is_active": True},
                    {"status": "active"}
                ]
            elif status == "inactive":
                query["$or"] = [
                    {"is_active": False},
                    {"status": "inactive"}
                ]
        
        # Search filter (email, name)
        if search:
            query["$or"] = [
                {"email": {"$regex": search, "$options": "i"}},
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}}
            ]
        
        # Date range filter
        if start_date or end_date:
            date_query = {}
            if start_date:
                try:
                    date_query["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except:
                    pass
            if end_date:
                try:
                    # Add one day to include the end date
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) + timedelta(days=1)
                    date_query["$lt"] = end_dt
                except:
                    pass
            if date_query:
                query["created_at"] = date_query
        
        # Get total count
        total = await db.users.count_documents(query)
        
        # For admins, we need to count how many vendors they created
        if role == "admin":
            # Build aggregation pipeline
            pipeline = [
                {"$match": query},
                {
                    "$lookup": {
                        "from": "users",
                        "let": {"admin_id": "$_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$and": [
                                            {"$eq": ["$role", "vendor"]},
                                            {"$eq": ["$created_by", "$$admin_id"]}
                                        ]
                                    }
                                }
                            },
                            {"$count": "count"}
                        ],
                        "as": "vendor_stats"
                    }
                },
                {
                    "$addFields": {
                        "vendor_count": {
                            "$ifNull": [
                                {"$arrayElemAt": ["$vendor_stats.count", 0]},
                                0
                            ]
                        }
                    }
                },
                {"$sort": {"created_at": -1}},
                {"$skip": skip},
                {"$limit": limit}
            ]
            
            users_cursor = db.users.aggregate(pipeline)
            users = []
            
            async for user in users_cursor:
                users.append({
                    "id": str(user["_id"]),
                    "email": user.get("email"),
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                    "phone": user.get("phone"),
                    "role": user.get("role", "customer"),
                    "is_active": user.get("is_active", user.get("status") == "active"),
                    "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
                    "vendor_count": user.get("vendor_count", 0)
                })
        else:
            # Get users with pagination (no vendor count needed)
            users_cursor = db.users.find(query).skip(skip).limit(limit).sort("created_at", -1)
            users = []
            
            async for user in users_cursor:
                users.append({
                    "id": str(user["_id"]),
                    "email": user.get("email"),
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                    "phone": user.get("phone"),
                    "role": user.get("role", "customer"),
                    "is_active": user.get("is_active", user.get("status") == "active"),
                    "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
                })
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "users": users
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: SuperAdminCreateUser,
    current_user: dict = Depends(verify_super_admin)
):
    """
    Create a new user (Super Admin only)
    """
    db = get_database()
    
    try:
        # Validate role
        if user_data.role not in ["customer", "vendor", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Allowed: customer, vendor, admin"
            )
        
        # Check if user exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user document
        user_doc = {
            "email": user_data.email,
            "password_hash": get_password_hash(user_data.password),
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "phone": user_data.phone,
            "role": user_data.role,
            "is_active": True,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": ObjectId(current_user["user_id"])  # Track who created this user
        }
        
        result = await db.users.insert_one(user_doc)
        user_doc["id"] = str(result.inserted_id)
        
        return {
            "message": f"{user_data.role.title()} created successfully",
            "user": {
                "id": str(result.inserted_id),
                "email": user_data.email,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "phone": user_data.phone,
                "role": user_data.role,
                "is_active": True,
                "created_at": user_doc["created_at"].isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    current_user: dict = Depends(verify_super_admin)
):
    """
    Update a user (Super Admin only)
    """
    db = get_database()
    
    try:
        # Validate ObjectId
        try:
            object_id = ObjectId(user_id)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )
        
        # Get user
        user = await db.users.find_one({"_id": object_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent modifying super admin
        if user.get("role") == "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify super admin users"
            )
        
        # Build update document
        update_doc = {"updated_at": datetime.utcnow()}
        
        if update_data.email is not None:
            # Check if new email already exists
            existing = await db.users.find_one({
                "email": update_data.email,
                "_id": {"$ne": object_id}
            })
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            update_doc["email"] = update_data.email
        
        if update_data.first_name is not None:
            update_doc["first_name"] = update_data.first_name
        if update_data.last_name is not None:
            update_doc["last_name"] = update_data.last_name
        if update_data.phone is not None:
            update_doc["phone"] = update_data.phone
        if update_data.role is not None:
            if update_data.role not in ["customer", "vendor", "admin"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role"
                )
            update_doc["role"] = update_data.role
        if update_data.is_active is not None:
            update_doc["is_active"] = update_data.is_active
            update_doc["status"] = "active" if update_data.is_active else "inactive"
        
        # Update user
        await db.users.update_one(
            {"_id": object_id},
            {"$set": update_doc}
        )
        
        # Get updated user
        updated_user = await db.users.find_one({"_id": object_id})
        
        return {
            "message": "User updated successfully",
            "user": {
                "id": str(updated_user["_id"]),
                "email": updated_user.get("email"),
                "first_name": updated_user.get("first_name", ""),
                "last_name": updated_user.get("last_name", ""),
                "phone": updated_user.get("phone"),
                "role": updated_user.get("role", "customer"),
                "is_active": updated_user.get("is_active", updated_user.get("status") == "active"),
                "created_at": updated_user.get("created_at").isoformat() if updated_user.get("created_at") else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.post("/setup", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def setup_initial_super_admin(
    setup_data: SuperAdminInitialSetup,
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Create the initial Super Admin account
    This endpoint should only be used once to set up the system
    """
    # Verify secret key
    expected_secret = os.getenv("SUPER_ADMIN_SECRET_KEY", "SUPER_SECRET_ADMIN_KEY_2024")
    if setup_data.secret_key != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret key"
        )
    
    # Check if super admin already exists
    super_admin_count = await repo.count_users_by_role("super_admin")
    if super_admin_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Super Admin already exists. Only one Super Admin is allowed."
        )
    
    # Check if user already exists
    if await repo.user_exists(setup_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create super admin
    user = await repo.create_user(
        email=setup_data.email,
        password=setup_data.password,
        first_name=setup_data.first_name,
        last_name=setup_data.last_name,
        phone=setup_data.phone,
        role="super_admin"
    )
    
    return {
        "message": "Super Admin created successfully",
        "user": repo.format_user_response(user)
    }

@router.post("/create-admin", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    admin_data: SuperAdminCreateUser,
    current_user: dict = Depends(verify_super_admin),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Create a new admin user (Super Admin only)
    """
    # Only allow creating admin, vendor, or customer roles
    if admin_data.role not in ["admin", "vendor", "customer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Super Admin can create: admin, vendor, customer"
        )
    
    # Check if user already exists
    if await repo.user_exists(admin_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create the user
    user = await repo.create_user(
        email=admin_data.email,
        password=admin_data.password,
        first_name=admin_data.first_name,
        last_name=admin_data.last_name,
        phone=admin_data.phone,
        role=admin_data.role
    )
    
    return {
        "message": f"{admin_data.role.title()} created successfully by Super Admin",
        "user": repo.format_user_response(user)
    }

@router.get("/users", response_model=dict)
async def list_all_users(
    skip: int = 0,
    limit: int = 50,
    role: str = None,
    current_user: dict = Depends(verify_super_admin),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    List all users with optional role filter (Super Admin only)
    """
    if role:
        users, total = await repo.get_users_by_role(role, skip, limit)
    else:
        users, total = await repo.get_all_users(skip, limit)
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "users": [repo.format_user_response(user) for user in users]
    }

@router.get("/dashboard-stats")
async def get_super_admin_dashboard_stats(
    current_user: dict = Depends(verify_super_admin),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Get comprehensive dashboard statistics for Super Admin
    """
    stats = {
        "total_users": await repo.count_all_users(),
        "total_customers": await repo.count_users_by_role("customer"),
        "total_vendors": await repo.count_users_by_role("vendor"), 
        "total_admins": await repo.count_users_by_role("admin"),
        "total_super_admins": await repo.count_users_by_role("super_admin"),
        "recent_registrations": await repo.get_recent_users(limit=10)
    }
    
    return stats

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(verify_super_admin)
):
    """
    Delete a user (Super Admin only)
    """
    db = get_database()
    
    try:
        # Validate ObjectId
        try:
            object_id = ObjectId(user_id)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )
        
        # Get user
        user = await db.users.find_one({"_id": object_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent deleting super admin
        if user.get("role") == "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete super admin users"
            )
        
        # Prevent self-deletion
        if user_id == current_user.get("user_id") or str(object_id) == current_user.get("user_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Delete user
        await db.users.delete_one({"_id": object_id})
        
        # If vendor, also delete vendor profile
        if user.get("role") == "vendor":
            await db.vendor_profiles.delete_many({"user_id": object_id})
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.get("/vendors")
async def get_all_vendors(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    account_status: Optional[str] = Query(None),
    business_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(verify_super_admin)
):
    """
    List all vendors with pagination and filters (Super Admin only)
    """
    db = get_database()
    
    try:
        # Build aggregation pipeline for proper filtering
        pipeline = []
        
        # Match vendors
        match_stage = {"role": "vendor"}
        
        # Account status filter (active/inactive)
        if account_status:
            if account_status == "active":
                match_stage["is_active"] = True
            elif account_status == "inactive":
                match_stage["is_active"] = False
        
        # Date range filter
        if start_date or end_date:
            date_query = {}
            if start_date:
                try:
                    date_query["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except:
                    pass
            if end_date:
                try:
                    # Add one day to include the end date
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) + timedelta(days=1)
                    date_query["$lt"] = end_dt
                except:
                    pass
            if date_query:
                match_stage["created_at"] = date_query
        
        pipeline.append({"$match": match_stage})
        
        # Lookup vendor profiles
        pipeline.append({
            "$lookup": {
                "from": "vendor_profiles",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "vendor_profile"
            }
        })
        
        # Unwind vendor_profile (make it an object instead of array)
        pipeline.append({
            "$unwind": {
                "path": "$vendor_profile",
                "preserveNullAndEmptyArrays": True
            }
        })
        
        # Lookup who created this vendor
        pipeline.append({
            "$lookup": {
                "from": "users",
                "localField": "created_by",
                "foreignField": "_id",
                "as": "creator"
            }
        })
        
        pipeline.append({
            "$unwind": {
                "path": "$creator",
                "preserveNullAndEmptyArrays": True
            }
        })
        
        # Apply search filter after joining vendor_profile
        if search:
            pipeline.append({
                "$match": {
                    "$or": [
                        {"email": {"$regex": search, "$options": "i"}},
                        {"first_name": {"$regex": search, "$options": "i"}},
                        {"last_name": {"$regex": search, "$options": "i"}},
                        {"vendor_profile.business_name": {"$regex": search, "$options": "i"}}
                    ]
                }
            })
        
        # Apply approval status filter
        if status:
            if status == "pending":
                # Match vendors with no profile OR approval_status is pending
                pipeline.append({
                    "$match": {
                        "$or": [
                            {"vendor_profile.approval_status": "pending"},
                            {"vendor_profile": {"$exists": False}}
                        ]
                    }
                })
            else:
                # Match vendors with specific approval status
                pipeline.append({
                    "$match": {
                        "vendor_profile.approval_status": status
                    }
                })
        
        # Apply business type filter
        if business_type:
            pipeline.append({
                "$match": {
                    "vendor_profile.business_type": business_type
                }
            })
        
        # Get total count before pagination
        count_pipeline = pipeline.copy()
        count_pipeline.append({"$count": "total"})
        count_result = await db.users.aggregate(count_pipeline).to_list(1)
        total = count_result[0]["total"] if count_result else 0
        
        # Add sorting and pagination
        pipeline.append({"$sort": {"created_at": -1}})
        pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})
        
        # Execute aggregation
        vendors_cursor = db.users.aggregate(pipeline)
        vendors = []
        
        async for vendor in vendors_cursor:
            vendor_id = vendor["_id"]
            vendor_profile = vendor.get("vendor_profile")
            creator = vendor.get("creator")
            
            vendor_data = {
                "id": str(vendor_id),
                "email": vendor.get("email"),
                "first_name": vendor.get("first_name", ""),
                "last_name": vendor.get("last_name", ""),
                "phone": vendor.get("phone"),
                "is_active": vendor.get("is_active", vendor.get("status") == "active"),
                "created_at": vendor.get("created_at").isoformat() if vendor.get("created_at") else None,
                "created_by_name": None,
                "created_by_email": None,
                "vendor_profile": None
            }
            
            # Add creator information
            if creator and isinstance(creator, dict):
                vendor_data["created_by_name"] = f"{creator.get('first_name', '')} {creator.get('last_name', '')}".strip()
                vendor_data["created_by_email"] = creator.get("email")
            
            if vendor_profile and isinstance(vendor_profile, dict):
                vendor_data["vendor_profile"] = {
                    "business_name": vendor_profile.get("business_name"),
                    "business_type": vendor_profile.get("business_type"),
                    "business_description": vendor_profile.get("business_description"),
                    "contact_email": vendor_profile.get("contact_email"),
                    "contact_phone": vendor_profile.get("contact_phone"),
                    "approval_status": vendor_profile.get("approval_status", "pending")
                }
            
            vendors.append(vendor_data)
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "vendors": vendors
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vendors: {str(e)}"
        )


@router.put("/vendors/{vendor_id}")
async def update_vendor(
    vendor_id: str,
    update_data: VendorUpdateRequest,
    current_user: dict = Depends(verify_super_admin)
):
    """
    Update a vendor (Super Admin only)
    """
    db = get_database()
    
    try:
        # Validate ObjectId
        try:
            object_id = ObjectId(vendor_id)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid vendor ID"
            )
        
        # Get vendor
        vendor = await db.users.find_one({"_id": object_id, "role": "vendor"})
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        # Update user fields
        user_update = {"updated_at": datetime.utcnow()}
        
        if update_data.email is not None:
            existing = await db.users.find_one({
                "email": update_data.email,
                "_id": {"$ne": object_id}
            })
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            user_update["email"] = update_data.email
        
        if update_data.first_name is not None:
            user_update["first_name"] = update_data.first_name
        if update_data.last_name is not None:
            user_update["last_name"] = update_data.last_name
        if update_data.phone is not None:
            user_update["phone"] = update_data.phone
        if update_data.is_active is not None:
            user_update["is_active"] = update_data.is_active
            user_update["status"] = "active" if update_data.is_active else "inactive"
        
        await db.users.update_one({"_id": object_id}, {"$set": user_update})
        
        # Update vendor profile
        vendor_profile_update = {}
        
        if update_data.business_name is not None:
            vendor_profile_update["business_name"] = update_data.business_name
        if update_data.business_type is not None:
            vendor_profile_update["business_type"] = update_data.business_type
        if update_data.business_description is not None:
            vendor_profile_update["business_description"] = update_data.business_description
        if update_data.contact_email is not None:
            vendor_profile_update["contact_email"] = update_data.contact_email
        if update_data.contact_phone is not None:
            vendor_profile_update["contact_phone"] = update_data.contact_phone
        if update_data.approval_status is not None:
            if update_data.approval_status not in ["pending", "approved", "rejected"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid approval status"
                )
            vendor_profile_update["approval_status"] = update_data.approval_status
        
        if vendor_profile_update:
            vendor_profile_update["updated_at"] = datetime.utcnow()
            await db.vendor_profiles.update_one(
                {"user_id": object_id},
                {"$set": vendor_profile_update},
                upsert=True
            )
        
        return {"message": "Vendor updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vendor: {str(e)}"
        )

@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: str,
    new_role: str,
    current_user: dict = Depends(verify_super_admin),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Change a user's role (Super Admin only)
    """
    if new_role not in ["customer", "vendor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Allowed roles: customer, vendor, admin"
        )
    
    # Get user
    user = await repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent changing super admin roles
    if user.get("role") == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change Super Admin role"
        )
    
    # Update role
    updated_user = await repo.update_user(user_id, {"role": new_role})
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )
    
    return {
        "message": f"User role changed to {new_role}",
        "user": repo.format_user_response(updated_user)
    }


@router.delete("/vendors/{vendor_id}")
async def delete_vendor(
    vendor_id: str,
    current_user: dict = Depends(verify_super_admin)
):
    """
    Delete a vendor and their profile (Super Admin only)
    """
    db = get_database()
    
    try:
        # Validate ObjectId
        try:
            object_id = ObjectId(vendor_id)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid vendor ID"
            )
        
        # Get vendor
        vendor = await db.users.find_one({"_id": object_id, "role": "vendor"})
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        # Delete vendor user
        await db.users.delete_one({"_id": object_id})
        
        # Delete vendor profile
        await db.vendor_profiles.delete_many({"user_id": object_id})
        
        # Optionally delete vendor's products
        await db.products.delete_many({"vendor_id": str(object_id)})
        
        return {"message": "Vendor deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete vendor: {str(e)}"
        )


@router.get("/analytics")
async def get_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(verify_super_admin)
):
    """
    Get platform analytics (Super Admin only)
    """
    db = get_database()
    
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Total counts
        total_users = await db.users.count_documents({})
        total_vendors = await db.users.count_documents({"role": "vendor"})
        total_orders = await db.orders.count_documents({})
        
        # Calculate total revenue
        revenue_pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$total_amount"}
                }
            }
        ]
        revenue_result = await db.orders.aggregate(revenue_pipeline).to_list(1)
        total_revenue = revenue_result[0]["total"] if revenue_result else 0
        
        # Active users (logged in within last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = await db.users.count_documents({
            "last_login": {"$gte": thirty_days_ago}
        })
        
        # New users this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_this_month = await db.users.count_documents({
            "created_at": {"$gte": month_start}
        })
        
        # Orders this month
        orders_this_month = await db.orders.count_documents({
            "created_at": {"$gte": month_start}
        })
        
        # Revenue this month
        revenue_month_pipeline = [
            {"$match": {"created_at": {"$gte": month_start}}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$total_amount"}
                }
            }
        ]
        revenue_month_result = await db.orders.aggregate(revenue_month_pipeline).to_list(1)
        revenue_this_month = revenue_month_result[0]["total"] if revenue_month_result else 0
        
        # Top products by sales
        top_products_pipeline = [
            {
                "$group": {
                    "_id": "$product_id",
                    "sales": {"$sum": "$quantity"},
                    "revenue": {"$sum": "$total_amount"}
                }
            },
            {"$sort": {"sales": -1}},
            {"$limit": 5}
        ]
        top_products_cursor = db.order_items.aggregate(top_products_pipeline)
        top_products = []
        async for item in top_products_cursor:
            product = await db.products.find_one({"_id": ObjectId(item["_id"])})
            if product:
                top_products.append({
                    "name": product.get("name", "Unknown"),
                    "sales": item["sales"],
                    "revenue": item["revenue"]
                })
        
        # Top vendors by orders
        top_vendors_pipeline = [
            {
                "$group": {
                    "_id": "$vendor_id",
                    "orders": {"$sum": 1},
                    "revenue": {"$sum": "$total_amount"}
                }
            },
            {"$sort": {"orders": -1}},
            {"$limit": 5}
        ]
        top_vendors_cursor = db.orders.aggregate(top_vendors_pipeline)
        top_vendors = []
        async for item in top_vendors_cursor:
            if item["_id"]:
                vendor = await db.users.find_one({"_id": ObjectId(item["_id"])})
                vendor_profile = await db.vendor_profiles.find_one({"user_id": ObjectId(item["_id"])})
                if vendor:
                    top_vendors.append({
                        "name": vendor_profile.get("business_name", f"{vendor.get('first_name', '')} {vendor.get('last_name', '')}") if vendor_profile else f"{vendor.get('first_name', '')} {vendor.get('last_name', '')}",
                        "orders": item["orders"],
                        "revenue": item["revenue"]
                    })
        
        return {
            "total_users": total_users,
            "total_vendors": total_vendors,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "active_users": active_users,
            "new_users_this_month": new_users_this_month,
            "orders_this_month": orders_this_month,
            "revenue_this_month": revenue_this_month,
            "top_products": top_products,
            "top_vendors": top_vendors
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}"
        )


@router.post("/setup", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def setup_initial_super_admin(
    setup_data: SuperAdminInitialSetup
):
    """
    Create the initial Super Admin account
    This endpoint should only be used once to set up the system
    """
    db = get_database()
    
    try:
        # Verify secret key
        expected_secret = os.getenv("SUPER_ADMIN_SECRET_KEY", "SUPER_SECRET_ADMIN_KEY_2024")
        if setup_data.secret_key != expected_secret:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid secret key"
            )
        
        # Check if super admin already exists
        super_admin_count = await db.users.count_documents({"role": "super_admin"})
        if super_admin_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Super Admin already exists. Only one Super Admin is allowed."
            )
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": setup_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create super admin
        user_doc = {
            "email": setup_data.email,
            "password_hash": get_password_hash(setup_data.password),
            "first_name": setup_data.first_name,
            "last_name": setup_data.last_name,
            "phone": setup_data.phone,
            "role": "super_admin",
            "is_active": True,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.users.insert_one(user_doc)
        
        return {
            "message": "Super Admin created successfully",
            "user": {
                "id": str(result.inserted_id),
                "email": setup_data.email,
                "first_name": setup_data.first_name,
                "last_name": setup_data.last_name,
                "phone": setup_data.phone,
                "role": "super_admin",
                "created_at": user_doc["created_at"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create super admin: {str(e)}"
        )


@router.post("/create-admin", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    admin_data: SuperAdminCreateUser,
    current_user: dict = Depends(verify_super_admin)
):
    """
    Create a new admin user (Super Admin only)
    """
    db = get_database()
    
    try:
        # Only allow creating admin role through this endpoint
        if admin_data.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint is for creating admin users only"
            )
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": admin_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create the admin user
        user_doc = {
            "email": admin_data.email,
            "password_hash": get_password_hash(admin_data.password),
            "first_name": admin_data.first_name,
            "last_name": admin_data.last_name,
            "phone": admin_data.phone,
            "role": "admin",
            "is_active": True,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": ObjectId(current_user["user_id"])  # Track who created this admin
        }
        
        result = await db.users.insert_one(user_doc)
        
        return {
            "message": "Admin created successfully by Super Admin",
            "user": {
                "id": str(result.inserted_id),
                "email": admin_data.email,
                "first_name": admin_data.first_name,
                "last_name": admin_data.last_name,
                "phone": admin_data.phone,
                "role": "admin",
                "created_at": user_doc["created_at"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin: {str(e)}"
        )


@router.get("/activity-log")
async def get_activity_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    activity_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(verify_super_admin)
):
    """
    Get activity log for vendor and admin operations (Super Admin only)
    Shows which admin created which vendors with vendor details
    """
    db = get_database()
    
    try:
        # Build aggregation pipeline to get vendors with their creators
        pipeline = []
        
        # Match criteria - focus on vendors and admins
        match_stage = {}
        
        # Filter by activity type
        if activity_type:
            if activity_type in ["vendor_created", "vendor_updated", "vendor_deleted"]:
                match_stage["role"] = "vendor"
            elif activity_type in ["admin_created", "admin_deleted"]:
                match_stage["role"] = "admin"
        else:
            # By default show vendors and admins only
            match_stage["role"] = {"$in": ["vendor", "admin"]}
        
        # Date range filter
        if start_date or end_date:
            date_query = {}
            if start_date:
                try:
                    date_query["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except:
                    pass
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) + timedelta(days=1)
                    date_query["$lt"] = end_dt
                except:
                    pass
            if date_query:
                match_stage["created_at"] = date_query
        
        if match_stage:
            pipeline.append({"$match": match_stage})
        
        # Lookup creator information (the admin who created this vendor/user)
        pipeline.append({
            "$lookup": {
                "from": "users",
                "localField": "created_by",
                "foreignField": "_id",
                "as": "creator"
            }
        })
        
        pipeline.append({
            "$unwind": {
                "path": "$creator",
                "preserveNullAndEmptyArrays": True
            }
        })
        
        # Lookup vendor profile for vendors
        pipeline.append({
            "$lookup": {
                "from": "vendor_profiles",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "vendor_profile"
            }
        })
        
        pipeline.append({
            "$unwind": {
                "path": "$vendor_profile",
                "preserveNullAndEmptyArrays": True
            }
        })
        
        # Search filter
        if search:
            pipeline.append({
                "$match": {
                    "$or": [
                        {"email": {"$regex": search, "$options": "i"}},
                        {"first_name": {"$regex": search, "$options": "i"}},
                        {"last_name": {"$regex": search, "$options": "i"}},
                        {"vendor_profile.business_name": {"$regex": search, "$options": "i"}},
                        {"creator.email": {"$regex": search, "$options": "i"}},
                        {"creator.first_name": {"$regex": search, "$options": "i"}},
                        {"creator.last_name": {"$regex": search, "$options": "i"}}
                    ]
                }
            })
        
        # Get total count
        count_pipeline = pipeline.copy()
        count_pipeline.append({"$count": "total"})
        count_result = await db.users.aggregate(count_pipeline).to_list(1)
        total = count_result[0]["total"] if count_result else 0
        
        # Add sorting and pagination
        pipeline.append({"$sort": {"created_at": -1}})
        pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})
        
        # Execute aggregation
        activities_cursor = db.users.aggregate(pipeline)
        activities = []
        
        async for item in activities_cursor:
            creator = item.get("creator")
            vendor_profile = item.get("vendor_profile")
            user_role = item.get("role", "user")
            
            # Determine activity type
            activity_type_str = f"{user_role}_created"
            
            # Build detailed description
            description = f"Created {user_role} account"
            vendor_details = None
            
            if user_role == "vendor" and vendor_profile:
                business_name = vendor_profile.get('business_name', 'Unknown Business')
                business_type = vendor_profile.get('business_type', 'N/A')
                approval_status = vendor_profile.get('approval_status', 'pending')
                
                description = f"Created vendor '{business_name}' - {business_type} business (Status: {approval_status})"
                
                # Add vendor details
                vendor_details = {
                    "business_name": business_name,
                    "business_type": business_type,
                    "business_description": vendor_profile.get('business_description'),
                    "approval_status": approval_status,
                    "contact_email": vendor_profile.get('contact_email'),
                    "contact_phone": vendor_profile.get('contact_phone')
                }
            
            activity = {
                "activity_type": activity_type_str,
                "created_at": item.get("created_at").isoformat() if item.get("created_at") else None,
                "actor_name": None,
                "actor_email": None,
                "actor_role": None,
                "target_name": f"{item.get('first_name', '')} {item.get('last_name', '')}".strip(),
                "target_email": item.get("email"),
                "target_role": user_role,
                "description": description,
                "vendor_details": vendor_details
            }
            
            # Add creator information (the admin who created this vendor)
            if creator and isinstance(creator, dict):
                activity["actor_name"] = f"{creator.get('first_name', '')} {creator.get('last_name', '')}".strip()
                activity["actor_email"] = creator.get("email")
                activity["actor_role"] = creator.get("role", "unknown")
            else:
                # If no creator, it was self-registered or created by system
                activity["actor_name"] = "Self Registered"
                activity["actor_role"] = "system"
            
            activities.append(activity)
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "activities": activities
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activity log: {str(e)}"
        )