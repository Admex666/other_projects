try:
    import mocks
except ImportError:
    pass

import pandas as pd
import numpy as np
import os
from src.scraper.instagram_scraper import MockInstagramScraper
from src.features.featurizer import Featurizer
from src.models.baseline_model import BaselineModel
from src.models.uplift_model import UpliftModel

def verify_and_train():
    print("--- Verification & Training Step ---")
    os.makedirs("models", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    # 1. Generate Training Data
    scraper = MockInstagramScraper()
    profile = scraper.get_profile_info("training_user")
    posts = scraper.get_posts("training_user", count=100)
    
    featurizer = Featurizer()
    df = featurizer.process_all_posts(posts, profile)
    
    # 2. Train Baseline
    print("Training Baseline Model...")
    baseline = BaselineModel("models/baseline.pkl")
    ctx_features = ['follower_count_log', 'hour_of_day', 'day_of_week']
    baseline.train(df, ctx_features)
    
    # Get baseline predictions to train uplift
    df['expected_engagement'] = baseline.predict(df, ctx_features)
    
    # 3. Train Uplift
    print("Training Uplift Model...")
    uplift = UpliftModel("models/uplift.pkl")
    content_features = ['caption_length', 'hashtag_count', 'emoji_count', 'is_question', 'brightness', 'contrast']
    uplift.train(df, content_features)
    
    print("\nVerification: Success. Models saved in models/")

if __name__ == "__main__":
    verify_and_train()
