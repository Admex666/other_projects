# app/models/category.py
from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional, Literal

class Category(Document):
    user_id: PydanticObjectId = Field(..., description="A kategóriát létrehozó felhasználó azonosítója")
    name: str = Field(..., description="A kategória neve")
    type: Literal["income", "expense"] = Field(..., description="A kategória típusa (bevétel vagy kiadás)")

    class Settings:
        name = "categories" # A MongoDB kollekció neve
        indexes = [
            ("user_id", "type", "name"), # Gyorsabb keresés felhasználó, típus és név alapján
        ]