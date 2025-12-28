import shap
import pandas as pd
import matplotlib.pyplot as plt

class ExplainabilityEngine:
    """
    Provides SHAP-based explanations for model predictions.
    """
    def __init__(self, model):
        self.explainer = shap.Explainer(model)

    def get_feature_importance(self, X: pd.DataFrame):
        """
        Calculates SHAP values for the input features.
        """
        shap_values = self.explainer(X)
        return shap_values

    def plot_summary(self, X: pd.DataFrame, save_path: str = None):
        """
        Plots a summary of feature importance.
        """
        shap_values = self.get_feature_importance(X)
        plt.figure()
        shap.summary_plot(shap_values, X, show=False)
        if save_path:
            plt.savefig(save_path)
        plt.close()
