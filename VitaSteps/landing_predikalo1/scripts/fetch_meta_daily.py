import os
import sys
import json
import csv
import urllib.request
import urllib.parse
import urllib.error
from datetime import date, datetime, timedelta
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

# Stripe fee model (HU EU cards estimate)
STRIPE_PCT   = 0.015   # 1.5%
STRIPE_FIXED = 50      # HUF / transaction

# Campaign Aliases for robust matching between DB campaign slugs and Meta campaign names
CAMPAIGN_ALIASES = {
    'pilis': ['pilis', 'nagykevely', 'nagy-kevely', 'nagy-kevély', 'kevely', 'kevély'],
    'predikaloszek': ['predikaloszek', 'prédikálószék', 'predikalo', 'prédikáló']
}

def is_same_campaign(db_campaign: str, meta_campaign: str) -> bool:
    if not db_campaign or not meta_campaign:
        return False
    db_c = db_campaign.lower().strip()
    meta_c = meta_campaign.lower().strip()
    if db_c == meta_c or db_c in meta_c or meta_c in db_c:
        return True
    for canonical, aliases in CAMPAIGN_ALIASES.items():
        db_has = any(a in db_c for a in aliases)
        meta_has = any(a in meta_c for a in aliases)
        if db_has and meta_has:
            return True
    return False


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
        err_str = e.read().decode()
        try:
            err = json.loads(err_str)
            msg = err.get('error', {}).get('message', err_str)
            code = err.get('error', {}).get('code', e.code)
            if code in (190, 102) or "Session has expired" in msg or "Error validating access token" in msg:
                print("\n" + "!" * 60)
                print("❌ META ACCESS TOKEN LEJÁRT VAGY ÉRVÉNYTELEN!")
                print("   Frissítsd a META_ACCESS_TOKEN-t a GitHub Secrets-ben és a .env fájlban.")
                print("!" * 60 + "\n")
            raise RuntimeError(f"Meta API {code}: {msg}")
        except Exception:
            raise RuntimeError(f"Meta API {e.code}: {err_str}")


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
    if not PUSHBULLET_TOKEN:
        print("   ⚠️ PUSHBULLET_ACCESS_TOKEN nincs beállítva, értesítés kihagyva.")
        return 0
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
            "level":          "ad",
            "fields":         "campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,spend,impressions,reach,frequency,clicks,actions,ctr,cpc,cpm",
            "time_range":     json.dumps({"since": date_str, "until": date_str}),
            "time_increment": 1,
            "limit":          100,
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
            "adset_id":      item.get("adset_id"),
            "adset_name":     item.get("adset_name"),
            "ad_id":         item.get("ad_id"),
            "ad_name":       item.get("ad_name"),
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

def fetch_orders_summary(target_date: date) -> list:
    """Returns list of paid real order dicts for target_date."""
    date_str = target_date.isoformat()
    next_day = (target_date + timedelta(days=1)).isoformat()
    path = (
        "orders"
        f"?created_at=gte.{date_str}T00:00:00Z"
        f"&created_at=lt.{next_day}T00:00:00Z"
        "&stripe_payment_status=eq.paid"
        "&is_test=eq.false"
        "&select=*"
    )
    rows = supabase_request("GET", path)
    return rows if isinstance(rows, list) else []



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
        if is_same_campaign(r.get("campaign"), campaign_key)
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
            if is_same_campaign((r.get("runs") or {}).get("campaign"), campaign_key)
        )
    except Exception:
        return 0


# ─── marketing_targets ───────────────────────────────────────────────────────

def fetch_targets() -> list:
    return supabase_request("GET", "marketing_targets?select=*")


def get_target(targets: list, campaign_name: str) -> dict:
    for t in targets:
        if is_same_campaign(t.get("campaign_name", ""), campaign_name):
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
    if is_good: return "🟢 Jó"
    if is_warn: return "🟡 Figyelem"
    return "⚪ Semleges"


# ─── Main ────────────────────────────────────────────────────────────────────

