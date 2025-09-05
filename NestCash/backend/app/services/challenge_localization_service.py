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
        base_path = Path(__file__).parent.parent / "seeds" / "challenges"
        
        # Alapértelmezett nyelv (magyar)
        hu_file = base_path / "challenges.json"
        if hu_file.exists():
            with open(hu_file, 'r', encoding='utf-8') as f:
                self._challenges_data['hu'] = json.load(f)['hu']
        
        # Angol
        en_file = base_path / "challenges.json"
        if en_file.exists():
            with open(en_file, 'r', encoding='utf-8') as f:
                self._challenges_data['en'] = json.load(f)['en']
    
    def get_challenge_data(self, challenge_code: str, lang: str = 'hu') -> Optional[Dict[str, Any]]:
        """Egy kihívás lokalizált adatainak lekérése"""
        if lang not in self._challenges_data:
            lang = 'hu'  # Fallback magyar nyelvre
        
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
    
    def get_available_languages(self) -> List[str]:
        """Elérhető nyelvek listája"""
        return list(self._challenges_data.keys())

challenge_localization_service = ChallengeLocalizationService()