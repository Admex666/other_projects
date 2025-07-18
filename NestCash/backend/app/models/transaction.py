# app/models/transaction.py
from __future__ import annotations
from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Transaction(Document):
    # Alap
    datum: str                         # ISO dátum 'YYYY-MM-DD'
    osszeg: float
    user_id: int
    kategoria: Optional[str] = None
    tipus: Optional[str] = None        # 'bevetel' / 'kiadas' / 'impulzus' stb.
    bev_kiad_tipus: Optional[str] = None

    # Meta
    tranzakcio_id: Optional[str] = None
    profil: Optional[str] = None
    leiras: Optional[str] = None
    forras: Optional[str] = None
    platform: Optional[str] = None
    helyszin: Optional[str] = None
    deviza: Optional[str] = "HUF"
    cimke: Optional[str] = None
    celhoz_kotott: Optional[str] = None

    # Dátum derived
    honap: Optional[str] = None  # 'YYYY-MM'
    het: Optional[int] = None
    nap_sorszam: Optional[int] = None
    ho: Optional[str] = None     # redundáns a mintában – hagyjuk

    # Flags
    ismetlodo: Optional[bool] = None
    fix_koltseg: Optional[bool] = None

    # Snapshot egyenlegek
    likvid: Optional[float] = None
    befektetes: Optional[float] = None
    megtakaritas: Optional[float] = None
    assets: Optional[float] = None

    # Transfer routing
    foszamla: Optional[str] = None
    alszamla: Optional[str] = None
    cel_foszamla: Optional[str] = None
    cel_alszamla: Optional[str] = None
    transfer_amount: Optional[str] = None

    class Settings:
        name = "transactions"

    # Opcionális: auto kitöltés mentés előtt
    async def before_insert(self):
        self._fill_derived_date_fields()

    async def before_replace(self):
        self._fill_derived_date_fields()

    def _fill_derived_date_fields(self):
        """
        Derive honap, het, nap_sorszam from datum if possible.
        datum expected 'YYYY-MM-DD'.
        """
        try:
            dt = datetime.strptime(self.datum, "%Y-%m-%d").date()
        except Exception:
            return
        self.honap = dt.strftime("%Y-%m")
        self.ho = self.honap  # backward compat
        self.het = dt.isocalendar().week  # ISO hét
        self.nap_sorszam = dt.weekday()   # 0=hétfő
