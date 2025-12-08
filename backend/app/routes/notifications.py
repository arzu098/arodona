"""Notification routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.databases.repositories.notification import NotificationRepository
from app.databases.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationSettings,
    NotificationList
)
from app.utils.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("", response_model=NotificationResponse)
async def create_notification(
    data: NotificationCreate,
    user = Depends(get_current_user),
    repo: NotificationRepository = Depends()
):
    """Create new notification."""
    notification = await repo.create_notification(data.dict())
    return notification

@router.get("", response_model=NotificationList)
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = False,
    user = Depends(get_current_user),
    repo: NotificationRepository = Depends()
):
    """List user's notifications."""
    notifications, total, unread = await repo.list_notifications(
        str(user["_id"]),
        skip,
        limit,
        unread_only
    )
    return {
        "notifications": notifications,
        "total": total,
        "unread": unread,
        "skip": skip,
        "limit": limit
    }

@router.post("/read")
async def mark_notifications_read(
    notification_ids: List[str],
    user = Depends(get_current_user),
    repo: NotificationRepository = Depends()
):
    """Mark notifications as read."""
    marked = await repo.mark_read(notification_ids, str(user["_id"]))
    return {"marked_read": marked}

@router.post("/delivered")
async def mark_notifications_delivered(
    notification_ids: List[str],
    user = Depends(get_current_user),
    repo: NotificationRepository = Depends()
):
    """Mark notifications as delivered."""
    marked = await repo.mark_delivered(notification_ids, str(user["_id"]))
    return {"marked_delivered": marked}

@router.delete("/")
async def delete_notifications(
    notification_ids: List[str],
    user = Depends(get_current_user),
    repo: NotificationRepository = Depends()
):
    """Delete notifications."""
    deleted = await repo.delete_notifications(notification_ids, str(user["_id"]))
    return {"deleted": deleted}

@router.get("/settings", response_model=NotificationSettings)
async def get_notification_settings(
    user = Depends(get_current_user),
    repo: NotificationRepository = Depends()
):
    """Get user's notification settings."""
    settings = await repo.get_user_settings(str(user["_id"]))
    if not settings:
        # Return default settings
        return NotificationSettings()
    return NotificationSettings(**settings)

@router.put("/settings", response_model=NotificationSettings)
async def update_notification_settings(
    settings: NotificationSettings,
    user = Depends(get_current_user),
    repo: NotificationRepository = Depends()
):
    """Update user's notification settings."""
    updated = await repo.update_user_settings(str(user["_id"]), settings.dict())
    return NotificationSettings(**updated)