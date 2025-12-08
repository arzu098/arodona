"""Message routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from app.databases.repositories.message import MessageRepository
from app.databases.schemas.message import (
    MessageCreate,
    MessageResponse,
    ThreadCreate,
    ThreadResponse,
    ThreadList
)
from app.utils.security import get_current_user
from app.utils.image_upload import upload_image

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/threads", response_model=ThreadResponse)
async def create_thread(
    data: ThreadCreate,
    user = Depends(get_current_user),
    repo: MessageRepository = Depends()
):
    """Create new message thread."""
    thread_data = data.dict()
    # Add current user to participants if not included
    if str(user["_id"]) not in thread_data["participants"]:
        thread_data["participants"].append(str(user["_id"]))
    return await repo.create_thread(thread_data)

@router.get("/threads", response_model=ThreadList)
async def list_threads(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user = Depends(get_current_user),
    repo: MessageRepository = Depends()
):
    """List user's message threads."""
    threads, total = await repo.get_user_threads(str(user["_id"]), skip, limit)
    return {
        "threads": threads,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    user = Depends(get_current_user),
    repo: MessageRepository = Depends()
):
    """Get thread details."""
    thread = await repo.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Check if user is participant
    if str(user["_id"]) not in thread["participants"]:
        raise HTTPException(status_code=403, detail="Not a thread participant")
    
    return thread

@router.get("/threads/{thread_id}/messages", response_model=dict)
async def list_thread_messages(
    thread_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user = Depends(get_current_user),
    repo: MessageRepository = Depends()
):
    """List messages in thread."""
    # Verify thread exists and user is participant
    thread = await repo.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    if str(user["_id"]) not in thread["participants"]:
        raise HTTPException(status_code=403, detail="Not a thread participant")
    
    messages, total = await repo.get_thread_messages(thread_id, skip, limit)
    return {
        "messages": messages,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.post("/threads/{thread_id}/messages", response_model=MessageResponse)
async def send_message(
    thread_id: str,
    data: MessageCreate,
    user = Depends(get_current_user),
    repo: MessageRepository = Depends()
):
    """Send message in thread."""
    # Verify thread exists and user is participant
    thread = await repo.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    if str(user["_id"]) not in thread["participants"]:
        raise HTTPException(status_code=403, detail="Not a thread participant")
    
    message_data = data.dict()
    message_data.update({
        "thread_id": thread_id,
        "sender_id": str(user["_id"])
    })
    return await repo.create_message(message_data)

@router.post("/threads/{thread_id}/attachments")
async def upload_attachment(
    thread_id: str,
    file: UploadFile = File(...),
    user = Depends(get_current_user),
    repo: MessageRepository = Depends()
):
    """Upload message attachment."""
    # Verify thread exists and user is participant
    thread = await repo.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    if str(user["_id"]) not in thread["participants"]:
        raise HTTPException(status_code=403, detail="Not a thread participant")
    
    attachment_url = await upload_image(file, "message_attachments")
    return {"url": attachment_url}

@router.post("/threads/{thread_id}/read")
async def mark_thread_read(
    thread_id: str,
    user = Depends(get_current_user),
    repo: MessageRepository = Depends()
):
    """Mark all messages in thread as read."""
    # Verify thread exists and user is participant
    thread = await repo.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    if str(user["_id"]) not in thread["participants"]:
        raise HTTPException(status_code=403, detail="Not a thread participant")
    
    marked = await repo.mark_messages_read(thread_id, str(user["_id"]))
    return {"marked_read": marked}

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    user = Depends(get_current_user),
    repo: MessageRepository = Depends()
):
    """Delete a message."""
    deleted = await repo.delete_message(message_id, str(user["_id"]))
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Message not found or not authorized to delete"
        )
    return {"deleted": True}

@router.get("/unread")
async def get_unread_count(
    user = Depends(get_current_user),
    repo: MessageRepository = Depends()
):
    """Get user's unread message count."""
    count = await repo.get_unread_count(str(user["_id"]))
    return {"unread_count": count}