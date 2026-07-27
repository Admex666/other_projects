import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import date, timedelta
from dotenv import load_dotenv

# Windows console UTF-8 support
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ===== CONFIG =====
ACCESS_TOKEN      = os.getenv("META_ACCESS_TOKEN")
AD_ACCOUNT_ID     = os.getenv("META_AD_ACCOUNT_ID", "").strip()
SUPABASE_URL      = os.getenv("SUPABASE_URL")
SUPABASE_KEY      = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
PUSHBULLET_TOKEN  = os.getenv("PUSHBULLET_ACCESS_TOKEN")
GRAPH_API_VERSION = "v20.0"

# Which date to pull (default: yesterday)
TARGET_DATE = date.today() - timedelta(days=1)

# Stripe fee model (HU EU cards estimate)
STRIPE_PCT   = 0.015   # 1.5%
STRIPE_FIXED = 50      # HUF / transaction


# ─── Helpers ────────────────────────────────────────────────────────────────

def fmt_account_id(acc_id: str) -> str:
    return acc_id if acc_id.startswith("act_") else f"act_{acc_id}"


def graph_get(endpoint: str, params: dict) -> dict:
    params["access_token"] = ACCESS_TOKEN
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "VitaSteps/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read().decode())
        raise RuntimeError(f"Meta API {e.code}: {err.get('error', {}).get('message', str(err))}")


def supabase_request(method: str, path: str, body: dict = None, extra_headers: dict = None):
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    data = json.dumps(body).encode() if body else None
    headers = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal",
    }
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body_str = r.read().decode()
            return json.loads(body_str) if body_str else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        raise RuntimeError(f"Supabase {method} {path} -> {e.code}: {err_body}")



