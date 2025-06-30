#%% Import, paramÃ©terek
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker('hu_HU')
random.seed(42)

# Profil-definÃ­ciÃ³k (arÃ¡nyok: alap, vÃ¡gy, megtakarÃ­tÃ¡s, impulzÃ­v vÃ¡sÃ¡rlÃ¡s esÃ©ly)
PROFILES = {
    "alacsony_jov": {
        "alap": 0.80,
        "vagy": 0.10,
        "megtakaritas": 0.10,
        "impulzus_prob": 0.3,
        "weight": 0.21,
        "income": (180_000, 220_000)
    },
    "kozeposztaly": {
        "alap": 0.75,
        "vagy": 0.15,
        "megtakaritas": 0.10,
        "impulzus_prob": 0.2,
        "weight": 0.50,
        "income": (325_000, 375_000)
    },
    "magas_jov": {
        "alap": 0.65,
        "vagy": 0.20,
        "megtakaritas": 0.15,
        "impulzus_prob": 0.2,
        "weight": 0.20,
        "income": (540_000, 660_000)
    },
    "arerzekeny": {
        "alap": 0.70,
        "vagy": 0.05,
        "megtakaritas": 0.15,
        "impulzus_prob": 0.1,
        "weight": 0.09,
        "income": (225_000, 275_000)
    }
}

CATEGORIES = {
    "alap": {
        "kategorialista": ["lakber", "rezsi", "elelmiszer", "kozlekedes", "gyogyszer"],
        "helyszinek": {
            "lakber": ["-"],
            "rezsi": ["-"],
            "elelmiszer": ["Tesco", "Lidl", "Auchan", "Spar", "CBA"],
            "kozlekedes": ["MAV", "BKK", "Volan"],
            "gyogyszer": ["gyogyszertar", "DM", "Rossmann"]
        },
        "cimkek": {
            "lakber": ["havi fix", "szukseges"],
            "rezsi": ["szukseges", "havi fix"],
            "elelmiszer": ["napi rutin", "szukseges"],
            "kozlekedes": ["napi rutin", "szukseges"],
            "gyogyszer": ["egeszseg", "szukseges"]
        },
        "celok": {
            "lakber": ["lakas"],
            "rezsi": [""],
            "elelmiszer": [""],
            "kozlekedes": [""],
            "gyogyszer": ["egeszseg"]
        }
    },
    "vagy": {
        "kategorialista": ["etterem", "mozi", "ruha", "utazas", "kutyu"],
        "helyszinek": {
            "etterem": ["McDonald's", "KFC", "helyi etterem"],
            "mozi": ["Cinema City", "Art Mozi"],
            "ruha": ["H&M", "Zara", "Decathlon"],
            "utazas": ["WizzAir", "MAV", "Airbnb"],
            "kutyu": ["Media Markt", "eMAG"]
        },
        "cimkek": {
            "etterem": ["szorakozas", "extra"],
            "mozi": ["szorakozas", "luxus"],
            "ruha": ["szorakozas", "extra"],
            "utazas": ["nyaralas", "luxus"],
            "kutyu": ["extra", "szorakozas"]
        },
        "celok": {
            "etterem": [""],
            "mozi": [""],
            "ruha": [""],
            "utazas": ["nyaralas"],
            "kutyu": [""]
        }
    },
    "megtakaritas": {
        "kategorialista": ["megtakaritas"],
        "helyszinek": {
            "megtakaritas": ["Bank", "OTP", "K&H"]
        },
        "cimkek": {
            "megtakaritas": ["jovo", "havi fix"]
        },
        "celok": {
            "megtakaritas": ["veszhelyzet", "gyerek", "lakas"]
        }
    },
    "impulzus": {
        "kategorialista": ["kave", "snack", "apro vasarlas", "online rendeles"],
        "helyszinek": {
            "kave": ["Costa", "Starbucks", "helyi kavezo"],
            "snack": ["bolt", "Lidl", "Spar"],
            "apro vasarlas": ["helyi bolt", "piac"],
            "online rendeles": ["eMAG", "Aliexpress", "Amazon"]
        },
        "cimkek": {
            "kave": ["napi rutin", "szorakozas"],
            "snack": ["napi rutin", "szukseges"],
            "apro vasarlas": ["extra"],
            "online rendeles": ["extra", "luxus"]
        },
        "celok": {
            "kave": [""],
            "snack": [""],
            "apro vasarlas": [""],
            "online rendeles": [""]
        }
    }
}

