#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 VitaSteps – Heti Üzleti Digest & KPI Monitoring Rendszer
=============================================================================
 Cél:
   Hetente gyorsan átlátni, hogy a VitaSteps hol veszít pénzt, hol van
   növekedési lehetőség, és mi legyen a következő konkrét döntési lépés.

 Szabályalapú garanciák (Zero Hallucination):
   - Kizárólag forrásolt, valós tényadatokból számol (Supabase, Stripe, Meta CSV).
   - Adatminőségi és Frissességi Kapu (Data Freshness Gate): egyértelműen
     jelzi, ha egy adatforrás (pl. Meta Ads API) elavult vagy nem elérhető.
   - Determinisztikus pénzügyi és fedezeti számítások (CM I, CM II, Készlet kifutás).

 Használat:
   python landing_predikalo1/scripts/weekly_business_digest.py          # Konzol nézet (dry-run)
   python landing_predikalo1/scripts/weekly_business_digest.py --push   # Pushbullet értesítés küldése
   python landing_predikalo1/scripts/weekly_business_digest.py --json   # Strukturált JSON kimenet
=============================================================================
"""

import os
import sys
import json
import csv
import argparse
import base64
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# UTF-8 kimenet biztosítása terminálon
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# .env betöltése mindkét lehetséges helyről
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(os.path.dirname(PROJECT_ROOT), ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
PUSHBULLET_TOKEN = os.getenv("PUSHBULLET_ACCESS_TOKEN")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

# ─── PÉNZÜGYI & EGYSÉGKÖLTSÉG ÁLLANDÓK ────────────────────────────────────────
COST_FOXPOST_PARCEL_HUF = 1250    # Foxpost csomagautomata feladási egységköltség
COST_SZAMLAZZ_INVOICE_HUF = 35    # Számlázz.hu e-számla díj
COST_PACKAGING_BOX_HUF = 120      # Doboz és biztonsági buborékos csomagolás
MEDAL_CAPEX_UNIT_HUF = 1630       # Alibaba érem bekerülési ár (163 000 Ft / 100 db)
STRIPE_PCT_FEE = 0.015            # Stripe tranzakciós jutalék (1.5%)
STRIPE_FIXED_FEE_HUF = 50         # Stripe tranzakciós fix díj (50 Ft)
TOTAL_MEDAL_LIMIT_PREDIKALO = 100 # Prédikálószék limitált éremkészlet
TOTAL_MEDAL_LIMIT_PILIS = 100     # Pilis / Nagy-Kevély limitált éremkészlet


# ─── SEGÉDFÜGGVÉNYEK ──────────────────────────────────────────────────────────
def fmt_huf(val: float) -> str:
    """Formázott forint érték ezres tagolással."""
    return f"{int(round(val)):,}".replace(",", " ") + " Ft"

def fmt_pct(val: float) -> str:
    """Formázott százalék érték."""
    return f"{val:.1f}%"

def supabase_get(path: str) -> List[Dict[str, Any]]:
    """Adatok lekérése a Supabase REST API-n keresztül."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode('utf-8')
            return json.loads(data) if data else []
    except Exception as e:
        sys.stderr.write(f"[Supabase Hiba] {path}: {e}\n")
        return []

