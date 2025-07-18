# app/models/user.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from beanie import Document

# Beanie Document a MongoDB-hez
class UserDocument(Document):
    username: str
    email: EmailStr
    password: str
    mobile: Optional[str] = None
    registration_date: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

# Csak válaszhoz (nincs jelszó)
class User(BaseModel):
    id: str  # Changed from _id to id for standard Pydantic usage
    username: str
    email: EmailStr
    mobile: Optional[str] = None
    registration_date: datetime

# Belső használatra (benne van a password)
class UserInDB(User):
    password: str

# Regisztrációhoz (input)
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    mobile: Optional[str] = None