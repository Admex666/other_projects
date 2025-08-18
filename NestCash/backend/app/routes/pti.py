# app/routes/pti.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from app.core.security import get_current_user
from app.models.user import User
from app.models.pti import PTIPeriod, RankingScope, UserPTISettings, PTIComponent
from app.models.pti_schemas import (
    PTISettingsUpdate, PTIUserSettings, PTIScoreResponse,
    PTIRankingRequest, PTIComparisonResponse, PTIDashboardResponse,
    PTICalculationRequest, PTIComponentRankingEntry, PTIRankingEntry,
    PTIComponentBreakdown
)
from app.services.pti_service import PTIService
from beanie import PydanticObjectId

router = APIRouter(prefix="/pti", tags=["PTI"])
logger = logging.getLogger(__name__)

@router.get("/dashboard", response_model=PTIDashboardResponse)
async def get_pti_dashboard(current_user: User = Depends(get_current_user)):
    """PTI dashboard - összes releváns adat egy helyen"""
    try:
        user_id = current_user.id
        
        # Aktuális PTI számítás minden időszakra
        results = await PTIService.calculate_and_save_all_periods(user_id)
        
        # Mindhárom időszakra külön ranglista lekérés
        weekly_ranking = await PTIService.get_user_ranking(
            user_id, PTIPeriod.WEEKLY, RankingScope.GLOBAL, 50, 0  # Több elemet kérünk le
        )
        monthly_ranking = await PTIService.get_user_ranking(
            user_id, PTIPeriod.MONTHLY, RankingScope.GLOBAL, 50, 0
        )
        yearly_ranking = await PTIService.get_user_ranking(
            user_id, PTIPeriod.YEARLY, RankingScope.GLOBAL, 50, 0
        )
        
        # Komponens ranglisták lekérése
        component_rankings = {}
        components = [PTIComponent.LEARNING, PTIComponent.HABITS, PTIComponent.BADGES, PTIComponent.LIMITS]
        
        for component in components:
            try:
                comp_ranking = await PTIService.get_component_ranking(
                    component=component,
                    period=PTIPeriod.WEEKLY,
                    scope=RankingScope.GLOBAL,
                    limit=1,
                    offset=0,
                    user_id=user_id
                )
                if comp_ranking.user_rank:
                    component_rankings[component.value] = {
                        "rank": comp_ranking.user_rank,
                        "user_id": user_id,
                        "username": current_user.username,
                        "component_score": comp_ranking.user_score or 0.0,
                        "percentile": comp_ranking.user_percentile or 0.0,
                        "is_current_user": True
                    }
            except Exception as e:
                logger.warning(f"Could not get component ranking for {component}: {e}")
                continue
        
        # User beállítások
        user_settings = await UserPTISettings.find_one(
            UserPTISettings.user_id == PydanticObjectId(user_id)
        )
        
        # Célok teljesítése
        weekly_goal_progress = None
        monthly_goal_progress = None
        
        if user_settings:
            if user_settings.weekly_pti_goal and results.get("weekly"):
                weekly_goal_progress = min(
                    (results["weekly"].total_pti / user_settings.weekly_pti_goal) * 100, 100
                )
            if user_settings.monthly_pti_goal and results.get("monthly"):
                monthly_goal_progress = min(
                    (results["monthly"].total_pti / user_settings.monthly_pti_goal) * 100, 100
                )
        
        # Fejlesztési javaslatok
        next_actions = await PTIService.get_improvement_suggestions(user_id)
        
        # Dashboard összeállítása
        current_pti = PTIScoreResponse(
            user_id=user_id,
            period=PTIPeriod.WEEKLY,
            period_key=PTIService.get_period_key(PTIPeriod.WEEKLY),
            components=results.get("weekly", None),
            pti_score=results.get("weekly", {}).total_pti if results.get("weekly") else 0,
            rank=weekly_ranking.user_rank,
            total_users=weekly_ranking.total_participants,
            calculated_at=datetime.utcnow()
        )
        
        # Felhasználó saját pozíciójának megkeresése minden időszakra
        weekly_user_entry = None
        monthly_user_entry = None
        yearly_user_entry = None
        
        # Heti pozíció keresése
        for entry in weekly_ranking.rankings:
            if entry.is_current_user:
                weekly_user_entry = entry
                break
        
        # Ha nincs a listában, akkor hozzuk létre
        if weekly_user_entry is None and weekly_ranking.user_rank:
            weekly_user_entry = PTIRankingEntry(
                rank=weekly_ranking.user_rank,
                user_id=user_id,
                username=current_user.username,
                is_anonymous=False,
                pti_score=weekly_ranking.user_score or 0.0,
                components=results.get("weekly", PTIComponentBreakdown(
                    learning_points=0, learning_contribution=0,
                    habit_score=0, habit_contribution=0,
                    badge_score=0, badge_contribution=0,
                    limit_score=0, limit_contribution=0,
                    total_pti=0
                )),
                is_current_user=True
            )
        
        # Havi pozíció keresése
        for entry in monthly_ranking.rankings:
            if entry.is_current_user:
                monthly_user_entry = entry
                break
                
        if monthly_user_entry is None and monthly_ranking.user_rank:
            monthly_user_entry = PTIRankingEntry(
                rank=monthly_ranking.user_rank,
                user_id=user_id,
                username=current_user.username,
                is_anonymous=False,
                pti_score=monthly_ranking.user_score or 0.0,
                components=results.get("monthly", PTIComponentBreakdown(
                    learning_points=0, learning_contribution=0,
                    habit_score=0, habit_contribution=0,
                    badge_score=0, badge_contribution=0,
                    limit_score=0, limit_contribution=0,
                    total_pti=0
                )),
                is_current_user=True
            )
        
        # Éves pozíció keresése
        for entry in yearly_ranking.rankings:
            if entry.is_current_user:
                yearly_user_entry = entry
                break
                
        if yearly_user_entry is None and yearly_ranking.user_rank:
            yearly_user_entry = PTIRankingEntry(
                rank=yearly_ranking.user_rank,
                user_id=user_id,
                username=current_user.username,
                is_anonymous=False,
                pti_score=yearly_ranking.user_score or 0.0,
                components=results.get("yearly", PTIComponentBreakdown(
                    learning_points=0, learning_contribution=0,
                    habit_score=0, habit_contribution=0,
                    badge_score=0, badge_contribution=0,
                    limit_score=0, limit_contribution=0,
                    total_pti=0
                )),
                is_current_user=True
            )
        
        # Feature usage tracking
        try:
            from app.models.analytics import FeatureUsageTracking
            await FeatureUsageTracking(
                user_id=PydanticObjectId(current_user.id),
                feature_name="pti_dashboard_viewed"
            ).insert()
        except Exception as e:
            logger.error(f"Feature tracking failed: {e}")

        return PTIDashboardResponse(
            current_pti=current_pti,
            weekly_ranking=weekly_user_entry,  # Most a felhasználó saját pozíciója
            monthly_ranking=monthly_user_entry,  # Most a felhasználó saját pozíciója
            yearly_ranking=yearly_user_entry,  # Most a felhasználó saját pozíciója
            component_rankings=component_rankings,
            weekly_goal_progress=weekly_goal_progress,
            monthly_goal_progress=monthly_goal_progress,
            next_actions=next_actions,
            last_7_days=[],
            last_4_weeks=[],
            last_12_months=[]
        )
        
    except Exception as e:
        logger.error(f"Error getting PTI dashboard for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Hiba a PTI dashboard lekérésekor")

