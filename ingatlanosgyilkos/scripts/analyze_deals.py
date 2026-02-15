#!/usr/bin/env python3
"""
Analyze rental listings and find best deals.

This script performs statistical analysis to identify undervalued rentals
based on price, district averages, and other factors.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis import filter_listings, find_statistical_best_deals, get_summary_stats


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze rental listings and find best deals",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--data',
        type=Path,
        required=True,
        help='Input CSV file with rental data'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        help='Output CSV file for best deals'
    )
    
    parser.add_argument(
        '--top-n',
        type=int,
        default=20,
        help='Number of top deals to show'
    )
    
    # Filters
    parser.add_argument(
        '--district',
        type=int,
        help='Filter by district (1-23)'
    )
    
    parser.add_argument(
        '--min-price',
        type=float,
        help='Minimum price (thousand Ft)'
    )
    
    parser.add_argument(
        '--max-price',
        type=float,
        help='Maximum price (thousand Ft)'
    )
    
    parser.add_argument(
        '--min-rooms',
        type=int,
        help='Minimum number of rooms'
    )
    
    parser.add_argument(
        '--max-rooms',
        type=int,
        help='Maximum number of rooms'
    )
    
    parser.add_argument(
        '--min-area',
        type=float,
        help='Minimum area (m²)'
    )
    
    parser.add_argument(
        '--max-area',
        type=float,
        help='Maximum area (m²)'
    )
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    
    # Validation
    if not args.data.exists():
        print(f"❌ Error: Data file {args.data} does not exist")
        sys.exit(1)
    
    # Load data
    print(f"📂 Loading data from {args.data}...")
    df = pd.read_csv(args.data)
    print(f"📋 Loaded {len(df)} listings")
    
    # Ensure required columns exist
    required_cols = ['price', 'area_m2', 'location']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ Error: Missing required columns: {missing_cols}")
        sys.exit(1)
    
    # Calculate price_per_m2 if not present
    if 'price_per_m2' not in df.columns:
        df['price_per_m2'] = df['price'] / df['area_m2']
        print("📐 Calculated price_per_m2")
    
    # Calculate kerület if not present
    if 'kerület' not in df.columns:
        def extract_district(location):
            import re
            if pd.isna(location):
                return None
            roman_nums = {'I':1, 'II':2, 'III':3, 'IV':4, 'V':5, 'VI':6, 'VII':7, 'VIII':8, 'IX':9, 'X':10,
                        'XI':11, 'XII':12, 'XIII':13, 'XIV':14, 'XV':15, 'XVI':16, 'XVII':17, 'XVIII':18,
                        'XIX':19, 'XX':20, 'XXI':21, 'XXII':22, 'XXIII':23}
            for roman, num in roman_nums.items():
                if roman in str(location):
                    return num
            return None
        
        df['kerület'] = df['location'].apply(extract_district)
        print("🗺️  Extracted districts")
    
    # Summary statistics before filtering
    print("\n📊 Dataset Summary:")
    stats = get_summary_stats(df)
    print(f"   Total listings: {stats['total_listings']}")
    print(f"   Avg price: {stats['avg_price']:.0f} Ft/month")
    print(f"   Avg area: {stats['avg_area']:.1f} m²")
    print(f"   Avg price/m²: {stats['avg_price_per_m2']:.0f} Ft/m²")
    print(f"   Districts: {stats['districts_covered']}")
    
    # Apply filters
    if any([args.district, args.min_price, args.max_price, args.min_rooms, 
            args.max_rooms, args.min_area, args.max_area]):
        print("\n🔍 Applying filters...")
        df_filtered = filter_listings(
            df,
            district=args.district,
            min_price=args.min_price,
            max_price=args.max_price,
            min_rooms=args.min_rooms,
            max_rooms=args.max_rooms,
            min_area=args.min_area,
            max_area=args.max_area
        )
        print(f"   {len(df)} → {len(df_filtered)} listings")
    else:
        df_filtered = df
    
    if len(df_filtered) == 0:
        print("❌ No listings match the filters!")
        sys.exit(1)
    
    # Find best deals
    print(f"\n📈 Finding top {args.top_n} best deals...")
    best_deals = find_statistical_best_deals(df_filtered, n_deals=args.top_n)
    
    if best_deals is None or len(best_deals) == 0:
        print("❌ Could not find any deals!")
        sys.exit(1)
    
    # Display results
    print(f"\n🏆 Top {len(best_deals)} Best Deals:\n")
    
    # Format for display
    display_df = best_deals.copy()
    display_df['price'] = display_df['price'].apply(lambda x: f"{x:,.0f} Ft")
    display_df['area_m2'] = display_df['area_m2'].apply(lambda x: f"{x:.0f} m²")
    display_df['price_per_m2'] = display_df['price_per_m2'].apply(lambda x: f"{x:.0f} Ft/m²")
    
    # Print table
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)
    
    print(display_df[['kerület', 'price', 'area_m2', 'price_per_m2', 'érték_pont', 'ár_arány']].to_string(index=False))
    
    # Show URLs
    print("\n🔗 URLs:")
    for idx, row in best_deals.head(5).iterrows():
        print(f"   {idx+1}. {row['url']}")
    
    # Save to file if requested
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        best_deals.to_csv(args.output, index=False)
        print(f"\n💾 Results saved to {args.output}")
    
    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
