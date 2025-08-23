# app/services/onboarding_service.py
from typing import List, Optional, Dict, Any
from beanie import PydanticObjectId

from app.models.user import UserDocument
from app.models.onboarding import UserType, UserIntent, BasicSetupData, OnboardingProgress
from app.models.account import AllUserAccountsDocument, UserAccounts, AccountDetails, SubAccountDetails

class OnboardingService:
    
    @staticmethod
    def determine_user_type(intents: List[UserIntent]) -> UserType:
        """Meghatározza a felhasználó típusát a kiválasztott szándékok alapján"""
        
        # Ha nincs választás vagy "nem tudom"
        if not intents or UserIntent.NOT_SURE in intents:
            return UserType.DEFAULT
        
        intent_weights = {
            UserIntent.TRACK_SPENDING: {"aware_spender": 3, "advanced": 1},
            UserIntent.COMPARE_WITH_OTHERS: {"competitive": 3, "community_driven": 1},
            UserIntent.LEARN_AND_IMPROVE: {"learner": 3, "aware_spender": 1},
            UserIntent.COMMUNITY_GROWTH: {"community_driven": 3, "learner": 1},
            UserIntent.ADVANCED_FEATURES: {"advanced": 3, "competitive": 1}
        }
        
        type_scores = {
            "aware_spender": 0,
            "community_driven": 0,
            "learner": 0,
            "advanced": 0,
            "competitive": 0
        }
        
        for intent in intents:
            if intent in intent_weights:
                for user_type, weight in intent_weights[intent].items():
                    type_scores[user_type] += weight
        
        # A legnagyobb pontszámú típus visszaadása
        best_type = max(type_scores, key=type_scores.get)
        return UserType(best_type)
    
    @staticmethod
    def get_tutorial_content(user_type: UserType) -> Dict[str, Any]:
        """Visszaadja a user típusnak megfelelő tutorial tartalmat"""
        
        tutorials = {
            UserType.AWARE_SPENDER: {
                "title": "Ismerd meg a költési korlátokat",
                "description": "Tanulj meg tudatos költési korlátokat beállítani",
                "steps": [
                    {"action": "navigate_to", "target": "limits", "text": "Nézd meg a Limitek menüt"},
                    {"action": "create_limit", "text": "Hozz létre egy havi költési korlátot"},
                    {"action": "set_notification", "text": "Állíts be értesítést a korlát elérésekor"}
                ],
                "cta": "Első korlát beállítása"
            },
            UserType.COMMUNITY_DRIVEN: {
                "title": "Csatlakozz a közösséghez",
                "description": "Fedezd fel kihívásokat és fórumokat",
                "steps": [
                    {"action": "navigate_to", "target": "challenges", "text": "Böngészd a kihívásokat"},
                    {"action": "join_challenge", "text": "Csatlakozz egy kihíváshoz"},
                    {"action": "navigate_to", "target": "forum", "text": "Nézd meg a fórum feedet"}
                ],
                "cta": "Első kihívás kiválasztása"
            },
            UserType.LEARNER: {
                "title": "Fejlődj lépésről lépésre",
                "description": "Kezdj el tanulni pénzügyi alapokról",
                "steps": [
                    {"action": "navigate_to", "target": "knowledge", "text": "Fedezd fel a Tudástárat"},
                    {"action": "start_course", "text": "Kezdj egy alapkurzust"},
                    {"action": "take_quiz", "text": "Próbáld ki az első kvízt"}
                ],
                "cta": "Első tananyag elindítása"
            },
            UserType.ADVANCED: {
                "title": "Automatizáld a pénzügyeidet",
                "description": "Importálj és automatizálj adatokat",
                "steps": [
                    {"action": "navigate_to", "target": "import", "text": "Menj a Tranzakciók > Import menübe"},
                    {"action": "setup_bank_connection", "text": "Kösd össze a bankodat"},
                    {"action": "create_rules", "text": "Hozz létre automatikus szabályokat"}
                ],
                "cta": "Adatok importálása"
            },
            UserType.COMPETITIVE: {
                "title": "Nézd meg, hol állsz!",
                "description": "Kövesd a pontjaidat és ranglistahelyezésedet",
                "steps": [
                    {"action": "navigate_to", "target": "rankings", "text": "Nézd meg a ranglistákat"},
                    {"action": "check_pti", "text": "Ellenőrizd a PTI indexedet"},
                    {"action": "view_achievements", "text": "Fedezd fel az eléréseket"}
                ],
                "cta": "Ranglisták megtekintése"
            }
        }
        
        return tutorials.get(user_type, tutorials[UserType.DEFAULT])
    
    @staticmethod
    async def create_initial_account(user_id: str, setup_data: BasicSetupData):
        """Létrehozza a felhasználó kezdeti számláját"""
        
        all_accounts_doc = await AllUserAccountsDocument.find_one()
        
        if not all_accounts_doc:
            all_accounts_doc = AllUserAccountsDocument(accounts_by_user={})
            await all_accounts_doc.insert()
        
        # Alapértelmezett számla létrehozása
        initial_sub_account = SubAccountDetails(
            balance=setup_data.initial_balance or 0.0,
            currency=setup_data.preferred_currency
        )
        
        user_accounts = UserAccounts(
            likvid=AccountDetails(alszamlak={
                setup_data.main_account_name or "Fő számla": initial_sub_account
            }),
            befektetes=AccountDetails(alszamlak={}),
            megtakaritas=AccountDetails(alszamlak={}),
        )
        
        all_accounts_doc.accounts_by_user[user_id] = user_accounts
        await all_accounts_doc.save()
        
        return user_accounts
    
    @staticmethod
    async def update_user_onboarding_progress(
        user_id: str, 
        step: int, 
        data: Optional[Dict[str, Any]] = None
    ):
        """Frissíti a felhasználó onboarding állapotát"""
        
        user = await UserDocument.find_one(UserDocument.id == PydanticObjectId(user_id))
        if not user:
            raise ValueError("User not found")
        
        # Előző lépés mentése a progress trackinghez
        previous_step = user.onboarding_step
        user.onboarding_step = step
        
        if data:
            if step == 1 and "selected_intents" in data:
                # Célfelmérés lépés
                user.selected_intents = data["selected_intents"]
                determined_type = OnboardingService.determine_user_type(
                    [UserIntent(intent) for intent in data["selected_intents"]]
                )
                user.user_type = determined_type.value
                
            elif step == 2 and "basic_setup" in data:
                # Alap beállítások lépés
                setup_data = data["basic_setup"]
                user.preferred_currency = data["basic_setup"].get("preferred_currency", "HUF")

                # Referral source mentése - ÚJ!
                if "referral_source" in setup_data:
                    user.referral_source = setup_data["referral_source"]
                if "referral_details" in setup_data:
                    user.referral_details = setup_data["referral_details"]

        await user.save()
        print(f"Onboarding progress: User {user_id} moved from step {previous_step} to {step}")
        return user
    
    @staticmethod
    async def complete_onboarding(user_id: str):
        """Befejezi az onboarding folyamatot"""
        
        user = await UserDocument.find_one(UserDocument.id == PydanticObjectId(user_id))
        if not user:
            raise ValueError("User not found")
        
        user.onboarding_completed = True
        user.onboarding_step = 6  # Teljes onboarding
        await user.save()
        
        return user
    
    @staticmethod
    def get_next_recommended_action(user_type: UserType) -> str:
        """Visszaadja a következő ajánlott műveletet a user típus alapján"""
        
        recommendations = {
            UserType.AWARE_SPENDER: "Hozz létre egy havi költési keretet a kezdéshez",
            UserType.COMMUNITY_DRIVEN: "Csatlakozz az első pénzügyi kihívásodhoz",
            UserType.LEARNER: "Kezdd el a 'Pénzügyi alapok' tananyagot",
            UserType.ADVANCED: "Importáld a bank tranzakcióidat",
            UserType.COMPETITIVE: "Nézd meg, hol állsz a ranglistán"
        }
        
        return recommendations.get(user_type, recommendations[UserType.DEFAULT])