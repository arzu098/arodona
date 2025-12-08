"""
Error logging utilities for better error tracking and debugging.
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorLogger:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["error_logs"]

    async def log_error(
        self,
        error: Exception,
        error_code: str,
        user_id: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log error details to both file and database"""
        # Create error log entry
        error_data = {
            "timestamp": datetime.utcnow(),
            "error_code": error_code,
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "user_id": user_id,
            "request_data": request_data,
            "context": context
        }

        # Log to file
        logger.error(
            f"Error {error_code}: {str(error)}\n"
            f"User ID: {user_id}\n"
            f"Context: {context}\n"
            f"Traceback: {traceback.format_exc()}"
        )

        # Log to database
        try:
            await self.collection.insert_one(error_data)
        except Exception as db_error:
            logger.error(f"Failed to log error to database: {str(db_error)}")

    async def get_recent_errors(
        self,
        limit: int = 100,
        error_code: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> list:
        """Get recent error logs with optional filtering"""
        filter_query = {}
        if error_code:
            filter_query["error_code"] = error_code
        if user_id:
            filter_query["user_id"] = user_id

        try:
            return await self.collection.find(
                filter_query
            ).sort("timestamp", -1).limit(limit).to_list(limit)
        except Exception as e:
            logger.error(f"Failed to retrieve error logs: {str(e)}")
            return []

    async def get_error_statistics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get error statistics for a date range"""
        try:
            pipeline = [
                {
                    "$match": {
                        "timestamp": {
                            "$gte": start_date,
                            "$lte": end_date
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$error_code",
                        "count": {"$sum": 1},
                        "users_affected": {"$addToSet": "$user_id"}
                    }
                }
            ]

            results = await self.collection.aggregate(pipeline).to_list(None)
            
            stats = {
                "total_errors": sum(r["count"] for r in results),
                "error_breakdown": {
                    r["_id"]: {
                        "count": r["count"],
                        "users_affected": len(r["users_affected"])
                    }
                    for r in results
                }
            }
            
            return stats
        except Exception as e:
            logger.error(f"Failed to generate error statistics: {str(e)}")
            return {
                "total_errors": 0,
                "error_breakdown": {}
            }