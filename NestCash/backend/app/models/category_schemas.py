# app/models/category_schemas.py
from pydantic import BaseModel, Field
from typing import Literal, List, Optional

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="A kategória neve")
    type: Literal["income", "expense"] = Field(..., description="A kategória típusa (bevétel vagy kiadás)")

class CategoryRead(BaseModel):
    id: str = Field(..., description="A kategória egyedi azonosítója")
    user_id: str = Field(..., description="A kategóriát létrehozó felhasználó azonosítója")
    name: str
    type: Literal["income", "expense"]

    class Config:
        from_attributes = True # Pydantic v2-ben ez a helyes módja a `orm_mode` helyett

class CategoryListResponse(BaseModel):
    total_count: int
    categories: List[CategoryRead]