# app/routes/badges.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from beanie import PydanticObjectId

from app.core.security import get_current_user
from app.models.user import User
from app.models.badge import BadgeCategory, UserBadgeRead, BadgeProgressRead, UserBadgeStats
from app.models.badge_schemas import (
    BadgeListResponse, BadgeProgressListResponse, UserBadgeUpdate,
    BadgeCategoryStats, BadgeLeaderboardResponse
)
from app.services.badge_service import badge_service

router = APIRouter(prefix="/badges", tags=["badges"])

@router.get("/my-badges", response_model=BadgeListResponse)
async def get_my_badges(
    current_user: User = Depends(get_current_user),
    category: Optional[BadgeCategory] = Query(None, description="Szűrés kategória szerint"),
    favorite_only: bool = Query(False, description="Csak kedvencek")
):
    """Felhasználó badge-einek lekérése"""
    try:
        user_badges_data = await badge_service.get_user_badges(current_user.id, category)
        
        badges_read = []
        total_points = 0
        
        for data in user_badges_data:
            user_badge = data["user_badge"]
            badge_type = data["badge_type"]
            
            # Kedvenc szűrés
            if favorite_only and not user_badge.is_favorite:
                continue
            
            badge_read = UserBadgeRead(
                id=str(user_badge.id),
                user_id=str(user_badge.user_id),
                badge_code=user_badge.badge_code,
                earned_at=user_badge.earned_at,
                level=user_badge.level,
                progress=user_badge.progress,
                context_data=user_badge.context_data,
                is_favorite=user_badge.is_favorite,
                is_visible=user_badge.is_visible,
                badge_name=badge_type.name,
                badge_description=badge_type.description,
                badge_icon=badge_type.icon,
                badge_color=badge_type.color,
                badge_category=badge_type.category,
                badge_rarity=badge_type.rarity,
                badge_points=badge_type.points
            )
            badges_read.append(badge_read)
            total_points += badge_type.points * user_badge.level
        
        return BadgeListResponse(
            badges=badges_read,
            total_count=len(badges_read),
            total_points=total_points
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge-ek lekérése sikertelen: {str(e)}")

@router.get("/progress", response_model=BadgeProgressListResponse)
async def get_badge_progress(
    current_user: User = Depends(get_current_user)
):
    """Folyamatban lévő badge-ek haladásának lekérése"""
    try:
        progress_data = await badge_service.get_badge_progress(current_user.id)
        
        progress_read = []
        total_progress = 0
        
        for data in progress_data:
            progress = data["progress"]
            badge_type = data["badge_type"]
            
            progress_item = BadgeProgressRead(
                id=str(progress.id),
                user_id=str(progress.user_id),
                badge_code=progress.badge_code,
                current_value=progress.current_value,
                target_value=progress.target_value,
                progress_percentage=progress.progress_percentage,
                started_at=progress.started_at,
                last_updated=progress.last_updated,
                metadata=progress.metadata,
                badge_name=badge_type.name,
                badge_description=badge_type.description,
                badge_icon=badge_type.icon,
                badge_color=badge_type.color
            )
            progress_read.append(progress_item)
            total_progress += progress.progress_percentage
        
        completion_rate = total_progress / len(progress_read) if progress_read else 0
        
        return BadgeProgressListResponse(
            progress_list=progress_read,
            total_count=len(progress_read),
            completion_rate=completion_rate
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge haladás lekérése sikertelen: {str(e)}")

@router.get("/stats", response_model=UserBadgeStats)
async def get_badge_stats(
    current_user: User = Depends(get_current_user)
):
    """Badge statisztikák lekérése"""
    try:
        stats_data = await badge_service.get_user_badge_stats(current_user.id)
        
        # Recent badges konvertálása
        recent_badges = []
        for user_badge in stats_data.get("recent_badges", []):
            # Itt ideálisan a badge típus adatokat is be kellene tölteni
            recent_badges.append(UserBadgeRead(
                id=str(user_badge.id),
                user_id=str(user_badge.user_id),
                badge_code=user_badge.badge_code,
                earned_at=user_badge.earned_at,
                level=user_badge.level,
                progress=user_badge.progress,
                context_data=user_badge.context_data,
                is_favorite=user_badge.is_favorite,
                is_visible=user_badge.is_visible
            ))
        
        # Favorite badges konvertálása
        favorite_badges = []
        for user_badge in stats_data.get("favorite_badges", []):
            favorite_badges.append(UserBadgeRead(
                id=str(user_badge.id),
                user_id=str(user_badge.user_id),
                badge_code=user_badge.badge_code,
                earned_at=user_badge.earned_at,
                level=user_badge.level,
                progress=user_badge.progress,
                context_data=user_badge.context_data,
                is_favorite=user_badge.is_favorite,
                is_visible=user_badge.is_visible
            ))
        
        return UserBadgeStats(
            total_badges=stats_data.get("total_badges", 0),
            total_points=stats_data.get("total_points", 0),
            badges_by_category=stats_data.get("badges_by_category", {}),
            badges_by_rarity=stats_data.get("badges_by_rarity", {}),
            recent_badges=recent_badges,
            favorite_badges=favorite_badges,
            in_progress_count=stats_data.get("in_progress_count", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge statisztikák lekérése sikertelen: {str(e)}")

@router.put("/my-badges/{badge_id}", response_model=UserBadgeRead)
async def update_my_badge(
    badge_id: str,
    badge_update: UserBadgeUpdate,
    current_user: User = Depends(get_current_user)
):
    """Badge beállításainak frissítése (kedvenc, láthatóság)"""
    try:
        from app.models.badge import UserBadge
        
        user_badge = await UserBadge.get(PydanticObjectId(badge_id))
        if not user_badge:
            raise HTTPException(status_code=404, detail="Badge nem található")
        
        if str(user_badge.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a badge-hez")
        
        # Frissítések alkalmazása
        if badge_update.is_favorite is not None:
            user_badge.is_favorite = badge_update.is_favorite
        
        if badge_update.is_visible is not None:
            user_badge.is_visible = badge_update.is_visible
        
        await user_badge.save()
        
        return UserBadgeRead(
            id=str(user_badge.id),
            user_id=str(user_badge.user_id),
            badge_code=user_badge.badge_code,
            earned_at=user_badge.earned_at,
            level=user_badge.level,
            progress=user_badge.progress,
            context_data=user_badge.context_data,
            is_favorite=user_badge.is_favorite,
            is_visible=user_badge.is_visible
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge frissítése sikertelen: {str(e)}")

@router.get("/categories/{category}/stats", response_model=BadgeCategoryStats)
async def get_category_stats(
    category: BadgeCategory,
    current_user: User = Depends(get_current_user)
):
    """Kategória szerinti badge statisztikák"""
    try:
        from app.models.badge import BadgeType, UserBadge
        
        # Kategória összes badge-e
        all_badges = await BadgeType.find({
            "category": category,
            "is_active": True
        }).to_list()
        
        # Felhasználó badge-ei ebben a kategóriában
        badge_codes = [badge.code for badge in all_badges]
        user_badges = await UserBadge.find({
            "user_id": PydanticObjectId(current_user.id),
            "badge_code": {"$in": badge_codes}
        }).to_list()
        
        # Pontok számítása
        total_points = sum(badge.points for badge in all_badges)
        earned_points = 0
        
        for user_badge in user_badges:
            badge_type = next((b for b in all_badges if b.code == user_badge.badge_code), None)
            if badge_type:
                earned_points += badge_type.points * user_badge.level
        
        completion_rate = (len(user_badges) / len(all_badges) * 100) if all_badges else 0
        
        return BadgeCategoryStats(
            category=category,
            total_badges=len(all_badges),
            earned_badges=len(user_badges),
            total_points=total_points,
            earned_points=earned_points,
            completion_rate=completion_rate
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kategória statisztikák lekérése sikertelen: {str(e)}")

@router.get("/leaderboard", response_model=BadgeLeaderboardResponse)
async def get_badge_leaderboard(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50, description="Leaderboard mérete")
):
    """Badge leaderboard lekérése"""
    try:
        from app.models.badge import UserBadge, BadgeType
        from app.models.user import UserDocument
        
        # Összes felhasználó badge-einek aggregálása
        pipeline = [
            {
                "$group": {
                    "_id": "$user_id",
                    "total_badges": {"$sum": 1},
                    "recent_badge": {"$last": "$$ROOT"}
                }
            },
            {"$sort": {"total_badges": -1}},
            {"$limit": limit}
        ]
        
        # Egyszerűsített leaderboard - ezt ki lehetne bővíteni
        user_badges = await UserBadge.find({}).to_list()
        user_stats = {}
        
        for badge in user_badges:
            user_id = str(badge.user_id)
            if user_id not in user_stats:
                user_stats[user_id] = {
                    "total_badges": 0,
                    "total_points": 0,
                    "recent_badge": badge
                }
            user_stats[user_id]["total_badges"] += 1
            if badge.earned_at > user_stats[user_id]["recent_badge"].earned_at:
                user_stats[user_id]["recent_badge"] = badge
        
        # Rendezés badge szám szerint
        sorted_users = sorted(user_stats.items(), 
                             key=lambda x: x[1]["total_badges"], 
                             reverse=True)[:limit]
        
        # Felhasználó adatok lekérése
        user_ids = [user_id for user_id, _ in sorted_users]
        users = await UserDocument.find({"_id": {"$in": [PydanticObjectId(uid) for uid in user_ids]}}).to_list()
        user_dict = {str(user.id): user for user in users}
        
        # Leaderboard összeállítása
        leaderboard = []
        user_rank = None
        
        for rank, (user_id, stats) in enumerate(sorted_users, 1):
            user = user_dict.get(user_id)
            if user:
                if user_id == current_user.id:
                    user_rank = rank
                
                leaderboard.append({
                    "rank": rank,
                    "user_id": user_id,
                    "username": user.username,
                    "total_badges": stats["total_badges"],
                    "total_points": stats["total_points"],
                    "recent_badge": UserBadgeRead(
                        id=str(stats["recent_badge"].id),
                        user_id=str(stats["recent_badge"].user_id),
                        badge_code=stats["recent_badge"].badge_code,
                        earned_at=stats["recent_badge"].earned_at,
                        level=stats["recent_badge"].level,
                        progress=stats["recent_badge"].progress,
                        context_data=stats["recent_badge"].context_data,
                        is_favorite=stats["recent_badge"].is_favorite,
                        is_visible=stats["recent_badge"].is_visible
                    ) if stats["recent_badge"] else None
                })
        
        return BadgeLeaderboardResponse(
            leaderboard=leaderboard,
            user_rank=user_rank,
            total_users=len(user_stats)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leaderboard lekérése sikertelen: {str(e)}")