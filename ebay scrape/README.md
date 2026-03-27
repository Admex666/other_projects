# Football Card Price Prediction Pipeline

This project modernizes the football card price analysis pipeline by using SofaScore as a data source and implementing a weighted fuzzy-matching engine for accurate card identification.

## 📁 Project Structure

- **`sofascore_client.py`**: Interface for fetching player performance stats and market value baselines from SofaScore.
- **`ebay_scraper.py`**: Scraper for eBay sold items. (Transitioning to browser-based engine for reliable English data).
- **`matching_engine.py`**: The core logic for identifying cards using a weighted token-based approach.
- **`normalization.py`**: Text processing utilities (lowercasing, accent removal, regex extraction).
- **`aliases.py`**: Dictionary of card sets, players, and Hungarian-to-English translations.
- **`tests/`**: Contains verification scripts for both English and Hungarian locales.
- **`debug/`**: HTML snapshots for troubleshooting selector changes.
- **`archive/`**: Legacy scripts and data files.

## 🧠 Matching Engine Logic

The engine uses a tiered, weighted scoring system (Confidence threshold: **0.85**):

1. **Hard Filter**: Year and Player Name check.
2. **Weighted Tokens**:
   - **Player Match**: 40% (Ner/Dict)
   - **Card Number**: 30% (Regex match)
   - **Set Match**: 15% (Jaccard similarity)
   - **Year Match**: 10%
   - **Attributes (Auto/Patch)**: 5%
3. **Boost**: If both Player and Card Number match perfectly, the score is boosted to 0.95+.

## ⚙️ Requirements

- `tls_client`
- `beautifulsoup4`
- `rapidfuzz`
- `pandas`
- `asyncio`

---
*Created with ⚽ for Card Market Analytics*
