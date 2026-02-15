"""
Statistical analysis functions for finding best rental deals.

This module provides functions for analyzing rental listings
and identifying statistically good deals.
"""

from typing import Dict

import numpy as np
import pandas as pd
from scipy import stats


def find_statistical_best_deals(df: pd.DataFrame, n_deals: int = 10) -> pd.DataFrame:
    """
    Find the best rental deals using statistical methods.
    
    Uses Z-score analysis and district average comparisons to identify
    undervalued rentals.
    
    Args:
        df: DataFrame with rental listing data
        n_deals: Number of top deals to return
        
    Returns:
        DataFrame with best deals sorted by value score
    """
    if df is None or len(df) == 0:
        return None
    
    print("📈 Running statistical analysis...")
    
    # Price per m² based evaluation
    df_analysis = df.copy()
    
    # 1. Z-score based outlier detection (good deals = low price)
    df_analysis['price_zscore'] = np.abs(stats.zscore(df_analysis['price_per_m2'].fillna(
        df_analysis['price_per_m2'].median())))
    
    # 2. Calculate district averages
    district_stats = df_analysis.groupby('kerület').agg({
        'price_per_m2': ['mean', 'std'],
        'price': 'mean'
    }).round(0)
    district_stats.columns = ['district_avg_price_m2', 'district_std_price_m2', 'district_avg_price']
    
    # 3. Calculate relative value (price/average ratio)
    df_analysis = df_analysis.merge(district_stats, on='kerület', how='left')
    df_analysis['price_ratio'] = df_analysis['price_per_m2'] / df_analysis['district_avg_price_m2']
    
    # 4. Calculate value score
    df_analysis['value_score'] = (
        (1 / df_analysis['price_ratio']) * 0.6 +  # Price/value ratio (60%)
        (1 / (df_analysis['price_zscore'] + 0.1)) * 0.4    # Statistical normality (40%)
    )
    
    # 5. Select best deals
    best_deals = df_analysis.nlargest(n_deals, 'value_score')[[
        'title', 'price', 'area_m2', 'price_per_m2', 'kerület', 
        'location', 'value_score', 'price_ratio', 'url'
    ]]
    
    best_deals = best_deals.round({'price_per_m2': 0, 'value_score': 3, 'price_ratio': 2})
    best_deals = best_deals.rename(columns={
        'price_ratio': 'ár_arány',  # 1.0 = average, <1.0 = better than average
        'value_score': 'érték_pont'
    })
    
    return best_deals


def filter_listings(df: pd.DataFrame, 
                   district: int = None,
                   min_price: float = None,
                   max_price: float = None,
                   min_rooms: int = None,
                   max_rooms: int = None,
                   min_area: float = None,
                   max_area: float = None) -> pd.DataFrame:
    """
    Filter rental listings based on criteria.
    
    Args:
        df: DataFrame with rental listings
        district: Filter by district number
        min_price, max_price: Price range in thousand Ft
        min_rooms, max_rooms: Number of rooms range
        min_area, max_area: Area range in m²
        
    Returns:
        Filtered DataFrame
    """
    filtered = df.copy()
    
    if district is not None:
        filtered = filtered[filtered['kerület'] == district]
    
    if min_price is not None:
        filtered = filtered[filtered['price'] >= min_price]
    
    if max_price is not None:
        filtered = filtered[filtered['price'] <= max_price]
    
    if min_rooms is not None:
        filtered = filtered[filtered['rooms'] >= min_rooms]
    
    if max_rooms is not None:
        filtered = filtered[filtered['rooms'] <= max_rooms]
    
    if min_area is not None:
        filtered = filtered[filtered['area_m2'] >= min_area]
    
    if max_area is not None:
        filtered = filtered[filtered['area_m2'] <= max_area]
    
    return filtered


def get_summary_stats(df: pd.DataFrame) -> Dict:
    """
    Get summary statistics for rental listings.
    
    Args:
        df: DataFrame with rental listings
        
    Returns:
        Dictionary with summary statistics
    """
    return {
        'total_listings': len(df),
        'avg_price': df['price'].mean(),
        'median_price': df['price'].median(),
        'avg_area': df['area_m2'].mean(),
        'avg_rooms': df['rooms'].mean(),
        'avg_price_per_m2': df['price_per_m2'].mean(),
        'districts_covered': df['kerület'].nunique()
    }
