from bson import ObjectId
from fastapi import FastAPI, HTTPException
from beanie import init_beanie
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

app = FastAPI()

# Almodell a foosszeg mezőhöz
class SubAccount(BaseModel):
    foosszeg: int = 0

# Fő modell (nem Beanie-s, mert egyedi szerkezetű dokumentum)
class AccountStructure(BaseModel):
    likvid: SubAccount
    befektetes: SubAccount
    megtakaritas: SubAccount

# Adatbázis kapcsolat globálisan
client = None
db = None

@app.on_event("startup")
async def app_init():
    global client, db
    load_dotenv()
    MONGO_URI = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client["nestcash"]

# 🔍 Egyedi user_id alapján account lekérdezés
@app.get("/accounts/{user_id}", response_model=AccountStructure)
async def get_user_accounts(user_id: int):
    try:
        user_id_str = str(user_id)
        accounts_data = await db["accounts"].find_one()

        if accounts_data and user_id_str in accounts_data:
            return accounts_data[user_id_str]

        # Alapértelmezett struktúra
        default_accounts = {
            "likvid": {"foosszeg": 0},
            "befektetes": {"foosszeg": 0},
            "megtakaritas": {"foosszeg": 0}
        }

        # Ha nincs dokumentum, beszúrjuk
        if accounts_data is None:
            await db["accounts"].insert_one({user_id_str: default_accounts})
        else:
            await db["accounts"].update_one(
                {"_id": accounts_data["_id"]},
                {"$set": {user_id_str: default_accounts}}
            )

        return default_accounts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba történt: {e}")
