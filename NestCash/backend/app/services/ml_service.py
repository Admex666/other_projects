# app/services/ml_service.py
"""
Machine Learning szolgáltatások a pénzügyi elemzésekhez
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from scipy import stats
import logging

from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

class MLAnalysisService:
    """ML elemzési szolgáltatások"""
    
    @staticmethod
    def prepare_transaction_features(transactions: List[Transaction]) -> pd.DataFrame:
        """Tranzakciók előkészítése ML modellekhez"""
        features = []
        
        for t in transactions:
            try:
                date_obj = datetime.strptime(t.date, '%Y-%m-%d')
                
                feature_row = {
                    'transaction_id': str(t.id),
                    'amount': abs(t.amount),
                    'is_expense': t.amount < 0,
                    'hour': t.hour or 12,
                    'weekday': date_obj.weekday(),
                    'is_weekend': date_obj.weekday() >= 5,
                    'month': date_obj.month,
                    'day_of_month': date_obj.day,
                    'quarter': (date_obj.month - 1) // 3 + 1,
                    'category': t.kategoria or 'Egyéb',
                    'main_account': t.main_account,
                    'sub_account': t.sub_account_name,
                    'is_recurring': t.ismetlodo or False,
                    'is_fixed_cost': t.fix_koltseg or False,
                    'date': date_obj,
                    'year_month': date_obj.strftime('%Y-%m')
                }
                features.append(feature_row)
            except Exception as e:
                logger.warning(f"Error processing transaction {t.id}: {e}")
                continue
        
        return pd.DataFrame(features)
    
    @staticmethod
    def detect_spending_anomalies(transactions: List[Transaction], contamination: float = 0.1) -> Dict:
        """Kiadási anomáliák detektálása Isolation Forest algoritmussal"""
        if len(transactions) < 20:
            return {"anomalies": [], "model_confidence": 0.0}
        
        df = MLAnalysisService.prepare_transaction_features(transactions)
        expense_df = df[df['is_expense']].copy()
        
        if len(expense_df) < 10:
            return {"anomalies": [], "model_confidence": 0.0}
        
        # Feature engineering numerikus értékekhez
        features_for_model = []
        
        for _, row in expense_df.iterrows():
            features = [
                row['amount'],
                row['hour'],
                row['weekday'],
                int(row['is_weekend']),
                row['month'],
                row['day_of_month'],
                row['quarter'],
                hash(row['category']) % 1000,  # Category encoding
                hash(row['main_account']) % 100,
                int(row['is_recurring']),
                int(row['is_fixed_cost'])
            ]
            features_for_model.append(features)
        
        # Normalizálás
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_for_model)
        
        # Isolation Forest modell
        iso_forest = IsolationForest(
            n_estimators=100,
            contamination=float(contamination),
            random_state=42
        )
        
        anomaly_labels = iso_forest.fit_predict(features_scaled)
        anomaly_scores = iso_forest.score_samples(features_scaled)
        
        # Anomáliák összegyűjtése
        anomalies = []
        for i, (label, score) in enumerate(zip(anomaly_labels, anomaly_scores)):
            if label == -1:  # Anomália
                row = expense_df.iloc[i]
                anomalies.append({
                    'transaction_id': row['transaction_id'],
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'amount': row['amount'],
                    'category': row['category'],
                    'anomaly_score': float(score),
                    'severity': MLAnalysisService._calculate_anomaly_severity(score)
                })
        
        # Model confidence (egyszerűsített)
        model_confidence = min(1.0, len(expense_df) / 100) * 0.8 + 0.2
        
        return {
            "anomalies": sorted(anomalies, key=lambda x: x['anomaly_score']),
            "model_confidence": model_confidence,
            "total_transactions": len(expense_df),
            "anomaly_ratio": len(anomalies) / len(expense_df)
        }
    
    @staticmethod
    def _calculate_anomaly_severity(score: float) -> str:
        """Anomália súlyosságának meghatározása"""
        if score < -0.6:
            return "high"
        elif score < -0.4:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def generate_spending_forecast(transactions: List[Transaction], periods_ahead: int = 6, forecast_type: str = "monthly") -> Dict:
        """Költési előrejelzés készítése"""
        if len(transactions) < 30:
            return {"error": "Insufficient data for forecasting"}
        
        df = MLAnalysisService.prepare_transaction_features(transactions)
        expense_df = df[df['is_expense']].copy()
        
        # Időszak szerinti aggregálás
        if forecast_type == "monthly":
            time_col = 'year_month'
            freq = 'M'
        else:  # weekly
            expense_df['year_week'] = expense_df['date'].dt.strftime('%Y-W%U')
            time_col = 'year_week'
            freq = 'W'
        
        # Időszakonkénti összesítés
        time_series = expense_df.groupby(time_col)['amount'].sum().sort_index()
        
        if len(time_series) < 3:
            return {"error": "Insufficient time periods for forecasting"}
        
        try:
            # Exponential Smoothing modell
            if len(time_series) >= 8:
                model = ExponentialSmoothing(
                    time_series.values,
                    trend='add',
                    seasonal='add' if len(time_series) >= 12 else None,
                    seasonal_periods=12 if forecast_type == "monthly" else 52
                ).fit()
            else:
                model = ExponentialSmoothing(time_series.values, trend='add').fit()
            
            # Előrejelzés
            forecast_values = model.forecast(periods_ahead)
            
            # Konfidencia intervallumok (egyszerűsített)
            historical_std = np.std(time_series.values)
            confidence_intervals = [
                (max(0, val - 1.96 * historical_std), val + 1.96 * historical_std)
                for val in forecast_values
            ]
            
            # Model accuracy
            fitted_values = model.fittedvalues
            mae = np.mean(np.abs(time_series.values[1:] - fitted_values))
            accuracy = max(0, 100 - (mae / np.mean(time_series.values) * 100))
            
            # Trend meghatározása
            trend = MLAnalysisService._determine_trend(time_series.values)
            
            return {
                "forecasts": [float(f) for f in forecast_values],
                "confidence_intervals": confidence_intervals,
                "model_accuracy": accuracy,
                "trend": trend,
                "seasonal_detected": hasattr(model, 'seasonal') and model.seasonal is not None
            }
            
        except Exception as e:
            # Fallback: egyszerű trend extrapoláció
            logger.warning(f"Advanced forecasting failed, using simple trend: {e}")
            return MLAnalysisService._simple_trend_forecast(time_series.values, periods_ahead)
    
    @staticmethod
    def _determine_trend(values: np.ndarray) -> str:
        """Trend meghatározása"""
        if len(values) < 3:
            return "stable"
        
        recent = np.mean(values[-3:])
        older = np.mean(values[-6:-3]) if len(values) >= 6 else np.mean(values[:-3])
        
        if recent > older * 1.05:
            return "increasing"
        elif recent < older * 0.95:
            return "decreasing"
        else:
            return "stable"
    
    @staticmethod
    def _simple_trend_forecast(values: np.ndarray, periods: int) -> Dict:
        """Egyszerű trend alapú előrejelzés"""
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        
        forecasts = []
        for i in range(periods):
            forecast = slope * (len(values) + i) + intercept
            forecasts.append(max(0, forecast))  # Negatív előrejelzés elkerülése
        
        # Egyszerű konfidencia intervallum
        std_dev = np.std(values)
        confidence_intervals = [
            (max(0, f - 1.96 * std_dev), f + 1.96 * std_dev)
            for f in forecasts
        ]
        
        return {
            "forecasts": forecasts,
            "confidence_intervals": confidence_intervals,
            "model_accuracy": 70.0,  # Konzervatív becslés
            "trend": MLAnalysisService._determine_trend(values),
            "seasonal_detected": False
        }
    
    @staticmethod
    def analyze_seasonality(transactions: List[Transaction]) -> Dict:
        """Szezonalitás elemzése"""
        if len(transactions) < 100:
            return {"has_seasonality": False, "reason": "Insufficient data"}
        
        df = MLAnalysisService.prepare_transaction_features(transactions)
        expense_df = df[df['is_expense']].copy()
        
        # Havi aggregálás
        monthly_spending = expense_df.groupby('year_month')['amount'].sum().sort_index()
        
        if len(monthly_spending) < 12:
            return {"has_seasonality": False, "reason": "Less than 12 months of data"}
        
        try:
            # Szezonális dekompozíció
            decomposition = seasonal_decompose(monthly_spending.values, period=12, model='additive')
            seasonal_component = decomposition.seasonal
            
            # Szezonalitás erősségének mérése
            seasonal_strength = np.std(seasonal_component) / np.std(monthly_spending.values)
            has_seasonality = seasonal_strength > 0.15
            
            # Havi átlagok
            expense_df['month_only'] = expense_df['month']
            monthly_patterns = expense_df.groupby('month_only')['amount'].agg(['mean', 'std']).fillna(0)
            
            peak_months = []
            low_months = []
            overall_mean = monthly_patterns['mean'].mean()
            
            for month, row in monthly_patterns.iterrows():
                month_name = datetime(2000, month, 1).strftime('%B')
                if row['mean'] > overall_mean * 1.2:
                    peak_months.append(month_name)
                elif row['mean'] < overall_mean * 0.8:
                    low_months.append(month_name)
            
            return {
                "has_seasonality": has_seasonality,
                "seasonal_strength": float(seasonal_strength),
                "peak_months": peak_months,
                "low_months": low_months,
                "monthly_averages": {
                    datetime(2000, month, 1).strftime('%B'): float(row['mean'])
                    for month, row in monthly_patterns.iterrows()
                }
            }
            
        except Exception as e:
            logger.error(f"Seasonality analysis failed: {e}")
            return {"has_seasonality": False, "reason": f"Analysis error: {str(e)}"}
    
    @staticmethod
    def generate_category_budgets(transactions: List[Transaction]) -> Dict:
        """Kategóriánkénti költségvetési javaslatok ML alapon"""
        df = MLAnalysisService.prepare_transaction_features(transactions)
        expense_df = df[df['is_expense']].copy()
        
        if len(expense_df) < 20:
            return {"recommendations": [], "confidence": 0.0}
        
        # Kategóriánkénti elemzés
        category_analysis = {}
        
        for category in expense_df['category'].unique():
            cat_data = expense_df[expense_df['category'] == category]
            
            if len(cat_data) < 3:  # Túl kevés adat
                continue
            
            # Havi összesítés
            monthly_spending = cat_data.groupby('year_month')['amount'].sum()
            
            if len(monthly_spending) > 0:
                mean_spending = monthly_spending.mean()
                std_spending = monthly_spending.std()
                cv = std_spending / mean_spending if mean_spending > 0 else 1
                
                # Ajánlott budget számítás
                if cv < 0.3:  # Stabil
                    recommended_budget = mean_spending * 1.1
                    confidence = 0.9
                elif cv < 0.6:  # Közepes
                    recommended_budget = mean_spending * 1.25
                    confidence = 0.75
                else:  # Változékony
                    recommended_budget = mean_spending * 1.5
                    confidence = 0.6
                
                category_analysis[category] = {
                    "current_monthly_avg": float(mean_spending),
                    "recommended_budget": float(recommended_budget),
                    "confidence": float(confidence),
                    "variability": float(cv),
                    "transaction_count": len(cat_data)
                }
        
        return {
            "recommendations": category_analysis,
            "total_categories": len(category_analysis),
            "analysis_confidence": min(1.0, len(expense_df) / 100)
        }

class CollaborativeFilteringService:
    """Collaborative filtering szolgáltatás felhasználói összehasonlításhoz"""
    
    @staticmethod
    def find_similar_users(user_transactions: List[Transaction], all_users_data: Dict[str, List[Transaction]], top_k: int = 5) -> List[Dict]:
        """Hasonló felhasználók keresése collaborative filtering alapon"""
        
        # Felhasználói profil készítése
        user_profile = CollaborativeFilteringService._create_user_profile(user_transactions)
        
        similarities = []
        
        for other_user_id, other_transactions in all_users_data.items():
            if len(other_transactions) < 10:  # Túl kevés adat
                continue
            
            other_profile = CollaborativeFilteringService._create_user_profile(other_transactions)
            
            # Cosine similarity számítás
            similarity = CollaborativeFilteringService._calculate_similarity(user_profile, other_profile)
            
            if similarity > 0.3:  # Minimum similarity threshold
                similarities.append({
                    "user_id": other_user_id,
                    "similarity_score": similarity,
                    "profile": other_profile
                })
        
        # Top K hasonló felhasználó
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similarities[:top_k]
    
    @staticmethod
    def _create_user_profile(transactions: List[Transaction]) -> Dict:
        """Felhasználói profil készítése tranzakciók alapján"""
        df = MLAnalysisService.prepare_transaction_features(transactions)
        expense_df = df[df['is_expense']].copy()
        
        if len(expense_df) == 0:
            return {}
        
        profile = {
            "total_spending": expense_df['amount'].sum(),
            "avg_transaction": expense_df['amount'].mean(),
            "transaction_count": len(expense_df),
            "category_distribution": {},
            "weekday_pattern": {},
            "time_pattern": {},
            "account_usage": {}
        }
        
        # Kategória eloszlás
        total_amount = expense_df['amount'].sum()
        for category, group in expense_df.groupby('category'):
            profile["category_distribution"][category] = group['amount'].sum() / total_amount
        
        # Hét napja szerinti minta
        for weekday, group in expense_df.groupby('weekday'):
            profile["weekday_pattern"][str(weekday)] = group['amount'].sum() / total_amount
        
        # Óra szerinti minta (egyszerűsített)
        morning = expense_df[expense_df['hour'] < 12]['amount'].sum()
        afternoon = expense_df[(expense_df['hour'] >= 12) & (expense_df['hour'] < 18)]['amount'].sum()
        evening = expense_df[expense_df['hour'] >= 18]['amount'].sum()
        
        profile["time_pattern"] = {
            "morning": morning / total_amount,
            "afternoon": afternoon / total_amount,
            "evening": evening / total_amount
        }
        
        # Számla használat
        for account, group in expense_df.groupby('main_account'):
            profile["account_usage"][account] = group['amount'].sum() / total_amount
        
        return profile
    
    @staticmethod
    def _calculate_similarity(profile1: Dict, profile2: Dict) -> float:
        """Profilok közötti hasonlóság számítása"""
        if not profile1 or not profile2:
            return 0.0
        
        similarities = []
        
        # Kategória hasonlóság
        cat_sim = CollaborativeFilteringService._dict_cosine_similarity(
            profile1.get("category_distribution", {}),
            profile2.get("category_distribution", {})
        )
        similarities.append(cat_sim * 0.4)  # 40% súly
        
        # Időbeli minta hasonlóság
        time_sim = CollaborativeFilteringService._dict_cosine_similarity(
            profile1.get("time_pattern", {}),
            profile2.get("time_pattern", {})
        )
        similarities.append(time_sim * 0.3)  # 30% súly
        
        # Számla használat hasonlóság
        account_sim = CollaborativeFilteringService._dict_cosine_similarity(
            profile1.get("account_usage", {}),
            profile2.get("account_usage", {})
        )
        similarities.append(account_sim * 0.3)  # 30% súly
        
        return sum(similarities)
    
    @staticmethod
    def _dict_cosine_similarity(dict1: Dict, dict2: Dict) -> float:
        """Két dictionary közötti cosine similarity"""
        if not dict1 or not dict2:
            return 0.0
        
        # Közös kulcsok
        all_keys = set(dict1.keys()) | set(dict2.keys())
        
        vec1 = [dict1.get(key, 0) for key in all_keys]
        vec2 = [dict2.get(key, 0) for key in all_keys]
        
        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)