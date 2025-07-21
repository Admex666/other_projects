from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase # Szükséges a közvetlen db hozzáféréshez
import logging
from bson import ObjectId # Szükséges az _id kezeléséhez, ha van

from app.models.account import AccountDetails, UserAccounts
from app.models.user import User
from app.core.security import get_current_user
from app.core.db import get_db # Szükséges a get_db függvényhez

router = APIRouter(prefix="/accounts", tags=["accounts"])
logger = logging.getLogger(__name__)

@router.get("/me", response_model=UserAccounts)
async def get_my_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db) # Direkt hozzáférés a db objektumhoz
):
    """
    Lekérdezi a bejelentkezett felhasználó számlaadatait.
    Ha nincs adat, létrehozza az alapértelmezett struktúrát.
    """
    try:
        user_id_str = str(current_user.id) # Az MVP-ben a user_id int volt, itt string

        # Megkeressük az EGYETLEN dokumentumot az "accounts" kollekcióban
        # Az MVP szerint ez a dokumentum tartalmazza az összes user_id-t kulcsként
        accounts_data_doc = await db["accounts"].find_one()

        if accounts_data_doc and user_id_str in accounts_data_doc:
            # Visszaadjuk a felhasználóhoz tartozó adatokat
            # Fontos: a MongoDB dict-et vissza kell alakítani Pydantic modellé
            return UserAccounts(**accounts_data_doc[user_id_str])

        # Ha ide jutunk, akkor nincs még adat ehhez a felhasználóhoz, vagy nincs "accounts" dokumentum
        default_accounts_data = {
            "likvid": {"foosszeg": 0.0},
            "befektetes": {"foosszeg": 0.0},
            "megtakaritas": {"foosszeg": 0.0}
        }
        
        # Alapértelmezett Pydantic modell létrehozása
        default_user_accounts = UserAccounts(**default_accounts_data)

        # Ha nincs még "accounts" dokumentum
        if accounts_data_doc is None:
            # Létrehozunk egy új dokumentumot a felhasználó adataival
            await db["accounts"].insert_one({
                user_id_str: default_accounts_data
            })
            logger.info(f"Created new accounts document and initial data for user {user_id_str}")
        else:
            # Ha van dokumentum, de a user_id nincs benne, frissítjük
            # Megjegyzés: Az MVP-ben az _id-t használta a frissítéshez.
            # Feltételezzük, hogy az "accounts" kollekcióban csak egy ilyen dokumentum van.
            await db["accounts"].update_one(
                {"_id": accounts_data_doc["_id"]}, # Az MVP-ből származó _id használata
                {"$set": {user_id_str: default_accounts_data}}
            )
            logger.info(f"Added initial account data for user {user_id_str} to existing document.")

        return default_user_accounts

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_my_accounts for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve or initialize account data: {e}")

# Mivel a GET /me kezeli az inicializálást, a POST / lehet, hogy nem szükséges,
# de ha mégis kell egy explicit inicializáló végpont:
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserAccounts)
async def create_initial_accounts_explicit(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Explicit inicializáló végpont, ha a GET /me nem hozná létre automatikusan, vagy újra létre kellene hozni.
    Ez a logika is tükrözi az MVP viselkedését, de a GET /me már magától megoldja.
    """
    try:
        user_id_str = str(current_user.id)
        accounts_data_doc = await db["accounts"].find_one()

        default_accounts_data = {
            "likvid": {"foosszeg": 0.0},
            "befektetes": {"foosszeg": 0.0},
            "megtakaritas": {"foosszeg": 0.0}
        }
        default_user_accounts = UserAccounts(**default_accounts_data)

        if accounts_data_doc is None:
            await db["accounts"].insert_one({user_id_str: default_accounts_data})
            logger.info(f"Created new accounts document with initial data for user {user_id_str} via POST.")
        else:
            if user_id_str in accounts_data_doc:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account data already exists for this user in the master document.")
            
            await db["accounts"].update_one(
                {"_id": accounts_data_doc["_id"]},
                {"$set": {user_id_str: default_accounts_data}}
            )
            logger.info(f"Added initial account data for user {user_id_str} to existing document via POST.")
        
        return default_user_accounts
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_initial_accounts_explicit for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create initial account data: {e}")