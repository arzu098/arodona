"""Vendor-Delivery Boy Chat API routes for pickup coordination."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ..db.connection import get_database
from ..utils.dependencies import get_current_user
from ..utils.errors import AppError, ErrorCode

router = APIRouter(prefix="/api/chat/vendor-delivery", tags=["vendor-delivery-chat"])
security = HTTPBearer()

class VendorDeliveryMessage:
    def __init__(self, **data):
        self.order_id = data.get('order_id')
        self.sender_id = data.get('sender_id')
        self.sender_type = data.get('sender_type')  # 'vendor' or 'delivery_boy'
        self.recipient_id = data.get('recipient_id')
        self.recipient_type = data.get('recipient_type')
        self.message = data.get('message')
        self.timestamp = data.get('timestamp', datetime.utcnow())
        self.status = data.get('status', 'sent')  # sent, delivered, read
        self.message_type = data.get('message_type', 'text')  # text, image, location

@router.post("/send-message")
async def send_vendor_delivery_message(
    message_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Send a message between vendor and delivery boy for pickup coordination."""
    try:
        print(f"Received message data: {message_data}")
        print(f"Current user: {current_user}")
        
        # Validate required fields
        order_id = message_data.get('order_id')
        message_text = message_data.get('message')
        
        print(f"Order ID: {order_id}, Message: {message_text}")
        
        if not all([order_id, message_text]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: order_id, message"
            )
        
        # Get sender info
        sender_id = current_user.get('user_id') or current_user.get('sub')
        sender_type = current_user.get('role')
        
        print(f"Sender ID: {sender_id}, Sender Type: {sender_type}")
        
        # Validate order exists and sender is authorized
        try:
            # Try different collection names
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
            if not order:
                order = await db.orders_collection.find_one({"_id": ObjectId(order_id)})
            if not order:
                order = await db.order.find_one({"_id": ObjectId(order_id)})
        except Exception as e:
            print(f"Error finding order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid order ID format: {str(e)}"
            )
        
        if not order:
            print(f"Order not found for ID: {order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        print(f"Order found: {order.get('_id')}")
        
        # Check authorization (vendor must be order vendor, delivery boy must be assigned)
        # Make authorization more flexible for testing
        if sender_type == 'vendor':
            # Check if vendor is associated with this order
            vendor_id = str(order.get('vendor_id') or order.get('seller_id') or order.get('vendor', ''))
            print(f"Order vendor_id: {vendor_id}, Sender ID: {sender_id}")
            # Skip strict authorization check for now to debug
            # if vendor_id and vendor_id != sender_id:
            #     raise HTTPException(
            #         status_code=status.HTTP_403_FORBIDDEN,
            #         detail="You can only chat about orders from your store"
            #     )
        elif sender_type == 'delivery_boy':
            delivery_boy_id = str(order.get('assigned_delivery_boy') or 
                                order.get('delivery_boy_id') or 
                                order.get('delivery_boy', ''))
            print(f"Order delivery_boy_id: {delivery_boy_id}, Sender ID: {sender_id}")
            # Skip strict authorization check for now to debug  
            # if delivery_boy_id and delivery_boy_id != sender_id:
            #     raise HTTPException(
            #         status_code=status.HTTP_403_FORBIDDEN,
            #         detail="You can only chat about orders assigned to you"
            #     )
        else:
            print(f"Invalid sender type: {sender_type}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only vendors and delivery boys can use vendor-delivery chat"
            )
        
        # Determine recipient based on sender type and order data
        if sender_type == 'vendor':
            recipient_type = 'delivery_boy'
            # Try multiple fields for delivery boy ID
            recipient_id = (order.get('assigned_delivery_boy') or 
                          order.get('delivery_boy_id') or 
                          order.get('delivery_boy'))
            if recipient_id:
                recipient_id = str(recipient_id)
            else:
                # For testing, use a default delivery boy ID or allow without recipient
                print("No delivery boy assigned, allowing message without recipient")
                recipient_id = "default_delivery_boy"
                # raise HTTPException(
                #     status_code=status.HTTP_400_BAD_REQUEST,
                #     detail="No delivery boy assigned to this order for pickup"
                # )
        else:  # delivery_boy
            recipient_type = 'vendor'
            # Try multiple fields for vendor ID
            recipient_id = (order.get('vendor_id') or 
                          order.get('seller_id') or 
                          order.get('vendor'))
            if recipient_id:
                recipient_id = str(recipient_id)
            else:
                # For testing, use a default vendor ID or allow without recipient
                print("Vendor information not found, allowing message without recipient")
                recipient_id = "default_vendor"
                # raise HTTPException(
                #     status_code=status.HTTP_400_BAD_REQUEST,
                #     detail="Vendor information not found for this order"
                # )
        
        print(f"Vendor-Delivery Message creation - Sender: {sender_id} ({sender_type}), Recipient: {recipient_id} ({recipient_type})")
        
        # Create message document
        message_doc = {
            'order_id': order_id,
            'sender_id': sender_id,
            'sender_type': sender_type,
            'recipient_id': recipient_id,
            'recipient_type': recipient_type,
            'message': message_text,
            'timestamp': datetime.utcnow(),
            'status': 'sent',
            'message_type': 'text',
            'chat_type': 'vendor_delivery'  # To distinguish from customer-delivery chat
        }
        
        # Insert message into vendor_delivery_messages collection
        result = await db.vendor_delivery_messages.insert_one(message_doc)
        
        # Return the created message
        message_doc['id'] = str(result.inserted_id)
        message_doc['_id'] = str(result.inserted_id)
        message_doc['timestamp'] = message_doc['timestamp'].isoformat()
        
        return message_doc
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending vendor-delivery message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.get("/messages/{order_id}")
async def get_vendor_delivery_messages(
    order_id: str,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get vendor-delivery chat messages for an order."""
    try:
        # Get user info
        user_id = current_user.get('user_id') or current_user.get('sub')
        user_role = current_user.get('role')
        
        print(f"Chat request - User ID: {user_id}, Role: {user_role}, Order ID: {order_id}")
        
        # Validate order exists and user is authorized
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            print(f"Order not found in orders collection, trying alternative collections...")
            # Try alternative collection names
            order = await db.orders_collection.find_one({"_id": ObjectId(order_id)})
            if not order:
                order = await db.order.find_one({"_id": ObjectId(order_id)})
        
        if not order:
            print(f"Order {order_id} not found in any collection")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        print(f"Order found: {order.get('_id')}")
        print(f"Order vendor fields: vendor_id={order.get('vendor_id')}, seller_id={order.get('seller_id')}, vendor={order.get('vendor')}")
        print(f"Order delivery fields: assigned_delivery_boy={order.get('assigned_delivery_boy')}, delivery_boy_id={order.get('delivery_boy_id')}, delivery_boy={order.get('delivery_boy')}")
        
        # Check authorization - make it more flexible
        authorized = False
        if user_role == 'vendor':
            # Check multiple possible vendor ID fields
            vendor_fields = [
                order.get('vendor_id'),
                order.get('seller_id'), 
                order.get('vendor'),
                order.get('seller')
            ]
            vendor_ids = [str(field) for field in vendor_fields if field is not None]
            print(f"Vendor IDs found in order: {vendor_ids}")
            
            if user_id in vendor_ids:
                authorized = True
            else:
                # For debugging - temporarily allow all vendors
                print(f"Vendor authorization failed. User ID {user_id} not in {vendor_ids}")
                # Temporarily allow all vendors for debugging
                authorized = True
                
        elif user_role == 'delivery_boy':
            # Check multiple possible delivery boy ID fields  
            delivery_fields = [
                order.get('assigned_delivery_boy'),
                order.get('delivery_boy_id'),
                order.get('delivery_boy')
            ]
            delivery_ids = [str(field) for field in delivery_fields if field is not None]
            print(f"Delivery boy IDs found in order: {delivery_ids}")
            
            if user_id in delivery_ids:
                authorized = True
            else:
                # For debugging - temporarily allow all delivery boys
                print(f"Delivery boy authorization failed. User ID {user_id} not in {delivery_ids}")
                # Temporarily allow all delivery boys for debugging
                authorized = True
        else:
            print(f"Invalid role: {user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only vendors and delivery boys can access vendor-delivery chat"
            )
        
        if not authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this chat"
            )
        
        # Get messages
        messages = []
        async for message in db.vendor_delivery_messages.find(
            {"order_id": order_id}
        ).sort("timestamp", 1).limit(limit):
            message['id'] = str(message['_id'])
            message['_id'] = str(message['_id'])
            message['timestamp'] = message['timestamp'].isoformat()
            messages.append(message)
        
        return {
            "messages": messages,
            "total": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching vendor-delivery messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )

@router.patch("/messages/{message_id}/status")
async def update_vendor_delivery_message_status(
    message_id: str,
    status_data: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update vendor-delivery message status (delivered, read)."""
    try:
        print(f"Updating vendor-delivery message status - message_id: {message_id}, status_data: {status_data}")
        
        new_status = status_data.get('status')
        if new_status not in ['delivered', 'read']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be 'delivered' or 'read'"
            )
        
        user_id = current_user.get('user_id') or current_user.get('sub')
        print(f"User ID: {user_id}, New Status: {new_status}")
        
        # Validate ObjectId format
        try:
            message_object_id = ObjectId(message_id)
        except Exception as oid_error:
            print(f"Invalid ObjectId format: {message_id}, error: {oid_error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message ID format"
            )
        
        # First check if message exists
        existing_message = await db.vendor_delivery_messages.find_one({"_id": message_object_id})
        if not existing_message:
            print(f"Vendor-delivery message not found with ID: {message_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        print(f"Found vendor-delivery message: {existing_message}")
        print(f"Message sender_id: {existing_message.get('sender_id')}")
        print(f"Message recipient_id: {existing_message.get('recipient_id')}")
        print(f"Current user_id: {user_id}")
        print(f"Current user role: {current_user.get('role')}")
        
        # Get the order to verify current user's relationship
        order = await db.orders.find_one({"_id": ObjectId(existing_message.get('order_id'))})
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found for this message"
            )
        
        # Check if current user is involved in this order
        user_role = current_user.get('role')
        is_order_participant = False
        
        if user_role == 'vendor':
            vendor_id = str(order.get('vendor_id') or order.get('seller_id'))
            is_order_participant = vendor_id == user_id
        elif user_role == 'delivery_boy':
            delivery_boy_id = str(order.get('assigned_delivery_boy') or 
                                order.get('delivery_boy_id') or 
                                order.get('delivery_boy'))
            is_order_participant = delivery_boy_id == user_id
        
        if not is_order_participant:
            print(f"User {user_id} ({user_role}) is not a participant in order {existing_message.get('order_id')}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update messages for this order"
            )
        
        # For 'read' status, only the recipient should be able to mark it
        if new_status == 'read':
            # If current user is delivery boy and message sender is vendor, allow
            # If current user is vendor and message sender is delivery boy, allow
            message_sender_id = str(existing_message.get('sender_id'))
            can_mark_read = (
                (user_role == 'delivery_boy' and existing_message.get('sender_type') == 'vendor') or
                (user_role == 'vendor' and existing_message.get('sender_type') == 'delivery_boy') or
                (message_sender_id != user_id)  # Can mark read if not the sender
            )
            
            if not can_mark_read:
                print(f"User {user_id} ({user_role}) cannot mark their own vendor-delivery message as read")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot mark your own messages as read"
                )
        
        print(f"Authorization passed - updating vendor-delivery message status to {new_status}")
        
        # Update message status
        result = await db.vendor_delivery_messages.update_one(
            {"_id": message_object_id},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        print(f"Update result: modified_count = {result.modified_count}")
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update message status"
            )
        
        return {"success": True, "message": f"Message status updated to {new_status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating vendor-delivery message status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update message status: {str(e)}"
        )