# Havi gyakoriságok kategóriánként (min, max alkalom/hó)
MONTHLY_FREQUENCY = {
    'alacsony_jov': {
        'etterem': (1, 4),
        'mozi': (0, 2),
        'ruha': (0, 1),
        'utazas': (0, 1),
        'kutyu': (0, 1),
        'megtakaritas': (1, 1),  # havonta egyszer
        'kave': (3, 12),
        'snack': (2, 10),
        'apro vasarlas': (2, 8),
        'online rendeles': (1, 3),
    },
    'kozeposztaly': {
        'etterem': (2, 8),
        'mozi': (1, 4),
        'ruha': (1, 3),
        'utazas': (0, 2),
        'kutyu': (1, 3),
        'megtakaritas': (1, 1),
        'kave': (3, 16),
        'snack': (2, 10),
        'apro vasarlas': (5, 15),
        'online rendeles': (1, 5),
    },
    'magas_jov': {
        'etterem': (5, 12),
        'mozi': (2, 6),
        'ruha': (2, 5),
        'utazas': (1, 3),
        'kutyu': (2, 5),
        'megtakaritas': (1, 2),
        'kave': (5, 22),
        'snack': (3, 15),
        'apro vasarlas': (8, 20),
        'online rendeles': (2, 7),
    },
    'arerzekeny': {
        'etterem': (0, 2),
        'mozi': (0, 1),
        'ruha': (0, 1),
        'utazas': (0, 1),
        'kutyu': (0, 1),
        'megtakaritas': (1, 1),
        'kave': (2, 7),
        'snack': (1, 6),
        'apro vasarlas': (1, 5),
        'online rendeles': (0, 2),
    },
}

# Ã¶sszegek intervallumok kategÃ³riÃ¡nkÃ©nt (forint)
AMT_BOUNDS = {
    'alacsony_jov': {
        'lakber': (50000, 70000),
        'rezsi': (20000, 30000),
        'elelmiszer': (15000, 25000),
        'kozlekedes': (5000, 10000),
        'gyogyszer': (2000, 5000),
        'etterem': (2000, 3500),
        'mozi': (500, 2000),
        'ruha': (2000, 5000),
        'utazas': (0, 3000),
        'kutyu': (0, 2000),
        'megtakaritas': (0, 10000),
        'csoki': (500, 1500),
        'kave': (1000, 3000),
        'snack': (500, 1500),
        'apro vasarlas': (500, 2000),
        'online rendeles': (500, 2000),
    },
    'kozeposztaly': {
        'lakber': (70000, 100000),
        'rezsi': (30000, 45000),
        'elelmiszer': (20000, 30000),
        'kozlekedes': (10000, 15000),
        'gyogyszer': (5000, 10000),
        'etterem': (2500, 5000),
        'mozi': (2000, 5000),
        'ruha': (5000, 15000),
        'utazas': (5000, 15000),
        'kutyu': (2000, 8000),
        'megtakaritas': (10000, 40000),
        'csoki': (2000, 5000),
        'kave': (3000, 7000),
        'snack': (2000, 5000),
        'apro vasarlas': (2000, 6000),
        'online rendeles': (5000, 10000),
    },
    'magas_jov': {
        'lakber': (100000, 180000),
        'rezsi': (40000, 60000),
        'elelmiszer': (27500, 50000),
        'kozlekedes': (15000, 30000),
        'gyogyszer': (5000, 15000),
        'etterem': (3000, 8000),
        'mozi': (5000, 10000),
        'ruha': (15000, 30000),
        'utazas': (20000, 50000),
        'kutyu': (5000, 15000),
        'megtakaritas': (25000, 100000),
        'csoki': (3000, 7000),
        'kave': (5000, 15000),
        'snack': (3000, 8000),
        'apro vasarlas': (3000, 10000),
        'online rendeles': (10000, 20000),
    },
    'arerzekeny': {
        'lakber': (60000, 90000),
        'rezsi': (20000, 35000),
        'elelmiszer': (15000, 25000),
        'kozlekedes': (8000, 12000),
        'gyogyszer': (3000, 8000),
        'etterem': (1750, 3250),
        'mozi': (500, 2000),
        'ruha': (2000, 5000),
        'utazas': (0, 5000),
        'kutyu': (0, 2000),
        'megtakaritas': (5000, 15000),
        'csoki': (500, 1500),
        'kave': (1000, 3000),
        'snack': (500, 1500),
        'apro vasarlas': (500, 2000),
        'online rendeles': (1000, 4000),
    },
}

