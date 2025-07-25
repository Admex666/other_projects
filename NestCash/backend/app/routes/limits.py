# app/routes/limits.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from beanie import PydanticObjectId
from datetime import datetime
import logging

from app.models.limit import Limit, LimitType, LimitPeriod
from app.models.limit_schemas import (
    LimitCreate, LimitRead, LimitUpdate, LimitListResponse,
    LimitUsage, LimitCheckResult, LimitStatus
)
from app.models.transaction import Transaction
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/limits", tags=["limits"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=LimitRead, status_code=201)
async def create_limit(
    limit_data: LimitCreate,
    current_user: User = Depends(get_current_user)
):
    """Új limit létrehozása"""
    try:
        # Ellenőrizzük, hogy már létezik-e hasonló limit
        existing = await Limit.find_one(
            Limit.user_id == PydanticObjectId(current_user.id),
            Limit.name == limit_data.name,
            Limit.is_active == True
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Már létezik aktív limit ezzel a névvel"
            )
        
        new_limit = Limit(
            user_id=PydanticObjectId(current_user.id),
            **limit_data.model_dump()
        )
        await new_limit.insert()
        
        return LimitRead(
            id=str(new_limit.id),
            user_id=str(new_limit.user_id),
            **new_limit.model_dump(exclude={"id", "user_id"})
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating limit: {e}")
        raise HTTPException(status_code=500, detail="Limit létrehozása sikertelen")

@router.get("/", response_model=LimitListResponse)
async def get_limits(
    current_user: User = Depends(get_current_user),
    active_only: bool = Query(True, description="Csak aktív limitek"),
    limit_type: Optional[LimitType] = Query(None, description="Szűrés típus szerint")
):
    """Felhasználó limiteinek lekérdezése"""
    try:
        query = Limit.find(Limit.user_id == PydanticObjectId(current_user.id))
        
        if active_only:
            query = query.find(Limit.is_active == True)
        
        if limit_type:
            query = query.find(Limit.type == limit_type)
        
        limits = await query.sort(-Limit.created_at).to_list()
        
        # Számítások hozzáadása
        limits_with_usage = []
        for limit in limits:
            current_spending = await get_current_spending(current_user.id, limit)
            
            limit_read = LimitRead(
                id=str(limit.id),
                user_id=str(limit.user_id),
                current_spending=current_spending,
                remaining_amount=max(0, limit.amount - current_spending),
                usage_percentage=min(100, (current_spending / limit.amount) * 100),
                period_start=limit.get_period_start(),
                period_end=limit.get_period_end(),
                **limit.model_dump(exclude={"id", "user_id"})
            )
            limits_with_usage.append(limit_read)
        
        active_count = sum(1 for l in limits if l.is_active)
        
        return LimitListResponse(
            limits=limits_with_usage,
            total_count=len(limits),
            active_count=active_count
        )
    except Exception as e:
        logger.error(f"Error getting limits: {e}")
        raise HTTPException(status_code=500, detail="Limitek lekérdezése sikertelen")

@router.get("/{limit_id}", response_model=LimitRead)
async def get_limit(
    limit_id: str,
    current_user: User = Depends(get_current_user)
):
    """Egy konkrét limit lekérdezése"""
    try:
        limit = await Limit.get(PydanticObjectId(limit_id))
        if not limit:
            raise HTTPException(status_code=404, detail="Limit nem található")
        
        if str(limit.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a limithez")
        
        current_spending = await get_current_spending(current_user.id, limit)
        
        return LimitRead(
            id=str(limit.id),
            user_id=str(limit.user_id),
            current_spending=current_spending,
            remaining_amount=max(0, limit.amount - current_spending),
            usage_percentage=min(100, (current_spending / limit.amount) * 100),
            period_start=limit.get_period_start(),
            period_end=limit.get_period_end(),
            **limit.model_dump(exclude={"id", "user_id"})
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting limit {limit_id}: {e}")
        raise HTTPException(status_code=500, detail="Limit lekérdezése sikertelen")

@router.put("/{limit_id}", response_model=LimitRead)
async def update_limit(
    limit_id: str,
    limit_data: LimitUpdate,
    current_user: User = Depends(get_current_user)
):
    """Limit frissítése"""
    try:
        limit = await Limit.get(PydanticObjectId(limit_id))
        if not limit:
            raise HTTPException(status_code=404, detail="Limit nem található")
        
        if str(limit.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a limithez")
        
        # Frissítjük csak a megadott mezőket
        update_data = limit_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(limit, key, value)
        
        await limit.save()
        
        current_spending = await get_current_spending(current_user.id, limit)
        
        return LimitRead(
            id=str(limit.id),
            user_id=str(limit.user_id),
            current_spending=current_spending,
            remaining_amount=max(0, limit.amount - current_spending),
            usage_percentage=min(100, (current_spending / limit.amount) * 100),
            period_start=limit.get_period_start(),
            period_end=limit.get_period_end(),
            **limit.model_dump(exclude={"id", "user_id"})
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating limit {limit_id}: {e}")
        raise HTTPException(status_code=500, detail="Limit frissítése sikertelen")

@router.delete("/{limit_id}", status_code=204)
async def delete_limit(
    limit_id: str,
    current_user: User = Depends(get_current_user)
):
    """Limit törlése"""
    try:
        limit = await Limit.get(PydanticObjectId(limit_id))
        if not limit:
            raise HTTPException(status_code=404, detail="Limit nem található")
        
        if str(limit.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a limithez")
        
        await limit.delete()
        return {"message": "Limit sikeresen törölve"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting limit {limit_id}: {e}")
        raise HTTPException(status_code=500, detail="Limit törlése sikertelen")

@router.post("/check", response_model=LimitCheckResult)
async def check_limits(
    amount: float,
    category: Optional[str] = None,
    main_account: Optional[str] = None,
    sub_account_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Tranzakció létrehozása előtt limitek ellenőrzése"""
    try:
        # Csak negatív összegeket (kiadásokat) ellenőrizzük
        if amount >= 0:
            return LimitCheckResult(is_allowed=True)
        
        exceeded_limits = []
        warnings = []
        
        # Aktív limitek lekérdezése
        active_limits = await Limit.find(
            Limit.user_id == PydanticObjectId(current_user.id),
            Limit.is_active == True
        ).to_list()
        
        for limit in active_limits:
            current_spending = await get_current_spending(current_user.id, limit)
            projected_spending = current_spending + abs(amount)
            
            # Ellenőrizzük, hogy a limit vonatkozik-e erre a tranzakcióra
            if not applies_to_transaction(limit, category, main_account, sub_account_name):
                continue
            
            if projected_spending > limit.amount:
                exceeded_limits.append(f"{limit.name} ({limit.amount} {limit.currency})")
            elif (limit.notification_threshold and 
                  (projected_spending / limit.amount) * 100 >= limit.notification_threshold):
                warnings.append(f"{limit.name}: {(projected_spending/limit.amount)*100:.1f}% elérve")
        
        is_allowed = len(exceeded_limits) == 0
        message = None
        
        if exceeded_limits:
            message = f"A következő limitek túllépnének: {', '.join(exceeded_limits)}"
        elif warnings:
            message = f"Figyelem: {', '.join(warnings)}"
        
        return LimitCheckResult(
            is_allowed=is_allowed,
            exceeded_limits=exceeded_limits,
            warnings=warnings,
            message=message
        )
    except Exception as e:
        logger.error(f"Error checking limits: {e}")
        raise HTTPException(status_code=500, detail="Limit ellenőrzés sikertelen")

@router.get("/status/overview", response_model=LimitStatus)
async def get_limits_status(current_user: User = Depends(get_current_user)):
    """Limitek státusz összesítője"""
    try:
        all_limits = await Limit.find(
            Limit.user_id == PydanticObjectId(current_user.id)
        ).to_list()
        
        active_limits = [l for l in all_limits if l.is_active]
        exceeded_count = 0
        warning_count = 0
        
        for limit in active_limits:
            current_spending = await get_current_spending(current_user.id, limit)
            usage_percentage = (current_spending / limit.amount) * 100
            
            if current_spending > limit.amount:
                exceeded_count += 1
            elif (limit.notification_threshold and 
                  usage_percentage >= limit.notification_threshold):
                warning_count += 1
        
        return LimitStatus(
            total_limits=len(all_limits),
            active_limits=len(active_limits),
            exceeded_limits=exceeded_count,
            warning_limits=warning_count
        )
    except Exception as e:
        logger.error(f"Error getting limits status: {e}")
        raise HTTPException(status_code=500, detail="Limit státusz lekérdezése sikertelen")

# Segédfüggvények

async def get_current_spending(user_id: str, limit: Limit) -> float:
    """Aktuális kiadás számítása a limit alapján"""
    period_start = limit.get_period_start()
    period_end = limit.get_period_end()
    
    # Alapszűrő: felhasználó és időszak
    query_filter = {
        "user_id": PydanticObjectId(user_id),
        "date": {
            "$gte": period_start.strftime("%Y-%m-%d"),
            "$lte": period_end.strftime("%Y-%m-%d")
        },
        "amount": {"$lt": 0}  # Csak kiadások
    }
    
    # Típus specifikus szűrés
    if limit.type == LimitType.CATEGORY and limit.category:
        query_filter["kategoria"] = limit.category
    elif limit.type == LimitType.ACCOUNT:
        if limit.main_account:
            query_filter["main_account"] = limit.main_account
        if limit.sub_account_name:
            query_filter["sub_account_name"] = limit.sub_account_name
    
    transactions = await Transaction.find(query_filter).to_list()
    return abs(sum(t.amount for t in transactions))

def applies_to_transaction(
    limit: Limit, 
    category: Optional[str], 
    main_account: Optional[str], 
    sub_account_name: Optional[str]
) -> bool:
    """Ellenőrzi, hogy a limit vonatkozik-e a tranzakcióra"""
    if limit.type == LimitType.SPENDING:
        return True  # Általános kiadási limit minderre vonatkozik
    elif limit.type == LimitType.CATEGORY:
        return limit.category == category
    elif limit.type == LimitType.ACCOUNT:
        account_match = True
        if limit.main_account and limit.main_account != main_account:
            account_match = False
        if limit.sub_account_name and limit.sub_account_name != sub_account_name:
            account_match = False
        return account_match
    
    return False