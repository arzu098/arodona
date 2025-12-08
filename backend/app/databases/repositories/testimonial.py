from backend.app.databases.schemas.testimonial import TestimonialSchema
from backend.app.db.connection import get_database
from typing import List, Optional
from bson import ObjectId

def get_testimonial_collection():
    db = get_database()
    return db["testimonials"]

def create_testimonial(data: TestimonialSchema) -> dict:
    collection = get_testimonial_collection()
    testimonial = data.dict()
    result = collection.insert_one(testimonial)
    testimonial["_id"] = str(result.inserted_id)
    return testimonial

def get_all_testimonials() -> List[dict]:
    collection = get_testimonial_collection()
    testimonials = list(collection.find())
    for t in testimonials:
        t["_id"] = str(t["_id"])
    return testimonials
