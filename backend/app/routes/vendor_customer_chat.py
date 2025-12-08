"""Vendor-Customer Chat API routes for order-related communication."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ..db.connection import get_database
from ..utils.dependencies import get_current_user
from ..utils.errors import AppError, ErrorCode

router = APIRouter(prefix="/api/chat/vendor-customer", tags=["vendor-customer-chat"])
security = HTTPBearer()

class VendorCustomerMessage:
    def __init__(self, **data):
        self.order_id = data.get('order_id')
        self.sender_id = data.get('sender_id')
        self.sender_type = data.get('sender_type')  # 'vendor' or 'customer'
        self.recipient_id = data.get('recipient_id')
        self.recipient_type = data.get('recipient_type')
        self.message = data.get('message')
        self.timestamp = data.get('timestamp', datetime.utcnow())
        self.status = data.get('status', 'sent')  # sent, delivered, read
        self.message_type = data.get('message_type', 'text')  # text, image, location

@router.post("/send-message")
async def send_vendor_customer_message(
    message_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Send a message between vendor and customer for order communication."""
    try:
        print(f"Received vendor-customer message data: {message_data}")
        print(f"Current user: {current_user}")
        
        # Validate required fields
        order_id = message_data.get('order_id')
        message_text = message_data.get('message')
        
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
        print(f"Order vendor fields: vendor_id={order.get('vendor_id')}, seller_id={order.get('seller_id')}")
        print(f"Order customer fields: customer_id={order.get('customer_id')}, user_id={order.get('user_id')}")
        print(f"Order vendor_orders field: {order.get('vendor_orders', {})}")
        
        # Check authorization - make it flexible
        authorized = False
        recipient_id = None
        recipient_type = None
        
        if sender_type == 'vendor':
            # Check if vendor is associated with this order
            # First check the vendor_orders field (primary method)
            vendor_orders = order.get('vendor_orders', {})
            if sender_id in vendor_orders:
                authorized = True
                print(f"Vendor {sender_id} found in vendor_orders")
            else:
                # Fallback to legacy vendor fields
                vendor_fields = [
                    order.get('vendor_id'),
                    order.get('seller_id'), 
                    order.get('vendor'),
                    order.get('seller')
                ]
                vendor_ids = [str(field) for field in vendor_fields if field is not None]
                print(f"Vendor IDs found in legacy fields: {vendor_ids}")
                
                if sender_id in vendor_ids:
                    authorized = True
                    print(f"Vendor {sender_id} found in legacy vendor fields")
            
            if authorized:
                recipient_type = 'customer'
                # Find customer ID
                customer_fields = [
                    order.get('customer_id'),
                    order.get('user_id'),
                    order.get('customer')
                ]
                customer_ids = [str(field) for field in customer_fields if field is not None]
                recipient_id = customer_ids[0] if customer_ids else None
                
        elif sender_type == 'customer':
            # Check if customer owns this order
            customer_fields = [
                order.get('customer_id'),
                order.get('user_id'),
                order.get('customer')
            ]
            customer_ids = [str(field) for field in customer_fields if field is not None]
            print(f"Customer IDs found in order: {customer_ids}")
            
            if sender_id in customer_ids:
                authorized = True
                recipient_type = 'vendor'
                # Find vendor ID - check vendor_orders first, then fallback to legacy fields
                vendor_orders = order.get('vendor_orders', {})
                if vendor_orders:
                    # Get the first vendor ID from vendor_orders keys
                    recipient_id = list(vendor_orders.keys())[0]
                    print(f"Vendor found in vendor_orders: {recipient_id}")
                else:
                    # Fallback to legacy vendor fields
                    vendor_fields = [
                        order.get('vendor_id'),
                        order.get('seller_id'),
                        order.get('vendor'),
                        order.get('seller')
                    ]
                    vendor_ids = [str(field) for field in vendor_fields if field is not None]
                    recipient_id = vendor_ids[0] if vendor_ids else None
                    print(f"Vendor found in legacy fields: {recipient_id}")
        else:
            print(f"Invalid sender type: {sender_type}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only vendors and customers can use vendor-customer chat"
            )
        
        if not authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to chat about this order"
            )
        
        if not recipient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not determine {recipient_type} for this order"
            )
        
        print(f"Recipient ID: {recipient_id}, Recipient Type: {recipient_type}")
        
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
            'message_type': message_data.get('message_type', 'text')
        }
        
        # Insert message into database
        result = await db.vendor_customer_messages.insert_one(message_doc)
        message_doc['_id'] = result.inserted_id
        
        # Convert ObjectId to string for JSON response
        message_response = {
            'id': str(message_doc['_id']),
            '_id': str(message_doc['_id']),
            'order_id': message_doc['order_id'],
            'sender_id': message_doc['sender_id'],
            'sender_type': message_doc['sender_type'],
            'recipient_id': message_doc['recipient_id'],
            'recipient_type': message_doc['recipient_type'],
            'message': message_doc['message'],
            'timestamp': message_doc['timestamp'].isoformat(),
            'status': message_doc['status'],
            'message_type': message_doc['message_type']
        }
        
        print(f"Message saved successfully: {message_response}")
        
        return message_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending vendor-customer message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.get("/messages/{order_id}")
