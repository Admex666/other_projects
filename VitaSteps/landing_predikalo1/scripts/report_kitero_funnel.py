#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 VitaSteps Kitérő – NPS=10 Kampány Teljes Funnel Riportoló Script
=============================================================================
 Funkció:
  - Beolvassa a landing_predikalo1/data/kitero_nps10_recipients.csv fájlt.
  - Lekéri a Supabase analytics_events és leads táblákból az eseményeket a CID-kre.
  - Kiszámolja a teljes mérési tölcsért és konverziós arányokat:
      1. Kiküldött e-mailek (sent == 1)
      2. Megnyitások (összes darabszám ÉS egyedi személyek száma)
      3. 50% fölé görgető látogatók
      4. Értékajánlatig (pricing blokk) elérő látogatók
      5. Nevet/e-mailt korai hozzáférésre leadként megadók
  - Megjeleníti az egyedi címzetti státusztáblát:
      (Email, Név, Megnyitotta?, Görgetett 50%?, Elérte az ajánlatot?, Lead?)

 Használat:
   python landing_predikalo1/scripts/report_kitero_funnel.py
   python landing_predikalo1/scripts/report_kitero_funnel.py --all
   python landing_predikalo1/scripts/report_kitero_funnel.py --json
=============================================================================
"""

import os
import sys
import csv
import json
import urllib.request
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv

# UTF-8 kimenet biztosítása Windows terminálon
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CSV_FILE = os.path.join(PROJECT_ROOT, "data", "kitero_nps10_recipients.csv")

# .env betöltése
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(os.path.dirname(PROJECT_ROOT), ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Színek ANSI kódjai
C_RESET   = "\033[0m"
C_BOLD    = "\033[1m"
C_DIM     = "\033[2m"
C_GREEN   = "\033[92m"
C_CYAN    = "\033[96m"
C_YELLOW  = "\033[93m"
C_RED     = "\033[91m"
C_MAGENTA = "\033[95m"
C_BLUE    = "\033[94m"
C_WHITE   = "\033[97m"
BG_DARK   = "\033[48;5;236m"

def supabase_get(endpoint: str) -> list:
    """Supabase REST API lekérdezés urllib-bel (külső függőség nélkül)."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print(f"{C_RED}❌ Hiba: Hiányzó SUPABASE_URL vagy SUPABASE_SERVICE_ROLE_KEY a .env-ben!{C_RESET}")
        sys.exit(1)

    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8', errors='ignore')
        print(f"{C_YELLOW}⚠️ Supabase lekérdezési figyelmeztetés ({e.code}): {err_msg}{C_RESET}")
        return []
    except Exception as e:
        print(f"{C_YELLOW}⚠️ Hiba a Supabase kapcsolatban: {e}{C_RESET}")
        return []

def load_csv_recipients(filepath: str) -> list:
    """Beolvassa a kitero_nps10_recipients.csv fájlt."""
    if not os.path.exists(filepath):
        print(f"{C_RED}❌ Nem található a címzettfájl: {filepath}{C_RESET}")
        sys.exit(1)

    recipients = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            recipients.append({
                "email": (row.get("email") or "").strip().lower(),
                "first_name": (row.get("first_name") or "").strip(),
                "all_names": (row.get("all_names") or "").strip(),
                "cid": (row.get("cid") or "").strip(),
                "sent": str(row.get("sent", "0")).strip() == "1",
                "sent_at": (row.get("sent_at") or "").strip()
            })
    return recipients

def make_progress_bar(pct: float, width: int = 24) -> str:
    """ASCII/Unicode progress bar előállítása."""
    clamped = max(0.0, min(100.0, pct))
    filled_len = int(round(width * clamped / 100.0))
    bar = "█" * filled_len + "░" * (width - filled_len)
    return bar

