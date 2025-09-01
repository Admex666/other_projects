# app/routes/categories.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from beanie import PydanticObjectId
from typing import List, Literal, Optional

from app.models.category import Category
from app.models.category_schemas import CategoryCreate, CategoryRead, CategoryListResponse
from app.core.security import get_current_user
from app.models.user import User
from app.utils.translation_helper import get_category_display_name

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: Request,
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user)
):
    # Nyelv lekérése
    lang = request.headers.get('Accept-Language', 'hu')[:2]

    # Ellenőrizzük, hogy a felhasználó már létrehozott-e ilyen nevű és típusú kategóriát
    existing_category = await Category.find_one(
        Category.user_id == PydanticObjectId(current_user.id),
        Category.name == category_data.name,
        Category.type == category_data.type
    )
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ilyen nevű és típusú kategória már létezik."
        )

    new_category = Category(
        user_id=PydanticObjectId(current_user.id),
        name=category_data.name,
        type=category_data.type
    )
    await new_category.insert()
    return CategoryRead(
        id=str(new_category.id),
        user_id=str(new_category.user_id),
        name=new_category.name,
        display_name=get_category_display_name(new_category.name, lang),  # ÚJ
        type=new_category.type
    )

@router.get("/", response_model=CategoryListResponse)
async def get_categories(
    request: Request,
    category_type: Optional[Literal["income", "expense"]] = None,
    current_user: User = Depends(get_current_user)
):
    # Nyelv lekérése a request header-ből
    lang = request.headers.get('Accept-Language', 'hu')[:2]
    
    query = Category.find(Category.user_id == PydanticObjectId(current_user.id))
    if category_type:
        query = query.find(Category.type == category_type)

    categories = await query.to_list()
    
    all_categories_read = []
    
    # Felhasználó által létrehozott kategóriák
    for cat in categories:
        all_categories_read.append(CategoryRead(
            id=str(cat.id),
            user_id=str(cat.user_id),
            name=cat.name,
            display_name=get_category_display_name(cat.name, lang),  # ÚJ
            type=cat.type
        ))

    # Alapértelmezett kategóriák hozzáadása
    default_expense_categories = ['category_food', 'category_housing', 'category_transport', 'category_entertainment', 'category_healthcare', 'category_education', 'category_clothing', 'category_other']
    default_income_categories = ['category_salary', 'category_gifts', 'category_investment', 'category_other']

    if category_type == "expense" or category_type is None:
        for default_cat_key in default_expense_categories:
            if not any(c.name == default_cat_key and c.type == "expense" for c in all_categories_read):
                all_categories_read.append(CategoryRead(
                    id=f"default-expense-{default_cat_key}",
                    user_id="",
                    name=default_cat_key,
                    display_name=get_category_display_name(default_cat_key, lang),  # ÚJ
                    type="expense"
                ))
    
    if category_type == "income" or category_type is None:
        for default_cat_key in default_income_categories:
            if not any(c.name == default_cat_key and c.type == "income" for c in all_categories_read):
                all_categories_read.append(CategoryRead(
                    id=f"default-income-{default_cat_key}",
                    user_id="",
                    name=default_cat_key,
                    display_name=get_category_display_name(default_cat_key, lang),  # ÚJ
                    type="income"
                ))

    return CategoryListResponse(
        total_count=len(all_categories_read),
        categories=all_categories_read
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user)
):
    category = await Category.find_one(
        Category.id == PydanticObjectId(category_id),
        Category.user_id == PydanticObjectId(current_user.id)
    )
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategória nem található.")
    
    # Ellenőrizzük, hogy a kategória használatban van-e tranzakciókban
    # Ehhez importálni kell a Transaction modellt
    from app.models.transaction import Transaction
    transactions_using_category = await Transaction.find_one(
        Transaction.user_id == PydanticObjectId(current_user.id),
        Transaction.kategoria == category.name # Feltételezve, hogy a tranzakciókban a kategória neve van tárolva
    )
    if transactions_using_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A kategória használatban van tranzakciókban, ezért nem törölhető."
        )

    await category.delete()
    return {"message": "Kategória sikeresen törölve."}