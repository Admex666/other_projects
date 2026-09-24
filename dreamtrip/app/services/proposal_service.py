"""
Optivoya Advisor Workspace — Multi-Option Proposal Service (Phase 8)
=====================================================================
Handles proposal generation, editing, versioning (v1, v2, v3),
cryptographically secure token sharing, client-safe rendering,
and print/export rendering for 1-3 shortlisted options.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import secrets
import hashlib
from app.models.advisor_models import (
    Proposal, ProposalVersion, ProposalShare, TripCase, Client, TripOption,
    generate_uuid, utc_now
)


class ProposalService:
    """
    Manages client proposal generation, versioning, document snapshotting,
    and secure revocable public sharing.
    """

    # In-memory store for active Proposal Shares (token -> ProposalShare)
    _SHARES_STORE: Dict[str, ProposalShare] = {}

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

    @classmethod
    def create_share_token(
        cls,
        proposal_id: str,
        version_number: int = 1,
        expires_in_days: int = 30
    ) -> ProposalShare:
        """
        Generates a cryptographically random, revocable public access token for client sharing.
        """
        from app.repositories.advisor_repository import ProposalShareRepository

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = utc_now() + timedelta(days=expires_in_days) if expires_in_days > 0 else None

        share = ProposalShare(
            id=f"share_{generate_uuid()[:8]}",
            proposal_id=proposal_id,
            proposal_version_number=version_number,
            token=raw_token,
            token_hash=token_hash,
            expires_at=expires_at
        )

        cls._SHARES_STORE[raw_token] = share
        cls._SHARES_STORE[token_hash] = share
        ProposalShareRepository.save_share(share)
        return share

    @classmethod
    def get_share_by_token(cls, token: str) -> Optional[ProposalShare]:
        """Validates and returns the share record if active and not expired."""
        from app.repositories.advisor_repository import ProposalShareRepository

        share = cls._SHARES_STORE.get(token)
        if not share:
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            share = ProposalShareRepository.get_share_by_token(token_hash)
            if not share:
                share = ProposalShareRepository.get_share_by_token(token)

        if not share or not share.is_valid():
            return None

        share.access_count += 1
        share.last_accessed_at = utc_now()
        cls._SHARES_STORE[token] = share
        if share.token_hash:
            cls._SHARES_STORE[share.token_hash] = share
        ProposalShareRepository.save_share(share)
        return share

    @classmethod
    def revoke_share_token(cls, token: str) -> bool:
        """Revokes an active share token."""
        from app.repositories.advisor_repository import ProposalShareRepository

        share = cls.get_share_by_token(token)
        if not share:
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            ProposalShareRepository.revoke_share(token_hash)
            ProposalShareRepository.revoke_share(token)
            return True

        share.is_revoked = True
        share.revoked_at = utc_now()
        cls._SHARES_STORE[token] = share
        if share.token_hash:
            cls._SHARES_STORE[share.token_hash] = share
        ProposalShareRepository.save_share(share)
        return True

    @classmethod
    def get_client_safe_proposal(cls, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strips private internal advisor notes, debug scores, and sensitive CRM references,
        leaving only client-facing proposal data.
        """
        client_safe = dict(proposal)
        client_safe.pop("advisor_notes", None)
        client_safe.pop("internal_risk_details", None)
        client_safe.pop("debug_telemetry", None)

        # Clean versions
        clean_versions = []
        for v in client_safe.get("versions", []):
            vd = dict(v) if isinstance(v, dict) else (v.model_dump() if hasattr(v, "model_dump") else dict(v))
            vd.pop("advisor_notes", None)
            clean_versions.append(vd)
        if clean_versions:
            client_safe["versions"] = clean_versions

        # Clean options
        clean_opts = []
        for opt in client_safe.get("options_snapshot", []):
            o = dict(opt)
            o.pop("debug_weights", None)
            clean_opts.append(o)
        client_safe["options_snapshot"] = clean_opts

        return client_safe
