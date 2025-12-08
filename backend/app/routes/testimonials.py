from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from pydantic import BaseModel
from bson import ObjectId
from backend.app.db.connection import get_database
import base64

router = APIRouter()

def get_collection():
    db = get_database()
    return db["testimonials"]

class TestimonialCreate(BaseModel):
    name: str
    message: str
    image_base64: Optional[str] = None

@router.post("/testimonials/")
async def create_testimonial(
    name: str = Form(...),
    message: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    image_base64 = None
    if image:
        content = await image.read()
        image_base64 = base64.b64encode(content).decode("utf-8")
    testimonial = {
        "name": name,
        "message": message,
        "image_base64": image_base64
    }
    collection = get_collection()
    result = collection.insert_one(testimonial)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to create testimonial")
    testimonial["_id"] = str(result.inserted_id)
    return testimonial

@router.get("/testimonials/")
async def get_testimonials():
    collection = get_collection()
    testimonials = list(collection.find())
    for t in testimonials:
        t["_id"] = str(t["_id"])
    return testimonials
