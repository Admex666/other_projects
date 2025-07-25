# app/models/limit_schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.limit import LimitType, LimitPeriod

class LimitCreate(BaseModel):
    """Limit létrehozásához használt séma"""
    name: str = Field(..., description="Limit neve")
    type: LimitType = Field(..., description="Limit típusa")
    amount: float = Field(..., gt=0, description="Limit összeg")
    period: LimitPeriod = Field(..., description="Limit időszaka")
    currency: str = Field(default="HUF", description="Deviza")
    
    # Opcionális mezők
    category: Optional[str] = Field(None, description="Kategória (category típusnál)")
    main_account: Optional[str] = Field(None, description="Főszámla (account típusnál)")
    sub_account_name: Optional[str] = Field(None, description="Alszámla (account típusnál)")
    
    # Értesítési beállítások
    notification_threshold: Optional[float] = Field(None, ge=0, le=100, description="Értesítési küszöb %")
    notify_on_exceed: bool = Field(default=True, description="Értesítés túllépéskor")
    
    @validator('category')
    def validate_category_for_type(cls, v, values):
        if values.get('type') == LimitType.CATEGORY and not v:
            raise ValueError('Kategória típusú limitnél kötelező a kategória megadása')
        return v
    
    @validator('main_account')
    def validate_account_for_type(cls, v, values):
        if values.get('type') == LimitType.ACCOUNT and not v:
            raise ValueError('Számla típusú limitnél kötelező a főszámla megadása')
        if v and v not in ['likvid', 'befektetes', 'megtakaritas']:
            raise ValueError('Érvénytelen főszámla típus')
        return v

class LimitRead(BaseModel):
    """Limit válaszhoz használt séma"""
    id: str
    user_id: str
    name: str
    type: LimitType
    amount: float
    period: LimitPeriod
    currency: str
    
    # Opcionális mezők
    category: Optional[str] = None
    main_account: Optional[str] = None
    sub_account_name: Optional[str] = None
    
    # Állapot
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Értesítési beállítások
    notification_threshold: Optional[float] = None
    notify_on_exceed: bool
    
    # Számított mezők (opcionális, ha kell)
    current_spending: Optional[float] = None
    remaining_amount: Optional[float] = None
    usage_percentage: Optional[float] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

class LimitUpdate(BaseModel):
    """Limit frissítéséhez használt séma"""
    name: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    period: Optional[LimitPeriod] = None
    currency: Optional[str] = None
    
    # Opcionális mezők
    category: Optional[str] = None
    main_account: Optional[str] = None
    sub_account_name: Optional[str] = None
    
    # Állapot
    is_active: Optional[bool] = None
    
    # Értesítési beállítások
    notification_threshold: Optional[float] = Field(None, ge=0, le=100)
    notify_on_exceed: Optional[bool] = None

class LimitListResponse(BaseModel):
    """Limit lista válasz séma"""
    limits: List[LimitRead]
    total_count: int
    active_count: int

class LimitUsage(BaseModel):
    """Limit használat információ"""
    limit_id: str
    limit_name: str
    limit_amount: float
    current_spending: float
    remaining_amount: float
    usage_percentage: float
    is_exceeded: bool
    period_start: datetime
    period_end: datetime
    
class LimitCheckResult(BaseModel):
    """Limit ellenőrzés eredménye"""
    is_allowed: bool
    exceeded_limits: List[str] = []  # Túllépett limitek ID-i
    warnings: List[str] = []         # Figyelmeztetések (pl. közel a limithez)
    message: Optional[str] = None

class LimitStatus(BaseModel):
    """Limit státusz összesítő"""
    total_limits: int
    active_limits: int
    exceeded_limits: int
    warning_limits: int  # Küszöb felett, de még nem túllépett