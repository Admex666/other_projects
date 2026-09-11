"""
Optivoya Vibe Profiling Engine - Experience Vector & Robust Normalization.

Implements the multi-dimensional destination character scoring system:
  - ExperienceVectorCalculator: feature-based absolute scores (0-100) from OSM categories,
    ratings, review counts, price levels, tags, and metadata.
  - BayesianShrinker: shrinks scores toward peer-group prior for low-data destinations.
  - RobustZScoreNormalizer: MAD-based normalization per peer group (handles Paris/Ibiza outliers).
  - VibeSummarizer: derives natural-language Hungarian mood summaries and badge labels.

Design invariants:
  - NO LLM hallucination: every score is derived from objective feature data.
  - Low data density -> lower confidence, not lower score (Bayesian shrinkage handles this).
  - Hidden gem is a derived metric, never a raw input.
  - All statistical internals are hidden from the user; only human-readable summaries surface.
"""
from __future__ import annotations

import json
import math
import os
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .models import CanonicalExperienceEntity

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BAYESIAN_K = 15  # n / (n + K): K=15 means 15 data points = 50% trust

_DEFAULT_PRIOR: Dict[str, float] = {
    "culture": 50.0, "food": 50.0, "beach": 20.0, "nature": 40.0,
    "nightlife": 35.0, "romance": 45.0, "authenticity": 50.0,
    "locality": 50.0, "walkability": 50.0, "tourist_intensity": 40.0,
    "adventure": 30.0, "family": 45.0,
}

# Category -> vibe dimensions mapping  (dimension, weight_contribution)
_CATEGORY_DIMENSION_MAP: Dict[str, List[Tuple[str, float]]] = {
    "culture_history":     [("culture", 1.0), ("romance", 0.3), ("locality", 0.2)],
    "food_market":         [("food", 1.0), ("locality", 0.5), ("authenticity", 0.4)],
    "beach_coastal":       [("beach", 1.0), ("nature", 0.3), ("romance", 0.2)],
    "nature_viewpoint":    [("nature", 1.0), ("adventure", 0.4), ("romance", 0.3)],
    "active_adventure":    [("adventure", 1.0), ("nature", 0.3), ("family", 0.2)],
    "wellness_spa":        [("romance", 0.5), ("walkability", 0.2)],
    "nightlife_bar":       [("nightlife", 1.0), ("food", 0.2)],
    "shopping":            [("locality", 0.4), ("tourist_intensity", 0.3)],
    "family_kids":         [("family", 1.0), ("walkability", 0.2)],
    "religious_spiritual": [("culture", 0.6), ("authenticity", 0.3)],
    "local_life":          [("locality", 1.0), ("authenticity", 0.8), ("food", 0.2)],
}

_SUBCATEGORY_BOOSTS: Dict[str, List[Tuple[str, float]]] = {
    "street_food":        [("authenticity", 0.6), ("food", 0.4), ("locality", 0.3)],
    "traditional_market": [("authenticity", 0.7), ("locality", 0.5)],
    "historic_quarter":   [("culture", 0.5), ("authenticity", 0.4), ("romance", 0.3)],
    "rooftop_bar":        [("nightlife", 0.4), ("romance", 0.3)],
    "hidden_beach":       [("beach", 0.5), ("authenticity", 0.4)],
    "vineyard":           [("food", 0.4), ("nature", 0.3), ("romance", 0.2)],
    "local_restaurant":   [("food", 0.5), ("authenticity", 0.4), ("locality", 0.3)],
}

_CHAIN_KEYWORDS = {
    "mcdonald", "starbucks", "burger king", "subway", "h&m", "zara",
    "primark", "five guys", "kfc", "spar", "billa", "lidl", "aldi",
    "sheraton", "hilton", "marriott", "hyatt", "radisson", "ibis",
}

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DimensionScore:
    absolute: float          # 0-100: Bayesian-smoothed
    relative_z: float        # -3..+3: robust Z-score vs peer group
    confidence: float        # 0.0-1.0: data density + source diversity
    freshness: float         # 0.0-1.0: recency
    raw_signal: float = 0.0  # pre-Bayes observed signal (internal)
    n_signals: int = 0       # contributing data points


