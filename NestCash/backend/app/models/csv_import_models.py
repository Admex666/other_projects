# app/models/csv_import_models.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class CSVColumnType(str, Enum):
    """CSV oszlop típusok"""
    DATE = "date"
    AMOUNT = "amount"
    DESCRIPTION = "description"
    TYPE = "type"
    CURRENCY = "currency"
    CATEGORY = "category"
    IGNORE = "ignore"

class ColumnMapping(BaseModel):
    """Egy CSV oszlop leképezése az app mezőjére"""
    csv_column_name: str = Field(..., description="CSV oszlop neve")
    app_field: CSVColumnType = Field(..., description="App mező típusa")
    required: bool = Field(True, description="Kötelező mező-e")

class CSVPreviewRow(BaseModel):
    """CSV előnézet egy sora"""
    row_index: int
    data: Dict[str, Any]
    parsed_data: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)

class CSVPreviewResponse(BaseModel):
    """CSV előnézet válasz"""
    headers: List[str]
    sample_rows: List[CSVPreviewRow]
    total_rows: int
    detected_mappings: List[ColumnMapping] = Field(default_factory=list)

class ImportConfiguration(BaseModel):
    """Import konfigurációs beállítások"""
    main_account: str = Field(..., description="Főszámla típusa")
    sub_account_name: str = Field(..., description="Alszámla neve")
    default_category: Optional[str] = Field(None, description="Alapértelmezett kategória")
    column_mappings: List[ColumnMapping] = Field(..., description="Oszlop leképezések")
    skip_duplicates: bool = Field(True, description="Duplikátumok átugrása")
    date_format: str = Field("%Y-%m-%d %H:%M:%S", description="Dátum formátum")

class TransactionImportData(BaseModel):
    """Egy importálandó tranzakció adatai"""
    date: str
    amount: float
    description: str
    type: str  # income/expense
    category: Optional[str] = None
    currency: str = "HUF"
    is_duplicate: bool = False
    original_row: Dict[str, Any]

class ImportExecuteRequest(BaseModel):
    """Import végrehajtási kérés"""
    file_data: str = Field(..., description="Base64 encoded CSV data")
    configuration: ImportConfiguration

class ImportResult(BaseModel):
    """Import eredmény"""
    success_count: int = 0
    error_count: int = 0
    duplicate_count: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    imported_transaction_ids: List[str] = Field(default_factory=list)

class ImportStats(BaseModel):
    """Import statisztikák"""
    total_income: float = 0.0
    total_expenses: float = 0.0
    by_category: Dict[str, float] = Field(default_factory=dict)
    by_currency: Dict[str, float] = Field(default_factory=dict)