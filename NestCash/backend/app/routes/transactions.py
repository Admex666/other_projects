# app/routes/transactions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from beanie import PydanticObjectId
from bson import ObjectId
import logging

from app.models.transaction import Transaction
from app.models.transaction_schemas import (
    TransactionCreate,
    TransactionRead,
    TransactionListResponse,
)

from app.core.security import get_current_user
from app.models.user import User
from app.models.account import AllUserAccountsDocument, SubAccountDetails # Import AllUserAccountsDocument és SubAccountDetails

router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = logging.getLogger(__name__)

# ----------- POST /transactions/ -----------
@router.post("/", response_model=TransactionRead, status_code=201)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user)
):
    # Ensure amount is treated as a positive number for incomes and negative for expenses
    # and adjust based on bev_kiad_tipus
    amount = transaction_data.osszeg
    if transaction_data.bev_kiad_tipus == 'kiadas' and amount > 0:
        amount *= -1
    elif transaction_data.bev_kiad_tipus == 'bevetel' and amount < 0:
        amount *= -1

    new_transaction = Transaction(
        **transaction_data.model_dump(exclude_unset=True), # Use model_dump to convert Pydantic model to dict
        user_id=PydanticObjectId(current_user.id),
        osszeg=amount # Set the adjusted amount here
    )

    # Automatikus dátum mezők kitöltése a `before_insert` hook segítségével
    # Nem kell manuálisan hívni, Beanie kezeli: await new_transaction.insert()

    # If it's a transfer, process it
    if transaction_data.tipus == 'átutalás':
        if not transaction_data.foszamla or not transaction_data.alszamla or \
           not transaction_data.cel_foszamla or not transaction_data.cel_alszamla or \
           transaction_data.transfer_amount is None:
            raise HTTPException(status_code=400, detail="Missing fields for transfer transaction.")

        transfer_amount_float = float(transaction_data.transfer_amount)

        # Update source sub-account (deduct)
        await update_sub_account_balance(
            current_user.id,
            transaction_data.foszamla,
            transaction_data.alszamla,
            -transfer_amount_float # Deduct from source
        )

        # Update destination sub-account (add)
        await update_sub_account_balance(
            current_user.id,
            transaction_data.cel_foszamla,
            transaction_data.cel_alszamla,
            transfer_amount_float # Add to destination
        )

    # Handle income/expense for specific sub-accounts (likvid, befektetes, megtakaritas, assets)
    if transaction_data.likvid is not None:
        await update_sub_account_balance(current_user.id, 'likvid', transaction_data.alszamla, transaction_data.likvid)
    if transaction_data.befektetes is not None:
        await update_sub_account_balance(current_user.id, 'befektetes', transaction_data.alszamla, transaction_data.befektetes)
    if transaction_data.megtakaritas is not None:
        await update_sub_account_balance(current_user.id, 'megtakaritas', transaction_data.alszamla, transaction_data.megtakaritas)
    if transaction_data.assets is not None:
        # Assuming 'assets' maps to a main account, if not, adjust logic
        await update_sub_account_balance(current_user.id, 'assets', transaction_data.alszamla, transaction_data.assets)

    await new_transaction.insert()
    return TransactionRead(**new_transaction.model_dump())

# Segédfüggvény alszámla egyenleg frissítéséhez
async def update_sub_account_balance(user_id: str, main_account_key: str, sub_account_name: str, amount_change: float):
    all_accounts_doc = await AllUserAccountsDocument.find_one()

    if not all_accounts_doc or user_id not in all_accounts_doc.accounts_by_user:
        raise HTTPException(status_code=404, detail="Accounts not found for user")

    user_accounts = all_accounts_doc.accounts_by_user[user_id]
    main_account = getattr(user_accounts, main_account_key, None)

    if not main_account:
        raise HTTPException(status_code=400, detail=f"Main account {main_account_key} not found.")

    if sub_account_name not in main_account.alszamlak:
        # If sub-account doesn't exist, create it. Assuming HUF as default currency.
        main_account.alszamlak[sub_account_name] = SubAccountDetails(balance=0.0, currency="HUF")

    main_account.alszamlak[sub_account_name].balance += amount_change
    await all_accounts_doc.save()