def pushbullet_send(title: str, body: str):
    payload = json.dumps({"type": "note", "title": title, "body": body}).encode()
    req = urllib.request.Request(
        "https://api.pushbullet.com/v2/pushes",
        data=payload,
        headers={"Access-Token": PUSHBULLET_TOKEN, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status


def fmtf(n: float) -> str:
    return f"{n:,.0f} Ft".replace(",", ".")


# ─── Meta Insights ───────────────────────────────────────────────────────────

def fetch_meta_insights(account_id: str, target_date: date) -> list:
    date_str = target_date.isoformat()
    res = graph_get(
        endpoint=f"{account_id}/insights",
        params={
            "level":          "campaign",
            "fields":         "campaign_id,campaign_name,spend,impressions,reach,frequency,clicks,actions,ctr,cpc,cpm",
            "time_range":     json.dumps({"since": date_str, "until": date_str}),
            "time_increment": 1,
            "limit":          50,
        }
    )
    return res.get("data", [])


def parse_insights(raw: list) -> list:
    rows = []
    for item in raw:
        actions = {a["action_type"]: float(a["value"]) for a in item.get("actions", [])}
        rows.append({
            "campaign_id":   item.get("campaign_id"),
            "campaign_name": item.get("campaign_name"),
            "spend":         float(item.get("spend", 0)),
            "impressions":   int(item.get("impressions", 0)),
            "reach":         int(item.get("reach", 0)),
            "frequency":     float(item.get("frequency", 0)),
            "clicks":        int(item.get("clicks", 0)),
            "link_clicks":   int(actions.get("link_click", 0)),
            "ctr":           float(item.get("ctr", 0)),
            "cpc":           float(item.get("cpc", 0)),
            "cpm":           float(item.get("cpm", 0)),
            "purchases":     0,
            "revenue":       0.0,
        })
    return rows


# ─── Supabase: Orders ────────────────────────────────────────────────────────

def fetch_orders_summary(target_date: date) -> dict:
    """Returns {campaign_slug: {purchases, revenue}} for paid real orders on target_date."""
    date_str = target_date.isoformat()
    next_day = (target_date + timedelta(days=1)).isoformat()
    path = (
        "orders"
        f"?created_at=gte.{date_str}T00:00:00Z"
        f"&created_at=lt.{next_day}T00:00:00Z"
        "&stripe_payment_status=eq.paid"
        "&is_test=eq.false"
        "&select=amount_total,campaign"
    )
    rows = supabase_request("GET", path)
    if not isinstance(rows, list):
        return {}
    summary: dict = {}
    for row in rows:
        campaign = row.get("campaign") or "unknown"
        amount   = float(row.get("amount_total", 0))
        if campaign not in summary:
            summary[campaign] = {"purchases": 0, "revenue": 0.0}
        summary[campaign]["purchases"] += 1
        summary[campaign]["revenue"]   += amount
    return summary


# ─── Supabase: Medals sold (runs count) ─────────────────────────────────────

def fetch_medals_sold(target_date: date, campaign_key: str) -> int:
    """Count runs created on target_date matching the campaign (= actual medals sold)."""
    date_str = target_date.isoformat()
    next_day = (target_date + timedelta(days=1)).isoformat()
    path = (
        "runs"
        f"?created_at=gte.{date_str}T00:00:00Z"
        f"&created_at=lt.{next_day}T00:00:00Z"
        "&is_test=eq.false"
        "&select=id,campaign"
    )
    rows = supabase_request("GET", path)
    if not isinstance(rows, list):
        return 0
    return sum(
        1 for r in rows
        if (r.get("campaign") or "").lower() in campaign_key.lower()
        or campaign_key.lower() in (r.get("campaign") or "").lower()
    )


# ─── Supabase: Shipped packages today ───────────────────────────────────────

def fetch_shipped_today(target_date: date, campaign_key: str) -> int:
    """Count packages actually shipped today for a campaign."""
    date_str = target_date.isoformat()
    next_day = (target_date + timedelta(days=1)).isoformat()
    try:
        path = (
            "shipments"
            f"?shipped_at=gte.{date_str}T00:00:00Z"
            f"&shipped_at=lt.{next_day}T00:00:00Z"
            "&shipped=eq.true"
            "&select=id,runs!inner(campaign)"
        )
        rows = supabase_request("GET", path)
        if not isinstance(rows, list):
            return 0
        return sum(
            1 for r in rows
            if (r.get("runs") or {}).get("campaign", "").lower() in campaign_key.lower()
            or campaign_key.lower() in (r.get("runs") or {}).get("campaign", "").lower()
        )
    except Exception:
        # shipped_at column may not exist yet - graceful fallback
        return 0


# ─── marketing_targets ───────────────────────────────────────────────────────

def fetch_targets() -> list:
    return supabase_request("GET", "marketing_targets?select=*")


def get_target(targets: list, campaign_name: str) -> dict:
    for t in targets:
        if t.get("campaign_name", "").strip().lower() == campaign_name.strip().lower():
            return t
    return {}


def campaign_status(cpa: float, roas: float, target: dict) -> str:
    if not target:
        return "⬜"
    is_crit = (target.get("critical_cpa") and cpa >= target["critical_cpa"]) \
           or (target.get("critical_roas") and roas <= target["critical_roas"] and roas > 0)
    is_good = (target.get("target_cpa") and cpa < target["target_cpa"]) \
          and (target.get("target_roas") and roas >= target["target_roas"])
    is_warn = (target.get("warning_cpa") and cpa >= target["warning_cpa"]) \
           or (target.get("warning_roas") and roas <= target["warning_roas"] and roas > 0)
    if is_crit: return "🔴 Kritikus"
    if is_good: return "🟢 Jo"
    if is_warn: return "🟡 Figyelem"
    return "⚪ Semleges"


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print(f"\n=== VitaSteps – Napi Meta Szinkron ({TARGET_DATE}) ===\n")

    account_id = fmt_account_id(AD_ACCOUNT_ID)
    print(f"1/5  Meta Insights lekérese ({account_id})...")
    raw_insights = fetch_meta_insights(account_id, TARGET_DATE)

    if not raw_insights:
        print("   Nincs adat a tegnapi napra (kampany szunetel?).")
        pushbullet_send(f"VitaSteps – {TARGET_DATE}", "Nincs Meta adat (kampany szunetel?).")
        return

    rows = parse_insights(raw_insights)
    print(f"   OK: {len(rows)} kampany\n")

    print("2/5  Orders lekérese...")
    orders_summary = fetch_orders_summary(TARGET_DATE)
    print(f"   OK: {sum(v['purchases'] for v in orders_summary.values())} rendelés\n")

    print("3/5  KPI célértékek lekérese...")
    targets = fetch_targets()
    print(f"   OK: {len(targets)} kampany cel\n")

    print("4/5  Szamitas + Supabase upsert...")
    pushbullet_lines = [f"VitaSteps Napi Riport – {TARGET_DATE}\n"]

    for row in rows:
        campaign_key = row["campaign_name"] or row["campaign_id"]

        # Match orders by substring (Meta name ↔ Supabase campaign slug)
        order_data = {"purchases": 0, "revenue": 0.0}
        for ck, od in orders_summary.items():
            if ck.lower() in campaign_key.lower() or campaign_key.lower() in ck.lower():
                order_data = od
                break

        row["purchases"] = order_data["purchases"]
        row["revenue"]   = order_data["revenue"]

        spend     = row["spend"]
        purchases = row["purchases"]
        revenue   = row["revenue"]

        # Medals sold (actual count from runs table)
        medals_sold   = fetch_medals_sold(TARGET_DATE, campaign_key)
        shipped_today = fetch_shipped_today(TARGET_DATE, campaign_key)

        # Cost params from marketing_targets
        target = get_target(targets, campaign_key)
        medal_unit_cost    = float(target.get("medal_cost", 2200))
        shipping_unit_cost = float(target.get("shipping_cost", 1290))

        # ── Stripe díj ──
        stripe_fees = round(revenue * STRIPE_PCT + STRIPE_FIXED * purchases, 0)

        # ── Gyártási költség ──
        medal_costs = round(medals_sold * medal_unit_cost, 0)

        # ── Szállítási költség (csak a ma ténylegesen feladott csomagok) ──
        shipping_costs = round(shipped_today * shipping_unit_cost, 0)

        # ── Eredménykimutatás ──
        total_costs  = spend + stripe_fees + medal_costs + shipping_costs
        gross_profit = round(revenue - total_costs, 0)
        margin_pct   = round(gross_profit / revenue * 100, 1) if revenue > 0 else 0.0

        # ── Cashflow ──
        # Inflow:  Stripe nettó (revenue - Stripe levonás)
        # Outflow: Meta spend, éremgyártás, szállítás
        stripe_net   = revenue - stripe_fees
        net_cashflow = round(stripe_net - spend - medal_costs - shipping_costs, 0)

        cpa  = round(spend / purchases, 0) if purchases > 0 else 0.0
        roas = round(revenue / spend, 2)   if spend > 0 else 0.0
        status = campaign_status(cpa, roas, target)

        # Supabase upsert
        upsert_row = {
            "date":          TARGET_DATE.isoformat(),
            "campaign_id":   row["campaign_id"],
            "campaign_name": row["campaign_name"],
            "spend":         spend,
            "impressions":   row["impressions"],
            "reach":         row["reach"],
            "frequency":     row["frequency"],
            "clicks":        row["clicks"],
            "link_clicks":   row["link_clicks"],
            "ctr":           row["ctr"],
            "cpc":           row["cpc"],
            "cpm":           row["cpm"],
            "purchases":     purchases,
            "revenue":       revenue,
            "cpa":           cpa,
            "roas":          roas,
        }
        supabase_request(
            "POST",
            "meta_daily_metrics?on_conflict=date,campaign_id",
            body=upsert_row,
            extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"}
        )

        profit_sign = "+" if gross_profit >= 0 else ""
        cf_sign     = "+" if net_cashflow >= 0 else ""
        profit_icon = "PROFIT" if gross_profit >= 0 else "VESZTESÉG"
        cf_icon     = "POZITIV" if net_cashflow >= 0 else "NEGATIV"

        print(
            f"   OK: {campaign_key}\n"
            f"      Spend: {fmtf(spend)} | Bevetel: {fmtf(revenue)}\n"
            f"      Profit: {profit_sign}{fmtf(gross_profit)} ({margin_pct}%) | "
            f"Cashflow: {cf_sign}{fmtf(net_cashflow)}"
        )

        # ── Pushbullet szöveg ──
        pushbullet_lines.append(
            f"\n{'='*40}\n"
            f"{campaign_key}  [{status}]\n"
            f"{'='*40}\n"
            f"\n[MARKETING]\n"
            f"  Spend:     {fmtf(spend)}\n"
            f"  CPA:       {fmtf(cpa)}  |  ROAS: {roas:.2f}x\n"
            f"  CTR:       {row['ctr']:.2f}%  |  Reach: {row['reach']:,}\n"
            f"\n[EREDMÉNYKIMUTATÁS]\n"
            f"  (+) Brutto bevetel: {fmtf(revenue)}\n"
            f"  (-) Stripe dij:     {fmtf(stripe_fees)}\n"
            f"  (-) Éremköltség:    {fmtf(medal_costs)}  ({medals_sold} db x {fmtf(medal_unit_cost)})\n"
            f"  (-) Szallitas:      {fmtf(shipping_costs)}  ({shipped_today} csomag x {fmtf(shipping_unit_cost)})\n"
            f"  (-) Marketing:      {fmtf(spend)}\n"
            f"  = Netto profit:     {profit_sign}{fmtf(gross_profit)}  ({margin_pct}%) [{profit_icon}]\n"
            f"\n[CASHFLOW]\n"
            f"  (+) Stripe netto:   {fmtf(stripe_net)}\n"
            f"  (-) Meta:           {fmtf(spend)}\n"
            f"  (-) Éremgyartas:    {fmtf(medal_costs)}\n"
            f"  (-) Szallitas:      {fmtf(shipping_costs)}\n"
            f"  = Net Cashflow:     {cf_sign}{fmtf(net_cashflow)} [{cf_icon}]\n"
        )

    print("\n5/5  Pushbullet értesítés küldése...")
    pushbullet_lines.append("\nvitastepsss.vercel.app/admin.html")
    pushbullet_send(f"VitaSteps {TARGET_DATE}", "\n".join(pushbullet_lines))
    print("   OK!\n")
    print("=== Kész ===\n")


if __name__ == "__main__":
    main()
