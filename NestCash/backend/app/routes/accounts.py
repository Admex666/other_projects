# app/routes/accounts.py

from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.models.user import User
from app.models.account import AllUserAccountsDocument, UserAccounts, AccountDetails, SubAccountDetails
from typing import Dict, Optional
from pydantic import BaseModel # Hozzáadva: BaseModel importálása

router = APIRouter(prefix="/accounts", tags=["accounts"])

# Hozzáadva: Modell a PUT kérés törzséhez
class SubAccountCreate(BaseModel):
    balance: float
    currency: str = "HUF" # Alapértelmezett érték, ha nincs megadva a kérésben

@router.get("/me", response_model=UserAccounts)
async def get_my_accounts(current_user: User = Depends(get_current_user)):
    user_id = str(current_user.id)
    all_accounts_doc = await AllUserAccountsDocument.find_one()

    if not all_accounts_doc:
        all_accounts_doc = AllUserAccountsDocument(
            accounts_by_user={
                user_id: UserAccounts(
                    likvid=AccountDetails(alszamlak={}),
                    befektetes=AccountDetails(alszamlak={}),
                    megtakaritas=AccountDetails(alszamlak={}),
                )
            }
        )
        await all_accounts_doc.insert()
    elif user_id not in all_accounts_doc.accounts_by_user:
        all_accounts_doc.accounts_by_user[user_id] = UserAccounts(
            likvid=AccountDetails(alszamlak={}),
            befektetes=AccountDetails(alszamlak={}),
            megtakaritas=AccountDetails(alszamlak={}),
        )
        await all_accounts_doc.save()

    return all_accounts_doc.accounts_by_user[user_id]

@router.put("/me/{main_account}/{sub_account_name}")
async def add_or_update_sub_account(
    main_account: str,
    sub_account_name: str,
    sub_account_data: SubAccountCreate, # Módosítva: A kérés testét ez a modell fogja feldolgozni
    current_user: User = Depends(get_current_user)
):
    user_id = str(current_user.id)
    all_accounts_doc = await AllUserAccountsDocument.find_one()

    if not all_accounts_doc:
        all_accounts_doc = AllUserAccountsDocument(
            accounts_by_user={
                user_id: UserAccounts(
                    likvid=AccountDetails(alszamlak={}),
                    befektetes=AccountDetails(alszamlak={}),
                    megtakaritas=AccountDetails(alszamlak={}),
                )
            }
        )
        await all_accounts_doc.insert()
    elif user_id not in all_accounts_doc.accounts_by_user:
        all_accounts_doc.accounts_by_user[user_id] = UserAccounts(
            likvid=AccountDetails(alszamlak={}),
            befektetes=AccountDetails(alszamlak={}),
            megtakaritas=AccountDetails(alszamlak={}),
        )
        await all_accounts_doc.save()

    user_accounts = all_accounts_doc.accounts_by_user[user_id]

    # Most a sub_account_data objektumról olvassuk le az egyenleget és a devizát
    sub_account_details = SubAccountDetails(
        balance=sub_account_data.balance,
        currency=sub_account_data.currency
    )

    if main_account == "likvid":
        user_accounts.likvid.alszamlak[sub_account_name] = sub_account_details
    elif main_account == "befektetes":
        user_accounts.befektetes.alszamlak[sub_account_name] = sub_account_details
    elif main_account == "megtakaritas":
        user_accounts.megtakaritas.alszamlak[sub_account_name] = sub_account_details
    else:
        raise HTTPException(status_code=400, detail="Invalid main account type")

    await all_accounts_doc.save()
    return {"message": "Alszámla sikeresen hozzáadva/frissítve"}

@router.delete("/me/{main_account}/{sub_account_name}")
async def delete_sub_account(
    main_account: str,
    sub_account_name: str,
    current_user: User = Depends(get_current_user)
):
    user_id = str(current_user.id)
    all_accounts_doc = await AllUserAccountsDocument.find_one()

    if not all_accounts_doc or user_id not in all_accounts_doc.accounts_by_user:
        raise HTTPException(status_code=404, detail="Accounts not found for user")

    user_accounts = all_accounts_doc.accounts_by_user[user_id]

    if main_account == "likvid":
        if sub_account_name in user_accounts.likvid.alszamlak:
            del user_accounts.likvid.alszamlak[sub_account_name]
        else:
            raise HTTPException(status_code=404, detail="Sub-account not found")
    elif main_account == "befektetes":
        if sub_account_name in user_accounts.befektetes.alszamlak:
            del user_accounts.befektetes.alszamlak[sub_account_name]
        else:
            raise HTTPException(status_code=404, detail="Sub-account not found")
    elif main_account == "megtakaritas":
        if sub_account_name in user_accounts.megtakaritas.alszamlak:
            del user_accounts.megtakaritas.alszamlak[sub_account_name]
        else:
            raise HTTPException(status_code=404, detail="Sub-account not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid main account type")

    await all_accounts_doc.save()
    return {"message": "Alszámla sikeresen törölve"}