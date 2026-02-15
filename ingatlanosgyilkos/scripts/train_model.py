#!/usr/bin/env python3
"""
Train rental price prediction model.

This script trains an ML model to predict rental prices per m²
using advanced feature engineering and model optimization.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import ModelOptimizer, interpret_rmse
from src.preprocessing import AdvancedRealEstatePreprocessor


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train ML model for rental price prediction",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--data',
        type=Path,
        required=True,
        help='Input CSV file with rental data'
    )
    
    parser.add_argument(
        '--district-prices',
        type=Path,
        default=Path('data/external/budapest_district_prices_2023.csv'),
        help='CSV file with district average prices'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('models'),
        help='Directory to save trained models'
    )
    
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Test set size (0.0-1.0)'
    )
    
    parser.add_argument(
        '--cv-folds',
        type=int,
        default=5,
        help='Number of cross-validation folds'
    )
    
    parser.add_argument(
        '--no-plot',
        action='store_true',
        help='Skip generating plots'
    )
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    
    # Validation
    if not args.data.exists():
        print(f"❌ Error: Data file {args.data} does not exist")
        sys.exit(1)
    
    if not args.district_prices.exists():
        print(f"⚠️  Warning: District prices file {args.district_prices} not found")
        print("   Using default values")
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    print("📊 Advanced rental price model training")
    print(f"🎯 Target: price_per_m2 (Ft/m²/month)")
    
    # Load data
    print(f"\n📂 Loading data from {args.data}...")
    df = pd.read_csv(args.data)
    print(f"📋 Loaded {len(df)} records")
    
    # Preprocessing
    print("\n🔧 Preprocessing pipeline...")
    preprocessor = AdvancedRealEstatePreprocessor(str(args.district_prices))
    df_processed, X, y, num_features, cat_features = preprocessor.preprocess_full_pipeline(df)
    
    print(f"✅ Cleaned records: {len(df_processed)}")
    print(f"🎯 Features: {len(num_features) + len(cat_features)}")
    print(f"💰 Average rental price: {df_processed['price'].mean():.0f} Ft/month")
    print(f"📏 Average area: {df_processed['area_m2'].mean():.1f} m²")
    print(f"🏷️  Average price_per_m2: {y.mean():.2f} Ft/m²/month")
    
    # Train-test split
    print(f"\n✂️  Splitting data ({int((1-args.test_size)*100)}% train, {int(args.test_size*100)}% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42
    )
    
    # Apply preprocessing
    X_train_processed = preprocessor.preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.preprocessor.transform(X_test)
    
    # Get feature names
    try:
        cat_encoder = preprocessor.preprocessor.named_transformers_['cat'].named_steps['onehot']
        cat_feature_names = cat_encoder.get_feature_names_out(cat_features)
        feature_names = num_features + list(cat_feature_names)
    except:
        feature_names = [f'feature_{i}' for i in range(X_train_processed.shape[1])]
    
    # Train models
    print("\n🚀 Training and evaluating models...\n")
    optimizer = ModelOptimizer()
    results = optimizer.evaluate_models(X_train_processed, X_test_processed, y_train, y_test)
    
    # Store y_test for plotting
    results['y_test'] = y_test
    
    # Results summary
    best_name, best_model = optimizer.best_model
    print(f"\n🏆 Best model: {best_name}")
    print(f"📈 RMSE: {optimizer.best_score:.3f} Ft/m²/month")
    
    # Interpret RMSE
    interpret_rmse(optimizer.best_score, y.mean())
    
    # Plot results
    if not args.no_plot:
        print("\n📊 Generating visualization...")
        results_df = optimizer.plot_results(results, feature_names)
        print("\n📈 Model Performance Summary:")
        print(results_df[['Test_RMSE', 'R2_Score', 'Relative_Error_%']].to_string())
    
    # Save model
    print(f"\n💾 Saving model to {args.output_dir}...")
    optimizer.save_best_model(
        preprocessor.preprocessor,
        num_features,
        cat_features,
        str(args.output_dir)
    )
    
    print("\n✅ Training complete!")
    print(f"   Model: {args.output_dir}/best_rental_price_model.pkl")
    print(f"   Preprocessor: {args.output_dir}/preprocessor.pkl")
    print(f"   Features: {args.output_dir}/feature_columns.pkl")


if __name__ == "__main__":
    main()
