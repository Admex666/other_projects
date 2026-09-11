"""
Optivoya Experience Engine — Phase 4: Data Enrichment, Classification & Experience Modeling.
Transforms resolved canonical entities into rich, multidimensional travel experiences:
- Temporal & Duration Modeling (visit duration, optimal time of day)
- Environmental Modeling (indoor/outdoor, weather sensitivity)
- Price & Budget Categorization (free, budget, moderate, premium)
- Travel Persona Tagging (family, romantic, culture, solo, foodie)
- Experience Tiering (flagship, hidden gem, local lifestyle)
- Walkability & Proximity Graph (nearest neighbors within walking distance)
- Quality & Confidence Score Engine
"""
import math
from typing import List, Dict, Any, Optional
from collections import defaultdict

from .models import CanonicalExperienceEntity

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates distance between two coordinates in kilometers."""
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class ExperienceEnricher:
    def __init__(self, walk_radius_km: float = 0.5):
        self.walk_radius_km = walk_radius_km

    def enrich_entities(
        self,
        entities: List[CanonicalExperienceEntity],
        center_lat: float,
        center_lon: float
    ) -> List[CanonicalExperienceEntity]:
        """Enriches and models a full set of canonical experience entities for a destination."""
        # 1. Spatial indexing for walking proximity graph
        valid_coords = [e for e in entities if e.lat is not None and e.lon is not None]
        proximity_graph = defaultdict(list)
        for i, e1 in enumerate(valid_coords):
            for j, e2 in enumerate(valid_coords):
                if i != j:
                    dist = haversine_km(e1.lat, e1.lon, e2.lat, e2.lon)
                    if dist <= self.walk_radius_km:
                        proximity_graph[e1.entity_id].append({
                            "entity_id": e2.entity_id,
                            "name": e2.canonical_name,
                            "dist_m": int(dist * 1000)
                        })

        enriched: List[CanonicalExperienceEntity] = []
        for e in entities:
            # A. Distance from destination center
            dist_center = None
            if e.lat is not None and e.lon is not None:
                dist_center = round(haversine_km(center_lat, center_lon, e.lat, e.lon), 2)

            # B. Temporal & Environmental Modeling
            duration = self._infer_duration(e)
            best_time = self._infer_best_time(e)
            indoor_outdoor = self._infer_indoor_outdoor(e)
            weather_sensitivity = self._infer_weather_sensitivity(indoor_outdoor, e)

            # C. Price Level Modeling
            price_level = self._infer_price_level(e)

            # D. Persona Tagging & Experience Type
            persona_tags = self._generate_persona_tags(e, indoor_outdoor)
            exp_type = self._classify_experience_type(e)

            # E. Confidence & Quality Tier Engine
            conf_score, quality_tier = self._calculate_quality_confidence(e)

            # F. Nearest neighbors for walking circuits
            neighbors = sorted(proximity_graph.get(e.entity_id, []), key=lambda x: x["dist_m"])[:5]

            # Update entity fields
            e.est_duration_hours = duration
            e.best_time_of_day = best_time
            e.price_level = price_level
            e.confidence_score = conf_score

            # Combine tags
            combined_tags = list(set(e.tags + persona_tags + [exp_type, f"tier_{quality_tier}", indoor_outdoor]))
            e.tags = sorted(combined_tags)

            # Store rich modeling attributes in metadata
            e.metadata.update({
                "indoor_outdoor": indoor_outdoor,
                "weather_sensitivity": weather_sensitivity,
                "quality_tier": quality_tier,
                "experience_type": exp_type,
                "persona_tags": persona_tags,
                "distance_center_km": dist_center,
                "walkable_neighbors_count": len(neighbors),
                "nearby_walkable_entities": neighbors
            })

            enriched.append(e)

        return enriched

    def _infer_duration(self, e: CanonicalExperienceEntity) -> float:
        """Estimates realistic visit duration in hours based on category and subcategory."""
        cat = e.category
        sub = e.subcategory or ""
        name = e.canonical_name.lower()

        if cat == "beach_coastal" or "beach" in sub:
            return 3.5
        elif cat == "active_adventure" or "boat" in name or "tour" in name:
            return 2.5
        elif "museum" in sub or "gallery" in sub:
            return 2.0
        elif "castle" in sub or "fortress" in sub:
            return 1.5
        elif "cathedral" in sub or "church" in sub or "basilica" in name:
            return 1.0
        elif cat == "nature_viewpoint" and "viewpoint" in sub:
            return 0.5
        elif "park" in sub or "garden" in sub:
            return 1.2
        elif cat == "food_market" or "market" in sub:
            return 1.0
        return 1.0

    def _infer_best_time(self, e: CanonicalExperienceEntity) -> str:
        """Determines ideal visit slot (morning, afternoon, sunset, evening, anytime)."""
        name = e.canonical_name.lower()
        sub = (e.subcategory or "").lower()
        cat = e.category

        if "viewpoint" in sub or "panorama" in name or "belvedere" in name:
            return "sunset"
        elif "lungomare" in name or "promenade" in name:
            return "sunset"
        elif cat == "beach_coastal":
            return "morning"  # Best water clarity, less crowd
        elif cat == "food_market" or "market" in name:
            return "morning"  # Fresh produce and active local trade
        elif "museum" in sub or "gallery" in sub:
            return "afternoon"  # Escape heat or afternoon leisure
        elif "piazza" in name or "albicocca" in name or "sedile" in name:
            return "evening"  # Lively evening aperitivo atmosphere
        return "anytime"

    def _infer_indoor_outdoor(self, e: CanonicalExperienceEntity) -> str:
        """Classifies place as indoor, outdoor, or mixed."""
        sub = (e.subcategory or "").lower()
        cat = e.category
        name = e.canonical_name.lower()

        if cat in ["beach_coastal", "nature_viewpoint"] or any(w in sub for w in ["beach", "viewpoint", "park", "garden"]):
            return "outdoor"
        if any(w in sub for w in ["museum", "gallery", "theatre"]) or any(w in name for w in ["teatro", "pinacoteca", "museo"]):
            return "indoor"
        if "church" in sub or "cathedral" in sub or "basilica" in name:
            return "indoor"
        if "castle" in sub or "fortress" in sub:
            return "mixed"
        if "market" in sub:
            return "mixed"
        return "outdoor"

    def _infer_weather_sensitivity(self, indoor_outdoor: str, e: CanonicalExperienceEntity) -> str:
        """Determines weather resilience."""
        if indoor_outdoor == "indoor":
            return "rain_safe"
        elif e.category == "beach_coastal" or "boat" in e.canonical_name.lower():
            return "sun_dependent"
        elif indoor_outdoor == "outdoor":
            return "fair_weather"
        return "all_weather"

    def _infer_price_level(self, e: CanonicalExperienceEntity) -> str:
        """Infers standard price bracket."""
        name = e.canonical_name.lower()
        sub = (e.subcategory or "").lower()
        cat = e.category

        if cat == "beach_coastal" and "libera" in name:
            return "free"
        if cat == "nature_viewpoint" or "viewpoint" in sub or "park" in sub:
            return "free"
        if "monument" in sub or "plaza" in sub or "fountain" in sub:
            return "free"
        if "church" in sub or "cathedral" in sub:
            return "free"  # Most public basilicas have free admission
        if cat == "active_adventure" or "tour" in name or "boat" in name:
            return "premium"
        if "museum" in sub or "castle" in sub:
            return "budget"  # Italian civic museums usually 5-10 EUR
        return "moderate"

    def _generate_persona_tags(self, e: CanonicalExperienceEntity, indoor_outdoor: str) -> List[str]:
        """Maps attributes to traveler personas."""
        personas = []
        name = e.canonical_name.lower()
        sub = (e.subcategory or "").lower()
        cat = e.category

        # Family friendly
        if "park" in sub or "garden" in sub or "playa" in name or "spiaggia" in name:
            personas.append("family_friendly")

        # Romantic / Couples
        if any(w in name for w in ["innamorati", "lungomare", "belvedere", "panorama", "vista"]) or "viewpoint" in sub:
            personas.append("couples_romantic")

        # Culture Aficionado
        if cat == "culture_history" or any(w in sub for w in ["church", "cathedral", "castle", "museum", "ruins"]):
            personas.append("culture_aficionado")

        # Solo Explorer
        if cat in ["nature_viewpoint", "food_market"] or indoor_outdoor == "outdoor":
            personas.append("solo_explorer")

        # Foodie & Local Vibe
        if cat == "food_market" or any(w in name for w in ["mercato", "food", "pescheria", "orecchiette"]):
            personas.append("foodie_local")

        # Beach & Sun Seeker
        if cat == "beach_coastal":
            personas.append("beach_seeker")

        return personas

    def _classify_experience_type(self, e: CanonicalExperienceEntity) -> str:
        """Classifies place as flagship, hidden gem, or local lifestyle."""
        revs = e.review_count or 0
        rating = e.rating or 0.0

        if revs >= 2000 or (e.confidence_score >= 0.85 and revs >= 500):
            return "must_see_flagship"
        elif rating >= 4.5 and revs < 500:
            return "hidden_gem"
        elif e.category == "food_market" or "mercato" in e.canonical_name.lower():
            return "local_lifestyle"
        return "regular_attraction"

    def _calculate_quality_confidence(self, e: CanonicalExperienceEntity) -> (float, str):
        """Calculates multi-factor confidence score and assigns tier."""
        score = 0.0

        # Corroboration (sources count)
        src_count = len(e.sources_present)
        if src_count >= 3:
            score += 0.40
        elif src_count == 2:
            score += 0.28
        else:
            score += 0.12

        # Social validation
        revs = e.review_count or 0
        if revs >= 5000:
            score += 0.35
        elif revs >= 1000:
            score += 0.28
        elif revs >= 200:
            score += 0.20
        elif revs >= 20:
            score += 0.10

        if (e.rating or 0.0) >= 4.5:
            score += 0.08

        # Metadata completeness
        if e.lat is not None and e.lon is not None:
            score += 0.07
        if e.image_urls and len(e.image_urls) > 0:
            score += 0.05
        if e.description:
            score += 0.05

        final_score = min(round(score, 2), 0.99)

        if final_score >= 0.80:
            quality_tier = "flagship"
        elif final_score >= 0.60:
            quality_tier = "recommended"
        else:
            quality_tier = "supplemental"

        return final_score, quality_tier
