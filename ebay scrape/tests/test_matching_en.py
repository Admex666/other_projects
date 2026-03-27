from matching_engine import MatchingEngine

def test_english_matches():
    engine = MatchingEngine()
    
    # English titles captured by the browser subagent
    test_cases = [
        {
            "ebay_title": "2019 TOPPS CHROME CHAMPIONS LEAGUE #74 ERLING HAALAND ROOKIE RC PSA 10",
            "card_data": {
                'player_name': 'Erling Haaland',
                'card_number': '74',
                'set_name': 'Topps Chrome UEFA Champions League',
                'year': '2019',
                'is_auto': False
            }
        },
        {
            "ebay_title": "2019 Topps Chrome UEFA Erling Haaland Rookie Refractor RC #74 Dortmund",
            "card_data": {
                'player_name': 'Erling Haaland',
                'card_number': '74',
                'set_name': 'Topps Chrome UEFA Champions League',
                'year': '2019',
                'is_auto': False
            }
        },
        {
            "ebay_title": "2019-20 Topps Chrome UCL Sapphire Edition - Erling Haaland #74 (RC) PSA 9!!!!",
            "card_data": {
                'player_name': 'Erling Haaland',
                'card_number': '74',
                'set_name': 'Topps Chrome UEFA Champions League',
                'year': '2019',
                'is_auto': False
            }
        }
    ]
    
    for case in test_cases:
        score, breakdown = engine.score_match(case["ebay_title"], case["card_data"])
        print(f"Title: {case['ebay_title']}")
        print(f"Score: {score:.4f}")
        print(f"Breakdown: {breakdown}")
        if score >= 0.85:
            print("RESULT: SUCCESS - Confidence Match")
        elif score >= 0.7:
            print("RESULT: PASS - Needs Review")
        else:
            print("RESULT: FAILURE")
        print("-" * 30)

if __name__ == "__main__":
    test_english_matches()
