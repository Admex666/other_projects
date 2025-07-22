# app/models/transaction_schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class TransactionCreate(BaseModel):
    date: datetime = Field(default_factory=datetime.now, description="A tranzakció dátuma és ideje")
    amount: float = Field(..., gt=0, description="A tranzakció összege")

    main_account: Literal["likvid", "befektetes", "megtakaritas"] = Field(..., description="A tranzakcióhoz tartozó főszámla típusa (likvid, befektetes, megtakaritas)")
    sub_account_name: str = Field(..., description="A tranzakcióhoz tartozó alszámla neve")

    kategoria: Optional[str] = None
    type: Literal["income", "expense", "transfer", "adjustment"] = Field(..., description="A tranzakció típusa (income/expense/transfer/adjustment)") # Módosítva
    description: Optional[str] = None
    
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
    date: datetime
    amount: float
    
    main_account: str
    sub_account_name: str

    kategoria: Optional[str] = None
    type: str # Kimeneten elegendő str
    currency: str

    tranzakcio_id: Optional[str] = None
    profil: Optional[str] = None
    description: Optional[str] = None
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