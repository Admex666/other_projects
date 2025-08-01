# app/routes/transactions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from beanie import PydanticObjectId
from bson import ObjectId
import logging
from datetime import datetime

from app.models.transaction import Transaction
from app.models.transaction_schemas import (
    TransactionCreate,
    TransactionRead,
    TransactionListResponse,
)
from app.core.security import get_current_user
from app.models.user import User
from app.models.account import AllUserAccountsDocument, SubAccountDetails # Import AllUserAccountsDocument és SubAccountDetails
from app.services.limit_service import LimitService
from app.services.badge_service import badge_service

router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = logging.getLogger(__name__)

# ----------- POST /transactions/ -----------
@router.post("/", response_model=TransactionRead, status_code=201)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user)
):
    # Az osszeg (amount) előjelének kezelése a 'type' alapján
    amount_to_save = transaction_data.amount
    if transaction_data.type == 'expense' and amount_to_save > 0:
        amount_to_save *= -1
    elif transaction_data.type == 'income' and amount_to_save < 0:
        amount_to_save *= -1

    # ÚJ: Limit ellenőrzés kiadásoknál
    if transaction_data.type == 'expense':
        limit_check = await LimitService.check_transaction_against_limits(
            user_id=current_user.id,
            amount=amount_to_save,
            category=transaction_data.kategoria,
            main_account=transaction_data.main_account,
            sub_account_name=transaction_data.sub_account_name
        )
        
        if not limit_check.is_allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Tranzakció limitek miatt elutasítva: {limit_check.message}"
            )

    # Alszámla devaizájának lekérzése
    all_accounts_doc = await AllUserAccountsDocument.find_one()
    if not all_accounts_doc or current_user.id not in all_accounts_doc.accounts_by_user:
        raise HTTPException(status_code=404, detail="Accounts not found for user")
    
    user_accounts = all_accounts_doc.accounts_by_user[current_user.id]
    main_account_details = getattr(user_accounts, transaction_data.main_account, None)

    if not main_account_details or transaction_data.sub_account_name not in main_account_details.alszamlak:
        # Ha az alszámla nem létezik, feltételezzük, hogy "HUF" az alapértelmezett deviza
        # vagy hibát dobunk, attól függően, hogy milyen üzleti logika a kívánatos.
        # Jelenleg a update_sub_account_balance létrehozza, ha nem létezik.
        # Itt is beállíthatjuk az alapértelmezett értéket.
        currency_to_save = "HUF" 
    else:
        currency_to_save = main_account_details.alszamlak[transaction_data.sub_account_name].currency

    new_transaction = Transaction(
        **transaction_data.model_dump(exclude={"amount"}),
        user_id=PydanticObjectId(current_user.id),
        amount=amount_to_save, # Beállítjuk a már előjellel ellátott összeget
        currency=currency_to_save # Hozzáadjuk a devizát
    )
    # Badge ellenőrzés a tranzakció létrehozása után
    try:
        earned_badges = await badge_service.check_and_award_badges(
            user_id=current_user.id,
            trigger_event="transaction_created",
            context={
                "transaction_id": str(new_transaction.id),
                "amount": abs(new_transaction.amount),
                "type": new_transaction.type,
                "category": new_transaction.kategoria
            }
        )
        
        # Itt lehetne értesítést küldeni a megszerzett badge-ekről
        if earned_badges:
            logger.info(f"User {current_user.id} earned {len(earned_badges)} badges")
            
    except Exception as e:
        logger.error(f"Badge check failed: {e}")
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
        currency=new_transaction.currency, # Itt is visszaadjuk a currencyt
        profil=new_transaction.profil,
        description=new_transaction.description,
        platform=new_transaction.platform,
        helyszin=new_transaction.helyszin,
        celhoz_kotott=new_transaction.celhoz_kotott,
        honap=new_transaction.honap,
        het=new_transaction.het,
        nap_sorszam=new_transaction.nap_sorszam,
        ismetlodo=new_transaction.ismetlodo,
        fix_koltseg=new_transaction.fix_koltseg,
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
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD (inclusive)"),
    category: Optional[str] = Query(None, alias="kategoria"),
    type: Optional[str] = Query(None, description="income vagy expense"),
):
    try:
        # Alapfilter: user_id
        query_filter = {"user_id": ObjectId(current_user.id)}

        # Típus szerinti szűrés
        if type == "income":
            query_filter["amount"] = {"$gt": 0}
        elif type == "expense":
            query_filter["amount"] = {"$lt": 0}

        # Dátum szerinti szűrés
        if start_date and end_date:
            query_filter["date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            query_filter["date"] = {"$gte": start_date}
        elif end_date:
            query_filter["date"] = {"$lte": end_date}

        # Kategória szűrés
        if category:
            query_filter["kategoria"] = category

        # MÓDOSÍTÁS: Közvetlenül a MongoDB collection-t használjuk a Pydantic validáció elkerülése érdekében
        collection = Transaction.get_motor_collection()
        
        total_count = await collection.count_documents(query_filter)
        
        # Raw dokumentumok lekérése
        cursor = collection.find(query_filter).sort("date", -1).skip(skip).limit(limit)
        raw_docs = await cursor.to_list(length=limit)

        # Konvertálás TransactionRead modellekké
        read_transactions = []
        for doc in raw_docs:
            try:
                # Dátum konvertálása string-re ha szükséges
                date_str = doc.get("date", "")
                if isinstance(date_str, datetime):
                    date_str = date_str.strftime('%Y-%m-%d')
                elif hasattr(date_str, 'strftime'):  # date objektum
                    date_str = date_str.strftime('%Y-%m-%d')
                
                read_transactions.append(TransactionRead(
                    id=str(doc["_id"]),
                    date=date_str,
                    amount=doc.get("amount", 0),
                    user_id=str(doc.get("user_id", "")),
                    kategoria=doc.get("kategoria"),
                    type=doc.get("type", ""),
                    currency=doc.get("currency", "HUF"),
                    honap=doc.get("honap"),
                    het=doc.get("het"),
                    nap_sorszam=doc.get("nap_sorszam"),
                    hour=doc.get("hour"),
                    year=doc.get("year"),
                    month=doc.get("month"),
                    day=doc.get("day"),
                    weekday=doc.get("weekday"),
                    description=doc.get("description"),
                    profil=doc.get("profil"),
                    platform=doc.get("platform"),
                    helyszin=doc.get("helyszin"),
                    ismetlodo=doc.get("ismetlodo", False),
                    fix_koltseg=doc.get("fix_koltseg", False),
                    main_account=doc.get("main_account", ""),
                    sub_account_name=doc.get("sub_account_name", ""),
                    celhoz_kotott=doc.get("celhoz_kotott", False),
                    # Computed fields
                    is_income=doc.get("amount", 0) > 0,
                    is_expense=doc.get("amount", 0) < 0,
                    absolute_amount=abs(doc.get("amount", 0)),
                ))
            except Exception as e:
                logger.error(f"Error processing transaction {doc.get('_id')}: {e}")
                continue

        return TransactionListResponse(
            transactions=read_transactions,
            total_count=total_count,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list transactions: {e}")

# ----------- GET /summary ----------
@router.get("/summary", response_model=dict)
async def get_summary(
    current_user: User = Depends(get_current_user),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    try:
        # Query filter felépítése
        query_filter = {"user_id": ObjectId(current_user.id)}
        
        # Dátum szerinti szűrés
        if start_date and end_date:
            query_filter["date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            query_filter["date"] = {"$gte": start_date}
        elif end_date:
            query_filter["date"] = {"$lte": end_date}

        # Tranzakciók lekérdezése
        transactions = await Transaction.find(query_filter).to_list()

        total_income = sum(t.amount for t in transactions if t.amount > 0)
        total_expenses = abs(sum(t.amount for t in transactions if t.amount < 0))  # Pozitív érték
        net_balance = total_income - total_expenses

        # Kategóriák szerinti összesítés
        category_summary = {}
        for t in transactions:
            if t.kategoria:
                if t.kategoria not in category_summary:
                    category_summary[t.kategoria] = {"income": 0.0, "expense": 0.0}
                if t.amount > 0:
                    category_summary[t.kategoria]["income"] += t.amount
                else:
                    category_summary[t.kategoria]["expense"] += abs(t.amount)

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,  # total_expense helyett total_expenses
            "net_balance": net_balance,
            "transaction_count": len(transactions),
            "category_summary": category_summary,
            "period_start": start_date,
            "period_end": end_date,
        }
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {e}")

# ----------- GET /{id} -----------
@router.get("/{tx_id}", response_model=TransactionRead)
async def get_transaction(tx_id: str, current_user: User = Depends(get_current_user)):
    try:
        oid = PydanticObjectId(tx_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid transaction id")

    try:
        # Raw dokumentum lekérése
        collection = Transaction.get_motor_collection()
        doc = await collection.find_one({"_id": ObjectId(tx_id)})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Security: csak a sajat user tranzakciója
        if str(doc["user_id"]) != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this transaction")

        # Dátum konvertálása
        date_str = doc.get("date", "")
        if isinstance(date_str, datetime):
            date_str = date_str.strftime('%Y-%m-%d')
        elif hasattr(date_str, 'strftime'):
            date_str = date_str.strftime('%Y-%m-%d')

        return TransactionRead(
            id=str(doc["_id"]),
            date=date_str,
            amount=doc.get("amount", 0),
            user_id=str(doc.get("user_id", "")),
            kategoria=doc.get("kategoria"),
            type=doc.get("type", ""),
            currency=doc.get("currency", "HUF"),
            honap=doc.get("honap"),
            het=doc.get("het"),
            nap_sorszam=doc.get("nap_sorszam"),
            hour=doc.get("hour"),
            year=doc.get("year"),
            month=doc.get("month"),
            day=doc.get("day"),
            weekday=doc.get("weekday"),
            description=doc.get("description"),
            profil=doc.get("profil"),
            platform=doc.get("platform"),
            helyszin=doc.get("helyszin"),
            ismetlodo=doc.get("ismetlodo", False),
            fix_koltseg=doc.get("fix_koltseg", False),
            main_account=doc.get("main_account", ""),
            sub_account_name=doc.get("sub_account_name", ""),
            celhoz_kotott=doc.get("celhoz_kotott", False),
            # Computed fields
            is_income=doc.get("amount", 0) > 0,
            is_expense=doc.get("amount", 0) < 0,
            absolute_amount=abs(doc.get("amount", 0)),
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

    # Ellenőrizzük, hogy a 'type' és az 'amount' konzisztens legyen, ha módosul
    if 'amount' in update_data and 'type' in update_data:
        amount_to_save = update_data['amount']
        if update_data['type'] == 'expense' and amount_to_save > 0:
            update_data['amount'] *= -1
        elif update_data['type'] == 'income' and amount_to_save < 0:
            update_data['amount'] *= -1
    elif 'amount' in update_data and doc.type: # Ha csak az amount változik, de a type már létezik
        amount_to_save = update_data['amount']
        if doc.type == 'expense' and amount_to_save > 0:
            update_data['amount'] *= -1
        elif doc.type == 'income' and amount_to_save < 0:
            update_data['amount'] *= -1
    elif 'type' in update_data and doc.amount: # Ha csak a type változik, de az amount már létezik
        amount_to_save = doc.amount
        if update_data['type'] == 'expense' and amount_to_save > 0:
            update_data['amount'] = -amount_to_save
        elif update_data['type'] == 'income' and amount_to_save < 0:
            update_data['amount'] = -amount_to_save


    # Alszámla devizájának frissítése, ha a fő- vagy alszámla változik
    # Fontos: Ha a fő- vagy alszámla változik, akkor a devizát is újra kell kérni
    # a `transactions.py` file elején definiált `AllUserAccountsDocument`-ből
    if 'main_account' in update_data or 'sub_account_name' in update_data:
        all_accounts_doc = await AllUserAccountsDocument.find_one()
        if not all_accounts_doc or current_user.id not in all_accounts_doc.accounts_by_user:
            raise HTTPException(status_code=404, detail="Accounts not found for user")
        
        user_accounts = all_accounts_doc.accounts_by_user[current_user.id]
        
        # A frissített fő- és alszámla nevek, vagy az eredeti dokumentumból
        updated_main_account = update_data.get('main_account', doc.main_account)
        updated_sub_account_name = update_data.get('sub_account_name', doc.sub_account_name)

        main_account_details = getattr(user_accounts, updated_main_account, None)

        if not main_account_details or updated_sub_account_name not in main_account_details.alszamlak:
            # Ha az alszámla nem létezik, feltételezzük, hogy "HUF" az alapértelmezett deviza
            update_data['currency'] = "HUF" 
        else:
            update_data['currency'] = main_account_details.alszamlak[updated_sub_account_name].currency

    for key, value in update_data.items():
        setattr(doc, key, value)

    await doc.save()
    doc_dict = doc.model_dump()
    doc_dict['id'] = str(doc.id)
    doc_dict['user_id'] = str(doc.user_id)
    return TransactionRead(**doc_dict)

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

# ----------- STATS -----------
@router.get("/stats", response_model=dict)
async def get_stats(
    current_user: User = Depends(get_current_user),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    """Stats endpoint - ugyanaz mint a summary, de más néven"""
    return await get_summary(current_user, start_date, end_date)