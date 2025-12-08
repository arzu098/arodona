"""User address schemas for delivery and billing."""

from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class AddressType(str, Enum):
    HOME = "HOME"
    WORK = "WORK"


class AddressCreate(BaseModel):
    name: str
    phone: str
    address: str
    city: str
    country: str
    address_type: AddressType = AddressType.HOME
    is_default: bool = False

    @validator('phone')
    def validate_phone(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Phone number must be at least 10 characters')
        return v.strip()

    @validator('name', 'address', 'city', 'country')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('This field cannot be empty')
        return v.strip()


class AddressUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    address_type: Optional[AddressType] = None
    is_default: Optional[bool] = None


class AddressResponse(BaseModel):
    id: str
    user_id: str
    name: str
    phone: str
    address: str
    city: str
    country: str
    address_type: AddressType
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
