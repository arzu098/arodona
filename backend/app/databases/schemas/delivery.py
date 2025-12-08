# app/schemas.py
from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class DeliveryBoyBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    vehicle_type: Optional[str] = None
    address: Optional[str] = None

class DeliveryBoyCreate(DeliveryBoyBase):
    password: str

class DeliveryBoyUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    vehicle_type: Optional[str] = None
    address: Optional[str] = None
