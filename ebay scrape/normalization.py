import re
import unicodedata
from typing import List, Set, Optional

# List of stopwords to remove from titles (card specific + general)
STOPWORDS = {
    "psa", "graded", "mint", "auto", "patch", "rc", "rookie", "card", "ebay", 
    "investment", "sneaky", "invest", "rare", "look", "l@@k", "authentic",
    "the", "a", "an", "and", "or", "to", "for", "with", "in", "on", "at"
}

def remove_accents(input_str: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def normalize_text(text: str) -> List[str]:
    """
    Normalizes text by:
    1. Lowercasing
    2. Removing accents
    3. Removing special characters (except # for numbers)
    4. Tokenizing
    5. Removing stopwords
    """
    if not text:
        return []
        
    text = text.lower()
    text = remove_accents(text)
    
    # Remove special characters but keep alphanumeric and #, / (often used in card numbers or dates)
    text = re.sub(r'[^a-z0-9#/ ]+', ' ', text)
    
    tokens = text.split()
    
    clean_tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    
    return clean_tokens

def extract_year(text: str) -> Optional[int]:
    """Extracts a 4-digit year starting with 19 or 20."""
    match = re.search(r'\b(19|20)\d{2}\b', text)
    if match:
        return int(match.group(0))
    return None

def extract_card_number(text: str) -> Optional[str]:
    """Extracts card number (e.g., #50, #RC1, 123)."""
    # 1. Look for # prefix
    match = re.search(r'#([a-z0-9\-]+)', text.lower())
    if match:
        return match.group(1)
        
    # 2. Look for standalone digits that aren't years
    # Usually at the end of a title or after a set name
    potential_nums = re.findall(r'\b([0-9]{1,3}[a-z]?)\b', text.lower())
    for num in potential_nums:
        if not (num.isdigit() and 1900 <= int(num) <= 2030):
            return num
            
    return None