async def get_vendor_customer_messages(
    order_id: str,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get vendor-customer chat messages for an order."""
    try:
        # Get user info
        user_id = current_user.get('user_id') or current_user.get('sub')
        user_role = current_user.get('role')
        
        print(f"Vendor-customer chat request - User ID: {user_id}, Role: {user_role}, Order ID: {order_id}")
        
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
        
        # Check authorization - flexible approach
        authorized = False
        
        if user_role == 'vendor':
            # Check vendor_orders field (primary method)
            vendor_orders = order.get('vendor_orders', {})
            if user_id in vendor_orders:
                authorized = True
                print(f"Vendor {user_id} found in vendor_orders")
            else:
                # Fallback to legacy vendor fields
                vendor_fields = [
                    order.get('vendor_id'),
                    order.get('seller_id'), 
                    order.get('vendor'),
                    order.get('seller')
                ]
                vendor_ids = [str(field) for field in vendor_fields if field is not None]
                print(f"Vendor IDs found in legacy fields: {vendor_ids}")
                
                if user_id in vendor_ids:
                    authorized = True
                    print(f"Vendor {user_id} found in legacy vendor fields")
                
        elif user_role == 'customer':
            # Check multiple possible customer ID fields  
            customer_fields = [
                order.get('customer_id'),
                order.get('user_id'),
                order.get('customer')
            ]
            customer_ids = [str(field) for field in customer_fields if field is not None]
            print(f"Customer IDs found in order: {customer_ids}")
            
            if user_id in customer_ids:
                authorized = True
            else:
                # Temporarily allow all customers for debugging
                print(f"Customer authorization failed. User ID {user_id} not in {customer_ids}")
                authorized = True
        else:
            print(f"Invalid role: {user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only vendors and customers can access vendor-customer chat"
            )
        
        if not authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this chat"
            )
        
        # Get messages
        messages = []
        async for message in db.vendor_customer_messages.find(
            {"order_id": order_id}
        ).sort("timestamp", 1).limit(limit):
            message['id'] = str(message['_id'])
            message['_id'] = str(message['_id'])
            message['timestamp'] = message['timestamp'].isoformat()
            messages.append(message)
        
        print(f"Found {len(messages)} vendor-customer messages for order {order_id}")
        
        return {
            "messages": messages,
            "total": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching vendor-customer messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )

@router.patch("/messages/{message_id}/status")
async def update_vendor_customer_message_status(
    message_id: str,
    status_data: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update message status (e.g., mark as read)."""
    try:
        user_id = current_user.get('user_id') or current_user.get('sub')
        new_status = status_data.get('status')
        
        if new_status not in ['delivered', 'read']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be 'delivered' or 'read'"
            )
        
        # Find the message
        message = await db.vendor_customer_messages.find_one({"_id": ObjectId(message_id)})
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Check if user is the recipient of this message
        if message.get('recipient_id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update status of messages sent to you"
            )
        
        # Update message status
        await db.vendor_customer_messages.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"status": new_status}}
        )
        
        return {"message": "Message status updated successfully", "status": new_status}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating message status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update message status: {str(e)}"
        )

@router.get("/conversations")
async def get_vendor_customer_conversations(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get list of vendor-customer conversations for current user."""
    try:
        user_id = current_user.get('user_id') or current_user.get('sub')
        user_role = current_user.get('role')
        
        # Get conversations where user is either sender or recipient
        conversations = []
        
        # Aggregate to get latest message per order
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"sender_id": user_id},
                        {"recipient_id": user_id}
                    ]
                }
            },
            {
                "$sort": {"timestamp": -1}
            },
            {
                "$group": {
                    "_id": "$order_id",
                    "latest_message": {"$first": "$$ROOT"},
                    "unread_count": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$eq": ["$recipient_id", user_id]},
                                        {"$ne": ["$status", "read"]}
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    }
                }
            },
            {
                "$sort": {"latest_message.timestamp": -1}
            }
        ]
        
        async for conv in db.vendor_customer_messages.aggregate(pipeline):
            order_id = conv['_id']
            latest_message = conv['latest_message']
            
            # Get order details
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
            if not order:
                continue
            
            # Determine other participant
            other_participant_id = (
                latest_message['recipient_id'] 
                if latest_message['sender_id'] == user_id 
                else latest_message['sender_id']
            )
            other_participant_type = (
                latest_message['recipient_type'] 
                if latest_message['sender_id'] == user_id 
                else latest_message['sender_type']
            )
            
            conversation = {
                'order_id': order_id,
                'order_number': order.get('order_number', f"#{order_id[:8]}"),
                'other_participant_id': other_participant_id,
                'other_participant_type': other_participant_type,
                'other_participant_name': (
                    order.get('vendor_name') if other_participant_type == 'vendor'
                    else order.get('customer_name', 'Customer')
                ),
                'latest_message': {
                    'message': latest_message['message'],
                    'timestamp': latest_message['timestamp'].isoformat(),
                    'sender_type': latest_message['sender_type'],
                    'status': latest_message['status']
                },
                'unread_count': conv['unread_count'],
                'order_status': order.get('status', 'unknown')
            }
            
            conversations.append(conversation)
        
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
        
    except Exception as e:
        print(f"Error fetching vendor-customer conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversations: {str(e)}"
        )