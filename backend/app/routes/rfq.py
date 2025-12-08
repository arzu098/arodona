"""Request for Quotation (RFQ) routes."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.databases.repositories.rfq import RFQRepository
from app.databases.schemas.rfq import (
    RFQCreate,
    RFQResponse,
    RFQList,
    QuoteCreate,
    QuoteResponse,
    QuoteList,
    RFQStatus,
    QuoteStatus
)
from app.utils.security import get_current_user, get_current_vendor

router = APIRouter(prefix="/rfq", tags=["rfq"])

# RFQ Management Routes
@router.post("", response_model=RFQResponse)
async def create_rfq(
    data: RFQCreate,
    user = Depends(get_current_user),
    repo: RFQRepository = Depends()
):
    """Create new RFQ."""
    rfq_data = data.dict()
    rfq_data["buyer_id"] = str(user["_id"])
    return await repo.create_rfq(rfq_data)

@router.get("/{rfq_id}", response_model=RFQResponse)
async def get_rfq(
    rfq_id: str,
    user = Depends(get_current_user),
    repo: RFQRepository = Depends()
):
    """Get RFQ details."""
    rfq = await repo.get_rfq(rfq_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return rfq

@router.get("", response_model=RFQList)
async def list_rfqs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    category_id: Optional[str] = None,
    my_rfqs: bool = False,
    user = Depends(get_current_user),
    repo: RFQRepository = Depends()
):
    """List RFQs with filters."""
    buyer_id = str(user["_id"]) if my_rfqs else None
    rfqs, total = await repo.list_rfqs(skip, limit, buyer_id, status, category_id)
    return {
        "rfqs": rfqs,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.post("/{rfq_id}/publish")
async def publish_rfq(
    rfq_id: str,
    user = Depends(get_current_user),
    repo: RFQRepository = Depends()
):
    """Publish RFQ."""
    rfq = await repo.get_rfq(rfq_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq["buyer_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    if rfq["status"] != RFQStatus.DRAFT:
        raise HTTPException(status_code=400, detail="RFQ must be in draft status")
    
    published = await repo.publish_rfq(rfq_id)
    return {"status": "published", "rfq": published}

@router.post("/{rfq_id}/close")
async def close_rfq(
    rfq_id: str,
    user = Depends(get_current_user),
    repo: RFQRepository = Depends()
):
    """Close RFQ."""
    rfq = await repo.get_rfq(rfq_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq["buyer_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    if rfq["status"] not in [RFQStatus.PUBLISHED, RFQStatus.IN_PROGRESS]:
        raise HTTPException(status_code=400, detail="RFQ must be published or in progress")
    
    closed = await repo.close_rfq(rfq_id)
    return {"status": "closed", "rfq": closed}

@router.post("/{rfq_id}/cancel")
async def cancel_rfq(
    rfq_id: str,
    user = Depends(get_current_user),
    repo: RFQRepository = Depends()
):
    """Cancel RFQ."""
    rfq = await repo.get_rfq(rfq_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq["buyer_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    if rfq["status"] in [RFQStatus.CLOSED, RFQStatus.CANCELLED, RFQStatus.AWARDED]:
        raise HTTPException(status_code=400, detail="RFQ cannot be cancelled")
    
    cancelled = await repo.cancel_rfq(rfq_id)
    return {"status": "cancelled", "rfq": cancelled}

# Quote Management Routes
@router.post("/quotes", response_model=QuoteResponse)
async def create_quote(
    data: QuoteCreate,
    vendor = Depends(get_current_vendor),
    repo: RFQRepository = Depends()
):
    """Create new quote for RFQ."""
    # Verify RFQ exists and is open for quotes
    rfq = await repo.get_rfq(data.rfq_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq["status"] != RFQStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="RFQ is not accepting quotes")
    
    quote_data = data.dict()
    quote_data["vendor_id"] = str(vendor["_id"])
    return await repo.create_quote(quote_data)

@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    user = Depends(get_current_user),
    repo: RFQRepository = Depends()
):
    """Get quote details."""
    quote = await repo.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@router.get("/quotes", response_model=QuoteList)
async def list_quotes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    rfq_id: Optional[str] = None,
    status: Optional[str] = None,
    my_quotes: bool = False,
    vendor = Depends(get_current_vendor),
    repo: RFQRepository = Depends()
):
    """List quotes with filters."""
    vendor_id = str(vendor["_id"]) if my_quotes else None
    quotes, total = await repo.list_quotes(skip, limit, rfq_id, vendor_id, status)
    return {
        "quotes": quotes,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.post("/quotes/{quote_id}/submit")
async def submit_quote(
    quote_id: str,
    vendor = Depends(get_current_vendor),
    repo: RFQRepository = Depends()
):
    """Submit quote."""
    quote = await repo.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote["vendor_id"] != str(vendor["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    if quote["status"] != QuoteStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Quote must be in draft status")
    
    submitted = await repo.submit_quote(quote_id)
    return {"status": "submitted", "quote": submitted}

@router.post("/{rfq_id}/quotes/{quote_id}/award")
async def award_quote(
    rfq_id: str,
    quote_id: str,
    user = Depends(get_current_user),
    repo: RFQRepository = Depends()
):
    """Award quote to vendor."""
    rfq = await repo.get_rfq(rfq_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq["buyer_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    if rfq["status"] not in [RFQStatus.PUBLISHED, RFQStatus.IN_PROGRESS]:
        raise HTTPException(status_code=400, detail="RFQ is not in valid state for award")
    
    quote = await repo.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote["rfq_id"] != rfq_id:
        raise HTTPException(status_code=400, detail="Quote does not belong to this RFQ")
    if quote["status"] != QuoteStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Quote must be submitted")
    
    rfq, quote = await repo.award_quote(rfq_id, quote_id)
    return {
        "status": "awarded",
        "rfq": rfq,
        "awarded_quote": quote
    }

@router.post("/quotes/{quote_id}/reject")
async def reject_quote(
    quote_id: str,
    user = Depends(get_current_user),
    repo: RFQRepository = Depends()
):
    """Reject quote."""
    quote = await repo.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Get RFQ to verify buyer
    rfq = await repo.get_rfq(quote["rfq_id"])
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq["buyer_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    rejected = await repo.reject_quote(quote_id)
    return {"status": "rejected", "quote": rejected}

@router.post("/quotes/{quote_id}/withdraw")
async def withdraw_quote(
    quote_id: str,
    vendor = Depends(get_current_vendor),
    repo: RFQRepository = Depends()
):
    """Withdraw quote."""
    quote = await repo.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote["vendor_id"] != str(vendor["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    if quote["status"] not in [QuoteStatus.DRAFT, QuoteStatus.SUBMITTED]:
        raise HTTPException(status_code=400, detail="Quote cannot be withdrawn")
    
    withdrawn = await repo.withdraw_quote(quote_id)
    return {"status": "withdrawn", "quote": withdrawn}