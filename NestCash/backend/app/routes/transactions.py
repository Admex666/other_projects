# app/routes/transactions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from beanie import PydanticObjectId

from app.models.transaction import Transaction
from app.models.transaction_schemas import (
    TransactionCreate,
    TransactionRead,
    TransactionListResponse,
)

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/transactions", tags=["transactions"])

# ----------- GET list -----------
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
    # alapfilter: csak a bejelentkezett user tranzakciói
    filters = {"user_id": current_user.user_id if hasattr(current_user, "user_id") else None}
    # ha nincs user_id meződ a User modellben: user_id helyett username vagy email -> DB-ben tárold!
    # ÉS: ha DB-ben integer user_id nincs, akkor változtasd: filters = {"username": current_user.username}

    # Ha nincs user_id attr a current_user-en, dobd ki:
    if filters["user_id"] is None:
        raise HTTPException(status_code=500, detail="User model missing user_id for filtering.")

    # további filterek
    if from_date and to_date:
        filters["datum"] = {"$gte": from_date, "$lte": to_date}
    elif from_date:
        filters["datum"] = {"$gte": from_date}
    elif to_date:
        filters["datum"] = {"$lte": to_date}

    if category:
        filters["kategoria"] = category

    if income_only and expense_only:
        # értelmetlen – felülbíráljuk
        income_only = None
        expense_only = None

    # Query build
    q = Transaction.find(filters)

    # income / expense fallback osszeg alapján
    if income_only:
        q = q.find(Transaction.osszeg > 0)  # Beanine query expression
    elif expense_only:
        q = q.find(Transaction.osszeg < 0)

    total = await q.count()
    docs = await q.skip(skip).limit(limit).sort(-Transaction.datum).to_list()

    items = [
        TransactionRead(
            id=str(d.id),
            datum=d.datum,
            osszeg=d.osszeg,
            user_id=d.user_id,
            kategoria=d.kategoria,
            tipus=d.tipus,
            bev_kiad_tipus=d.bev_kiad_tipus,
            honap=d.honap,
            het=d.het,
            nap_sorszam=d.nap_sorszam,
            leiras=d.leiras,
            deviza=d.deviza,
        )
        for d in docs
    ]

    return TransactionListResponse(total=total, items=items)

# ----------- POST create -----------
@router.post("/", response_model=TransactionRead, status_code=201)
async def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Létrehoz egy tranzakciót a bejelentkezett userhez.
    user_id a tokenből (current_user) származik – felülírja a payload user_id-ját biztonság kedvéért.
    """
    # Biztonság: user_id forcing – ha nincs user_id a current_user-en, át kell tervezni
    user_id = getattr(current_user, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=500, detail="Current user has no user_id; cannot create transaction.")

    doc = Transaction(
        datum=payload.datum,
        osszeg=payload.osszeg,
        user_id=user_id,
        kategoria=payload.kategoria,
        tipus=payload.tipus,
        bev_kiad_tipus=payload.bev_kiad_tipus,
        leiras=payload.leiras,
        deviza=payload.deviza,
        profil=payload.profil,
        forras=payload.forras,
        platform=payload.platform,
        helyszin=payload.helyszin,
        cimke=payload.cimke,
        ismetlodo=payload.ismetlodo,
        fix_koltseg=payload.fix_koltseg,
        foszamla=payload.foszamla,
        alszamla=payload.alszamla,
        cel_foszamla=payload.cel_foszamla,
        cel_alszamla=payload.cel_alszamla,
        transfer_amount=payload.transfer_amount,
        likvid=payload.likvid,
        befektetes=payload.befektetes,
        megtakaritas=payload.megtakaritas,
        assets=payload.assets,
    )
    await doc.insert()

    return TransactionRead(
        id=str(doc.id),
        datum=doc.datum,
        osszeg=doc.osszeg,
        user_id=doc.user_id,
        kategoria=doc.kategoria,
        tipus=doc.tipus,
        bev_kiad_tipus=doc.bev_kiad_tipus,
        honap=doc.honap,
        het=doc.het,
        nap_sorszam=doc.nap_sorszam,
        leiras=doc.leiras,
        deviza=doc.deviza,
    )

# ----------- GET /{id} -----------
@router.get("/{tx_id}", response_model=TransactionRead)
async def get_transaction(tx_id: str, current_user: User = Depends(get_current_user)):
    try:
        oid = PydanticObjectId(tx_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid transaction id")

    doc = await Transaction.get(oid)
    if not doc:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Security: csak a sajat user tranzakciója
    user_id = getattr(current_user, "user_id", None)
    if user_id is None or doc.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this transaction")

    return TransactionRead(
        id=str(doc.id),
        datum=doc.datum,
        osszeg=doc.osszeg,
        user_id=doc.user_id,
        kategoria=doc.kategoria,
        tipus=doc.tipus,
        bev_kiad_tipus=doc.bev_kiad_tipus,
        honap=doc.honap,
        het=doc.het,
        nap_sorszam=doc.nap_sorszam,
        leiras=doc.leiras,
        deviza=doc.deviza,
    )

@router.get("/summary")
async def transactions_summary(
    current_user: User = Depends(get_current_user),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    group_by: str = "honap",  # honap | kategoria | tipus
):
    user_id = getattr(current_user, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=500, detail="Current user missing user_id.")

    match_stage = {"user_id": user_id}
    if from_date and to_date:
        match_stage["datum"] = {"$gte": from_date, "$lte": to_date}
    elif from_date:
        match_stage["datum"] = {"$gte": from_date}
    elif to_date:
        match_stage["datum"] = {"$lte": to_date}

    if group_by not in {"honap", "kategoria", "tipus"}:
        raise HTTPException(status_code=400, detail="Invalid group_by")

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": f"${group_by}",
            "ossz_osszeg": {"$sum": "$osszeg"},
            "count": {"$sum": 1},
            # bevetelek / kiadasok külön (osszeg előjel alapján)
            "bevetel": {"$sum": {"$cond": [{"$gt": ["$osszeg", 0]}, "$osszeg", 0]}},
            "kiadas": {"$sum": {"$cond": [{"$lt": ["$osszeg", 0]}, "$osszeg", 0]}},
        }},
        {"$sort": {"_id": 1}},
    ]

    # közvetlen Motor pipeline (Beanie Documentből collection)
    coll = Transaction.get_motor_collection()
    result = await coll.aggregate(pipeline).to_list(length=1000)

    # tisztítás: _id -> label
    parsed = []
    for row in result:
        parsed.append({
            group_by: row["_id"],
            "ossz_osszeg": row["ossz_osszeg"],
            "bevetel": row["bevetel"],
            "kiadas": row["kiadas"],
            "count": row["count"],
        })
    return {"group_by": group_by, "rows": parsed}
