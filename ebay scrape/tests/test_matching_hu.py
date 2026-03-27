from matching_engine import MatchingEngine

def test_hungarian_match():
    engine = MatchingEngine()
    
    # Sample from our recent scraper run
    ebay_title = "ERLING HAALAND PSA 10 2019 TOPPS KRÓM UCL #74 ÚJONC RC"
    
    card_data = {
        'player_name': 'Erling Haaland',
        'card_number': '74',
        'set_name': 'Topps Chrome UEFA Champions League',
        'year': '2019',
        'is_auto': False
    }
    
    score, breakdown = engine.score_match(ebay_title, card_data)
    print(f"Title: {ebay_title}")
    print(f"Score: {score:.4f}")
    print(f"Breakdown: {breakdown}")
    
    if score >= 0.85:
        print("SUCCESS: Match identified correctly!")
    else:
        print("FAILURE: Score too low.")

if __name__ == "__main__":
    test_hungarian_match()
