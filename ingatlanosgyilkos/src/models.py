"""
Machine learning models and optimization for rental price prediction.

This module provides classes for training, evaluating, and optimizing
ML models for real estate price prediction.
"""

from typing import Dict, List, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from lightgbm import LGBMRegressor
from sklearn.ensemble import (ExtraTreesRegressor, GradientBoostingRegressor,
                               RandomForestRegressor)
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, cross_val_score
from xgboost import XGBRegressor


class ModelOptimizer:
    """Optimizer for training and evaluating multiple regression models."""
    
    def __init__(self):
        """Initialize model optimizer."""
        self.models = {}
        self.best_model = None
        self.best_score = float('inf')
    
    def get_optimized_models(self) -> Dict:
        """
        Get dictionary of optimized model configurations.
        
        Returns:
            Dictionary mapping model names to model instances
        """
        return {
            "Random Forest": RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            
            "XGBoost": XGBRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            ),
            
            "LightGBM": LGBMRegressor(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            ),
            
            "Extra Trees": ExtraTreesRegressor(
                n_estimators=200,
                max_depth=12,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            
            "Gradient Boosting": GradientBoostingRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            ),
            
            "Ridge": Ridge(alpha=1.0),
            "ElasticNet": ElasticNet(alpha=1.0, l1_ratio=0.5, random_state=42)
        }
    
    def hyperparameter_tuning(self, model, param_grid, X_train, y_train):
        """
        Perform hyperparameter tuning with GridSearchCV.
        
        Args:
            model: Model instance
            param_grid: Parameter grid for search
            X_train: Training features
            y_train: Training target
            
        Returns:
            Tuple of (best_estimator, best_score)
        """
        grid_search = GridSearchCV(
            model, param_grid, cv=5, 
            scoring='neg_mean_squared_error', 
            n_jobs=-1, verbose=1
        )
        grid_search.fit(X_train, y_train)
        return grid_search.best_estimator_, grid_search.best_score_
    
    def evaluate_models(self, X_train, X_test, y_train, y_test) -> Dict:
        """
        Evaluate all models with cross-validation.
        
        Args:
            X_train: Training features
            X_test: Test features
            y_train: Training target
            y_test: Test target
            
        Returns:
            Dictionary with evaluation results for each model
        """
        models = self.get_optimized_models()
        results = {}
        
        print("🚀 Testing models...")
        print(f"🎯 Target: price_per_m2 (Ft/m²/month)")
        
        avg_price_per_m2 = y_train.mean()
        print(f"📊 Average price_per_m2: {avg_price_per_m2:.2f} Ft/m²/month")
        
        for name, model in models.items():
            print(f"\n📈 Testing {name}...")
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, 
                                        scoring='neg_mean_squared_error', n_jobs=-1)
            cv_rmse = np.sqrt(-cv_scores)
            
            # Train model
            model.fit(X_train, y_train)
            
            # Predictions
            y_pred = model.predict(X_test)
            
            # Metrics
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Relative error
            relative_error = (rmse / avg_price_per_m2) * 100
            
            results[name] = {
                'CV_RMSE_mean': cv_rmse.mean(),
                'CV_RMSE_std': cv_rmse.std(),
                'Test_RMSE': rmse,
                'Test_MAE': mae,
                'R2_Score': r2,
                'Relative_Error_%': relative_error,
                'Model': model,
                'Predictions': y_pred
            }
            
            if rmse < self.best_score:
                self.best_score = rmse
                self.best_model = (name, model)
            
            print(f"  R² score: {r2:.4f}")
            print(f"  CV RMSE: {cv_rmse.mean():.3f} ± {cv_rmse.std():.3f}")
            print(f"  Test RMSE: {rmse:.3f} Ft/m²/month")
            print(f"  Relative error: {relative_error:.1f}%")
            print(f"  Test MAE: {mae:.3f} Ft/m²/month")
        
        return results
    
    def plot_results(self, results: Dict, feature_names: List[str]) -> pd.DataFrame:
        """
        Visualize model results.
        
        Args:
            results: Results dictionary from evaluate_models
            feature_names: List of feature names
            
        Returns:
            DataFrame with sorted results
        """
        # Model comparison
        results_df = pd.DataFrame({k: v for k, v in results.items() 
                                  if k not in ['Model', 'Predictions', 'y_test']}).T
        results_df = results_df.sort_values('Test_RMSE')
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # RMSE comparison
        sns.barplot(data=results_df.reset_index(), x='index', y='Test_RMSE', ax=axes[0,0])
        axes[0,0].set_title('Model RMSE Comparison')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # R² comparison
        sns.barplot(data=results_df.reset_index(), x='index', y='R2_Score', ax=axes[0,1])
        axes[0,1].set_title('Model R² Comparison')
        axes[0,1].tick_params(axis='x', rotation=45)
        
        # Feature importance (best model)
        best_model_name = results_df.index[0]
        best_model = results[best_model_name]['Model']
        
        if hasattr(best_model, 'feature_importances_'):
            importance = pd.Series(best_model.feature_importances_, index=feature_names)
            top_features = importance.sort_values(ascending=False).head(15)
            
            sns.barplot(x=top_features.values, y=top_features.index, ax=axes[1,0])
            axes[1,0].set_title(f'Top 15 Features - {best_model_name}')
            axes[1,0].set_xlabel('Importance')
        
        # Actual vs Predicted
        y_test_actual = results['y_test']
        y_pred = results[best_model_name]['Predictions']
        sns.scatterplot(x=y_test_actual, y=y_pred, ax=axes[1,1], alpha=0.6)
        axes[1,1].plot([y_test_actual.min(), y_test_actual.max()], 
                      [y_test_actual.min(), y_test_actual.max()], 'k--')
        axes[1,1].set_xlabel('Actual Price/m²')
        axes[1,1].set_ylabel('Predicted Price/m²')
        axes[1,1].set_title(f'Actual vs Predicted - {best_model_name}')
        
        plt.tight_layout()
        plt.savefig('models/model_evaluation.png', dpi=300, bbox_inches='tight')
        print("\n📊 Plot saved to models/model_evaluation.png")
        
        return results_df
    
    def save_best_model(self, preprocessor, num_features: List[str], cat_features: List[str], 
                       output_dir: str = "models"):
        """
        Save the best model and preprocessor.
        
        Args:
            preprocessor: Fitted preprocessor
            num_features: List of numerical feature names
            cat_features: List of categorical feature names
            output_dir: Output directory
        """
        if self.best_model is None:
            print("❌ No model has been trained yet!")
            return
        
        best_name, best_model_instance = self.best_model
        
        joblib.dump(best_model_instance, f'{output_dir}/best_rental_price_model.pkl')
        joblib.dump(preprocessor, f'{output_dir}/preprocessor.pkl')
        joblib.dump((num_features, cat_features), f'{output_dir}/feature_columns.pkl')
        
        print(f"\n💾 Model saved: {best_name}")
        print(f"   RMSE: {self.best_score:.3f} Ft/m²/month")


def interpret_rmse(rmse_value: float, avg_price_per_m2: float):
    """
    Interpret RMSE value for price_per_m2 prediction.
    
    Args:
        rmse_value: RMSE value
        avg_price_per_m2: Average price per m²
    """
    relative_error = (rmse_value / avg_price_per_m2) * 100
    
    print(f"\n📊 RMSE INTERPRETATION:")
    print(f"• Absolute RMSE: {rmse_value:.2f} Ft/m²/month")
    print(f"• Average price: {avg_price_per_m2:.2f} Ft/m²/month")
    print(f"• Relative error: {relative_error:.1f}%")
    
    if relative_error < 10:
        print("✅ Excellent model - practically usable")
    elif relative_error < 20:
        print("✅ Good model - acceptable accuracy")
    elif relative_error < 30:
        print("⚠️  Average model - shows trends")
    else:
        print("❌ Weak model - too much noise")
    
    print(f"\n🏢 Practical example:")
    print(f"For a 60 m² apartment, this means average {rmse_value * 60:.0f} Ft/month estimation error")
