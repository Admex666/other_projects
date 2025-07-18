# app/models/transaction_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

# Bemenet létrehozáshoz
class TransactionCreate(BaseModel):
    datum: str                           # 'YYYY-MM-DD'
    osszeg: float
    user_id: int
    kategoria: Optional[str] = None
    tipus: Optional[str] = None
    bev_kiad_tipus: Optional[str] = None
    leiras: Optional[str] = None
    deviza: Optional[str] = "HUF"
    profil: Optional[str] = None
    forras: Optional[str] = None
    platform: Optional[str] = None
    helyszin: Optional[str] = None
    cimke: Optional[str] = None
    ismetlodo: Optional[bool] = None
    fix_koltseg: Optional[bool] = None
    foszamla: Optional[str] = None
    alszamla: Optional[str] = None
    cel_foszamla: Optional[str] = None
    cel_alszamla: Optional[str] = None
    transfer_amount: Optional[str] = None

    # snapshot mezők opcionálisak; ha küldöd, eltároljuk
    likvid: Optional[float] = None
    befektetes: Optional[float] = None
    megtakaritas: Optional[float] = None
    assets: Optional[float] = None

class TransactionRead(BaseModel):
    id: str = Field(..., description="Mongo _id string")
    datum: str
    osszeg: float
    user_id: int
    kategoria: Optional[str] = None
    tipus: Optional[str] = None
    bev_kiad_tipus: Optional[str] = None
    honap: Optional[str] = None
    het: Optional[int] = None
    nap_sorszam: Optional[int] = None
    leiras: Optional[str] = None
    deviza: Optional[str] = None

    # stb. – ha több mezőre szükség lesz, bővíthető

class TransactionListResponse(BaseModel):
    total: int
    items: list[TransactionRead]
