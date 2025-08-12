# app/services/accountability_service.py
from typing import List, Optional, Dict, Tuple
from beanie import PydanticObjectId
from datetime import datetime, timedelta
import logging

from app.models.accountability_models import (
    AccountabilityProfile, Partnership, CheckIn, PartnershipStatus,
    CheckInFrequency, GoalCategory, MatchScore, PartnerSuggestion,
    MotivationStyle, PersonalityType
)
from app.models.user import UserDocument
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

class AccountabilityService:
    """Accountability partner szolgáltatás"""
    
    @staticmethod
    async def get_partner_suggestions(
        user_id: str, 
        limit: int = 10,
        exclude_existing: bool = True
    ) -> List[PartnerSuggestion]:
        """Partner javaslatok generálása matching algoritmussal"""
        try:
            # Felhasználó profiljának lekérése
            user_profile = await AccountabilityProfile.find_one(
                {"user_id": PydanticObjectId(user_id), "is_active": True}
            )
            
            if not user_profile:
                return []
            
            # Meglévő partnerek kizárása
            excluded_user_ids = {PydanticObjectId(user_id)}
            
            if exclude_existing:
                existing_partnerships = await Partnership.find({
                    "$or": [
                        {"requester_id": PydanticObjectId(user_id)},
                        {"requested_id": PydanticObjectId(user_id)}
                    ],
                    "status": {"$in": [PartnershipStatus.ACTIVE, PartnershipStatus.PENDING]}
                }).to_list()
                
                for partnership in existing_partnerships:
                    if str(partnership.requester_id) != user_id:
                        excluded_user_ids.add(partnership.requester_id)
                    if str(partnership.requested_id) != user_id:
                        excluded_user_ids.add(partnership.requested_id)
            
            # Potenciális partnerek lekérése
            potential_partners = await AccountabilityProfile.find({
                "user_id": {"$nin": list(excluded_user_ids)},
                "is_active": True,
                "is_looking_for_partners": True
            }).to_list()
            
            # Kompatibilitási pontszám számítása
            suggestions = []
            for partner_profile in potential_partners:
                score = await AccountabilityService._calculate_compatibility_score(
                    user_profile, partner_profile
                )
                
                if score >= 0.3:  # Minimum kompatibilitási küszöb
                    # Felhasználó adatok lekérése
                    partner_user = await UserDocument.get(partner_profile.user_id)
                    if partner_user:
                        suggestions.append(PartnerSuggestion(
                            user_id=str(partner_profile.user_id),
                            username=partner_user.username,
                            bio=partner_profile.bio,
                            goal_categories=partner_profile.goal_categories,
                            compatibility_score=score,
                            common_goals=AccountabilityService._get_common_goals(
                                user_profile, partner_profile
                            ),
                            matching_factors=AccountabilityService._get_matching_factors(
                                user_profile, partner_profile
                            )
                        ))
            
            # Pontszám szerint rendezés és limit alkalmazása
            suggestions.sort(key=lambda x: x.compatibility_score, reverse=True)
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting partner suggestions: {e}")
            return []
    
    @staticmethod
    async def _calculate_compatibility_score(
        profile1: AccountabilityProfile,
        profile2: AccountabilityProfile
    ) -> float:
        """Kompatibilitási pontszám számítása két profil között"""
        score = 0.0
        
        # Közös célok (30% súly)
        common_goals = set(profile1.goal_categories) & set(profile2.goal_categories)
        total_goals = set(profile1.goal_categories) | set(profile2.goal_categories)
        if total_goals:
            goal_score = len(common_goals) / len(total_goals)
            score += goal_score * 0.3
        
        # Check-in gyakoriság kompatibilitás (25% súly)
        freq_compatibility = AccountabilityService._get_frequency_compatibility(
            profile1.checkin_frequency, profile2.checkin_frequency
        )
        score += freq_compatibility * 0.25
        
        # Motivációs stílus (20% súly)
        if profile1.motivation_style == profile2.motivation_style:
            score += 0.2
        elif AccountabilityService._are_compatible_motivation_styles(
            profile1.motivation_style, profile2.motivation_style
        ):
            score += 0.1
        
        # Személyiség típus (15% súly)
        if profile1.personality_type == profile2.personality_type:
            score += 0.15
        elif AccountabilityService._are_compatible_personalities(
            profile1.personality_type, profile2.personality_type
        ):
            score += 0.08
        
        # Időzóna (10% súly)
        if profile1.timezone == profile2.timezone:
            score += 0.1
        
        return min(1.0, score)
    
    @staticmethod
    def _get_frequency_compatibility(freq1: CheckInFrequency, freq2: CheckInFrequency) -> float:
        """Check-in gyakoriság kompatibilitás számítása"""
        freq_order = [
            CheckInFrequency.DAILY,
            CheckInFrequency.EVERY_OTHER_DAY,
            CheckInFrequency.WEEKLY,
            CheckInFrequency.BI_WEEKLY
        ]
        
        try:
            idx1 = freq_order.index(freq1)
            idx2 = freq_order.index(freq2)
            diff = abs(idx1 - idx2)
            
            if diff == 0:
                return 1.0
            elif diff == 1:
                return 0.7
            elif diff == 2:
                return 0.4
            else:
                return 0.1
        except ValueError:
            return 0.5
    
    @staticmethod
    async def check_partnership_limit(user_id: str) -> Tuple[bool, int, int]:
        """Accountability partner limit ellenőrzése"""
        try:
            # Jelenlegi aktív partnerek száma
            active_partnerships = await Partnership.find({
                "$or": [
                    {"requester_id": PydanticObjectId(user_id)},
                    {"requested_id": PydanticObjectId(user_id)}
                ],
                "status": PartnershipStatus.ACTIVE
            }).count()
            
            # Előfizetés típus alapján limit
            feature_access = await PermissionService.check_feature_access(
                user_id=user_id,
                feature="accountability_partner",
                current_partner_count=active_partnerships
            )
            
            limit = feature_access.current_limit or 1  # Default 1 FREE usernek
            can_add_more = feature_access.has_access
            
            return can_add_more, active_partnerships, limit
            
        except Exception as e:
            logger.error(f"Error checking partnership limit: {e}")
            return False, 0, 1
    
    @staticmethod
    async def create_partnership_request(
        requester_id: str,
        requested_id: str,
        checkin_frequency: CheckInFrequency,
        shared_goals: List[str]
    ) -> Partnership:
        """Új partnership kérelem létrehozása"""
        partnership = Partnership(
            requester_id=PydanticObjectId(requester_id),
            requested_id=PydanticObjectId(requested_id),
            checkin_frequency=checkin_frequency,
            shared_goals=shared_goals
        )
        
        await partnership.insert()
        return partnership
    
    @staticmethod
    async def create_checkin(
        partnership_id: str,
        user_id: str,
        goals_met: bool,
        progress_rating: int,
        notes: Optional[str] = None,
        habit_completions: Optional[List[str]] = None
    ) -> CheckIn:
        """Új check-in létrehozása"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Ellenőrizzük, hogy ma már volt-e check-in
        existing = await CheckIn.find_one({
            "partnership_id": PydanticObjectId(partnership_id),
            "user_id": PydanticObjectId(user_id),
            "date": today
        })
        
        if existing:
            # Frissítjük a meglévőt
            existing.goals_met = goals_met
            existing.progress_rating = progress_rating
            existing.notes = notes
            existing.habit_completions = [PydanticObjectId(hid) for hid in (habit_completions or [])]
            await existing.save()
            checkin = existing
        else:
            # Új check-in
            checkin = CheckIn(
                partnership_id=PydanticObjectId(partnership_id),
                user_id=PydanticObjectId(user_id),
                date=today,
                goals_met=goals_met,
                progress_rating=progress_rating,
                notes=notes,
                habit_completions=[PydanticObjectId(hid) for hid in (habit_completions or [])]
            )
            await checkin.insert()
        
        # Partnership statisztikák frissítése
        await AccountabilityService._update_partnership_stats(partnership_id)
        
        return checkin
    
    @staticmethod
    async def _update_partnership_stats(partnership_id: str):
        """Partnership statisztikák frissítése"""
        try:
            partnership = await Partnership.get(PydanticObjectId(partnership_id))
            if not partnership:
                return
            
            checkins = await CheckIn.find({"partnership_id": PydanticObjectId(partnership_id)}).to_list()
            
            partnership.total_checkins = len(checkins)
            partnership.successful_checkins = sum(1 for c in checkins if c.goals_met)
            await partnership.save()
            
        except Exception as e:
            logger.error(f"Error updating partnership stats: {e}")

    @staticmethod
    def _are_compatible_motivation_styles(style1: MotivationStyle, style2: MotivationStyle) -> bool:
        """Ellenőrzi, hogy két motivációs stílus kompatibilis-e egymással"""
        # Kompatibilis párok meghatározása
        compatible_pairs = {
            (MotivationStyle.POSITIVE_REINFORCEMENT, MotivationStyle.FLEXIBLE),
            (MotivationStyle.CHALLENGE_BASED, MotivationStyle.STRUCTURED),
            (MotivationStyle.STRUCTURED, MotivationStyle.FLEXIBLE),
        }
        
        # Mindkét irányban ellenőrizzük
        return (style1, style2) in compatible_pairs or (style2, style1) in compatible_pairs
    
    @staticmethod
    def _are_compatible_personalities(type1: PersonalityType, type2: PersonalityType) -> bool:
        """Ellenőrzi, hogy két személyiség típus kompatibilis-e egymással"""
        # Kompatibilis párok meghatározása
        compatible_pairs = {
            (PersonalityType.COMPETITIVE_DIRECT, PersonalityType.BALANCED),
            (PersonalityType.SUPPORTIVE_GENTLE, PersonalityType.BALANCED),
        }
        
        # Mindkét irányban ellenőrizzük
        return (type1, type2) in compatible_pairs or (type2, type1) in compatible_pairs
    
    @staticmethod
    def _get_common_goals(profile1: AccountabilityProfile, profile2: AccountabilityProfile) -> List[str]:
        """Közös célok meghatározása két profil között"""
        common_categories = set(profile1.goal_categories) & set(profile2.goal_categories)
        
        # GoalCategory enum értékeket display name-re konvertáljuk
        goal_display_names = {
            GoalCategory.FINANCIAL: "Pénzügyek",
            GoalCategory.SAVINGS: "Megtakarítás", 
            GoalCategory.INVESTMENT: "Befektetés",
            GoalCategory.SPENDING_CONTROL: "Kiadások kontroll",
            GoalCategory.HABIT_BUILDING: "Szokásépítés"
        }
        
        return [goal_display_names.get(category, category.value) for category in common_categories]
    
    @staticmethod
    def _get_matching_factors(profile1: AccountabilityProfile, profile2: AccountabilityProfile) -> Dict[str, str]:
        """Matching faktorok meghatározása két profil között"""
        factors = {}
        
        # Közös célok száma
        common_goals_count = len(set(profile1.goal_categories) & set(profile2.goal_categories))
        if common_goals_count > 0:
            factors["common_goals"] = f"{common_goals_count} közös cél"
        
        # Check-in gyakoriság
        if profile1.checkin_frequency == profile2.checkin_frequency:
            factors["checkin_frequency"] = "Azonos check-in gyakoriság"
        
        # Motivációs stílus
        if profile1.motivation_style == profile2.motivation_style:
            factors["motivation_style"] = "Azonos motivációs stílus"
        elif AccountabilityService._are_compatible_motivation_styles(profile1.motivation_style, profile2.motivation_style):
            factors["motivation_style"] = "Kompatibilis motivációs stílus"
        
        # Személyiség típus
        if profile1.personality_type == profile2.personality_type:
            factors["personality_type"] = "Azonos személyiség típus"
        elif AccountabilityService._are_compatible_personalities(profile1.personality_type, profile2.personality_type):
            factors["personality_type"] = "Kompatibilis személyiség típus"
        
        # Időzóna
        if profile1.timezone == profile2.timezone:
            factors["timezone"] = "Azonos időzóna"
        
        return factors
    
    @staticmethod
    async def get_checkins(
        partnership_id: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[CheckIn]:
        """Check-in-ek lekérése egy partnership-hez"""
        try:
            query_filter = {"partnership_id": PydanticObjectId(partnership_id)}
            
            if user_id:
                query_filter["user_id"] = PydanticObjectId(user_id)
            
            checkins = await CheckIn.find(query_filter).sort(-CheckIn.created_at).limit(limit).to_list()
            
            return checkins
            
        except Exception as e:
            logger.error(f"Error getting checkins: {e}")
            return []