# app/routes/analysis.py
from fastapi import APIRouter, Depends, HTTPException
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

from app.core.security import get_current_user
from app.models.user import User
from app.models.transaction import Transaction, TransactionType # Importáljuk a TransactionType enumot
from app.services.UserFinancialEDA import UserFinancialEDA
from app.models.analysis_schemas import FinancialAnalysisResponse
from app.core.db import get_db # Importáljuk a get_db-t a nyers mongo kollekció eléréséhez
from motor.motor_asyncio import AsyncIOMotorDatabase # Típus-tippeléshez

router = APIRouter(prefix="/financial-analysis", tags=["financial_analysis"])

@router.get("/me", response_model=FinancialAnalysisResponse)
async def get_my_financial_analysis(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db) # Injektáljuk az adatbázis klienst
):
    """
    Visszaadja a bejelentkezett felhasználó pénzügyi elemzését.
    """
    # Tranzakciók lekérése közvetlenül a MongoDB kollekcióból dictionary formátumban,
    # elkerülve a Beanie modell validációt a lekérdezés során.
    # Ez segít, ha az adatbázisban inkonzisztens dokumentumok vannak,
    # de nekünk manuálisan kell kezelni a típuskonverziókat.
    
    transaction_collection = db.transactions # Hozzáférünk a 'transactions' kollekcióhoz
    cursor = transaction_collection.find({})
    raw_transactions_docs = await cursor.to_list()

    if not raw_transactions_docs:
        raise HTTPException(status_code=404, detail="No transaction data available in the database.")

    transactions_list = []
    for doc in raw_transactions_docs:
        try:
            # Kezeljük a potenciálisan hiányzó mezőket .get() segítségével és alapértelmezett értékekkel
            # Győződjünk meg arról, hogy a típusok megegyeznek a UserFinancialEDA elvárásaival
            
            # user_id konvertálása stringgé
            user_id_str = str(doc.get('user_id')) if doc.get('user_id') else None
            if not user_id_str: # Ha a user_id hiányzik vagy érvénytelen, hagyjuk ki ezt a dokumentumot
                continue

            # Dátum konvertálása
            date_val = doc.get('date')
            if isinstance(date_val, datetime): # Ha már datetime, akkor jó
                datum = date_val
            elif isinstance(date_val, dict) and '$date' in date_val: # MongoDB kiterjesztett JSON dátum formátum
                # Feltételezve, hogy {"$date": {"$numberLong": "MILLISECONDS"}} formátumban van
                try:
                    millis = int(date_val['$date']['$numberLong'])
                    datum = datetime.fromtimestamp(millis / 1000)
                except (KeyError, ValueError, TypeError):
                    datum = datetime.now() # Visszaesés aktuális dátumra
            else:
                datum = datetime.now() # Visszaesés aktuális dátumra más formátumok esetén

            # Biztosítsuk, hogy az 'amount' float legyen
            osszeg = float(doc.get('amount', 0.0)) # Alapértelmezett 0.0, ha hiányzik vagy nem konvertálható

            # Enum típus kezelése a 'type' mezőhöz
            transaction_type_val = doc.get('type')
            if isinstance(transaction_type_val, TransactionType):
                tipus = transaction_type_val.value
            elif isinstance(transaction_type_val, str):
                tipus = transaction_type_val
            else:
                tipus = "unknown" # Visszaesés "unknown" értékre

            transactions_list.append({
                'datum': datum,
                'osszeg': osszeg,
                'user_id': user_id_str,
                'profil': doc.get('profil', 'ismeretlen'), # Alapértelmezett 'ismeretlen', ha hiányzik
                'kategoria': doc.get('kategoria', 'ismeretlen'), # Alapértelmezett 'ismeretlen', ha hiányzik
                'fix_koltseg': doc.get('fix_koltseg', False), # Alapértelmezett False, ha hiányzik
                'tipus': tipus
            })
        except Exception as e:
            # Naplózzuk a hibát, és hagyjuk ki ezt a dokumentumot, ha súlyosan hibás
            print(f"Hiba a tranzakciós dokumentum feldolgozásakor: {doc} - {e}")
            continue

    if not transactions_list:
        raise HTTPException(status_code=404, detail="No valid transaction data found after processing.")

    df = pd.DataFrame(transactions_list)

    # Inicializáljuk az elemző osztályt a teljes adathalmazzal
    eda = UserFinancialEDA(df)

    # Futtatjuk az elemzést a jelenlegi felhasználóra
    analysis_result = eda.analyze_user(str(current_user.id), show_plots=False)

    if analysis_result is None:
        raise HTTPException(status_code=404, detail=f"No transactions found for user ID: {current_user.id}.")

    # Visszaadjuk az elemzés eredményét a Pydantic modell szerint
    return FinancialAnalysisResponse(**analysis_result)