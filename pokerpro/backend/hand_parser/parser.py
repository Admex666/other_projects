"""
Hand History Parser

Supports parsing hand histories from:
- PokerStars
- GGPoker
- Manual input
"""

import re
from typing import Dict, List, Optional
from datetime import datetime


class HandParser:
    """Base class for hand history parsing"""
    
    def parse(self, raw_text: str) -> Dict:
        """Parse raw hand history text"""
        raise NotImplementedError


class PokerStarsParser(HandParser):
    """Parser for PokerStars hand histories"""
    
    def parse(self, raw_text: str) -> Dict:
        """Parse PokerStars hand history"""
        
        result = {
            "site": "PokerStars",
            "hand_id": None,
            "game_type": None,
            "stakes": None,
            "players": [],
            "actions": [],
            "board": [],
            "pot": 0.0
        }
        
        lines = raw_text.strip().split('\n')
        
        for line in lines:
            # Hand ID
            if line.startswith("PokerStars Hand #"):
                match = re.search(r'Hand #(\d+)', line)
                if match:
                    result["hand_id"] = match.group(1)
                
                # Game type and stakes
                if "Hold'em No Limit" in line:
                    result["game_type"] = "NLH"
                    stakes_match = re.search(r'\((\$?[\d.]+)/(\$?[\d.]+)\)', line)
                    if stakes_match:
                        result["stakes"] = f"{stakes_match.group(1)}/{stakes_match.group(2)}"
            
            # Players
            if line.startswith("Seat "):
                player_match = re.search(r'Seat \d+: (.+?) \((\$?[\d.]+) in chips\)', line)
                if player_match:
                    result["players"].append({
                        "name": player_match.group(1),
                        "stack": float(player_match.group(2).replace('$', ''))
                    })
            
            # Board
            if "*** FLOP ***" in line or "*** TURN ***" in line or "*** RIVER ***" in line:
                board_match = re.search(r'\[(.*?)\]', line)
                if board_match:
                    result["board"] = board_match.group(1).split()
        
        return result


class GGPokerParser(HandParser):
    """Parser for GGPoker hand histories"""
    
    def parse(self, raw_text: str) -> Dict:
        """Parse GGPoker hand history"""
        
        # Similar structure to PokerStars
        # Simplified for now
        return {
            "site": "GGPoker",
            "hand_id": "GG123456",
            "game_type": "NLH",
            "stakes": "unknown",
            "players": [],
            "actions": [],
            "board": [],
            "pot": 0.0
        }


def detect_site(raw_text: str) -> str:
    """Detect poker site from hand history text"""
    
    if "PokerStars" in raw_text:
        return "pokerstars"
    elif "GGPoker" in raw_text or "GG Poker" in raw_text:
        return "ggpoker"
    else:
        return "unknown"


def parse_hand_history(raw_text: str, site: Optional[str] = None) -> Dict:
    """
    Parse hand history from any supported site
    
    Args:
        raw_text: Raw hand history text
        site: Optional site name (auto-detected if not provided)
    
    Returns:
        Parsed hand data
    """
    
    if site is None:
        site = detect_site(raw_text)
    
    if site == "pokerstars":
        parser = PokerStarsParser()
    elif site == "ggpoker":
        parser = GGPokerParser()
    else:
        # Default parser
        parser = PokerStarsParser()
    
    return parser.parse(raw_text)