@dataclass
class ExperienceVector:
    destination_id: str
    city_name: str
    country: str
    dimensions: Dict[str, DimensionScore] = field(default_factory=dict)
    hidden_gem_score: float = 0.0
    overall_fit: float = 0.0
    vibe_summary: str = ""
    top_dimensions: List[str] = field(default_factory=list)
    peer_group: str = "european_all"
    total_entities: int = 0
    data_confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "destination_id": self.destination_id,
            "city_name": self.city_name,
            "country": self.country,
            "peer_group": self.peer_group,
            "total_entities": self.total_entities,
            "data_confidence": round(self.data_confidence, 3),
            "hidden_gem_score": round(self.hidden_gem_score, 1),
            "vibe_summary": self.vibe_summary,
            "top_dimensions": self.top_dimensions,
            "overall_fit": round(self.overall_fit, 1),
            "dimensions": {
                k: {
                    "absolute": round(v.absolute, 1),
                    "relative_z": round(v.relative_z, 2),
                    "confidence": round(v.confidence, 3),
                    "freshness": round(v.freshness, 3),
                }
                for k, v in self.dimensions.items()
            },
        }


# ---------------------------------------------------------------------------
# 1. ExperienceVectorCalculator
# ---------------------------------------------------------------------------

class ExperienceVectorCalculator:
    """
    Builds raw (pre-normalization) dimension scores from canonical entities.
    Each entity contributes weighted signals based on category, subcategory,
    tags, rating, review count, and enrichment metadata.
    """

    def calculate(
        self,
        entities: List[CanonicalExperienceEntity],
        destination_id: str,
        city_name: str,
        country: str,
        freshness: float = 1.0,
    ) -> ExperienceVector:
        dim_signals: Dict[str, List[float]] = {k: [] for k in _DEFAULT_PRIOR}
        source_sets: Dict[str, set] = {k: set() for k in _DEFAULT_PRIOR}
        chain_count = 0
        local_count = 0
        total = len(entities)

        for entity in entities:
            cat = entity.category or ""
            subcat = entity.subcategory or ""
            tags = [t.lower() for t in (entity.tags or [])]
            name_lower = entity.canonical_name.lower()
            rating = entity.rating or 4.0
            review_count = entity.review_count or 0
            sources = set(entity.sources_present or [])
            meta = entity.metadata or {}

            # Quality multiplier: rating 1-5 -> 0.4-1.2
            quality_mult = 0.4 + (max(0.0, min(5.0, rating)) / 5.0) * 0.8
            # Popularity multiplier: log-scale of review count
            pop_mult = 1.0 + math.log10(max(review_count, 1)) * 0.15
            combined_mult = quality_mult * pop_mult

            is_chain = any(kw in name_lower for kw in _CHAIN_KEYWORDS)
            is_local = meta.get("is_local_independent", False) or ("local" in tags)
            if is_chain:
                chain_count += 1
            if is_local:
                local_count += 1

            # Category contributions
            for dim, weight in _CATEGORY_DIMENSION_MAP.get(cat, []):
                dim_signals[dim].append(weight * combined_mult * 10.0)
                source_sets[dim] |= sources

            # Subcategory boosts
            for dim, weight in _SUBCATEGORY_BOOSTS.get(subcat, []):
                dim_signals[dim].append(weight * combined_mult * 6.0)

            # Tag-level signals
            if "romantic" in tags or "couples" in tags:
                dim_signals["romance"].append(combined_mult * 5.0)
            if "family" in tags or "kids" in tags:
                dim_signals["family"].append(combined_mult * 5.0)
            if "hiking" in tags or "adventure" in tags:
                dim_signals["adventure"].append(combined_mult * 5.0)
            if "nightclub" in tags or "bar" in tags:
                dim_signals["nightlife"].append(combined_mult * 4.0)

            # Walkability from enrichment proximity
            walk_neighbors = meta.get("walkable_neighbors_count", 0)
            if walk_neighbors >= 2:
                dim_signals["walkability"].append(walk_neighbors * 2.5)

            # Persona tags
            for ptag in meta.get("persona_tags", []):
                if ptag in ("culture_aficionado", "solo_explorer"):
                    dim_signals["authenticity"].append(combined_mult * 3.0)
                if ptag == "foodie_local":
                    dim_signals["locality"].append(combined_mult * 4.0)
                    dim_signals["food"].append(combined_mult * 3.0)

        # Tourist intensity: avg review volume + chain density
        avg_review = statistics.mean([e.review_count or 0 for e in entities]) if entities else 0
        tourist_signal = math.log10(max(avg_review, 1)) * 8.0
        tourist_chain_bonus = (chain_count / max(total, 1)) * 20.0
        dim_signals["tourist_intensity"].append(tourist_signal + tourist_chain_bonus)

        # Authenticity / locality: chain vs local ratio
        chain_ratio = chain_count / max(total, 1)
        local_ratio = local_count / max(total, 1)
        dim_signals["authenticity"].append((local_ratio - chain_ratio * 1.5) * 25.0 + 30.0)
        dim_signals["locality"].append(local_ratio * 30.0 + 20.0)

        # Build DimensionScore objects
        dimensions: Dict[str, DimensionScore] = {}
        confidence_vals = []

        for dim, signals in dim_signals.items():
            n = len(signals)
            raw = min(100.0, max(0.0, statistics.mean(signals))) if n > 0 else 0.0
            src_diversity = len(source_sets.get(dim, set())) / 3.0
            count_confidence = n / (n + BAYESIAN_K) if n > 0 else 0.0
            confidence = round(min(1.0, src_diversity * 0.4 + count_confidence * 0.6), 3)
            confidence_vals.append(confidence)

            dimensions[dim] = DimensionScore(
                absolute=raw,
                relative_z=0.0,
                confidence=confidence,
                freshness=freshness,
                raw_signal=raw,
                n_signals=n,
            )

        overall_confidence = round(statistics.mean(confidence_vals), 3) if confidence_vals else 0.5

        return ExperienceVector(
            destination_id=destination_id,
            city_name=city_name,
            country=country,
            dimensions=dimensions,
            total_entities=total,
            data_confidence=overall_confidence,
        )


