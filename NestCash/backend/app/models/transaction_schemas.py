# app/models/transaction_schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class TransactionCreate(BaseModel):
    """Tranzakció létrehozásához használt séma"""
    date: str = Field(..., description="Tranzakció dátuma YYYY-MM-DD formátumban")
    amount: float = Field(..., description="Összeg (mindig pozitív, a type alapján lesz előjelezve)")
    main_account: str = Field(..., description="Főszámla típusa (likvid, befektetes, megtakaritas)")
    sub_account_name: str = Field(..., description="Alszámla neve")
    kategoria: Optional[str] = Field(None, description="Kategória")
    type: str = Field(..., description="Tranzakció típusa: income, expense, transfer")
    description: Optional[str] = Field(None, description="Leírás")
    hour: Optional[int] = Field(12, description="Óra (0-23)", ge=0, le=23)
    
    # Opcionális mezők
    profil: Optional[str] = Field(None, description="Profil")
    forras: Optional[str] = Field(None, description="Forrás")
    platform: Optional[str] = Field(None, description="Platform")
    helyszin: Optional[str] = Field(None, description="Helyszín")
    ismetlodo: Optional[bool] = Field(False, description="Ismétlődő tranzakció")
    fix_koltseg: Optional[bool] = Field(False, description="Fix költség")
    celhoz_kotott: Optional[bool] = Field(False, description="Célhoz kötött")
        
    @validator('date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('A dátumnak YYYY-MM-DD formátumúnak kell lennie')
    
    @validator('type')
    def validate_type(cls, v):
        if v not in ['income', 'expense', 'transfer']:
            raise ValueError('A típusnak income, expense vagy transfer értékűnek kell lennie')
        return v
    
    @validator('main_account')
    def validate_main_account(cls, v):
        if v not in ['likvid', 'befektetes', 'megtakaritas']:
            raise ValueError('A főszámlának likvid, befektetes vagy megtakaritas értékűnek kell lennie')
        return v

class TransactionRead(BaseModel):
    """Tranzakció válaszhoz használt séma"""
    id: str
    user_id: str
    date: str
    amount: float
    currency: str = "HUF"
    main_account: str
    sub_account_name: str
    kategoria: Optional[str] = None
    type: str
    description: Optional[str] = None
    
    # Időbélyegek
    honap: Optional[str] = None
    het: Optional[str] = None
    nap_sorszam: Optional[int] = None
    hour: Optional[int] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    weekday: Optional[str] = None
    
    # Opcionális mezők
    profil: Optional[str] = None
    platform: Optional[str] = None
    helyszin: Optional[str] = None
    cimke: Optional[str] = None
    ismetlodo: Optional[bool] = False
    fix_koltseg: Optional[bool] = False
    celhoz_kotott: Optional[bool] = False
    
    # Transzfer specifikus mezők
    cel_foszamla: Optional[str] = None
    cel_alszamla: Optional[str] = None
    transfer_amount: Optional[float] = None
    
    # Számított mezők
    is_income: Optional[bool] = None
    is_expense: Optional[bool] = None
    absolute_amount: Optional[float] = None
    formatted_date: Optional[str] = None
    quarter: Optional[str] = None
    is_weekend: Optional[bool] = None
    time_of_day: Optional[str] = None

class TransactionUpdate(BaseModel):
    """Tranzakció frissítéséhez használt séma"""
    date: Optional[str] = Field(None, description="Tranzakció dátuma YYYY-MM-DD formátumban")
    amount: Optional[float] = Field(None, description="Összeg")
    main_account: Optional[str] = Field(None, description="Főszámla típusa")
    sub_account_name: Optional[str] = Field(None, description="Alszámla neve")
    kategoria: Optional[str] = Field(None, description="Kategória")
    type: Optional[str] = Field(None, description="Tranzakció típusa")
    description: Optional[str] = Field(None, description="Leírás")
    hour: Optional[int] = Field(None, description="Óra (0-23)", ge=0, le=23)
    
    # Opcionális mezők
    profil: Optional[str] = None
    forras: Optional[str] = None
    platform: Optional[str] = None
    helyszin: Optional[str] = None
    cimke: Optional[str] = None
    ismetlodo: Optional[bool] = None
    fix_koltseg: Optional[bool] = None
    celhoz_kotott: Optional[bool] = None
    
    @validator('date')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('A dátumnak YYYY-MM-DD formátumúnak kell lennie')
        return v
    
    @validator('type')
    def validate_type(cls, v):
        if v is not None and v not in ['income', 'expense', 'transfer']:
            raise ValueError('A típusnak income, expense vagy transfer értékűnek kell lennie')
        return v

class TransactionListResponse(BaseModel):
    """Tranzakció lista válasz séma"""
    transactions: List[TransactionRead]
    total_count: int
    skip: int
    limit: int
    has_more: Optional[bool] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # has_more automatikus számítása
        if self.has_more is None:
            self.has_more = (self.skip + len(self.transactions)) < self.total_count

class TransactionSummary(BaseModel):
    """Tranzakció összesítő séma"""
    total_income: float
    total_expense: float
    net_balance: float
    transaction_count: int
    category_summary: dict
    period_start: str
    period_end: str

class CategorySummary(BaseModel):
    """Kategória összesítő séma"""
    category: str
    income_total: float
    expense_total: float
    net_total: float
    transaction_count: int
    avg_transaction_amount: float

class MonthlyTrend(BaseModel):
    """Havi trend séma"""
    month: str  # YYYY-MM
    income: float
    expense: float
    net: float
    transaction_count: int

class WeeklyTrend(BaseModel):
    """Heti trend séma"""
    week: str  # YYYY-WXX
    income: float
    expense: float
    net: float
    transaction_count: int

class DailyPattern(BaseModel):
    """Napi minta séma"""
    weekday: str
    avg_income: float
    avg_expense: float
    transaction_count: int
    peak_hour: int

class HourlyPattern(BaseModel):
    """Órás minta séma"""
    hour: int
    transaction_count: int
    avg_amount: float
    time_of_day: str  # reggel, délután, este, éjszaka