#%% Function
def generate_user_transactions(user, months=3):
    profile_name = user["profil"]
    profile = PROFILES[profile_name]
    monthly_income = user["monthly_income"]
    fixed_costs = user["fixed_costs"]
    user_id = user["user_id"]

    data = []
    likvid = 0
    megtakaritas = user["szamlak"]["megtakaritas"]
    befektetes = user["szamlak"]["befektetes"]

    for month_offset in range(months):
        start_date = datetime.today() - pd.DateOffset(months=month_offset + 1)
        payday = start_date.replace(day=1) + timedelta(days=random.randint(0, 2))
        honap = payday.strftime("%Y-%m")
        spending_limit = monthly_income * 0.95  # kÃ¶ltÃ©si plafon

        # Fizu 
        likvid += monthly_income
        data.append({
            "datum": payday.date(),
            "honap": honap,
            "het": payday.isocalendar()[1],
            "nap_sorszam": payday.weekday(),
            "tranzakcio_id": f"{user_id}_{payday.strftime('%Y%m%d')}_{random.randint(1000, 9999)}",
            "osszeg": monthly_income,
            "kategoria": "fizetes",
            "user_id": user_id,
            "profil": profile_name,
            "tipus": "bevetel",
            "leiras": "havi fizetes",
            "forras": "demo",
            "ismetlodo": True,
            "fix_koltseg": False,
            "bev_kiad_tipus": "bevetel",
            "platform": "utalas",
            "helyszin": "Banki utalas",
            "deviza": "HUF",
            "cimke": "jovedelem, fix",
            "celhoz_kotott": "",
            "likvid": round(likvid),
            "befektetes": round(befektetes),
            "megtakaritas": round(megtakaritas)
        })
        
        # Befektetési hozamok hozzáadása portfolió alapján
        for bef_tipus, alap in user.get("szamlak", {}).items():
            if alap <= 0:
                continue
            # Éves hozam 4-10%, leosztva hónapra
            hozam_szazalek = random.uniform(0.01, 0.04) / 12 if bef_tipus == "megtakaritas" else random.uniform(0.05, 0.12) / 12
            hozam = round(alap * hozam_szazalek, -1)
            
            hozam_date = fake.date_between_dates(
                date_start=start_date + pd.DateOffset(days=5),
                date_end=start_date + pd.DateOffset(days=20)
            )
            
            if bef_tipus == "megtakaritas":
                megtakaritas += hozam
            elif bef_tipus == "befektetes":
                befektetes += hozam
            data.append({
                "datum": hozam_date,
                "honap": honap,
                "het": hozam_date.isocalendar()[1],
                "nap_sorszam": hozam_date.weekday(),
                "tranzakcio_id": f"{user_id}_{hozam_date.strftime('%Y%m%d')}_{random.randint(1000, 9999)}",
                "osszeg": hozam,
                "kategoria": f"{bef_tipus}_hozam",
                "user_id": user_id,
                "profil": profile_name,
                "tipus": "befektetes_hozam",
                "leiras": f"{bef_tipus} hozam",
                "forras": "hozam generator",
                "ismetlodo": True,
                "fix_koltseg": False,
                "bev_kiad_tipus": "bevetel",
                "platform": "utalas",
                "helyszin": "Banki utalas",
                "deviza": "HUF",
                "cimke": "hozam, befektetes",
                "celhoz_kotott": bef_tipus,
                "likvid": round(likvid),
                "befektetes": round(befektetes),
                "megtakaritas": round(megtakaritas)
            })
        
        user["szamlak"][bef_tipus] += hozam
        
        month_spent = 0

        # Fix ktsg levonása
        for category, amount in fixed_costs.items():
            date = fake.date_between_dates(
                date_start=start_date,
                date_end=start_date + pd.DateOffset(days=5)
            )
            month_spent += amount
            
            likvid -= amount
            data.append({
                "datum": date,
                "honap": honap,
                "het": date.isocalendar()[1],
                "nap_sorszam": date.weekday(),
                "tranzakcio_id": f"{user_id}_{date.strftime('%Y%m%d')}_{random.randint(1000, 9999)}",
                "osszeg": -amount,
                "kategoria": category,
                "user_id": user_id,
                "profil": profile_name,
                "tipus": "alap",
                "leiras": f"{category} koltseg",
                "forras": "demo",
                "ismetlodo": True,
                "fix_koltseg": True,
                "bev_kiad_tipus": "szukseglet",
                "platform": "utalÃ¡s",
                "helyszin": "Banki utalÃ¡s",
                "deviza": "HUF",
                "cimke": "fix, rezsi",
                "celhoz_kotott": "",
                "likvid": round(likvid),
                "befektetes": round(befektetes),
                "megtakaritas": round(megtakaritas)
            })

        # Változó költségek - gyakoriság alapú
        for ttype in ["vagy", "megtakaritas", "impulzus"]:
            for category in CATEGORIES[ttype]["kategorialista"]:
                min_freq, max_freq = MONTHLY_FREQUENCY[profile_name][category]
                monthly_transactions = random.randint(min_freq, max_freq)
                
                for _ in range(monthly_transactions):
                    # Ellenőrizzük, hogy van-e még költési keret
                    if month_spent >= spending_limit:
                        break
                    
                    lo, hi = AMT_BOUNDS[profile_name][category]
                    max_osszeg = spending_limit - month_spent
                    amount = round(min(random.uniform(lo, hi), max_osszeg), -2)

                    if amount <= 0:
                        continue
                    
                    if ttype == "megtakaritas":
                        user["szamlak"]['megtakaritas'] += amount

                    date = fake.date_between_dates(
                        date_start=start_date,
                        date_end=start_date + pd.DateOffset(days=27)
                    )

                    het = date.isocalendar()[1]
                    nap_sorszam = date.weekday()
                    tranzakcio_id = f"{user_id}_{date.strftime('%Y%m%d')}_{random.randint(1000, 9999)}"
                    forras = random.choice(["demo", "manualis", "import"])
                    ismetlodo = category in ["lakber", "rezsi", "kozlekedes", "megtakaritas"]
                    fix_koltseg = category in ["lakber", "rezsi", "kozlekedes"]
                    bev_kiad_tipus = (
                        "szukseglet" if ttype == "alap"
                        else "megtakaritas" if ttype == "megtakaritas"
                        else "luxus"
                    )
                    platform = random.choices(["bolt", "web"], weights=[0.55, 0.45])[0]
                    helyszin = (
                        "Banki utalas" if platform == "utalas"
                        else random.choice(CATEGORIES[ttype]["helyszinek"].get(category, ["ismeretlen"]))
                    )
                    cimke = ", ".join(random.sample(CATEGORIES[ttype]["cimkek"].get(category, ["altalanos"]), k=1))
                    cel_valasztek = CATEGORIES[ttype]["celok"].get(category, [""])
                    celhoz_kotott = random.choice(cel_valasztek)
                    leiras = fake.sentence(nb_words=3)
                    
                    likvid -= amount
                    if ttype == "megtakaritas":
                        bef_tipus = random.choice(['megtakaritas', 'befektetes'])
                        if bef_tipus == 'megtakaritas':
                            megtakaritas += amount
                        elif bef_tipus == 'befektetes':
                            befektetes += amount
                        leiras = f'{int(amount)}Ft -> {bef_tipus}'
                        amount = 0 # nincs cash-flow hatás

                    data.append({
                        "datum": date,
                        "honap": honap,
                        "het": het,
                        "nap_sorszam": nap_sorszam,
                        "tranzakcio_id": tranzakcio_id,
                        "osszeg": -amount,
                        "kategoria": category,
                        "user_id": user_id,
                        "profil": profile_name,
                        "tipus": ttype,
                        "leiras": leiras,
                        "forras": forras,
                        "ismetlodo": ismetlodo,
                        "fix_koltseg": fix_koltseg,
                        "bev_kiad_tipus": bev_kiad_tipus,
                        "platform": platform,
                        "helyszin": helyszin,
                        "deviza": "HUF",
                        "cimke": cimke,
                        "celhoz_kotott": celhoz_kotott,
                        "likvid": round(likvid),
                        "befektetes": round(befektetes),
                        "megtakaritas": round(megtakaritas)
                    })

                    month_spent += amount
            
    df = pd.DataFrame(data)
    df['assets'] = df.likvid + df.befektetes + df.megtakaritas
    
    return df


