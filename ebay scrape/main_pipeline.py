import asyncio
import pandas as pd
from typing import List, Dict, Any
from sofascore_client import SofaScoreClient
from tcdb_scraper import TcdbScraper
from ebay_scraper_v2 import EbayScraperV2
from matching_engine import MatchingEngine
import os

class FootballCardPipeline:
    def __init__(self):
        self.sofascore = SofaScoreClient()
        self.tcdb = TcdbScraper()
        self.ebay = EbayScraperV2()
        self.matcher = MatchingEngine()
        
    async def run_for_player(self, player_name: str):
        print(f"\n--- Processing Player: {player_name} ---")
        
        # 1. Fetch Cards from TCDB (Ground Truth)
        print(f"Fetching TCDB cards for {player_name}...")
        tcdb_cards = await self.tcdb.fetch_player_cards(player_name)
        if not tcdb_cards:
            print(f"No TCDB data for {player_name}. Skipping.")
            return []

        # 2. Fetch Sold Items from eBay
        # We query for the player's most popular cards or general name
        print(f"Fetching eBay sold items for {player_name}...")
        ebay_items = await self.ebay.fetch_sold_items(f"{player_name} rookie card", limit=20)
        
        # 3. Match and Price
        results = []
        for item in ebay_items:
            # Prepare card data for matcher (unify keys)
            formatted_tcdb = []
            for c in tcdb_cards:
                formatted_tcdb.append({
                    'player_name': c['player'],
                    'card_number': c['number'],
                    'set_name': c['set'],
                    'year': c['year'],
                    'is_auto': 'AU' in c.get('raw_text', '')
                })
            
            best_match = self.matcher.get_best_match(item['title'], formatted_tcdb)
            if best_match:
                results.append({
                    'ebay_title': item['title'],
                    'ebay_price': item['price'],
                    'currency': item['currency'],
                    'matched_set': best_match['set_name'],
                    'matched_number': best_match['card_number'],
                    'matched_year': best_match['year'],
                    'confidence': best_match.get('match_score', 0)
                })
        
        print(f"Matched {len(results)} / {len(ebay_items)} items for {player_name}.")
        return results

    async def run_full_pipeline(self, tournament_id: int, season_id: int, limit: int = 3):
        # 1. Get Top Young Players
        print("Fetching top young players from SofaScore...")
        players = self.sofascore.get_top_young_players(tournament_id, season_id, max_age=23, limit=limit)
        
        all_results = []
        for p in players:
            player_results = await self.run_for_player(p['name'])
            # Attach SofaScore stats
            for res in player_results:
                res['player_rating'] = p['rating']
                res['market_value'] = p.get('marketValue', 0)
                all_results.append(res)
        
        # Save to CSV
        if all_results:
            df = pd.DataFrame(all_results)
            output_path = "data/pipeline_results.csv"
            os.makedirs("data", exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"\nPipeline finished! Saved results to {output_path}")
        else:
            print("\nNo results matched.")

if __name__ == "__main__":
    pipeline = FootballCardPipeline()
    # Let's run for a specific high-value player to see the matching in action
    asyncio.run(pipeline.run_for_player("Phil Foden"))