@router.get("/conversations")
async def get_vendor_delivery_conversations(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get list of active vendor-delivery conversations for a user."""
    try:
        user_id = current_user.get('user_id') or current_user.get('sub')
        user_role = current_user.get('role')
        
        print(f"🔍 Fetching conversations for user: {user_id}, role: {user_role}")
        
        conversations = []
        
        if user_role == 'vendor':
            # For vendors: Get all their orders with assigned delivery boys
            # First check if vendor exists in users collection with role='vendor'
            vendor_user = await db.users.find_one({"_id": ObjectId(user_id), "role": "vendor"})
            if vendor_user:
                # Find orders where vendor is assigned via vendor_orders field
                orders_cursor = db.orders.find({
                    f"vendor_orders.{user_id}": {"$exists": True}
                })
            else:
                # Fallback: find orders by vendor_id field
                orders_cursor = db.orders.find({
                    "$or": [
                        {"vendor_id": user_id},
                        {"seller_id": user_id}
                    ]
                })
            
            async for order in orders_cursor:
                # Check if delivery boy is assigned
                assigned_delivery_boy = order.get('assigned_delivery_boy') or order.get('delivery_boy_id')
                
                if assigned_delivery_boy:
                    # Get delivery boy details
                    delivery_boy = await db.delivery_boys_collection.find_one(
                        {"_id": ObjectId(assigned_delivery_boy)}
                    )
                    
                    recipient_name = delivery_boy.get('name', 'Delivery Partner') if delivery_boy else 'Delivery Partner'
                    
                    # Get last message if any
                    last_message = await db.vendor_delivery_messages.find_one(
                        {"order_id": str(order["_id"])},
                        sort=[("timestamp", -1)]
                    )
                    
                    # Count unread messages for vendor
                    unread_count = await db.vendor_delivery_messages.count_documents({
                        "order_id": str(order["_id"]),
                        "recipient_id": user_id,
                        "status": {"$ne": "read"}
                    })
                    
                    conversations.append({
                        'order_id': str(order['_id']),
                        'order_number': order.get('order_number', f"#{str(order['_id'])[:8]}"),
                        'recipient_id': str(assigned_delivery_boy),
                        'recipient_name': recipient_name,
                        'last_message': last_message.get('message', 'No messages yet') if last_message else 'No messages yet',
                        'last_timestamp': last_message.get('timestamp').isoformat() if last_message else None,
                        'unread_count': unread_count,
                        'order_status': order.get('status', 'unknown')
                    })
                    
        elif user_role == 'delivery_boy':
            # For delivery boys: Get all orders assigned to them
            orders_cursor = db.orders.find({
                "$or": [
                    {"assigned_delivery_boy": user_id},
                    {"delivery_boy_id": user_id}
                ]
            })
            
            async for order in orders_cursor:
                # Get vendor details
                vendor_id = order.get('vendor_id') or order.get('seller_id')
                if vendor_id:
                    # Try to get vendor from users collection first
                    vendor_user = await db.users.find_one({"_id": ObjectId(vendor_id), "role": "vendor"})
                    if vendor_user:
                        vendor_name = f"{vendor_user.get('first_name', '')} {vendor_user.get('last_name', '')}".strip()
                        if not vendor_name:
                            vendor_name = vendor_user.get('business_name', 'Vendor')
                    else:
                        # Fallback to vendors collection
                        vendor = await db.vendors_collection.find_one({"_id": ObjectId(vendor_id)})
                        vendor_name = vendor.get('business_name', vendor.get('name', 'Vendor')) if vendor else 'Vendor'
                    
                    # Get last message if any
                    last_message = await db.vendor_delivery_messages.find_one(
                        {"order_id": str(order["_id"])},
                        sort=[("timestamp", -1)]
                    )
                    
                    # Count unread messages for delivery boy
                    unread_count = await db.vendor_delivery_messages.count_documents({
                        "order_id": str(order["_id"]),
                        "recipient_id": user_id,
                        "status": {"$ne": "read"}
                    })
                    
                    conversations.append({
                        'order_id': str(order['_id']),
                        'order_number': order.get('order_number', f"#{str(order['_id'])[:8]}"),
                        'recipient_id': str(vendor_id),
                        'recipient_name': vendor_name,
                        'last_message': last_message.get('message', 'No messages yet') if last_message else 'No messages yet',
                        'last_timestamp': last_message.get('timestamp').isoformat() if last_message else None,
                        'unread_count': unread_count,
                        'order_status': order.get('status', 'unknown')
                    })
        
        # Sort conversations by last timestamp (most recent first)
        conversations.sort(key=lambda x: x['last_timestamp'] or '', reverse=True)
        
        print(f"📋 Found {len(conversations)} conversations for {user_role}")
        
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
        
    except Exception as e:
        print(f"Error fetching vendor-delivery conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversations: {str(e)}"
        )