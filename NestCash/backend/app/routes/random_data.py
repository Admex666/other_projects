# app/routes/random_data.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from beanie import PydanticObjectId

from app.models.transaction import Transaction
from app.models.transaction_schemas import TransactionRead
from app.models.user import User
from app.core.security import get_current_user
from app.routes.transactions import update_sub_account_balance

router = APIRouter(prefix="/random", tags=["random-data"])

# Kategóriák és tipikus összegek
CATEGORIES_WITH_AMOUNTS = {
    "Élelmiszer": {"min": 2000, "max": 25000, "avg": 8000},
    "Lakhatás": {"min": 50000, "max": 200000, "avg": 120000},
    "Közlekedés": {"min": 5000, "max": 50000, "avg": 20000},
    "Egészségügy": {"min": 3000, "max": 80000, "avg": 15000},
    "Szórakozás": {"min": 2000, "max": 30000, "avg": 12000},
    "Ruházat": {"min": 5000, "max": 50000, "avg": 18000},
    "Kommunikáció": {"min": 3000, "max": 15000, "avg": 8000},
    "Oktatás": {"min": 10000, "max": 100000, "avg": 35000},
    "Utazás": {"min": 15000, "max": 300000, "avg": 80000},
    "Háztartási cikkek": {"min": 3000, "max": 80000, "avg": 20000},
    "Szolgáltatások": {"min": 5000, "max": 40000, "avg": 15000},
    "Ajándék": {"min": 5000, "max": 50000, "avg": 20000},
}

# Bevételi kategóriák
INCOME_CATEGORIES = {
    "Fizetés": {"min": 200000, "max": 800000, "avg": 400000},
    "Freelance": {"min": 50000, "max": 300000, "avg": 120000},
    "Befektetés": {"min": 10000, "max": 100000, "avg": 30000},
    "Ajándék": {"min": 10000, "max": 100000, "avg": 25000},
    "Eladás": {"min": 5000, "max": 200000, "avg": 40000},
    "Egyéb bevétel": {"min": 5000, "max": 50000, "avg": 20000},
}

# Főszámlák és tipikus alszámlák
MAIN_ACCOUNTS = {
    "likvid": [
        "Készpénz", "Bankszámla", "Hitelkártya", "Revolut", 
        "OTP bankszámla", "K&H számla", "Wise kártya"
    ],
    "befektetes": [
        "Részvények", "Kötvények", "Befektetési alap", "Crypto",
        "Random Capital", "TBSZ", "Nyugdíjpénztár"
    ],
    "megtakaritas": [
        "Vészhelyzeti alap", "Nyaralás alap", "Lakásvásárlás", 
        "Autó alap", "Megtakarítási számla", "Lekötött betét"
    ]
}

# Leírások sablonja
DESCRIPTIONS = {
    "Élelmiszer": [
        "Tesco bevásárlás", "Auchan heti nagy bevásárlás", "Spar gyors vásárlás",
        "Lidl akciós termékek", "CBA sarok", "Piac friss zöldség",
        "Péksütemény", "Kávé útközben"
    ],
    "Lakhatás": [
        "Rezsi számla", "Lakbér", "Közös költség", "Gáz számla",
        "Villany számla", "Víz számla", "Internet", "Társasházi hozzájárulás"
    ],
    "Közlekedés": [
        "BKK bérlet", "Benzin", "Parkolás", "Taxi", "Bolt ride",
        "Vonatjegy", "Autópálya matrica", "Szerviz költség"
    ],
    "Szórakozás": [
        "Mozi jegy", "Koncert jegy", "Étterem", "Kávézó", "Pub",
        "Netflix előfizetés", "Spotify premium", "Xbox Game Pass"
    ]
}

# Helyszínek
LOCATIONS = [
    "Budapest", "Debrecen", "Szeged", "Miskolc", "Pécs", "Győr",
    "Kecskemét", "Székesfehérvár", "Szombathely", "Érd", "Online",
    "Tesco Árkád", "Westend", "Arena Mall", "MOM Park"
]

# Platformok
PLATFORMS = [
    "Bankkártya", "Készpénz", "Online", "Revolut", "PayPal",
    "Google Pay", "Apple Pay", "Wirecard", "Barion"
]

