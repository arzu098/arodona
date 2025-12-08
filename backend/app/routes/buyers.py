from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from datetime import datetime

from app.databases.schemas.buyer import (
    BuyerCreate,
    BuyerUpdate,
    BuyerResponse,
    BuyerDocument,
    BuyerVerification,
    BuyerCredit,
    BuyerCreditStatus,
    BuyerListResponse,
    BuyerType,
    BuyerVerificationStatus
)
from app.databases.repositories.buyer import BuyerRepository
from app.databases.repositories.user import UserRepository
from app.db.connection import get_database
from app.utils.security import get_current_user
from app.utils.image_upload import save_image

router = APIRouter(prefix="/api/buyers", tags=["Buyers"])

async def get_buyer_repository() -> BuyerRepository:
    """Dependency to get buyer repository"""
    db = get_database()
    return BuyerRepository(db)

async def get_user_repository() -> UserRepository:
    """Dependency to get user repository"""
    db = get_database()
    return UserRepository(db)

@router.post("", response_model=BuyerResponse, status_code=status.HTTP_201_CREATED)
async def register_buyer(
    buyer_data: BuyerCreate,
    current_user: dict = Depends(get_current_user),
    buyer_repo: BuyerRepository = Depends(get_buyer_repository)
):
    """
    Register as a buyer
    - Individual or business buyer
    - Optional business details
    - Optional preferences
    """
    # Check if user is already a buyer
    existing_buyer = await buyer_repo.get_buyer_by_user(current_user["user_id"])
    if existing_buyer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already registered as a buyer"
        )
    
    # Create buyer
    buyer = await buyer_repo.create_buyer(
        user_id=current_user["user_id"],
        data=buyer_data.dict()
    )
    
    return buyer_repo.format_buyer_response(buyer)

@router.get("/{buyer_id}", response_model=BuyerResponse)
async def get_buyer_profile(
    buyer_id: str,
    current_user: dict = Depends(get_current_user),
    buyer_repo: BuyerRepository = Depends(get_buyer_repository)
):
    """Get buyer profile"""
    buyer = await buyer_repo.get_buyer(buyer_id)
    if not buyer or buyer["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found"
        )
    return buyer_repo.format_buyer_response(buyer)

@router.put("/{buyer_id}/preferences", response_model=BuyerResponse)
async def update_preferences(
    buyer_id: str,
    update_data: BuyerUpdate,
    current_user: dict = Depends(get_current_user),
    buyer_repo: BuyerRepository = Depends(get_buyer_repository)
):
    """Update buyer preferences"""
    buyer = await buyer_repo.get_buyer(buyer_id)
    if not buyer or buyer["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found"
        )
    
    updated_buyer = await buyer_repo.update_buyer(buyer_id, update_data.dict(exclude_unset=True))
    return buyer_repo.format_buyer_response(updated_buyer)

@router.post("/{buyer_id}/verify", response_model=BuyerResponse)
async def verify_business_buyer(
    buyer_id: str,
    document: BuyerDocument,
    current_user: dict = Depends(get_current_user),
    buyer_repo: BuyerRepository = Depends(get_buyer_repository)
):
    """
    Submit business verification documents
    Required for business buyers
    """
    buyer = await buyer_repo.get_buyer(buyer_id)
    if not buyer or buyer["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found"
        )
        
    if buyer["type"] != BuyerType.BUSINESS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only business buyers need verification"
        )
        
    # Save document
    file_url = await save_image(
        document.file,
        f"buyers/{buyer_id}/documents",
        document.type
    )
    
    # Add document to buyer's records
    update_data = {
        "verification_documents": {"$push": {"type": document.type, "url": file_url}}
    }
    await buyer_repo.update_buyer(buyer_id, update_data)
    
    return {"url": file_url}

@router.get("/{buyer_id}/credit/status", response_model=BuyerCreditStatus)
async def get_credit_status(
    buyer_id: str,
    current_user: dict = Depends(get_current_user),
    buyer_repo: BuyerRepository = Depends(get_buyer_repository)
):
    """Get buyer credit status"""
    buyer = await buyer_repo.get_buyer(buyer_id)
    if not buyer or buyer["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found"
        )
        
    if not buyer.get("credit_status"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No credit history found"
        )
        
    return BuyerCreditStatus(**buyer["credit_status"])

@router.post("/{buyer_id}/credit/apply")
async def apply_for_credit(
    buyer_id: str,
    application: BuyerCredit,
    current_user: dict = Depends(get_current_user),
    buyer_repo: BuyerRepository = Depends(get_buyer_repository)
):
    """
    Apply for buyer credit
    Requires business verification
    """
    buyer = await buyer_repo.get_buyer(buyer_id)
    if not buyer or buyer["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found"
        )
        
    if buyer["type"] != BuyerType.BUSINESS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only business buyers can apply for credit"
        )
        
    if buyer.get("verification_status") != BuyerVerificationStatus.VERIFIED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business must be verified first"
        )
        
    # TODO: Process credit application
    return {
        "message": "Credit application received",
        "application_id": "temp_id"  # Replace with actual application ID
    }

@router.get("/{buyer_id}/orders")
async def get_buyer_orders(
    buyer_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    buyer_repo: BuyerRepository = Depends(get_buyer_repository)
):
    """Get buyer's order history"""
    buyer = await buyer_repo.get_buyer(buyer_id)
    if not buyer or buyer["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found"
        )
        
    # TODO: Implement order fetching from orders collection
    return {
        "total": 0,
        "orders": []
    }

@router.get("", response_model=BuyerListResponse)
async def list_buyers(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    type: Optional[BuyerType] = None,
    verification_status: Optional[BuyerVerificationStatus] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    buyer_repo: BuyerRepository = Depends(get_buyer_repository)
):
    """
    List all buyers (admin only)
    Optional filters:
    - type: Filter by buyer type
    - verification_status: Filter by verification status
    - search: Search by business name
    """
    # TODO: Add admin check
    # if not is_admin(current_user):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only admins can list buyers"
    #     )
    
    buyers, total = await buyer_repo.get_buyers(
        skip=skip,
        limit=limit,
        type=type,
        verification_status=verification_status,
        search=search
    )
    
    return {
        "total": total,
        "page": skip // limit + 1,
        "limit": limit,
        "buyers": [buyer_repo.format_buyer_response(b) for b in buyers]
    }