# app/seeds/challenge_seeds.py
from datetime import datetime
from app.models.challenge import (
    ChallengeDocument, ChallengeType, ChallengeDifficulty, 
    ChallengeStatus, ChallengeReward, ChallengeRule
)

DEFAULT_CHALLENGES = [
    {
        "title": "30 napos megtakarítási kihívás",
        "description": "Tegyél félre 50,000 HUF-ot 30 nap alatt! Ez egy nagyszerű módja annak, hogy elkezdj rendszeresen megtakarítani és kiépítsd a pénzügyi tartalékaidat.",
        "short_description": "50,000 HUF megtakarítás 30 nap alatt",
        "challenge_type": ChallengeType.SAVINGS,
        "difficulty": ChallengeDifficulty.EASY,
        "duration_days": 30,
        "target_amount": 50000.0,
        "rules": [
            ChallengeRule(
                type="min_amount",
                value=1000.0,
                description="Minimum napi 1,000 HUF megtakarítás"
            )
        ],
        "rewards": ChallengeReward(
            points=100,
            badges=["first_saver", "month_complete"],
            title="Takarékos Kezdő"
        ),
        "tags": ["megtakarítás", "kezdő", "30nap"],
        "image_url": "/images/challenges/savings_30.jpg"
    },
    {
        "title": "Kávé kihívás - Havi kiadás csökkentés",
        "description": "Csökkentsd a külső étkezési kiadásaidat (pl. kávé, ebéd) 50%-kal egy hónapon keresztül. Készíts otthon és vigyél magaddal!",
        "short_description": "Külső étkezési kiadások 50%-os csökkentése",
        "challenge_type": ChallengeType.EXPENSE_REDUCTION,
        "difficulty": ChallengeDifficulty.MEDIUM,
        "duration_days": 30,
        "target_amount": 20000.0,  # Átlagos megtakarítás összeg
        "rules": [
            ChallengeRule(
                type="max_amount",
                value=500.0,
                description="Maximum napi 500 HUF külső étkezés"
            )
        ],
        "rewards": ChallengeReward(
            points=150,
            badges=["expense_cutter", "home_chef"],
            title="Költségcsökkentő"
        ),
        "tags": ["kiadás", "étkezés", "takarékosság"],
        "track_categories": ["Étkezés", "Kávé", "Étterem"],
        "image_url": "/images/challenges/coffee_challenge.jpg"
    },
    {
        "title": "21 napos pénzügyi tudatosság",
        "description": "Vezess napló minden tranzakcióról 21 napig. Legalább 3 tranzakciót rögzíts naponta és írj hozzá megjegyzést!",
        "short_description": "Napi pénzügyi napló vezetése 21 napig",
        "challenge_type": ChallengeType.HABIT_STREAK,
        "difficulty": ChallengeDifficulty.EASY,
        "duration_days": 21,
        "rules": [
            ChallengeRule(
                type="min_transactions",
                value=3.0,
                description="Minimum 3 tranzakció rögzítése naponta"
            ),
            ChallengeRule(
                type="required_description",
                value=1.0,
                description="Minden tranzakciónak legyen leírása"
            )
        ],
        "rewards": ChallengeReward(
            points=80,
            badges=["consistent_tracker", "habit_builder"],
            title="Tudatos Pénzkezelő"
        ),
        "tags": ["szokás", "napló", "tudatosság"],
        "image_url": "/images/challenges/awareness_21.jpg"
    },
    {
        "title": "Nagy megtakarítási kihívás - 6 hónap",
        "description": "Tegyél félre 500,000 HUF-ot 6 hónap alatt! Ez egy komolyabb kihívás, ami valódi pénzügyi fegyelmet igényel.",
        "short_description": "500,000 HUF megtakarítás 6 hónapon át",
        "challenge_type": ChallengeType.SAVINGS,
        "difficulty": ChallengeDifficulty.HARD,
        "duration_days": 180,
        "target_amount": 500000.0,
        "rules": [
            ChallengeRule(
                type="min_amount",
                value=2500.0,
                description="Minimum napi 2,500 HUF megtakarítás"
            ),
            ChallengeRule(
                type="consistency",
                value=5.0,
                description="Legalább 5 naponta kell megtakarítani"
            )
        ],
        "rewards": ChallengeReward(
            points=500,
            badges=["big_saver", "half_year_hero", "financial_discipline"],
            title="Megtakarítási Mester"
        ),
        "tags": ["megtakarítás", "haladó", "6hónap", "nagy kihívás"],
        "image_url": "/images/challenges/big_savings.jpg"
    },
    {
        "title": "Befektetési alapok - Első lépések",
        "description": "Kezdj el befektetni! Tegyél el legalább 100,000 HUF-ot befektetési számlára 60 nap alatt.",
        "short_description": "100,000 HUF befektetés 60 nap alatt",
        "challenge_type": ChallengeType.INVESTMENT,
        "difficulty": ChallengeDifficulty.MEDIUM,
        "duration_days": 60,
        "target_amount": 100000.0,
        "rules": [
            ChallengeRule(
                type="min_amount",
                value=1500.0,
                description="Minimum napi 1,500 HUF befektetés"
            )
        ],
        "rewards": ChallengeReward(
            points=200,
            badges=["investor_starter", "future_builder"],
            title="Kezdő Befektető"
        ),
        "tags": ["befektetés", "jövő", "tőke"],
        "track_accounts": ["Részvény", "Alapok", "Kötvény"],
        "image_url": "/images/challenges/investment_start.jpg"
    },
    {
        "title": "Hetente egyszer streak",
        "description": "Rögzíts legalább egy tranzakciót minden héten 12 héten keresztül. Tartsd karban a pénzügyi tudatosságodat!",
        "short_description": "Heti rendszerességű rögzítés 12 hétig",
        "challenge_type": ChallengeType.HABIT_STREAK,
        "difficulty": ChallengeDifficulty.EASY,
        "duration_days": 84,  # 12 hét
        "rules": [
            ChallengeRule(
                type="weekly_minimum",
                value=1.0,
                description="Legalább 1 tranzakció hetente"
            )
        ],
        "rewards": ChallengeReward(
            points=60,
            badges=["weekly_warrior", "consistency_keeper"],
            title="Rendszeres Nyomkövető"
        ),
        "tags": ["heti", "szokás", "rendszeresség"],
        "image_url": "/images/challenges/weekly_streak.jpg"
    }
]

async def create_default_challenges():
    """Alapértelmezett kihívások létrehozása az adatbázisban"""
    try:
        existing_count = await ChallengeDocument.find().count()
        if existing_count > 0:
            print(f"Already {existing_count} challenges in database, skipping seed")
            return
        
        created_challenges = []
        for challenge_data in DEFAULT_CHALLENGES:
            challenge = ChallengeDocument(**challenge_data)
            await challenge.insert()
            created_challenges.append(challenge)
            print(f"Created challenge: {challenge.title}")
        
        print(f"Successfully created {len(created_challenges)} default challenges")
        return created_challenges
        
    except Exception as e:
        print(f"Error creating default challenges: {e}")
        return []

# Manuális futtatáshoz
if __name__ == "__main__":
    import asyncio
    from app.core.db import init_db
    
    async def main():
        await init_db()
        await create_default_challenges()
    
    asyncio.run(main())