import numpy as np

class Explainer:
    def __init__(self, model):
        self.model = model
    def __call__(self, X):
        return np.random.normal(0, 1, X.shape)

def summary_plot(shap_values, X, show=False):
    pass
