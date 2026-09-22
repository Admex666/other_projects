"""
Optivoya Advisor Workspace — Multi-Option Proposal Service (Phase 8)
=====================================================================
Handles proposal generation, editing, versioning (v1, v2, v3),
and print/export rendering for 1-3 shortlisted options.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.models.advisor_models import (
    Proposal, ProposalVersion, TripCase, Client, TripOption,
    generate_uuid, utc_now
)


class ProposalService:
    """
    Manages client proposal generation, versioning, and document snapshotting.
    """

    @classmethod
    def create_proposal(
        cls,
        trip_case: TripCase,
        client: Client,
        options: List[Dict[str, Any]],
        title: Optional[str] = None,
        client_intro: Optional[str] = None,
        advisor_notes: Optional[str] = None,
        recommendation_summary: Optional[str] = None,
        agency_name: str = "Optivoya Travel Advisory"
    ) -> Dict[str, Any]:
        """
        Generates a new initial proposal (v1) snapshot from selected options.
        """
        proposal_id = f"prop_{generate_uuid()[:8]}"
        destination_name = getattr(trip_case, "destination_focus", None) or getattr(trip_case, "destination_city", None) or "Európa"

        default_title = f"Személyre Szabott Utazási Ajánlat — {destination_name}"
        default_intro = (
            f"Kedves {client.name}!\n\n"
            f"Örömmel állítottuk össze a(z) {destination_name} utazásodhoz a legoptimálisabb opciókat, "
            f"figyelembe véve az időpontot, a kényelmi preferenciáidat és a költségkeretet. "
            f"Az alábbiakban 3 eltérő döntési archetípust találsz a részletes programokkal és árakkal."
        )
        default_rec = (
            "Szakértői javaslatunk az 'Option A (Best Overall)' választása a kiváló ár-érték arány "
            "és a közvetlen járatmenetrend miatt, de kényelmi fókusz esetén az 'Option C' is kiemelkedő."
        )

        proposal_doc = {
            "id": proposal_id,
            "case_id": trip_case.id,
            "client_id": client.id,
            "client_name": client.name,
            "client_email": client.email,
            "version": 1,
            "title": title or default_title,
            "client_intro": client_intro or default_intro,
            "advisor_notes": advisor_notes or "",
            "recommendation_summary": recommendation_summary or default_rec,
            "selected_option_ids": [o.get("id") for o in options if o.get("id")],
            "options_snapshot": options,
            "total_options_count": len(options),
            "agency_name": agency_name,
            "agency_logo_url": "/static/logo.png",
            "status": "DRAFT",
            "created_at": utc_now(),
            "updated_at": utc_now()
        }

        return proposal_doc

    @classmethod
    def create_next_version(
        cls,
        base_proposal: Dict[str, Any],
        updated_options: List[Dict[str, Any]],
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a new version (v2, v3...) branching from an existing proposal.
        """
        new_version_num = base_proposal.get("version", 1) + 1
        new_proposal = dict(base_proposal)
        new_proposal["id"] = f"prop_{generate_uuid()[:8]}"
        new_proposal["version"] = new_version_num
        new_proposal["options_snapshot"] = updated_options
        new_proposal["selected_option_ids"] = [o.get("id") for o in updated_options if o.get("id")]
        new_proposal["total_options_count"] = len(updated_options)
        new_proposal["status"] = "DRAFT"
        new_proposal["updated_at"] = utc_now()
        new_proposal["created_at"] = utc_now()

        if reason:
            curr_notes = new_proposal.get("advisor_notes", "")
            new_proposal["advisor_notes"] = f"{curr_notes}\n\n[v{new_version_num} Módosítás]: {reason}".strip()

        return new_proposal

    @classmethod
    def update_proposal(
        cls,
        proposal: Dict[str, Any],
        title: Optional[str] = None,
        client_intro: Optional[str] = None,
        advisor_notes: Optional[str] = None,
        recommendation_summary: Optional[str] = None,
        selected_option_ids: Optional[List[str]] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates editable metadata and visible option filters of a proposal.
        """
        if title is not None: proposal["title"] = title
        if client_intro is not None: proposal["client_intro"] = client_intro
        if advisor_notes is not None: proposal["advisor_notes"] = advisor_notes
        if recommendation_summary is not None: proposal["recommendation_summary"] = recommendation_summary
        if status is not None: proposal["status"] = status

        if selected_option_ids is not None:
            proposal["selected_option_ids"] = selected_option_ids
            # Filter snapshot options
            all_opts = proposal.get("options_snapshot", [])
            proposal["total_options_count"] = len([o for o in all_opts if o.get("id") in selected_option_ids])

        proposal["updated_at"] = utc_now()
        return proposal