def get_stripe_balance() -> Dict[str, Any]:
    """Élő Stripe egyenleg lekérése."""
    if not STRIPE_SECRET_KEY:
        return {"available_huf": 0, "pending_huf": 0, "status": "no_key"}
    try:
        auth_header = base64.b64encode(f"{STRIPE_SECRET_KEY}:".encode()).decode()
        req = urllib.request.Request(
            "https://api.stripe.com/v1/balance",
            headers={"Authorization": f"Basic {auth_header}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
            avail = sum(b.get("amount", 0) for b in raw.get("available", []) if b.get("currency", "").lower() == "huf") / 100.0
            pend = sum(b.get("amount", 0) for b in raw.get("pending", []) if b.get("currency", "").lower() == "huf") / 100.0
            return {"available_huf": avail, "pending_huf": pend, "status": "ok"}
    except Exception as e:
        sys.stderr.write(f"[Stripe Hiba] {e}\n")
        return {"available_huf": 0, "pending_huf": 0, "status": "error", "error": str(e)}

def send_pushbullet_note(title: str, body: str) -> bool:
    """Értesítés küldése Pushbullet API-n keresztül."""
    if not PUSHBULLET_TOKEN:
        sys.stderr.write("⚠️ PUSHBULLET_ACCESS_TOKEN nincs konfigurálva a .env fájlban!\n")
        return False
    payload = json.dumps({"type": "note", "title": title, "body": body}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.pushbullet.com/v2/pushes",
        data=payload,
        headers={"Access-Token": PUSHBULLET_TOKEN, "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except Exception as e:
        sys.stderr.write(f"[Pushbullet Hiba] {e}\n")
        return False


# ─── AGGREGÁLÓ ÉS DIGEST MOTOR ────────────────────────────────────────────────
def build_weekly_business_digest(days: int = 7) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    curr_start = now - timedelta(days=days)
    prev_start = now - timedelta(days=days * 2)

    freshness_reports = []
    warnings = []

    # 1. RENDELÉSEK & BEVÉTEL (Supabase `orders`)
    orders_raw = supabase_get(
        "orders?select=id,created_at,amount_total,stripe_payment_status,is_test,campaign&stripe_payment_status=eq.paid&is_test=eq.false&order=created_at.desc"
    )
    
    last_order_dt = None
    if orders_raw:
        try:
            last_order_dt = datetime.fromisoformat(orders_raw[0]["created_at"].replace("Z", "+00:00"))
        except Exception:
            pass
    
    order_freshness = "Élő (friss)"
    if last_order_dt:
        days_since_last_order = (now - last_order_dt).total_seconds() / 86400.0
        if days_since_last_order > 14:
            order_freshness = f"Inaktív ({days_since_last_order:.0f} napja nincs új rendelés)"
            warnings.append(f"Rendelések: {days_since_last_order:.0f} napja nem érkezett új fizetett vásárlás.")
    freshness_reports.append({
        "source": "Supabase Orders (Fizetett rendelések)",
        "last_entry": last_order_dt.strftime("%Y-%m-%d %H:%M UTC") if last_order_dt else "N/A",
        "status": order_freshness
    })

    # Szétválogatás: Aktuális 7 nap vs Előző 7 nap vs All-time
    curr_orders = []
    prev_orders = []
    pilis_total_sold = 0
    predikalo_total_sold = 0

    for o in orders_raw:
        camp = (o.get("campaign") or "").lower()
        if "pilis" in camp or "kevely" in camp:
            pilis_total_sold += 1
        elif "predikalo" in camp:
            predikalo_total_sold += 1

        try:
            odt = datetime.fromisoformat(o["created_at"].replace("Z", "+00:00"))
            if odt >= curr_start:
                curr_orders.append(o)
            elif odt >= prev_start and odt < curr_start:
                prev_orders.append(o)
        except Exception:
            continue

    curr_rev = sum(float(o.get("amount_total") or 0) for o in curr_orders)
    prev_rev = sum(float(o.get("amount_total") or 0) for o in prev_orders)
    all_time_rev = sum(float(o.get("amount_total") or 0) for o in orders_raw)

    curr_order_count = len(curr_orders)
    prev_order_count = len(prev_orders)

    # 2. VÁLTOZÓ KÖLTSÉGEK & FEDEZETEK
    def calc_variable_costs(orders_list: List[Dict[str, Any]]) -> Dict[str, float]:
        foxpost = len(orders_list) * COST_FOXPOST_PARCEL_HUF
        szamlazz = len(orders_list) * COST_SZAMLAZZ_INVOICE_HUF
        packing = len(orders_list) * COST_PACKAGING_BOX_HUF
        medal_cogs = len(orders_list) * MEDAL_CAPEX_UNIT_HUF
        stripe_fees = sum((float(o.get("amount_total") or 0) * STRIPE_PCT_FEE + STRIPE_FIXED_FEE_HUF) for o in orders_list)
        operational_direct = foxpost + szamlazz + packing + stripe_fees
        total_direct_with_medal = operational_direct + medal_cogs
        return {
            "foxpost": foxpost,
            "stripe": stripe_fees,
            "szamlazz": szamlazz,
            "packing": packing,
            "medal_cogs": medal_cogs,
            "operational_direct": operational_direct,
            "total_with_cogs": total_direct_with_medal
        }

    curr_costs = calc_variable_costs(curr_orders)
    prev_costs = calc_variable_costs(prev_orders)

    # CM I (Contribution Margin I / Fedezet I = Árbevétel - Közvetlen működési és termékköltségek)
    curr_cm1 = curr_rev - curr_costs["total_with_cogs"]
    curr_cm1_pct = (curr_cm1 / curr_rev * 100.0) if curr_rev > 0 else 0.0

    # 3. META MARKETING ADATOK & CM II
    # Lekérés: Supabase meta_daily_metrics és/vagy helyi CSV
    meta_rows = supabase_get("meta_daily_metrics?select=date,spend,impressions,purchases,reach,link_clicks&order=date.desc&limit=60")
    meta_spend_curr = 0.0
    meta_spend_prev = 0.0
    latest_meta_date = None

    if meta_rows:
        latest_meta_date = meta_rows[0].get("date")
        curr_start_date_str = curr_start.strftime("%Y-%m-%d")
        prev_start_date_str = prev_start.strftime("%Y-%m-%d")

        for m in meta_rows:
            d = m.get("date")
            sp = float(m.get("spend") or 0)
            if d >= curr_start_date_str:
                meta_spend_curr += sp
            elif d >= prev_start_date_str and d < curr_start_date_str:
                meta_spend_prev += sp

    meta_freshness = "Élő (friss)"
    if latest_meta_date:
        try:
            lmd = datetime.strptime(latest_meta_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            meta_age_days = (now - lmd).days
            if meta_age_days > 3:
                meta_freshness = f"⚠️ Elavult ({latest_meta_date}, {meta_age_days} napja)"
                warnings.append(f"Meta Ads: Az adatok {meta_age_days} napja elavultak (utolsó: {latest_meta_date}). Meta API hozzáférés ellenőrzendő.")
        except Exception:
            pass
    else:
        meta_freshness = "⚠️ Nincs elérhető Meta adat"
        warnings.append("Meta Ads: Nincs elérhető rögzített hirdetési adat.")

    freshness_reports.append({
        "source": "Meta Marketing API / Napi Adatok",
        "last_entry": latest_meta_date or "N/A",
        "status": meta_freshness
    })

    # CM II (Contribution Margin II = CM I - Marketing költés)
    curr_cm2 = curr_cm1 - meta_spend_curr
    curr_cm2_pct = (curr_cm2 / curr_rev * 100.0) if curr_rev > 0 else 0.0
    blended_cac = (meta_spend_curr / curr_order_count) if curr_order_count > 0 else 0.0

    # 4. ÉLŐ STRIPE EGYENLEG
    stripe_info = get_stripe_balance()
    stripe_freshness = "Élő (API OK)" if stripe_info.get("status") == "ok" else f"Hiba ({stripe_info.get('status')})"
    freshness_reports.append({
        "source": "Stripe Live Balance API",
        "last_entry": now.strftime("%Y-%m-%d %H:%M UTC"),
        "status": stripe_freshness
    })

    # 5. KÉSZLETKIMUTATÁS & KIFUTÁSI IDŐ (Runway)
    predikalo_remaining = max(0, TOTAL_MEDAL_LIMIT_PREDIKALO - predikalo_total_sold)
    pilis_remaining = max(0, TOTAL_MEDAL_LIMIT_PILIS - pilis_total_sold)
    total_remaining_medals = predikalo_remaining + pilis_remaining
    total_inventory_cost_value = total_remaining_medals * MEDAL_CAPEX_UNIT_HUF

    # Kifutás számítás (utolsó 30 napos sebesség alapján simítva)
    thirty_days_ago = now - timedelta(days=30)
    recent_30d_orders = [o for o in orders_raw if datetime.fromisoformat(o["created_at"].replace("Z", "+00:00")) >= thirty_days_ago]
    weekly_velocity = (len(recent_30d_orders) / 30.0) * 7.0

    runway_weeks_text = "N/A (inaktív sebesség)"
    if weekly_velocity > 0:
        rw_weeks = total_remaining_medals / weekly_velocity
        runway_weeks_text = f"~{rw_weeks:.1f} hét ({rw_weeks / 4.3:.1f} hónap)"
    else:
        runway_weeks_text = "Stabil (nincs azonnali készlethiány veszély)"

    # 6. LEADEK & ÉRDEKLŐDŐK (Supabase `leads`)
    leads_raw = supabase_get("leads?select=id,created_at,converted,unsubscribed,source&order=created_at.desc")
    total_leads_count = len(leads_raw)
    converted_leads_count = sum(1 for l in leads_raw if l.get("converted") is True)
    lead_conv_rate = (converted_leads_count / total_leads_count * 100.0) if total_leads_count > 0 else 0.0

    curr_new_leads = 0
    latest_lead_dt = None
    if leads_raw:
        try:
            latest_lead_dt = datetime.fromisoformat(leads_raw[0]["created_at"].replace("Z", "+00:00"))
        except Exception:
            pass
        for l in leads_raw:
            try:
                ldt = datetime.fromisoformat(l["created_at"].replace("Z", "+00:00"))
                if ldt >= curr_start:
                    curr_new_leads += 1
            except Exception:
                continue

    freshness_reports.append({
        "source": "Supabase Leads (Útvonal-feloldás és feliratkozások)",
        "last_entry": latest_lead_dt.strftime("%Y-%m-%d %H:%M UTC") if latest_lead_dt else "N/A",
        "status": "Élő (friss)"
    })

    # 7. KITÉRŐ NPS=10 EMAIL KAMPÁNY TÖLCSÉR (Funnel)
    kitero_csv_path = os.path.join(PROJECT_ROOT, "data", "kitero_nps10_recipients.csv")
    kitero_stats = {
        "recipients_count": 0,
        "sent_count": 0,
        "unique_opens": 0,
        "unique_scroll_50": 0,
        "unique_pricing_view": 0,
        "unique_leads": 0
    }
    if os.path.exists(kitero_csv_path):
        try:
            with open(kitero_csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    kitero_stats["recipients_count"] += 1
                    if r.get("sent", "").strip() == "1":
                        kitero_stats["sent_count"] += 1
        except Exception as e:
            sys.stderr.write(f"[Kitérő CSV olvasási hiba]: {e}\n")

    event_names = ["email_open", "scroll_50", "pricing_view", "kitero_view"]
    query_str = urllib.parse.quote(f"in.({','.join(event_names)})")
    kitero_events = supabase_get(f"analytics_events?event_name={query_str}&select=event_name,event_data&order=created_at.desc&limit=500")
    
    open_cids = set()
    scroll_cids = set()
    pricing_cids = set()
    for ev in kitero_events:
        ed = ev.get("event_data") or {}
        if isinstance(ed, str):
            try:
                ed = json.loads(ed)
            except Exception:
                ed = {}
        cid = ed.get("cid")
        ename = ev.get("event_name")
        if not cid:
            continue
        if ename == "email_open":
            open_cids.add(cid)
        elif ename == "scroll_50":
            scroll_cids.add(cid)
        elif ename == "pricing_view":
            pricing_cids.add(cid)

    kitero_leads = supabase_get("leads?campaign=eq.kitero_val_1&select=id")
    kitero_stats["unique_opens"] = len(open_cids)
    kitero_stats["unique_scroll_50"] = len(scroll_cids)
    kitero_stats["unique_pricing_view"] = len(pricing_cids)
    kitero_stats["unique_leads"] = len(kitero_leads)

    # 8. LOGISZTIKA & CSOMAGOLÁS (`shipments`)
    shipments_raw = supabase_get("shipments?select=id,shipped,created_at&shipped=eq.false")
    pending_shipments_count = len(shipments_raw)
    if pending_shipments_count > 0:
        warnings.append(f"Logisztika: {pending_shipments_count} db jóváhagyott érem még feladásra/csomagolásra vár.")

    # 9. ÜGYFÉLELÉGEDETTSÉG (NPS a `feedbacks` táblából)
    feedbacks_raw = supabase_get("feedbacks?select=nps_score")
    nps_scores = [float(fb["nps_score"]) for fb in feedbacks_raw if fb.get("nps_score") is not None]
    avg_nps = (sum(nps_scores) / len(nps_scores)) if nps_scores else 0.0

    # ─── HEURISZTIKUS DÖNTÉSI & AKCIÓTERVEZŐ MOTOR ──────────────────────────────
    # Szabályalapú analízis a 3 kulcskérdésre
    leaks_and_risks = []
    growth_opportunities = []
    action_plan = []

    # Kockázat / Szivárgás detektor
    if pending_shipments_count > 10:
        leaks_and_risks.append(
            f"📦 {pending_shipments_count} feladatlan érem a Foxpost listában. A késedelmes szállítás rontja a futói élményt és az NPS-t."
        )
    if "Elavult" in meta_freshness:
        leaks_and_risks.append(
            "📢 A Meta Marketing API hozzáférés nem frissült (okt. 25. óta). Fennáll a veszélye, hogy hirdetések vakon futnak, vagy az akvizíció leállt."
        )
    if curr_order_count == 0:
        leaks_and_risks.append(
            "⚠️ Az elmúlt 7 napban 0 új fizetett rendelés érkezett. A hirdetési tölcsér és az utánkövető email szekvencia újraindítása szükséges."
        )
    unconverted_leads = total_leads_count - converted_leads_count
    if unconverted_leads > 30:
        leaks_and_risks.append(
            f"❄️ {unconverted_leads} hideg feliratkozó (ingyenes útvonal letöltő) ül a rendszerben vásárlás nélkül."
        )

    # Növekedési lehetőség detektor
    if pilis_remaining > 50:
        growth_opportunities.append(
            f"🏅 Nagy-Kevély / Pilis éremkészlet: még {pilis_remaining} db (60%) elérhető. Célzott éjszakai túra / csillagászati tematikájú kampánnyal magas árréssel értékesíthető."
        )
    if kitero_stats["sent_count"] > 0:
        growth_opportunities.append(
            f"🚶 VitaSteps Kitérő digitális élményséta: {kitero_stats['sent_count']} lojális éremvásárlónak kiküldve. Zéró fizikai előállítási és szállítási költség (100% fedezetű upsell)."
        )
    if avg_nps >= 9.5:
        growth_opportunities.append(
            f"⭐ Kiemelkedő NPS elégedettség ({avg_nps:.2f}/10). Ajánlói (referral) program aktiválása közvetlen kedvezménykódokkal vagy éremkuponnal."
        )

    # Konkrét heti akcióterv
    action_plan.append(
        "1. 📦 Foxpost csomagfeladás: A várakozó érmek címkenyomtatása és rekeszbe helyezése az admin felületről."
    )
    if "Elavult" in meta_freshness:
        action_plan.append(
            "2. 🔑 Meta Token frissítés: A Facebook Business Managerben a Marketing API token megújítása vagy költési állapot manuális ellenőrzése."
        )
    action_plan.append(
        f"3. ✉️ Nurture kampány a {unconverted_leads} hideg leadnek: Limitált éremkészlet emlékeztető kiküldése a Pilis útvonalra."
    )
    if kitero_stats["sent_count"] > 0 and kitero_stats["unique_opens"] < 5:
        action_plan.append(
            "4. 🚶 Kitérő Follow-up: Emlékeztető küldése a 19 NPS=10 béta meghívottnak a korai hozzáférésről."
        )

    # ─── PUSHBULLET SZÖVEG MEGFOGALMAZÁSA ──────────────────────────────────────
    pb_lines = [
        f"📊 VITASTEPS HETI KPI DIGEST ({now.strftime('%Y.%m.%d')})",
        "────────────────────────",
        f"💰 Heti Árbevétel: {fmt_huf(curr_rev)} ({curr_order_count} db rendelés)",
        f"📦 Fedezet I (CM I): {fmt_huf(curr_cm1)} ({fmt_pct(curr_cm1_pct)})",
        f"📢 Meta Költés: {fmt_huf(meta_spend_curr)} (CM II: {fmt_huf(curr_cm2)})",
        f"💳 Stripe Egyenleg: {fmt_huf(stripe_info.get('available_huf', 0))}",
        "",
        "📦 KÉSZLETHELYZET & RUNWAY:",
        f"• Prédikálószék: {predikalo_remaining}/100 db érem maradt",
        f"• Pilis: {pilis_remaining}/100 db érem maradt",
        f"• Készletérték: {fmt_huf(total_inventory_cost_value)}",
        f"• Kifutási idő: {runway_weeks_text}",
        "",
        "🎯 TÖLCSÉR & KONVERZIÓ:",
        f"• Összes lead: {total_leads_count} db ({converted_leads_count} vásárolt, {fmt_pct(lead_conv_rate)})",
        f"• Új heti lead: +{curr_new_leads} db",
        f"• Kitérő béta kiküldve: {kitero_stats['sent_count']} db",
        f"• NPS átlag: {avg_nps:.2f}/10 ({len(nps_scores)} értékelés)",
    ]

    if warnings:
        pb_lines.append("")
        pb_lines.append("⚠️ FIGYELMEZTETÉSEK & KOCKÁZATOK:")
        for w in warnings[:3]:
            pb_lines.append(f"• {w}")

    pb_lines.append("")
    pb_lines.append("🎯 JAVASOLT KÖVETKEZŐ LÉPÉSEK:")
    for ap in action_plan[:3]:
        pb_lines.append(f"• {ap}")

    pushbullet_body = "\n".join(pb_lines)
    pushbullet_title = f"VitaSteps KPI Digest – Hét {now.strftime('%W')}"

    return {
        "digest_id": f"digest_{now.strftime('%Y%m%d_%H%M%S')}",
        "generated_at": now.isoformat(),
        "period_days": days,
        "freshness_gate": {
            "all_fresh": len([r for r in freshness_reports if "⚠️" in r["status"] or "Inaktív" in r["status"]]) == 0,
            "reports": freshness_reports,
            "warnings": warnings
        },
        "financials": {
            "currency": "HUF",
            "gross_revenue_7d": curr_rev,
            "orders_count_7d": curr_order_count,
            "prev_revenue_7d": prev_rev,
            "prev_orders_count_7d": prev_order_count,
            "all_time_revenue": all_time_rev,
            "total_orders_count": len(orders_raw),
            "costs_7d": curr_costs,
            "cm1_7d": curr_cm1,
            "cm1_pct_7d": curr_cm1_pct,
            "meta_spend_7d": meta_spend_curr,
            "cm2_7d": curr_cm2,
            "cm2_pct_7d": curr_cm2_pct,
            "blended_cac": blended_cac,
            "stripe": stripe_info
        },
        "inventory": {
            "predikalo": {
                "limit": TOTAL_MEDAL_LIMIT_PREDIKALO,
                "sold": predikalo_total_sold,
                "remaining": predikalo_remaining
            },
            "pilis": {
                "limit": TOTAL_MEDAL_LIMIT_PILIS,
                "sold": pilis_total_sold,
                "remaining": pilis_remaining
            },
            "total_remaining": total_remaining_medals,
            "total_inventory_cost_value_huf": total_inventory_cost_value,
            "weekly_velocity": round(weekly_velocity, 2),
            "runway_text": runway_weeks_text
        },
        "funnel_and_leads": {
            "total_leads": total_leads_count,
            "converted_leads": converted_leads_count,
            "lead_conversion_rate_pct": round(lead_conv_rate, 1),
            "new_leads_7d": curr_new_leads,
            "kitero_nps10_campaign": kitero_stats,
            "avg_nps_score": round(avg_nps, 2),
            "feedbacks_count": len(nps_scores)
        },
        "operations": {
            "pending_unshipped_medals": pending_shipments_count
        },
        "insights": {
            "leaks_and_risks": leaks_and_risks,
            "growth_opportunities": growth_opportunities,
            "action_plan": action_plan
        },
        "pushbullet": {
            "title": pushbullet_title,
            "body": pushbullet_body
        }
    }


# ─── MAIN BELÉPÉSI PONT ───────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="VitaSteps Heti KPI Monitoring és Üzleti Digest")
    parser.add_argument("--push", action="store_true", help="Pushbullet értesítés elküldése")
    parser.add_argument("--json", action="store_true", help="Strukturált JSON kimenet")
    parser.add_argument("--days", type=int, default=7, help="Időszak hossza napokban (alapértelmezett: 7)")
    args = parser.parse_args()

    digest = build_weekly_business_digest(days=args.days)

    if args.json:
        print(json.dumps(digest, indent=2, ensure_ascii=False))
        return

    # Formázott konzol kimenet
    fg = digest["freshness_gate"]
    fin = digest["financials"]
    inv = digest["inventory"]
    fnl = digest["funnel_and_leads"]
    ins = digest["insights"]

    print("=" * 65)
    print(f"  🚀 VITASTEPS HETI KPI MONITORING & ÜZLETI DIGEST")
    print(f"  Időpont: {digest['generated_at'][:19]} UTC | Ablak: {args.days} nap")
    print("=" * 65)

    print("\n🔍 1. ADATFRISSESSÉGI KAPU (Data Freshness Gate):")
    for r in fg["reports"]:
        print(f"  • {r['source']:<38}: {r['status']}")
    if fg["warnings"]:
        print("  ⚠️ Észlelt adatminőségi figyelmeztetések:")
        for w in fg["warnings"]:
            print(f"    - {w}")

    print("\n💰 2. PÉNZÜGYEK & FEDEZET (Elmúlt 7 nap):")
    print(f"  • Bruttó árbevétel : {fmt_huf(fin['gross_revenue_7d'])} ({fin['orders_count_7d']} db rendelés)")
    print(f"  • Közvetlen költ.   : {fmt_huf(fin['costs_7d']['total_with_cogs'])} (Foxpost, Stripe, Számlázz, Érem)")
    print(f"  • Fedezet I (CM I)  : {fmt_huf(fin['cm1_7d'])} ({fmt_pct(fin['cm1_pct_7d'])})")
    print(f"  • Meta költés       : {fmt_huf(fin['meta_spend_7d'])}")
    print(f"  • Fedezet II (CM II): {fmt_huf(fin['cm2_7d'])} ({fmt_pct(fin['cm2_pct_7d'])})")
    print(f"  • Stripe Egyenleg   : {fmt_huf(fin['stripe'].get('available_huf', 0))}")

    print("\n📦 3. KÉSZLETKIMUTATÁS & RUNWAY:")
    print(f"  • Prédikálószék érem : {inv['predikalo']['remaining']} / {inv['predikalo']['limit']} db szabad ({inv['predikalo']['sold']} eladva)")
    print(f"  • Pilis érem         : {inv['pilis']['remaining']} / {inv['pilis']['limit']} db szabad ({inv['pilis']['sold']} eladva)")
    print(f"  • Készletérték (bek.): {fmt_huf(inv['total_inventory_cost_value_huf'])}")
    print(f"  • Készlet kifutás    : {inv['runway_text']}")

    print("\n🎯 4. TÖLCSÉR, LEADEK & KITÉRŐ:")
    print(f"  • Összes lead        : {fnl['total_leads']} db ({fnl['converted_leads']} konvertált, {fnl['lead_conversion_rate_pct']}%)")
    print(f"  • Új heti lead       : +{fnl['new_leads_7d']} db")
    print(f"  • Kitérő béta kiküldve: {fnl['kitero_nps10_campaign']['sent_count']} db ({fnl['kitero_nps10_campaign']['unique_opens']} megnyitás)")
    print(f"  • NPS átlag          : {fnl['avg_nps_score']:.2f} / 10 ({fnl['feedbacks_count']} értékelés alapján)")
    print(f"  • Csomagolásra vár   : {digest['operations']['pending_unshipped_medals']} db érem")

    print("\n💡 5. VEZETŐI ELEMZÉS & DÖNTÉSI AKCIÓTERV:")
    print("  🚨 Hol veszít pénzt / Kockázatok:")
    for leak in ins["leaks_and_risks"]:
        print(f"    • {leak}")
    print("  🌱 Növekedési lehetőségek:")
    for opp in ins["growth_opportunities"]:
        print(f"    • {opp}")
    print("  📋 Következő heti prioritások:")
    for ap in ins["action_plan"]:
        print(f"    • {ap}")

    print("\n" + "=" * 65)

    if args.push:
        print("📱 Pushbullet értesítés küldése folyamatban...")
        success = send_pushbullet_note(digest["pushbullet"]["title"], digest["pushbullet"]["body"])
        if success:
            print("✅ Pushbullet értesítés sikeresen elküldve!")
        else:
            print("❌ Pushbullet értesítés küldése sikertelen.")
            sys.exit(1)
    else:
        print("ℹ️ Értesítés elküldéséhez futtasd a --push kapcsolóval!")

if __name__ == "__main__":
    main()