# ---------------------------------------------------------------------------
# 2. BayesianShrinker
# ---------------------------------------------------------------------------

class BayesianShrinker:
    """
    Applies Bayesian shrinkage: w(n) = n/(n+K)
    score_bayes = w(n) * score_observed + (1 - w(n)) * prior
    """

    def __init__(self, k: int = BAYESIAN_K, priors: Optional[Dict[str, float]] = None):
        self.k = k
        self.priors = priors or _DEFAULT_PRIOR.copy()

    def shrink(self, vector: ExperienceVector) -> ExperienceVector:
        for dim, ds in vector.dimensions.items():
            # If there are NO signals at all, keep the score at 0 (no data = no claim)
            if ds.n_signals == 0:
                ds.absolute = 0.0
                continue
            n = max(ds.n_signals, 1)
            w = n / (n + self.k)
            prior = self.priors.get(dim, 50.0)
            ds.absolute = round(w * ds.raw_signal + (1 - w) * prior, 2)
        return vector


# ---------------------------------------------------------------------------
# 3. RobustZScoreNormalizer
# ---------------------------------------------------------------------------

class RobustZScoreNormalizer:
    """
    Computes robust Z-scores using Median Absolute Deviation (MAD).
    z_robust = (x - median) / (1.4826 * MAD)
    Resistant to Paris/Ibiza-style outliers.
    """

    def __init__(self, peer_groups: Optional[Dict[str, List[str]]] = None):
        self._peer_groups = peer_groups or {}
        self._group_stats: Dict[str, Dict[str, Tuple[float, float]]] = {}

    def fit(self, vectors: List[ExperienceVector], group_name: str = "european_all") -> None:
        dim_values: Dict[str, List[float]] = {k: [] for k in _DEFAULT_PRIOR}
        for vec in vectors:
            for dim, ds in vec.dimensions.items():
                dim_values[dim].append(ds.absolute)

        stats: Dict[str, Tuple[float, float]] = {}
        for dim, vals in dim_values.items():
            if len(vals) < 2:
                stats[dim] = (50.0, 10.0)
                continue
            med = statistics.median(vals)
            mad = statistics.median([abs(v - med) for v in vals])
            if mad == 0:
                mad = 1.0
            stats[dim] = (med, mad)

        self._group_stats[group_name] = stats

    def transform(self, vector: ExperienceVector, group_name: str = "european_all") -> ExperienceVector:
        stats = self._group_stats.get(group_name, {})
        for dim, ds in vector.dimensions.items():
            if dim in stats:
                med, mad = stats[dim]
                z = (ds.absolute - med) / (1.4826 * mad)
                ds.relative_z = round(max(-3.0, min(3.0, z)), 3)
            else:
                ds.relative_z = 0.0
        vector.peer_group = group_name
        return vector

    @classmethod
    def from_peer_groups_file(cls, path: str) -> "RobustZScoreNormalizer":
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(peer_groups=data.get("groups", {}))
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()


