try:
    import mocks
except ImportError:
    pass

import argparse
import pandas as pd
import numpy as np
from src.scraper.instagram_scraper import InstagramScraper
from src.features.featurizer import Featurizer
from src.models.baseline_model import BaselineModel
from src.models.uplift_model import UpliftModel

def run_pipeline(username: str, limit: int):
    print(f"--- Starting pipeline for user: {username} ---")
    
    # 1. Scrape
    scraper = InstagramScraper()
    profile = scraper.get_profile_info(username)
    if not profile:
        print("Failed to fetch profile. Exiting.")
        return
        
    posts = scraper.get_posts(username, count=limit)
    print(f"Scraped {len(posts)} posts for {username}")

    if not posts:
        print("No posts found or access denied.")
        return

    # 2. Featurize
    featurizer = Featurizer()
    df = featurizer.process_all_posts(posts, profile)
    print(f"Features extracted. Shape: {df.shape}")

    # 3. Predict / Infer
    baseline = BaselineModel("models/baseline.pkl")
    uplift = UpliftModel("models/uplift.pkl")
    
    # Mock models if not trained (for demonstration)
    if not baseline.load():
        print("Warning: Baseline model not found. Using random values for demo.")
        df['expected_engagement'] = df['follower_count_log'] * 10 + np.random.normal(0, 1, len(df))
    else:
        df['expected_engagement'] = baseline.predict(df, ['follower_count_log', 'hour_of_day', 'day_of_week'])

    if not uplift.load():
        print("Warning: Uplift model not found. Using random values for demo.")
        df['predicted_lift'] = np.random.uniform(-0.5, 0.5, len(df))
    else:
        # Use a subset of features for content-aware prediction
        content_features = ['caption_length', 'hashtag_count', 'emoji_count', 'is_question', 'brightness', 'contrast']
        df['predicted_lift'] = uplift.predict(df, content_features)

    # 4. Final Score
    df['final_score'] = df['predicted_lift'] * 100 # Lift as percentage
    
    # 5. Output Results
    print("\n--- Prediction Results (Top 5 Posts) ---")
    results = df[['post_id', 'expected_engagement', 'actual_engagement', 'predicted_lift']]
    print(results.head())
    
    # Save to CSV
    df.to_csv(f"data/processed/{username}_predictions.csv", index=False)
    print(f"\nResults saved to data/processed/{username}_predictions.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Engagement Prediction Pipeline")
    parser.add_argument("--username", type=str, required=True, help="Username to analyze")
    parser.add_argument("--limit", type=int, default=10, help="Max posts to scrape")
    args = parser.parse_args()
    
    run_pipeline(args.username, args.limit)
