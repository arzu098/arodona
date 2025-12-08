"""
Comprehensive Payment Repository for Jewelry E-commerce.
Handles payment processing, Stripe integration, vendor payouts,
refunds, disputes, and payment analytics with multi-currency support.
"""

from typing import Dict, Any, Optional, List, Tuple
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.db.connection import get_database
from app.databases.schemas.payments import (
    PaymentStatus, PaymentGateway, Currency, VendorPayoutStatus,
    RefundStatus, DisputeStatus, PaymentMethodType
)

logger = logging.getLogger(__name__)

class PaymentRepository:
    """Comprehensive payment repository for jewelry e-commerce platform"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.payments = db["payments"]
        self.refunds = db["refunds"]
        self.payment_methods = db["payment_methods"]
        self.vendor_payouts = db["vendor_payouts"]
        self.payment_intents = db["payment_intents"]
        self.disputes = db["payment_disputes"]
        self.payment_analytics = db["payment_analytics"]
        self.orders = db["orders"]
        self.vendors = db["vendors"]

    def generate_payment_id(self) -> str:
        """Generate unique payment ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = str(uuid4().hex[:8]).upper()
        return f"PAY-{timestamp}-{random_suffix}"

    async def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new payment record"""
        try:
            current_time = datetime.utcnow()
            payment_id = self.generate_payment_id()
            
            payment_doc = {
                "_id": ObjectId(),
                "payment_id": payment_id,
                "order_id": payment_data["order_id"],
                "customer_id": payment_data["customer_id"],
                "amount": float(payment_data["amount"]),
                "currency": payment_data.get("currency", Currency.USD.value),
                "status": PaymentStatus.CREATED.value,
                "gateway": payment_data.get("gateway", PaymentGateway.STRIPE.value),
                "gateway_payment_id": None,
                "gateway_transaction_id": None,
                "payment_method": payment_data.get("payment_method"),
                "client_secret": None,
                "payment_url": None,
                "next_action": None,
                "amount_captured": 0.0,
                "amount_refunded": 0.0,
                "platform_fee": payment_data.get("platform_fee", 0.0),
                "gateway_fee": payment_data.get("gateway_fee", 0.0),
                "vendor_payouts": [],
                "risk_score": None,
                "fraud_details": None,
                "metadata": payment_data.get("metadata", {}),
                "created_at": current_time,
                "updated_at": current_time,
                "authorized_at": None,
                "captured_at": None
            }
            
            result = await self.payments.insert_one(payment_doc)
            payment_doc["_id"] = result.inserted_id
            
            return payment_doc
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            raise

    async def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by payment ID"""
        try:
            return await self.payments.find_one({"payment_id": payment_id})
        except Exception as e:
            logger.error(f"Error fetching payment: {str(e)}")
            return None

    async def get_payment_by_gateway_id(self, gateway_payment_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by gateway payment ID"""
        try:
            return await self.payments.find_one({"gateway_payment_id": gateway_payment_id})
        except Exception as e:
            logger.error(f"Error fetching payment by gateway ID: {str(e)}")
            return None

    async def update_payment(self, payment_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update payment with new data"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            # Handle status change timestamps
            if "status" in update_data:
                if update_data["status"] == PaymentStatus.SUCCEEDED.value and "captured_at" not in update_data:
                    update_data["captured_at"] = datetime.utcnow()
                elif update_data["status"] == PaymentStatus.REQUIRES_CAPTURE.value and "authorized_at" not in update_data:
                    update_data["authorized_at"] = datetime.utcnow()
            
            result = await self.payments.find_one_and_update(
                {"payment_id": payment_id},
                {"$set": update_data},
                return_document=True
            )
            
            return result
        except Exception as e:
            logger.error(f"Error updating payment: {str(e)}")
            return None

    async def get_customer_payments(
        self, 
        customer_id: str, 
        status_filter: Optional[List[str]] = None,
        page: int = 1, 
        per_page: int = 20
    ) -> Tuple[List[Dict], int, int]:
        """Get customer payments with filtering and pagination"""
        try:
            skip = (page - 1) * per_page
            
            filter_query = {"customer_id": customer_id}
            if status_filter:
                filter_query["status"] = {"$in": status_filter}
            
            total = await self.payments.count_documents(filter_query)
            total_pages = (total + per_page - 1) // per_page
            
            payments = await self.payments.find(filter_query).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
            
            return payments, total, total_pages
        except Exception as e:
            logger.error(f"Error fetching customer payments: {str(e)}")
            return [], 0, 0

    # Refund Management
    def generate_refund_id(self) -> str:
        """Generate unique refund ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = str(uuid4().hex[:6]).upper()
        return f"REF-{timestamp}-{random_suffix}"

    async def create_refund(self, refund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new refund request"""
        try:
            current_time = datetime.utcnow()
            refund_id = self.generate_refund_id()
            
            # Get original payment details
            payment = await self.get_payment(refund_data["payment_id"])
            if not payment:
                raise ValueError("Payment not found")
            
            refund_doc = {
                "_id": ObjectId(),
                "refund_id": refund_id,
                "payment_id": refund_data["payment_id"],
                "order_id": payment["order_id"],
                "amount": float(refund_data.get("amount", payment["amount"])),
                "currency": payment["currency"],
                "status": RefundStatus.PENDING.value,
                "gateway": payment["gateway"],
                "gateway_refund_id": None,
                "reason": refund_data["reason"],
                "description": refund_data.get("description"),
                "fee_refunded": None,
                "processed_by": refund_data.get("processed_by"),
                "failure_reason": None,
                "metadata": refund_data.get("metadata", {}),
                "created_at": current_time,
                "processed_at": None
            }
            
            result = await self.refunds.insert_one(refund_doc)
            refund_doc["_id"] = result.inserted_id
            
            return refund_doc
        except Exception as e:
            logger.error(f"Error creating refund: {str(e)}")
            raise

    async def update_refund(self, refund_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update refund status and details"""
        try:
            if "status" in update_data and update_data["status"] == RefundStatus.SUCCEEDED.value:
                update_data["processed_at"] = datetime.utcnow()
            
            result = await self.refunds.find_one_and_update(
                {"refund_id": refund_id},
                {"$set": update_data},
                return_document=True
            )
            
            # Update payment amount_refunded
            if result and "amount" in update_data:
                await self.payments.update_one(
                    {"payment_id": result["payment_id"]},
                    {"$inc": {"amount_refunded": update_data["amount"]}}
                )
            
            return result
        except Exception as e:
            logger.error(f"Error updating refund: {str(e)}")
            return None

    async def get_refund(self, refund_id: str) -> Optional[Dict[str, Any]]:
        """Get refund by refund ID"""
        try:
            return await self.refunds.find_one({"refund_id": refund_id})
        except Exception as e:
            logger.error(f"Error fetching refund: {str(e)}")
            return None

    # Payment Methods Management
    async def save_payment_method(self, method_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save customer payment method"""
        try:
            current_time = datetime.utcnow()
            
            method_doc = {
                "_id": ObjectId(),
                "customer_id": method_data["customer_id"],
                "type": method_data["type"],
                "gateway": method_data["gateway"],
                "gateway_method_id": method_data["gateway_method_id"],
                "last_four": method_data.get("last_four"),
                "brand": method_data.get("brand"),
                "funding": method_data.get("funding"),
                "expires_month": method_data.get("expires_month"),
                "expires_year": method_data.get("expires_year"),
                "bank_name": method_data.get("bank_name"),
                "account_type": method_data.get("account_type"),
                "is_default": method_data.get("is_default", False),
                "is_verified": method_data.get("is_verified", False),
                "nickname": method_data.get("nickname"),
                "created_at": current_time,
                "updated_at": current_time,
                "last_used_at": None
            }
            
            # If this is set as default, unset other defaults
            if method_doc["is_default"]:
                await self.payment_methods.update_many(
                    {"customer_id": method_data["customer_id"], "is_default": True},
                    {"$set": {"is_default": False}}
                )
            
            result = await self.payment_methods.insert_one(method_doc)
            method_doc["_id"] = result.inserted_id
            
            return method_doc
        except Exception as e:
            logger.error(f"Error saving payment method: {str(e)}")
            raise

    async def get_customer_payment_methods(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all saved payment methods for customer"""
        try:
            methods = await self.payment_methods.find(
                {"customer_id": customer_id}
            ).sort("created_at", -1).to_list(None)
            
            return methods
        except Exception as e:
            logger.error(f"Error fetching payment methods: {str(e)}")
            return []

    async def delete_payment_method(self, customer_id: str, method_id: str) -> bool:
        """Delete customer payment method"""
        try:
            result = await self.payment_methods.delete_one({
                "_id": ObjectId(method_id),
                "customer_id": customer_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting payment method: {str(e)}")
            return False

    # Vendor Payout Management
    def generate_payout_id(self) -> str:
        """Generate unique payout ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = str(uuid4().hex[:6]).upper()
        return f"POUT-{timestamp}-{random_suffix}"

    async def calculate_vendor_payout(
        self, 
        vendor_id: str,
        start_date: datetime,
        end_date: datetime,
        order_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Calculate vendor payout amount for a period"""
        try:
            # Build match filter for orders
            match_filter = {
                f"vendor_orders.{vendor_id}": {"$exists": True},
                "status": {"$in": ["delivered", "completed"]},
                "payment_status": "completed",
                "created_at": {"$gte": start_date, "$lte": end_date}
            }
            
            if order_ids:
                match_filter["_id"] = {"$in": [ObjectId(oid) for oid in order_ids]}
            
            # Get vendor commission rate
            vendor = await self.vendors.find_one({"_id": ObjectId(vendor_id)})
            commission_rate = vendor.get("commission_rate", 0.15) if vendor else 0.15  # Default 15%
            
            # Aggregate orders and calculate totals
            pipeline = [
                {"$match": match_filter},
                {
                    "$project": {
                        "order_id": {"$toString": "$_id"},
                        "order_number": 1,
                        "vendor_items": {
                            "$filter": {
                                "input": "$items",
                                "cond": {"$eq": ["$$this.vendor_id", vendor_id]}
                            }
                        },
                        "created_at": 1
                    }
                },
                {
                    "$project": {
                        "order_id": 1,
                        "order_number": 1,
                        "created_at": 1,
                        "vendor_total": {"$sum": "$vendor_items.line_total"}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_orders": {"$sum": 1},
                        "gross_sales": {"$sum": "$vendor_total"},
                        "order_ids": {"$push": "$order_id"},
                        "order_numbers": {"$push": "$order_number"}
                    }
                }
            ]
            
            result = await self.orders.aggregate(pipeline).to_list(1)
            
            if not result:
                return {
                    "vendor_id": vendor_id,
                    "gross_sales": 0.0,
                    "commission_amount": 0.0,
                    "platform_fee": 0.0,
                    "gateway_fees": 0.0,
                    "net_amount": 0.0,
                    "order_count": 0,
                    "order_ids": []
                }
            
            data = result[0]
            gross_sales = float(data["gross_sales"])
            commission_amount = gross_sales * commission_rate
            
            # Calculate platform fee (1% of gross sales)
            platform_fee = gross_sales * 0.01
            
            # Estimate gateway fees (2.9% + $0.30 per transaction)
            gateway_fees = (gross_sales * 0.029) + (data["total_orders"] * 0.30)
            
            # Calculate net payout
            net_amount = gross_sales - commission_amount - platform_fee - gateway_fees
            
            return {
                "vendor_id": vendor_id,
                "gross_sales": gross_sales,
                "commission_rate": commission_rate,
                "commission_amount": commission_amount,
                "platform_fee": platform_fee,
                "gateway_fees": gateway_fees,
                "adjustments": 0.0,
                "net_amount": max(0.0, net_amount),  # Ensure non-negative
                "order_count": data["total_orders"],
                "order_ids": data["order_ids"]
            }
        except Exception as e:
            logger.error(f"Error calculating vendor payout: {str(e)}")
            raise

    async def create_vendor_payout(self, payout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a vendor payout record"""
        try:
            current_time = datetime.utcnow()
            payout_id = self.generate_payout_id()
            
            # Get vendor details
            vendor = await self.vendors.find_one({"_id": ObjectId(payout_data["vendor_id"])})
            vendor_name = vendor["business_name"] if vendor else "Unknown Vendor"
            
            payout_doc = {
                "_id": ObjectId(),
                "payout_id": payout_id,
                "vendor_id": payout_data["vendor_id"],
                "vendor_name": vendor_name,
                "gross_sales": float(payout_data["gross_sales"]),
                "commission_rate": float(payout_data["commission_rate"]),
                "commission_amount": float(payout_data["commission_amount"]),
                "platform_fee": float(payout_data["platform_fee"]),
                "gateway_fees": float(payout_data["gateway_fees"]),
                "adjustments": float(payout_data.get("adjustments", 0.0)),
                "net_amount": float(payout_data["net_amount"]),
                "currency": payout_data.get("currency", Currency.USD.value),
                "status": VendorPayoutStatus.PENDING.value,
                "gateway": payout_data.get("gateway"),
                "gateway_payout_id": None,
                "payout_method": payout_data.get("payout_method", "bank_account"),
                "bank_account_last_four": payout_data.get("bank_account_last_four"),
                "order_ids": payout_data["order_ids"],
                "order_count": len(payout_data["order_ids"]),
                "period_start": payout_data["period_start"],
                "period_end": payout_data["period_end"],
                "scheduled_at": payout_data.get("scheduled_at", current_time),
                "processed_at": None,
                "created_at": current_time,
                "processed_by": payout_data.get("processed_by"),
                "failure_reason": None,
                "notes": payout_data.get("notes")
            }
            
            result = await self.vendor_payouts.insert_one(payout_doc)
            payout_doc["_id"] = result.inserted_id
            
            return payout_doc
        except Exception as e:
            logger.error(f"Error creating vendor payout: {str(e)}")
            raise

    async def get_payment_analytics(
        self, 
        start_date: datetime, 
        end_date: datetime,
        vendor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive payment analytics"""
        try:
            match_filter = {
                "created_at": {"$gte": start_date, "$lte": end_date}
            }
            
            if vendor_id:
                # Filter payments for specific vendor orders
                vendor_orders = await self.orders.find(
                    {f"vendor_orders.{vendor_id}": {"$exists": True}},
                    {"_id": 1}
                ).to_list(None)
                order_ids = [str(order["_id"]) for order in vendor_orders]
                match_filter["order_id"] = {"$in": order_ids}
            
            # Aggregate payment data
            pipeline = [
                {"$match": match_filter},
                {
                    "$group": {
                        "_id": None,
                        "total_revenue": {"$sum": "$amount"},
                        "total_transactions": {"$sum": 1},
                        "successful_payments": {
                            "$sum": {"$cond": [{"$eq": ["$status", "succeeded"]}, 1, 0]}
                        },
                        "failed_payments": {
                            "$sum": {"$cond": [{"$in": ["$status", ["failed", "cancelled"]]}, 1, 0]}
                        },
                        "refunded_amount": {"$sum": "$amount_refunded"},
                        "total_gateway_fees": {"$sum": "$gateway_fee"},
                        "total_platform_fees": {"$sum": "$platform_fee"},
                        "payment_methods": {"$push": "$payment_method.type"},
                        "currencies": {"$push": "$currency"}
                    }
                }
            ]
            
            result = await self.payments.aggregate(pipeline).to_list(1)
            
            if not result:
                return {
                    "total_revenue": 0.0,
                    "total_transactions": 0,
                    "successful_payments": 0,
                    "failed_payments": 0,
                    "refunded_amount": 0.0,
                    "average_transaction_value": 0.0,
                    "payment_methods": {},
                    "currency_breakdown": {},
                    "total_gateway_fees": 0.0,
                    "total_platform_fees": 0.0,
                    "total_vendor_payouts": 0.0,
                    "pending_vendor_payouts": 0.0,
                    "period_start": start_date,
                    "period_end": end_date
                }
            
            data = result[0]
            
            # Calculate additional metrics
            avg_transaction = data["total_revenue"] / max(1, data["total_transactions"])
            
            return {
                "total_revenue": data["total_revenue"],
                "total_transactions": data["total_transactions"],
                "successful_payments": data["successful_payments"],
                "failed_payments": data["failed_payments"],
                "refunded_amount": data["refunded_amount"],
                "average_transaction_value": avg_transaction,
                "payment_methods": {},  # Can be enhanced with method breakdown
                "currency_breakdown": {},  # Can be enhanced with currency breakdown
                "total_gateway_fees": data["total_gateway_fees"],
                "total_platform_fees": data["total_platform_fees"],
                "total_vendor_payouts": 0.0,  # Can be calculated from payouts collection
                "pending_vendor_payouts": 0.0,  # Can be calculated from payouts collection
                "period_start": start_date,
                "period_end": end_date
            }
        except Exception as e:
            logger.error(f"Error generating payment analytics: {str(e)}")
            return {}

    async def create_indexes(self) -> None:
        """Create comprehensive indexes for payment collections"""
        try:
            # Payments collection indexes
            await self.payments.create_index("payment_id", unique=True)
            await self.payments.create_index("gateway_payment_id")
            await self.payments.create_index("customer_id")
            await self.payments.create_index("order_id")
            await self.payments.create_index("status")
            await self.payments.create_index([("customer_id", 1), ("created_at", -1)])
            await self.payments.create_index([("status", 1), ("created_at", -1)])
            await self.payments.create_index("created_at", -1)
            
            # Refunds collection indexes
            await self.refunds.create_index("refund_id", unique=True)
            await self.refunds.create_index("payment_id")
            await self.refunds.create_index("order_id")
            await self.refunds.create_index("status")
            await self.refunds.create_index("created_at", -1)
            
            # Payment methods collection indexes
            await self.payment_methods.create_index("customer_id")
            await self.payment_methods.create_index("gateway_method_id")
            await self.payment_methods.create_index([("customer_id", 1), ("is_default", -1)])
            
            # Vendor payouts collection indexes
            await self.vendor_payouts.create_index("payout_id", unique=True)
            await self.vendor_payouts.create_index("vendor_id")
            await self.vendor_payouts.create_index("status")
            await self.vendor_payouts.create_index([("vendor_id", 1), ("created_at", -1)])
            await self.vendor_payouts.create_index("scheduled_at")
            
            logger.info("Payment repository indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating payment indexes: {str(e)}")
