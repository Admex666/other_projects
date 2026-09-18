"""
Optivoya Test Suite — Phase 1: Advisor Models & Domain Validation
Tests Pydantic validation, multi-tenancy hierarchies, Provenance freshness,
Hard/Soft constraint evaluation, and 3-Option archetype models.
"""

import unittest
from datetime import datetime, timedelta, timezone
from app.models.advisor_models import (
    Agency,
    Advisor,
    Client,
    ClientPreferences,
    TripCase,
    TripCaseStatus,
    ResearchScope,
    BudgetMode,
    HardConstraints,
    SoftPreferences,
    ResolvedTripPreferences,
    ProviderProvenance,
    VerificationStatus,
    TripOption,
    OptionArchetype,
    Proposal,
    ProposalVersion
)


class TestAdvisorModels(unittest.TestCase):

    def test_agency_and_advisor_hierarchy(self):
        """Tests Agency and Advisor creation with default branding and UUID prefix."""
        agency = Agency(name="Apex Travel Boutique", slug="apex-travel")
        self.assertTrue(agency.id.startswith("agency_"))
        self.assertEqual(agency.branding.primary_color, "#2563eb")

        advisor = Advisor(
            agency_id=agency.id,
            name="Kovács Katalin",
            email="katalin@apextravel.com",
            role="lead_advisor"
        )
        self.assertTrue(advisor.id.startswith("adv_"))
        self.assertEqual(advisor.agency_id, agency.id)

    def test_client_creation_and_preferences(self):
        """Tests Client model with persistent travel preferences."""
        prefs = ClientPreferences(
            preferred_origins=["Budapest (BUD)", "Bécs (VIE)"],
            direct_flights_only=True,
            hotel_min_stars=4,
            interests=["gastronomy", "beach"]
        )

        client = Client(
            agency_id="agency_123",
            advisor_id="adv_456",
            name="Nagy Gábor",
            email="gabor.nagy@example.com",
            preferences=prefs
        )

        self.assertTrue(client.id.startswith("cli_"))
        self.assertTrue(client.preferences.direct_flights_only)
        self.assertEqual(client.preferences.hotel_min_stars, 4)

    def test_provenance_freshness_and_status(self):
        """Tests ProviderProvenance TTL calculation and freshness verification."""
        now = datetime.now(timezone.utc)
        fresh_prov = ProviderProvenance(
            provider="Kiwi",
            checked_at=now - timedelta(minutes=10),
            freshness_ttl_seconds=1800,  # 30 min TTL
            verification_status=VerificationStatus.VERIFIED
        )
        self.assertTrue(fresh_prov.is_fresh())

        stale_prov = ProviderProvenance(
            provider="Cozycozy",
            checked_at=now - timedelta(minutes=45),
            freshness_ttl_seconds=1800,
            verification_status=VerificationStatus.STALE
        )
        self.assertFalse(stale_prov.is_fresh())

    def test_hard_soft_constraint_hierarchy(self):
        """Tests HardConstraints vs SoftPreferences separation."""
        hard = HardConstraints(
            max_total_budget_huf=400000.0,
            direct_flights_only=True,
            min_hotel_stars=4,
            min_safety_score=60
        )

        soft = SoftPreferences(
            target_temperature=26.0,
            vibe_weights={"culture": 80.0, "beach": 90.0, "gastronomy": 95.0},
            budget_flexibility_pct=15.0
        )

        resolved = ResolvedTripPreferences(hard=hard, soft=soft)

        self.assertEqual(resolved.hard.max_total_budget_huf, 400000.0)
        self.assertTrue(resolved.hard.direct_flights_only)
        self.assertEqual(resolved.soft.target_temperature, 26.0)
        self.assertEqual(resolved.soft.vibe_weights["gastronomy"], 95.0)

    def test_trip_case_and_3_option_archetypes(self):
        """Tests TripCase and 3-Option archetype creation."""
        trip_case = TripCase(
            agency_id="agency_1",
            advisor_id="adv_1",
            client_id="cli_1",
            title="Nagy Család Római Nyaralás",
            scope=ResearchScope.FULL_TRIP,
            budget_mode=BudgetMode.TOTAL_BUDGET,
            total_budget_huf=500000.0,
            adults=2,
            duration_days=7
        )

        self.assertEqual(trip_case.status, TripCaseStatus.BRIEF)
        self.assertEqual(trip_case.duration_days, 7)

        # 3 Option Archetypes
        opt_a = TripOption(
            case_id=trip_case.id,
            archetype=OptionArchetype.BEST_OVERALL,
            title="Római Történelmi Élménycsomag",
            total_price_huf=420000.0,
            price_per_person_huf=210000.0,
            trip_score=92,
            why_this_option="Kiemelkedő központi szállás és kényelmes közvetlen járat."
        )

        opt_b = TripOption(
            case_id=trip_case.id,
            archetype=OptionArchetype.BEST_VALUE,
            title="Költségoptimalizált Róma",
            total_price_huf=310000.0,
            price_per_person_huf=155000.0,
            trip_score=84,
            why_this_option="26%-os megtakarítás kiváló metrókapcsolattal."
        )

        opt_c = TripOption(
            case_id=trip_case.id,
            archetype=OptionArchetype.BEST_EXPERIENCE,
            title="Prémium Gasztro & Kultúra Fókusz",
            total_price_huf=480000.0,
            price_per_person_huf=240000.0,
            trip_score=95,
            why_this_option="4 csillagos boutique hotel és Michelin ajánlott éttermek."
        )

        self.assertEqual(opt_a.archetype, OptionArchetype.BEST_OVERALL)
        self.assertEqual(opt_b.archetype, OptionArchetype.BEST_VALUE)
        self.assertEqual(opt_c.archetype, OptionArchetype.BEST_EXPERIENCE)
        self.assertGreater(opt_c.trip_score, opt_b.trip_score)

    def test_proposal_versioning(self):
        """Tests Proposal creation and multi-version snapshots."""
        prop = Proposal(
            case_id="case_1",
            agency_id="agency_1",
            advisor_id="adv_1",
            client_id="cli_1",
            title="Utazási Ajánlat — Róma 2026"
        )

        v1 = ProposalVersion(
            version_number=1,
            title="Utazási Ajánlat v1",
            intro_message="Kedves Gábor, összeállítottunk 3 kiváló opciót.",
            option_ids=["opt_1", "opt_2", "opt_3"]
        )
        prop.versions.append(v1)

        self.assertEqual(len(prop.versions), 1)
        self.assertEqual(prop.versions[0].version_number, 1)
        self.assertEqual(len(prop.shareable_token), 16)


if __name__ == "__main__":
    unittest.main()
