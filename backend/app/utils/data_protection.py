"""
Data Protection Service
Prevents accidental deletion of user data and provides backup mechanisms
"""
import os
from datetime import datetime
from app.config import ENVIRONMENT

class DataProtectionService:
    """Service to protect user data from accidental deletion"""
    
    def __init__(self):
        self.protection_enabled = os.getenv("PROTECT_USER_DATA", "true").lower() == "true"
        self.disable_sample_cleanup = os.getenv("DISABLE_SAMPLE_CLEANUP", "true").lower() == "true"
        self.environment = ENVIRONMENT
    
    def is_deletion_allowed(self, collection_name: str, document: dict) -> bool:
        """Check if deletion of a document is allowed"""
        
        # Always protect in production
        if self.environment == "production":
            return self._is_safe_production_deletion(collection_name, document)
        
        # In development, be more permissive but still protect user data
        if self.protection_enabled:
            return self._is_safe_development_deletion(collection_name, document)
        
        return True
    
    def _is_safe_production_deletion(self, collection_name: str, document: dict) -> bool:
        """Production deletion rules - very strict"""
        
        # Never delete real user data in production
        if collection_name in ['users', 'vendors', 'products']:
            # Only allow soft deletes
            return False
        
        # Allow deletion of temporary data
        if collection_name in ['sessions', 'otps', 'temp_files']:
            return True
        
        return False
    
    def _is_safe_development_deletion(self, collection_name: str, document: dict) -> bool:
        """Development deletion rules - more permissive"""
        
        # Protect real user data even in development
        if collection_name == 'users':
            email = document.get('email', '')
            # Don't delete real emails
            if '@' in email and not any(test in email.lower() for test in ['test', 'demo', 'sample']):
                return False
        
        if collection_name == 'products':
            name = document.get('name', '')
            # Don't delete products that don't look like test data
            if name and not any(test in name.lower() for test in ['test', 'demo', 'sample']):
                return False
        
        return True
    
    def should_skip_cleanup(self) -> bool:
        """Check if cleanup operations should be skipped"""
        return self.disable_sample_cleanup
    
    def log_protection_event(self, event_type: str, details: dict):
        """Log data protection events"""
        timestamp = datetime.utcnow().isoformat()
        print(f"🛡️ DATA PROTECTION [{timestamp}]: {event_type}")
        print(f"   Details: {details}")
    
    def validate_bulk_operation(self, collection_name: str, operation_type: str, filter_query: dict) -> bool:
        """Validate bulk operations to prevent accidental data loss"""
        
        # In production, be extra careful with bulk operations
        if self.environment == "production":
            if operation_type in ['delete_many', 'drop']:
                self.log_protection_event("BLOCKED_BULK_OPERATION", {
                    "collection": collection_name,
                    "operation": operation_type,
                    "filter": str(filter_query),
                    "reason": "Bulk operations blocked in production"
                })
                return False
        
        # Check for dangerous patterns
        if not filter_query or filter_query == {}:
            self.log_protection_event("BLOCKED_DANGEROUS_OPERATION", {
                "collection": collection_name,
                "operation": operation_type,
                "reason": "Empty filter would affect all documents"
            })
            return False
        
        return True

# Global instance
data_protection = DataProtectionService()