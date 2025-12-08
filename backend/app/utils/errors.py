"""
Custom error handling and exceptions for the application.
"""

from fastapi import HTTPException, status
from typing import Optional, Dict, Any
from enum import Enum

class ErrorCode(str, Enum):
    """Enumeration of application error codes"""
    # Authentication errors
    AUTH_INVALID_CREDENTIALS = "AUTH_001"
    AUTH_TOKEN_EXPIRED = "AUTH_002"
    AUTH_INVALID_TOKEN = "AUTH_003"
    AUTH_2FA_REQUIRED = "AUTH_004"
    AUTH_INVALID_2FA_CODE = "AUTH_005"
    AUTH_OAUTH_ERROR = "AUTH_006"
    
    # Authorization errors
    AUTHZ_INSUFFICIENT_PERMISSIONS = "AUTHZ_001"
    AUTHZ_ACCESS_DENIED = "AUTHZ_002"
    AUTHZ_ADMIN_REQUIRED = "AUTHZ_003"
    ACCESS_DENIED = "AUTHZ_002"  # Alias for common usage
    
    # Validation errors
    VAL_INVALID_INPUT = "VAL_001"
    VAL_MISSING_FIELD = "VAL_002"
    VAL_INVALID_FORMAT = "VAL_003"
    
    # Resource errors
    NOT_FOUND_USER = "NOT_FOUND_001"
    NOT_FOUND_PRODUCT = "NOT_FOUND_002"
    NOT_FOUND_ORDER = "NOT_FOUND_003"
    NOT_FOUND_CART = "NOT_FOUND_004"
    VENDOR_NOT_FOUND = "NOT_FOUND_005"
    
    # Shorthand aliases for common errors
    PRODUCT_NOT_FOUND = "NOT_FOUND_002"
    CART_NOT_FOUND = "NOT_FOUND_004"
    INVALID_INPUT = "VAL_001"
    AUTHENTICATION_REQUIRED = "AUTH_007"
    CART_EMPTY = "BIZ_004"
    INTERNAL_ERROR = "SYS_001"
    
    # Database errors
    DB_CONNECTION_ERROR = "DB_001"
    DB_QUERY_ERROR = "DB_002"
    DB_UPDATE_ERROR = "DB_003"
    
    # Business logic errors
    BIZ_INSUFFICIENT_STOCK = "BIZ_001"
    BIZ_INVALID_ORDER_STATUS = "BIZ_002"
    BIZ_PAYMENT_FAILED = "BIZ_003"
    BIZ_CART_EMPTY = "BIZ_004"
    BIZ_INVALID_QUANTITY = "BIZ_005"
    
    # Cart errors
    CART_ITEM_NOT_FOUND = "CART_001"
    CART_INVALID_QUANTITY = "CART_002"
    CART_PRODUCT_UNAVAILABLE = "CART_003"
    CART_OPERATION_FAILED = "CART_004"
    
    # Order errors
    ORDER_CREATION_FAILED = "ORDER_001"
    ORDER_FETCH_FAILED = "ORDER_002"
    ORDER_UPDATE_FAILED = "ORDER_003"
    ORDER_CANCELLATION_FAILED = "ORDER_004"
    CHECKOUT_VALIDATION_FAILED = "ORDER_005"

class AppError(HTTPException):
    """Base exception for application errors"""
    def __init__(
        self,
        detail: str = None,
        message: str = None,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        error_type: str = "internal_server_error",
        context: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        # Support both 'message' and 'detail' parameters for compatibility
        error_message = detail or message or "An unexpected error occurred"
        super().__init__(status_code=status_code, detail=error_message)
        self.error_code = error_code
        self.error_type = error_type
        self.context = context or details or {}

class AuthenticationError(AppError):
    """Authentication related errors"""
    def __init__(self, detail: str, error_code: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=f"AUTH_{error_code}",
            error_type="authentication_error",
            context=context
        )

class AuthorizationError(AppError):
    """Authorization related errors"""
    def __init__(self, detail: str, error_code: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=f"AUTHZ_{error_code}",
            error_type="authorization_error",
            context=context
        )

class ValidationError(AppError):
    """Data validation errors"""
    def __init__(self, detail: str, error_code: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=f"VAL_{error_code}",
            error_type="validation_error",
            context=context
        )

class ResourceNotFoundError(AppError):
    """Resource not found errors"""
    def __init__(self, detail: str, error_code: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=f"NOT_FOUND_{error_code}",
            error_type="not_found_error",
            context=context
        )

class DatabaseError(AppError):
    """Database operation errors"""
    def __init__(self, detail: str, error_code: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=f"DB_{error_code}",
            error_type="database_error",
            context=context
        )

class BusinessLogicError(AppError):
    """Business logic related errors"""
    def __init__(self, detail: str, error_code: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=f"BIZ_{error_code}",
            error_type="business_logic_error",
            context=context
        )

class UserError(AppError):
    """User-related errors"""
    def __init__(self, detail: str, error_code: str = "USER_ERROR", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=f"USER_{error_code}",
            error_type="user_error",
            context=context
        )

# Error codes and messages
ERROR_CODES = {
    # Authentication errors
    "AUTH_001": "Invalid credentials",
    "AUTH_002": "Token expired",
    "AUTH_003": "Invalid token",
    "AUTH_004": "2FA required",
    "AUTH_005": "Invalid 2FA code",
    "AUTH_006": "OAuth provider error",
    
    # Authorization errors
    "AUTHZ_001": "Insufficient permissions",
    "AUTHZ_002": "Resource access denied",
    "AUTHZ_003": "Admin access required",
    
    # Validation errors
    "VAL_001": "Invalid input data",
    "VAL_002": "Missing required field",
    "VAL_003": "Invalid format",
    
    # Resource errors
    "NOT_FOUND_001": "User not found",
    "NOT_FOUND_002": "Product not found",
    "NOT_FOUND_003": "Order not found",
    
    # Database errors
    "DB_001": "Database connection error",
    "DB_002": "Database query error",
    "DB_003": "Database update error",
    
    # Business logic errors
    "BIZ_001": "Insufficient stock",
    "BIZ_002": "Invalid order status",
    "BIZ_003": "Payment failed"
}