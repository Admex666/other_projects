"""
Optivoya Experience Connectors — Multi-Source Diagnostic Runner
Tests all 4 connectors (OSM, Wikidata, Wikipedia, Google Maps) on a destination seed (e.g. Bari, Italy),
saves the raw source records, and prints an analytical breakdown of what each source provides.

Usage:
    python scripts/test_experience_connectors.py
    python scripts/test_experience_connectors.py --city Rome --lat 41.9028 --lon 12.4964 --country Italy
"""
import sys
import os
import argparse
from typing import List

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.experience.connectors import (
    DestinationSeed,
    RawSourceRecord,
    OSMConnector,
    WikidataConnector,
    WikipediaConnector,
    GoogleMapsConnector
)
from app.services.experience.raw_store import RawDataStore

def run_connectors_pipeline(
    seed: DestinationSeed,
    osm_limit: int = 150,
    wd_limit: int = 100,
    wp_limit: int = 30,
    gm_limit: int = 35
):
    print("=" * 80)
    print(f"🚀 OPTIVOYA EXPERIENCE CONNECTORS PIPELINE")
    print(f"Destination: {seed.name}, {seed.country} (ID: {seed.destination_id})")
    print(f"Center Coordinates: ({seed.lat}, {seed.lon}) | Radius: {seed.radius_km} km")
    print(f"Target Limits: OSM={osm_limit} | Wikidata={wd_limit} | Wikipedia={wp_limit} | GoogleMaps={gm_limit}")
    print("=" * 80)

    store = RawDataStore()
    all_records: List[RawSourceRecord] = []

    # 1. OSM Overpass Connector
    print("\n[1/4] Querying OpenStreetMap (OSM Overpass)...")
    osm_conn = OSMConnector()
    osm_records = osm_conn.fetch_records(seed, limit=osm_limit)
    print(f" -> Found {len(osm_records)} OSM records.")
    store.save_records(osm_records, seed.destination_id)
    all_records.extend(osm_records)

    # 2. Wikidata Semantic Connector
    print("\n[2/4] Querying Wikidata SPARQL...")
    wd_conn = WikidataConnector()
    wd_records = wd_conn.fetch_records(seed, limit=wd_limit)
    print(f" -> Found {len(wd_records)} Wikidata semantic entities.")
    store.save_records(wd_records, seed.destination_id)
    all_records.extend(wd_records)

    # 3. Wikipedia Narrative Connector
    print("\n[3/4] Querying Wikipedia Geosearch & REST API...")
    wp_conn = WikipediaConnector()
    wp_records = wp_conn.fetch_records(seed, limit=wp_limit)
    print(f" -> Found {len(wp_records)} Wikipedia articles and extracts.")
    store.save_records(wp_records, seed.destination_id)
    all_records.extend(wp_records)

    # 4. Google Maps Browser Scraper
    print("\n[4/4] Scraping Google Maps Places (Playwright)...")
    gm_conn = GoogleMapsConnector()
    gm_records = gm_conn.fetch_records(seed, limit=gm_limit)
    print(f" -> Scraped {len(gm_records)} Google Maps places (with ratings & reviews).")
    store.save_records(gm_records, seed.destination_id)
    all_records.extend(gm_records)

    # =========================================================================
    # DIAGNOSTIC BREAKDOWN & EVALUATION
    # =========================================================================
    print("\n" + "=" * 80)
    print("📊 DATA EXTRACTION & VALUE BREAKDOWN")
    print("=" * 80)

    print(f"\nTotal Raw Records Ingested: {len(all_records)}")
    print(f"Saved to Raw Store at: data/raw_sources/{seed.destination_id}/")

    print("\n--- A) OpenStreetMap (Geospatial, Beaches, Viewpoints, Free Amenities) ---")
    beaches = []
    viewpoints = []
    museums = []
    others = []
    for r in osm_records:
        tags = r.raw_payload.get("tags", {})
        nat = tags.get("natural")
        tour = tags.get("tourism")
        hist = tags.get("historic")
        if nat == "beach":
            beaches.append(r.name_candidate)
        elif tour == "viewpoint":
            viewpoints.append(r.name_candidate)
        elif tour == "museum":
            museums.append(r.name_candidate)
        else:
            others.append(f"{r.name_candidate} [{tour or hist or 'place'}]")

    print(f" * Strandok (Beaches) ({len(beaches)}): {', '.join(beaches[:5]) or 'none'}")
    print(f" * Kilátók (Viewpoints) ({len(viewpoints)}): {', '.join(viewpoints[:5]) or 'none'}")
    print(f" * Múzeumok ({len(museums)}): {', '.join(museums[:5]) or 'none'}")
    print(f" * További látványosságok: {', '.join(others[:5])}")

    print("\n--- B) Wikidata (Ontology, UNESCO/Heritage, Cross-links, Images) ---")
    for r in wd_records[:6]:
        inst = r.raw_payload.get("instance_of_label", "-")
        has_img = "📸 Igen" if r.raw_payload.get("image_url") else "❌ Nincs"
        has_wiki = "🔗 Igen" if r.raw_payload.get("wikipedia_url") else "❌ Nincs"
        print(f" * {r.name_candidate} | Típus: {inst} | Kép: {has_img} | Wikipedia: {has_wiki}")

    print("\n--- C) Wikipedia (Kulturális narratíva & Háttértudás) ---")
    for r in wp_records[:3]:
        extract = r.raw_payload.get("extract", "")[:120]
        print(f" * {r.name_candidate}: \"{extract}...\"")

    print("\n--- D) Google Maps (Kereskedelmi aktivitás, Értékelések, Népszerűség) ---")
    for r in gm_records[:8]:
        p = r.raw_payload
        rating = f"⭐ {p.get('rating')}" if p.get('rating') else "⭐ -"
        revs = f"({p.get('review_count')} vélemény)" if p.get('review_count') else ""
        print(f" * {r.name_candidate} | {rating} {revs}")

    # Cross-source overlap analysis
    print("\n" + "=" * 80)
    print("🔍 CROSS-SOURCE MATCH CANDIDATES (Közös entitások)")
    print("=" * 80)
    names_osm = {r.name_candidate.lower(): r.name_candidate for r in osm_records}
    names_wd = {r.name_candidate.lower(): r.name_candidate for r in wd_records}
    names_gm = {r.name_candidate.lower(): r.name_candidate for r in gm_records}

    # Find token-based partial matches
    matches = []
    for g_key, g_orig in names_gm.items():
        found_in = ["Google Maps"]
        matched_osm = None
        matched_wd = None
        
        # Check OSM
        for o_key, o_orig in names_osm.items():
            if any(token in o_key for token in g_key.split() if len(token) > 4):
                found_in.append("OSM")
                matched_osm = o_orig
                break

        # Check Wikidata
        for w_key, w_orig in names_wd.items():
            if any(token in w_key for token in g_key.split() if len(token) > 4):
                found_in.append("Wikidata")
                matched_wd = w_orig
                break

        if len(found_in) > 1:
            matches.append({
                "target": g_orig,
                "sources": found_in,
                "osm_name": matched_osm,
                "wd_name": matched_wd
            })

    if matches:
        print(f"Találtunk {len(matches)} több forrásban is azonosítható helyszínt:")
        for m in matches[:6]:
            print(f" 👉 {m['target']} (Források: {', '.join(m['sources'])})")
    else:
        print("Több forrásban fellelhető reprezentatív helyszínek feldolgozva.")

    print("\n[OK] Connectors pipeline futás befejeződött!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test experience connectors")
    parser.add_argument("--city", default="Bari", help="City name")
    parser.add_argument("--country", default="Italy", help="Country")
    parser.add_argument("--lat", type=float, default=41.1171, help="Latitude")
    parser.add_argument("--lon", type=float, default=16.8719, help="Longitude")
    parser.add_argument("--radius", type=float, default=15.0, help="Radius in km")
    parser.add_argument("--osm-limit", type=int, default=150, help="OSM record limit")
    parser.add_argument("--wd-limit", type=int, default=100, help="Wikidata record limit")
    parser.add_argument("--wp-limit", type=int, default=30, help="Wikipedia record limit")
    parser.add_argument("--gm-limit", type=int, default=35, help="Google Maps place limit")
    args = parser.parse_args()

    dest_id = f"{args.country[:2].upper()}_{args.city.upper().replace(' ', '_')}"
    seed = DestinationSeed(
        destination_id=dest_id,
        name=args.city,
        country=args.country,
        lat=args.lat,
        lon=args.lon,
        radius_km=args.radius
    )
    run_connectors_pipeline(
        seed,
        osm_limit=args.osm_limit,
        wd_limit=args.wd_limit,
        wp_limit=args.wp_limit,
        gm_limit=args.gm_limit
    )
