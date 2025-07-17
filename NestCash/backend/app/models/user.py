# app/models/user.py
from __future__ import annotations

from beanie import Document
from pydantic import EmailStr, Field
from typing import Optional
from datetime import datetime


class User(Document):
    username: str
    email: EmailStr
    password: str                  # bcrypt hash
    mobile: Optional[str] = None
    registration_date: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