# ----------- GET list ----------
@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    from_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="YYYY-MM-DD (inclusive)"),
    category: Optional[str] = Query(None, alias="kategoria"),
    income_only: Optional[bool] = Query(None, description="Return only bevetel (osszeg>0)"),
    expense_only: Optional[bool] = Query(None, description="Return only kiadas (osszeg<0)"),
):
    try:
        # alapfilter: csak a bevetel vagy csak a kiadas
        query_filter = {"user_id": ObjectId(current_user.id)}

        if income_only:
            query_filter["osszeg"] = {"$gt": 0}
        if expense_only:
            query_filter["osszeg"] = {"$lt": 0}

        # Dátum szerinti szűrés
        if from_date and to_date:
            query_filter["datum"] = {"$gte": from_date, "$lte": to_date}
        elif from_date:
            query_filter["datum"] = {"$gte": from_date}
        elif to_date:
            query_filter["datum"] = {"$lte": to_date}

        # Kategória szűrés
        if category:
            query_filter["kategoria"] = category

        total_count = await Transaction.find(query_filter).count()
        transactions = await Transaction.find(query_filter)\
            .sort(-Transaction.datum)\
            .skip(skip)\
            .limit(limit)\
            .to_list()

        # Konvertálás TransactionRead modellekké
        read_transactions = [
            TransactionRead(
                id=str(doc.id),
                datum=doc.datum,
                osszeg=doc.osszeg,
                user_id=str(doc.user_id),
                kategoria=doc.kategoria,
                tipus=doc.tipus,
                bev_kiad_tipus=doc.bev_kiad_tipus,
                honap=doc.honap,
                het=doc.het,
                nap_sorszam=doc.nap_sorszam,
                leiras=doc.leiras,
                deviza=doc.deviza,
                profil=doc.profil,
                forras=doc.forras,
                platform=doc.platform,
                helyszin=doc.helyszin,
                cimke=doc.cimke,
                ismetlodo=doc.ismetlodo,
                fix_koltseg=doc.fix_koltseg,
                foszamla=doc.foszamla,
                alszamla=doc.alszamla,
                cel_foszamla=doc.cel_foszamla,
                cel_alszamla=doc.cel_alszamla,
                transfer_amount=doc.transfer_amount,
                likvid=doc.likvid,
                befektetes=doc.befektetes,
                megtakaritas=doc.megtakaritas,
                assets=doc.assets,
            ) for doc in transactions
        ]

        return TransactionListResponse(
            transactions=read_transactions,
            total=total_count,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list transactions: {e}")
# ----------- GET /summary ----------
@router.get("/summary", response_model=dict)
async def get_summary(current_user: User = Depends(get_current_user)):
    try:
        # Összes tranzakció lekérdezése a felhasználóhoz
        transactions = await Transaction.find({"user_id": ObjectId(current_user.id)}).to_list()

        total_income = sum(t.osszeg for t in transactions if t.osszeg > 0)
        total_expense = sum(t.osszeg for t in transactions if t.osszeg < 0)
        net_balance = total_income + total_expense

        # Kategóriák szerinti összesítés
        category_summary = {}
        for t in transactions:
            if t.kategoria:
                if t.kategoria not in category_summary:
                    category_summary[t.kategoria] = {"income": 0.0, "expense": 0.0}
                if t.osszeg > 0:
                    category_summary[t.kategoria]["income"] += t.osszeg
                else:
                    category_summary[t.kategoria]["expense"] += t.osszeg

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_balance": net_balance,
            "category_summary": category_summary
        }
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")

# ----------- GET /{id} -----------
@router.get("/{tx_id}", response_model=TransactionRead)
async def get_transaction(tx_id: str, current_user: User = Depends(get_current_user)):
    try:
        oid = PydanticObjectId(tx_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid transaction id")

    try:
        doc = await Transaction.get(oid)
        if not doc:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Security: csak a sajat user tranzakciója
        if str(doc.user_id) != current_user.id:  # Módosítás itt: str(doc.user_id)
            raise HTTPException(status_code=403, detail="Not authorized to view this transaction")

        return TransactionRead(
            id=str(doc.id),
            datum=doc.datum,
            osszeg=doc.osszeg,
            user_id=str(doc.user_id),
            kategoria=doc.kategoria,
            tipus=doc.tipus,
            bev_kiad_tipus=doc.bev_kiad_tipus,
            honap=doc.honap,
            het=doc.het,
            nap_sorszam=doc.nap_sorszam,
            leiras=doc.leiras,
            deviza=doc.deviza,
            profil=doc.profil,
            forras=doc.forras,
            platform=doc.platform,
            helyszin=doc.helyszin,
            cimke=doc.cimke,
            ismetlodo=doc.ismetlodo,
            fix_koltseg=doc.fix_koltseg,
            foszamla=doc.foszamla,
            alszamla=doc.alszamla,
            cel_foszamla=doc.cel_foszamla,
            cel_alszamla=doc.cel_alszamla,
            transfer_amount=doc.transfer_amount,
            likvid=doc.likvid,
            befektetes=doc.befektetes,
            megtakaritas=doc.megtakaritas,
            assets=doc.assets,
        )
    except Exception as e:
        logger.error(f"Error getting transaction {tx_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get transaction: {e}")

# ----------- PUT /{id} -----------
@router.put("/{tx_id}", response_model=TransactionRead)
async def update_transaction(
    tx_id: str,
    transaction_data: TransactionCreate, # Ugyanazt a sémát használjuk a bejövő adatokra
    current_user: User = Depends(get_current_user)
):
    try:
        oid = PydanticObjectId(tx_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid transaction id")

    doc = await Transaction.get(oid)
    if not doc:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Security: csak a sajat user tranzakciója
    if str(doc.user_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this transaction")

    # Frissítjük a dokumentumot a bejövő adatokkal
    # Csak azokat a mezőket frissítjük, amik a transaction_data-ban be vannak állítva
    update_data = transaction_data.model_dump(exclude_unset=True) # exclude_unset=True ensures only provided fields are updated
    for key, value in update_data.items():
        setattr(doc, key, value)

    await doc.save()
    return TransactionRead(**doc.model_dump())

# ----------- DELETE /{id} -----------
@router.delete("/{tx_id}", status_code=204) # 204 No Content for successful deletion
async def delete_transaction(tx_id: str, current_user: User = Depends(get_current_user)):
    try:
        oid = PydanticObjectId(tx_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid transaction id")

    doc = await Transaction.get(oid)
    if not doc:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Security: csak a sajat user tranzakciója
    if str(doc.user_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this transaction")

    await doc.delete()
    return {"message": "Transaction deleted successfully"}