def run_for_date(target_date: date):
    print(f"\n=== VitaSteps – Napi Meta Szinkron ({target_date}) ===\n")

    account_id = fmt_account_id(AD_ACCOUNT_ID)
    print(f"1/5  Meta Insights lekérése ({account_id})...")
    raw_insights = fetch_meta_insights(account_id, target_date)

    if not raw_insights:
        print(f"   ℹ️ Nincs Meta hirdetési adat a megadott napra ({target_date}).")
        return

    rows = parse_insights(raw_insights)
    print(f"   ✅ OK: {len(rows)} kampány taláva\n")

    print("2/5  Orders lekérése Supabase-ből...")
    paid_orders = fetch_orders_summary(target_date)
    print(f"   ✅ OK: {len(paid_orders)} fizetett rendelés az adatbázisban a mai napra.\n")

    print("3/5  KPI célértékek lekérése...")
    targets = fetch_targets()
    print(f"   ✅ OK: {len(targets)} kampány cél\n")

    print("4/5  Számítás + Supabase upsert...")
    pushbullet_lines = [f"📊 VitaSteps Napi Riport – {target_date}\n"]

    # 4a. Attribute orders to Ads (by utm_content -> utm_campaign -> product highest-spend ad fallback)
    sales_allocation = {row["ad_id"]: {"purchases": 0, "revenue": 0.0} for row in rows}

    for order in paid_orders:
        amount = float(order.get("amount_total", 0))
        utm_content  = (order.get("utm_content") or "").strip().lower()
        utm_campaign = (order.get("utm_campaign") or "").strip().lower()
        order_prod   = (order.get("campaign") or "pilis").strip().lower()

        matched_ad = None

        # 1. Match by utm_content (Ad name or Ad ID)
        if utm_content:
            for r in rows:
                ad_name = (r.get("ad_name") or "").strip().lower()
                ad_id   = (r.get("ad_id") or "").strip().lower()
                if utm_content == ad_name or utm_content == ad_id or utm_content in ad_name or ad_name in utm_content:
                    matched_ad = r
                    break

        # 2. Match by utm_campaign
        if not matched_ad and utm_campaign:
            matching_campaign_ads = [
                r for r in rows
                if utm_campaign == (r.get("campaign_name") or "").strip().lower()
                or utm_campaign == (r.get("campaign_id") or "").strip().lower()
                or utm_campaign in (r.get("campaign_name") or "").strip().lower()
            ]
            if matching_campaign_ads:
                matched_ad = max(matching_campaign_ads, key=lambda r: r["spend"])

        # 3. Fallback to product highest-spend Ad
        if not matched_ad:
            matching_product_ads = [
                r for r in rows
                if is_same_campaign(order_prod, r.get("campaign_name") or "")
            ]
            if matching_product_ads:
                matched_ad = max(matching_product_ads, key=lambda r: r["spend"])

        # If an ad was matched, allocate sales
        if matched_ad:
            sales_allocation[matched_ad["ad_id"]]["purchases"] += 1
            sales_allocation[matched_ad["ad_id"]]["revenue"]   += amount

    for row in rows:
        campaign_key = row["ad_name"] or row["campaign_name"] or row["campaign_id"]
        alloc = sales_allocation.get(row["ad_id"], {"purchases": 0, "revenue": 0.0})
        row["purchases"] = alloc["purchases"]
        row["revenue"]   = alloc["revenue"]

        spend     = row["spend"]
        purchases = row["purchases"]
        revenue   = row["revenue"]

        # Medals sold (actual count from runs table)
        medals_sold   = fetch_medals_sold(target_date, row["campaign_name"])
        shipped_today = fetch_shipped_today(target_date, row["campaign_name"])

        # Cost params from marketing_targets
        target = get_target(targets, row["campaign_name"])
        medal_unit_cost    = float(target.get("medal_cost", 1630))
        shipping_unit_cost = float(target.get("shipping_cost", 1141))

        # Stripe fee
        stripe_fees = round(revenue * STRIPE_PCT + STRIPE_FIXED * purchases, 0)

        # Medal cost
        medal_costs = round(medals_sold * medal_unit_cost, 0)

        # Shipping cost
        shipping_costs = round(shipped_today * shipping_unit_cost, 0)

        # Profit & Loss
        total_costs  = spend + stripe_fees + medal_costs + shipping_costs
        gross_profit = round(revenue - total_costs, 0)
        margin_pct   = round(gross_profit / revenue * 100, 1) if revenue > 0 else 0.0

        # Cashflow
        stripe_net   = revenue - stripe_fees
        net_cashflow = round(stripe_net - spend - medal_costs - shipping_costs, 0)

        cpa  = round(spend / purchases, 0) if purchases > 0 else 0.0
        roas = round(revenue / spend, 2)   if spend > 0 else 0.0
        status = campaign_status(cpa, roas, target)

        # Supabase upsert (Try Ad level first, fallback to Campaign level if schema cache lacks ad_id)
        upsert_row_ad = {
            "date":          target_date.isoformat(),
            "campaign_id":   row["campaign_id"],
            "campaign_name": row["campaign_name"],
            "adset_id":      row["adset_id"],
            "adset_name":    row["adset_name"],
            "ad_id":         row["ad_id"],
            "ad_name":       row["ad_name"],
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
        try:
            supabase_request(
                "POST",
                "meta_daily_metrics?on_conflict=date,ad_id",
                body=upsert_row_ad,
                extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"}
            )
        except Exception:
            # Fallback to campaign level upsert if ad_id column is not in DB schema yet
            upsert_row_camp = {
                "date":          target_date.isoformat(),
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
                body=upsert_row_camp,
                extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"}
            )

        profit_sign = "+" if gross_profit >= 0 else ""
        cf_sign     = "+" if net_cashflow >= 0 else ""
        profit_icon = "PROFIT" if gross_profit >= 0 else "VESZTESÉG"
        cf_icon     = "POZITÍV" if net_cashflow >= 0 else "NEGATÍV"

        print(
            f"   ✅ {campaign_key}\n"
            f"      Költés: {fmtf(spend)} | Vásárlás: {purchases} db | Bevétel: {fmtf(revenue)}\n"
            f"      Profit: {profit_sign}{fmtf(gross_profit)} ({margin_pct}%) | Cashflow: {cf_sign}{fmtf(net_cashflow)}"
        )

        # Pushbullet text
        pushbullet_lines.append(
            f"\n{'='*40}\n"
            f"{campaign_key}  [{status}]\n"
            f"{'='*40}\n"
            f"\n[MARKETING]\n"
            f"  Spend:     {fmtf(spend)}\n"
            f"  Purchases: {purchases} db\n"
            f"  CPA:       {fmtf(cpa)}  |  ROAS: {roas:.2f}x\n"
            f"  CTR:       {row['ctr']:.2f}%  |  Reach: {row['reach']:,}\n"
            f"\n[EREDMÉNYKIMUTATÁS]\n"
            f"  (+) Bruttó bevétel:  {fmtf(revenue)}\n"
            f"  (-) Stripe díj:      {fmtf(stripe_fees)}\n"
            f"  (-) Éremköltség:     {fmtf(medal_costs)}  ({medals_sold} db x {fmtf(medal_unit_cost)})\n"
            f"  (-) Szállítás:       {fmtf(shipping_costs)}  ({shipped_today} csomag x {fmtf(shipping_unit_cost)})\n"
            f"  (-) Marketing:       {fmtf(spend)}\n"
            f"  = Nettó profit:      {profit_sign}{fmtf(gross_profit)}  ({margin_pct}%) [{profit_icon}]\n"
            f"\n[CASHFLOW]\n"
            f"  (+) Stripe nettó:    {fmtf(stripe_net)}\n"
            f"  (-) Meta:            {fmtf(spend)}\n"
            f"  (-) Éremgyártás:     {fmtf(medal_costs)}\n"
            f"  (-) Szállítás:       {fmtf(shipping_costs)}\n"
            f"  = Net Cashflow:      {cf_sign}{fmtf(net_cashflow)} [{cf_icon}]\n"
        )

        # Collect for CSV export
        row["cpa"]  = cpa
        row["roas"] = roas

    # Automatically synchronize daily rows into meta_kreativ_napi_riport.csv
    update_creative_csv(rows, target_date)

    print("\n5/5  Pushbullet értesítés küldése...")
    pushbullet_lines.append("\nvitastepsss.vercel.app/admin.html")
    pushbullet_send(f"VitaSteps {target_date}", "\n".join(pushbullet_lines))
    print("   ✅ Értesítés elküldve!\n")
    print(f"=== Kész: {target_date} ===\n")


def update_creative_csv(rows, target_date):
    csv_paths = [
        os.path.join(PROJECT_ROOT, 'meta_kreativ_napi_riport.csv'),
        os.path.join(PROJECT_ROOT, 'landing_predikalo1', 'meta_kreativ_napi_riport.csv'),
        os.path.join(os.getcwd(), 'landing_predikalo1', 'meta_kreativ_napi_riport.csv'),
        os.path.join(os.getcwd(), 'meta_kreativ_napi_riport.csv')
    ]
    target_csv = None
    for p in csv_paths:
        if os.path.exists(os.path.dirname(os.path.abspath(p))):
            target_csv = p
            break
    if not target_csv:
        target_csv = os.path.join(PROJECT_ROOT, 'meta_kreativ_napi_riport.csv')

    fieldnames = [
        'Datum', 'Kampany', 'Hirdetes_Sorozat', 'Kreativ_Nev', 'Hirdetes_ID',
        'Koltes_HUF', 'Megjelenes', 'Eleres', 'Gyakorisag', 'Osszes_Kattintas',
        'Link_Kattintas', 'CTR_Szazalek', 'CPC_HUF', 'CPM_HUF', 'Vasarlas_DB',
        'Bevetel_HUF', 'CPA_HUF', 'ROAS'
    ]

    target_d_str = target_date.isoformat()
    existing_rows = []

    if os.path.exists(target_csv):
        try:
            with open(target_csv, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                for r in reader:
                    if r.get('Datum') != target_d_str:
                        existing_rows.append(r)
        except Exception as e:
            print(f"Figyelmeztetés a CSV olvasásakor: {e}")

    for r in rows:
        existing_rows.append({
            'Datum': target_d_str,
            'Kampany': r.get('campaign_name', ''),
            'Hirdetes_Sorozat': r.get('adset_name', ''),
            'Kreativ_Nev': r.get('ad_name', ''),
            'Hirdetes_ID': r.get('ad_id', ''),
            'Koltes_HUF': int(round(float(r.get('spend', 0)))),
            'Megjelenes': int(r.get('impressions', 0)),
            'Eleres': int(r.get('reach', 0)),
            'Gyakorisag': round(float(r.get('frequency', 0)), 2),
            'Osszes_Kattintas': int(r.get('clicks', 0)),
            'Link_Kattintas': int(r.get('link_clicks', 0)),
            'CTR_Szazalek': round(float(r.get('ctr', 0)), 2),
            'CPC_HUF': int(round(float(r.get('cpc', 0)))),
            'CPM_HUF': int(round(float(r.get('cpm', 0)))),
            'Vasarlas_DB': int(r.get('purchases', 0)),
            'Bevetel_HUF': int(round(float(r.get('revenue', 0)))),
            'CPA_HUF': int(round(float(r.get('cpa', 0)))),
            'ROAS': round(float(r.get('roas', 0)), 2)
        })

    existing_rows.sort(key=lambda x: (x.get('Datum', ''), -int(x.get('Koltes_HUF', 0))), reverse=True)
    with open(target_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(existing_rows)
    print(f"   📁 Napi kreatív riport CSV automatikusan frissítve ({len(existing_rows)} sor): {target_csv}")


def main():
    target_date = date.today() - timedelta(days=1)
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith("--date="):
            target_date = datetime.strptime(arg.split("=")[1], "%Y-%m-%d").date()
        elif arg.startswith("--backfill="):
            days = int(arg.split("=")[1])
            for d in range(days, 0, -1):
                dt = date.today() - timedelta(days=d)
                run_for_date(dt)
            return

    run_for_date(target_date)


if __name__ == "__main__":
    main()
