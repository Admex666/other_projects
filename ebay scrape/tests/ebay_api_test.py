#%% Generating access token
import requests
import base64

# Sandbox kulcsok
client_id = 'AdamJaku-scardssa-SBX-a0e925d46-8d48b2e2'
client_secret = 'SBX-25542f2e7446-c1f4-4a2f-ac6e-e57b'

# Kódolás Basic Auth-hoz
credentials = f"{client_id}:{client_secret}"
encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

# Header
headers = {
    'Authorization': f'Basic {encoded_credentials}',
    'Content-Type': 'application/x-www-form-urlencoded'
}

# Body
data = {
    'grant_type': 'client_credentials',
    'scope': 'https://api.ebay.com/oauth/api_scope'
}

# POST kérés az eBay Identity Serverhez (Sandbox URL)
url = 'https://api.sandbox.ebay.com/identity/v1/oauth2/token'

response = requests.post(url, headers=headers, data=data)

if response.status_code == 200:
    token_info = response.json()
    access_token = token_info['access_token']
    print("Access Token:", access_token)
else:
    print("Hiba történt:", response.status_code, response.text)

#%%
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "X-EBAY-C-ENDUSER-CONTEXT": "contextualLocation=country=HU"
}

query = "sports trading cards"

url = f"https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search?q={query}&limit=5"

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    for item in data.get('itemSummaries', []):
        print(f"Cím: {item.get('title')}")
        print(f"Ár: {item.get('price', {}).get('value')} {item.get('price', {}).get('currency')}")
        print(f"Elérhető: {item.get('itemWebUrl')}")
        print("---")
else:
    print("Hiba:", response.status_code, response.text)
    
    
#%% Finding API
import requests

# eBay App ID (Sandbox vagy Production környezethez)
appid = 'AdamJaku-scardssa-SBX-a0e925d46-8d48b2e2'

# Keresési paraméterek
params = {
    'OPERATION-NAME': 'findItemsByKeywords',
    'SERVICE-VERSION': '1.0.0',
    'SECURITY-APPNAME': appid,
    'RESPONSE-DATA-FORMAT': 'JSON',
    'REST-PAYLOAD': '',
    'keywords': 'sports trading cards',
    'paginationInput.entriesPerPage': '5',
    'itemFilter(0).name': 'LocatedIn',
    'itemFilter(0).value': 'US'
}

# API végpont (Production környezet)
url = 'https://svcs.sandbox.ebay.com/services/search/FindingService/v1'

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    items = data.get('findItemsByKeywordsResponse', [])[0].get('searchResult', [])[0].get('item', [])
    for item in items:
        title = item.get('title', [])[0]
        price = item.get('sellingStatus', [])[0].get('currentPrice', [])[0].get('__value__')
        currency = item.get('sellingStatus', [])[0].get('currentPrice', [])[0].get('@currencyId')
        link = item.get('viewItemURL', [])[0]
        print(f"Cím: {title}")
        print(f"Ár: {price} {currency}")
        print(f"Link: {link}")
        print("---")
else:
    print(f"Hiba: {response.status_code}")
    print(response.text)

#%% Browse API
import requests
# Keresési kulcsszó
query = 'sports cards'

# API végpont
url = f'https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search?q={query}&limit=5'

# Fejlécek
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
    'X-EBAY-C-ENDUSER-CONTEXT': 'contextualLocation=country=US'
}

# API hívás
response = requests.get(url, headers=headers)

# Eredmények feldolgozása
if response.status_code == 200:
    data = response.json()
    for item in data.get('itemSummaries', []):
        title = item.get('title')
        price = item.get('price', {}).get('value')
        currency = item.get('price', {}).get('currency')
        item_url = item.get('itemWebUrl')
        print(f"Cím: {title}")
        print(f"Ár: {price} {currency}")
        print(f"Link: {item_url}")
        print("---")
else:
    print(f"Hiba történt: {response.status_code}")
    print(response.text)
