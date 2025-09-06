# app/routes/challenges.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from beanie import PydanticObjectId
from bson import ObjectId
from datetime import datetime
import logging
from pydantic import BaseModel

from app.models.challenge import (
    ChallengeDocument, UserChallengeDocument,
    ChallengeType, ChallengeDifficulty, ChallengeStatus, ParticipationStatus,
    ChallengeCreate, ChallengeUpdate, ChallengeRead, ChallengeListResponse,
    UserChallengeJoin, UserChallengeUpdate, UserChallengeRead, UserChallengeListResponse,
    ChallengeProgress 
)
from app.core.security import get_current_user
from app.models.user import User
from app.services.challenge_service import ChallengeService
from app.services.challenge_localization_service import challenge_localization_service

router = APIRouter(prefix="/challenges", tags=["challenges"])
logger = logging.getLogger(__name__)

# === KIHÍVÁSOK BÖNGÉSZÉSE ===
@router.get("/", response_model=ChallengeListResponse)
async def list_challenges(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    challenge_type: Optional[ChallengeType] = Query(None),
    difficulty: Optional[ChallengeDifficulty] = Query(None),
    search: Optional[str] = Query(None),
    only_available: bool = Query(True),
    sort_by: str = Query("newest"),
    lang: str = Query('hu', description="Nyelv kód (hu, en)")
):
    """Kihívások listázása JSON fájlból"""
    try:
        # Kihívások betöltése JSON fájlból
        all_challenges = challenge_localization_service.get_all_challenges(lang)
        
        # Szűrések alkalmazása
        filtered_challenges = all_challenges.copy()
        
        # Típus szűrés
        if challenge_type:
            filtered_challenges = [c for c in filtered_challenges if c.get('challenge_type') == challenge_type.value]
        
        # Nehézség szűrés
        if difficulty:
            filtered_challenges = [c for c in filtered_challenges if c.get('difficulty') == difficulty.value]
        
        # Keresés
        if search:
            search_lower = search.lower()
            filtered_challenges = [
                c for c in filtered_challenges 
                if search_lower in c.get('title', '').lower() or 
                   search_lower in c.get('description', '').lower() or
                   search_lower in c.get('short_description', '').lower()
            ]
        
        # Rendezés (egyszerű implementáció)
        if sort_by == "difficulty":
            difficulty_order = {"easy": 1, "medium": 2, "hard": 3, "expert": 4}
            filtered_challenges.sort(key=lambda x: difficulty_order.get(x.get('difficulty', 'easy'), 1))
        # A "newest" és "popular" rendezés JSON fájlnál nem releváns
        
        # Lapozás
        total_count = len(filtered_challenges)
        paginated_challenges = filtered_challenges[skip:skip + limit]
        
        # Felhasználó részvételének ellenőrzése
        challenge_codes = [c.get('code') for c in paginated_challenges if c.get('code')]
        user_participations = []
        if challenge_codes:
            user_participations = await UserChallengeDocument.find({
                "user_id": ObjectId(current_user.id),
                "challenge_code": {"$in": challenge_codes}
            }).to_list()
        
        participation_map = {
            up.challenge_code: up for up in user_participations
        }
        
        # Válasz összeállítása
        challenge_reads = []
        for challenge_data in paginated_challenges:
            challenge_code = challenge_data.get('code')
            participation = participation_map.get(challenge_code)
            
            # Rules és Rewards objektumok létrehozása
            rules = [ChallengeRule(**rule) for rule in challenge_data.get('rules', [])]
            rewards = ChallengeReward(**challenge_data.get('rewards', {}))
            
            challenge_read = ChallengeRead(
                id=challenge_code,  # A kód lesz az ID
                title=challenge_data.get('title', ''),
                description=challenge_data.get('description', ''),
                short_description=challenge_data.get('short_description'),
                challenge_type=ChallengeType(challenge_data.get('challenge_type', 'savings')),
                difficulty=ChallengeDifficulty(challenge_data.get('difficulty', 'easy')),
                duration_days=challenge_data.get('duration_days', 30),
                target_amount=challenge_data.get('target_amount'),
                rules=rules,
                rewards=rewards,
                status=ChallengeStatus.ACTIVE,  # JSON-ból mindig aktív
                created_at=datetime.utcnow(),  # Dummy értékek
                updated_at=datetime.utcnow(),
                participant_count=0,  # Ezt számítani kellene a UserChallengeDocument-ekből
                completion_rate=0.0,
                image_url=challenge_data.get('image_url'),
                tags=challenge_data.get('tags', []),
                creator_username="system",
                is_participating=participation is not None and participation.status == ParticipationStatus.ACTIVE,
                my_progress=participation.progress if participation else None,
                my_status=participation.status if participation else None
            )
            
            challenge_reads.append(challenge_read)
        
        return ChallengeListResponse(
            challenges=challenge_reads,
            total_count=total_count,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing challenges: {e}")
        raise HTTPException(status_code=500, detail="Failed to list challenges")

# === EGY KIHÍVÁS RÉSZLETES ADATAI ===
@router.get("/{challenge_code}", response_model=ChallengeRead)
async def get_challenge(
    challenge_code: str,
    current_user: User = Depends(get_current_user),
    lang: str = Query('hu', description="Nyelv kód")
):
    """Kihívás részletes adatainak lekérése kód alapján"""
    try:
        # Kihívás keresése JSON fájlban
        challenge_data = challenge_localization_service.get_challenge_by_code(challenge_code, lang)
        if not challenge_data:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Felhasználó részvételének ellenőrzése
        participation = await UserChallengeDocument.find_one({
            "user_id": ObjectId(current_user.id),
            "challenge_code": challenge_code
        })
        
        # Rules és Rewards objektumok létrehozása
        rules = [ChallengeRule(**rule) for rule in challenge_data.get('rules', [])]
        rewards = ChallengeReward(**challenge_data.get('rewards', {}))
        
        return ChallengeRead(
            id=challenge_code,
            title=challenge_data.get('title', ''),
            description=challenge_data.get('description', ''),
            short_description=challenge_data.get('short_description'),
            challenge_type=ChallengeType(challenge_data.get('challenge_type', 'savings')),
            difficulty=ChallengeDifficulty(challenge_data.get('difficulty', 'easy')),
            duration_days=challenge_data.get('duration_days', 30),
            target_amount=challenge_data.get('target_amount'),
            rules=rules,
            rewards=rewards,
            status=ChallengeStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            participant_count=0,  # Ezt kellene számítani
            completion_rate=0.0,
            image_url=challenge_data.get('image_url'),
            tags=challenge_data.get('tags', []),
            creator_username="system",
            is_participating=participation is not None and participation.status == ParticipationStatus.ACTIVE,
            my_progress=participation.progress if participation else None,
            my_status=participation.status if participation else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting challenge {challenge_code}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get challenge")

# === KIHÍVÁSHOZ CSATLAKOZÁS ===
@router.post("/{challenge_code}/join", response_model=UserChallengeRead)
async def join_challenge(
    challenge_code: str,
    join_data: UserChallengeJoin,
    current_user: User = Depends(get_current_user)
):
    """Csatlakozás egy kihíváshoz"""
    try:
        # Kihívás keresése JSON fájlban
        challenge = challenge_localization_service.get_challenge_by_code(challenge_code)
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Meglévő részvétel ellenőrzése
        existing_participation = await UserChallengeDocument.find_one({
            "user_id": ObjectId(current_user.id),
            "challenge_code": challenge_code
        })

        if existing_participation:
            if existing_participation.status == ParticipationStatus.ACTIVE:
                raise HTTPException(status_code=400, detail="Already participating in this challenge")
            elif existing_participation.status == ParticipationStatus.ABANDONED:
                # Reaktiváljuk az elhagyott kihívást
                existing_participation.status = ParticipationStatus.ACTIVE
                existing_participation.personal_target = join_data.personal_target or existing_participation.personal_target
                existing_participation.notes = join_data.notes or existing_participation.notes
                existing_participation.started_at = datetime.utcnow()  # Új kezdés
                existing_participation.updated_at = datetime.utcnow()
                
                # Haladás újraszámítása
                updated_progress = await ChallengeService.calculate_challenge_progress(
                    current_user.id, challenge, existing_participation
                )
                existing_participation.progress = updated_progress
                
                await existing_participation.save()
                
                # Kihívás statisztikáinak frissítése
                await ChallengeService.update_challenge_statistics(challenge_code)
                
                return UserChallengeRead(
                    id=str(existing_participation.id),
                    user_id=str(existing_participation.user_id),
                    username=existing_participation.username,
                    challenge_code=str(existing_participation.challenge_code),
                    status=existing_participation.status,
                    joined_at=existing_participation.joined_at,
                    started_at=existing_participation.started_at,
                    completed_at=existing_participation.completed_at,
                    updated_at=existing_participation.updated_at,
                    progress=existing_participation.progress,
                    personal_target=existing_participation.personal_target,
                    notes=existing_participation.notes,
                    earned_points=existing_participation.earned_points,
                    earned_badges=existing_participation.earned_badges,
                    best_streak=existing_participation.best_streak,
                    current_streak=existing_participation.current_streak,
                    challenge_title=challenge.title,
                    challenge_type=challenge.challenge_type,
                    challenge_difficulty=challenge.difficulty
                )
            else:
                raise HTTPException(status_code=400, detail="Cannot rejoin completed or failed challenge")
        
        # Kezdeti haladás létrehozása
        target_value = join_data.personal_target or challenge.get('target_amount', 0.0)
        initial_progress = ChallengeProgress(
            current_value=0.0,
            target_value=target_value,
            unit="HUF" if challenge.get('challenge_type') != "habit_streak" else "nap",
            percentage=0.0
        )

        # Részvétel létrehozása
        user_challenge = UserChallengeDocument(
            user_id=PydanticObjectId(current_user.id),
            username=current_user.username,
            challenge_code=challenge_code,
            personal_target=join_data.personal_target,
            notes=join_data.notes,
            progress=initial_progress,
            started_at=datetime.utcnow()
        )

        await user_challenge.insert()

        # Most már frissíthetjük a haladást a létrehozott objektummal
        updated_progress = await ChallengeService.calculate_challenge_progress(
            current_user.id, challenge, user_challenge
        )
        user_challenge.progress = updated_progress
        
        # Frissítsd az objektumot az adatbázisban
        await UserChallengeDocument.find_one({"_id": user_challenge.id}).update({
            "$set": {"progress": updated_progress.dict()}
        })

        # Frissítsd a memóriában lévő objektumot is a válaszhoz
        user_challenge.progress = updated_progress
        
        # Kihívás statisztikáinak frissítése
        await ChallengeService.update_challenge_statistics(challenge_code)
        
        return UserChallengeRead(
            id=str(user_challenge.id),
            user_id=str(user_challenge.user_id),
            username=user_challenge.username,
            challenge_code=challenge_code,
            status=user_challenge.status,
            joined_at=user_challenge.joined_at,
            started_at=user_challenge.started_at,
            completed_at=user_challenge.completed_at,
            updated_at=user_challenge.updated_at,
            progress=user_challenge.progress,
            personal_target=user_challenge.personal_target,
            notes=user_challenge.notes,
            earned_points=user_challenge.earned_points,
            earned_badges=user_challenge.earned_badges,
            best_streak=user_challenge.best_streak,
            current_streak=user_challenge.current_streak,
            challenge_title=challenge.get('title', ''),
            challenge_type=ChallengeType(challenge.get('challenge_type', 'savings')),
            challenge_difficulty=ChallengeDifficulty(challenge.get('difficulty', 'easy'))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining challenge {challenge_code}: {e}")
        raise HTTPException(status_code=500, detail="Failed to join challenge")

# === KIHÍVÁS ELHAGYÁSA ===
@router.delete("/{challenge_code}/leave", status_code=204)
async def leave_challenge(
    challenge_code: str,
    current_user: User = Depends(get_current_user)
):
    """Kihívás elhagyása"""
    try:
        oid = PydanticObjectId(challenge_code)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid challenge ID")
    
    try:
        # Részvétel keresése
        participation = await UserChallengeDocument.find_one({
            "user_id": ObjectId(current_user.id),
            "challenge_code": oid
        })
        
        if not participation:
            raise HTTPException(status_code=400, detail="Not participating in this challenge")
        
        # Státusz frissítése (nem töröljük, hogy megmaradjon a statisztika)
        participation.status = ParticipationStatus.ABANDONED
        participation.updated_at = datetime.utcnow()
        await participation.save()
        
        # Kihívás statisztikáinak frissítése
        await ChallengeService.update_challenge_statistics(challenge_code)
        
        return {"message": "Successfully left the challenge"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error leaving challenge {challenge_code}: {e}")
        raise HTTPException(status_code=500, detail="Failed to leave challenge")

# === SAJÁT KIHÍVÁSOK LISTÁJA ===
@router.get("/my/participations", response_model=UserChallengeListResponse)
async def list_my_challenges(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    status: Optional[ParticipationStatus] = Query(None, description="Státusz szerinti szűrés"),
    challenge_type: Optional[ChallengeType] = Query(None, description="Típus szerinti szűrés")
):
    """Felhasználó saját kihívásainak listája"""
    try:
        # Alapszűrő
        query_filter = {"user_id": ObjectId(current_user.id)}
        
        # Státusz szűrés
        if status:
            query_filter["status"] = status
        
        # Lekérdezés
        total_count = await UserChallengeDocument.find(query_filter).count()
        user_challenges = await UserChallengeDocument.find(query_filter)\
            .sort([("joined_at", -1)])\
            .skip(skip)\
            .limit(limit)\
            .to_list()
        
        # Kihívás adatok lekérése
        challenge_ids = [uc.challenge_code for uc in user_challenges]
        challenges = []
        if challenge_ids:
            challenges = await ChallengeDocument.find({
                "_id": {"$in": challenge_ids}
            }).to_list()
        
        challenge_map = {str(c.id): c for c in challenges}
        
        # Típus szűrés (ha meg van adva)
        if challenge_type:
            user_challenges = [
                uc for uc in user_challenges 
                if challenge_map.get(str(uc.challenge_code), {}).challenge_type == challenge_type
            ]
        
        # Válasz összeállítása
        user_challenge_reads = []
        for uc in user_challenges:
            challenge = challenge_map.get(str(uc.challenge_code))
            if not challenge:
                continue
            
            # Haladás frissítése ha aktív
            if uc.status == ParticipationStatus.ACTIVE:
                updated_progress = await ChallengeService.calculate_challenge_progress(
                    current_user.id, challenge, uc
                )
                uc.progress = updated_progress
                
                # Befejezés ellenőrzése
                if await ChallengeService.check_challenge_completion(uc):
                    await ChallengeService.award_completion_rewards(uc, challenge)
            
            user_challenge_reads.append(UserChallengeRead(
                id=str(uc.id),
                user_id=str(uc.user_id),
                username=uc.username,
                challenge_code=str(uc.challenge_code),
                status=uc.status,
                joined_at=uc.joined_at,
                started_at=uc.started_at,
                completed_at=uc.completed_at,
                updated_at=uc.updated_at,
                progress=uc.progress,
                personal_target=uc.personal_target,
                notes=uc.notes,
                earned_points=uc.earned_points,
                earned_badges=uc.earned_badges,
                best_streak=uc.best_streak,
                current_streak=uc.current_streak,
                challenge_title=challenge.title,
                challenge_type=challenge.challenge_type,
                challenge_difficulty=challenge.difficulty
            ))
        
        return UserChallengeListResponse(
            user_challenges=user_challenge_reads,
            total_count=len(user_challenge_reads),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing user challenges: {e}")
        raise HTTPException(status_code=500, detail="Failed to list user challenges")

# === AJÁNLOTT KIHÍVÁSOK ===
@router.get("/recommendations/for-me", response_model=ChallengeListResponse)
async def get_recommended_challenges(
    current_user: User = Depends(get_current_user),
    limit: int = Query(5, ge=1, le=20)
):
    """Személyre szabott kihívás ajánlások"""
    try:
        recommended_challenges = await ChallengeService.get_recommended_challenges(
            current_user.id, limit
        )
        
        # Felhasználó részvételének ellenőrzése
        challenge_ids = [challenge.id for challenge in recommended_challenges]
        user_participations = []
        if challenge_ids:
            user_participations = await UserChallengeDocument.find({
                "user_id": ObjectId(current_user.id),
                "challenge_code": {"$in": challenge_ids}
            }).to_list()
        
        participation_map = {
            str(up.challenge_code): up for up in user_participations
        }
        
        # Válasz összeállítása
        challenge_reads = []
        for challenge in recommended_challenges:
            challenge_id_str = str(challenge.id)
            participation = participation_map.get(challenge_id_str)
            
            challenge_reads.append(ChallengeRead(
                id=challenge_id_str,
                title=challenge.title,
                description=challenge.description,
                short_description=challenge.short_description,
                challenge_type=challenge.challenge_type,
                difficulty=challenge.difficulty,
                duration_days=challenge.duration_days,
                target_amount=challenge.target_amount,
                rules=challenge.rules,
                rewards=challenge.rewards,
                status=challenge.status,
                created_at=challenge.created_at,
                updated_at=challenge.updated_at,
                participant_count=challenge.participant_count,
                completion_rate=challenge.completion_rate,
                image_url=challenge.image_url,
                tags=challenge.tags,
                creator_username=challenge.creator_username,
                is_participating=participation is not None and participation.status == ParticipationStatus.ACTIVE,
                my_progress=participation.progress if participation else None,
                my_status=participation.status if participation else None
            ))
        
        return ChallengeListResponse(
            challenges=challenge_reads,
            total_count=len(challenge_reads),
            skip=0,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error getting recommended challenges: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommended challenges")

# === KIHÍVÁS HALADÁS FRISSÍTÉSE ===
@router.post("/{challenge_code}/update-progress")
async def update_challenge_progress(
    challenge_code: str,
    current_user: User = Depends(get_current_user)
):
    """Kihívás haladásának manuális frissítése"""
    try:
        oid = challenge_code
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid challenge ID")
    
    try:
        # Részvétel keresése
        participation = await UserChallengeDocument.find_one({
            "user_id": ObjectId(current_user.id),
            "challenge_code": oid
        })
        
        if not participation:
            raise HTTPException(status_code=400, detail="Not participating in this challenge")
        
        if participation.status != ParticipationStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Challenge participation is not active")
        
        # Kihívás lekérése
        challenge = await ChallengeDocument.get(oid)
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Haladás újraszámítása
        updated_progress = await ChallengeService.calculate_challenge_progress(
            current_user.id, challenge, participation
        )
        
        participation.progress = updated_progress
        participation.updated_at = datetime.utcnow()
        
        # Befejezés ellenőrzése
        if await ChallengeService.check_challenge_completion(participation):
            await ChallengeService.award_completion_rewards(participation, challenge)
        else:
            await participation.save()
        
        return {
            "message": "Progress updated successfully",
            "progress": updated_progress
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating challenge progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to update progress")
    

    # Bulk challenge creation response model
class BulkChallengeResponse(BaseModel):
    created_count: int
    skipped_count: int
    errors: List[str] = []
    created_challenges: List[str] = []  # challenge IDs

# === BULK CHALLENGE CREATION ===
@router.post("/bulk/create", response_model=BulkChallengeResponse)
async def bulk_create_challenges(
    challenges_data: List[ChallengeCreate],
    current_user: User = Depends(get_current_user)
):
    """Több kihívás egyszerre történő létrehozása"""
    
    # Ellenőrizzük, hogy a felhasználó admin-e (opcionális)
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    created_count = 0
    skipped_count = 0
    errors = []
    created_challenges = []
    
    try:
        for idx, challenge_data in enumerate(challenges_data):
            try:
                # Ellenőrizzük, hogy már létezik-e ilyen címmel
                existing = await ChallengeDocument.find_one({
                    "title": challenge_data.title
                })
                
                if existing:
                    skipped_count += 1
                    errors.append(f"Challenge #{idx + 1} '{challenge_data.title}' already exists")
                    continue
                
                # Kihívás létrehozása
                challenge_doc = ChallengeDocument(
                    title=challenge_data.title,
                    description=challenge_data.description,
                    short_description=challenge_data.short_description,
                    challenge_type=challenge_data.challenge_type,
                    difficulty=challenge_data.difficulty,
                    duration_days=challenge_data.duration_days,
                    target_amount=challenge_data.target_amount,
                    rules=challenge_data.rules or [],
                    rewards=challenge_data.rewards,
                    status=ChallengeStatus.ACTIVE,
                    tags=challenge_data.tags or [],
                    image_url=challenge_data.image_url,
                    track_categories=getattr(challenge_data, 'track_categories', []),
                    track_accounts=getattr(challenge_data, 'track_accounts', []),
                    creator_username=current_user.username,
                    participant_count=0,
                    completion_rate=0.0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                await challenge_doc.insert()
                created_count += 1
                created_challenges.append(str(challenge_doc.id))
                
            except Exception as e:
                errors.append(f"Error creating challenge #{idx + 1}: {str(e)}")
                logger.error(f"Error creating challenge {idx + 1}: {e}")
        
        return BulkChallengeResponse(
            created_count=created_count,
            skipped_count=skipped_count,
            errors=errors,
            created_challenges=created_challenges
        )
        
    except Exception as e:
        logger.error(f"Error in bulk challenge creation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create challenges")


from typing import List
from app.models.challenge import (
    ChallengeRule, ChallengeReward, ChallengeStatus
)

# === DEFAULT CHALLENGES DATA ===
@router.post("/bulk/create-defaults")
async def create_default_challenges(
    current_user: User = Depends(get_current_user),
    lang: str = Query('hu', description="Nyelv a kihívások létrehozásához")
):
    """Alapértelmezett kihívások létrehozása"""
    
    # Ellenőrizzük, hogy a felhasználó admin-e (opcionális)
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Lokalizált kihívások betöltése
        challenges_data = challenge_localization_service.get_all_challenges(lang)
        
        created_count = 0
        skipped_count = 0
        errors = []
        created_challenges = []
        
        for challenge_data in challenges_data:
            try:
                # Ellenőrizzük, hogy már létezik-e ilyen kóddal
                existing = await ChallengeDocument.find_one({
                    "challenge_code": challenge_data.get("code")
                })
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Kihívás létrehozása
                challenge_doc = ChallengeDocument(
                    challenge_code=challenge_data.get("code"),  # ÚJ mező
                    title=challenge_data["title"],
                    description=challenge_data["description"],
                    short_description=challenge_data.get("short_description"),
                    challenge_type=ChallengeType(challenge_data["challenge_type"]),
                    difficulty=ChallengeDifficulty(challenge_data["difficulty"]),
                    duration_days=challenge_data["duration_days"],
                    target_amount=challenge_data.get("target_amount"),
                    rules=[ChallengeRule(**rule) for rule in challenge_data.get("rules", [])],
                    rewards=ChallengeReward(**challenge_data.get("rewards", {})),
                    status=ChallengeStatus.ACTIVE,
                    tags=challenge_data.get("tags", []),
                    creator_username=current_user.username,
                    # ... többi mező
                )
                
                await challenge_doc.insert()
                created_count += 1
                created_challenges.append(str(challenge_doc.id))
                
            except Exception as e:
                errors.append(f"Error creating '{challenge_data.get('title', 'unknown')}': {str(e)}")
        
        return BulkChallengeResponse(
            created_count=created_count,
            skipped_count=skipped_count,
            errors=errors,
            created_challenges=created_challenges
        )
        
    except Exception as e:
        logger.error(f"Error creating default challenges: {e}")
        raise HTTPException(status_code=500, detail="Failed to create default challenges")