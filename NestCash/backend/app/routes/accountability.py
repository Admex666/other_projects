# app/routes/accountability.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from beanie import PydanticObjectId
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from app.core.security import get_current_user
from app.models.user import User, UserDocument
from app.models.accountability_models import (
    AccountabilityProfile, Partnership, CheckIn, PartnershipStatus
)
from app.models.accountability_schemas import (
    AccountabilityProfileCreate, AccountabilityProfileUpdate, AccountabilityProfileRead,
    PartnershipRequest, PartnershipResponse, PartnershipRead,
    CheckInCreate, CheckInRead, PartnerSuggestionRead
)
from app.services.accountability_service import AccountabilityService

router = APIRouter(prefix="/accountability", tags=["accountability"])

# === PROFILE MANAGEMENT ===

@router.post("/profile", response_model=AccountabilityProfileRead, status_code=201)
async def create_accountability_profile(
    profile_data: AccountabilityProfileCreate,
    current_user: User = Depends(get_current_user)
):
    """Accountability profil létrehozása"""
    # Ellenőrizzük, hogy már van-e profil
    existing = await AccountabilityProfile.find_one({"user_id": PydanticObjectId(current_user.id)})
    if existing:
        raise HTTPException(status_code=409, detail="Már létezik accountability profil")
    
    profile = AccountabilityProfile(
        user_id=PydanticObjectId(current_user.id),
        **profile_data.model_dump()
    )
    await profile.insert()
    
    return AccountabilityProfileRead(
        id=str(profile.id),
        user_id=str(profile.user_id),
        **profile.model_dump(exclude={"id", "user_id"})
    )

