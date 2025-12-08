from fastapi import APIRouter, HTTPException, Depends, status
from app.databases.schemas.user import AdminCreateVendor, RegisterResponse
from app.databases.repositories.user import UserRepository
from app.databases.repositories.vendor import VendorRepository
from app.db.connection import get_database
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/admin", tags=["Admin Management"])

async def get_user_repository() -> UserRepository:
    """Dependency to get user repository"""
    db = get_database()
    return UserRepository(db)

async def get_vendor_repository() -> VendorRepository:
    """Dependency to get vendor repository"""
    db = get_database()
    return VendorRepository(db)

async def verify_admin_or_super_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify that the current user has admin or super_admin role"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Super Admin privileges required"
        )
    return current_user

@router.post("/create-vendor", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor_account(
    vendor_data: AdminCreateVendor,
    current_user: dict = Depends(verify_admin_or_super_admin),
    user_repo: UserRepository = Depends(get_user_repository),
    vendor_repo: VendorRepository = Depends(get_vendor_repository)
):
    """
    Create a new vendor account (Admin or Super Admin only)
    This creates both the user account and vendor profile
    """
    # Check if user already exists
    if await user_repo.user_exists(vendor_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create vendor user account
    user = await user_repo.create_user(
        email=vendor_data.email,
        password=vendor_data.password,
        first_name=vendor_data.first_name,
        last_name=vendor_data.last_name,
        phone=vendor_data.phone,
        role="vendor"
    )
    
    # Create vendor profile if business details provided
    if vendor_data.business_name or vendor_data.business_type:
        vendor_profile_data = {
            "business_name": vendor_data.business_name or f"{vendor_data.first_name}'s Business",
            "business_type": vendor_data.business_type or "jewelry",
            "tax_id": "",
            "registration_number": "",
            "storefront": {
                "description": "Welcome to " + (vendor_data.business_name or f"{vendor_data.first_name}'s Store"),
                "logo": "",
                "banner": "",
                "policies": {
                    "return_policy": "30-day return policy",
                    "shipping_policy": "Free shipping on orders over $100",
                    "privacy_policy": "We respect your privacy"
                }
            }
        }
        
        try:
            await vendor_repo.create_vendor(str(user["_id"]), vendor_profile_data)
        except Exception as e:
            # If vendor profile creation fails, log it but don't fail the user creation
            print(f"Warning: Failed to create vendor profile: {e}")
    
    return {
        "message": f"Vendor account created successfully by {current_user.get('role', 'Admin')}",
        "user": user_repo.format_user_response(user)
    }

@router.get("/vendors")
async def list_vendors(
    skip: int = 0,
    limit: int = 50,
    status_filter: str = None,
    current_user: dict = Depends(verify_admin_or_super_admin),
    user_repo: UserRepository = Depends(get_user_repository),
    vendor_repo: VendorRepository = Depends(get_vendor_repository)
):
    """
    List all vendor accounts (Admin or Super Admin only)
    """
    # Get all vendor users
    vendor_users, total_users = await user_repo.get_users_by_role("vendor", skip, limit)
    
    # Format vendors with business information merged into flat structure
    vendors = []
    for user in vendor_users:
        vendor_profile = await vendor_repo.get_vendor_by_user(str(user["_id"]))
        
        # Create flat vendor object
        vendor_info = {
            "id": str(user["_id"]),
            "email": user.get("email"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "phone": user.get("phone"),
            "role": user.get("role"),
            "status": user.get("status", "inactive"),
            "avatar": user.get("avatar"),
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
            # Add business info from either user document or vendor profile
            "business_name": user.get("business_name") or (vendor_profile.get("business_name") if vendor_profile else None),
            "business_type": user.get("business_type") or (vendor_profile.get("business_type") if vendor_profile else None),
            "business_status": user.get("business_status", "pending")
        }
        vendors.append(vendor_info)
    
    return {
        "total": total_users,
        "skip": skip,
        "limit": limit,
        "vendors": vendors
    }

@router.get("/dashboard-stats")
async def get_admin_dashboard_stats(
    current_user: dict = Depends(verify_admin_or_super_admin),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get dashboard statistics for Admin
    """
    stats = {
        "total_users": await user_repo.count_all_users(),
        "total_customers": await user_repo.count_users_by_role("customer"),
        "total_vendors": await user_repo.count_users_by_role("vendor"),
        "pending_vendor_approvals": 0,  # Will be implemented with vendor approval system
        "recent_users": await user_repo.get_recent_users(limit=5)
    }
    
    # Only super admin can see admin count
    if current_user.get("role") == "super_admin":
        stats["total_admins"] = await user_repo.count_users_by_role("admin")
    
    return stats

@router.put("/vendors/{vendor_id}/status")
async def update_vendor_status(
    vendor_id: str,
    new_status: str,
    notes: str = "",
    current_user: dict = Depends(verify_admin_or_super_admin),
    vendor_repo: VendorRepository = Depends(get_vendor_repository)
):
    """
    Update vendor approval status (Admin or Super Admin only)
    """
    if new_status not in ["pending", "approved", "rejected", "suspended"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Allowed: pending, approved, rejected, suspended"
        )
    
    # Update vendor status
    updated_vendor = await vendor_repo.update_vendor_status(vendor_id, new_status, notes)
    if not updated_vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    return {
        "message": f"Vendor status updated to {new_status}",
        "vendor": vendor_repo.format_vendor_response(updated_vendor)
    }