@router.get("/score", response_model=PTIScoreResponse)
async def get_pti_score(
    period: PTIPeriod = Query(PTIPeriod.WEEKLY),
    calculate: bool = Query(False, description="Újra számítsa-e vagy cache-ből vegye"),
    current_user: User = Depends(get_current_user)
):
    """Felhasználó PTI pontszámának lekérése"""
    try:
        user_id = current_user.id
        
        if calculate:
            # Újraszámítás
            components = await PTIService.calculate_pti_score(user_id, period)
            await PTIService.save_pti_score(user_id, period, components)
            
            # Rangsorok frissítése
            period_key = PTIService.get_period_key(period)
            await PTIService.update_rankings(period, period_key)
        else:
            # Cache-ből lekérés
            period_key = PTIService.get_period_key(period)
            from app.models.pti import PTIScore
            
            existing_score = await PTIScore.find_one(
                PTIScore.user_id == PydanticObjectId(user_id),
                PTIScore.period == period,
                PTIScore.period_key == period_key
            )
            
            if not existing_score:
                # Ha nincs cache, akkor számítsuk ki
                components = await PTIService.calculate_pti_score(user_id, period)
                await PTIService.save_pti_score(user_id, period, components)
            else:
                # Cache-ből komponensek összeállítása
                from app.models.pti import PTIComponentBreakdown
                components = PTIComponentBreakdown(
                    learning_points=existing_score.learning_points,
                    learning_contribution=existing_score.learning_points * PTIService.LEARNING_WEIGHT,
                    habit_score=existing_score.habit_score,
                    habit_contribution=existing_score.habit_score * PTIService.HABIT_WEIGHT,
                    badge_score=existing_score.badge_score,
                    badge_contribution=existing_score.badge_score * PTIService.BADGE_WEIGHT,
                    limit_score=existing_score.limit_score,
                    limit_contribution=existing_score.limit_score * PTIService.LIMIT_WEIGHT,
                    total_pti=existing_score.normalized_pti
                )
        
        # Percentilis számítása
        from app.models.pti import PTIScore
        total_users = await PTIScore.find(
            PTIScore.period == period,
            PTIScore.period_key == PTIService.get_period_key(period)
        ).count()
        
        better_users = await PTIScore.find(
            PTIScore.period == period,
            PTIScore.period_key == PTIService.get_period_key(period),
            PTIScore.normalized_pti > components.total_pti
        ).count()
        
        rank = better_users + 1
        percentile = ((total_users - rank + 1) / total_users) * 100 if total_users > 0 else 0
        
        return PTIScoreResponse(
            user_id=user_id,
            period=period,
            period_key=PTIService.get_period_key(period),
            components=components,
            pti_score=components.total_pti,
            rank=rank,
            total_users=total_users,
            percentile=percentile,
            calculated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting PTI score for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Hiba a PTI pontszám lekérésekor")

@router.post("/calculate", response_model=dict)
async def calculate_pti(
    request: PTICalculationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """PTI számítás indítása (háttérben vagy azonnal)"""
    try:
        target_user_id = request.user_id if request.user_id else current_user.id
        
        if request.force_recalculate:
            # Háttérben futtatás
            background_tasks.add_task(
                PTIService.calculate_and_save_all_periods,
                target_user_id
            )
            return {"message": "PTI számítás elindítva háttérben", "status": "started"}
        else:
            # Azonnali számítás
            results = await PTIService.calculate_and_save_all_periods(target_user_id)
            return {"message": "PTI számítás befejezve", "status": "completed", "results": results}
            
    except Exception as e:
        logger.error(f"Error calculating PTI: {e}")
        raise HTTPException(status_code=500, detail="Hiba a PTI számítás során")

@router.get("/ranking", response_model=dict)
async def get_ranking(
    period: PTIPeriod = Query(PTIPeriod.WEEKLY),
    scope: RankingScope = Query(RankingScope.GLOBAL),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """PTI ranglista lekérése"""
    try:
        ranking = await PTIService.get_user_ranking(
            current_user.id, period, scope, limit, offset
        )

        # Feature usage tracking
        try:
            from app.models.analytics import FeatureUsageTracking
            await FeatureUsageTracking(
                user_id=PydanticObjectId(current_user.id),
                feature_name="pti_ranking_viewed"
            ).insert()
        except Exception as e:
            logger.error(f"Feature tracking failed: {e}")

        return ranking.dict()
        
    except Exception as e:
        logger.error(f"Error getting PTI ranking: {e}")
        raise HTTPException(status_code=500, detail="Hiba a ranglista lekérésekor")

@router.get("/settings", response_model=PTIUserSettings)
async def get_pti_settings(current_user: User = Depends(get_current_user)):
    """Felhasználó PTI beállításainak lekérése"""
    try:
        settings = await UserPTISettings.find_one(
            UserPTISettings.user_id == PydanticObjectId(current_user.id)
        )
        
        if not settings:
            # Alapértelmezett beállítások létrehozása
            settings = UserPTISettings(
                user_id=PydanticObjectId(current_user.id)
            )
            await settings.insert()
        
        return PTIUserSettings(
            user_id=str(settings.user_id),
            show_in_global_ranking=settings.show_in_global_ranking,
            show_in_friends_ranking=settings.show_in_friends_ranking,
            is_anonymous=settings.is_anonymous,
            anonymous_name=settings.anonymous_name,
            notify_rank_change=settings.notify_rank_change,
            notify_weekly_summary=settings.notify_weekly_summary,
            notify_achievements=settings.notify_achievements,
            weekly_pti_goal=settings.weekly_pti_goal,
            monthly_pti_goal=settings.monthly_pti_goal,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error getting PTI settings for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Hiba a beállítások lekérésekor")

@router.put("/settings", response_model=PTIUserSettings)
async def update_pti_settings(
    settings_update: PTISettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    """PTI beállítások frissítése"""
    try:
        settings = await UserPTISettings.find_one(
            UserPTISettings.user_id == PydanticObjectId(current_user.id)
        )
        
        if not settings:
            settings = UserPTISettings(
                user_id=PydanticObjectId(current_user.id)
            )
        
        # Frissítések alkalmazása
        update_data = settings_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        settings.updated_at = datetime.utcnow()
        await settings.save()
        
        return PTIUserSettings(
            user_id=str(settings.user_id),
            show_in_global_ranking=settings.show_in_global_ranking,
            show_in_friends_ranking=settings.show_in_friends_ranking,
            is_anonymous=settings.is_anonymous,
            anonymous_name=settings.anonymous_name,
            notify_rank_change=settings.notify_rank_change,
            notify_weekly_summary=settings.notify_weekly_summary,
            notify_achievements=settings.notify_achievements,
            weekly_pti_goal=settings.weekly_pti_goal,
            monthly_pti_goal=settings.monthly_pti_goal,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error updating PTI settings for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Hiba a beállítások frissítésekor")

@router.get("/comparison")
async def get_pti_comparison(
    period: PTIPeriod = Query(PTIPeriod.WEEKLY),
    current_user: User = Depends(get_current_user)
):
    """PTI összehasonlítás előző időszakkal"""
    try:
        # Aktuális PTI
        current_components = await PTIService.calculate_pti_score(current_user.id, period)
        current_response = PTIScoreResponse(
            user_id=current_user.id,
            period=period,
            period_key=PTIService.get_period_key(period),
            components=current_components,
            pti_score=current_components.total_pti,
            calculated_at=datetime.utcnow()
        )
        
        # Előző időszak PTI-je
        previous_response = None
        pti_change = None
        rank_change = None
        improvements = []
        declines = []
        
        # Előző időszak dátumának számítása
        reference_date = datetime.utcnow()
        if period == PTIPeriod.WEEKLY:
            prev_date = reference_date - timedelta(weeks=1)
        elif period == PTIPeriod.MONTHLY:
            if reference_date.month == 1:
                prev_date = reference_date.replace(year=reference_date.year - 1, month=12)
            else:
                prev_date = reference_date.replace(month=reference_date.month - 1)
        else:  # YEARLY
            prev_date = reference_date.replace(year=reference_date.year - 1)
        
        # Előző időszak adatainak lekérése
        from app.models.pti import PTIScore
        prev_period_key = PTIService.get_period_key(period, prev_date)
        previous_score = await PTIScore.find_one(
            PTIScore.user_id == PydanticObjectId(current_user.id),
            PTIScore.period == period,
            PTIScore.period_key == prev_period_key
        )
        
        if previous_score:
            from app.models.pti import PTIComponentBreakdown
            prev_components = PTIComponentBreakdown(
                learning_points=previous_score.learning_points,
                learning_contribution=previous_score.learning_points * PTIService.LEARNING_WEIGHT,
                habit_score=previous_score.habit_score,
                habit_contribution=previous_score.habit_score * PTIService.HABIT_WEIGHT,
                badge_score=previous_score.badge_score,
                badge_contribution=previous_score.badge_score * PTIService.BADGE_WEIGHT,
                limit_score=previous_score.limit_score,
                limit_contribution=previous_score.limit_score * PTIService.LIMIT_WEIGHT,
                total_pti=previous_score.normalized_pti
            )
            
            previous_response = PTIScoreResponse(
                user_id=current_user.id,
                period=period,
                period_key=prev_period_key,
                components=prev_components,
                pti_score=prev_components.total_pti,
                rank=previous_score.global_rank,
                total_users=previous_score.total_users,
                calculated_at=previous_score.calculated_at
            )
            
            # Változások számítása
            pti_change = current_components.total_pti - prev_components.total_pti
            
            # Rangsor változás (ha van aktuális rangsor)
            current_rank = await PTIService.get_user_ranking(
                current_user.id, period, RankingScope.GLOBAL, 1, 0
            )
            if current_rank.user_rank and previous_score.global_rank:
                rank_change = previous_score.global_rank - current_rank.user_rank  # Pozitív = javulás
            
            # Komponensenkénti változások elemzése
            if current_components.learning_points > prev_components.learning_points:
                improvements.append("📚 Tanulási pontok növekedtek")
            elif current_components.learning_points < prev_components.learning_points:
                declines.append("📚 Tanulási pontok csökkentek")
                
            if current_components.habit_score > prev_components.habit_score:
                improvements.append("💪 Szokáskövetés javult")
            elif current_components.habit_score < prev_components.habit_score:
                declines.append("💪 Szokáskövetés romlott")
                
            if current_components.badge_score > prev_components.badge_score:
                improvements.append("🏆 Badge pontszám nőtt")
            elif current_components.badge_score < prev_components.badge_score:
                declines.append("🏆 Badge pontszám csökkent")
                
            if current_components.limit_score > prev_components.limit_score:
                improvements.append("📊 Limit betartás javult")
            elif current_components.limit_score < prev_components.limit_score:
                declines.append("📊 Limit betartás romlott")
        
        return PTIComparisonResponse(
            current_period=current_response,
            previous_period=previous_response,
            pti_change=pti_change,
            rank_change=rank_change,
            improvements=improvements,
            declines=declines
        )
        
    except Exception as e:
        logger.error(f"Error getting PTI comparison for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Hiba az összehasonlítás lekérésekor")

@router.get("/suggestions")
async def get_improvement_suggestions(
    current_user: User = Depends(get_current_user)
):
    """Fejlesztési javaslatok lekérése"""
    try:
        suggestions = await PTIService.get_improvement_suggestions(current_user.id)
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Error getting improvement suggestions for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Hiba a javaslatok lekérésekor")

@router.get("/leaderboard/stats")
async def get_leaderboard_stats(
    period: PTIPeriod = Query(PTIPeriod.WEEKLY),
    current_user: User = Depends(get_current_user)
):
    """Ranglista statisztikák"""
    try:
        from app.models.pti import PTIScore
        period_key = PTIService.get_period_key(period)
        
        # Alapstatisztikák
        all_scores = await PTIScore.find(
            PTIScore.period == period,
            PTIScore.period_key == period_key
        ).to_list()
        
        if not all_scores:
            return {
                "period": period,
                "period_key": period_key,
                "total_participants": 0,
                "message": "Nincs adat ehhez az időszakhoz"
            }
        
        pti_values = [score.normalized_pti for score in all_scores]
        learning_values = [score.learning_points for score in all_scores]
        habit_values = [score.habit_score for score in all_scores]
        badge_values = [score.badge_score for score in all_scores]
        limit_values = [score.limit_score for score in all_scores]
        
        # Statisztikák számítása
        total_participants = len(all_scores)
        average_pti = sum(pti_values) / total_participants
        median_pti = sorted(pti_values)[total_participants // 2]
        highest_pti = max(pti_values)
        lowest_pti = min(pti_values)
        
        # Komponens átlagok
        avg_learning = sum(learning_values) / total_participants
        avg_habit = sum(habit_values) / total_participants
        avg_badge = sum(badge_values) / total_participants
        avg_limit = sum(limit_values) / total_participants
        
        return {
            "period": period,
            "period_key": period_key,
            "total_participants": total_participants,
            "average_pti": round(average_pti, 2),
            "median_pti": round(median_pti, 2),
            "highest_pti": round(highest_pti, 2),
            "lowest_pti": round(lowest_pti, 2),
            "avg_learning_points": round(avg_learning, 2),
            "avg_habit_score": round(avg_habit, 2),
            "avg_badge_score": round(avg_badge, 2),
            "avg_limit_score": round(avg_limit, 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting leaderboard stats: {e}")
        raise HTTPException(status_code=500, detail="Hiba a statisztikák lekérésekor")

@router.post("/recalculate/all")
async def recalculate_all_users(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    period: Optional[PTIPeriod] = Query(None) # Move period to the end
):
    """Összes felhasználó PTI újraszámítása (admin funkció)"""
    try:
        # TODO: Admin jogosultság ellenőrzése
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Nincs jogosultsága")
        
        async def recalculate_all():
            from app.models.user import UserDocument
            users = await UserDocument.find().to_list()
            
            periods_to_calc = [period] if period else [PTIPeriod.WEEKLY, PTIPeriod.MONTHLY, PTIPeriod.YEARLY]
            
            for user in users:
                try:
                    for p in periods_to_calc:
                        components = await PTIService.calculate_pti_score(str(user.id), p)
                        await PTIService.save_pti_score(str(user.id), p, components)
                        
                        # Rangsorok frissítése
                        period_key = PTIService.get_period_key(p)
                        await PTIService.update_rankings(p, period_key)
                        
                except Exception as e:
                    logger.error(f"Error recalculating PTI for user {user.id}: {e}")
                    continue
        
        background_tasks.add_task(recalculate_all)
        
        return {
            "message": "Összes felhasználó PTI újraszámítása elindítva háttérben",
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Error starting recalculation: {e}")
        raise HTTPException(status_code=500, detail="Hiba az újraszámítás indításakor")
    
@router.get("/period-info")
async def get_period_info(
    period: PTIPeriod = Query(PTIPeriod.WEEKLY),
    current_user: User = Depends(get_current_user)
):
    """Aktuális időszak információk lekérése"""
    try:
        period_info = PTIService.get_period_info(period)
        return period_info.dict()
        
    except Exception as e:
        logger.error(f"Error getting period info: {e}")
        raise HTTPException(status_code=500, detail="Hiba az időszak információk lekérésekor")

@router.get("/history")
async def get_pti_history(
    period: PTIPeriod = Query(PTIPeriod.WEEKLY),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """PTI történet lekérése"""
    try:
        history = await PTIService.get_user_pti_history(
            current_user.id, period, limit, offset
        )
        return history.dict()
        
    except Exception as e:
        logger.error(f"Error getting PTI history for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Hiba a PTI történet lekérésekor")
    
@router.get("/component-ranking", response_model=dict)
async def get_component_ranking(
    period: PTIPeriod = Query(PTIPeriod.WEEKLY),
    component: PTIComponent = Query(PTIComponent.TOTAL),
    scope: RankingScope = Query(RankingScope.GLOBAL),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Komponens-specifikus ranglista lekérése"""
    try:
        ranking = await PTIService.get_component_ranking(
            component=component,  # Paraméter név hozzáadása
            period=period,
            scope=scope,
            limit=limit,
            offset=offset,
            user_id=current_user.id
        )

        # Feature usage tracking
        try:
            from app.models.analytics import FeatureUsageTracking
            await FeatureUsageTracking(
                user_id=PydanticObjectId(current_user.id),
                feature_name="pti_component_ranking_viewed"
            ).insert()
        except Exception as e:
            logger.error(f"Feature tracking failed: {e}")
            
        return ranking.dict()
        
    except Exception as e:
        logger.error(f"Error getting component ranking: {e}")
        raise HTTPException(status_code=500, detail="Hiba a komponens ranglista lekérésekor")