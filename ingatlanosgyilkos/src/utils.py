"""
Utility functions for the Budapest rental analysis project.
"""

import pandas as pd
import numpy as np
import re
from typing import Optional


def extract_number(text: str) -> Optional[float]:
    """
    Extract numeric value from text string.
    
    Args:
        text: String containing numbers
        
    Returns:
        Extracted float value or None
    """
    if not text or pd.isna(text):
        return None
    text = str(text).replace("\xa0", "").replace(".", "").replace(" ", "")
    match = re.search(r'(\d+,?\d*)', text)
    return float(match.group(1).replace(",", ".")) if match else None


def extract_district(location: str) -> Optional[int]:
    """
    Extract Budapest district number from location string.
    
    Args:
        location: Location string (e.g., "Budapest V. kerület")
        
    Returns:
        District number (1-23) or None
    """
    if pd.isna(location) or 'kerület' not in str(location):
        return None
    
    try:
        roman_nums = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
            'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13,
            'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18,
            'XIX': 19, 'XX': 20, 'XXI': 21, 'XXII': 22, 'XXIII': 23
        }
        
        location_clean = str(location).replace('.', '').strip()
        for roman, num in roman_nums.items():
            if roman in location_clean:
                return num
        return None
    except:
        return None


def parse_floor(floor_str: str) -> float:
    """
    Parse floor string to numeric value.
    
    Args:
        floor_str: Floor description (e.g., "2. emelet", "földszint")
        
    Returns:
        Numeric floor value
    """
    if pd.isna(floor_str):
        return 0
    
    floor_str = str(floor_str).lower()
    
    if 'földszint' in floor_str:
        return 0
    if 'félemelet' in floor_str:
        return 0.5
    if 'szint' in floor_str:
        return 0
    
    match = re.search(r'(\d+)', floor_str)
    return int(match.group(1)) if match else 0


def parse_area(area_str: str) -> float:
    """
    Parse area string to numeric value in m².
    
    Args:
        area_str: Area description (e.g., "10 m²")
        
    Returns:
        Numeric area value
    """
    if pd.isna(area_str):
        return 0.0
    
    try:
        clean_str = re.sub(r'[^\d,\.]', '', str(area_str)).replace(',', '.')
        return float(clean_str)
    except (ValueError, TypeError):
        return 0.0
