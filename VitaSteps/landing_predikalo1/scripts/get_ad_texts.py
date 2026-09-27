import os
import sys
import json
import urllib.request
import urllib.parse
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

token = os.getenv('META_ACCESS_TOKEN')
ad_acc = os.getenv('META_AD_ACCOUNT_ID', '').strip()
if not ad_acc.startswith('act_'):
    ad_acc = f'act_{ad_acc}'

url = f'https://graph.facebook.com/v20.0/{ad_acc}/ads'
params = {
    'access_token': token,
    'fields': 'id,name,campaign{id,name},adset{id,name},status,creative{id,name,title,body,object_story_spec,asset_feed_spec,call_to_action_type,image_url}',
    'limit': 150
}
req = urllib.request.Request(f'{url}?{urllib.parse.urlencode(params)}')
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))

ads = data.get('data', [])

for ad in ads:
    ad_name = ad.get('name', '')
    camp_name = (ad.get('campaign') or {}).get('name', '')
    cr = ad.get('creative') or {}

    oss = cr.get('object_story_spec') or {}
    ld = oss.get('link_data') or {}
    vd = oss.get('video_data') or {}

    primary_text = cr.get('body') or ld.get('message') or vd.get('message') or ''
    headline = cr.get('title') or ld.get('name') or vd.get('title') or ''
    description = ld.get('description') or vd.get('description') or ''
    cta = cr.get('call_to_action_type') or (ld.get('call_to_action') or {}).get('type') or ''
    link = ld.get('link') or ''

    # Filter for target keywords
    if any(k in ad_name.lower() for k in ['v4', 'v4a', '27kethet', '27meghossz', '27mielottkeso']):
        print('=' * 80)
        print(f'HIRDETÉS NEVE: {ad_name}')
        print(f'KAMPÁNY: {camp_name}')
        print(f'STÁTUSZ: {ad.get("status")}')
        print(f'CÍMSOR (Headline): {headline}')
        print(f'LEÍRÁS (Description): {description}')
        print(f'CTA GOMB: {cta}')
        print(f'CÉLOLDAL: {link}')
        print('ELSŐDLEGES SZÖVEG (Primary Text):')
        print(primary_text)
        print()
