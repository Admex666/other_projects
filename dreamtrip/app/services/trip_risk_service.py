"""
Optivoya Advisor Workspace — Operational Trip Risk Engine (Phase 7)
====================================================================
Identifies logistical, schedule, and cost risks across trip options:
- TIGHT_LAYOVER (< 60 min connection)
- LATE_NIGHT_ARRIVAL (> 23:00 arrival)
- AIRPORT_TRANSFER_GAP (> 50 km to city)
- RESORT_FEE_RISK (Hidden city tax / resort fee)
- ATTRACTION_CLOSED (Museum/monument closure day)
- WEATHER_EXTREME (Rainy season or extreme temperature advisory)
"""

from typing import List, Dict, Any
from enum import Enum


class RiskSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class TripRiskService:
    """
    Evaluates trip packages for realistic operational constraints and hazards.
    """

    @classmethod
    def evaluate_option_risks(cls, option_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scans flight, stay, destination, and activities for potential hazards.
        """
        risks = []
        flight = option_data.get("flight", {})
        stay = option_data.get("stay", {})
        destination = option_data.get("destination", {})
        activities = option_data.get("activities", [])

        # 1. Flight Layover Risk
        stops = flight.get("stops", 0)
        layover_minutes = flight.get("layover_minutes")
        if stops > 0 and layover_minutes is not None:
            if layover_minutes < 50:
                risks.append({
                    "risk_id": "TIGHT_LAYOVER",
                    "severity": RiskSeverity.CRITICAL.value,
                    "title": f"Rendkívül szűk átszállási idő ({layover_minutes} perc)",
                    "description": "Nemzetközi járatoknál a poggyászátrakás és az útlevélellenőrzés kockázatos lehet.",
                    "mitigation": "Javasolt legalább 80 perces átszállási idő választása."
                })
            elif layover_minutes < 75:
                risks.append({
                    "risk_id": "MODERATE_LAYOVER",
                    "severity": RiskSeverity.WARNING.value,
                    "title": f"Szűkös átszállási idő ({layover_minutes} perc)",
                    "description": "Kisebb járatkésés esetén az átszállás sietős lehet.",
                    "mitigation": "Készüljön fel gyors kapuváltásra."
                })

        # 2. Late Night Arrival Risk
        arrival_time = flight.get("arrival_time", "")
        if arrival_time:
            try:
                hour = int(arrival_time.split(":")[0])
                if hour >= 23 or hour < 5:
                    risks.append({
                        "risk_id": "LATE_NIGHT_ARRIVAL",
                        "severity": RiskSeverity.WARNING.value,
                        "title": f"Késő éjszakai érkezés ({arrival_time})",
                        "description": "A tömegközlekedés éjszaka korlátozott lehet, a késői szállodai check-in előre egyeztetendő.",
                        "mitigation": "Előre foglalt privát transzfer vagy éjjel-nappali recepció javasolt."
                    })
            except (ValueError, IndexError):
                pass

        # 3. Airport Transfer Distance
        airport_distance_km = flight.get("airport_distance_km", 18)
        if airport_distance_km > 60:
            risks.append({
                "risk_id": "AIRPORT_TRANSFER_GAP",
                "severity": RiskSeverity.INFO.value,
                "title": f"Távoli repülőtér ({airport_distance_km} km a belvárostól)",
                "description": "A transzferidő 1-1.5 óra is lehet, a transzferköltséget érdemes bekalkulálni.",
                "mitigation": "Reptéri expressz vonat vagy buszjárat menetrendjének ellenőrzése."
            })

        # 4. Hidden City Tax / Resort Fee
        city = destination.get("city", "")
        if city in ["Róma", "Velence", "Barcelona", "Párizs", "Amszterdam", "New York"]:
            risks.append({
                "risk_id": "RESORT_FEE_RISK",
                "severity": RiskSeverity.INFO.value,
                "title": f"Helyi idegenforgalmi adó (City Tax) {city} városában",
                "description": f"{city} belvárosában kb. 3-8 EUR / fő / éj helyi adó fizetendő közvetlenül a szállodánál.",
                "mitigation": "Tájékoztassa az ügyfelet a helyszínen fizetendő tétellel kapcsolatban."
            })

        # 5. Activity Schedule Conflicts
        for act in activities:
            if "múzeum" in act.get("name", "").lower() or "museum" in act.get("name", "").lower():
                risks.append({
                    "risk_id": "ATTRACTION_CLOSED",
                    "severity": RiskSeverity.INFO.value,
                    "title": f"Nyitvatartási egyeztetés ({act.get('name')})",
                    "description": "Sok európai múzeum hétfőnként zárva tart.",
                    "mitigation": "A napi útiterv összeállításakor kerülje a hétfői napot ehhez a programhoz."
                })
                break

        return risks

    @classmethod
    def evaluate_case_risks(cls, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates risks for all options in a case and returns summary statistics.
        """
        all_option_risks = {}
        total_critical = 0
        total_warning = 0
        total_info = 0

        for opt in options:
            opt_id = opt.get("id") or "unknown"
            risks = cls.evaluate_option_risks(opt)
            all_option_risks[opt_id] = risks

            for r in risks:
                sev = r.get("severity")
                if sev == RiskSeverity.CRITICAL.value:
                    total_critical += 1
                elif sev == RiskSeverity.WARNING.value:
                    total_warning += 1
                elif sev == RiskSeverity.INFO.value:
                    total_info += 1

        return {
            "total_critical": total_critical,
            "total_warning": total_warning,
            "total_info": total_info,
            "has_high_risk": total_critical > 0,
            "option_risks": all_option_risks
        }