#%% GenerÃ¡lÃ¡s
total_users = 50
# Egyedi felhasznÃ¡lÃ³k listÃ¡ja elÅre
users = []
user_counter = 1

for profile_name, profile in PROFILES.items():
    count = int(total_users * profile["weight"])
    for _ in range(count):
        users.append({
            "user_id": user_counter,
            "profil": profile_name,
            "monthly_income": random.randint(profile["income"][0], profile["income"][1]),
            "fixed_costs": {
                "lakber": random.randint(AMT_BOUNDS[profile_name]['lakber'][0],AMT_BOUNDS[profile_name]['lakber'][1]),
                "rezsi":random.randint(AMT_BOUNDS[profile_name]['rezsi'][0],AMT_BOUNDS[profile_name]['rezsi'][1]),
                "kozlekedes": random.randint(AMT_BOUNDS[profile_name]['kozlekedes'][0],AMT_BOUNDS[profile_name]['kozlekedes'][1]),
                "elelmiszer": random.randint(AMT_BOUNDS[profile_name]['elelmiszer'][0],AMT_BOUNDS[profile_name]['elelmiszer'][1]),
            },
            "variable_spending_limit_ratio": 0.8,
            "szamlak": {
                "befektetes": random.randint(0, 50000),
                "megtakaritas": random.randint(0, 200000)
            }
        })
        user_counter += 1

dfs = []
for user in users:
    df_user = generate_user_transactions(user, months=12)
    dfs.append(df_user)

df_all = pd.concat(dfs, ignore_index=True)

print(df_all.head(10))

vagyonok = {usernr:df_all[df_all.user_id == usernr]['assets'].to_list()[-1] for usernr in range(1, total_users)}
print(vagyonok.values())

#%% Save
df_all.sort_values("datum", inplace=True)
df_all.to_csv("szintetikus_tranzakciok.csv", index=False)

#%% Save accounts
import json
accounts = {}
for user_id in df_all.user_id.unique():
    user_id_str = str(user_id)
    accounts[user_id_str] = {}
    for account in ['likvid', 'befektetes', 'megtakaritas']:
        foosszeg = df_all[df_all.user_id == user_id][account].iloc[-1]
        accounts[user_id_str][account] = {'foosszeg': int(foosszeg)}
            
with open("accounts.json", "w") as f:
    json.dump(accounts, f)
    