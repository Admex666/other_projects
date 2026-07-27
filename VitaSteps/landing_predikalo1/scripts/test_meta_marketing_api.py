import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from dotenv import load_dotenv

# Windows console UTF-8 support
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ===== CONFIGURATION =====
# Read keys from .env (supports multiple common variable names)
ACCESS_TOKEN  = os.getenv("META_ACCESS_TOKEN") or os.getenv("FACEBOOK_ACCESS_TOKEN") or os.getenv("META_USER_TOKEN")
AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID") or os.getenv("FACEBOOK_AD_ACCOUNT_ID")

GRAPH_API_VERSION = "v20.0"

def get_formatted_account_id(acc_id: str) -> str:
    """Ensures account ID has 'act_' prefix required by Meta Graph API."""
    acc_id = acc_id.strip()
    if not acc_id.startswith("act_"):
        return f"act_{acc_id}"
    return acc_id


def graph_api_request(endpoint: str, params: dict = None) -> dict:
    """Makes a GET request to Meta Graph API."""
    if params is None:
        params = {}
    
    params['access_token'] = ACCESS_TOKEN
    query_string = urllib.parse.urlencode(params)
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{endpoint}?{query_string}"

    req = urllib.request.Request(url, headers={"User-Agent": "VitaSteps-MarketingAPI-Test/1.0"})
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            err_json = json.loads(error_body)
            print(f"\n❌ Meta Graph API HTTP {e.code} Error:\n{json.dumps(err_json, indent=2, ensure_ascii=False)}")
        except Exception:
            print(f"\n❌ HTTP {e.code} Error: {error_body}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Network / Request Error: {e}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("🚀 Meta Marketing API – Test Call Script")
    print("=" * 60)

    if not ACCESS_TOKEN:
        print("❌ HIBA: Hányzik a META_ACCESS_TOKEN a .env fájlból!")
        print("   Kérlek add hozzá a .env-hez: META_ACCESS_TOKEN=EAAB...")
        sys.exit(1)

    if not AD_ACCOUNT_ID:
        print("❌ HIBA: Hiányzik a META_AD_ACCOUNT_ID a .env fájlból!")
        print("   Kérlek add hozzá a .env-hez: META_AD_ACCOUNT_ID=act_123456789 vagy 123456789")
        sys.exit(1)

    account_id = get_formatted_account_id(AD_ACCOUNT_ID)

    #print(f"\n🔑 Token felismerve: {ACCESS_TOKEN[:10]}...{ACCESS_TOKEN[-5:]}")
    #print(f"📊 Ad Account ID: {account_id}")

    # 1. Fetch Ad Account Details
    print(f"\n1️⃣ Hirdetési fiók adatainak lekérése ({account_id})...")
    acc_info = graph_api_request(
        endpoint=account_id,
        params={
            "fields": "id,name,account_status,currency,amount_spent,business{id,name}"
        }
    )

    status_map = {
        1: "ACTIVE (Aktív ✅)",
        2: "DISABLED (Felfüggesztve ❌)",
        3: "UNSETTLED (Tartozás miatt felfüggesztve ⚠️)",
        7: "PENDING_RISK_REVIEW (Kockázati felülvizsgálat alatt ⚠️)",
        9: "IN_GRACE_PERIOD (Türelmi időben ⚠️)",
        100: "PENDING_CLOSURE (Zárás alatt ⚠️)",
        101: "CLOSED (Zárva ❌)"
    }
    
    acc_status_code = acc_info.get("account_status")
    acc_status_str = status_map.get(acc_status_code, f"UNKNOWN ({acc_status_code})")
    spent_amount = float(acc_info.get("amount_spent", 0)) / 100

    print("\n--- Hirdetési fiók összegzés ---")
    print(f"  • Fiók neve:       {acc_info.get('name')}")
    print(f"  • Fiók ID:         {acc_info.get('id')}")
    print(f"  • Fiók státusza:   {acc_status_str}")
    print(f"  • Pénznem:         {acc_info.get('currency')}")
    print(f"  • Összes költés:    {spent_amount:,.2f} {acc_info.get('currency')}")
    if acc_info.get("business"):
        print(f"  • Business Manager: {acc_info['business'].get('name')} (ID: {acc_info['business'].get('id')})")

    # 2. Fetch Active & Paused Campaigns
    print(f"\n2️⃣ Kampányok lekérése ({account_id}/campaigns)...")
    campaigns_res = graph_api_request(
        endpoint=f"{account_id}/campaigns",
        params={
            "fields": "id,name,status,effective_status,objective,daily_budget,lifetime_budget,created_time",
            "limit": 10
        }
    )

    campaigns = campaigns_res.get("data", [])
    print(f"\n--- Összesen talált kampányok száma: {len(campaigns)} ---")

    if not campaigns:
        print("  ℹ️ Ebben a hirdetési fiókban még nincsenek kampányok.")
    else:
        for idx, camp in enumerate(campaigns, 1):
            daily_b = f"{float(camp.get('daily_budget', 0))/100:,.0f} {acc_info.get('currency')}/nap" if camp.get('daily_budget') else "N/A"
            print(f"\n  [{idx}] {camp.get('name')}")
            print(f"      • ID:               {camp.get('id')}")
            print(f"      • Státusz:          {camp.get('effective_status')}")
            print(f"      • Cél (Objective):  {camp.get('objective', 'N/A')}")
            print(f"      • Napi keret:       {daily_b}")

    print("\n" + "=" * 60)
    print("✅ Sikeres Meta Marketing API próbahívás!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
