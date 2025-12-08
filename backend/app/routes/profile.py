from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId
from app.databases.schemas.user import UserUpdate, UserProfileResponse, UserResponse, AvatarUpdate
from app.databases.repositories.user import UserRepository
from app.db.connection import get_database
from app.utils.security import get_current_user
from app.utils.avatar_utils import save_user_avatar

router = APIRouter(prefix="/api/profile", tags=["User Profile"])

async def get_user_repository() -> UserRepository:
    """Dependency to get user repository"""
    db = get_database()
    return UserRepository(db)

@router.get("/me", response_model=UserResponse)
async def get_current_profile(current_user: dict = Depends(get_current_user), repo: UserRepository = Depends(get_user_repository)):
    """
    Get current user profile
    - Requires valid JWT token
    """
    user_id = current_user.get("user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Get raw user document from database
    user_doc = await repo.collection.find_one({"_id": ObjectId(user_id)})
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return repo.format_user_response(user_doc)

@router.put("/avatar", response_model=UserProfileResponse)
async def update_avatar(
    avatar_update: AvatarUpdate,
    current_user: dict = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Update user avatar
    - Requires valid JWT token
    - **avatar**: Base64 encoded image string
    """
    user_id = current_user.get("user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_doc = await repo.collection.find_one({"_id": ObjectId(user_id)})
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Save avatar and get path
    avatar_path = await save_user_avatar(avatar_update.avatar, user_id)
    
    # Update user with new avatar path
    from app.databases.schemas.users import UserUpdate as UserUpdateSchema
    update_data = UserUpdateSchema(avatar=avatar_path)
    success = await repo.update_user(user_id, update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update avatar"
        )
    
    # Get updated user document
    updated_user_doc = await repo.collection.find_one({"_id": ObjectId(user_id)})
    
    return {
        "message": "Avatar updated successfully",
        "user": repo.format_user_response(updated_user_doc)
    }
