"""
Preflop GTO Ranges for No-Limit Hold'em

This module contains preflop ranges for various positions and actions.
Ranges are based on GTO solutions and represent frequencies (0-1).
"""

from typing import Dict

# Hand rankings for easy lookup
HAND_RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']


def get_rfi_range(position: str, stack_depth: int = 100) -> Dict[str, float]:
    """
    Get Raise First In (RFI) ranges by position
    
    Args:
        position: BTN, CO, MP, EP, SB
        stack_depth: Stack depth in BB (default 100)
    
    Returns:
        Dictionary of hand -> frequency
    """
    
    ranges = {
        "BTN": {
            # Premium pairs
            "AA": 1.0, "KK": 1.0, "QQ": 1.0, "JJ": 1.0, "TT": 1.0,
            "99": 1.0, "88": 1.0, "77": 1.0, "66": 1.0, "55": 1.0,
            "44": 1.0, "33": 1.0, "22": 1.0,
            
            # Suited broadway
            "AKs": 1.0, "AQs": 1.0, "AJs": 1.0, "ATs": 1.0,
            "KQs": 1.0, "KJs": 1.0, "KTs": 1.0,
            "QJs": 1.0, "QTs": 1.0, "JTs": 1.0,
            
            # Offsuit broadway
            "AKo": 1.0, "AQo": 1.0, "AJo": 1.0, "ATo": 1.0,
            "KQo": 1.0, "KJo": 1.0, "KTo": 0.8,
            "QJo": 1.0, "QTo": 0.7, "JTo": 0.6,
            
            # Suited connectors and gappers
            "T9s": 1.0, "98s": 1.0, "87s": 1.0, "76s": 1.0, "65s": 1.0,
            "54s": 1.0, "T8s": 0.8, "97s": 0.8, "86s": 0.7, "75s": 0.7,
            
            # Suited Ax
            "A9s": 1.0, "A8s": 1.0, "A7s": 1.0, "A6s": 1.0,
            "A5s": 1.0, "A4s": 1.0, "A3s": 1.0, "A2s": 1.0,
            
            # More offsuit
            "A9o": 0.7, "A8o": 0.5, "A7o": 0.4,
            "K9o": 0.6, "Q9o": 0.5, "J9o": 0.4,
        },
        
        "CO": {
            # Tighter than BTN
            "AA": 1.0, "KK": 1.0, "QQ": 1.0, "JJ": 1.0, "TT": 1.0,
            "99": 1.0, "88": 1.0, "77": 1.0, "66": 1.0, "55": 1.0,
            "44": 0.9, "33": 0.8, "22": 0.8,
            
            "AKs": 1.0, "AQs": 1.0, "AJs": 1.0, "ATs": 1.0, "A9s": 1.0,
            "KQs": 1.0, "KJs": 1.0, "KTs": 1.0, "K9s": 0.7,
            "QJs": 1.0, "QTs": 1.0, "JTs": 1.0, "T9s": 1.0,
            
            "AKo": 1.0, "AQo": 1.0, "AJo": 1.0, "ATo": 1.0,
            "KQo": 1.0, "KJo": 0.9, "QJo": 0.8,
            
            "A5s": 1.0, "A4s": 1.0, "A3s": 1.0, "A2s": 1.0,
            "98s": 1.0, "87s": 1.0, "76s": 1.0, "65s": 0.9,
        },
        
        "MP": {
            # Tighter range
            "AA": 1.0, "KK": 1.0, "QQ": 1.0, "JJ": 1.0, "TT": 1.0,
            "99": 1.0, "88": 1.0, "77": 0.9, "66": 0.8, "55": 0.7,
            
            "AKs": 1.0, "AQs": 1.0, "AJs": 1.0, "ATs": 1.0,
            "KQs": 1.0, "KJs": 1.0, "KTs": 0.9,
            "QJs": 1.0, "QTs": 0.9, "JTs": 0.9,
            
            "AKo": 1.0, "AQo": 1.0, "AJo": 1.0, "ATo": 0.9,
            "KQo": 1.0, "KJo": 0.7,
            
            "A5s": 0.8, "A4s": 0.8, "A3s": 0.7, "A2s": 0.7,
        },
        
        "EP": {
            # Tight range
            "AA": 1.0, "KK": 1.0, "QQ": 1.0, "JJ": 1.0, "TT": 1.0,
            "99": 1.0, "88": 0.8, "77": 0.6,
            
            "AKs": 1.0, "AQs": 1.0, "AJs": 1.0, "ATs": 0.9,
            "KQs": 1.0, "KJs": 0.9, "QJs": 0.8, "JTs": 0.7,
            
            "AKo": 1.0, "AQo": 1.0, "AJo": 0.9,
            "KQo": 0.8,
        },
        
        "SB": {
            # Similar to BTN but slightly tighter
            "AA": 1.0, "KK": 1.0, "QQ": 1.0, "JJ": 1.0, "TT": 1.0,
            "99": 1.0, "88": 1.0, "77": 1.0, "66": 0.9, "55": 0.9,
            
            "AKs": 1.0, "AQs": 1.0, "AJs": 1.0, "ATs": 1.0,
            "KQs": 1.0, "KJs": 1.0, "KTs": 0.9,
            "QJs": 1.0, "QTs": 0.9, "JTs": 0.9,
            
            "AKo": 1.0, "AQo": 1.0, "AJo": 1.0, "ATo": 0.9,
            "KQo": 1.0, "KJo": 0.8,
        }
    }
    
    return ranges.get(position, {})


