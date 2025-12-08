"""Analytics routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from app.databases.repositories.analytics import AnalyticsRepository
from app.databases.schemas.analytics import (
    DateRangeParams,
    FilterParams,
    SalesReport,
    VendorPerformanceReport,
    CustomerAnalytics,
    MarketplaceMetrics,
    InventoryAnalytics
)
from app.utils.security import get_current_user, get_current_admin, get_current_vendor

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.post("/sales", response_model=SalesReport)
async def get_sales_analytics(
    date_range: DateRangeParams,
    filters: FilterParams = None,
    user = Depends(get_current_admin),
    repo: AnalyticsRepository = Depends()
):
    """Get sales analytics report."""
    filters = filters or FilterParams()
    return await repo.get_sales_report(
        start_date=date_range.start_date,
        end_date=date_range.end_date,
        interval=date_range.interval,
        vendor_id=filters.vendor_id,
        category_id=filters.category_id
    )

@router.post("/vendor-performance", response_model=VendorPerformanceReport)
async def get_vendor_performance(
    date_range: DateRangeParams,
    vendor = Depends(get_current_vendor),
    repo: AnalyticsRepository = Depends()
):
    """Get vendor performance analytics."""
    return await repo.get_vendor_performance(
        str(vendor["_id"]),
        date_range.start_date,
        date_range.end_date
    )

@router.post("/customer", response_model=CustomerAnalytics)
async def get_customer_analytics(
    date_range: DateRangeParams,
    user = Depends(get_current_admin),
    repo: AnalyticsRepository = Depends()
):
    """Get customer behavior analytics."""
    return await repo.get_customer_analytics(
        date_range.start_date,
        date_range.end_date
    )

@router.post("/marketplace", response_model=MarketplaceMetrics)
async def get_marketplace_analytics(
    date_range: DateRangeParams,
    user = Depends(get_current_admin),
    repo: AnalyticsRepository = Depends()
):
    """Get overall marketplace performance metrics."""
    return await repo.get_marketplace_metrics(
        date_range.start_date,
        date_range.end_date
    )

@router.get("/inventory", response_model=InventoryAnalytics)
async def get_inventory_analytics(
    user = Depends(get_current_admin),
    repo: AnalyticsRepository = Depends()
):
    """Get inventory and product analytics."""
    return await repo.get_inventory_analytics()