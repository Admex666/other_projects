import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import hashlib
from pymongo import MongoClient
from bson.objectid import ObjectId
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

def get_mongo_client():
    try:
        client = MongoClient(
            st.secrets["mongo"]["uri"],
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        client.admin.command('ping')
        return client
    except ServerSelectionTimeoutError:
        st.error("⚠️ Could not connect to MongoDB: Timeout occurred")
        st.stop()
    except ConnectionFailure as e:
        st.error(f"⚠️ MongoDB connection failed: {e}")
        st.stop()

# Initialize connection
try:
    client = get_mongo_client()
    db = client["nestcash"]
except Exception as e:
    st.error(f"⚠️ Critical error initializing database: {e}")
    st.stop()


def load_data():
    """Tranzakciók betöltése"""
    transactions = list(db["transactions"].find({}, {'_id': 0}))
    return pd.DataFrame(transactions) if transactions else pd.DataFrame()

def save_data(df):
    """Tranzakciók mentése - Period objektumok kezelésével"""
    if df.empty:
        return
    
    # Pandas Period objektumok átalakítása stringgé
    if 'ho' in df.columns:
        df['ho'] = df['ho'].astype(str)
    
    # NaN és inf értékek kezelése
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna('')
    
    # DataFrame konvertálása dictionary listává
    records = df.to_dict("records")
    
    # Összes problémás típus konvertálása
    for record in records:
        for key, value in record.items():
            # Period objektumok kezelése
            if hasattr(value, 'strftime'):
                record[key] = str(value)
            # NaN értékek kezelése
            elif pd.isna(value):
                record[key] = None
            # Numpy típusok kezelése
            elif isinstance(value, (np.integer, np.floating)):
                if pd.isna(value):
                    record[key] = None
                else:
                    record[key] = float(value) if isinstance(value, np.floating) else int(value)
    
    # Régi adatok törlése és újak beszúrása
    db["transactions"].delete_many({})
    if records:
        db["transactions"].insert_many(records)

def load_users():
    users = get_collection("users")
    if not users:
        return pd.DataFrame(columns=["user_id", "username", "password", "email", "registration_date"])
    return pd.DataFrame.from_dict(users, orient='index')

def save_users(users_df):
    users_dict = users_df.set_index(users_df['user_id'].astype(str)).to_dict(orient='index')
    update_collection("users", users_dict)

def get_collection(collection_name):
    """MongoDB kollekció lekérése dictionary-ként"""
    docs = list(db[collection_name].find({}))
    return {str(doc["_id"]): doc for doc in docs} if docs else {}

def update_collection(collection_name, data_dict):
    """MongoDB kollekció frissítése"""
    try:
        if collection_name == "accounts":
            # Az accounts speciális kezelése
            existing_accounts = db[collection_name].find_one()
            
            if existing_accounts is None:
                # Ha nincs accounts dokumentum, létrehozzuk
                db[collection_name].insert_one(data_dict)
            else:
                # Frissítjük a meglévő adatokat
                update_data = {k: v for k, v in data_dict.items() if k != "_id"}
                db[collection_name].update_one(
                    {"_id": existing_accounts["_id"]},
                    {"$set": update_data},
                    upsert=True
                )
        else:
            # Egyéb kollekciók kezelése
            for doc_id, data in data_dict.items():
                try:
                    # Csak akkor próbálunk ObjectId-t létrehozni, ha az doc_id valid formátumú
                    if len(doc_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in doc_id):
                        object_id = ObjectId(doc_id)
                    else:
                        # Ha nem valid ObjectId, akkor keressük más módon
                        existing_doc = db[collection_name].find_one({"user_id": doc_id})
                        if existing_doc:
                            object_id = existing_doc["_id"]
                        else:
                            # Ha nincs ilyen dokumentum, hozzunk létre újat
                            data["user_id"] = doc_id
                            result = db[collection_name].insert_one(data)
                            continue
                    
                    db[collection_name].update_one(
                        {"_id": object_id},
                        {"$set": data},
                        upsert=True
                    )
                except Exception as e:
                    st.error(f"Hiba a dokumentum frissítésekor: {e}")
                    continue
                    
    except Exception as e:
        st.error(f"Hiba történt a kollekció frissítésekor: {e}")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    user = db.users.find_one({"username": username})
    if user and user.get("password") == hash_password(password):
        st.session_state.user_id = user["user_id"]
        return user
    return None

def get_user_accounts(user_id):
    """Felhasználói számlák lekérése az accounts dokumentumból"""
    try:
        user_id_str = str(user_id)
        accounts_data = db["accounts"].find_one()
        
        if accounts_data and user_id_str in accounts_data:
            return accounts_data[user_id_str]
        
        # Alapértelmezett struktúra, ha nincs ilyen felhasználó
        default_accounts = {
            "likvid": {"foosszeg": 0},
            "befektetes": {"foosszeg": 0},
            "megtakaritas": {"foosszeg": 0}
        }
        
        # Hozzáadjuk az alapértelmezett struktúrát az adatbázishoz
        if accounts_data is None:
            db["accounts"].insert_one({user_id_str: default_accounts})
        else:
            db["accounts"].update_one(
                {"_id": accounts_data["_id"]},
                {"$set": {user_id_str: default_accounts}}
            )
        
        return default_accounts
        
    except Exception as e:
        st.error(f"Hiba történt a számlaadatok lekérésekor: {e}")
        return {
            "likvid": {"foosszeg": 0},
            "befektetes": {"foosszeg": 0},
            "megtakaritas": {"foosszeg": 0}
        }

def update_account_balance(user_id, foszamla, alszamla, amount):
    """Számlegyenleg frissítése"""
    try:
        user_id_str = str(user_id)
        
        accounts_data = db["accounts"].find_one()
        
        if not accounts_data:
            accounts_data = {}
        
        if user_id_str not in accounts_data:
            accounts_data[user_id_str] = {
                "likvid": {"foosszeg": 0},
                "befektetes": {"foosszeg": 0},
                "megtakaritas": {"foosszeg": 0}
            }

        db["accounts"].update_one(
            {"_id": accounts_data["_id"]} if "_id" in accounts_data else {},
            {"$inc": {f'{user_id_str}.{foszamla}.{alszamla}': amount}}
        )
        
        
        return db["accounts"].find_one()[user_id_str][foszamla][alszamla]
        
    except Exception as e:
        st.error(f"Hiba történt az egyenleg frissítésekor: {e}")
        return 0

def load_accounts():
    accounts = get_collection("accounts")
    return accounts if accounts else {}

def save_accounts(accounts_dict):
    """Speciális accounts mentési logika"""
    try:
        # Ellenőrizzük, hogy van-e adat
        if not accounts_dict:
            st.warning("Nincsenek mentendő számlaadatok")
            return False
        
        # Az accounts dokumentum teljes lekérése
        existing_accounts = db["accounts"].find_one()
        
        if existing_accounts is None:
            # Ha nincs accounts dokumentum, létrehozzuk
            db["accounts"].insert_one(accounts_dict)
        else:
            # Frissítjük a meglévő adatokat
            for user_id, user_data in accounts_dict.items():
                existing_accounts[user_id] = user_data
            
            # Mentjük vissza az adatbázisba
            db["accounts"].update_one(
                {"_id": existing_accounts["_id"]},
                {"$set": {k: v for k, v in existing_accounts.items() if k != "_id"}},
                upsert=True
            )
        
        return True
        
    except Exception as e:
        st.error(f"Hiba történt az accounts mentésekor: {e}")
        return False

def add_transaction(new_transaction):
    try:
        if "tranzakcio_id" not in new_transaction:
            new_transaction["tranzakcio_id"] = f"{new_transaction['user_id']}_{datetime.now().strftime('%Y%m%d')}_{int(time.time())}"
            
        result = db.transactions.insert_one(new_transaction)
        return result.inserted_id is not None
    except Exception as e:
        st.error(f"Error adding transaction: {e}")
        return False

def update_transaction(transaction_id, updated_data):
    try:
        result = db.transactions.update_one(
            {"tranzakcio_id": transaction_id},
            {"$set": updated_data}
        )
        return result.modified_count > 0
    except Exception as e:
        st.error(f"Error updating transaction: {e}")
        return False

def delete_transaction(transaction_id):
    try:
        result = db.transactions.delete_one({"tranzakcio_id": transaction_id})
        return result.deleted_count > 0
    except Exception as e:
        st.error(f"Error deleting transaction: {e}")
        return False

def log_transaction_change(user_id, action, transaction_id, old_values=None, new_values=None):
    log_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user_id": str(user_id),
        "action": action,
        "transaction_id": transaction_id,
        "old_values": str(old_values) if old_values else None,
        "new_values": str(new_values) if new_values else None
    }
    
    db.transaction_logs.insert_one(log_data)

