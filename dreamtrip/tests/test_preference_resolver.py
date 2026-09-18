"""
Optivoya Shared Intelligence — Preference Resolver Tests
Validates the 4-layer preference hierarchy and 3-mode budget validation:
Layer 4 (Overrides) > Layer 3 (Case Brief) > Layer 2 (Client Profile) > Layer 1 (Defaults)
"""

import unittest
from app.models.advisor_models import (
    TripCase, Client, ClientPreferences,
    HardConstraints, SoftPreferences, AvoidRules, NiceToHave,
    AdvisorOverrides, ResolvedTripPreferences, BudgetMode, TripCaseStatus
)
from app.services.preference_resolver import PreferenceResolver


class TestPreferenceResolver(unittest.TestCase):

    def test_layer1_system_defaults(self):
        """Empty case with no client profile should resolve to sane system defaults."""
        case = TripCase(
            agency_id="agency_1",
            advisor_id="adv_1",
            client_id="cli_1"
        )
        resolved = PreferenceResolver.resolve_preferences(case)
        self.assertIsNotNone(resolved.hard)
        self.assertEqual(resolved.hard.min_hotel_stars, 3)
        self.assertEqual(resolved.hard.min_hotel_rating, 7.5)
        self.assertFalse(resolved.hard.direct_flights_only)
        self.assertEqual(resolved.soft.target_temperature, 24.0)

    def test_layer2_client_profile_inheritance(self):
        """Persistent client travel profile should propagate to resolved constraints."""
        client = Client(
            id="cli_luxury",
            agency_id="agency_1",
            advisor_id="adv_1",
            name="Varga Zoltán",
            email="varga@test.com",
            preferences=ClientPreferences(
                hotel_min_stars=5,
                hotel_min_rating=9.2,
                direct_flights_only=True,
                avoid_airlines=["W6", "FR"],
                interests=["gastronomy", "beach"]
            )
        )
        case = TripCase(
            agency_id="agency_1",
            advisor_id="adv_1",
            client_id="cli_luxury",
            total_budget_huf=1200000
        )
        resolved = PreferenceResolver.resolve_preferences(case, client=client)
        self.assertEqual(resolved.hard.min_hotel_stars, 5)
        self.assertEqual(resolved.hard.min_hotel_rating, 9.2)
        self.assertTrue(resolved.hard.direct_flights_only)
        self.assertIn("W6", resolved.avoid.avoid_airlines)
        self.assertEqual(resolved.soft.vibe_weights["gastronomy"], 80.0)

    def test_layer3_case_brief_override(self):
        """Case Brief constraints should override Client Profile defaults."""
        client = Client(
            id="cli_1",
            agency_id="agency_1",
            advisor_id="adv_1",
            name="Nagy Éva",
            email="eva@test.com",
            preferences=ClientPreferences(
                hotel_min_stars=4,
                direct_flights_only=False
            )
        )
        # Case specifies strict direct flights only
        case = TripCase(
            agency_id="agency_1",
            advisor_id="adv_1",
            client_id="cli_1",
            preferences=ResolvedTripPreferences(
                hard=HardConstraints(
                    direct_flights_only=True,
                    min_hotel_stars=3
                )
            )
        )
        resolved = PreferenceResolver.resolve_preferences(case, client=client)
        self.assertTrue(resolved.hard.direct_flights_only)  # Case brief overrides client False
        self.assertEqual(resolved.hard.min_hotel_stars, 3)     # Case brief overrides client 4

    def test_layer4_advisor_overrides(self):
        """Advisor overrides should take absolute highest precedence."""
        case = TripCase(
            agency_id="agency_1",
            advisor_id="adv_1",
            client_id="cli_1",
            destination_focus="Paris"
        )
        overrides = AdvisorOverrides(
            pinned_destination="Nice",
            custom_markup_huf=25000
        )
        resolved = PreferenceResolver.resolve_preferences(case, advisor_overrides=overrides)
        self.assertEqual(case.destination_focus, "Nice")
        self.assertEqual(resolved.overrides.custom_markup_huf, 25000)

    def test_budget_mode_validations(self):
        """Validates Mode A (Total), Mode B (Component), and Mode C (Scope Only)."""
        # Mode A valid
        case_a = TripCase(agency_id="a1", advisor_id="ad1", client_id="c1", budget_mode=BudgetMode.TOTAL_BUDGET, total_budget_huf=450000)
        res_a = PreferenceResolver.validate_budget_mode(case_a)
        self.assertTrue(res_a["valid"])

        # Mode A missing budget
        case_a_bad = TripCase(agency_id="a1", advisor_id="ad1", client_id="c1", budget_mode=BudgetMode.TOTAL_BUDGET, total_budget_huf=None)
        res_a_bad = PreferenceResolver.validate_budget_mode(case_a_bad)
        self.assertFalse(res_a_bad["valid"])

        # Mode B valid
        case_b = TripCase(agency_id="a1", advisor_id="ad1", client_id="c1", budget_mode=BudgetMode.COMPONENT_BUDGETS, flight_budget_huf=90000, stay_budget_huf=250000)
        res_b = PreferenceResolver.validate_budget_mode(case_b)
        self.assertTrue(res_b["valid"])

        # Mode C valid
        case_c = TripCase(agency_id="a1", advisor_id="ad1", client_id="c1", budget_mode=BudgetMode.SCOPE_ONLY)
        res_c = PreferenceResolver.validate_budget_mode(case_c)
        self.assertTrue(res_c["valid"])


if __name__ == "__main__":
    unittest.main()