def get_3bet_range(position: str, vs_position: str) -> Dict[str, float]:
    """
    Get 3-bet ranges
    
    Args:
        position: Our position (BTN, CO, etc.)
        vs_position: Opponent's position
    
    Returns:
        Dictionary of hand -> frequency
    """
    
    # Simplified 3-bet range (vs CO open from BTN)
    if position == "BTN" and vs_position == "CO":
        return {
            "AA": 1.0, "KK": 1.0, "QQ": 1.0, "JJ": 0.9, "TT": 0.7,
            "AKs": 1.0, "AQs": 1.0, "AJs": 0.8, "ATs": 0.5,
            "AKo": 1.0, "AQo": 0.8,
            "KQs": 0.7, "KJs": 0.5,
            "A5s": 0.6, "A4s": 0.6, "A3s": 0.5, "A2s": 0.5,  # Bluffs
        }
    
    # Default tight 3-bet range
    return {
        "AA": 1.0, "KK": 1.0, "QQ": 1.0, "JJ": 1.0,
        "AKs": 1.0, "AKo": 1.0,
    }


def get_defend_range(position: str, vs_position: str) -> Dict[str, float]:
    """
    Get Defend (Call/3bet) ranges
    
    Args:
        position: Our position (e.g. BB)
        vs_position: Opener's position (e.g. BTN)
    """
    if position == "BB" and vs_position == "BTN":
        # Wide defense range
        return {
            # Pairs
            "AA": 1.0, "KK": 1.0, "QQ": 1.0, "JJ": 1.0, "TT": 1.0, "99": 1.0, "88": 1.0,
            "77": 1.0, "66": 1.0, "55": 1.0, "44": 1.0, "33": 0.8, "22": 0.5,
            # Suited
            "AKs": 1.0, "AQs": 1.0, "AJs": 1.0, "ATs": 1.0, "A9s": 1.0, "A8s": 1.0,
            "A7s": 0.8, "A6s": 0.6, "A5s": 0.8, "A4s": 0.7, "A3s": 0.6, "A2s": 0.5,
            "KQs": 1.0, "KJs": 1.0, "KTs": 1.0, "K9s": 0.8, "K8s": 0.6,
            "QJs": 1.0, "QTs": 1.0, "Q9s": 0.8, "Q8s": 0.5,
            "JTs": 1.0, "J9s": 0.8, "J8s": 0.6,
            "T9s": 1.0, "T8s": 0.8, "98s": 1.0, "87s": 1.0, "76s": 1.0, "65s": 1.0,
            # Offsuit
            "AKo": 1.0, "AQo": 1.0, "AJo": 1.0, "ATo": 1.0, "A9o": 0.8, "A8o": 0.5,
            "KQo": 1.0, "KJo": 1.0, "KTo": 0.8, "K9o": 0.5,
            "QJo": 1.0, "QTo": 0.8, "Q9o": 0.5,
            "JTo": 0.9, "J9o": 0.6, 
            "T9o": 0.8, "98o": 0.6
        }
    
    return get_rfi_range("BTN") # Fallback to a wide range


def calculate_vpip(range_dict: Dict[str, float]) -> float:
    """Calculate VPIP percentage from range"""
    
    # Total combinations in poker: 1326
    # Pairs: 6 combos each
    # Suited: 4 combos each
    # Offsuit: 12 combos each
    
    total_combos = 0
    
    for hand, freq in range_dict.items():
        if len(hand) == 2:  # Pair
            combos = 6
        elif hand.endswith('s'):  # Suited
            combos = 4
        else:  # Offsuit
            combos = 12
        
        total_combos += combos * freq
    
    return (total_combos / 1326) * 100


def visualize_range(range_dict: Dict[str, float]) -> Dict[str, float]:
    """
    Convert range to full 13x13 grid for visualization
    
    Returns:
        Dictionary with all 169 hand combinations
    """
    
    grid = {}
    
    for i, rank1 in enumerate(HAND_RANKS):
        for j, rank2 in enumerate(HAND_RANKS):
            if i == j:  # Pair
                hand = f"{rank1}{rank2}"
                grid[hand] = range_dict.get(hand, 0.0)
            elif i < j:  # Suited (upper triangle)
                hand = f"{rank1}{rank2}s"
                grid[hand] = range_dict.get(hand, 0.0)
            else:  # Offsuit (lower triangle)
                hand = f"{rank2}{rank1}o"
                grid[hand] = range_dict.get(hand, 0.0)
    
    return grid