def analyze_funnel(include_unsent: bool = False):
    """Lekéri az adatbázisból az eseményeket és előállítja a teljes funnel statisztikát."""
    recipients = load_csv_recipients(CSV_FILE)

    # Releváns események lekérése Supabase-ből
    event_names = [
        "email_open",
        "landing_view",
        "email_click",
        "scroll_25",
        "scroll_50",
        "scroll_75",
        "scroll_90",
        "pricing_view",
        "cta_click",
        "lead_submit"
    ]
    query_str = urllib.parse.quote(f"in.({','.join(event_names)})")
    events = supabase_get(f"analytics_events?event_name={query_str}&select=id,session_id,visitor_id,event_name,event_data,created_at&order=created_at.desc&limit=10000")

    # Kitérő leadek lekérése
    leads = supabase_get("leads?campaign=eq.kitero_val_1&select=id,email,name,campaign,source,created_at")

    # Indexelés
    cid_to_events = {}
    session_to_cid = {}
    visitor_to_cid = {}

    for evt in events:
        edata = evt.get("event_data") or {}
        cid = edata.get("cid")
        if cid:
            if cid not in cid_to_events:
                cid_to_events[cid] = []
            cid_to_events[cid].append(evt)
            if evt.get("session_id"):
                session_to_cid[evt["session_id"]] = cid
            if evt.get("visitor_id"):
                visitor_to_cid[evt["visitor_id"]] = cid

    # Második kör: kapcsoljuk azokat az eseményeket, amelyek session/visitor alapján tartoznak a CID-hez
    for evt in events:
        edata = evt.get("event_data") or {}
        if not edata.get("cid"):
            inferred = session_to_cid.get(evt.get("session_id")) or visitor_to_cid.get(evt.get("visitor_id"))
            if inferred:
                if inferred not in cid_to_events:
                    cid_to_events[inferred] = []
                cid_to_events[inferred].append(evt)

    # Lead indexelés
    leads_by_email = {}
    leads_by_source_cid = {}
    for ld in leads:
        em = (ld.get("email") or "").strip().lower()
        if em:
            leads_by_email[em] = ld
        src = ld.get("source") or ""
        if src.startswith("email_cid_"):
            scid = src.replace("email_cid_", "").strip()
            leads_by_source_cid[scid] = ld

    # Egyedi státuszok felépítése címzettenként
    analyzed_recipients = []
    for r in recipients:
        cid = r["cid"]
        email = r["email"]
        evts = cid_to_events.get(cid, [])

        # Megnyitások
        open_evts = [e for e in evts if e.get("event_name") == "email_open"]
        open_count = len(open_evts)
        opened = open_count > 0

        # Átkattintás / Landing view
        clicks = [e for e in evts if e.get("event_name") in ("email_click", "landing_view")]
        clicked = len(clicks) > 0

        # 50%+ Görgetés
        scroll_50_evts = [
            e for e in evts 
            if e.get("event_name") in ("scroll_50", "scroll_75", "scroll_90") or 
               (e.get("event_data", {}).get("scroll_depth") and int(e.get("event_data", {}).get("scroll_depth", 0)) >= 50)
        ]
        scrolled_50 = len(scroll_50_evts) > 0

        # Értékajánlat (Pricing view)
        pricing_evts = [e for e in evts if e.get("event_name") in ("pricing_view", "offer_view")]
        viewed_pricing = len(pricing_evts) > 0

        # Lead beküldés
        lead_evts = [e for e in evts if e.get("event_name") == "lead_submit"]
        db_lead = leads_by_source_cid.get(cid) or leads_by_email.get(email)
        is_lead = len(lead_evts) > 0 or db_lead is not None

        # Név kijelzéshez
        display_name = r["first_name"]
        if not display_name and r["all_names"]:
            display_name = r["all_names"].split("/")[0].strip()
        if not display_name:
            display_name = "Címzett"

        analyzed_recipients.append({
            "email": email,
            "name": display_name,
            "all_names": r["all_names"],
            "cid": cid,
            "sent": r["sent"],
            "sent_at": r["sent_at"],
            "opened": opened,
            "open_count": open_count,
            "clicked": clicked,
            "scrolled_50": scrolled_50,
            "viewed_pricing": viewedPricing if 'viewedPricing' in locals() else viewed_pricing,
            "is_lead": is_lead,
            "raw_events_count": len(evts)
        })

    # Funnel bázis meghatározása:
    # Ha van sent == 1 címzett, akkor a sent címzettek a bázis, különben a teljes lista (vagy ha include_unsent)
    sent_list = [r for r in analyzed_recipients if r["sent"]]
    if len(sent_list) > 0 and not include_unsent:
        baseline = sent_list
        is_live_mode = True
    else:
        baseline = analyzed_recipients
        is_live_mode = len(sent_list) > 0

    base_count = len(baseline)
    sent_count = len(sent_list)

    total_opens = sum(r["open_count"] for r in baseline)
    unique_openers = len([r for r in baseline if r["opened"]])
    unique_clickers = len([r for r in baseline if r["clicked"]])
    unique_scrollers = len([r for r in baseline if r["scrolled_50"]])
    unique_pricing = len([r for r in baseline if r["viewed_pricing"]])
    unique_leads = len([r for r in baseline if r["is_lead"]])

    # Arányok számítása
    open_rate = (unique_openers / base_count * 100) if base_count > 0 else 0.0
    click_rate = (unique_clickers / base_count * 100) if base_count > 0 else 0.0
    scroll_rate = (unique_scrollers / base_count * 100) if base_count > 0 else 0.0
    pricing_rate = (unique_pricing / base_count * 100) if base_count > 0 else 0.0
    lead_rate = (unique_leads / base_count * 100) if base_count > 0 else 0.0

    # Lépésről lépésre konverziók (micro conversion)
    scroll_from_open = (unique_scrollers / unique_openers * 100) if unique_openers > 0 else 0.0
    pricing_from_open = (unique_pricing / unique_openers * 100) if unique_openers > 0 else 0.0
    lead_from_pricing = (unique_leads / unique_pricing * 100) if unique_pricing > 0 else 0.0

    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_recipients_in_csv": len(recipients),
        "sent_count": sent_count,
        "evaluated_base_count": base_count,
        "is_live_mode": is_live_mode,
        "total_opens": totalOpens if 'totalOpens' in locals() else total_opens,
        "unique_openers": unique_openers,
        "open_rate_pct": round(open_rate, 1),
        "unique_clickers": unique_clickers,
        "click_rate_pct": round(click_rate, 1),
        "unique_scrollers_50": unique_scrollers,
        "scroll_rate_pct": round(scroll_rate, 1),
        "scroll_from_open_pct": round(scroll_from_open, 1),
        "unique_pricing_viewers": unique_pricing,
        "pricing_rate_pct": round(pricing_rate, 1),
        "pricing_from_open_pct": round(pricing_from_open, 1),
        "unique_leads": unique_leads,
        "lead_rate_pct": round(lead_rate, 1),
        "lead_from_pricing_pct": round(lead_from_pricing, 1)
    }

    return summary, analyzed_recipients

