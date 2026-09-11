"""
Entity Resolution & Deduplication Pipeline for Optivoya Experience Engine.
Merges raw multi-source records (OSM, Wikidata, Wikipedia, Google Maps) into canonical,
deduplicated experience entities with verified coordinates, reviews, images, and confidence scores.
"""
import math
import re
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime

from .connectors.base import RawSourceRecord
from .models import CanonicalExperienceEntity

def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def tokenize_name(name: str) -> set:
    """Normalizes and tokenizes a place name for fuzzy matching."""
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', name.lower())
    stop_words = {"the", "of", "di", "de", "del", "della", "san", "santa", "and", "in", "a", "il", "la", "le"}
    tokens = {t for t in cleaned.split() if len(t) > 2 and t not in stop_words}
    return tokens

def name_similarity(name1: str, name2: str) -> float:
    """Calculates Jaccard token similarity between two names."""
    tokens1 = tokenize_name(name1)
    tokens2 = tokenize_name(name2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union)

class EntityResolutionEngine:
    def __init__(self, match_distance_meters: float = 200.0, name_similarity_threshold: float = 0.35):
        self.match_distance_meters = match_distance_meters
        self.name_similarity_threshold = name_similarity_threshold

    def resolve_destination(self, raw_records: List[RawSourceRecord], destination_id: str) -> List[CanonicalExperienceEntity]:
        """Resolves and merges raw source records into deduplicated canonical experience entities."""
        clusters: List[List[RawSourceRecord]] = []

        # Index records by source
        by_source = defaultdict(list)
        for r in raw_records:
            by_source[r.source].append(r)

        # 1. Cluster by exact Wikidata QID (OSM wikidata tag == Wikidata QID)
        qid_to_records = defaultdict(list)
        unmatched_records = []

        for r in raw_records:
            qid = None
            if r.source == "wikidata":
                qid = r.source_id
            elif r.source == "osm":
                qid = r.raw_payload.get("tags", {}).get("wikidata")
            
            if qid and qid.startswith("Q"):
                qid_to_records[qid].append(r)
            else:
                unmatched_records.append(r)

        for qid, recs in qid_to_records.items():
            clusters.append(recs)

        # 2. Match remaining records by Coordinates + Name Similarity
        for rec in unmatched_records:
            r_lat, r_lon = self._extract_coords(rec)
            best_cluster_idx = None
            best_score = 0.0

            if r_lat is not None and r_lon is not None:
                for idx, cluster in enumerate(clusters):
                    # Compare against representative record in cluster
                    for c_rec in cluster:
                        c_lat, c_lon = self._extract_coords(c_rec)
                        if c_lat is not None and c_lon is not None:
                            dist = haversine_meters(r_lat, r_lon, c_lat, c_lon)
                            if dist <= self.match_distance_meters:
                                sim = name_similarity(rec.name_candidate, c_rec.name_candidate)
                                if sim >= self.name_similarity_threshold:
                                    score = (1.0 - (dist / self.match_distance_meters)) * 0.5 + sim * 0.5
                                    if score > best_score:
                                        best_score = score
                                        best_cluster_idx = idx
                                    break

            if best_cluster_idx is not None:
                clusters[best_cluster_idx].append(rec)
            else:
                # Also try pure name similarity if no coordinates
                name_matched = False
                for idx, cluster in enumerate(clusters):
                    for c_rec in cluster:
                        sim = name_similarity(rec.name_candidate, c_rec.name_candidate)
                        if sim >= 0.75:  # High confidence name match
                            clusters[idx].append(rec)
                            name_matched = True
                            break
                    if name_matched:
                        break

                if not name_matched:
                    clusters.append([rec])

        # 3. Build CanonicalExperienceEntity from each cluster
        canonical_entities: List[CanonicalExperienceEntity] = []
        seen_ids = set()
        for cluster in clusters:
            entity = self._merge_cluster(cluster, destination_id)
            if entity:
                base_id = entity.entity_id
                counter = 1
                while entity.entity_id in seen_ids:
                    entity.entity_id = f"{base_id}_{counter}"
                    counter += 1
                seen_ids.add(entity.entity_id)
                canonical_entities.append(entity)

        return canonical_entities

    def _extract_coords(self, record: RawSourceRecord) -> Tuple[Optional[float], Optional[float]]:
        """Extracts latitude and longitude from different source formats."""
        p = record.raw_payload
        if record.source == "osm":
            lat = p.get("lat") or p.get("center", {}).get("lat")
            lon = p.get("lon") or p.get("center", {}).get("lon")
            return lat, lon
        elif record.source == "google_maps":
            return p.get("lat"), p.get("lon")
        elif record.source == "wikidata":
            wkt = p.get("location_wkt", "")
            match = re.search(r'Point\(([-0-9.]+)\s+([-0-9.]+)\)', wkt)
            if match:
                return float(match.group(2)), float(match.group(1))
        return None, None

    def _merge_cluster(self, cluster: List[RawSourceRecord], destination_id: str) -> Optional[CanonicalExperienceEntity]:
        """Merges a cluster of matched raw records into a single CanonicalExperienceEntity."""
        if not cluster:
            return None

        # Determine best canonical name
        gm_rec = next((r for r in cluster if r.source == "google_maps"), None)
        osm_rec = next((r for r in cluster if r.source == "osm"), None)
        wd_rec = next((r for r in cluster if r.source == "wikidata"), None)
        wp_rec = next((r for r in cluster if r.source == "wikipedia"), None)

        canonical_name = (
            (gm_rec and gm_rec.name_candidate) or
            (osm_rec and osm_rec.name_candidate) or
            (wd_rec and wd_rec.name_candidate) or
            cluster[0].name_candidate
        )

        # Sources present and IDs
        sources_present = list({r.source for r in cluster})
        source_ids = {r.source: str(r.source_id) for r in cluster}

        # Coordinates (prefer Google or OSM)
        lat, lon = None, None
        for r in [gm_rec, osm_rec, wd_rec]:
            if r:
                c_lat, c_lon = self._extract_coords(r)
                if c_lat is not None and c_lon is not None:
                    lat, lon = c_lat, c_lon
                    break

        # Rating & Reviews (from Google Maps)
        rating = None
        review_count = 0
        if gm_rec:
            rating = gm_rec.raw_payload.get("rating")
            review_count = gm_rec.raw_payload.get("review_count") or 0

        # Images (prefer Wikidata Commons / Wikipedia thumbnail)
        image_urls = []
        if wd_rec and wd_rec.raw_payload.get("image_url"):
            image_urls.append(wd_rec.raw_payload["image_url"])
        if wp_rec and wp_rec.raw_payload.get("thumbnail", {}).get("source"):
            image_urls.append(wp_rec.raw_payload["thumbnail"]["source"])

        # Description (from Wikipedia)
        description = None
        if wp_rec:
            description = wp_rec.raw_payload.get("extract")

        # Category classification
        category, subcategory = self._classify_category(cluster)

        # Confidence Score
        # 3+ sources -> 0.98 | 2 sources -> 0.85 | 1 source + reviews -> 0.75 | 1 source minimal -> 0.60
        src_count = len(sources_present)
        if src_count >= 3:
            confidence = 0.98
        elif src_count == 2:
            confidence = 0.85
        elif review_count > 100:
            confidence = 0.78
        else:
            confidence = 0.60

        # Safe unique entity_id
        slug = re.sub(r'[^a-zA-Z0-9]', '_', canonical_name.lower())[:30].strip('_')
        entity_id = f"exp_{destination_id.lower()}_{slug}"

        return CanonicalExperienceEntity(
            entity_id=entity_id,
            destination_id=destination_id,
            canonical_name=canonical_name,
            category=category,
            subcategory=subcategory,
            lat=lat,
            lon=lon,
            rating=rating,
            review_count=review_count,
            confidence_score=confidence,
            sources_present=sources_present,
            source_ids=source_ids,
            image_urls=image_urls,
            description=description,
            tags=self._generate_tags(cluster, category)
        )

    def _classify_category(self, cluster: List[RawSourceRecord]) -> Tuple[str, str]:
        """Infers high-level category and subcategory from tags across all cluster sources."""
        all_text = " ".join([
            r.name_candidate.lower() + " " + str(r.raw_payload) for r in cluster
        ]).lower()

        if any(w in all_text for w in ["beach", "spiaggia", "strand", "playa", "coast"]):
            return "beach_coastal", "public_beach"
        if any(w in all_text for w in ["viewpoint", "belvedere", "panorama", "cliff", "peak", "vista"]):
            return "nature_viewpoint", "viewpoint"
        if any(w in all_text for w in ["museum", "museo", "gallery", "pinacoteca"]):
            return "culture_history", "museum"
        if any(w in all_text for w in ["church", "chiesa", "cathedral", "cattedrale", "basilica", "san ", "santa "]):
            return "culture_history", "church_cathedral"
        if any(w in all_text for w in ["castle", "castello", "fortress", "palazzo", "sedile", "ruins"]):
            return "culture_history", "castle_fortress"
        if any(w in all_text for w in ["park", "parco", "garden", "giardino"]):
            return "nature_viewpoint", "park_garden"
        if any(w in all_text for w in ["market", "mercato", "food", "trattoria"]):
            return "food_market", "local_market"
        if any(w in all_text for w in ["boat", "tour", "cruise", "barca"]):
            return "active_adventure", "boat_tour"
        if any(w in all_text for w in ["theatre", "teatro", "opera"]):
            return "culture_history", "theatre"

        return "culture_history", "landmark"

    def _generate_tags(self, cluster: List[RawSourceRecord], category: str) -> List[str]:
        """Generates searchable behavioral tags for travel personas."""
        tags = [category]
        all_text = " ".join([r.name_candidate for r in cluster]).lower()
        if "unesco" in all_text or any("unesco" in str(r.raw_payload).lower() for r in cluster):
            tags.append("unesco_heritage")
        if "view" in all_text or "panorama" in all_text or "vista" in all_text:
            tags.append("scenic_views")
        if "beach" in all_text or "spiaggia" in all_text:
            tags.append("waterfront")
        return tags
