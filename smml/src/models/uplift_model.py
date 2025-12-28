import lightgbm as lgb
import pandas as pd
import numpy as np
from .baseline_model import BaseModel

class UpliftModel(BaseModel):
    """
    Predicts Engagement Lift using content features.
    """
    def train(self, df: pd.DataFrame, features: list):
        # Calculate Target: (actual - expected) / expected
        # Expected comes from baseline predictions during training (or cross-val)
        # For simplicity in MVP, we assume 'expected_engagement' is already in df
        df['lift'] = (df['actual_engagement'] - df['expected_engagement']) / (df['expected_engagement'] + 1)
        
        y = df['lift']
        X = df[features]
        
        self.model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05)
        self.model.fit(X, y)
        self.save()

    def predict(self, df: pd.DataFrame, features: list) -> np.ndarray:
        if not self.model:
            self.load()
        return self.model.predict(df[features])
