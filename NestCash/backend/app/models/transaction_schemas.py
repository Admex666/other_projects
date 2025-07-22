# app/models/transaction_schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class TransactionCreate(BaseModel):
    date: datetime = Field(default_factory=datetime.now, description="A tranzakció dátuma és ideje")
    amount: float = Field(..., description="A tranzakció összege") # Módosítva: elengedve a gt=0 validáció, ha kiadást is kezelünk

    main_account: Literal["likvid", "befektetes", "megtakaritas"] = Field(..., description="A tranzakcióhoz tartozó főszámla típusa (likvid, befektetes, megtakaritas)")
    sub_account_name: str = Field(..., description="A tranzakcióhoz tartozó alszámla neve")

    kategoria: Optional[str] = None
    type: Literal["income", "expense", "transfer", "adjustment"] = Field(..., description="A tranzakció típusa (income/expense/transfer/adjustment)")
    description: Optional[str] = None # Már Optional

    # A deviza mező továbbra is hiányzik a bemenetről, a backend fogja feltölteni az alszámla alapján

    profil: Optional[str] = None
    forras: Optional[str] = None
    platform: Optional[str] = None
    helyszin: Optional[str] = None
    cimke: Optional[str] = None
    ismetlodo: Optional[bool] = None
    fix_koltseg: Optional[bool] = None

class TransactionRead(BaseModel):
    id: str = Field(..., description="Mongo _id string")
    user_id: str
    date: datetime # datum helyett date
    amount: float # osszeg helyett amount

    main_account: str # foszamla helyett main_account
    sub_account_name: str # alszamla helyett sub_account_name

    kategoria: Optional[str] = None
    type: str # Kimeneten elegendő str (tipus helyett type)
    currency: str # deviza helyett currency

    tranzakcio_id: Optional[str] = None
    profil: Optional[str] = None
    description: Optional[str] = None # leiras helyett description
    forras: Optional[str] = None
    platform: Optional[str] = None
    helyszin: Optional[str] = None
    cimke: Optional[str] = None
    celhoz_kotott: Optional[str] = None

    honap: Optional[str] = None
    het: Optional[int] = None
    nap_sorszam: Optional[int] = None

    ismetlodo: Optional[bool] = None
    fix_koltseg: Optional[bool] = None

    class Config:
        populate_by_name = True

class TransactionListResponse(BaseModel):
    total_count: int
    transactions: List[TransactionRead]