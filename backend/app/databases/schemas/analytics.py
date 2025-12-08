"""Analytics schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TimeSeriesMetric(BaseModel):
    """Time series data point."""
    timestamp: datetime
    value: float

class SalesReport(BaseModel):
    """Sales analytics report."""
    total_revenue: float
    total_orders: int
    average_order_value: float
    sales_by_day: List[TimeSeriesMetric]
    sales_by_category: Dict[str, float]
    top_products: List[Dict[str, Any]]
    refund_rate: float
    
class VendorPerformanceReport(BaseModel):
    """Vendor performance analytics."""
    total_revenue: float
    total_orders: int
    order_fulfillment_rate: float
    average_shipping_time: float
    rating: float
    customer_satisfaction: float
    revenue_trend: List[TimeSeriesMetric]
    category_performance: List[Dict[str, Any]]

class CustomerAnalytics(BaseModel):
    """Customer behavior analytics."""
    total_customers: int
    new_customers: int
    repeat_customers: int
    average_lifetime_value: float
    retention_rate: float
    acquisition_channels: Dict[str, int]
    customer_segments: List[Dict[str, Any]]

class MarketplaceMetrics(BaseModel):
    """Overall marketplace performance metrics."""
    gross_merchandise_value: float
    total_transactions: int
    active_vendors: int
    active_buyers: int
    conversion_rate: float
    average_basket_size: float
    category_distribution: Dict[str, float]
    top_search_terms: List[Dict[str, int]]
    
class InventoryAnalytics(BaseModel):
    """Inventory and product analytics."""
    total_products: int
    active_products: int
    out_of_stock_products: int
    low_stock_products: int
    top_performing_categories: List[Dict[str, Any]]
    inventory_turnover: float
    stock_metrics: Dict[str, float]

class DateRangeParams(BaseModel):
    """Date range filter parameters."""
    start_date: datetime
    end_date: datetime = Field(default_factory=datetime.utcnow)
    interval: str = Field("day", description="Aggregation interval (hour/day/week/month)")

class FilterParams(BaseModel):
    """Common filter parameters."""
    vendor_id: Optional[str] = None
    category_id: Optional[str] = None
    product_id: Optional[str] = None
    status: Optional[str] = None