from pydantic import BaseModel
from typing import Optional

class TestimonialSchema(BaseModel):
    name: str
    message: str
    image_base64: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "message": "Great service!",
                "image_base64": "...base64string..."
            }
        }
