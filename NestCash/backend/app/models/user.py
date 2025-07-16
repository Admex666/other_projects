from beanie import Document
from pydantic import EmailStr
from typing import Optional
from datetime import datetime

class User(Document):
    user_id: int
    username: str
    password: str  # SHA-256 hash
    email: EmailStr
    registration_date: Optional[str]

    class Settings:
        name = "users"