def generate_random_date(days_back: int = 365) -> str:
    """Random dátum generálása a megadott napon belül"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)
    
    # Random nap választása a tartományból
    random_days = random.randint(0, days_back)
    random_date = end_date - timedelta(days=random_days)
    
    return random_date.strftime("%Y-%m-%d")

def generate_random_amount(category: str, transaction_type: str) -> float:
    """Random összeg generálása kategória alapján"""
    if transaction_type == "income":
        if category in INCOME_CATEGORIES:
            cat_data = INCOME_CATEGORIES[category]
        else:
            cat_data = {"min": 20000, "max": 500000, "avg": 150000}
    else:
        if category in CATEGORIES_WITH_AMOUNTS:
            cat_data = CATEGORIES_WITH_AMOUNTS[category]
        else:
            cat_data = {"min": 3000, "max": 50000, "avg": 15000}
    
    # Normál eloszlás használata az átlag körül
    # 80%-ban az átlag +-50%-a, 20%-ban szélesebb tartomány
    if random.random() < 0.8:
        # Szűkebb tartomány az átlag körül
        min_amount = max(cat_data["min"], cat_data["avg"] * 0.5)
        max_amount = min(cat_data["max"], cat_data["avg"] * 1.5)
    else:
        # Teljes tartomány
        min_amount = cat_data["min"]
        max_amount = cat_data["max"]
    
    return round(random.uniform(min_amount, max_amount), 0)

def get_random_description(category: str) -> str:
    """Random leírás generálása kategória alapján"""
    if category in DESCRIPTIONS:
        return random.choice(DESCRIPTIONS[category])
    else:
        return f"{category} - {random.choice(['vásárlás', 'kifizetés', 'szolgáltatás', 'egyéb'])}"

@router.post("/transactions/generate", response_model=List[TransactionRead])
async def generate_random_transactions(
    current_user: User = Depends(get_current_user),
    count: int = Query(50, ge=1, le=1000, description="Generálandó tranzakciók száma"),
    days_back: int = Query(365, ge=30, le=1095, description="Hány napra visszamenőleg generáljon"),
    income_ratio: float = Query(0.3, ge=0.1, le=0.9, description="Bevételi tranzakciók aránya (0.1-0.9)"),
    update_balances: bool = Query(True, description="Frissítse-e az alszámla egyenlegeket")
):
    """
    Random tranzakciók generálása a felhasználóhoz
    
    - **count**: Hány tranzakciót generáljon (1-1000)
    - **days_back**: Hány napra visszamenőleg (30-1095)
    - **income_ratio**: Bevételi tranzakciók aránya (0.1-0.9)
    - **update_balances**: Frissítse-e az alszámla egyenlegeket
    """
    
    try:
        generated_transactions = []
        
        # Bevételi és kiadási tranzakciók számának meghatározása
        income_count = int(count * income_ratio)
        expense_count = count - income_count
        
        # Bevételi tranzakciók generálása
        for _ in range(income_count):
            category = random.choice(list(INCOME_CATEGORIES.keys()))
            main_account = random.choice(list(MAIN_ACCOUNTS.keys()))
            sub_account = random.choice(MAIN_ACCOUNTS[main_account])
            amount = generate_random_amount(category, "income")
            
            transaction_data = {
                "date": generate_random_date(days_back),
                "amount": amount,
                "main_account": main_account,
                "sub_account_name": sub_account,
                "kategoria": category,
                "type": "income",
                "description": get_random_description(category),
                "hour": random.randint(8, 20),
                "helyszin": random.choice(LOCATIONS) if random.random() < 0.6 else None,
                "platform": random.choice(PLATFORMS) if random.random() < 0.7 else None,
                "ismetlodo": random.random() < 0.2,  # 20% ismétlődő
                "fix_koltseg": random.random() < 0.1,  # 10% fix költség
            }
            
            # Tranzakció létrehozása
            new_transaction = Transaction(
                **transaction_data,
                user_id=PydanticObjectId(current_user.id),
                currency="HUF"
            )
            
            await new_transaction.insert()
            
            # Alszámla egyenleg frissítése
            if update_balances:
                await update_sub_account_balance(
                    current_user.id,
                    main_account,
                    sub_account,
                    amount
                )
            
            generated_transactions.append(new_transaction)
        
        # Kiadási tranzakciók generálása
        for _ in range(expense_count):
            category = random.choice(list(CATEGORIES_WITH_AMOUNTS.keys()))
            main_account = random.choice(list(MAIN_ACCOUNTS.keys()))
            sub_account = random.choice(MAIN_ACCOUNTS[main_account])
            amount = generate_random_amount(category, "expense")
            
            transaction_data = {
                "date": generate_random_date(days_back),
                "amount": -amount,  # Kiadás negatív
                "main_account": main_account,
                "sub_account_name": sub_account,
                "kategoria": category,
                "type": "expense",
                "description": get_random_description(category),
                "hour": random.randint(7, 23),
                "helyszin": random.choice(LOCATIONS) if random.random() < 0.8 else None,
                "platform": random.choice(PLATFORMS) if random.random() < 0.8 else None,
                "ismetlodo": random.random() < 0.3,  # 30% ismétlődő kiadás
                "fix_koltseg": random.random() < 0.2,  # 20% fix költség
            }
            
            # Tranzakció létrehozása
            new_transaction = Transaction(
                **transaction_data,
                user_id=PydanticObjectId(current_user.id),
                currency="HUF"
            )
            
            await new_transaction.insert()
            
            # Alszámla egyenleg frissítése
            if update_balances:
                await update_sub_account_balance(
                    current_user.id,
                    main_account,
                    sub_account,
                    -amount  # Kiadás levonása
                )
            
            generated_transactions.append(new_transaction)
        
        # TransactionRead formátumra konvertálás
        result_transactions = []
        for doc in generated_transactions:
            result_transactions.append(TransactionRead(
                id=str(doc.id),
                user_id=str(doc.user_id),
                date=doc.date,
                amount=doc.amount,
                currency=doc.currency,
                main_account=doc.main_account,
                sub_account_name=doc.sub_account_name,
                kategoria=doc.kategoria,
                type=doc.type,
                description=doc.description,
                hour=doc.hour,
                helyszin=doc.helyszin,
                platform=doc.platform,
                ismetlodo=doc.ismetlodo,
                fix_koltseg=doc.fix_koltseg,
                honap=doc.honap,
                het=doc.het,
                nap_sorszam=doc.nap_sorszam,
                year=doc.year,
                month=doc.month,
                day=doc.day,
                weekday=doc.weekday,
                # Számított mezők
                is_income=doc.amount > 0,
                is_expense=doc.amount < 0,
                absolute_amount=abs(doc.amount),
                formatted_date=doc.formatted_date,
                quarter=doc.quarter,
                is_weekend=doc.is_weekend,
                time_of_day=doc.time_of_day,
            ))
        
        return result_transactions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba a random tranzakciók generálásában: {str(e)}")

@router.delete("/transactions/clear-all")
async def clear_all_transactions(
    current_user: User = Depends(get_current_user),
    confirm: bool = Query(False, description="Megerősítés a törléshez")
):
    """
    VESZÉLYES: Az összes tranzakció törlése a felhasználóhoz
    
    - **confirm**: True értékkel kell meghívni a törlés megerősítéséhez
    """
    
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="A törlés megerősítéséhez add meg a confirm=true paramétert"
        )
    
    try:
        # Összes tranzakció törlése a felhasználóhoz
        result = await Transaction.find({"user_id": PydanticObjectId(current_user.id)}).delete()
        
        return {
            "message": f"Sikeresen törölve {result.deleted_count} tranzakció",
            "deleted_count": result.deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba a tranzakciók törlésében: {str(e)}")

@router.get("/transactions/stats")
async def get_random_generation_stats(current_user: User = Depends(get_current_user)):
    """Statisztikák a jelenlegi tranzakciókról"""
    
    try:
        transactions = await Transaction.find({"user_id": PydanticObjectId(current_user.id)}).to_list()
        
        if not transactions:
            return {"message": "Nincs tranzakció", "total_count": 0}
        
        total_count = len(transactions)
        income_count = len([t for t in transactions if t.amount > 0])
        expense_count = len([t for t in transactions if t.amount < 0])
        
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        total_expense = sum(abs(t.amount) for t in transactions if t.amount < 0)
        
        # Kategóriák szerinti csoportosítás
        categories = {}
        for t in transactions:
            cat = t.kategoria or "Egyéb"
            if cat not in categories:
                categories[cat] = {"count": 0, "total_amount": 0}
            categories[cat]["count"] += 1
            categories[cat]["total_amount"] += abs(t.amount)
        
        return {
            "total_count": total_count,
            "income_count": income_count,
            "expense_count": expense_count,
            "income_ratio": income_count / total_count if total_count > 0 else 0,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_balance": total_income - total_expense,
            "categories": dict(sorted(categories.items(), key=lambda x: x[1]["total_amount"], reverse=True)[:10]),
            "date_range": {
                "earliest": min(t.date for t in transactions),
                "latest": max(t.date for t in transactions)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba a statisztikák lekérésében: {str(e)}")