@router.get("/profile", response_model=AccountabilityProfileRead)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Saját accountability profil lekérése"""
    profile = await AccountabilityProfile.find_one({"user_id": PydanticObjectId(current_user.id)})
    if not profile:
        raise HTTPException(status_code=404, detail="Accountability profil nem található")
    
    return AccountabilityProfileRead(
        id=str(profile.id),
        user_id=str(profile.user_id),
        **profile.model_dump(exclude={"id", "user_id"})
    )

# === MATCHING ===

@router.get("/suggestions", response_model=List[PartnerSuggestionRead])
async def get_partner_suggestions(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
):
    """Partner javaslatok lekérése (csak Plus/Pro felhasználóknak)"""
    # Előfizetés ellenőrzése
    from app.services.permission_service import PermissionService
    
    # Ellenőrizzük, hogy van-e hozzáférése a matching funkcióhoz
    # FREE felhasználók csak kereshetnek, nem használhatják a matching-et
    subscription = await PermissionService.get_user_subscription(current_user.id)
    if subscription.tier.value == "free":
        raise HTTPException(
            status_code=403, 
            detail="Matching funkció csak Plus és Pro előfizetőknek elérhető"
        )
    
    suggestions = await AccountabilityService.get_partner_suggestions(
        user_id=current_user.id,
        limit=limit
    )
    
    return suggestions

# === PARTNERSHIPS ===

@router.get("/partnerships", response_model=List[PartnershipRead])
async def get_my_partnerships(
    current_user: User = Depends(get_current_user),
    status: Optional[PartnershipStatus] = Query(None)
):
    """Saját partnership-ek lekérése"""
    query_filter = {
        "$or": [
            {"requester_id": PydanticObjectId(current_user.id)},
            {"requested_id": PydanticObjectId(current_user.id)}
        ]
    }
    
    if status:
        query_filter["status"] = status
    
    partnerships = await Partnership.find(query_filter).sort(-Partnership.created_at).to_list()
    
    # Partner adatok lekérése és konvertálás
    result = []
    for partnership in partnerships:
        # JAVÍTÁS: is_incoming logika javítása
        # is_incoming = True ha a current_user a requested_id (őt kérték meg)
        is_incoming = str(partnership.requested_id) == current_user.id
        
        # Partner ID meghatározása
        partner_id = (partnership.requester_id 
                     if is_incoming  # ha bejövő, akkor a requester a partner
                     else partnership.requested_id)  # ha kimenő, akkor a requested a partner
        
        partner_user = await UserDocument.get(partner_id)
        
        # DEBUG logging
        logger.info(f"Partnership {partnership.id}: current_user={current_user.id}, "
                   f"requester={partnership.requester_id}, requested={partnership.requested_id}, "
                   f"is_incoming={is_incoming}, partner_id={partner_id}")
        
        result.append(PartnershipRead(
            id=str(partnership.id),
            partner_user_id=str(partner_id),
            partner_username=partner_user.username if partner_user else "Ismeretlen",
            status=partnership.status,
            checkin_frequency=partnership.checkin_frequency,
            shared_goals=partnership.shared_goals,
            created_at=partnership.created_at,
            accepted_at=partnership.accepted_at,
            total_checkins=partnership.total_checkins,
            successful_checkins=partnership.successful_checkins,
            is_incoming=is_incoming  # Ez a kulcs mező!
        ))
    
    return result

@router.post("/partnerships/request", status_code=201)
async def request_partnership(
    request_data: PartnershipRequest,
    current_user: User = Depends(get_current_user)
):
    """Partnership kérelem küldése"""
    # Partner limit ellenőrzése
    can_add, current_count, limit = await AccountabilityService.check_partnership_limit(current_user.id)
    
    if not can_add:
        raise HTTPException(
            status_code=403,
            detail=f"Elérted a partner limitet ({current_count}/{limit}). Előfizetés frissítés szükséges."
        )
    
    # Létrehozás
    partnership = await AccountabilityService.create_partnership_request(
        requester_id=current_user.id,
        requested_id=request_data.target_user_id,  # <-- "requested_user_id" helyett "target_user_id"
        checkin_frequency=request_data.checkin_frequency,
        shared_goals=request_data.shared_goals
    )
    
    return {"message": "Partnership kérelem elküldve", "partnership_id": str(partnership.id)}

# === CHECK-INS ===

@router.post("/partnerships/{partnership_id}/checkins", response_model=CheckInRead, status_code=201)
async def create_checkin(
    partnership_id: str,
    checkin_data: CheckInCreate,
    current_user: User = Depends(get_current_user)
):
    """Check-in létrehozása"""
    # Partnership ellenőrzése
    partnership = await Partnership.get(PydanticObjectId(partnership_id))
    if not partnership:
        raise HTTPException(status_code=404, detail="Partnership nem található")
    
    user_in_partnership = (
        str(partnership.requester_id) == current_user.id or 
        str(partnership.requested_id) == current_user.id
    )
    
    if not user_in_partnership:
        raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a partnership-hez")
    
    if partnership.status != PartnershipStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Partnership nem aktív")
    
    checkin = await AccountabilityService.create_checkin(
        partnership_id=partnership_id,
        user_id=current_user.id,
        goals_met=checkin_data.goals_met,
        progress_rating=checkin_data.progress_rating,
        notes=checkin_data.notes,
        habit_completions=checkin_data.habit_completions
    )
    
    return CheckInRead(
        id=str(checkin.id),
        partnership_id=str(checkin.partnership_id),
        user_id=str(checkin.user_id),
        date=checkin.date,
        goals_met=checkin.goals_met,
        progress_rating=checkin.progress_rating,
        notes=checkin.notes,
        created_at=checkin.created_at
    )

@router.post("/partnerships/{partnership_id}/respond", status_code=200)
async def respond_to_partnership(
    partnership_id: str,
    response_data: PartnershipResponse,
    current_user: User = Depends(get_current_user)
):
    """Partnership kérelemre válaszadás (elfogadás/elutasítás)"""
    try:
        # Partnership lekérése
        partnership = await Partnership.get(PydanticObjectId(partnership_id))
        if not partnership:
            raise HTTPException(status_code=404, detail="Partnership nem található")
        
        # Debug logging
        logger.info(f"Current user ID: {current_user.id}")
        logger.info(f"Partnership requester_id: {partnership.requester_id}")
        logger.info(f"Partnership requested_id: {partnership.requested_id}")
        logger.info(f"Partnership status: {partnership.status}")
        
        # Ellenőrizzük, hogy a felhasználó jogosult-e válaszolni
        # Csak a requested_id (megkért felhasználó) válaszolhat
        current_user_obj_id = PydanticObjectId(current_user.id)
        if partnership.requested_id != current_user_obj_id:
            logger.warning(f"Access denied. User {current_user.id} tried to respond to partnership where they are not the requested party. Requester: {partnership.requester_id}, Requested: {partnership.requested_id}")
            raise HTTPException(status_code=403, detail="Csak a megkért felhasználó válaszolhat a kérelemre")
        
        # Ellenőrizzük, hogy még pending státuszban van-e
        if partnership.status != PartnershipStatus.PENDING:
            raise HTTPException(status_code=400, detail="Ez a partnership kérelem már feldolgozva lett")
        
        # Válasz feldolgozása
        if response_data.accept:
            partnership.status = PartnershipStatus.ACTIVE
            partnership.accepted_at = datetime.utcnow()
        else:
            partnership.status = PartnershipStatus.DECLINED
        
        await partnership.save()
        
        return {
            "message": "Partnership elfogadva" if response_data.accept else "Partnership elutasítva",
            "partnership_id": str(partnership.id),
            "status": partnership.status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to partnership: {e}")
        raise HTTPException(status_code=500, detail="Hiba a partnership válasz feldolgozása során")