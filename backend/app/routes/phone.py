
from fastapi import APIRouter, HTTPException, Depends, status, Request, Header, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import random
import requests
from datetime import datetime, timedelta
import os
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/phone", tags=["Phone Authentication"])

# Pydantic models for request validation
class SendOTPRequest(BaseModel):
    phone: str

class VerifyOTPRequest(BaseModel):
    otp: str

session_store = {}

API_KEY = "9d03333181fb0f6bd495e8b157259880"

@router.post("/send-otp")
async def send_otp(request: SendOTPRequest):
    try:
        phone = request.phone.strip()
        
        if not phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required"
            )

        # Generate 6-digit OTP
        otp = random.randint(100000, 999999)

        # Save in session store with both phone and OTP as keys
        session_store[phone] = otp
        session_store[str(otp)] = phone  # Store OTP -> phone mapping
        logger.info(f"OTP generated for phone: {phone}")

        # Create API URL
        url = f"https://sms.renflair.in/V1.php?API={API_KEY}&PHONE={phone}&OTP={otp}"

        try:
            # Call SMS API with timeout
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            logger.info(f"SMS API response for {phone}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"SMS API error for {phone}: {str(e)}")
            # Still return success even if SMS fails, for development
            return {
                "status": "success",
                "message": "OTP generated (SMS service unavailable)",
                "phone": phone,
                "otp": otp,   # Remove in production
                "sms_error": str(e)
            }
        
        return {
            "status": "success",
            "message": "OTP sent successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in send_otp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    try:
        otp_str = request.otp.strip()
        
        if not otp_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP is required"
            )

        try:
            otp = int(otp_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP must be a valid number"
            )

        # Check if OTP exists in session store
        if str(otp) not in session_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired OTP. Please request a new OTP."
            )

        # Get phone number from OTP mapping
        phone = session_store[str(otp)]
        
        # Verify OTP matches
        if session_store.get(phone) == otp:
            # Clean up both mappings after successful verification
            del session_store[phone]
            del session_store[str(otp)]
            logger.info(f"OTP verified successfully for phone: {phone}")
            return {
                "status": "success", 
                "message": "OTP Verified",
                "phone": phone
            }

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in verify_otp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )