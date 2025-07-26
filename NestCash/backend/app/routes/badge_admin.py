# app/routes/badge_admin.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from beanie import PydanticObjectId

from app.core.security import get_current_user
from app.models.user import User
from app.models.badge import BadgeType, UserBadge, BadgeCategory, BadgeRarity, BadgeTypeRead
from app.models.badge_schemas import BadgeTypeCreate, BadgeTypeUpdate
from app.services.badge_service import badge_service

router = APIRouter(prefix="/admin/badges", tags=["badge-admin"])

# TODO: Implementálni admin jogosultság ellenőrzést
def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Admin jogosultság ellenőrzése - jelenleg minden bejelentkezett felhasználó admin"""
    # Itt implementálható a tényleges admin ellenőrzés
    return current_user

@router.get("/types", response_model=List[BadgeTypeRead])
async def get_all_badge_types(
    admin_user: User = Depends(get_admin_user),
    category: Optional[BadgeCategory] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Összes badge típus lekérése admin célokra"""
    try:
        query = {}
        
        if category:
            query["category"] = category
        
        if is_active is not None:
            query["is_active"] = is_active
        
        badge_types = await BadgeType.find(query).sort("category", "name").to_list()
        
        return [
            BadgeTypeRead(
                id=str(bt.id),
                code=bt.code,
                name=bt.name,
                description=bt.description,
                icon=bt.icon,
                color=bt.color,
                image_url=bt.image_url,
                category=bt.category,
                rarity=bt.rarity,
                condition_type=bt.condition_type,
                condition_config=bt.condition_config,
                is_active=bt.is_active,
                is_repeatable=bt.is_repeatable,
                points=bt.points,
                has_levels=bt.has_levels,
                max_level=bt.max_level
            )
            for bt in badge_types
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge típusok lekérése sikertelen: {str(e)}")

@router.post("/types", response_model=BadgeTypeRead, status_code=201)
async def create_badge_type(
    badge_data: BadgeTypeCreate,
    admin_user: User = Depends(get_admin_user)
):
    """Új badge típus létrehozása"""
    try:
        # Ellenőrizzük, hogy már létezik-e ilyen kódú badge
        existing = await BadgeType.find_one({"code": badge_data.code})
        if existing:
            raise HTTPException(status_code=409, detail="Már létezik badge ezzel a kóddal")
        
        new_badge_type = BadgeType(**badge_data.model_dump())
        await new_badge_type.insert()
        
        return BadgeTypeRead(
            id=str(new_badge_type.id),
            code=new_badge_type.code,
            name=new_badge_type.name,
            description=new_badge_type.description,
            icon=new_badge_type.icon,
            color=new_badge_type.color,
            image_url=new_badge_type.image_url,
            category=new_badge_type.category,
            rarity=new_badge_type.rarity,
            condition_type=new_badge_type.condition_type,
            condition_config=new_badge_type.condition_config,
            is_active=new_badge_type.is_active,
            is_repeatable=new_badge_type.is_repeatable,
            points=new_badge_type.points,
            has_levels=new_badge_type.has_levels,
            max_level=new_badge_type.max_level
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge típus létrehozása sikertelen: {str(e)}")

@router.put("/types/{badge_type_id}", response_model=BadgeTypeRead)
async def update_badge_type(
    badge_type_id: str,
    badge_data: BadgeTypeUpdate,
    admin_user: User = Depends(get_admin_user)
):
    """Badge típus frissítése"""
    try:
        badge_type = await BadgeType.get(PydanticObjectId(badge_type_id))
        if not badge_type:
            raise HTTPException(status_code=404, detail="Badge típus nem található")
        
        # Frissítjük a megadott mezőket
        update_data = badge_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(badge_type, key, value)
        
        from datetime import datetime
        badge_type.updated_at = datetime.utcnow()
        await badge_type.save()
        
        return BadgeTypeRead(
            id=str(badge_type.id),
            code=badge_type.code,
            name=badge_type.name,
            description=badge_type.description,
            icon=badge_type.icon,
            color=badge_type.color,
            image_url=badge_type.image_url,
            category=badge_type.category,
            rarity=badge_type.rarity,
            condition_type=badge_type.condition_type,
            condition_config=badge_type.condition_config,
            is_active=badge_type.is_active,
            is_repeatable=badge_type.is_repeatable,
            points=badge_type.points,
            has_levels=badge_type.has_levels,
            max_level=badge_type.max_level
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge típus frissítése sikertelen: {str(e)}")

@router.delete("/types/{badge_type_id}", status_code=204)
async def delete_badge_type(
    badge_type_id: str,
    admin_user: User = Depends(get_admin_user)
):
    """Badge típus törlése"""
    try:
        badge_type = await BadgeType.get(PydanticObjectId(badge_type_id))
        if not badge_type:
            raise HTTPException(status_code=404, detail="Badge típus nem található")
        
        # Ellenőrizzük, hogy van-e felhasználó aki már megszerezte
        user_count = await UserBadge.find({"badge_code": badge_type.code}).count()
        if user_count > 0:
            raise HTTPException(
                status_code=409, 
                detail=f"Nem törölhető, {user_count} felhasználó már megszerezte ezt a badge-et"
            )
        
        await badge_type.delete()
        return {"message": "Badge típus sikeresen törölve"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge típus törlése sikertelen: {str(e)}")

@router.post("/award")
async def award_badge_manually(
    user_id: str,
    badge_code: str,
    admin_user: User = Depends(get_admin_user)
):
    """Badge manuális odaítélése felhasználónak"""
    try:
        from app.models.user import UserDocument
        
        # Ellenőrizzük, hogy létezik-e a felhasználó
        user = await UserDocument.get(PydanticObjectId(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="Felhasználó nem található")
        
        # Ellenőrizzük, hogy létezik-e a badge típus
        badge_type = await BadgeType.find_one({"code": badge_code})
        if not badge_type:
            raise HTTPException(status_code=404, detail="Badge típus nem található")
        
        # Ellenőrizzük, hogy már megkapta-e (ha nem ismételhető)
        if not badge_type.is_repeatable:
            existing = await UserBadge.find_one({
                "user_id": PydanticObjectId(user_id),
                "badge_code": badge_code
            })
            if existing:
                raise HTTPException(status_code=409, detail="Felhasználó már megkapta ezt a badge-et")
        
        # Badge odaítélése
        from datetime import datetime
        new_user_badge = UserBadge(
            user_id=PydanticObjectId(user_id),
            badge_code=badge_code,
            context_data={
                "manually_awarded": True,
                "awarded_by": admin_user.id,
                "awarded_by_username": admin_user.username
            }
        )
        await new_user_badge.insert()
        
        return {
            "message": f"Badge '{badge_type.name}' sikeresen odaítélve {user.username} felhasználónak",
            "badge_id": str(new_user_badge.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge manuális odaítélése sikertelen: {str(e)}")

@router.delete("/revoke")
async def revoke_badge(
    user_id: str,
    badge_code: str,
    admin_user: User = Depends(get_admin_user)
):
    """Badge elvétele felhasználótól"""
    try:
        user_badge = await UserBadge.find_one({
            "user_id": PydanticObjectId(user_id),
            "badge_code": badge_code
        })
        
        if not user_badge:
            raise HTTPException(status_code=404, detail="Felhasználónak nincs ilyen badge-e")
        
        await user_badge.delete()
        
        return {"message": "Badge sikeresen elvéve"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge elvétele sikertelen: {str(e)}")

@router.get("/statistics")
async def get_badge_statistics(
    admin_user: User = Depends(get_admin_user)
):
    """Badge rendszer statisztikái"""
    try:
        # Badge típusok száma kategóriánként
        badge_types = await BadgeType.find({}).to_list()
        types_by_category = {}
        types_by_rarity = {}
        
        for bt in badge_types:
            # Kategória szerint
            category = bt.category.value
            types_by_category[category] = types_by_category.get(category, 0) + 1
            
            # Ritkaság szerint
            rarity = bt.rarity.value
            types_by_rarity[rarity] = types_by_rarity.get(rarity, 0) + 1
        
        # Összes megszerzett badge
        total_user_badges = await UserBadge.find({}).count()
        
        # Egyedi felhasználók akiknek van badge-ük
        pipeline = [
            {"$group": {"_id": "$user_id"}},
            {"$count": "unique_users"}
        ]
        # Egyszerűsített verzió - proper aggregation kellene
        unique_badge_holders = len(set([str(ub.user_id) for ub in await UserBadge.find({}).to_list()]))
        
        # Leggyakrabban megszerzett badge-ek
        badge_counts = {}
        all_user_badges = await UserBadge.find({}).to_list()
        for ub in all_user_badges:
            badge_counts[ub.badge_code] = badge_counts.get(ub.badge_code, 0) + 1
        
        most_earned = sorted(badge_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_badge_types": len(badge_types),
            "active_badge_types": len([bt for bt in badge_types if bt.is_active]),
            "types_by_category": types_by_category,
            "types_by_rarity": types_by_rarity,
            "total_user_badges": total_user_badges,
            "unique_badge_holders": unique_badge_holders,
            "most_earned_badges": [
                {"badge_code": code, "count": count} for code, count in most_earned
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statisztikák lekérése sikertelen: {str(e)}")

@router.post("/trigger-check/{user_id}")
async def trigger_badge_check(
    user_id: str,
    trigger_event: str,
    admin_user: User = Depends(get_admin_user)
):
    """Badge ellenőrzés manuális triggerelése egy felhasználóra"""
    try:
        from app.models.user import UserDocument
        
        # Ellenőrizzük, hogy létezik-e a felhasználó
        user = await UserDocument.get(PydanticObjectId(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="Felhasználó nem található")
        
        # Badge ellenőrzés futtatása
        earned_badges = await badge_service.check_and_award_badges(
            user_id=user_id,
            trigger_event=trigger_event,
            context={"manual_trigger": True, "triggered_by_admin": admin_user.id}
        )
        
        return {
            "message": f"Badge ellenőrzés futtatva {user.username} felhasználóra",
            "earned_badges_count": len(earned_badges),
            "earned_badges": [
                {
                    "badge_code": eb.badge_code,
                    "badge_name": eb.badge_name,
                    "points": eb.points_earned,
                    "is_new": eb.is_new_badge
                }
                for eb in earned_badges
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge ellenőrzés sikertelen: {str(e)}")