def print_terminal_report(summary: dict, recipients: list, include_unsent: bool = False):
    """Szépen formázott, prémium CLI riport kirajzolása a terminálba."""
    w = 78
    print()
    print(f"{C_BOLD}{C_GREEN}╔{'═' * (w - 2)}╗{C_RESET}")
    title = "🚶  VITASTEPS KITÉRŐ – NPS=10 KAMPÁNY TELJES FUNNEL RIPORT"
    print(f"{C_BOLD}{C_GREEN}║ {title.center(w - 4)} ║{C_RESET}")
    print(f"{C_BOLD}{C_GREEN}╠{'═' * (w - 2)}╣{C_RESET}")

    now_str = summary["timestamp"]
    mode_text = "ÉLŐ KAMPÁNY (sent == 1)" if summary["is_live_mode"] and not include_unsent else "ÖSSZES CÍMZETT ELEMZÉSE (Előnézet/Teszt)"
    print(f"{C_GREEN}║{C_RESET}  Időbélyeg:   {C_WHITE}{now_str}{C_RESET} {' ' * (w - 29 - len(now_str))}{C_GREEN}║{C_RESET}")
    print(f"{C_GREEN}║{C_RESET}  Mód:         {C_CYAN}{mode_text}{C_RESET} {' ' * (w - 18 - len(mode_text))}{C_GREEN}║{C_RESET}")
    print(f"{C_GREEN}║{C_RESET}  Adatforrás:  {C_WHITE}kitero_nps10_recipients.csv & Supabase analytics_events{C_RESET} {C_GREEN}║{C_RESET}")
    print(f"{C_BOLD}{C_GREEN}╚{'═' * (w - 2)}╝{C_RESET}")
    print()

    # 1. FUNNEL OVERVIEW BLOKK
    print(f"{C_BOLD}{C_WHITE}📊 TELJES FUNNEL ÁTTEKINTÉS & LÉPÉSRŐL-LÉPÉSRE KONVERZIÓK{C_RESET}")
    print(f"{C_DIM}{'─' * w}{C_RESET}")

    base = summary["evaluated_base_count"]
    sent = summary["sent_count"]

    def row(step_num: str, step_name: str, count: int, pct: float, extra: str = "", color: str = C_WHITE):
        bar = make_progress_bar(pct, width=20)
        line = f" {C_BOLD}{color}[{step_num}] {step_name:<26}{C_RESET} {C_BOLD}{count:>3} fő{C_RESET} ({pct:>5.1f}%)  {color}{bar}{C_RESET}  {C_DIM}{extra}{C_RESET}"
        print(line)

    # 1. Lépés: Kiküldött e-mailek
    sent_extra = f"(CSV-ben összesen: {summary['total_recipients_in_csv']} címzett)"
    row("1", "Kiküldött e-mailek", sent if summary["is_live_mode"] else base, 100.0, sent_extra, C_WHITE)

    # 2. Lépés: Megnyitások
    open_extra = f"(Összes megnyitás: {summary['total_opens']} db)"
    row("2", "Megnyitotta az e-mailt", summary["unique_openers"], summary["open_rate_pct"], open_extra, C_CYAN)

    # 2.5 Lépés: Átkattintás
    click_extra = f"(Megnyitók {round(summary['unique_clickers'] / summary['unique_openers'] * 100, 1) if summary['unique_openers'] > 0 else 0.0}%-a)"
    row("→", "Átkattintott / Látogató", summary["unique_clickers"], summary["click_rate_pct"], click_extra, C_BLUE)

    # 3. Lépés: Görgetés 50%+
    scroll_extra = f"(Megnyitók {summary['scroll_from_open_pct']} %-a)"
    row("3", "50% fölé görgetett", summary["unique_scrollers_50"], summary["scroll_rate_pct"], scroll_extra, C_YELLOW)

    # 4. Lépés: Értékajánlatig elérők
    pricing_extra = f"(Megnyitók {summary['pricing_from_open_pct']} %-a)"
    row("4", "Értékajánlatig (árhoz) ért", summary["unique_pricing_viewers"], summary["pricing_rate_pct"], pricing_extra, C_MAGENTA)

    # 5. Lépés: Lead submit
    lead_extra = f"(Ajánlatot látók {summary['lead_from_pricing_pct']} %-a)"
    row("5", "Leadet adott (Érdeklődik)", summary["unique_leads"], summary["lead_rate_pct"], lead_extra, C_GREEN)

    print(f"{C_DIM}{'─' * w}{C_RESET}")
    print()

    # 2. CÍMZETTENKÉNTI RÉSZLETES TÁBLÁZAT
    print(f"{C_BOLD}{C_WHITE}👥 EGYÉNI CÍMZETTI FUNNEL STÁTUSZTÁBLA ({len(recipients)} címzett){C_RESET}")
    print(f"{C_DIM}{'─' * 106}{C_RESET}")

    header = f"{C_BOLD}{'Email':<30} {'Név':<16} {'Kiküldve?':<10} {'Megnyitotta?':<14} {'Görgetett 50%?':<16} {'Ajánlatig ért?':<15} {'Lead?':<8}{C_RESET}"
    print(header)
    print(f"{C_DIM}{'─' * 106}{C_RESET}")

    for r in recipients:
        email_str = (r["email"][:28] + "..") if len(r["email"]) > 30 else r["email"]
        name_str = (r["name"][:14] + "..") if len(r["name"]) > 16 else r["name"]

        sent_str = f"{C_GREEN}✅ Igen{C_RESET}" if r["sent"] else f"{C_DIM}❌ Nem{C_RESET}"
        
        if r["opened"]:
            open_str = f"{C_CYAN}✅ Igen ({r['open_count']}){C_RESET}"
        else:
            open_str = f"{C_DIM}❌ Nem{C_RESET}"

        scroll_str = f"{C_YELLOW}✅ Igen{C_RESET}" if r["scrolled_50"] else f"{C_DIM}❌ Nem{C_RESET}"
        pricing_str = f"{C_MAGENTA}✅ Igen{C_RESET}" if r["viewed_pricing"] else f"{C_DIM}❌ Nem{C_RESET}"
        lead_str = f"{C_GREEN}{C_BOLD}🎯 LEAD!{C_RESET}" if r["is_lead"] else f"{C_DIM}❌ Nem{C_RESET}"

        print(f"{email_str:<30} {name_str:<16} {sent_str:<19} {open_str:<23} {scroll_str:<25} {pricing_str:<24} {lead_str}")

    print(f"{C_DIM}{'─' * 106}{C_RESET}")
    print()

    # 3. ÉRTÉKELÉS & AJÁNLÁS
    print(f"{C_BOLD}{C_YELLOW}💡 STRATÉGIAI FUNNEL KÖVETKEZTETÉS:{C_RESET}")
    if summary["sent_count"] == 0:
        print(f"  {C_CYAN}ℹ️  A kampány még nem került éles kiküldésre (sent == 0).{C_RESET}")
        print(f"  {C_DIM}Kiküldés élesítése: python landing_predikalo1/scripts/send_kitero_nps10_campaign.py --live{C_RESET}")
    else:
        print(f"  {C_WHITE}• Megnyitási arány (Open Rate): {C_BOLD}{summary['open_rate_pct']}%{C_RESET}")
        print(f"  {C_WHITE}• Értékajánlatig jutási arány (Pricing View Rate): {C_BOLD}{summary['pricing_rate_pct']}%{C_RESET}")
        print(f"  {C_WHITE}• Végső Lead Konverziós Arány: {C_BOLD}{summary['lead_rate_pct']}%{C_RESET}")
    print()

def main():
    args = sys.argv[1:]
    include_unsent = "--all" in args
    json_mode = "--json" in args

    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    summary, recipients = analyze_funnel(include_unsent=include_unsent)

    if json_mode:
        output = {
            "summary": summary,
            "recipients": recipients
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_terminal_report(summary, recipients, include_unsent=include_unsent)

if __name__ == "__main__":
    main()