# ---------------------------------------------------------------------------
# 4. HiddenGemCalculator
# ---------------------------------------------------------------------------

class HiddenGemCalculator:
    """
    Derived metric only - never a raw input.
    HiddenGem = Authenticity x Locality x Quality x (1 - TouristIntensity) x pop_correction
    """

    def calculate(self, vector: ExperienceVector) -> float:
        dims = vector.dimensions
        auth  = dims.get("authenticity",      DimensionScore(50, 0, 0.5, 1.0)).absolute / 100.0
        local = dims.get("locality",          DimensionScore(50, 0, 0.5, 1.0)).absolute / 100.0
        quality_vals = [
            dims.get("culture",  DimensionScore(50, 0, 0.5, 1.0)).absolute,
            dims.get("food",     DimensionScore(50, 0, 0.5, 1.0)).absolute,
            dims.get("nature",   DimensionScore(50, 0, 0.5, 1.0)).absolute,
        ]
        quality = statistics.mean(quality_vals) / 100.0
        tourist = dims.get("tourist_intensity", DimensionScore(40, 0, 0.5, 1.0)).absolute / 100.0
        pop_correction = 1.0 - min(1.0, vector.total_entities / 300.0) * 0.4
        raw = auth * local * quality * max(0.0, 1.0 - tourist) * pop_correction
        return round(raw * 100.0, 1)


# ---------------------------------------------------------------------------
# 5. VibeSummarizer
# ---------------------------------------------------------------------------

class VibeSummarizer:
    """
    Generates natural-language Hungarian vibe summaries and badge labels.
    No LLM: purely rule-based from dimension ranks and Z-scores.
    """

    _DIM_HU: Dict[str, str] = {
        "culture": "Kultúra", "food": "Gasztronómia", "beach": "Tengerpart",
        "nature": "Természet", "nightlife": "Ejszakai elet", "romance": "Romantika",
        "authenticity": "Autentikussag", "locality": "Helyi eleterzs",
        "walkability": "Gyalogosbarat", "tourist_intensity": "Turisztikai forgalom",
        "adventure": "Kaland", "family": "Csaladbarat",
    }

    _ADJECTIVES: Dict[str, List[str]] = {
        "culture":      ["kulturaban gazdag", "kulturalis", "muemlekes"],
        "food":         ["gasztro-fokuszu", "kulinaris", "gasztronomial"],
        "beach":        ["tengerparti", "strandos", "tengerkoeli"],
        "nature":       ["termeszetkoeli", "zoeldoevezetes", "panoramas"],
        "nightlife":    ["pezsgo ejszakai eletu", "baros", "elenk"],
        "romance":      ["romantikus", "hangulatos", "festoi"],
        "authenticity": ["autentikus", "eredeti karakteru", "hamisitaatlan"],
        "locality":     ["eros helyi karakteru", "helyi eleterzsu", "valodi"],
        "adventure":    ["kalandos", "aktiv"],
        "family":       ["csaladbarat"],
    }

    def summarize(self, vector: ExperienceVector) -> str:
        dims = vector.dimensions
        sorted_dims = sorted(
            [(d, ds.absolute) for d, ds in dims.items() if d != "tourist_intensity"],
            key=lambda x: x[1], reverse=True,
        )
        top3 = [d for d, _ in sorted_dims[:3]]
        adjs = []
        for dim in top3:
            adj_list = self._ADJECTIVES.get(dim, [])
            if adj_list:
                adjs.append(adj_list[0])

        city = vector.city_name
        country = vector.country

        if len(adjs) >= 2:
            summary = f"{city}: {adjs[0]}, {adjs[1]} {country}i varos"
            if len(adjs) == 3:
                summary += f" - {adjs[2]} karakterrel"
        elif len(adjs) == 1:
            summary = f"{city}: {adjs[0]} {country}i varos"
        else:
            summary = f"{city}: jellegzetes {country}i uti cel"
        return summary

    def top_dimensions(self, vector: ExperienceVector, n: int = 3) -> List[str]:
        return [
            d for d, _ in sorted(
                [(d, ds.absolute) for d, ds in vector.dimensions.items()
                 if d != "tourist_intensity"],
                key=lambda x: x[1], reverse=True,
            )[:n]
        ]

    def badge_labels(self, vector: ExperienceVector, z_threshold: float = 0.8) -> List[Dict[str, Any]]:
        badges = []
        for dim, ds in vector.dimensions.items():
            if dim == "tourist_intensity":
                continue
            if ds.relative_z >= z_threshold:
                label = "kiemelkedo" if ds.relative_z >= 1.5 else "eros"
                badges.append({
                    "dim": dim,
                    "label_hu": self._DIM_HU.get(dim, dim),
                    "badge": f"{self._DIM_HU.get(dim, dim)}: +{ds.relative_z:.1f}s {label}",
                    "z": ds.relative_z,
                    "absolute": ds.absolute,
                })
        return sorted(badges, key=lambda b: b["z"], reverse=True)

    def fit_score(self, vector: ExperienceVector, user_preferences: Dict[str, float]) -> float:
        """Personalized Fit Score (0-100): user preference weighted dot product."""
        total_w = sum(max(0.0, w) for w in user_preferences.values())
        if total_w == 0:
            return 50.0
        fit = sum(
            max(0.0, user_preferences.get(dim, 0.0)) * ds.absolute
            for dim, ds in vector.dimensions.items()
        ) / total_w
        return round(min(100.0, fit), 1)


