"""
Global error handling middleware.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.utils.errors import AppError, ERROR_CODES
from app.utils.error_logging import ErrorLogger
from app.db.connection import get_database
import traceback
import sys

async def error_handler(request: Request, call_next):
    """Global error handling middleware"""
    try:
        return await call_next(request)

    except AppError as e:
        # Handle our custom application errors
        error_response = {
            "status": "error",
            "code": e.error_code,
            "type": e.error_type,
            "message": e.detail,
            "context": e.context
        }

        # Log error if it's a server error
        if e.status_code >= 500:
            error_logger = ErrorLogger(get_database())
            await error_logger.log_error(
                error=e,
                error_code=e.error_code,
                user_id=request.state.user_id if hasattr(request.state, "user_id") else None,
                request_data={
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "path_params": request.path_params,
                    "query_params": dict(request.query_params)
                },
                context=e.context
            )

        return JSONResponse(
            status_code=e.status_code,
            content=error_response
        )

    except Exception as e:
        # Handle unexpected errors
        error_code = "INTERNAL_ERROR"
        error_response = {
            "status": "error",
            "code": error_code,
            "type": "internal_server_error",
            "message": "An unexpected error occurred",
            "context": {
                "error_details": str(e) if not isinstance(e, Exception) else None
            }
        }

        # Log the unexpected error
        error_logger = ErrorLogger(get_database())
        await error_logger.log_error(
            error=e,
            error_code=error_code,
            user_id=request.state.user_id if hasattr(request.state, "user_id") else None,
            request_data={
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "path_params": request.path_params,
                "query_params": dict(request.query_params)
            },
            context={
                "traceback": traceback.format_exception(*sys.exc_info())
            }
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )