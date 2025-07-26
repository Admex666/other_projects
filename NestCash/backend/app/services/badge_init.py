# app/services/badge_init.py
import logging
from datetime import datetime
from app.models.badge import BadgeType, BadgeCategory, BadgeRarity

logger = logging.getLogger(__name__)

async def initialize_default_badges():
    """Alapértelmezett badge típusok inicializálása"""
    
    default_badges = [
        # === TRANZAKCIÓ ALAPÚ BADGE-EK ===
        {
            "code": "first_transaction",
            "name": "Első lépés",
            "description": "Első tranzakció rögzítése",
            "icon": "🌟",
            "category": BadgeCategory.TRANSACTION,
            "rarity": BadgeRarity.COMMON,
            "condition_type": "transaction_count",
            "condition_config": {"target_count": 1},
            "points": 10
        },
        {
            "code": "transaction_veteran",
            "name": "Veterán",
            "description": "100 tranzakció rögzítése",
            "icon": "🏆",
            "category": BadgeCategory.TRANSACTION,
            "rarity": BadgeRarity.UNCOMMON,
            "condition_type": "transaction_count",
            "condition_config": {"target_count": 100},
            "points": 50
        },
        {
            "code": "big_spender",
            "name": "Nagy költekező",
            "description": "1 millió forint kiadás",
            "icon": "💸",
            "category": BadgeCategory.MILESTONE,
            "rarity": BadgeRarity.RARE,
            "condition_type": "spending_milestone",
            "condition_config": {"target_amount": 1000000},
            "points": 100
        },
        
        # === MEGTAKARÍTÁSI BADGE-EK ===
        {
            "code": "first_savings",
            "name": "Takarékos kezdet",
            "description": "Első megtakarítás",
            "icon": "🐷",
            "category": BadgeCategory.SAVINGS,
            "rarity": BadgeRarity.COMMON,
            "condition_type": "saving_milestone",
            "condition_config": {"target_amount": 10000, "account_type": "megtakaritas"},
            "points": 20
        },
        {
            "code": "savings_master",
            "name": "Megtakarítási mester",
            "description": "500 ezer forint megtakarítás",
            "icon": "💰",
            "category": BadgeCategory.SAVINGS,
            "rarity": BadgeRarity.EPIC,
            "condition_type": "saving_milestone",
            "condition_config": {"target_amount": 500000, "account_type": "megtakaritas"},
            "points": 200
        },
        
        # === TUDÁS ALAPÚ BADGE-EK ===
        {
            "code": "knowledge_beginner",
            "name": "Tudásszomjas",
            "description": "Első lecke teljesítése",
            "icon": "📚",
            "category": BadgeCategory.KNOWLEDGE,
            "rarity": BadgeRarity.COMMON,
            "condition_type": "knowledge_lessons",
            "condition_config": {"target_lessons": 1, "min_quiz_score": 70},
            "points": 15
        },
        {
            "code": "knowledge_expert",
            "name": "Pénzügyi szakértő",
            "description": "10 lecke teljesítése",
            "icon": "🎓",
            "category": BadgeCategory.KNOWLEDGE,
            "rarity": BadgeRarity.UNCOMMON,
            "condition_type": "knowledge_lessons",
            "condition_config": {"target_lessons": 10, "min_quiz_score": 70},
            "points": 75
        },
        {
            "code": "quiz_perfectionist",
            "name": "Perfekcionista",
            "description": "5 lecke 100%-os eredménnyel",
            "icon": "💯",
            "category": BadgeCategory.KNOWLEDGE,
            "rarity": BadgeRarity.RARE,
            "condition_type": "knowledge_lessons",
            "condition_config": {"target_lessons": 5, "min_quiz_score": 100},
            "points": 150
        },
        
        # === SOROZAT ALAPÚ BADGE-EK ===
        {
            "code": "streak_week",
            "name": "Heti rutin",
            "description": "7 napos tanulási sorozat",
            "icon": "🔥",
            "category": BadgeCategory.STREAK,
            "rarity": BadgeRarity.COMMON,
            "condition_type": "knowledge_streak",
            "condition_config": {"target_streak": 7},
            "points": 30
        },
        {
            "code": "streak_month",
            "name": "Havi bajnok",
            "description": "30 napos tanulási sorozat",
            "icon": "🚀",
            "category": BadgeCategory.STREAK,
            "rarity": BadgeRarity.RARE,
            "condition_config": {"target_streak": 30},
            "condition_type": "knowledge_streak",
            "points": 200
        },
        {
            "code": "streak_legendary",
            "name": "Legendás kitartás",
            "description": "100 napos tanulási sorozat",
            "icon": "👑",
            "category": BadgeCategory.STREAK,
            "rarity": BadgeRarity.LEGENDARY,
            "condition_type": "knowledge_streak",
            "condition_config": {"target_streak": 100},
            "points": 500
        },
        
        # === KÖZÖSSÉGI BADGE-EK ===
        {
            "code": "social_first_post",
            "name": "Közösségi tag",
            "description": "Első poszt megosztása",
            "icon": "💬",
            "category": BadgeCategory.SOCIAL,
            "rarity": BadgeRarity.COMMON,
            "condition_type": "social_posts",
            "condition_config": {"target_posts": 1},
            "points": 15
        },
        {
            "code": "social_active",
            "name": "Aktív közösségi tag",
            "description": "10 poszt megosztása",
            "icon": "🗣️",
            "category": BadgeCategory.SOCIAL,
            "rarity": BadgeRarity.UNCOMMON,
            "condition_type": "social_posts",
            "condition_config": {"target_posts": 10},
            "points": 50
        },
        
        # === MÉRFÖLDKŐ BADGE-EK ===
        {
            "code": "welcome_badge",
            "name": "Üdvözlet!",
            "description": "Regisztráció a NestCash-be",
            "icon": "👋",
            "category": BadgeCategory.MILESTONE,
            "rarity": BadgeRarity.COMMON,
            "condition_type": "milestone_days",
            "condition_config": {"target_days": 0},
            "points": 5
        },
        {
            "code": "loyal_user",
            "name": "Hűséges felhasználó",
            "description": "30 napja regisztrált",
            "icon": "💙",
            "category": BadgeCategory.MILESTONE,
            "rarity": BadgeRarity.UNCOMMON,
            "condition_type": "milestone_days",
            "condition_config": {"target_days": 30},
            "points": 40
        },
        {
            "code": "annual_user",
            "name": "Éves tag",
            "description": "1 éve használja a NestCash-t",
            "icon": "🎉",
            "category": BadgeCategory.MILESTONE,
            "rarity": BadgeRarity.EPIC,
            "condition_type": "milestone_days",
            "condition_config": {"target_days": 365},
            "points": 300
        },
        
        # === KÜLÖNLEGES BADGE-EK ===
        {
            "code": "early_adopter",
            "name": "Korai elfogadó",
            "description": "A NestCash első felhasználói között",
            "icon": "🌅",
            "category": BadgeCategory.SPECIAL,
            "rarity": BadgeRarity.LEGENDARY,
            "condition_type": "milestone_days",
            "condition_config": {"target_days": 0},  # Manuálisan adható
            "points": 1000
        },
        {
            "code": "beta_tester",
            "name": "Béta tesztelő",
            "description": "Segített a fejlesztésben",
            "icon": "🧪",
            "category": BadgeCategory.SPECIAL,
            "rarity": BadgeRarity.EPIC,
            "condition_type": "milestone_days",
            "condition_config": {"target_days": 0},  # Manuálisan adható
            "points": 500
        },
        
        # === SZINTES BADGE-EK ===
        {
            "code": "transaction_master",
            "name": "Tranzakció mester",
            "description": "Tranzakciók rögzítésének mestere",
            "icon": "📊",
            "category": BadgeCategory.TRANSACTION,
            "rarity": BadgeRarity.RARE,
            "condition_type": "transaction_count",
            "condition_config": {"target_count": 50},
            "points": 25,
            "has_levels": True,
            "max_level": 10,  # 50, 100, 200, 400... tranzakció
            "is_repeatable": True
        },
        {
            "code": "savings_champion",
            "name": "Megtakarítási bajnok",
            "description": "Folyamatos megtakarítás",
            "icon": "🏅",
            "category": BadgeCategory.SAVINGS,
            "rarity": BadgeRarity.UNCOMMON,
            "condition_type": "saving_milestone",
            "condition_config": {"target_amount": 50000, "account_type": "megtakaritas"},
            "points": 50,
            "has_levels": True,
            "max_level": 5,  # 50k, 100k, 250k, 500k, 1M
            "is_repeatable": True
        }
    ]
    
    try:
        created_count = 0
        updated_count = 0
        
        for badge_data in default_badges:
            # Ellenőrizzük, hogy már létezik-e
            existing_badge = await BadgeType.find_one({"code": badge_data["code"]})
            
            if existing_badge:
                # Frissítjük a meglévőt (kivéve a condition_config-ot, hogy ne törjük el a testreszabásokat)
                for key, value in badge_data.items():
                    if key != "condition_config" or not existing_badge.condition_config:
                        setattr(existing_badge, key, value)
                
                existing_badge.updated_at = datetime.utcnow()
                await existing_badge.save()
                updated_count += 1
                
            else:
                # Új badge létrehozása
                new_badge = BadgeType(**badge_data)
                await new_badge.insert()
                created_count += 1
        
        logger.info(f"Badge initialization completed: {created_count} created, {updated_count} updated")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing badges: {e}")
        return False

