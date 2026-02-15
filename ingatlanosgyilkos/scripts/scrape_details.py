#!/usr/bin/env python3
"""
Scrape detailed rental listing information from Zenga.hu.

This script downloads detailed information for rental listings,
using parallel processing for efficiency and caching to avoid redundant work.
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper import CacheManager, process_batch


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape detailed rental listing data from Zenga.hu",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help='Input CSV file with URLs to scrape'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/raw/zenga_rentals_details.csv'),
        help='Output CSV file for scraped data'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=9,
        help='Number of parallel Chrome drivers'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=200,
        help='Number of URLs to process per batch'
    )
    
    parser.add_argument(
        '--cache-file',
        type=Path,
        default=Path('cache/scrape_cache_rentals.json'),
        help='Cache file to track processed URLs'
    )
    
    parser.add_argument(
        '--test-only',
        action='store_true',
        help='Test with only one URL'
    )
    
    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    start_time = time.time()
    
    # Validation
    if not args.input.exists():
        print(f"❌ Error: Input file {args.input} does not exist")
        sys.exit(1)
    
    # Create output directory
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Load URLs
    print(f"📂 Loading URLs from {args.input}...")
    links_df_all = pd.read_csv(args.input)
    
    # Filter for rental listings only
    links_df_all = links_df_all[links_df_all["url"].str.contains("/kiado", na=False)]
    print(f"📋 Found {len(links_df_all)} rental URLs")
    
    # Load existing data
    if args.output.exists():
        existing_df = pd.read_csv(args.output)
        existing_urls = set(existing_df["url"].tolist())
        print(f"✅ {len(existing_df)} already scraped")
    else:
        existing_df = pd.DataFrame()
        existing_urls = set()
    
    # Load cache
    cache_manager = CacheManager(str(args.cache_file))
    cache = cache_manager.load_cache()
    existing_urls.update(cache["processed_urls"])
    
    # Filter new URLs
    links_df = links_df_all[~links_df_all["url"].isin(existing_urls)]
    print(f"🆕 {len(links_df)} new URLs to process")
    
    if len(links_df) == 0:
        print("✅ All URLs already processed!")
        return
    
    # Test mode
    if args.test_only:
        print("\n🧪 TEST MODE - Processing only 1 URL")
        urls_list = links_df["url"].tolist()[:1]
    else:
        urls_list = links_df["url"].tolist()
        
        # Confirmation
        if not args.no_confirm:
            response = input(f"\n⏰ Process {len(urls_list)} URLs? (y/n): ")
            if response.lower() != 'y':
                print("⏹️  Cancelled")
                return
    
    # Process in batches
    all_results = []
    
    for i in range(0, len(urls_list), args.batch_size):
        batch = urls_list[i:i+args.batch_size]
        batch_num = i//args.batch_size + 1
        total_batches = (len(urls_list)-1)//args.batch_size + 1
        
        print(f"\n🔄 Batch {batch_num}/{total_batches}")
        
        batch_results = process_batch(batch, existing_urls, max_workers=args.max_workers)
        all_results.extend(batch_results)
        
        # Save intermediate results
        if all_results:
            new_df = pd.DataFrame(all_results)
            if not existing_df.empty:
                updated_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                updated_df = new_df
            
            updated_df.to_csv(args.output, index=False)
            
            # Update cache
            processed_urls = [item["url"] for item in all_results]
            cache_manager.save_cache(processed_urls)
            
            print(f"💾 {len(all_results)} new listings saved")
    
    # Final summary
    elapsed = time.time() - start_time
    rate = len(all_results) / (elapsed / 60) if elapsed > 0 else 0
    
    print(f"\n🎉 COMPLETED!")
    print(f"⏱️  Time: {elapsed/60:.1f} minutes")
    print(f"📊 New data: {len(all_results)}")
    print(f"🚀 Speed: {rate:.0f} listings/min")
    print(f"📄 Saved to: {args.output}")


if __name__ == "__main__":
    main()
