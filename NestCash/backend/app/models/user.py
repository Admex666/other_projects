from beanie import Document
from pydantic import EmailStr
from typing import Optional
from datetime import datetime

class User(Document):
    username: str
    email: EmailStr
    password: str  # bcrypt hash
    registration_date: Optional[str]

    class Settings:
        name = "users"
