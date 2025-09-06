# app/services/challenge_localization_service.py
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

class ChallengeLocalizationService:
    """Kihívások lokalizációs szolgáltatása"""
    
    def __init__(self):
        self._challenges_data = {}
        self._load_challenges()
    
    def _load_challenges(self):
        """Kihívások betöltése JSON fájlokból"""
        base_path = Path(__file__).parent.parent / "seeds"
        
        # challenges.json fájl betöltése
        challenges_file = base_path / "challenges.json"
        if challenges_file.exists():
            with open(challenges_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._challenges_data = data
    
    def get_challenge_by_code(self, challenge_code: str, lang: str = 'hu') -> Optional[Dict[str, Any]]:
        """Egy kihívás adatainak lekérése kód alapján"""
        if lang not in self._challenges_data:
            lang = 'hu'
        
        challenges = self._challenges_data.get(lang, {}).get('challenges', [])
        for challenge in challenges:
            if challenge.get('code') == challenge_code:
                return challenge
        return None
    
    def get_all_challenges(self, lang: str = 'hu') -> List[Dict[str, Any]]:
        """Összes kihívás lokalizált adatainak lekérése"""
        if lang not in self._challenges_data:
            lang = 'hu'
        
        return self._challenges_data.get(lang, {}).get('challenges', [])
    
    def get_challenges_by_type(self, challenge_type: str, lang: str = 'hu') -> List[Dict[str, Any]]:
        """Kihívások szűrése típus szerint"""
        all_challenges = self.get_all_challenges(lang)
        return [c for c in all_challenges if c.get('challenge_type') == challenge_type]
    
    def get_challenges_by_difficulty(self, difficulty: str, lang: str = 'hu') -> List[Dict[str, Any]]:
        """Kihívások szűrése nehézség szerint"""
        all_challenges = self.get_all_challenges(lang)
        return [c for c in all_challenges if c.get('difficulty') == difficulty]

challenge_localization_service = ChallengeLocalizationService()