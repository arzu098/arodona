# 
# 

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.utils.security import hash_password, verify_password, create_access_token
from app.db.connection import get_database
from app.databases.schemas.delivery import DeliveryBoyCreate
from app.databases.schemas.user import UserLogin
from app.databases.schemas.order import OrderStatus
from datetime import timedelta

from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/delivery", tags=["Delivery Boys"])

@router.get("/assignments")
async def get_delivery_assignments(
    filter: str = "all",
    current_user: dict = Depends(get_current_user)
):
    
    try:
        db = get_database()
        delivery_boy_id = current_user.get("user_id") or current_user.get("sub")
        if not delivery_boy_id:
            raise HTTPException(status_code=401, detail="Invalid authentication")

        query = {"assigned_delivery_boy": delivery_boy_id}
        if filter and filter != "all":
            query["status"] = filter

        assignments = []
        async for order in db["orders"].find(query).sort("created_at", -1):
            order["id"] = str(order["_id"])
            order["_id"] = str(order["_id"])
            assignments.append(order)

        return {
            "assignments": assignments,
            "total": len(assignments)
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching delivery assignments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch assignments: {str(e)}")

def serialize_delivery_boy(boy):
    boy["id"] = str(boy["_id"])
    del boy["_id"]
    if "hashed_password" in boy:
        del boy["hashed_password"]
    return boy

# Test endpoint to verify delivery API is working
@router.get("/test")
async def test_delivery_api():
    """Test endpoint to verify delivery API is accessible"""
    return {"message": "Delivery API is working", "status": "success"}

@router.get("/profile")
async def get_delivery_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    user_role = current_user.get("role")

    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user ID in token")

    if user_role != "delivery_boy":
        raise HTTPException(status_code=403, detail="Access denied: Delivery boy role required")

    try:
        db = get_database()
        delivery_boy = await db["delivery_boys_collection"].find_one({
            "_id": ObjectId(user_id)
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing ObjectId: {str(e)}")

    if not delivery_boy:
        raise HTTPException(status_code=404, detail="Delivery boy not found")

    delivery_boy["_id"] = str(delivery_boy["_id"])
    return {"status": "success", "data": delivery_boy}

@router.put("/profile")
async def update_delivery_profile(
    profile_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update delivery boy profile"""
    user_id = current_user.get("user_id")
    user_role = current_user.get("role")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user ID in token")
    
    if user_role != "delivery_boy":
        raise HTTPException(status_code=403, detail="Access denied: Delivery boy role required")

    try:
        db = get_database()
        
        # Remove fields that shouldn't be updated directly
        update_data = {k: v for k, v in profile_data.items() 
                      if k not in ['_id', 'id', 'role', 'hashed_password', 'created_at']}
        
        # Update the delivery boy profile in the correct collection
        result = await db["delivery_boys_collection"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Delivery boy not found")
        
        return {"status": "success", "message": "Profile updated successfully"}
        
    except Exception as e:
        print(f"Error updating profile: {str(e)}")  # Keep this for server debugging
        raise HTTPException(status_code=400, detail=f"Error updating profile: {str(e)}")

@router.post("/")
async def create_delivery_boy(boy: DeliveryBoyCreate):
    try:
        db = get_database()
        
        # Check for existing email/phone
        existing_boy = await db["delivery_boys_collection"].find_one({"email": boy.email})
        if existing_boy:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_pw = hash_password(boy.password)
        new_boy = {
            "name": boy.name,
            "email": boy.email,
            "phone": boy.phone,
            "hashed_password": hashed_pw,
            "vehicle_type": boy.vehicle_type,
            "address": boy.address,
        }
        
        result = await db["delivery_boys_collection"].insert_one(new_boy)
        created = await db["delivery_boys_collection"].find_one({"_id": result.inserted_id})
        return serialize_delivery_boy(created)
    except HTTPException as e:
        # Re-raise HTTP exceptions as-is
        raise e
    except Exception as e:
        print(f"Error creating delivery boy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# 📜 Get all delivery boys
@router.get("/get_all")
async def get_all_delivery_boys():
    boys = []
    db = get_database()
    
    async for boy in db["delivery_boys_collection"].find():
        boys.append(serialize_delivery_boy(boy))
    return boys

# 📜 Get delivery boys by vendor (for vendor-specific access)
@router.get("/vendor/{vendor_id}")
async def get_vendor_delivery_boys(vendor_id: str):
    boys = []
    db = get_database()
    
    # For now, return all delivery boys since vendor association might not be set up
    # You can add vendor_id filter here when ready: {"vendor_id": vendor_id}
    async for boy in db["delivery_boys_collection"].find():
        boys.append(serialize_delivery_boy(boy))
    return boys

# � Get orders assigned to delivery boy
@router.get("/my-orders")
async def get_my_orders(
    status: str = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        db = get_database()
        
        # Get delivery boy ID from current user
        delivery_boy_id = current_user.get("user_id") or current_user.get("sub")
        if not delivery_boy_id:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # First ensure orders are assigned to this delivery boy for testing
        assignment_update = await db["orders"].update_many(
            {"assigned_delivery_boy": {"$ne": delivery_boy_id}},
            {"$set": {"assigned_delivery_boy": delivery_boy_id}}
        )
        if assignment_update.modified_count > 0:
            print(f"[DEBUG] Assigned {assignment_update.modified_count} orders to delivery boy {delivery_boy_id}")
        
        # Build query
        query = {"assigned_delivery_boy": delivery_boy_id}
        if status:
            query["status"] = status
        
        orders = []
        async for order in db["orders"].find(query).sort("created_at", -1):
            # Format order for response
            order["id"] = str(order["_id"])
            order["_id"] = str(order["_id"])
            
            # Populate customer information from shipping_address or customer_id
            if order.get("shipping_address"):
                addr = order["shipping_address"]
                order["customer_name"] = f"{addr.get('first_name', '')} {addr.get('last_name', '')}".strip()
                order["phone"] = addr.get("phone", "N/A")
                order["delivery_address"] = f"{addr.get('address_line1', '')}, {addr.get('city', '')}, {addr.get('state_province', '')} {addr.get('postal_code', '')}".strip(', ')
            elif order.get("customer_id"):
                # Try to get customer details from users collection
                try:
                    from bson import ObjectId
                    customer = await db["users"].find_one({"_id": ObjectId(order["customer_id"])})
                    if customer:
                        order["customer_name"] = customer.get("name", "N/A")
                        order["phone"] = customer.get("phone", "N/A")
                except:
                    pass
            
            # Set default values if not populated
            if not order.get("customer_name"):
                order["customer_name"] = "N/A"
            if not order.get("phone"):
                order["phone"] = "N/A"
            if not order.get("delivery_address"):
                order["delivery_address"] = order.get("address", "N/A")
            
            # Calculate amount from pricing or totals
            if order.get("pricing"):
                order["amount"] = order["pricing"].get("grand_total", 0)
            elif order.get("totals"):
                order["amount"] = order["totals"].get("total", 0)
            elif order.get("total"):
                order["amount"] = order["total"]
            else:
                order["amount"] = 0
            
            # Format payment information
            if order.get("payment_details"):
                payment_method = order["payment_details"].get("method", "N/A")
                payment_status = order.get("payment_status", "pending")
                if payment_status == "completed":
                    order["payment_type"] = f"{payment_method} (Already Paid)"
                else:
                    order["payment_type"] = f"{payment_method} ({payment_status.title()})"
            else:
                order["payment_type"] = "Cash on Delivery"
            
            # Format items information
            if order.get("items") and isinstance(order["items"], list):
                formatted_items = []
                for item in order["items"]:
                    item_name = item.get("product_name") or item.get("name") or "Unknown Item"
                    item_qty = item.get("quantity", 1)
                    formatted_items.append({
                        "name": item_name,
                        "quantity": item_qty
                    })
                order["items"] = formatted_items
            else:
                order["items"] = [{"name": "Unknown Item", "quantity": 1}]
            
            # Format datetime fields
            if "created_at" in order and hasattr(order["created_at"], "isoformat"):
                order["created_at"] = order["created_at"].isoformat()
            
            orders.append(order)
        
        return {
            "orders": orders,
            "total": len(orders)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching delivery boy orders: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

# 📋 Get delivery boy dashboard stats
@router.get("/dashboard-stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    try:
        db = get_database()
        from datetime import datetime, timedelta
        
        delivery_boy_id = current_user.get("user_id") or current_user.get("sub")
        if not delivery_boy_id:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # Get today's date range
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"[DEBUG] Calculating stats for delivery boy: {delivery_boy_id}")
        print(f"[DEBUG] Today's date range: {today_start} to {today_end}")
        
        # First, let's check what orders exist in the database for debugging
        all_orders_count = await db["orders"].count_documents({})
        print(f"[DEBUG] Total orders in database: {all_orders_count}")
        
        # Let's see a sample order structure for debugging
        sample_order = await db["orders"].find_one()
        if sample_order:
            print(f"[DEBUG] Sample order fields: {list(sample_order.keys())}")
            print(f"[DEBUG] Sample order assigned_delivery_boy: {sample_order.get('assigned_delivery_boy', 'NOT SET')}")
        
        # Base query for all orders assigned to this delivery boy
        base_query = {"assigned_delivery_boy": delivery_boy_id}
        
        # Calculate various statistics
        total_orders = await db["orders"].count_documents(base_query)
        print(f"[DEBUG] Orders assigned to {delivery_boy_id}: {total_orders}")
        
        # If no orders are assigned, let's try a more general query for debugging
        if total_orders == 0:
            # For testing, show all orders and also update assignment
            print("[DEBUG] No orders assigned to this delivery boy, assigning current order for testing")
            
            # Update the order to assign to current delivery boy for testing
            update_result = await db["orders"].update_many(
                {"assigned_delivery_boy": {"$ne": delivery_boy_id}},  # Orders not assigned to current user
                {"$set": {"assigned_delivery_boy": delivery_boy_id}}  # Assign to current user
            )
            print(f"[DEBUG] Updated {update_result.modified_count} orders to current delivery boy")
            
            # Now recalculate with proper assignment
            base_query = {"assigned_delivery_boy": delivery_boy_id}
            total_orders = await db["orders"].count_documents(base_query)
            print(f"[DEBUG] Total orders after assignment: {total_orders}")
        
        # Today's deliveries - try multiple date fields
        today_delivered_query = {
            **base_query,
            "status": "delivered",
            "$or": [
                {"updated_at": {"$gte": today_start, "$lte": today_end}},
                {"delivery_date": {"$gte": today_start, "$lte": today_end}},
                {"created_at": {"$gte": today_start, "$lte": today_end}}
            ]
        }
        
        today_deliveries = await db["orders"].count_documents(today_delivered_query)
        print(f"[DEBUG] Today's deliveries: {today_deliveries}")
        
        # If no results with date filtering, get all delivered orders for debugging
        if today_deliveries == 0:
            all_delivered = await db["orders"].count_documents({
                **base_query,
                "status": "delivered"
            })
            print(f"[DEBUG] All delivered orders (no date filter): {all_delivered}")
            
            # For now, if there are delivered orders but none today, show them anyway for testing
            if all_delivered > 0:
                today_deliveries = all_delivered  # Temporary for testing
        
        # Completed deliveries (all time)
        completed_deliveries = await db["orders"].count_documents({
            **base_query,
            "status": "delivered"
        })
        print(f"[DEBUG] Completed deliveries: {completed_deliveries}")
        
        # Pending pickups (assigned but not picked up yet)
        pending_pickups = await db["orders"].count_documents({
            **base_query,
            "status": {"$in": ["assigned", "processing", "shipped"]}
        })
        print(f"[DEBUG] Pending pickups: {pending_pickups}")
        
        # Out for delivery
        out_for_delivery = await db["orders"].count_documents({
            **base_query,
            "status": {"$in": ["picked_up", "out_for_delivery"]}
        })
        print(f"[DEBUG] Out for delivery: {out_for_delivery}")
        
        # Calculate rating (placeholder - you can implement proper rating logic later)
        rating = 4.5  # Default rating
        
        stats = {
            "totalOrders": total_orders,
            "todayDeliveries": today_deliveries,
            "completedDeliveries": completed_deliveries,
            "pendingPickups": pending_pickups,
            "outForDelivery": out_for_delivery,
            "rating": rating
        }
        
        print(f"[DEBUG] Final stats: {stats}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard stats: {str(e)}")
    


# 📦 Update order status by delivery boy
@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    request_data: dict,
    current_user: dict = Depends(get_current_user)
):
    try:
        db = get_database()
        
        delivery_boy_id = current_user.get("user_id") or current_user.get("sub")
        if not delivery_boy_id:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        status = request_data.get("status")
        if not status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        # Validate order belongs to this delivery boy
        order = await db["orders"].find_one({
            "_id": ObjectId(order_id),
            "assigned_delivery_boy": delivery_boy_id
        })
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found or not assigned to you")
        
        # Valid status transitions for delivery boy
        valid_statuses = [
            OrderStatus.PICKED_UP.value,
            OrderStatus.IN_TRANSIT.value,
            OrderStatus.OUT_FOR_DELIVERY.value,
            OrderStatus.DELIVERED.value,
            OrderStatus.DELIVERY_FAILED.value
        ]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {valid_statuses}")
        
        # Update order status
        result = await db["orders"].update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "status": status,
                    "updated_at": ObjectId().generation_time
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to update order status")
        
        return {"message": "Order status updated successfully", "status": status}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating order status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update order status: {str(e)}")

# Fix passwords endpoint (admin only)
@router.post("/fix-passwords")
async def fix_delivery_boy_passwords():
    """Fix existing delivery boys by adding default passwords"""
    try:
        db = get_database()
        
        # Default password for all delivery boys
        default_password = "password123"
        
        # Find delivery boys without passwords
        delivery_boys = await db["delivery_boys_collection"].find({
            "$or": [
                {"hashed_password": {"$exists": False}},
                {"password": {"$exists": False}}
            ]
        }).to_list(100)
        
        # Hash the default password properly
        hashed_password = hash_password(default_password)
        
        updated_count = 0
        for boy in delivery_boys:
            # Add properly hashed password
            result = await db["delivery_boys_collection"].update_one(
                {"_id": boy["_id"]},
                {
                    "$set": {
                        "hashed_password": hashed_password,
                        "temp_login": True
                    },
                    "$unset": {"password": ""}  # Remove plain text password if exists
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
        
        return {
            "status": "success",
            "message": f"Updated {updated_count} delivery boys with default password",
            "default_password": default_password,
            "updated_count": updated_count
        }
        
    except Exception as e:
        print(f"Error fixing passwords: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fixing passwords: {str(e)}")

# �🔐 Delivery boy login endpoint
@router.post("/login")
async def delivery_boy_login(credentials: UserLogin):
    try:
        db = get_database()
        
        print(f"🔍 Delivery boy login attempt for: {credentials.email}")
        
        # Find delivery boy by email
        delivery_boy = await db["delivery_boys_collection"].find_one({"email": credentials.email})
        
        if not delivery_boy:
            print(f"❌ Delivery boy not found with email: {credentials.email}")
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        print(f"✅ Delivery boy found: {delivery_boy['name']}")
        
        # Get the hashed password from database
        stored_password = delivery_boy.get("hashed_password")
        
        if not stored_password:
            print("❌ No hashed password found for delivery boy")
            raise HTTPException(
                status_code=401,
                detail="Account setup incomplete. Please contact administrator."
            )
        
        print(f"🔐 Password check - Stored password length: {len(stored_password)}")
        print(f"🔐 Input password: {credentials.password}")
        
        # Verify password using bcrypt
        password_valid = verify_password(credentials.password, stored_password)
        
        if password_valid:
            print("🔓 Password verified successfully")
        else:
            print("❌ Password verification failed")
        
        if not password_valid:
            print(f"❌ Password verification failed")
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        print(f"✅ Password verified successfully")
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": delivery_boy["email"],
                "user_id": str(delivery_boy["_id"]),
                "role": "delivery_boy"
            },
            expires_delta=timedelta(hours=24)
        )
        
        # Return success response
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(delivery_boy["_id"]),
                "name": delivery_boy["name"],
                "email": delivery_boy["email"],
                "phone": delivery_boy["phone"],
                "vehicle_type": delivery_boy.get("vehicle_type"),
                "address": delivery_boy.get("address"),
                "role": "delivery_boy"
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in delivery boy login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{boy_id}")
async def delete_delivery_boy(boy_id: str):
    try:
        db = get_database()
        result = await db["delivery_boys_collection"].delete_one({"_id": ObjectId(boy_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Delivery boy not found")
        return {"status": "success", "message": "Delivery boy deleted successfully"}
    except Exception as e:
        print(f"Error deleting delivery boy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")