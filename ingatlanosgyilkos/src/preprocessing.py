"""
Advanced real estate data preprocessing and feature engineering.

This module provides classes for cleaning rental listing data
and creating advanced features for ML models.
"""

import re
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class AdvancedRealEstatePreprocessor:
    """Advanced preprocessor for real estate data with feature engineering."""
    
    def __init__(self, district_prices_path: str):
        """
        Initialize preprocessor.
        
        Args:
            district_prices_path: Path to CSV with district average prices
        """
        self.district_prices = pd.read_csv(district_prices_path, sep=';')
        self.preprocessor = None
        self.feature_names =None
    
    def create_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create advanced features from base data.
        
        Args:
            df: DataFrame with base features
            
        Returns:
            DataFrame with additional engineered features
        """
        df = df.copy()
        
        # === BASIC FEATURES ===
        
        # 1. Square meters per room
        if 'area_m2' in df.columns and 'rooms' in df.columns:
            df['m2_per_room'] = df['area_m2'] / df['rooms'].replace(0, np.nan)
        else:
            df['m2_per_room'] = np.nan
        
        # 2. Balcony/Terrace boolean flags
        def parse_area(area_str):
            if pd.isna(area_str):
                return 0.0
            try:
                clean_str = re.sub(r'[^\d,\.]', '', str(area_str)).replace(',', '.')
                return float(clean_str)
            except (ValueError, TypeError):
                return 0.0
        
        if 'Erkély' in df.columns:
            df['balcony_area'] = df['Erkély'].apply(parse_area)
            df['has_balcony'] = (df['balcony_area'] > 0).astype(int)
        else:
            df['balcony_area'] = 0.0
            df['has_balcony'] = 0
        
        if 'Terasz' in df.columns:
            df['terrace_area'] = df['Terasz'].apply(parse_area)
            df['has_terrace'] = (df['terrace_area'] > 0).astype(int)
        else:
            df['terrace_area'] = 0.0
            df['has_terrace'] = 0
        
        df['outdoor_space'] = df['balcony_area'] + df['terrace_area']
        
        # 3. Building age categories
        if 'Építés éve' in df.columns:
            df['building_age'] = 2024 - df['Építés éve'].fillna(2000)
            df['era'] = pd.cut(df['Építés éve'].fillna(2000), 
                                bins=[0, 1945, 1970, 1990, 2010, 2024], 
                                labels=['Előháború', 'Szocializmus', 'Rendszerváltás', 'Modern', 'Új'])
        else:
            df['building_age'] = np.nan
            df['era'] = 'Ismeretlen'
        
        # 4. Floor categories
        if 'Szintek száma' in df.columns:
            df['is_ground_floor'] = (df['floor_numeric'] == 0).astype(int)
            df['is_top_floor'] = (df['floor_numeric'] >= df['Szintek száma'].fillna(5) - 1).astype(int)
            df['floor_ratio'] = df['floor_numeric'] / df['Szintek száma'].fillna(5)
        else:
            df['is_ground_floor'] = 0
            df['is_top_floor'] = 0
            df['floor_ratio'] = np.nan
        
        # 5. District premium categories
        premium_districts = [1, 2, 5, 6, 12]
        suburban_districts = [16, 17, 18, 19, 20, 21, 22, 23]
        
        if 'kerület' in df.columns:
            df['is_premium_district'] = df['kerület'].isin(premium_districts).astype(int)
            df['is_suburban'] = df['kerület'].isin(suburban_districts).astype(int)
        else:
            df['is_premium_district'] = 0
            df['is_suburban'] = 0
        
        # === INTERACTION FEATURES ===
        
        # 6. Price vs district average ratio
        if 'price_per_m2' in df.columns and 'district_avg_price' in df.columns:
            df['price_vs_district_ratio'] = df['price_per_m2'] / df['district_avg_price']
        else:
            df['price_vs_district_ratio'] = np.nan
        
        # 7. Size categories
        if 'area_m2' in df.columns:
            df['size_category'] = pd.cut(df['area_m2'].fillna(50), 
                                        bins=[0, 40, 60, 80, 120, 1000],
                                        labels=['Kicsi', 'Közepes', 'Nagy', 'XL', 'Villa'])
        else:
            df['size_category'] = 'Ismeretlen'
        
        # 8. Energy efficiency numeric
        if 'Energetikai besorolás' in df.columns:
            energy_map = {'A+': 7, 'A': 6, 'B': 5, 'C': 4, 'D': 3, 'E': 2, 'F': 1, 'G': 0}
            df['energy_numeric'] = df['Energetikai besorolás'].map(energy_map).fillna(2)
        else:
            df['energy_numeric'] = 2
        
        # 9. Condition numeric
        if 'Állapot' in df.columns:
            condition_map = {'Új építésű': 6, 'Újszerű': 5, 'Felújított': 4, 
                            'Jó állapotú': 3, 'Átlagos': 2, 'Felújítandó': 1}
            df['condition_numeric'] = df['Állapot'].map(condition_map).fillna(2)
        else:
            df['condition_numeric'] = 2
        
        # 10. Premium heating type
        if 'Fűtés' in df.columns:
            premium_heating = ['Mennyezeti hűtés-fűtés', 'Hőszivattyú', 'Gázkazán']
            df['premium_heating'] = df['Fűtés'].isin(premium_heating).astype(int)
        else:
            df['premium_heating'] = 0
        
        # === COMPOSITE FEATURES ===
        
        # 11. Quality index
        df['quality_index'] = (df['condition_numeric'] + df['energy_numeric'] + 
                            df['premium_heating'] * 2) / 4
        
        # 12. Location score
        df['location_score'] = (df['is_premium_district'] * 3 + 
                            (1 - df['is_suburban']) * 2 + 
                            df['floor_ratio'].fillna(0.5) + 
                            (df['outdoor_space'] > 0).astype(int))
        
        # 13. Modern features combination
        df['modern_features'] = ((df['building_age'] < 20).astype(int) + 
                                df['premium_heating'] + 
                                (df['energy_numeric'] >= 5).astype(int))
        
        # 14. Practicality index
        df['practicality_index'] = (df['m2_per_room'].fillna(25) / 30 +
                                    (df['area_m2'].fillna(0) >= 50).astype(int) +
                                    (df['has_balcony'] | df['has_terrace']).astype(int))
        
        return df
    
    def clean_and_prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare rental data with filtering.
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        initial_count = len(df)
        
        # Basic filters for rental data
        conditions = [
            ('price', '>', 50),           # Min 50k Ft/month
            ('price', '<', 2000),          # Max 2M Ft/month
            ('area_m2', '>', 15),          # Min 15 m²
            ('area_m2', '<', 300),         # Max 300 m²
            ('price_per_m2', '>', 0.5),    # Min 500 Ft/m²/month
            ('price_per_m2', '<', 50),     # Max 50k Ft/m²/month
            ('location', 'contains', 'Budapest')
        ]
        
        # Dynamic filtering
        for col, op, value in conditions:
            if col in df.columns:
                if op == '>':
                    df = df[df[col] > value]
                elif op == '<':
                    df = df[df[col] < value]
                elif op == 'contains':
                    df = df[df[col].str.contains(value, na=False)]
        
        filtered_count = len(df)
        print(f"📊 Filtering: {initial_count} → {filtered_count} records ({initial_count-filtered_count} removed)")
        
        return df
    
    def get_feature_columns(self) -> Tuple[List[str], List[str]]:
        """
        Get feature column definitions.
        
        Returns:
            Tuple of (numerical_features, categorical_features)
        """
        numerical_features = [
            'area_m2', 'floor_numeric', 'rooms', 'building_age', 'energy_numeric',
            'condition_numeric', 'quality_index', 'location_score', 'modern_features',
            'practicality_index', 'm2_per_room', 'outdoor_space',
            'floor_ratio', 'Építés éve', 'Szintek száma'
        ]
        
        categorical_features = [
            'kerület', 'Típus', 'Állapot', 'Fűtés', 'Energetikai besorolás',
            'era', 'size_category', 'is_premium_district', 'is_suburban',
            'has_balcony', 'has_terrace', 'is_ground_floor', 'is_top_floor',
            'premium_heating'
        ]
        
        return numerical_features, categorical_features
    
    def create_preprocessor(self, numerical_features: List[str], categorical_features: List[str]):
        """
        Create preprocessing pipeline.
        
        Args:
            numerical_features: List of numerical feature names
            categorical_features: List of categorical feature names
            
        Returns:
            ColumnTransformer preprocessor
        """
        numerical_transformer = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])
        
        preprocessor = ColumnTransformer([
            ('num', numerical_transformer, numerical_features),
            ('cat', categorical_transformer, categorical_features)
        ])
        
        return preprocessor
    
    def preprocess_full_pipeline(self, df: pd.DataFrame):
        """
        Full preprocessing pipeline for rental data.
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Tuple of (processed_df, X, y, num_features, cat_features)
        """
        print("🔧 Feature engineering...")
        
        # District prices preparation
        if 'Lakások összesen átlagár, ezer Ft/m²' in self.district_prices.columns:
            self.district_prices['kerület'] = self.district_prices['Az ingatlan helye'].str.extract('(\d+)').astype(float)
            district_avg = self.district_prices[['kerület', 'Lakások összesen átlagár, ezer Ft/m²']].copy()
            district_avg.iloc[:, 1] = district_avg.iloc[:, 1] / 1000
            district_avg = district_avg.rename(columns={'Lakások összesen átlagár, ezer Ft/m²': 'district_avg_price'})
        else:
            print("⚠️  No district average price data, using defaults")
            district_avg = pd.DataFrame({
                'kerület': range(1, 24),
                'district_avg_price': [1.0] * 23
            })
        
        # Extract district
        def extract_district(location):
            if pd.isna(location) or 'kerület' not in str(location):
                return None
            try:
                roman_nums = {'I':1, 'II':2, 'III':3, 'IV':4, 'V':5, 'VI':6, 'VII':7, 'VIII':8, 'IX':9, 'X':10,
                            'XI':11, 'XII':12, 'XIII':13, 'XIV':14, 'XV':15, 'XVI':16, 'XVII':17, 'XVIII':18,
                            'XIX':19, 'XX':20, 'XXI':21, 'XXII':22, 'XXIII':23}
                
                location_clean = str(location).replace('.', '').strip()
                for roman, num in roman_nums.items():
                    if roman in location_clean:
                        return num
                return None
            except:
                return None
        
        df['kerület'] = df['location'].apply(extract_district)
        
        # Merge district prices
        df = pd.merge(df, district_avg, on='kerület', how='left')
        
        # Price per m²
        if 'price' in df.columns and 'area_m2' in df.columns:
            df['price_per_m2'] = df['price'] / df['area_m2']
        else:
            df['price_per_m2'] = np.nan
        
        # Floor numeric conversion
        def parse_floor(floor_str):
            if pd.isna(floor_str):
                return 0
            floor_str = str(floor_str).lower()
            if 'földszint' in floor_str:
                return 0
            if 'félemelet' in floor_str:
                return 0.5
            if 'szint' in floor_str:
                return 0
            match = re.search(r'(\d+)', floor_str)
            return int(match.group(1)) if match else 0
        
        df['floor_numeric'] = df['floor'].apply(parse_floor)
        
        # Data cleaning
        df = self.clean_and_prepare_data(df)
        
        # Advanced features
        df = self.create_advanced_features(df)
        
        # Get feature columns
        numerical_features, categorical_features = self.get_feature_columns()
        
        # Keep only existing columns
        existing_num = [f for f in numerical_features if f in df.columns]
        existing_cat = [f for f in categorical_features if f in df.columns]
        
        print(f"📊 Numerical features: {len(existing_num)}")
        print(f"📊 Categorical features: {len(existing_cat)}")
        
        # Create preprocessor
        self.preprocessor = self.create_preprocessor(existing_num, existing_cat)
        
        # Features and target
        X = df[existing_num + existing_cat]
        
        # Target: price_per_m2
        if 'price_per_m2' in df.columns:
            y = df['price_per_m2'] * 1000  # Convert to Ft/m²
            print("🎯 Target: price_per_m2")
        else:
            df['price_per_m2'] = df['price'] / df['area_m2']
            y = df['price_per_m2'] * 1000
            print("🎯 Target: price_per_m2 (calculated)")
        
        return df, X, y, existing_num, existing_cat
