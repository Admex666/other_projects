"""
Optivoya Advisor Workspace v2 — Research State & Intent Engine Service
=====================================================================
Manages the continuous "Research State" domain model and the Dynamic Research Intent Engine
across the 5 UX phases:
① UNDERSTAND → ② DEFINE → ③ RESEARCH → ④ DECIDE → ⑤ DELIVER.

Key Responsibilities:
1. Initialize / build ResearchState from TripCase + Client profile.
2. Resolve Research Intent automatically across 7 archetypes:
   - KNOWN_DESTINATION_FULL
   - DESTINATION_DISCOVERY
   - FLIGHT_FIRST
   - STAY_FIRST
   - RE_OPTIMIZE
   - FIND_BETTER_COMPONENT
   - MIXED_SCOPE_COMPETITION
3. Generate Dynamic Research Plan (step-by-step pipeline with providers and time estimates).
4. Evaluate "Mi van / Mi nincs?" missing info matrix with actionable system responses.
5. Manage component-level intent actions (KEEP, REPLACE, IMPROVE).
6. Support intent confirmation, transitions, criteria approval, and phase state machine.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

from app.models.advisor_models import (
    TripCase, Client, ResearchState, ResearchStatePhase,
    ComponentIntentAction, ExistingComponent,
    ResearchPlan, ResearchPlanStep, ResearchPlanStepStatus,
    WhatWeKnow, WhatWeDontKnow, WhatIsFixed, WhatIsFlexible,
    WhatMatters, WhatWeAreSearching, WhatWeFound, WhatIsVerified,
    WhatAdvisorChanged, WhatStillNeedsDecision, MissingInfoMatrixItem
)

logger = logging.getLogger("research_state_service")

# In-memory fast cache for active research states keyed by case_id
_RESEARCH_STATES: Dict[str, ResearchState] = {}


class ResearchStateService:
    """
    Central orchestration service for Advisor Workspace v2 Research State & Intent Engine.
    """

    @classmethod
    def get_or_create_research_state(
        cls,
        trip_case: TripCase,
        client: Optional[Client] = None,
        force_rebuild: bool = False
    ) -> ResearchState:
        """
        Retrieves the cached ResearchState or builds a fresh instance from TripCase.
        """
        case_id = trip_case.id
        if not force_rebuild and case_id in _RESEARCH_STATES:
            return _RESEARCH_STATES[case_id]

        state = cls.build_research_state(trip_case=trip_case, client=client)
        _RESEARCH_STATES[case_id] = state
        return state

    @classmethod
    def build_research_state(
        cls,
        trip_case: TripCase,
        client: Optional[Client] = None
    ) -> ResearchState:
        """
        Constructs a complete ResearchState snapshot based on TripCase and Client Profile.
        """
        # 1. WHAT WE KNOW
        cand_dests = []
        if getattr(trip_case, "candidate_destinations", None):
            cand_dests = list(trip_case.candidate_destinations)
        elif trip_case.destination_focus:
            cand_dests = [trip_case.destination_focus]

        cand_origins = []
        if getattr(trip_case, "candidate_origins", None):
            cand_origins = list(trip_case.candidate_origins)
        elif trip_case.origin:
            cand_origins = [trip_case.origin]
        else:
            cand_origins = ["Budapest (BUD)"]

        # Parse existing components if any
        existing_comps: List[ExistingComponent] = []
        if hasattr(trip_case, "existing_components") and trip_case.existing_components:
            for item in trip_case.existing_components:
                if isinstance(item, dict):
                    existing_comps.append(ExistingComponent(**item))
                elif isinstance(item, ExistingComponent):
                    existing_comps.append(item)

        budget_val = None
        if getattr(trip_case, "budget_constraint", None) and getattr(trip_case.budget_constraint, "total", None) and trip_case.budget_constraint.total.amount:
            budget_val = trip_case.budget_constraint.total.amount
        elif getattr(trip_case, "total_budget_huf", None):
            budget_val = trip_case.total_budget_huf

        budget_curr = "HUF"
        budget_hard = "hard"
        budget_bas = "group"
        if getattr(trip_case, "budget_constraint", None):
            budget_curr = trip_case.budget_constraint.currency or "HUF"
            if getattr(trip_case.budget_constraint, "total", None):
                if hasattr(trip_case.budget_constraint.total.hardness, "value"):
                    budget_hard = trip_case.budget_constraint.total.hardness.value
                elif trip_case.budget_constraint.total.hardness:
                    budget_hard = str(trip_case.budget_constraint.total.hardness)
                if hasattr(trip_case.budget_constraint.total.basis, "value"):
                    budget_bas = trip_case.budget_constraint.total.basis.value
                elif trip_case.budget_constraint.total.basis:
                    budget_bas = str(trip_case.budget_constraint.total.basis)

        out_d = getattr(trip_case, "exact_out_date", None) or getattr(trip_case, "out_date", None)
        in_d = getattr(trip_case, "exact_in_date", None) or getattr(trip_case, "in_date", None)
        d_mode = getattr(trip_case, "date_mode", "exact") or "exact"
        dur_days = getattr(trip_case, "duration_days_min", None) or getattr(trip_case, "duration_days", 7) or 7

        what_we_know = WhatWeKnow(
            client_id=trip_case.client_id,
            client_name=client.name if client else "Ügyfél",
            travelers_count=trip_case.adults + trip_case.children,
            adults=trip_case.adults,
            children=trip_case.children,
            origin=trip_case.origin or "Budapest",
            candidate_origins=cand_origins,
            destination=trip_case.destination_focus,
            candidate_destinations=cand_dests,
            trip_type=getattr(trip_case, "trip_type", "city_break") or "city_break",
            date_mode=d_mode,
            exact_out_date=out_d,
            exact_in_date=in_d,
            month=getattr(trip_case, "month", None),
            duration_days=dur_days,
            total_budget=budget_val,
            budget_currency=budget_curr,
            budget_hardness=budget_hard,
            budget_basis=budget_bas,
            existing_components=existing_comps
        )

        # 2. WHAT WE DON'T KNOW
        missing_fields = []
        uncertainties = []
        if not what_we_know.destination and not what_we_know.candidate_destinations:
            missing_fields.append("destination")
        if what_we_know.date_mode == "exact" and (not what_we_know.exact_out_date or not what_we_know.exact_in_date):
            missing_fields.append("exact_dates")
        if what_we_know.total_budget is None or what_we_know.total_budget <= 0:
            missing_fields.append("budget")

        what_we_dont_know = WhatWeDontKnow(
            missing_fields=missing_fields,
            uncertainties=uncertainties,
            required_clarifications=[]
        )

        # 3. WHAT IS FIXED
        locked_flight_ids = [c.details.get("id") for c in existing_comps if c.component_type == "flight" and c.action == ComponentIntentAction.KEEP and c.details.get("id")]
        locked_stay_ids = [c.details.get("id") for c in existing_comps if c.component_type == "stay" and c.action == ComponentIntentAction.KEEP and c.details.get("id")]
        
        what_is_fixed = WhatIsFixed(
            locked_destination=what_we_know.destination if what_we_know.destination and len(what_we_know.candidate_destinations) <= 1 else None,
            locked_flight_ids=locked_flight_ids,
            locked_stay_ids=locked_stay_ids,
            locked_dates=(what_we_know.date_mode == "exact" and bool(what_we_know.exact_out_date and what_we_know.exact_in_date)),
            locked_budget=(what_we_know.total_budget is not None and what_we_know.budget_hardness == "hard")
        )

        # 4. WHAT IS FLEXIBLE
        what_is_flexible = WhatIsFlexible(
            date_flexibility_days=0 if what_we_know.date_mode == "exact" else 3,
            budget_relaxation_allowed=(what_we_know.budget_hardness != "hard"),
            max_budget_stretch_percent=15.0 if what_we_know.budget_hardness != "hard" else 0.0
        )

        # 5. WHAT MATTERS (Criteria & Preferences)
        selected_dims = ["price", "hotel_quality", "location", "experience"]
        if client and client.preferences:
            if client.preferences.direct_flights_only:
                selected_dims.append("direct_flight")
        
        what_matters = WhatMatters(
            selected_dimensions=selected_dims,
            ahp_weights={"price": 0.35, "hotel_quality": 0.25, "location": 0.25, "experience": 0.15},
            hard_constraints={
                "direct_flights_only": client.preferences.direct_flights_only if client and client.preferences else False,
                "min_hotel_stars": client.preferences.hotel_min_stars if client and client.preferences else 3
            },
            soft_preferences={
                "interests": client.preferences.interests if client and client.preferences else ["sightseeing", "gastronomy"]
            }
        )

        # 6. RESOLVE INTENT (Automatic Research Intent Reconstruction)
        intent_key, intent_text = cls.resolve_research_intent(what_we_know, what_is_fixed, existing_comps)

        # 7. GENERATE DYNAMIC RESEARCH PLAN
        research_plan = cls.generate_dynamic_research_plan(intent_key, intent_text, what_we_know, what_is_fixed)

        # 8. CONSTRUCT RESEARCH STATE
        state = ResearchState(
            case_id=trip_case.id,
            agency_id=trip_case.agency_id,
            advisor_id=trip_case.advisor_id,
            phase=ResearchStatePhase.UNDERSTAND,
            resolved_intent=intent_key,
            intent_summary=intent_text,
            intent_confirmed=False,
            research_plan=research_plan,
            what_we_know=what_we_know,
            what_we_dont_know=what_we_dont_know,
            what_is_fixed=what_is_fixed,
            what_is_flexible=what_is_flexible,
            what_matters=what_matters,
            what_we_are_searching=WhatWeAreSearching(
                current_status_text="Készenlétben (Cél rekonstruálva, jóváhagyásra vár)"
            ),
            what_we_found=WhatWeFound(),
            what_is_verified=WhatIsVerified(),
            what_advisor_changed=WhatAdvisorChanged(),
            what_still_needs_decision=WhatStillNeedsDecision(
                intent_confirmed=False,
                criteria_approved=False
            )
        )

        return state

    @classmethod
    def resolve_research_intent(
        cls,
        what_we_know: WhatWeKnow,
        what_is_fixed: WhatIsFixed,
        existing_comps: List[ExistingComponent]
    ) -> Tuple[str, str]:
        """
        Reconstructs the precise research goal / intent without manual 9-workflow selection.
        """
        has_dest = bool(what_we_know.destination)
        has_multi_dest = len(what_we_know.candidate_destinations) > 1
        
        has_fixed_flight = any(c.component_type == "flight" and c.action == ComponentIntentAction.KEEP for c in existing_comps) or len(what_is_fixed.locked_flight_ids) > 0
        has_fixed_stay = any(c.component_type == "stay" and c.action == ComponentIntentAction.KEEP for c in existing_comps) or len(what_is_fixed.locked_stay_ids) > 0
        has_improve_comp = any(c.action in (ComponentIntentAction.REPLACE, ComponentIntentAction.IMPROVE) for c in existing_comps)
        
        budget_str = f"{int(what_we_know.total_budget):,} {what_we_know.budget_currency}".replace(",", " ") if what_we_know.total_budget else "nincs korlát"
        travelers = f"{what_we_know.travelers_count} fő"

        if has_improve_comp:
            comp_types = [c.component_type for c in existing_comps if c.action in (ComponentIntentAction.REPLACE, ComponentIntentAction.IMPROVE)]
            comp_str = ", ".join(comp_types)
            intent_key = "FIND_BETTER_COMPONENT"
            intent_text = (
                f"Kifejezett komponens-csere vagy minőségi alternatívakeresés ({comp_str}) {travelers} részére. "
                f"A cél szigorúan jobb ár-érték arányú vagy magasabb minőségű alternatívák felkutatása."
            )
        elif has_fixed_flight and has_fixed_stay:
            intent_key = "RE_OPTIMIZATION"
            intent_text = (
                f"Meglévő rögzített repülőjegy és szállás mellett teljes útiterv összeállítása, "
                f"helyi transzferek, nyitvatartások és prémium élmények optimalizálása {travelers} részére."
            )
        elif has_dest and has_fixed_flight:
            dest_name = what_we_know.destination or "kiválasztott célpont"
            intent_key = "STAY_FIRST"
            intent_text = (
                f"A célállomás ({dest_name}) és a repülőjegy már rögzített. "
                f"A kutatás a prémium szállásokra és a helyi élményekre fókuszál (~{budget_str} keretből)."
            )
        elif has_multi_dest:
            dests_repr = ", ".join(what_we_know.candidate_destinations[:3])
            intent_key = "MIXED_SCOPE_COMPETITION"
            intent_text = (
                f"Több lehetséges célállomás versenyeztetése ({dests_repr}) {travelers} részére. "
                f"Párhuzamos összehasonlító elemzés a legjobb ár-érték és élményegyensúly megtalálására."
            )
        elif has_dest and not has_fixed_flight:
            dest_name = what_we_know.destination or what_we_know.candidate_destinations[0]
            intent_key = "FLIGHT_FIRST"
            intent_text = (
                f"Konkrét utazási célpont ({dest_name}) {travelers} részére. "
                f"A rendszer menetrend- és ár-optimalizált repülőjáratokat, hozzájuk illeszkedő szállásokat és programokat keres."
            )
        else:
            intent_key = "DESTINATION_DISCOVERY"
            intent_text = (
                f"Nyitott célállomás-keresés és inspirációs rangsorolás {travelers} részére "
                f"(~{budget_str} keretből), az éghajlat, repülési költségek és élményprofilok alapján."
            )

        return intent_key, intent_text

    @classmethod
    def generate_dynamic_research_plan(
        cls,
        intent_key: str,
        intent_text: str,
        what_we_know: WhatWeKnow,
        what_is_fixed: WhatIsFixed
    ) -> ResearchPlan:
        """
        Builds the structured, sequential Research Plan corresponding to the recognized intent.
        """
        steps: List[ResearchPlanStep] = []

        if intent_key == "DESTINATION_DISCOVERY":
            steps = [
                ResearchPlanStep(
                    step_id="dest_discovery",
                    label="Desztinációs Pool & Klímaszűrés",
                    provider="Open-Meteo & Numbeo KG",
                    estimated_duration_sec=1.5,
                    details="40+ európai város időjárási, költségszinti és élményprofil szűrése"
                ),
                ResearchPlanStep(
                    step_id="flight_scan",
                    label="Párhuzamos Repülőjegy Keresés",
                    provider="Kiwi GraphQL API",
                    estimated_duration_sec=2.0,
                    details="Legkedvezőbb menetrendek és árak feltárása a szűrt városokba"
                ),
                ResearchPlanStep(
                    step_id="stay_clusters",
                    label="Központi Szállások Feltérképezése",
                    provider="Cozycozy Aggregator",
                    estimated_duration_sec=2.0,
                    details="4-5 csillagos belvárosi szállások és árszintek összehasonlítása"
                ),
                ResearchPlanStep(
                    step_id="experience_profiling",
                    label="Élményprofil & Látnivaló Illesztés",
                    provider="TripAdvisor & Places KG",
                    estimated_duration_sec=1.5,
                    details="Kulturális, gasztronómiai és élményfaktorok hozzárendelése"
                ),
                ResearchPlanStep(
                    step_id="synthesis_ranking",
                    label="PROMETHEE II Többkritériumos Rangsorolás",
                    provider="Decision Engine",
                    estimated_duration_sec=1.0,
                    details="Összesített TripScore és 3 karakteres opció felépítése"
                )
            ]

        elif intent_key == "STAY_FIRST":
            steps = [
                ResearchPlanStep(
                    step_id="flight_lock",
                    label="Meglévő Repülőmenetrend Zárolása",
                    provider="Existing Booking Data",
                    estimated_duration_sec=0.5,
                    details="Érkezési és indulási idők, valamint repülőtéri transzferablak rögzítése"
                ),
                ResearchPlanStep(
                    step_id="stay_deep_search",
                    label="Prémium Szállás Keresés & Minőségellenőrzés",
                    provider="Cozycozy Live API",
                    estimated_duration_sec=2.5,
                    details="Lokáció, vendégértékelések (>8.8) és prémium kényelmi szolgáltatások szűrése"
                ),
                ResearchPlanStep(
                    step_id="geo_logistics",
                    label="Helyi Logisztika & Elhelyezkedési Elemzés",
                    provider="OSM / Routing API",
                    estimated_duration_sec=1.0,
                    details="Séta- és tömegközlekedési idők kalkulációja a főbb látványosságokhoz"
                ),
                ResearchPlanStep(
                    step_id="curated_experiences",
                    label="Helyi Élmények & Éttermek Ajánlása",
                    provider="Experience KG",
                    estimated_duration_sec=1.5,
                    details="A szállás környékéhez illeszkedő kiemelt gasztro- és programpontok"
                ),
                ResearchPlanStep(
                    step_id="synthesis",
                    label="3 Összehasonlítható Szállás-opció Kialakítása",
                    provider="Decision Engine",
                    estimated_duration_sec=1.0,
                    details="Ár-érték, luxus és elhelyezkedés alapú opciók generálása"
                )
            ]

        elif intent_key == "RE_OPTIMIZATION":
            steps = [
                ResearchPlanStep(
                    step_id="components_lock",
                    label="Meglévő Repülő & Szállás Rögzítése",
                    provider="Existing Components",
                    estimated_duration_sec=0.5,
                    details="Időpontok, címek és fix foglalási határok beolvasása"
                ),
                ResearchPlanStep(
                    step_id="geo_routing",
                    label="Fizikailag Reális Napi Logisztika",
                    provider="Routing API & Transit Matrix",
                    estimated_duration_sec=1.5,
                    details="Napi útvonalak, utazási idők és optimális zónabeosztások számítása"
                ),
                ResearchPlanStep(
                    step_id="opening_hours",
                    label="Nyitvatartások & Idősávok Ellenőrzése",
                    provider="Places API",
                    estimated_duration_sec=1.5,
                    details="Múzeumok, látványosságok és előre foglalós belépők ütemezése"
                ),
                ResearchPlanStep(
                    step_id="curated_dining",
                    label="Gasztronómia & Egyedi Élmények",
                    provider="Curated DB & VIP Concierge",
                    estimated_duration_sec=1.5,
                    details="Környékbeli kiváló éttermek és rejtett látnivalók integrálása"
                ),
                ResearchPlanStep(
                    step_id="itinerary_synthesis",
                    label="Napi Bontású Részletes Útiterv Szintézis",
                    provider="Decision Engine",
                    estimated_duration_sec=1.0,
                    details="Teljes napirend, térkép és tanácsadói magyarázat összeállítása"
                )
            ]

        elif intent_key == "FIND_BETTER_COMPONENT":
            steps = [
                ResearchPlanStep(
                    step_id="component_eval",
                    label="Meglévő Elem Értékelése",
                    provider="Component Analyzer",
                    estimated_duration_sec=0.5,
                    details="Jelenlegi ár, csillagszám, lokáció és feltételek elemzése"
                ),
                ResearchPlanStep(
                    step_id="market_sweep",
                    label="Célzott Alternatívák Piacfeltárása",
                    provider="Kiwi / Cozycozy APIs",
                    estimated_duration_sec=2.5,
                    details="Ugyanazon desztináción és idősávban elérhető prémium opciók lekérése"
                ),
                ResearchPlanStep(
                    step_id="pareto_filtering",
                    label="Szigorúan Jobb (Pareto) Szűrés",
                    provider="Optimization Engine",
                    estimated_duration_sec=1.0,
                    details="Kizárólag jobb árú VAGY magasabb minőségű alternatívák megtartása"
                ),
                ResearchPlanStep(
                    step_id="tradeoff_summary",
                    label="Trade-off & Előny-Hátrány Elemzés",
                    provider="Decision Engine",
                    estimated_duration_sec=1.0,
                    details="Konkrét megtakarítás vagy minőségi ugrás számszerű magyarázata"
                )
            ]

        elif intent_key == "MIXED_SCOPE_COMPETITION":
            steps = [
                ResearchPlanStep(
                    step_id="dest_competition",
                    label="Célállomások Párhuzamos Versenyeztetése",
                    provider="Climate & Numbeo KG",
                    estimated_duration_sec=1.5,
                    details="Versengő célvárosok összehasonlító profilozása"
                ),
                ResearchPlanStep(
                    step_id="parallel_flight_search",
                    label="Párhuzamos Járatkeresés Célpontonként",
                    provider="Kiwi GraphQL API",
                    estimated_duration_sec=2.5,
                    details="Menetrendek és jegyárak párhuzamos lekérdezése"
                ),
                ResearchPlanStep(
                    step_id="parallel_stay_search",
                    label="Párhuzamos Szálláskeresés",
                    provider="Cozycozy Live API",
                    estimated_duration_sec=2.5,
                    details="Minőségi szállások árai és elérhetőségei célpontonként"
                ),
                ResearchPlanStep(
                    step_id="promethee_ranking",
                    label="PROMETHEE Rangsor & Trade-off Szintézis",
                    provider="Decision Engine",
                    estimated_duration_sec=1.5,
                    details="Célállomásonkénti legjobb opció kiválasztása és összehasonlítása"
                )
            ]

        else:  # FLIGHT_FIRST or KNOWN_DESTINATION_FULL
            steps = [
                ResearchPlanStep(
                    step_id="flight_search",
                    label="Optimalizált Járatkeresés",
                    provider="Kiwi GraphQL API",
                    estimated_duration_sec=2.0,
                    details="Közvetlen járatok és legkényelmesebb menetrendek lekérése"
                ),
                ResearchPlanStep(
                    step_id="stay_search",
                    label="Minőségi Szállások Keresése",
                    provider="Cozycozy Live API",
                    estimated_duration_sec=2.0,
                    details="Központi 4-5 csillagos hotelek és butikhotelek szűrése"
                ),
                ResearchPlanStep(
                    step_id="geo_logistics",
                    label="Helyi Logisztika & Transzferek",
                    provider="OSM / Routing API",
                    estimated_duration_sec=1.0,
                    details="Reális repülőtéri és belvárosi utazási idők kalkulációja"
                ),
                ResearchPlanStep(
                    step_id="experiences",
                    label="Élmények & Látványosságok",
                    provider="Experience KG",
                    estimated_duration_sec=1.5,
                    details="Személyre szabott programok és látnivalók kiválasztása"
                ),
                ResearchPlanStep(
                    step_id="synthesis",
                    label="3 Karakteres Opció Szintézise",
                    provider="Decision Engine",
                    estimated_duration_sec=1.0,
                    details="Legjobb összkép, prémium élmény és költséghatékony alternatívák felépítése"
                )
            ]

        total_sec = sum(s.estimated_duration_sec for s in steps)
        return ResearchPlan(
            intent=intent_key,
            summary=intent_text,
            steps=steps,
            total_estimated_sec=round(total_sec, 1)
        )

    @classmethod
    def generate_missing_info_matrix(cls, state: ResearchState) -> List[MissingInfoMatrixItem]:
        """
        Builds the canonical "Mi van / Mi nincs?" evaluation table.
        """
        know = state.what_we_know
        matters = state.what_matters
        items: List[MissingInfoMatrixItem] = []

        # 1. Ügyfél
        has_client = bool(know.client_id)
        items.append(MissingInfoMatrixItem(
            field_key="client",
            label="Ügyfél Profil",
            has_value=has_client,
            is_certain=has_client,
            current_value_repr=know.client_name or "Nincs kiválasztva",
            system_action="Tartós preferenciák és korábbi utak betöltve" if has_client else "Általános alapértelmezések alkalmazása",
            urgency="recommended"
        ))

        # 2. Célállomás
        has_dest = bool(know.destination or len(know.candidate_destinations) > 0)
        dest_str = know.destination or (", ".join(know.candidate_destinations) if know.candidate_destinations else "Nincs megadva")
        items.append(MissingInfoMatrixItem(
            field_key="destination",
            label="Célállomás / Desztináció",
            has_value=has_dest,
            is_certain=bool(know.destination and len(know.candidate_destinations) <= 1),
            current_value_repr=dest_str,
            system_action="Fókuszált járat és szálláskutatás" if has_dest else "40+ európai város többpilléres rangsorolása",
            urgency="required" if not has_dest else "normal"
        ))

        # 3. Dátumok és Időtartam
        has_dates = bool(
            (know.date_mode == "exact" and know.exact_out_date and know.exact_in_date) or
            (know.date_mode == "interval" and know.date_range_start) or
            (know.date_mode == "month" and know.month)
        )
        if know.date_mode == "exact" and know.exact_out_date:
            date_repr = f"{know.exact_out_date} – {know.exact_in_date} ({know.duration_days} nap)"
        elif know.date_mode == "month":
            date_repr = f"{know.month}. hónap ({know.duration_days} nap)"
        else:
            date_repr = f"Rugalmas ({know.duration_days} nap)"

        items.append(MissingInfoMatrixItem(
            field_key="dates",
            label="Utazási Dátumok",
            has_value=has_dates,
            is_certain=(know.date_mode == "exact" and has_dates),
            current_value_repr=date_repr,
            system_action="Fix dátumos járat- és szálláslekérdezés" if (know.date_mode == "exact") else "Rugalmas menetrendi ablak pásztázása",
            urgency="required"
        ))

        # 4. Költségvetési Keret
        has_budget = bool(know.total_budget and know.total_budget > 0)
        budget_repr = f"{int(know.total_budget):,} {know.budget_currency} ({know.budget_hardness})".replace(",", " ") if has_budget else "Nincs korlát megadva"
        items.append(MissingInfoMatrixItem(
            field_key="budget",
            label="Költségvetési Keret",
            has_value=has_budget,
            is_certain=has_budget,
            current_value_repr=budget_repr,
            system_action="Szigorú Pass/Fail költségplafon érvényesítése" if (has_budget and know.budget_hardness == "hard") else "Érték-alapú optimalizálás",
            urgency="required" if not has_budget else "normal"
        ))

        # 5. Meglévő Repülőjegy
        fixed_flight = any(c.component_type == "flight" and c.action == ComponentIntentAction.KEEP for c in know.existing_components)
        items.append(MissingInfoMatrixItem(
            field_key="flight",
            label="Repülőjárat",
            has_value=fixed_flight,
            is_certain=fixed_flight,
            current_value_repr="Meglévő repülőjegy rögzítve" if fixed_flight else "Nincs (Kutatás szükséges)",
            system_action="Járat zárolva, menetrendhez igazítás" if fixed_flight else "Élő Kiwi GraphQL járatkeresés & PROMETHEE rangsor",
            urgency="normal"
        ))

        # 6. Meglévő Szállás
        fixed_stay = any(c.component_type == "stay" and c.action == ComponentIntentAction.KEEP for c in know.existing_components)
        items.append(MissingInfoMatrixItem(
            field_key="stay",
            label="Szállás",
            has_value=fixed_stay,
            is_certain=fixed_stay,
            current_value_repr="Meglévő szállás rögzítve" if fixed_stay else "Nincs (Kutatás szükséges)",
            system_action="Szállás zárolva, lokációhoz igazítás" if fixed_stay else "Élő Cozycozy szállásaggregáció & minőségi szűrés",
            urgency="normal"
        ))

        # 7. Aktív Döntési Dimenziók
        dim_count = len(matters.selected_dimensions)
        items.append(MissingInfoMatrixItem(
            field_key="dimensions",
            label="Döntési Dimenziók & Súlyok",
            has_value=(dim_count > 0),
            is_certain=(len(matters.ahp_weights) > 0),
            current_value_repr=f"{dim_count} dimenzió aktív ({', '.join(matters.selected_dimensions[:3])}...)",
            system_action="AHP páros súlyozás és PROMETHEE outranking",
            urgency="recommended"
        ))

        return items

    @classmethod
    def confirm_intent(
        cls,
        case_id: str,
        confirmed: bool = True,
        override_intent: Optional[str] = None
    ) -> Optional[ResearchState]:
        """
        Confirms or overrides the research intent for a given Case.
        Transitions the phase from UNDERSTAND to DEFINE upon confirmation.
        """
        if case_id not in _RESEARCH_STATES:
            return None

        state = _RESEARCH_STATES[case_id]
        state.intent_confirmed = confirmed
        state.what_still_needs_decision.intent_confirmed = confirmed
        if override_intent:
            state.resolved_intent = override_intent
            state.research_plan = cls.generate_dynamic_research_plan(
                override_intent,
                state.intent_summary or "",
                state.what_we_know,
                state.what_is_fixed
            )

        if confirmed and state.phase == ResearchStatePhase.UNDERSTAND:
            state.phase = ResearchStatePhase.DEFINE

        state.updated_at = datetime.now(timezone.utc)
        return state

    @classmethod
    def update_component_intent(
        cls,
        case_id: str,
        component_type: str,
        action: ComponentIntentAction,
        component_id: Optional[str] = None,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[ResearchState]:
        """
        Updates or registers an existing component's intent (KEEP, REPLACE, IMPROVE)
        and automatically re-evaluates the Research Intent & Research Plan.
        """
        if case_id not in _RESEARCH_STATES:
            return None

        state = _RESEARCH_STATES[case_id]
        existing_list = state.what_we_know.existing_components

        # Find existing match or append
        found = False
        for comp in existing_list:
            if comp.component_type == component_type and (not component_id or comp.details.get("id") == component_id):
                comp.action = action
                if title:
                    comp.title = title
                if details:
                    comp.details.update(details)
                comp.is_locked = (action == ComponentIntentAction.KEEP)
                found = True
                break

        if not found:
            new_comp = ExistingComponent(
                component_type=component_type,
                action=action,
                title=title or f"Meglévő {component_type}",
                details=details or ({"id": component_id} if component_id else {}),
                is_locked=(action == ComponentIntentAction.KEEP)
            )
            existing_list.append(new_comp)

        # Recalculate Fixed components
        locked_flight_ids = [c.details.get("id") for c in existing_list if c.component_type == "flight" and c.action == ComponentIntentAction.KEEP and c.details.get("id")]
        locked_stay_ids = [c.details.get("id") for c in existing_list if c.component_type == "stay" and c.action == ComponentIntentAction.KEEP and c.details.get("id")]
        state.what_is_fixed.locked_flight_ids = locked_flight_ids
        state.what_is_fixed.locked_stay_ids = locked_stay_ids

        # Re-resolve intent and plan
        intent_key, intent_text = cls.resolve_research_intent(state.what_we_know, state.what_is_fixed, existing_list)
        state.resolved_intent = intent_key
        state.intent_summary = intent_text
        state.research_plan = cls.generate_dynamic_research_plan(intent_key, intent_text, state.what_we_know, state.what_is_fixed)
        state.updated_at = datetime.now(timezone.utc)

        return state
