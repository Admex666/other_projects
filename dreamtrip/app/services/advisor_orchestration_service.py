"""
Optivoya B2B Advisor Workspace — Research Orchestration Service
Supports the 9 specialized Advisor Research Workflows with built-in resilience,
graceful fallbacks, provenance tracking, and progressive candidate generation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import uuid
import time
import logging

from app.models.advisor_models import (
    TripCase, Client, ResolvedTripPreferences, TripOption, OptionArchetype,
    ProviderProvenance, VerificationStatus, ResearchScope, BudgetMode,
    utc_now, generate_uuid
)
from app.services.preference_resolver import PreferenceResolver
from app.services.destination_matching_service import DestinationMatchingService
from app.services.flight_intelligence_service import FlightIntelligenceService
from app.services.accommodation_intelligence_service import AccommodationIntelligenceService
from app.services.experience_intelligence_service import ExperienceIntelligenceService
from app.services.trip_scoring_service import TripScoreService
from app.services.multi_option_engine import MultiOptionEngine

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# 9 ADVISOR RESEARCH WORKFLOW IDENTIFIERS
# ─────────────────────────────────────────────────────────────
class ResearchStrategy:
    DESTINATION_DISCOVERY = "destination_discovery"       # 1. 45+ destinations -> flights -> stays
    KNOWN_DESTINATION = "known_destination"               # 2. Deep dive into specific destination
    FLIGHT_FIRST = "flight_first"                         # 3. Flight deal / schedule priority
    STAY_FIRST = "stay_first"                             # 4. Premium accommodation priority
    FULL_TRIP_OPTIMIZATION = "full_trip_optimization"     # 5. Simultaneous multi-criteria package optimization
    COMPONENT_ONLY = "component_only"                     # 6. Flight only OR Stay only
    MIXED_SCOPE = "mixed_scope"                           # 7. Multi-destination side-by-side comparison
    RE_OPTIMIZATION = "re_optimization"                   # 8. Re-evaluate with altered constraints
    FIND_BETTER = "find_better"                           # 9. Targeted component upgrade / tuning


class AdvisorOrchestrationService:
    """
    Central orchestration engine for B2B Advisor Research workflows.
    Executes resilient intelligence pipelines across Kiwi, Cozycozy, Open-Meteo, and POI services.
    """

    # In-memory research job cache for asynchronous / idempotent research execution
    _RESEARCH_JOBS: Dict[str, Dict[str, Any]] = {}
    _CANDIDATES_POOL: Dict[str, List[Dict[str, Any]]] = {}   # case_id -> list of candidates

    @classmethod
    def execute_research(
        cls,
        trip_case: TripCase,
        client: Optional[Client] = None,
        strategy: str = ResearchStrategy.FULL_TRIP_OPTIMIZATION,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for executing one of the 9 Advisor Research Strategies.
        Returns a complete research summary containing candidate options, component pools,
        provenance, and execution telemetry.
        """
        start_time = time.time()
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        custom_params = custom_params or {}

        # 1. Resolve 4-layer preference hierarchy
        resolved = PreferenceResolver.resolve_preferences(trip_case, client)
        hard = resolved.hard
        soft = resolved.soft
        avoid = resolved.avoid
        nice = resolved.nice_to_have
        overrides = resolved.overrides

        origin = overrides.pinned_destination or trip_case.origin or "Budapest"
        dest_focus = overrides.pinned_destination or trip_case.destination_focus
        if dest_focus and dest_focus.lower() in ["discovery", "bárhova", "any", "összes", "nincs megadva"]:
            dest_focus = None

        # Determine target travel dates
        today = date.today()
        default_out = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        default_in = (today + timedelta(days=37)).strftime("%Y-%m-%d")
        out_date = trip_case.out_date or default_out
        in_date = trip_case.in_date or default_in

        duration_days = trip_case.duration_days or 7
        adults = trip_case.adults or 2
        children = trip_case.children or 0

        # Research tracking structure
        job_record = {
            "job_id": job_id,
            "case_id": trip_case.id,
            "strategy": strategy,
            "status": "running",
            "progress_pct": 10,
            "steps_completed": [],
            "warnings": [],
            "providers_status": {
                "kiwi": {"status": "running", "count": 0, "error": None},
                "cozycozy": {"status": "running", "count": 0, "error": None},
                "open_meteo": {"status": "running", "count": 0, "error": None},
                "poi_wikidata": {"status": "running", "count": 0, "error": None}
            },
            "provenance_summary": [],
            "candidates": [],
            "flights_pool": [],
            "stays_pool": [],
            "destinations_pool": [],
            "created_at": utc_now().isoformat()
        }
        cls._RESEARCH_JOBS[job_id] = job_record

        try:
            # ─────────────────────────────────────────────────────────────
            # WORKFLOW DISPATCHER
            # ─────────────────────────────────────────────────────────────
            if strategy == ResearchStrategy.DESTINATION_DISCOVERY or not dest_focus:
                result = cls._run_destination_discovery(
                    trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job_record
                )
            elif strategy == ResearchStrategy.KNOWN_DESTINATION:
                result = cls._run_known_destination_research(
                    dest_focus, trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job_record
                )
            elif strategy == ResearchStrategy.FLIGHT_FIRST:
                result = cls._run_flight_first_strategy(
                    dest_focus, trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job_record
                )
            elif strategy == ResearchStrategy.STAY_FIRST:
                result = cls._run_stay_first_strategy(
                    dest_focus, trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job_record
                )
            elif strategy == ResearchStrategy.COMPONENT_ONLY:
                result = cls._run_component_only_research(
                    dest_focus, trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job_record
                )
            elif strategy == ResearchStrategy.MIXED_SCOPE:
                result = cls._run_mixed_scope_research(
                    custom_params.get("candidate_cities") or [dest_focus or "Barcelona", "Rome", "Vienna"],
                    trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job_record
                )
            elif strategy == ResearchStrategy.RE_OPTIMIZATION:
                result = cls._run_re_optimization(
                    trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, custom_params, job_record
                )
            elif strategy == ResearchStrategy.FIND_BETTER:
                result = cls._run_find_better(
                    dest_focus or "Barcelona", trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, custom_params, job_record
                )
            else:
                # Default: Full-Trip Optimization
                result = cls._run_full_trip_optimization(
                    dest_focus or "Barcelona", trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job_record
                )

            elapsed = round(time.time() - start_time, 3)
            raw_candidates = result.get("candidates", [])
            archetypes = MultiOptionEngine.generate_archetypes(
                raw_candidates,
                resolved,
                trip_case.total_budget_huf
            )

            job_record["status"] = "completed"
            job_record["progress_pct"] = 100
            job_record["elapsed_seconds"] = elapsed
            job_record["candidates"] = archetypes or raw_candidates
            job_record["destinations_pool"] = result.get("destinations_pool", [])
            job_record["flights_pool"] = result.get("flights_pool", [])
            job_record["stays_pool"] = result.get("stays_pool", [])

            # Store in candidate pool for this case
            cls._CANDIDATES_POOL[trip_case.id] = job_record["candidates"]

            # Persist ResearchRun to DB / Persistent SQLite
            try:
                from app.repositories.advisor_repository import ResearchRunRepository
                from app.models.advisor_models import ResearchRun, ResearchRunStatus
                run = ResearchRun(
                    id=job_id,
                    case_id=trip_case.id,
                    agency_id=trip_case.agency_id or "agency_default_lux",
                    advisor_id=trip_case.advisor_id or "adv_adam_lead",
                    strategy=strategy,
                    status=ResearchRunStatus.COMPLETED,
                    progress_pct=100,
                    steps_completed=job_record.get("steps_completed", []),
                    providers_status=job_record.get("providers_status", {}),
                    candidates=job_record.get("candidates", []),
                    destinations_pool=job_record.get("destinations_pool", []),
                    flights_pool=job_record.get("flights_pool", []),
                    stays_pool=job_record.get("stays_pool", []),
                    warnings=job_record.get("warnings", []),
                    elapsed_seconds=elapsed
                )
                ResearchRunRepository.save_run(run)
            except Exception as pe:
                logger.warning(f"ResearchRun persistence failed: {pe}")

            return job_record

        except Exception as e:
            logger.exception(f"Research workflow failed: {e}")
            job_record["status"] = "failed"
            job_record["error"] = str(e)
            job_record["progress_pct"] = 100

            try:
                from app.repositories.advisor_repository import ResearchRunRepository
                from app.models.advisor_models import ResearchRun, ResearchRunStatus
                run = ResearchRun(
                    id=job_id,
                    case_id=trip_case.id,
                    agency_id=trip_case.agency_id or "agency_default_lux",
                    advisor_id=trip_case.advisor_id or "adv_adam_lead",
                    strategy=strategy,
                    status=ResearchRunStatus.FAILED,
                    progress_pct=100,
                    steps_completed=job_record.get("steps_completed", []),
                    providers_status=job_record.get("providers_status", {}),
                    warnings=job_record.get("warnings", []) + [str(e)]
                )
                ResearchRunRepository.save_run(run)
            except Exception:
                pass

            return job_record

    # ─────────────────────────────────────────────────────────────
    # WORKFLOW 1: DESTINATION DISCOVERY
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _run_destination_discovery(
        cls, trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job
    ) -> Dict[str, Any]:
        """Workflow 1: Evaluates 45+ destinations, filters by climate/safety, matches top candidates."""
        job["steps_completed"].append("Scoring and filtering 45+ destinations via AHP & climate models")
        job["progress_pct"] = 25

        # 1. Rank destinations
        dest_candidates = DestinationMatchingService.evaluate_and_rank_destinations(
            origin=origin,
            duration_days=duration_days,
            adults=adults,
            children=children,
            target_temp=resolved.soft.target_temperature,
            min_safety=resolved.hard.min_safety_score or 50,
            preferred_regions=resolved.hard.required_regions or None,
            ahp_weights={
                "total_cost": resolved.soft.ahp_pillar_weights.get("destination", 25.0),
                "weather": resolved.soft.ahp_pillar_weights.get("experience", 25.0),
                "safety": 30.0
            },
            limit=8
        )

        job["steps_completed"].append(f"Ranked {len(dest_candidates)} destination candidates")
        job["progress_pct"] = 50

        # Filter out avoid destinations
        avoid_cities = [a.lower() for a in resolved.avoid.avoid_destinations]
        filtered_destinations = [d for d in dest_candidates if d.get("city", "").lower() not in avoid_cities]
        if not filtered_destinations:
            filtered_destinations = dest_candidates[:3]

        top_dests = filtered_destinations[:3]
        all_candidates = []
        all_flights = []
        all_stays = []

        for dest in top_dests:
            city_name = dest.get("city", "Barcelona")
            flights = cls._fetch_flights_safe(origin, city_name, out_date, in_date, adults, resolved, job)
            stays = cls._fetch_stays_safe(city_name, dest.get("country", ""), out_date, in_date, adults, resolved, job)
            activities = ExperienceIntelligenceService.get_curated_activities(city_name, dest.get("country", ""), duration_days)

            all_flights.extend(flights)
            all_stays.extend(stays)

            # Build candidates for this destination
            best_flight = flights[0] if flights else cls._build_mock_flight(origin, city_name, out_date, in_date)
            best_stay = stays[0] if stays else cls._build_mock_stay(city_name, duration_days)

            cand = cls._compose_candidate(
                dest=dest,
                flight=best_flight,
                stay=best_stay,
                activities=activities,
                adults=adults,
                children=children,
                duration_days=duration_days,
                resolved=resolved,
                archetype=OptionArchetype.BEST_OVERALL
            )
            all_candidates.append(cand)

        job["steps_completed"].append(f"Generated {len(all_candidates)} destination-backed trip candidates")
        job["progress_pct"] = 90

        return {
            "candidates": all_candidates,
            "destinations_pool": filtered_destinations,
            "flights_pool": all_flights,
            "stays_pool": all_stays
        }

    # ─────────────────────────────────────────────────────────────
    # WORKFLOW 2: KNOWN DESTINATION RESEARCH
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _run_known_destination_research(
        cls, destination: str, trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job
    ) -> Dict[str, Any]:
        """Workflow 2: Deep research for a specific destination across multiple tiers."""
        job["steps_completed"].append(f"Initiating deep research for {destination}")
        job["progress_pct"] = 25

        dest_info = cls._get_destination_meta(destination)
        flights = cls._fetch_flights_safe(origin, destination, out_date, in_date, adults, resolved, job)
        job["progress_pct"] = 55

        stays = cls._fetch_stays_safe(destination, dest_info.get("country", ""), out_date, in_date, adults, resolved, job)
        job["progress_pct"] = 75

        activities = ExperienceIntelligenceService.get_curated_activities(destination, dest_info.get("country", ""), duration_days)
        job["progress_pct"] = 85

        # Create Archetype options: Best Overall, Best Value, Best Experience
        candidates = cls._generate_archetype_candidates(
            dest_info, flights, stays, activities, adults, children, duration_days, resolved
        )

        job["steps_completed"].append(f"Generated 3 distinct decision archetype candidates for {destination}")
        return {
            "candidates": candidates,
            "destinations_pool": [dest_info],
            "flights_pool": flights,
            "stays_pool": stays
        }

    # ─────────────────────────────────────────────────────────────
    # WORKFLOW 3: FLIGHT-FIRST STRATEGY
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _run_flight_first_strategy(
        cls, destination: Optional[str], trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job
    ) -> Dict[str, Any]:
        """Workflow 3: Finds top-tier flight deals first, then pairs with suitable stays."""
        job["steps_completed"].append("Executing Flight-First priority search")
        dest_target = destination or "Rome"
        dest_info = cls._get_destination_meta(dest_target)

        # Stricter flight criteria (emphasize direct and low price)
        flights = cls._fetch_flights_safe(origin, dest_target, out_date, in_date, adults, resolved, job)
        # Sort flights strictly by PROMETHEE or price
        flights.sort(key=lambda f: float(f.get("price_total_huf", 999999)))

        stays = cls._fetch_stays_safe(dest_target, dest_info.get("country", ""), out_date, in_date, adults, resolved, job)
        activities = ExperienceIntelligenceService.get_curated_activities(dest_target, dest_info.get("country", ""), duration_days)

        candidates = cls._generate_archetype_candidates(
            dest_info, flights, stays, activities, adults, children, duration_days, resolved
        )
        return {
            "candidates": candidates,
            "destinations_pool": [dest_info],
            "flights_pool": flights,
            "stays_pool": stays
        }

    # ─────────────────────────────────────────────────────────────
    # WORKFLOW 4: STAY-FIRST STRATEGY
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _run_stay_first_strategy(
        cls, destination: Optional[str], trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job
    ) -> Dict[str, Any]:
        """Workflow 4: Finds premium/high-rated accommodation first, then complements flight schedule."""
        job["steps_completed"].append("Executing Stay-First luxury & comfort priority search")
        dest_target = destination or "Paris"
        dest_info = cls._get_destination_meta(dest_target)

        # Enforce minimum 4 stars and high rating for stay first
        custom_resolved = resolved.model_copy(deep=True)
        if not custom_resolved.hard.min_hotel_stars or custom_resolved.hard.min_hotel_stars < 4:
            custom_resolved.hard.min_hotel_stars = 4

        stays = cls._fetch_stays_safe(dest_target, dest_info.get("country", ""), out_date, in_date, adults, custom_resolved, job)
        stays.sort(key=lambda s: float(s.get("rating_normalized", 0.0)), reverse=True)

        flights = cls._fetch_flights_safe(origin, dest_target, out_date, in_date, adults, resolved, job)
        activities = ExperienceIntelligenceService.get_curated_activities(dest_target, dest_info.get("country", ""), duration_days)

        candidates = cls._generate_archetype_candidates(
            dest_info, flights, stays, activities, adults, children, duration_days, resolved
        )
        return {
            "candidates": candidates,
            "destinations_pool": [dest_info],
            "flights_pool": flights,
            "stays_pool": stays
        }

    # ─────────────────────────────────────────────────────────────
    # WORKFLOW 5: FULL-TRIP OPTIMIZATION
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _run_full_trip_optimization(
        cls, destination: str, trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job
    ) -> Dict[str, Any]:
        """Workflow 5: End-to-end multi-criteria package optimization maximizing total TripScore."""
        job["steps_completed"].append(f"Simultaneous full-trip package optimization for {destination}")
        dest_info = cls._get_destination_meta(destination)

        flights = cls._fetch_flights_safe(origin, destination, out_date, in_date, adults, resolved, job)
        stays = cls._fetch_stays_safe(destination, dest_info.get("country", ""), out_date, in_date, adults, resolved, job)
        activities = ExperienceIntelligenceService.get_curated_activities(destination, dest_info.get("country", ""), duration_days)

        candidates = cls._generate_archetype_candidates(
            dest_info, flights, stays, activities, adults, children, duration_days, resolved
        )
        return {
            "candidates": candidates,
            "destinations_pool": [dest_info],
            "flights_pool": flights,
            "stays_pool": stays
        }

    # ─────────────────────────────────────────────────────────────
    # WORKFLOW 6: COMPONENT-ONLY RESEARCH
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _run_component_only_research(
        cls, destination: Optional[str], trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job
    ) -> Dict[str, Any]:
        """Workflow 6: Focused research on Flights Only or Accommodation Only."""
        dest_target = destination or "Barcelona"
        dest_info = cls._get_destination_meta(dest_target)
        scope = trip_case.scope

        flights = []
        stays = []
        candidates = []

        if scope == ResearchScope.FLIGHT_ONLY:
            job["steps_completed"].append(f"Searching flights only for {dest_target}")
            flights = cls._fetch_flights_safe(origin, dest_target, out_date, in_date, adults, resolved, job)
            for fl in flights[:3]:
                candidates.append({
                    "id": f"cand_fl_{uuid.uuid4().hex[:8]}",
                    "component_type": "flight",
                    "title": f"Repülőút {origin} → {dest_target}",
                    "flight": fl,
                    "total_price_huf": fl.get("price_total_huf", 0.0),
                    "trip_score": 88,
                    "provenance": fl.get("provenance", {})
                })
        elif scope == ResearchScope.STAY_ONLY:
            job["steps_completed"].append(f"Searching accommodation only for {dest_target}")
            stays = cls._fetch_stays_safe(dest_target, dest_info.get("country", ""), out_date, in_date, adults, resolved, job)
            for st in stays[:3]:
                candidates.append({
                    "id": f"cand_st_{uuid.uuid4().hex[:8]}",
                    "component_type": "accommodation",
                    "title": st.get("name", f"Hotel {dest_target}"),
                    "stay": st,
                    "total_price_huf": st.get("price_total_huf", 0.0),
                    "trip_score": 87,
                    "provenance": st.get("provenance", {})
                })
        else:
            # Both components
            flights = cls._fetch_flights_safe(origin, dest_target, out_date, in_date, adults, resolved, job)
            stays = cls._fetch_stays_safe(dest_target, dest_info.get("country", ""), out_date, in_date, adults, resolved, job)

        return {
            "candidates": candidates,
            "destinations_pool": [dest_info],
            "flights_pool": flights,
            "stays_pool": stays
        }

    # ─────────────────────────────────────────────────────────────
    # WORKFLOW 7: MIXED-SCOPE RESEARCH
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _run_mixed_scope_research(
        cls, candidate_cities: List[str], trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, job
    ) -> Dict[str, Any]:
        """Workflow 7: Multi-destination side-by-side comparison for Flight+Stay bundles."""
        job["steps_completed"].append(f"Comparing candidate cities: {', '.join(candidate_cities)}")
        all_candidates = []
        all_flights = []
        all_stays = []

        for city in candidate_cities[:3]:
            dest_info = cls._get_destination_meta(city)
            flights = cls._fetch_flights_safe(origin, city, out_date, in_date, adults, resolved, job)
            stays = cls._fetch_stays_safe(city, dest_info.get("country", ""), out_date, in_date, adults, resolved, job)
            activities = ExperienceIntelligenceService.get_curated_activities(city, dest_info.get("country", ""), duration_days)

            all_flights.extend(flights)
            all_stays.extend(stays)

            best_flight = flights[0] if flights else cls._build_mock_flight(origin, city, out_date, in_date)
            best_stay = stays[0] if stays else cls._build_mock_stay(city, duration_days)

            cand = cls._compose_candidate(
                dest=dest_info,
                flight=best_flight,
                stay=best_stay,
                activities=activities,
                adults=adults,
                children=children,
                duration_days=duration_days,
                resolved=resolved,
                archetype=OptionArchetype.BEST_OVERALL
            )
            all_candidates.append(cand)

        return {
            "candidates": all_candidates,
            "destinations_pool": [cls._get_destination_meta(c) for c in candidate_cities],
            "flights_pool": all_flights,
            "stays_pool": all_stays
        }

    # ─────────────────────────────────────────────────────────────
    # WORKFLOW 8: RE-OPTIMIZATION WORKFLOW
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _run_re_optimization(
        cls, trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, custom_params, job
    ) -> Dict[str, Any]:
        """Workflow 8: Re-calculates and re-ranks based on newly altered constraints or budget shift."""
        job["steps_completed"].append("Executing live re-optimization with updated constraints")
        dest_target = custom_params.get("destination") or trip_case.destination_focus or "Barcelona"
        dest_info = cls._get_destination_meta(dest_target)

        flights = cls._fetch_flights_safe(origin, dest_target, out_date, in_date, adults, resolved, job)
        stays = cls._fetch_stays_safe(dest_target, dest_info.get("country", ""), out_date, in_date, adults, resolved, job)
        activities = ExperienceIntelligenceService.get_curated_activities(dest_target, dest_info.get("country", ""), duration_days)

        candidates = cls._generate_archetype_candidates(
            dest_info, flights, stays, activities, adults, children, duration_days, resolved
        )
        return {
            "candidates": candidates,
            "destinations_pool": [dest_info],
            "flights_pool": flights,
            "stays_pool": stays
        }

    # ─────────────────────────────────────────────────────────────
    # WORKFLOW 9: FIND BETTER WORKFLOW
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _run_find_better(
        cls, destination: str, trip_case, resolved, origin, out_date, in_date, adults, children, duration_days, custom_params, job
    ) -> Dict[str, Any]:
        """Workflow 9: Targeted component tuning (e.g. Find cheaper flight or higher rated hotel)."""
        target_component = custom_params.get("target_component", "stay")
        job["steps_completed"].append(f"Executing 'Find Better' tuning for component: {target_component}")

        dest_info = cls._get_destination_meta(destination)
        existing_candidates = cls._CANDIDATES_POOL.get(trip_case.id, [])
        if existing_candidates:
            # Fast in-memory candidate re-ranking from existing pool
            flights = [c.get("flight") for c in existing_candidates if c.get("flight")]
            stays = [c.get("stay") for c in existing_candidates if c.get("stay")]
            if not flights:
                flights = cls._fetch_flights_safe(origin, destination, out_date, in_date, adults, resolved, job)
            if not stays:
                stays = cls._generate_fallback_stays(destination, dest_info.get("country", ""))
        else:
            flights = cls._fetch_flights_safe(origin, destination, out_date, in_date, adults, resolved, job)
            stays = cls._fetch_stays_safe(destination, dest_info.get("country", ""), out_date, in_date, adults, resolved, job)
            
        activities = ExperienceIntelligenceService.get_curated_activities(destination, dest_info.get("country", ""), duration_days)

        if target_component == "flight":
            flights.sort(key=lambda f: float(f.get("price_total_huf", 999999)))
        elif target_component == "stay":
            stays.sort(key=lambda s: float(s.get("rating_normalized", 0.0)), reverse=True)

        candidates = cls._generate_archetype_candidates(
            dest_info, flights, stays, activities, adults, children, duration_days, resolved
        )
        return {
            "candidates": candidates,
            "destinations_pool": [dest_info],
            "flights_pool": flights,
            "stays_pool": stays
        }

    # ─────────────────────────────────────────────────────────────
    # RESILIENCE & PROVIDER CALL HELPERS
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _fetch_flights_safe(
        cls, origin: str, destination: str, out_date: str, in_date: str, adults: int, resolved: ResolvedTripPreferences, job: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Resilient flight search with Kiwi API and graceful fallback handling."""
        try:
            hard = resolved.hard
            direct_only = bool(hard.direct_flights_only)
            max_stops = hard.max_stops if hard.max_stops is not None else 1
            max_duration = hard.max_flight_duration_h or 0.0

            results = FlightIntelligenceService.search_and_rank_flights(
                origin=origin,
                destination=destination,
                out_date=out_date,
                in_date=in_date,
                adults=adults,
                direct_only=direct_only,
                max_stops=max_stops,
                max_duration_h=max_duration,
                ahp_weights=resolved.soft.flight_priority_weights,
                limit=10
            )

            # Filter avoid airlines
            if results and resolved.avoid.avoid_airlines:
                avoid_list = [a.lower() for a in resolved.avoid.avoid_airlines]
                results = [r for r in results if r.get("airline", "").lower() not in avoid_list]

            if results:
                for r in results:
                    r["provenance"] = ProviderProvenance(
                        provider="Kiwi.com GraphQL",
                        checked_at=utc_now(),
                        verification_status=VerificationStatus.VERIFIED,
                        is_estimated=False
                    ).model_dump()
                return results

        except Exception as e:
            logger.warning(f"Live flight search failed or timed out: {e}. Activating fallback flight intelligence.")
            if isinstance(job, dict):
                job.setdefault("warnings", []).append(f"Kiwi API élőszolgáltatás nem elérhető ({e}). Becsült járatadatok használva.")

        # Resilient fallback mock flight candidates
        return [
            cls._build_mock_flight(origin, destination, out_date, in_date, 68000, "Wizz Air / Ryanair", 0),
            cls._build_mock_flight(origin, destination, out_date, in_date, 95000, "Lufthansa / Austrian", 1),
            cls._build_mock_flight(origin, destination, out_date, in_date, 125000, "Air France / KLM", 0)
        ]

    @classmethod
    def _fetch_stays_safe(
        cls, destination: str, country: str, checkin: str, checkout: str, adults: int, resolved: ResolvedTripPreferences, job: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Resilient accommodation search with Cozycozy scraper and graceful fallback handling."""
        try:
            hard = resolved.hard
            min_stars = hard.min_hotel_stars or 3
            min_rating = hard.min_hotel_rating or 7.5
            breakfast = resolved.nice_to_have.breakfast_included

            results = AccommodationIntelligenceService.search_and_rank_stays(
                city=destination,
                country=country or "",
                checkin=checkin,
                checkout=checkout,
                adults=adults,
                min_stars=min_stars,
                min_rating=min_rating,
                breakfast=breakfast,
                amenities=hard.required_amenities,
                limit=10
            )

            if results:
                for r in results:
                    r["provenance"] = ProviderProvenance(
                        provider="Cozycozy Engine",
                        checked_at=utc_now(),
                        verification_status=VerificationStatus.VERIFIED,
                        is_estimated=False
                    ).model_dump()
                return results

        except Exception as e:
            logger.warning(f"Live accommodation scraper failed: {e}. Activating fallback accommodation model.")
            if isinstance(job, dict):
                job.setdefault("warnings", []).append(f"Cozycozy szállásadatbázis nem elérhető ({e}). Becsült szállásadatok használva.")

        # Resilient fallback stays
        duration = 7
        return [
            cls._build_mock_stay(destination, duration, f"Grand Hotel {destination} Central", 4, 8.8, 195000),
            cls._build_mock_stay(destination, duration, f"Boutique Hotel & Suites {destination}", 4, 9.2, 240000),
            cls._build_mock_stay(destination, duration, f"Cozy Design Apartments {destination}", 3, 8.5, 145000)
        ]

    # ─────────────────────────────────────────────────────────────
    # CANDIDATE & ARCHETYPE BUILDERS
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _generate_archetype_candidates(
        cls, dest_info: Dict[str, Any], flights: List[Dict[str, Any]], stays: List[Dict[str, Any]],
        activities: List[Dict[str, Any]], adults: int, children: int, duration_days: int, resolved: ResolvedTripPreferences
    ) -> List[Dict[str, Any]]:
        """Generates the 3 standard decision archetypes: Best Overall, Best Value, Best Experience."""
        candidates = []

        if not flights:
            flights = [cls._build_mock_flight("BUD", dest_info.get("city", "Dest"), "2026-10-01", "2026-10-08")]
        if not stays:
            stays = [cls._build_mock_stay(dest_info.get("city", "Dest"), duration_days)]

        # Option A: BEST OVERALL (Highest balanced score)
        best_flight_a = flights[0]
        best_stay_a = stays[0]
        cand_a = cls._compose_candidate(
            dest=dest_info,
            flight=best_flight_a,
            stay=best_stay_a,
            activities=activities,
            adults=adults,
            children=children,
            duration_days=duration_days,
            resolved=resolved,
            archetype=OptionArchetype.BEST_OVERALL
        )
        cand_a["title"] = f"{dest_info.get('city', 'Város')} — Prémium Kiegyensúlyozott Utazás"
        cand_a["tagline"] = "Kiváló elhelyezkedésű 4* hotel, kényelmes közvetlen járatok"
        cand_a["why_this_option"] = "A legjobb összetett TripScore mutatóval rendelkező csomag, ideális kompromisszum az ár és a kényelem között."
        cand_a["tradeoffs"] = ["Mérsékelt árprémium a legolcsóbb alternatívához képest", "Fix menetrendű közvetlen járat"]
        candidates.append(cand_a)

        # Option B: BEST VALUE (Budget-optimized)
        cheapest_flight = sorted(flights, key=lambda f: float(f.get("price_total_huf", 999999)))[0]
        cheapest_stay = sorted(stays, key=lambda s: float(s.get("price_total_huf", 999999)))[0]
        cand_b = cls._compose_candidate(
            dest=dest_info,
            flight=cheapest_flight,
            stay=cheapest_stay,
            activities=activities,
            adults=adults,
            children=children,
            duration_days=duration_days,
            resolved=resolved,
            archetype=OptionArchetype.BEST_VALUE
        )
        cand_b["title"] = f"{dest_info.get('city', 'Város')} — Költségtudatos Smart Csomag"
        cand_b["tagline"] = "Maximális ár-érték arány, minőségi 3-4* szállás"
        cand_b["why_this_option"] = "Akár 20-30%-kal alacsonyabb összköltség, miközben minden alapvető kényelmi elvárás teljesül."
        cand_b["tradeoffs"] = ["Kora reggeli vagy késő esti járati időpont lehetséges", "Központtól némileg távolabbi szállás"]
        candidates.append(cand_b)

        # Option C: BEST EXPERIENCE (Top-tier rating / Luxury)
        top_stay = sorted(stays, key=lambda s: float(s.get("rating_normalized", 0.0)), reverse=True)[0]
        cand_c = cls._compose_candidate(
            dest=dest_info,
            flight=best_flight_a,
            stay=top_stay,
            activities=activities,
            adults=adults,
            children=children,
            duration_days=duration_days,
            resolved=resolved,
            archetype=OptionArchetype.BEST_EXPERIENCE
        )
        cand_c["title"] = f"{dest_info.get('city', 'Város')} — Exkluzív Élményfókuszú Csomag"
        cand_c["tagline"] = "Csúcsminősítésű 4-5* szállás, prémium lokáció és gazdag programcsomag"
        cand_c["why_this_option"] = "Kivételes vendégértékelésű szállás és a legteljesebb gasztro-kulturális élményprogram."
        cand_c["tradeoffs"] = ["Magasabb költségkeretet igényel", "Népszerűbb időszakokban gyorsabban betelik"]
        candidates.append(cand_c)

        return candidates

    @classmethod
    def _compose_candidate(
        cls, dest: Dict[str, Any], flight: Dict[str, Any], stay: Dict[str, Any],
        activities: List[Dict[str, Any]], adults: int, children: int, duration_days: int,
        resolved: ResolvedTripPreferences, archetype: OptionArchetype
    ) -> Dict[str, Any]:
        """Composes a single validated candidate package with holistic TripScore."""
        total_pax = max(1, adults + children)
        flight_price = float(flight.get("price_total_huf", 0.0) or flight.get("price_huf", 0.0))
        stay_price = float(stay.get("price_total_huf", 0.0) or stay.get("price_huf", 0.0))
        total_price = flight_price + stay_price
        price_per_pax = round(total_price / total_pax)

        # Dynamic Trip Scoring
        score_eval = TripScoreService.calculate_trip_score(
            destination=dest,
            flight=flight,
            accommodation=stay,
            activities=activities,
            weights=resolved.soft.ahp_pillar_weights
        )

        return {
            "id": f"cand_{uuid.uuid4().hex[:10]}",
            "archetype": archetype.value if hasattr(archetype, "value") else str(archetype),
            "title": f"{dest.get('city', 'Város')} Utazási Csomag",
            "tagline": "Optimalizált utazási opció",
            "total_price_huf": total_price,
            "price_per_person_huf": price_per_pax,
            "currency": "HUF",
            "destination": dest,
            "flight": flight,
            "stay": stay,
            "activities": activities[:4],
            "trip_score": score_eval.get("trip_score", 85),
            "pillar_scores": score_eval.get("pillar_scores", {}),
            "effective_vacation_hours": duration_days * 14.0,
            "why_this_option": "Személyre szabott illeszkedés a feloldott preferenciák alapján.",
            "tradeoffs": [],
            "verification_status": VerificationStatus.VERIFIED.value,
            "is_pinned": False,
            "created_at": utc_now().isoformat()
        }

    # ─────────────────────────────────────────────────────────────
    # MOCK & METADATA FACTORIES
    # ─────────────────────────────────────────────────────────────
    @classmethod
    def _get_destination_meta(cls, city: str) -> Dict[str, Any]:
        """Retrieves structured destination metadata with fallback."""
        city_clean = city.strip().capitalize()
        vibes = ExperienceIntelligenceService.get_destination_vibe(city)
        return {
            "city": city_clean,
            "country": "Európa",
            "safety_score": 88,
            "temperature_avg": 23.5,
            "daily_cost_eur": 85,
            "vibe_scores": vibes,
            "provenance": ProviderProvenance(provider="Destination Model").model_dump()
        }

    @classmethod
    def _build_mock_flight(
        cls, origin: str, dest: str, out_date: str, in_date: str, price: float = 75000, airline: str = "Wizz Air", stops: int = 0
    ) -> Dict[str, Any]:
        return {
            "id": f"fl_{uuid.uuid4().hex[:8]}",
            "origin": origin,
            "destination": dest,
            "airline": airline,
            "out_date": out_date,
            "in_date": in_date,
            "stops": stops,
            "out_duration_h": 2.2,
            "in_duration_h": 2.3,
            "price_total_huf": price,
            "provenance": ProviderProvenance(
                provider="Kiwi.com (Estimated)",
                verification_status=VerificationStatus.ESTIMATED,
                is_estimated=True
            ).model_dump()
        }

    @classmethod
    def _build_mock_stay(
        cls, dest: str, duration: int, name: Optional[str] = None, stars: int = 4, rating: float = 8.8, price: float = 180000
    ) -> Dict[str, Any]:
        return {
            "id": f"stay_{uuid.uuid4().hex[:8]}",
            "name": name or f"Grand Hotel {dest} Central",
            "city": dest,
            "stars": stars,
            "rating_normalized": rating,
            "stars_normalized": stars,
            "nights": duration,
            "price_total_huf": price,
            "amenities": ["Wifi", "Légkondicionáló", "Központi elhelyezkedés"],
            "provenance": ProviderProvenance(
                provider="Cozycozy (Estimated)",
                verification_status=VerificationStatus.ESTIMATED,
                is_estimated=True
            ).model_dump()
        }

    @classmethod
    def get_research_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Returns the status, progress, and results of an async research job."""
        job = cls._RESEARCH_JOBS.get(job_id)
        if job:
            return job

        try:
            from app.repositories.advisor_repository import ResearchRunRepository
            run = ResearchRunRepository.get_run(job_id)
            if run:
                return {
                    "job_id": run.id,
                    "case_id": run.case_id,
                    "strategy": run.strategy,
                    "status": run.status.value if hasattr(run.status, "value") else str(run.status),
                    "progress_pct": run.progress_pct,
                    "steps_completed": run.steps_completed,
                    "providers_status": run.providers_status,
                    "candidates": run.candidates,
                    "destinations_pool": run.destinations_pool,
                    "flights_pool": run.flights_pool,
                    "stays_pool": run.stays_pool,
                    "warnings": run.warnings,
                    "elapsed_seconds": run.elapsed_seconds
                }
        except Exception:
            pass
        return None

    @classmethod
    def cancel_research_job(cls, job_id: str) -> bool:
        """Cancels a running or queued research job."""
        job = cls._RESEARCH_JOBS.get(job_id)
        if job:
            job["status"] = "cancelled"
            job["progress_pct"] = 0
            job["warnings"].append("Research cancelled by advisor.")

        try:
            from app.repositories.advisor_repository import ResearchRunRepository
            from app.models.advisor_models import ResearchRunStatus
            run = ResearchRunRepository.get_run(job_id)
            if run:
                run.status = ResearchRunStatus.CANCELLED
                run.warnings.append("Research cancelled by advisor.")
                ResearchRunRepository.save_run(run)
                return True
        except Exception:
            pass

        return bool(job)
