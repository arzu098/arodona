"""
Business and KYC verification endpoints.
Handles business registration and KYC document management.
"""

from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from typing import List
from app.databases.schemas.business import (
    BusinessRegistration, 
    BusinessResponse, 
    KYCDocumentUpload,
    KYCStatusResponse
)
from app.databases.repositories.user import UserRepository
from app.db.connection import get_database
from app.utils.security import get_current_user
from app.utils.image_upload import save_image
from datetime import datetime

router = APIRouter(prefix="/api/users", tags=["Business & KYC"])

async def get_user_repository() -> UserRepository:
    """Dependency to get user repository"""
    db = get_database()
    return UserRepository(db)

@router.post("/business/register", response_model=BusinessResponse)
async def register_business(
    business_data: BusinessRegistration,
    current_user: dict = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Register business details for a user
    - Business name and registration details
    - Tax information
    - Business address
    - Contact information
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Check if user already has business profile
        user = await repo.get_user_by_id(user_id)
        if user.get("business_details"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business profile already exists"
            )
        
        # Add business details to user
        business_info = business_data.dict()
        business_info["registration_date"] = datetime.utcnow()
        business_info["status"] = "pending"
        
        updated_user = await repo.add_business_details(user_id, business_info)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register business"
            )
        
        return {
            "message": "Business registered successfully",
            "business": business_info
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering business: {str(e)}"
        )

@router.post("/{user_id}/kyc", response_model=KYCStatusResponse)
async def upload_kyc_documents(
    user_id: str,
    document: KYCDocumentUpload,
    current_user: dict = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Upload KYC verification documents
    - ID proof (passport, driver's license)
    - Address proof
    - Business registration documents
    """
    try:
        # Check if user has permission
        if current_user.get("user_id") != user_id and current_user.get("role") not in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload KYC documents for this user"
            )
        
        # Save document
        file_url = await save_image(
            document.file,
            f"kyc/{user_id}",
            document.document_type
        )
        
        # Add document to user's KYC records
        kyc_doc = {
            "type": document.document_type,
            "url": file_url,
            "status": "pending",
            "uploaded_at": datetime.utcnow()
        }
        
        updated_user = await repo.add_kyc_document(user_id, kyc_doc)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload KYC document"
            )
        
        return {
            "message": "Document uploaded successfully",
            "document": kyc_doc
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )

@router.get("/{user_id}/kyc/status", response_model=KYCStatusResponse)
async def get_kyc_status(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Get KYC verification status
    - Document status (pending/approved/rejected)
    - Missing documents
    - Verification timeline
    """
    try:
        # Check if user has permission
        if current_user.get("user_id") != user_id and current_user.get("role") not in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view KYC status for this user"
            )
        
        # Get user's KYC details
        user = await repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        kyc_status = user.get("kyc_documents", [])
        
        return {
            "user_id": user_id,
            "documents": kyc_status,
            "status": "verified" if all(doc["status"] == "approved" for doc in kyc_status) else "pending",
            "last_updated": max((doc["uploaded_at"] for doc in kyc_status), default=None)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting KYC status: {str(e)}"
        )

@router.get("/{user_id}/activities", response_model=List[dict])
async def get_user_activities(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repository)
):
    """
    Get user activity logs
    - Login history
    - Order activities
    - Profile updates
    - KYC/Business updates
    """
    try:
        # Check if user has permission
        if current_user.get("user_id") != user_id and current_user.get("role") not in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view activities for this user"
            )
        
        # Get user activities
        activities = await repo.get_user_activities(user_id)
        
        return activities
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user activities: {str(e)}"
        )