async def award_welcome_badges():
    """Üdvözlő badge-ek odaítélése minden regisztrált felhasználónak"""
    try:
        from app.models.user import UserDocument
        from app.models.badge import UserBadge
        from datetime import datetime
        
        # Minden felhasználó lekérése
        users = await UserDocument.find({}).to_list()
        
        welcome_badge_code = "welcome_badge"
        awarded_count = 0
        
        for user in users:
            # Ellenőrizzük, hogy már megkapta-e
            existing = await UserBadge.find_one({
                "user_id": user.id,
                "badge_code": welcome_badge_code
            })
            
            if not existing:
                welcome_badge = UserBadge(
                    user_id=user.id,
                    badge_code=welcome_badge_code,
                    context_data={
                        "registration_date": user.registration_date.isoformat(),
                        "auto_awarded": True
                    }
                )
                await welcome_badge.insert()
                awarded_count += 1
        
        logger.info(f"Welcome badges awarded to {awarded_count} users")
        return True
        
    except Exception as e:
        logger.error(f"Error awarding welcome badges: {e}")
        return False

# Convenience funkció az összes inicializáláshoz
async def initialize_badge_system():
    """Teljes badge rendszer inicializálása"""
    logger.info("Initializing badge system...")
    
    # Badge típusok inicializálása
    badges_success = await initialize_default_badges()
    
    # Üdvözlő badge-ek kiosztása
    welcome_success = await award_welcome_badges()
    
    if badges_success and welcome_success:
        logger.info("Badge system initialization completed successfully")
        return True
    else:
        logger.error("Badge system initialization failed")
        return False