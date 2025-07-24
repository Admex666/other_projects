# app/models/transaction.py
from __future__ import annotations
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, validator, computed_field
from typing import Optional
from datetime import datetime
import calendar

class Transaction(Document):
    user_id: PydanticObjectId
    date: str = Field(..., description="Tranzakció dátuma YYYY-MM-DD formátumban")
    amount: float = Field(..., description="Összeg (pozitív: bevétel, negatív: kiadás)")
    currency: str = Field(default="HUF", description="Deviza")
    main_account: str = Field(..., description="Főszámla típusa (likvid, befektetes, megtakaritas)")
    sub_account_name: str = Field(..., description="Alszámla neve")
    kategoria: Optional[str] = Field(None, description="Kategória")
    type: str = Field(..., description="Tranzakció típusa: income, expense, transfer")
    description: Optional[str] = Field(None, description="Leírás")
    
    # Opcionális mezők
    profil: Optional[str] = Field(None, description="Profil")
    platform: Optional[str] = Field(None, description="Platform")
    helyszin: Optional[str] = Field(None, description="Helyszín")
    ismetlodo: Optional[bool] = Field(False, description="Ismétlődő tranzakció")
    fix_koltseg: Optional[bool] = Field(False, description="Fix költség")
    celhoz_kotott: Optional[bool] = Field(False, description="Célhoz kötött")
    
    # Időbeli mezők - ezek automatikusan számítódnak
    honap: Optional[str] = Field(None, description="Hónap (YYYY-MM)")
    het: Optional[str] = Field(None, description="Hét (YYYY-WXX)")
    nap_sorszam: Optional[int] = Field(None, description="A hét napjának sorszáma (0=hétfő)")
    hour: Optional[int] = Field(default=12, description="Óra (0-23)")
    year: Optional[int] = Field(None, description="Év")
    month: Optional[int] = Field(None, description="Hónap száma (1-12)")
    day: Optional[int] = Field(None, description="Nap")
    weekday: Optional[str] = Field(None, description="Hét napja")
    
    @validator('date')
    def validate_date_format(cls, v):
        """Dátum formátum ellenőrzése"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('A dátumnak YYYY-MM-DD formátumúnak kell lennie')
    
    @validator('hour')
    def validate_hour(cls, v):
        """Óra értékének ellenőrzése"""
        if v is not None and (v < 0 or v > 23):
            raise ValueError('Az órának 0 és 23 között kell lennie')
        return v
    
    def __init__(self, **data):
        super().__init__(**data)
        # Időbélyegek automatikus generálása
        self._generate_time_fields()
    
    def _generate_time_fields(self):
        """Időbélyegek automatikus generálása a dátum alapján"""
        if self.date:
            try:
                date_obj = datetime.strptime(self.date, '%Y-%m-%d')
                
                # Alapvető időbélyegek
                self.year = date_obj.year
                self.month = date_obj.month
                self.day = date_obj.day
                self.weekday = calendar.day_name[date_obj.weekday()]
                
                # Hónap string formátumban
                self.honap = date_obj.strftime('%Y-%m')
                
                # Hét formátumban (ISO week)
                year, week, _ = date_obj.isocalendar()
                self.het = f"{year}-W{week:02d}"
                
                # Hét napjának sorszáma (0=hétfő, 6=vasárnap)
                self.nap_sorszam = date_obj.weekday()
                
            except ValueError:
                pass  # Ha hibás a dátum formátum, nem generálunk időbélyegeket
    
    @computed_field
    @property
    def is_income(self) -> bool:
        """Bevétel-e a tranzakció"""
        return self.amount > 0
    
    @computed_field
    @property
    def is_expense(self) -> bool:
        """Kiadás-e a tranzakció"""
        return self.amount < 0
    
    @computed_field
    @property
    def absolute_amount(self) -> float:
        """Abszolút érték"""
        return abs(self.amount)
    
    @computed_field
    @property
    def formatted_date(self) -> str:
        """Formázott dátum"""
        try:
            date_obj = datetime.strptime(self.date, '%Y-%m-%d')
            return date_obj.strftime('%Y. %m. %d.')
        except ValueError:
            return self.date
    
    @computed_field
    @property
    def quarter(self) -> str:
        """Negyedév meghatározása"""
        if self.month:
            q = (self.month - 1) // 3 + 1
            return f"{self.year}-Q{q}"
        return None
    
    @computed_field
    @property
    def is_weekend(self) -> bool:
        """Hétvégén történt-e"""
        return self.nap_sorszam in [5, 6] if self.nap_sorszam is not None else False
    
    @computed_field
    @property
    def time_of_day(self) -> str:
        """Napszak meghatározása"""
        if self.hour is None:
            return "ismeretlen"
        elif 6 <= self.hour < 12:
            return "reggel"
        elif 12 <= self.hour < 18:
            return "délután"
        elif 18 <= self.hour < 22:
            return "este"
        else:
            return "éjszaka"
    
    async def save(self, **kwargs):
        """Mentés előtt időbélyegek frissítése"""
        self._generate_time_fields()
        return await super().save(**kwargs)
    
    class Settings:
        name = "transactions"
        indexes = [
            "user_id",
            "date",
            "kategoria",
            "type",
            "main_account",
            "honap",
            "het",
            [("user_id", 1), ("date", -1)],  # Kompozit index
            [("user_id", 1), ("honap", 1)],   # Havi lekérdezésekhez
            [("user_id", 1), ("kategoria", 1)],  # Kategória szerinti lekérdezésekhez
        ]