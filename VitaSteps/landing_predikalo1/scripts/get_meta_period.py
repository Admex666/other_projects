import os, sys, json, urllib.request, urllib.parse
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('landing_predikalo1/.env')
load_dotenv('.env')

ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
AD_ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID', '').strip()
GRAPH_API_VERSION = 'v20.0'

def fmt_account_id(acc_id: str) -> str:
    return acc_id if acc_id.startswith('act_') else f'act_{acc_id}'

def graph_get(endpoint: str, params: dict) -> dict:
    params['access_token'] = ACCESS_TOKEN
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'VitaSteps/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

account_id = fmt_account_id(AD_ACCOUNT_ID)

# 1. Lekérés összesítve az időszakra (2026-09-18 - 2026-09-21)
params = {
    'level': 'ad',
    'fields': 'campaign_name,adset_name,ad_id,ad_name,spend,impressions,reach,frequency,clicks,actions,ctr,cpc,cpm',
    'time_range': json.dumps({'since': '2026-09-18', 'until': '2026-09-21'}),
    'limit': 100
}

res = graph_get(f"{account_id}/insights", params)
data = res.get('data', [])

print(f"==================================================")
print(f"📊 META ADS STATISZTIKA: 2026.09.18 – 2026.09.21")
print(f"==================================================")
print(f"Összes hirdetés lekérve: {len(data)}\n")

active_ads = []
for item in data:
    spend = float(item.get('spend', 0))
    if spend > 0:
        actions = {a["action_type"]: float(a["value"]) for a in item.get("actions", [])}
        active_ads.append({
            'ad_name': item.get('ad_name'),
            'campaign_name': item.get('campaign_name'),
            'adset_name': item.get('adset_name'),
            'ad_id': item.get('ad_id'),
            'spend': spend,
            'impressions': int(item.get('impressions', 0)),
            'reach': int(item.get('reach', 0)),
            'frequency': float(item.get('frequency', 0)),
            'clicks': int(item.get('clicks', 0)),
            'link_clicks': int(actions.get('link_click', 0)),
            'ctr': float(item.get('ctr', 0)),
            'cpc': float(item.get('cpc', 0)),
            'cpm': float(item.get('cpm', 0))
        })

# Sort by spend descending
active_ads.sort(key=lambda x: x['spend'], reverse=True)

total_spend = sum(a['spend'] for a in active_ads)
total_impressions = sum(a['impressions'] for a in active_ads)
total_reach = sum(a['reach'] for a in active_ads)
total_link_clicks = sum(a['link_clicks'] for a in active_ads)

for i, a in enumerate(active_ads, 1):
    gross_spend = a['spend'] * 1.27
    print(f"{i}. 🎯 {a['ad_name']}")
    print(f"   Kampány: {a['campaign_name']}")
    print(f"   Költés: {a['spend']:,.0f} Ft (nettó) | {gross_spend:,.0f} Ft (+27% ÁFA)".replace(',', '.'))
    print(f"   Megjelenés (Impressions): {a['impressions']:,}".replace(',', '.'))
    print(f"   Elérés (Reach): {a['reach']:,}".replace(',', '.'))
    print(f"   Gyakoriság: {a['frequency']:.2f} | Kattintások (link): {a['link_clicks']} db | CTR: {a['ctr']:.2f}%\n")

print(f"==================================================")
print(f"💰 IDŐSZAKI ÖSSZESÍTŐ (2026.09.18 – 2026.09.21):")
print(f"   • Összes nettó költés: {total_spend:,.0f} Ft".replace(',', '.'))
print(f"   • Összes bruttó költés (+27% ÁFA): {total_spend*1.27:,.0f} Ft".replace(',', '.'))
print(f"   • Összes megjelenés: {total_impressions:,}".replace(',', '.'))
print(f"   • Összesített egyedi elérés: {total_reach:,} (ad-level összeg)".replace(',', '.'))
print(f"   • Összes link kattintás: {total_link_clicks:,} db".replace(',', '.'))
print(f"==================================================")