def check_automatic_habits(user_id, transaction_data):
    """Automatikus szokáskövetés tranzakciók alapján"""
    try:
        # Szokások lekérése
        habits = list(db.habits.find({
            "user_id": str(user_id),
            "is_active": True
        }))
        
        today = datetime.now().date().strftime("%Y-%m-%d")
        
        for habit in habits:
            # "Nem rendeltem ételt" szokás automatikus követése
            if "ételt" in habit["title"].lower() and "nem" in habit["title"].lower():
                if transaction_data.get("kategoria") == "etterem" or transaction_data.get("platform") == "web":
                    # Étterem vagy online rendelés esetén a szokás megszakadt
                    log_habit_completion_auto(habit["habit_id"], user_id, False, 
                                            f"Automatikus: {transaction_data.get('kategoria')} tranzakció")
                
            # "Impulzusvásárlás kerülése" szokás
            if "impulzus" in habit["title"].lower():
                if transaction_data.get("tipus") == "impulzus":
                    log_habit_completion_auto(habit["habit_id"], user_id, False, 
                                            f"Automatikus: impulzus vásárlás")
                                            
            # "Bevásárlólista alapján" szokás
            if "bevásárlólista" in habit["title"].lower() or "lista" in habit["title"].lower():
                if transaction_data.get("kategoria") == "elelmiszer" and transaction_data.get("cimke") != "lista":
                    log_habit_completion_auto(habit["habit_id"], user_id, False, 
                                            f"Automatikus: lista nélküli vásárlás")
                                            
    except Exception as e:
        print(f"Hiba az automatikus szokáskövetésben: {e}")

