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
    transaction_data: TransactionCreate, # Ez a séma most már jobban egyezik
    current_user: User = Depends(get_current_user)
):
    # Az osszeg (amount) előjelének kezelése a 'type' alapján
    amount_to_save = transaction_data.amount
    if transaction_data.type == 'expense' and amount_to_save > 0:
        amount_to_save *= -1
    elif transaction_data.type == 'income' and amount_to_save < 0:
        amount_to_save *= -1

    new_transaction = Transaction(
        **transaction_data.model_dump(exclude_unset=True),
        user_id=PydanticObjectId(current_user.id)
    )

    # If it's a transfer, process it (ezt a részt felül kell vizsgálni a TransactionCreate séma alapján)
    # Jelenleg a TransactionCreate séma nem tartalmazza a forrás és cél számla mezőket transzferhez.
    # Ha transzfert is szeretnénk kezelni, a TransactionCreate sémát ki kell egészíteni a szükséges mezőkkel,
    # és a logikát is be kell építeni ide.
    if transaction_data.type == 'transfer':
        # Példa, ha a TransactionCreate tartalmazná a cél számla infókat:
        # if not transaction_data.destination_main_account or not transaction_data.destination_sub_account:
        #     raise HTTPException(status_code=400, detail="Missing destination account fields for transfer.")
        #
        # await update_sub_account_balance(
        #     current_user.id,
        #     transaction_data.main_account,
        #     transaction_data.sub_account_name,
        #     -amount_to_save # Levonás a forrás számláról
        # )
        #
        # await update_sub_account_balance(
        #     current_user.id,
        #     transaction_data.destination_main_account,
        #     transaction_data.destination_sub_account,
        #     amount_to_save # Hozzáadás a cél számlához
        # )
        raise HTTPException(status_code=501, detail="Transfer functionality not fully implemented with current schema.")


    # Handle income/expense for specific sub-accounts (likvid, befektetes, megtakaritas)
    # Ezeket a mezőket (likvid, befektetes, megtakaritas, assets) valószínűleg el kell távolítani a TransactionCreate-ből
    # ha csak az amount és main_account/sub_account_name alapján történik a frissítés.
    # Az update_sub_account_balance függvény hívása itt:
    await update_sub_account_balance(
        current_user.id,
        transaction_data.main_account,
        transaction_data.sub_account_name,
        amount_to_save
    )

    await new_transaction.insert()
    return TransactionRead(
        id=str(new_transaction.id),
        user_id=str(new_transaction.user_id),
        date=new_transaction.date,
        amount=new_transaction.amount,
        main_account=new_transaction.main_account,
        sub_account_name=new_transaction.sub_account_name,
        kategoria=new_transaction.kategoria,
        type=new_transaction.type,
        currency=new_transaction.currency,
        tranzakcio_id=new_transaction.tranzakcio_id,
        profil=new_transaction.profil,
        description=new_transaction.description,
        forras=new_transaction.forras,
        platform=new_transaction.platform,
        helyszin=new_transaction.helyszin,
        cimke=new_transaction.cimke,
        celhoz_kotott=new_transaction.celhoz_kotott,
        honap=new_transaction.honap,
        het=new_transaction.het,
        nap_sorszam=new_transaction.nap_sorszam,
        ismetlodo=new_transaction.ismetlodo,
        fix_koltseg=new_transaction.fix_koltseg,
        # Az alábbi mezők csak akkor kellenek, ha a TransactionRead séma tartalmazza őket
        # és a Transaction modell is rendelkezik velük (pl. transzfer esetén)
        # cel_foszamla=new_transaction.cel_foszamla,
        # cel_alszamla=new_transaction.cel_alszamla,
        # transfer_amount=new_transaction.transfer_amount,
        # likvid=new_transaction.likvid,
        # befektetes=new_transaction.befektetes,
        # megtakaritas=new_transaction.megtakaritas,
        # assets=new_transaction.assets,
    )


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