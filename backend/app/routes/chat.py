"""Chat API routes for customer-delivery boy communication."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ..db.connection import get_database
from ..utils.dependencies import get_current_user
from ..utils.errors import AppError, ErrorCode

router = APIRouter(prefix="/api/chat", tags=["chat"])
security = HTTPBearer()

class ChatMessage:
    def __init__(self, **data):
        self.order_id = data.get('order_id')
        self.sender_id = data.get('sender_id')
        self.sender_type = data.get('sender_type')  # 'customer' or 'delivery_boy'
        self.recipient_id = data.get('recipient_id')
        self.recipient_type = data.get('recipient_type')
        self.message = data.get('message')
        self.timestamp = data.get('timestamp', datetime.utcnow())
        self.status = data.get('status', 'sent')  # sent, delivered, read
        self.message_type = data.get('message_type', 'text')  # text, image, location

@router.post("/send-message")
async def send_message(
    message_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Send a message between customer and delivery boy."""
    try:
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
        
        # Validate order exists and sender is authorized
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Check authorization (customer must be order owner, delivery boy must be assigned)
        if sender_type == 'customer':
            if str(order.get('customer_id')) != sender_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only chat about your own orders"
                )
        elif sender_type == 'delivery_boy':
            if str(order.get('assigned_delivery_boy')) != sender_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only chat about orders assigned to you"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only customers and delivery boys can use chat"
            )
        
        # Determine recipient based on sender type and order data
        if sender_type == 'customer':
            recipient_type = 'delivery_boy'
            # Try multiple fields for delivery boy ID
            recipient_id = (order.get('assigned_delivery_boy') or 
                          order.get('delivery_boy_id') or 
                          order.get('delivery_boy'))
            if recipient_id:
                recipient_id = str(recipient_id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No delivery boy assigned to this order yet"
                )
        else:  # delivery_boy
            recipient_type = 'customer'
            # Try multiple fields for customer ID
            recipient_id = (order.get('customer_id') or 
                          order.get('user_id') or 
                          order.get('customer'))
            if recipient_id:
                recipient_id = str(recipient_id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer information not found for this order"
                )
        
        print(f"Message creation - Sender: {sender_id} ({sender_type}), Recipient: {recipient_id} ({recipient_type})")
        
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
            'message_type': 'text'
        }
        
        # Insert message
        result = await db.chat_messages.insert_one(message_doc)
        
        # Return the created message
        message_doc['id'] = str(result.inserted_id)
        message_doc['_id'] = str(result.inserted_id)
        message_doc['timestamp'] = message_doc['timestamp'].isoformat()
        
        return message_doc
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.get("/messages/{order_id}")
async def get_messages(
    order_id: str,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get chat messages for an order."""
    try:
        # Get user info
        user_id = current_user.get('user_id') or current_user.get('sub')
        user_role = current_user.get('role')
        
        # Validate order exists and user is authorized
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Check authorization
        if user_role == 'customer':
            if str(order.get('customer_id')) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view chat for your own orders"
                )
        elif user_role == 'delivery_boy':
            if str(order.get('assigned_delivery_boy')) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view chat for orders assigned to you"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only customers and delivery boys can access chat"
            )
        
        # Get messages
        messages = []
        async for message in db.chat_messages.find(
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
        print(f"Error fetching messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )

@router.patch("/messages/{message_id}/status")
async def update_message_status(
    message_id: str,
    status_data: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update message status (delivered, read)."""
    try:
        print(f"Updating message status - message_id: {message_id}, status_data: {status_data}")
        
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
        existing_message = await db.chat_messages.find_one({"_id": message_object_id})
        if not existing_message:
            print(f"Message not found with ID: {message_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        print(f"Found message: {existing_message}")
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
        
        if user_role == 'customer':
            customer_id = str(order.get('customer_id') or order.get('user_id'))
            is_order_participant = customer_id == user_id
        elif user_role == 'delivery_boy':
            delivery_boy_id = str(order.get('assigned_delivery_boy') or order.get('delivery_boy_id') or order.get('delivery_boy'))
            is_order_participant = delivery_boy_id == user_id
        
        if not is_order_participant:
            print(f"User {user_id} ({user_role}) is not a participant in order {existing_message.get('order_id')}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update messages for this order"
            )
        
        # For 'read' status, only the recipient should be able to mark it
        # But we'll be flexible about who can mark as read based on the order participation
        if new_status == 'read':
            # If current user is delivery boy and message sender is customer, allow
            # If current user is customer and message sender is delivery boy, allow
            message_sender_id = str(existing_message.get('sender_id'))
            can_mark_read = (
                (user_role == 'delivery_boy' and existing_message.get('sender_type') == 'customer') or
                (user_role == 'customer' and existing_message.get('sender_type') == 'delivery_boy') or
                (message_sender_id != user_id)  # Can mark read if not the sender
            )
            
            if not can_mark_read:
                print(f"User {user_id} ({user_role}) cannot mark their own message as read")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot mark your own messages as read"
                )
        
        print(f"Authorization passed - updating message status to {new_status}")
        
        # Update message status
        result = await db.chat_messages.update_one(
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
        print(f"Error updating message status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update message status: {str(e)}"
        )

@router.get("/conversations")
async def get_conversations(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get list of active conversations for a user."""
    try:
        user_id = current_user.get('user_id') or current_user.get('sub')
        user_role = current_user.get('role')
        
        # Get orders with conversations
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
                "$group": {
                    "_id": "$order_id",
                    "last_message": {"$last": "$message"},
                    "last_timestamp": {"$last": "$timestamp"},
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
            {"$sort": {"last_timestamp": -1}}
        ]
        
        conversations = []
        async for conv in db.chat_messages.aggregate(pipeline):
            # Get order details
            order = await db.orders.find_one({"_id": ObjectId(conv["_id"])})
            if order:
                # Get recipient info
                if user_role == 'customer':
                    recipient_id = order.get('assigned_delivery_boy')
                    # Get delivery boy name
                    delivery_boy = await db.delivery_boys_collection.find_one(
                        {"_id": ObjectId(recipient_id)} if recipient_id else {}
                    )
                    recipient_name = delivery_boy.get('name', 'Delivery Boy') if delivery_boy else 'Delivery Boy'
                else:
                    recipient_id = order.get('customer_id')
                    # Get customer name from shipping address or user
                    recipient_name = 'Customer'
                    if order.get('shipping_address'):
                        addr = order['shipping_address']
                        recipient_name = f"{addr.get('first_name', '')} {addr.get('last_name', '')}".strip()
                
                conversations.append({
                    'order_id': conv['_id'],
                    'order_number': order.get('order_number', f"#{conv['_id'][:8]}"),
                    'recipient_id': recipient_id,
                    'recipient_name': recipient_name,
                    'last_message': conv['last_message'],
                    'last_timestamp': conv['last_timestamp'].isoformat(),
                    'unread_count': conv['unread_count'],
                    'order_status': order.get('status', 'unknown')
                })
        
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
        
    except Exception as e:
        print(f"Error fetching conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversations: {str(e)}"
        )

@router.get("/debug/user-info")
async def debug_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Debug endpoint to check current user information."""
    try:
        return {
            "user_id": current_user.get('user_id') or current_user.get('sub'),
            "role": current_user.get('role'),
            "full_user_data": current_user
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/message/{message_id}")
async def debug_message(
    message_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Debug endpoint to check message details."""
    try:
        user_id = current_user.get('user_id') or current_user.get('sub')
        print(f"Debug - Current user_id: {user_id}")
        print(f"Debug - Current user role: {current_user.get('role')}")
        
        message = await db.chat_messages.find_one({"_id": ObjectId(message_id)})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Get order info
        order = await db.orders.find_one({"_id": ObjectId(message.get('order_id'))})
        
        # Convert ObjectId to string for JSON serialization
        message['_id'] = str(message['_id'])
        if message.get('timestamp'):
            message['timestamp'] = message['timestamp'].isoformat()
        if message.get('updated_at'):
            message['updated_at'] = message['updated_at'].isoformat()
        
        order_info = None
        if order:
            order_info = {
                'customer_id': str(order.get('customer_id', '')),
                'user_id': str(order.get('user_id', '')),
                'assigned_delivery_boy': str(order.get('assigned_delivery_boy', '')),
                'delivery_boy_id': str(order.get('delivery_boy_id', '')),
                'delivery_boy': str(order.get('delivery_boy', ''))
            }
        
        return {
            "message": message,
            "order_info": order_info,
            "current_user_id": user_id,
            "current_user_role": current_user.get('role'),
            "is_sender": message.get('sender_id') == user_id,
            "is_recipient": message.get('recipient_id') == user_id
        }
        
    except Exception as e:
        print(f"Error in debug endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug failed: {str(e)}"
        )