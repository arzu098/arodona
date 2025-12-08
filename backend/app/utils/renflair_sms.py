"""
Renflair SMS Service - Python equivalent of your PHP code
Handles OTP sending and verification using Renflair SMS API
"""

import os
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RenflairSMSService:
    """Renflair SMS service class - Python version of your PHP code"""
    
    def __init__(self):
        self.api_key = os.getenv("RENFLAIR_API_KEY", "")
        self.base_url = "https://sms.renflair.in/V1.php"
    
    async def send_otp_sms(self, phone: str, otp: str) -> Dict[str, Any]:
        """
        Send OTP SMS using Renflair API (equivalent to your PHP send code)
        
        PHP equivalent:
        $URL="https://sms.renflair.in/V1.php?API=$API&PHONE=$PHONE&OTP=$OTP";
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "message": "Renflair API key not configured",
                    "provider": "renflair"
                }
            
            # Clean phone number (remove country code +91)
            clean_phone = phone.replace("+91", "").replace("+", "")
            
            # Build URL exactly like PHP code
            url = f"{self.base_url}?API={self.api_key}&PHONE={clean_phone}&OTP={otp}"
            
            # Make request (equivalent to PHP curl)
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    # Try to parse JSON response
                    result = response.json()
                    
                    logger.info(f"Renflair SMS sent to {phone}: {result}")
                    
                    return {
                        "success": True,
                        "message": "OTP sent successfully via Renflair",
                        "provider": "renflair",
                        "response": result,
                        "phone": clean_phone,
                        "otp_sent": True
                    }
                    
                except ValueError:
                    # If response is not JSON, check text response
                    response_text = response.text.lower()
                    
                    if any(keyword in response_text for keyword in ['success', 'sent', 'delivered']):
                        logger.info(f"Renflair SMS sent to {phone}: {response.text}")
                        
                        return {
                            "success": True,
                            "message": "OTP sent successfully via Renflair",
                            "provider": "renflair",
                            "response": response.text,
                            "phone": clean_phone,
                            "otp_sent": True
                        }
                    else:
                        logger.error(f"Renflair SMS failed for {phone}: {response.text}")
                        
                        return {
                            "success": False,
                            "message": f"Renflair SMS failed: {response.text}",
                            "provider": "renflair",
                            "phone": clean_phone
                        }
            else:
                logger.error(f"Renflair API error: HTTP {response.status_code}")
                return {
                    "success": False,
                    "message": f"Renflair API error: HTTP {response.status_code}",
                    "provider": "renflair"
                }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Renflair request failed: {str(e)}")
            return {
                "success": False,
                "message": f"Network error: {str(e)}",
                "provider": "renflair"
            }
        
        except Exception as e:
            logger.error(f"Renflair SMS error: {str(e)}")
            return {
                "success": False,
                "message": f"SMS sending failed: {str(e)}",
                "provider": "renflair"
            }
    
    def verify_otp(self, actual_otp: str, entered_otp: str, phone: str) -> Dict[str, Any]:
       
        try:
            if actual_otp == entered_otp:
                logger.info(f"OTP verified successfully for phone: {phone}")
                
                return {
                    "success": True,
                    "verified": True,
                    "message": "Account Verified with OTP",
                    "phone": phone,
                    "status": "verified"
                }
            else:
                logger.warning(f"Incorrect OTP entered for phone: {phone}")
                
                return {
                    "success": False,
                    "verified": False,
                    "message": "Incorrect OTP Entered",
                    "phone": phone,
                    "status": "invalid_otp"
                }
        
        except Exception as e:
            logger.error(f"OTP verification error: {str(e)}")
            return {
                "success": False,
                "verified": False,
                "message": f"Verification failed: {str(e)}",
                "phone": phone,
                "status": "error"
            }

# Global instance
renflair_sms_service = RenflairSMSService()

# Convenience functions
async def send_renflair_otp(phone: str, otp: str) -> Dict[str, Any]:
    """Send OTP using Renflair service"""
    return await renflair_sms_service.send_otp_sms(phone, otp)

def verify_renflair_otp(actual_otp: str, entered_otp: str, phone: str) -> Dict[str, Any]:
    """Verify OTP using Renflair logic"""
    return renflair_sms_service.verify_otp(actual_otp, entered_otp, phone)