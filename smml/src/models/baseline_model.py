import lightgbm as lgb
import pandas as pd
import numpy as np
import pickle
import os

class BaseModel:
    """
    Base class for engagement models.
    """
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None

    def save(self):
        if self.model:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)

    def load(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
        return self.model is not None

class BaselineModel(BaseModel):
    """
    Predicts expected engagement based on context features only.
    """
    def train(self, df: pd.DataFrame, features: list):
        # Target is log engagement
        y = np.log1p(df['actual_engagement'])
        X = df[features]
        
        self.model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.1)
        self.model.fit(X, y)
        self.save()

    def predict(self, df: pd.DataFrame, features: list) -> np.ndarray:
        if not self.model:
            self.load()
        return np.expm1(self.model.predict(df[features]))