def log_habit_completion_auto(habit_id, user_id, completed, notes=""):
    """Automatikus szokás teljesítés naplózása"""
    try:
        today = datetime.now().date().strftime("%Y-%m-%d")
        
        # Ellenőrizzük, hogy ma már volt-e bejegyzés
        existing_log = db.habit_logs.find_one({
            "user_id": str(user_id),
            "habit_id": habit_id,
            "date": today
        })
        
        if existing_log:
            # Csak akkor frissítünk, ha negatív eredményt találtunk
            if not completed and existing_log.get("completed", True):
                db.habit_logs.update_one(
                    {"_id": existing_log["_id"]},
                    {
                        "$set": {
                            "completed": completed,
                            "notes": notes,
                            "auto_detected": True
                        }
                    }
                )
                update_habit_streak_auto(habit_id, user_id)
        else:
            # Ha nincs mai bejegyzés és negatív eredmény, akkor rögzítjük
            if not completed:
                log_data = {
                    "user_id": str(user_id),
                    "habit_id": habit_id,
                    "date": today,
                    "completed": completed,
                    "value": None,
                    "notes": notes,
                    "auto_detected": True,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                db.habit_logs.insert_one(log_data)
                update_habit_streak_auto(habit_id, user_id)
                
    except Exception as e:
        print(f"Hiba az automatikus naplózásban: {e}")

def update_habit_streak_auto(habit_id, user_id):
    """Automatikus streak frissítés"""
    try:
        from datetime import datetime, timedelta
        
        # Utolsó 30 nap logjai
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        logs = list(db.habit_logs.find({
            "user_id": str(user_id),
            "habit_id": habit_id,
            "date": {"$gte": thirty_days_ago}
        }).sort("date", -1))
        
        if not logs:
            return
        
        # Jelenlegi streak számítása
        current_streak = 0
        today = datetime.now().date()
        
        for log in logs:
            log_date = datetime.strptime(log["date"], "%Y-%m-%d").date()
            days_diff = (today - log_date).days
            
            if days_diff == current_streak and log["completed"]:
                current_streak += 1
            else:
                break
        
        # Frissítés az adatbázisban
        db.habits.update_one(
            {"habit_id": habit_id, "user_id": str(user_id)},
            {
                "$set": {
                    "streak_count": current_streak,
                    "last_completed": logs[0]["date"] if logs and logs[0]["completed"] else None
                }
            }
        )
        
    except Exception as e:
        print(f"Hiba az automatikus streak frissítésben: {e}")

def get_habit_suggestions(user_id):
    """Szokás javaslatok felhasználó tranzakciói alapján"""
    try:
        # Utolsó 30 nap tranzakciói
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        user_transactions = list(db.transactions.find({
            "user_id": user_id,
            "datum": {"$gte": thirty_days_ago}
        }))
        
        suggestions = []
        
        if user_transactions:
            # Étterem/online rendelés gyakoriság
            food_orders = [t for t in user_transactions if t.get("kategoria") in ["etterem", "online rendeles"]]
            if len(food_orders) >= 5:
                suggestions.append({
                    "title": "Nem rendeltem ételt",
                    "reason": f"Utolsó 30 napban {len(food_orders)} alkalommal rendeltél ételt",
                    "category": "Pénzügyi"
                })
            
            # Impulzusvásárlás gyakoriság
            impulse_purchases = [t for t in user_transactions if t.get("tipus") == "impulzus"]
            if len(impulse_purchases) >= 3:
                suggestions.append({
                    "title": "Impulzusvásárlás kerülése",
                    "reason": f"Utolsó 30 napban {len(impulse_purchases)} impulzusvásárlás",
                    "category": "Pénzügyi"
                })
            
            # Megtakarítás hiánya
            savings = [t for t in user_transactions if t.get("kategoria") == "megtakaritas"]
            if len(savings) < 5:
                suggestions.append({
                    "title": "Napi megtakarítás",
                    "reason": "Kevés megtakarítási tranzakció az elmúlt időszakban",
                    "category": "Megtakarítás"
                })
        
        return suggestions
        
    except Exception as e:
        print(f"Hiba a javaslatok generálásában: {e}")
        return []
    
def format_accounts(user_accounts):
    """Formázza a számlákat 'főszámla/alszámla' formátumba"""
    formatted = []
    for foszamla, alszamlak in user_accounts.items():
        if alszamlak:
            for alszamla in alszamlak.keys():
                formatted.append(f"{foszamla}/{alszamla}")
        else:
            formatted.append(f"{foszamla}/")  # Ha nincs alszámla
    return formatted

def get_user_monthly_limits(user_id):
    """Felhasználó havi korlátainak lekérése"""
    limits_data = db.monthly_limits.find_one({"user_id": user_id})
    return limits_data.get("limits", {}) if limits_data else {}

def save_user_monthly_limits(user_id, limits):
    """Felhasználó havi korlátainak mentése"""
    db.monthly_limits.update_one(
        {"user_id": user_id},
        {"$set": {"limits": limits}},
        upsert=True
    )

def calculate_monthly_progress(user_id, current_month):
    """Havi haladás számítása kategóriánként"""
    from datetime import datetime
    import calendar
    
    # Aktuális hónap adatainak lekérése
    current_transactions = db.transactions.find({
        "user_id": user_id,
        "ho": current_month
    })
    
    # Kategóriánkénti összesítés
    category_totals = {}
    for transaction in current_transactions:
        category = transaction.get("kategoria", "")
        amount = transaction.get("osszeg", 0)
        
        if category not in category_totals:
            category_totals[category] = 0
        category_totals[category] += amount
    
    # Havi korlátok lekérése
    limits = get_user_monthly_limits(user_id)
    
    # Haladás számítása
    progress = {}
    current_date = datetime.now()
    days_in_month = calendar.monthrange(current_date.year, current_date.month)[1]
    current_day = current_date.day
    
    for category, limit_data in limits.items():
        limit_type = limit_data.get("type", "maximum")  # maximum vagy minimum
        limit_amount = limit_data.get("amount", 0)
        
        current_spent = abs(category_totals.get(category, 0))
        
        if limit_type == "maximum":
            # Kiadási korlát esetén
            remaining = limit_amount - current_spent
            daily_ideal = (limit_amount / days_in_month) * current_day
            daily_difference = current_spent - daily_ideal
        else:
            # Bevételi minimum esetén
            remaining = current_spent - limit_amount
            daily_ideal = (limit_amount / days_in_month) * current_day
            daily_difference = daily_ideal - current_spent
        
        progress[category] = {
            "limit_amount": limit_amount,
            "current_amount": current_spent,
            "remaining": remaining,
            "daily_ideal": daily_ideal,
            "daily_difference": daily_difference,
            "progress_percentage": (current_spent / limit_amount * 100) if limit_amount > 0 else 0,
            "limit_type": limit_type
        }
    
    return progress