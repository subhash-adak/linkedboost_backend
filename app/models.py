from pydantic import BaseModel, EmailStr
from typing import Optional
from bson import ObjectId

class User(BaseModel):
    name: str
    email: EmailStr
    hashed_password: str
    is_verified: bool = False
    verification_token: Optional[str] = None
