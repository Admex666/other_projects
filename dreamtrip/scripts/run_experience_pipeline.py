"""
End-to-End Experience Pipeline Runner: Ingest -> Raw Store -> Resolve -> Experience DB -> Destination Profile
Usage:
    python scripts/run_experience_pipeline.py --city Bari --country Italy
    python scripts/run_experience_pipeline.py --from-raw IT_BARI
"""
import sys
import os
import argparse

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase, is_supabase_configured
from app.services.experience.connectors import (
    DestinationSeed,
    OSMConnector,
    WikidataConnector,
    WikipediaConnector,
    GoogleMapsConnector
)
from app.services.experience.raw_store import RawDataStore
from app.services.experience.entity_resolution import EntityResolutionEngine
from app.services.experience.enrichment import ExperienceEnricher
from app.services.experience.destination_profiler import DestinationProfiler
from app.services.experience.experience_db import ExperienceDB

def run_pipeline(
    city: str = "Bari",
    country: str = "Italy",
    lat: float = 41.1171,
    lon: float = 16.8719,
    radius_km: float = 15.0,
    from_raw: str = None
):
    print("=" * 80)
    print(f"🚀 OPTIVOYA EXPERIENCE ENGINE — END-TO-END PIPELINE")
    print("=" * 80)

    dest_id = from_raw.upper() if from_raw else f"{country[:2].upper()}_{city.upper().replace(' ', '_')}"
    raw_store = RawDataStore()
    exp_db = ExperienceDB()

    # Step 1: Ingest or load raw records
    if from_raw:
        print(f"\n[1/5] Loading existing raw records from local store for {dest_id}...")
        raw_records = raw_store.load_records(dest_id)
        print(f" -> Loaded {len(raw_records)} raw records.")
    else:
        seed = DestinationSeed(
            destination_id=dest_id,
            name=city,
            country=country,
            lat=lat,
            lon=lon,
            radius_km=radius_km
        )
        print(f"\n[1/5] Ingesting fresh raw data for {city}, {country} ({lat}, {lon})...")
        raw_records = []

        # OSM
        print(" * Fetching OSM...")
        osm_recs = OSMConnector().fetch_records(seed, limit=150)
        raw_store.save_records(osm_recs, dest_id)
        raw_records.extend(osm_recs)

        # Wikidata
        print(" * Fetching Wikidata...")
        wd_recs = WikidataConnector().fetch_records(seed, limit=100)
        raw_store.save_records(wd_recs, dest_id)
        raw_records.extend(wd_recs)

        # Wikipedia
        print(" * Fetching Wikipedia...")
        wp_recs = WikipediaConnector().fetch_records(seed, limit=30)
        raw_store.save_records(wp_recs, dest_id)
        raw_records.extend(wp_recs)

        # Google Maps
        print(" * Scraping Google Maps...")
        gm_recs = GoogleMapsConnector().fetch_records(seed, limit=30)
        raw_store.save_records(gm_recs, dest_id)
        raw_records.extend(gm_recs)

        print(f" -> Total {len(raw_records)} raw records ingested and cached.")

    # Step 2: Sync raw records to Supabase raw_source_records
    print(f"\n[2/5] Syncing raw source records to Supabase 'raw_source_records'...")
    synced_raw = raw_store._sync_records_to_supabase(raw_records, dest_id)
    print(f" -> Synced {synced_raw} raw records to Supabase.")

    # Step 3: Entity Resolution & Deduplication
    print(f"\n[3/5] Resolving entities & cross-source deduplication...")
    resolver = EntityResolutionEngine()
    canonical_entities = resolver.resolve_destination(raw_records, dest_id)
    print(f" -> Created {len(canonical_entities)} canonical experience entities!")

    # Step 4: Data Enrichment, Classification & Experience Modeling (PHASE 4)
    print(f"\n[4/5] Running Phase 4: Data Enrichment, Classification & Modeling...")
    enricher = ExperienceEnricher(walk_radius_km=0.5)
    enriched_entities = enricher.enrich_entities(canonical_entities, center_lat=lat, center_lon=lon)
    print(f" -> Enriched {len(enriched_entities)} entities with temporal, price, persona, and walkability data!")

    # Upsert enriched canonical entities to Supabase
    print(f" * Saving enriched canonical entities to Supabase 'experience_entities'...")
    synced_entities = exp_db.upsert_canonical_entities(enriched_entities)
    print(f" -> Synced {synced_entities} entities to Supabase.")

    # Step 5: Aggregate Destination Experience Profile
    print(f"\n[5/5] Generating Destination Experience Profile...")
    profiler = DestinationProfiler()
    profile = profiler.build_profile(
        destination_id=dest_id,
        city_name=city,
        country=country,
        entities=enriched_entities
    )

    # Upsert profile to Supabase
    print(f" * Saving destination profile to Supabase 'destination_experience_profiles'...")
    profile_saved = exp_db.upsert_destination_profile(profile)
    print(f" -> Profile saved in Supabase: {profile_saved}")

    # =========================================================================
    # PHASE 4 MULTI-DIMENSIONAL BREAKDOWN
    # =========================================================================
    print("\n" + "=" * 80)
    print(f"📊 PHASE 4 ENRICHMENT & MODELING BREAKDOWN: {city.upper()}")
    print("=" * 80)
    
    # 1. Quality Tiers
    tiers = {}
    for e in enriched_entities:
        t = e.metadata.get("quality_tier", "supplemental")
        tiers[t] = tiers.get(t, 0) + 1
    print("\n1. Quality & Confidence Tiers:")
    print(f" * Flagship (Tier 1, Score >= 0.80): {tiers.get('flagship', 0)} places")
    print(f" * Recommended (Tier 2, Score 0.60-0.79): {tiers.get('recommended', 0)} places")
    print(f" * Supplemental (Tier 3): {tiers.get('supplemental', 0)} places")

    # 2. Environmental & Weather
    env_breakdown = {}
    for e in enriched_entities:
        env = e.metadata.get("indoor_outdoor", "outdoor")
        env_breakdown[env] = env_breakdown.get(env, 0) + 1
    print("\n2. Environment & Setting:")
    for env, c in env_breakdown.items():
        print(f" * {env.capitalize()}: {c} places")

    # 3. Price Brackets
    prices = {}
    for e in enriched_entities:
        p = e.price_level
        prices[p] = prices.get(p, 0) + 1
    print("\n3. Price Categories:")
    for p, c in prices.items():
        print(f" * {p.capitalize()}: {c} places")

    # 4. Travel Persona Tagging
    persona_counts = {}
    for e in enriched_entities:
        for persona in e.metadata.get("persona_tags", []):
            persona_counts[persona] = persona_counts.get(persona, 0) + 1
    print("\n4. Traveler Persona Distribution:")
    for persona, c in sorted(persona_counts.items(), key=lambda x: x[1], reverse=True):
        print(f" * {persona}: {c} matching activities")

    # 5. Walkability & Proximity Graph Sample
    print("\n5. Walkable Circuit / Itinerary Pairing Sample (Neighbors < 500m):")
    walkable_samples = [e for e in enriched_entities if e.metadata.get("walkable_neighbors_count", 0) >= 3][:3]
    for e in walkable_samples:
        print(f" 📍 {e.canonical_name} ({e.metadata.get('walkable_neighbors_count')} nearby places within 500m):")
        for n in e.metadata.get("nearby_walkable_entities", [])[:3]:
            print(f"    -> {n['name']} ({n['dist_m']} meters walk)")

    print("\n[OK] Experience pipeline execution completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run complete experience pipeline")
    parser.add_argument("--city", default="Bari", help="City name")
    parser.add_argument("--country", default="Italy", help="Country")
    parser.add_argument("--lat", type=float, default=41.1171, help="Latitude")
    parser.add_argument("--lon", type=float, default=16.8719, help="Longitude")
    parser.add_argument("--radius", type=float, default=15.0, help="Radius in km")
    parser.add_argument("--from-raw", default=None, help="Process existing raw destination store (e.g. IT_BARI)")
    args = parser.parse_args()

    run_pipeline(
        city=args.city,
        country=args.country,
        lat=args.lat,
        lon=args.lon,
        radius_km=args.radius,
        from_raw=args.from_raw
    )
