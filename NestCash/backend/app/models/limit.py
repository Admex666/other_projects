# app/models/limit.py
from __future__ import annotations
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime, timedelta
from enum import Enum

class LimitType(str, Enum):
    SPENDING = "spending"  # Általános kiadási limit
    CATEGORY = "category"  # Kategória-specifikus limit
    ACCOUNT = "account"    # Számla-specifikus limit

class LimitPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Limit(Document):
    user_id: PydanticObjectId
    name: str = Field(..., description="Limit neve (pl. 'Havi élelmiszer budget')")
    type: LimitType = Field(..., description="Limit típusa")
    amount: float = Field(..., gt=0, description="Limit összeg (mindig pozitív)")
    period: LimitPeriod = Field(..., description="Limit időszaka")
    currency: str = Field(default="HUF", description="Deviza")
    
    # Opcionális mezők típusfüggően
    category: Optional[str] = Field(None, description="Kategória neve (category típusnál kötelező)")
    main_account: Optional[str] = Field(None, description="Főszámla (account típusnál)")
    sub_account_name: Optional[str] = Field(None, description="Alszámla neve (account típusnál)")
    
    # Állapot és időzítés
    is_active: bool = Field(default=True, description="Aktív-e a limit")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Értesítési beállítások
    notification_threshold: Optional[float] = Field(None, ge=0, le=100, description="Értesítési küszöb %-ban")
    notify_on_exceed: bool = Field(default=True, description="Értesítés túllépéskor")
    
    @validator('category')
    def validate_category_for_type(cls, v, values):
        """Kategória típusnál kötelező a kategória megadása"""
        if values.get('type') == LimitType.CATEGORY and not v:
            raise ValueError('Kategória típusú limitnél kötelező a kategória megadása')
        return v
    
    @validator('main_account')
    def validate_account_for_type(cls, v, values):
        """Account típusnál kötelező a főszámla megadása"""
        if values.get('type') == LimitType.ACCOUNT and not v:
            raise ValueError('Számla típusú limitnél kötelező a főszámla megadása')
        if v and v not in ['likvid', 'befektetes', 'megtakaritas']:
            raise ValueError('Érvénytelen főszámla típus')
        return v
    
    @validator('notification_threshold')
    def validate_threshold(cls, v):
        """Értesítési küszöb validálása"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Az értesítési küszöbnek 0 és 100 között kell lennie')
        return v
    
    async def save(self, **kwargs):
        """Mentés előtt updated_at frissítése"""
        self.updated_at = datetime.utcnow()
        return await super().save(**kwargs)
    
    def get_period_start(self, reference_date: datetime = None) -> datetime:
        """Aktuális időszak kezdetének kiszámítása"""
        if reference_date is None:
            reference_date = datetime.utcnow()
            
        if self.period == LimitPeriod.DAILY:
            return reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.period == LimitPeriod.WEEKLY:
            # Hét kezdete (hétfő)
            days_since_monday = reference_date.weekday()
            week_start = reference_date - timedelta(days=days_since_monday)
            return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.period == LimitPeriod.MONTHLY:
            return reference_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif self.period == LimitPeriod.YEARLY:
            return reference_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    def get_period_end(self, reference_date: datetime = None) -> datetime:
        """Aktuális időszak végének kiszámítása"""
        from datetime import timedelta
        import calendar
        
        if reference_date is None:
            reference_date = datetime.utcnow()
            
        if self.period == LimitPeriod.DAILY:
            return reference_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif self.period == LimitPeriod.WEEKLY:
            # Hét vége (vasárnap)
            days_since_monday = reference_date.weekday()
            week_end = reference_date + timedelta(days=(6 - days_since_monday))
            return week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif self.period == LimitPeriod.MONTHLY:
            # Hónap utolsó napja
            last_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
            return reference_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        elif self.period == LimitPeriod.YEARLY:
            return reference_date.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
    
    class Settings:
        name = "limits"
        indexes = [
            "user_id",
            "type",
            "is_active",
            [("user_id", 1), ("is_active", 1)],  # Aktív limitek lekérdezéséhez
            [("user_id", 1), ("type", 1)],       # Típus szerinti lekérdezésekhez
            [("user_id", 1), ("category", 1)],   # Kategória specifikus limitek
        ]