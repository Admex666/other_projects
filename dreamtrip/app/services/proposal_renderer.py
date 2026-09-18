"""
Optivoya Shared Intelligence — Proposal Renderer Service
Generates structured HTML & printable proposals for B2C Single Trip and B2B Multi-Option Client Proposals.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class ProposalRenderer:
    """
    Unified proposal renderer supporting SingleTripProposal (B2C) and MultiOptionProposal (B2B).
    """

    @classmethod
    def render_single_trip_html(
        cls,
        trip_data: Dict[str, Any],
        agency_name: str = "Optivoya Travel Advisory"
    ) -> str:
        """
        Renders a printable single-trip proposal document.
        """
        dest = trip_data.get("destination", {})
        flight = trip_data.get("flight", {})
        stay = trip_data.get("accommodation", {})
        breakdown = trip_data.get("breakdown", {})

        dest_name = dest.get("name") or dest.get("city", "Célállomás")
        dest_country = dest.get("country", "")

        return f"""<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <title>Utazási Ajánlat — {dest_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #0f172a; line-height: 1.5; padding: 40px; max-width: 800px; margin: 0 auto; }}
        .header {{ border-bottom: 2px solid #2563eb; padding-bottom: 16px; margin-bottom: 24px; }}
        .agency {{ font-size: 12px; font-weight: 800; color: #2563eb; text-transform: uppercase; }}
        .title {{ font-size: 26px; font-weight: 900; margin: 4px 0; }}
        .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 16px; }}
        .card-title {{ font-size: 13px; font-weight: 800; color: #2563eb; text-transform: uppercase; margin-bottom: 6px; }}
        .total-box {{ background: #0f172a; color: #ffffff; border-radius: 12px; padding: 20px; display: flex; justify-content: space-between; align-items: center; margin-top: 24px; }}
        .total-num {{ font-size: 24px; font-weight: 900; color: #38bdf8; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="agency">{agency_name}</div>
        <div class="title">{dest_name}, {dest_country} Utazási Terv</div>
        <div>Generálva: {datetime.now().strftime('%Y.%m.%d')}</div>
    </div>

    <div class="card">
        <div class="card-title">📍 Célállomás</div>
        <strong>{dest_name}, {dest_country}</strong>
        <div>{dest.get('explanation', '')}</div>
    </div>

    <div class="card">
        <div class="card-title">✈️ Repülőjárat & Menetrend</div>
        <strong>{flight.get('airline', 'Repülőjárat')} Retúr</strong>
        <div>{flight.get('out_date', '')} – {flight.get('in_date', '')}</div>
        <div style="font-weight: 800; margin-top: 6px; color: #2563eb;">{round(float(flight.get('price_total_huf', flight.get('total_price_huf', 0)) or 0)):,} Ft</div>
    </div>

    <div class="card">
        <div class="card-title">🏨 Szállás</div>
        <strong>{stay.get('name', 'Szálloda')}</strong>
        <div>{stay.get('nights', 7)} éjszaka · Értékelés: {stay.get('rating_normalized', stay.get('rating', 8.5))}/10</div>
        <div style="font-weight: 800; margin-top: 6px; color: #2563eb;">{round(float(stay.get('price_total_huf', 0) or 0)):,} Ft</div>
    </div>

    <div class="total-box">
        <div>
            <div style="font-size: 12px; text-transform: uppercase; color: #94a3b8;">Becsült Teljes Költség</div>
            <div class="total-num">{round(float(breakdown.get('totalHuf', 0) or 0)):,} Ft</div>
        </div>
    </div>
</body>
</html>"""

    @classmethod
    def render_multi_option_html(
        cls,
        case_data: Dict[str, Any],
        options: List[Dict[str, Any]],
        agency_name: str = "Optivoya B2B Advisory",
        advisor_name: str = "Utazási Szakértő",
        notes: str = ""
    ) -> str:
        """
        Renders an agency-branded 3-option comparison proposal document.
        """
        client_name = case_data.get("client_name", "Kedves Ügyfelünk")
        case_title = case_data.get("title", "Személyre Szabott Utazási Javaslat")

        options_html = ""
        for opt in options:
            opt_title = opt.get("title", "Utazási Opció")
            archetype = opt.get("archetype", "Standard")
            total_price = opt.get("total_price_huf", 0)
            per_person = opt.get("price_per_person_huf", 0)
            dest = opt.get("destination", {})
            flight = opt.get("flight", {})
            stay = opt.get("stay", {})

            options_html += f"""
            <div class="option-card">
                <div class="option-header">
                    <div>
                        <span class="badge badge-{archetype.lower()}">{archetype.upper()}</span>
                        <h2 style="margin: 4px 0; font-size: 20px;">{opt_title}</h2>
                        <div style="color: #64748b; font-size: 13px;">📍 {dest.get('name', '')}, {dest.get('country', '')}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 22px; font-weight: 900; color: #0f172a; font-family: monospace;">{round(total_price):,} Ft</div>
                        <div style="font-size: 12px; color: #64748b;">~{round(per_person):,} Ft / fő</div>
                    </div>
                </div>

                <div class="option-details">
                    <div class="detail-row">
                        <strong>✈️ Járat:</strong> {flight.get('airline', 'Járat')} ({flight.get('out_date', '')} – {flight.get('in_date', '')}) · {flight.get('stops', 0)} átszállás
                    </div>
                    <div class="detail-row">
                        <strong>🏨 Szállás:</strong> {stay.get('name', 'Szállás')} ({stay.get('stars', 3)}★ · {stay.get('rating', 8.5)}/10)
                    </div>
                    {f'<div class="detail-row" style="margin-top: 8px; font-style: italic; color: #0284c7;">💡 {opt.get("why_this_option", "")}</div>' if opt.get("why_this_option") else ''}
                </div>
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <title>{case_title} — {agency_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #0f172a; line-height: 1.5; padding: 40px; max-width: 900px; margin: 0 auto; }}
        .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: flex-end; }}
        .agency-brand {{ font-size: 14px; font-weight: 800; color: #2563eb; text-transform: uppercase; letter-spacing: 0.5px; }}
        .option-card {{ border: 1.5px solid #cbd5e1; border-radius: 16px; padding: 24px; margin-bottom: 24px; page-break-inside: avoid; }}
        .option-header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #f1f5f9; padding-bottom: 14px; margin-bottom: 14px; }}
        .badge {{ font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; background: #e0f2fe; color: #0369a1; }}
        .badge-best_overall {{ background: #dcfce7; color: #15803d; }}
        .badge-best_value {{ background: #e0f2fe; color: #0369a1; }}
        .badge-best_experience {{ background: #f3e8ff; color: #7e22ce; }}
        .detail-row {{ margin-bottom: 6px; font-size: 14px; }}
        .notes-box {{ background: #f8fafc; border-left: 4px solid #2563eb; padding: 16px; border-radius: 0 12px 12px 0; margin-top: 24px; }}
        @media print {{ body {{ padding: 20px; }} }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="agency-brand">{agency_name}</div>
            <h1 style="font-size: 28px; font-weight: 900; margin: 6px 0;">{case_title}</h1>
            <div style="color: #64748b;">Ügyfél: <strong>{client_name}</strong> · Tanácsadó: {advisor_name}</div>
        </div>
        <div style="font-size: 12px; color: #94a3b8; text-align: right;">
            Dátum: {datetime.now().strftime('%Y.%m.%d')}<br>
            Ajánlat azonosító: {case_data.get('id', 'PROP-001')}
        </div>
    </div>

    <div>
        {options_html}
    </div>

    {f'<div class="notes-box"><strong>Tanácsadói összefoglaló:</strong><br>{notes}</div>' if notes else ''}
</body>
</html>"""
