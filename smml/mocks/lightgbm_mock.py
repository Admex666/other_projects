import numpy as np

class LGBMRegressor:
    def __init__(self, **kwargs):
        self.params = kwargs
    def fit(self, X, y):
        pass
    def predict(self, X):
        return np.random.normal(0, 1, len(X))
