# app/models/transaction.py

from __future__ import annotations
from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"

class Transaction(Document):
    # Alap mezők
    date: datetime = Field(default_factory=datetime.now, description="A tranzakció dátuma és ideje")
    amount: float = Field(..., description="A tranzakció összege")
    user_id: PydanticObjectId

    # Számla hivatkozások
    main_account: Literal["likvid", "befektetes", "megtakaritas"] = Field(..., description="A tranzakcióhoz tartozó főszámla típusa (likvid, befektetes, megtakaritas)")
    sub_account_name: str = Field(..., description="A tranzakcióhoz tartozó alszámla neve")

    # Módosított és megtartott mezők
    kategoria: Optional[str] = None
    type: TransactionType = Field(..., description="A tranzakció típusa (income/expense/transfer/adjustment)")
    currency: str = Field("HUF", description="A tranzakció devizaneme (az alszámlából származik)")

    # Meta
    tranzakcio_id: Optional[str] = None
    profil: Optional[str] = None
    description: Optional[str] = None # leiras helyett description
    forras: Optional[str] = None
    platform: Optional[str] = None
    helyszin: Optional[str] = None
    cimke: Optional[str] = None
    celhoz_kotott: Optional[str] = None

    # Dátum derived mezők
    honap: Optional[str] = None
    het: Optional[int] = None
    nap_sorszam: Optional[int] = None

    # Flags
    ismetlodo: Optional[bool] = None
    fix_koltseg: Optional[bool] = None

    class Settings:
        name = "transactions"

    # Auto kitöltés mentés előtt
    async def before_insert(self):
        self._fill_derived_date_fields()

    async def before_replace(self):
        self._fill_derived_date_fields()

    def _fill_derived_date_fields(self):
        """
        Derive honap, het, nap_sorszam from date if possible.
        """
        if self.date:
            self.honap = self.date.strftime("%Y-%m")
            self.het = self.date.isocalendar().week
            self.nap_sorszam = self.date.weekday()
        else:
            self.honap = None
            self.het = None
            self.nap_sorszam = None