# ---------------------------------------------------------------------------
# 6. VibeEngine (facade)
# ---------------------------------------------------------------------------

class VibeEngine:
    """
    High-level facade for the full vibe profiling pipeline.

    Single destination:
        engine = VibeEngine()
        vector = engine.profile(entities, destination_id, city_name, country)

    Batch peer-group normalization:
        vectors = [engine.profile(...) for ...]
        engine.normalize_peer_group(vectors, group_name="mediterranean_coastal")
    """

    def __init__(
        self,
        peer_groups_file: Optional[str] = None,
        bayesian_k: int = BAYESIAN_K,
    ):
        self._calculator = ExperienceVectorCalculator()
        self._shrinker = BayesianShrinker(k=bayesian_k)
        self._hidden_gem = HiddenGemCalculator()
        self._summarizer = VibeSummarizer()
        self._normalizer = RobustZScoreNormalizer.from_peer_groups_file(
            peer_groups_file or _default_peer_groups_path()
        )

    def profile(
        self,
        entities: List[CanonicalExperienceEntity],
        destination_id: str,
        city_name: str,
        country: str,
        freshness: float = 1.0,
        user_preferences: Optional[Dict[str, float]] = None,
    ) -> ExperienceVector:
        vector = self._calculator.calculate(entities, destination_id, city_name, country, freshness)
        vector = self._shrinker.shrink(vector)
        vector.hidden_gem_score = self._hidden_gem.calculate(vector)
        vector.top_dimensions = self._summarizer.top_dimensions(vector)
        vector.vibe_summary = self._summarizer.summarize(vector)
        if user_preferences:
            vector.overall_fit = self._summarizer.fit_score(vector, user_preferences)
        return vector

    def normalize_peer_group(
        self,
        vectors: List[ExperienceVector],
        group_name: str = "european_all",
    ) -> List[ExperienceVector]:
        self._normalizer.fit(vectors, group_name)
        return [self._normalizer.transform(v, group_name) for v in vectors]

    def badges(self, vector: ExperienceVector, z_threshold: float = 0.8) -> List[Dict[str, Any]]:
        return self._summarizer.badge_labels(vector, z_threshold)

    def fit_score(self, vector: ExperienceVector, user_preferences: Dict[str, float]) -> float:
        score = self._summarizer.fit_score(vector, user_preferences)
        vector.overall_fit = score
        return score


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _default_peer_groups_path() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "..", "..", "data", "peer_groups.json")


_engine: Optional[VibeEngine] = None


def get_vibe_engine() -> VibeEngine:
    """Returns the module-level shared VibeEngine instance."""
    global _engine
    if _engine is None:
        _engine = VibeEngine()
    return _engine
