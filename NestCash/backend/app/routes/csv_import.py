# app/routes/csv_import.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import base64
import logging

from app.core.security import get_current_user
from app.models.user import User
from app.models.category import Category
from app.models.account import AllUserAccountsDocument
from app.models.csv_import_models import (
    CSVPreviewResponse, ImportConfiguration, ImportExecuteRequest, 
    ImportResult, ColumnMapping
)
from app.services.csv_import_service import CSVImportService

router = APIRouter(prefix="/import", tags=["csv-import"])
logger = logging.getLogger(__name__)

@router.post("/csv/upload", response_model=CSVPreviewResponse)
async def upload_csv_for_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """CSV fájl feltöltése és előnézet generálása"""
    
    # Fájl típus ellenőrzése
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Fájl méret ellenőrzése (max 5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="File size too large (max 5MB)")
    
    try:
        # Base64 enkódolás
        base64_data = base64.b64encode(content).decode('utf-8')
        
        # Előnézet generálása
        preview = await CSVImportService.preview_csv(base64_data)
        
        return preview
        
    except Exception as e:
        logger.error(f"CSV preview error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")

@router.post("/csv/preview", response_model=CSVPreviewResponse) 
async def preview_csv_with_base64(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Base64 encoded CSV előnézet (frontend használatra)"""
    try:
        file_data = request.get('file_data')
        if not file_data:
            raise HTTPException(status_code=422, detail="file_data field is required")
            
        preview = await CSVImportService.preview_csv(file_data)
        return preview
    except Exception as e:
        logger.error(f"CSV preview error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")

@router.get("/csv/user-data")
async def get_user_import_data(
    current_user: User = Depends(get_current_user)
):
    """User adatok lekérdezése az import konfigurációhoz"""
    try:
        # Felhasználó kategóriáinak lekérdezése
        categories = await Category.find({"user_id": current_user.id}).to_list()
        category_names = [cat.name for cat in categories]
        
        # Felhasználó számláinak lekérdezése
        all_accounts_doc = await AllUserAccountsDocument.find_one()
        accounts = {
            "main_accounts": ["likvid", "befektetes", "megtakaritas"],
            "sub_accounts": {}
        }
        
        if all_accounts_doc and current_user.id in all_accounts_doc.accounts_by_user:
            user_accounts = all_accounts_doc.accounts_by_user[current_user.id]
            
            accounts["sub_accounts"] = {
                "likvid": list(user_accounts.likvid.alszamlak.keys()) if user_accounts.likvid.alszamlak else [],
                "befektetes": list(user_accounts.befektetes.alszamlak.keys()) if user_accounts.befektetes.alszamlak else [],
                "megtakaritas": list(user_accounts.megtakaritas.alszamlak.keys()) if user_accounts.megtakaritas.alszamlak else []
            }
        
        return {
            "categories": category_names,
            "accounts": accounts,
            "supported_currencies": ["HUF", "EUR", "USD", "GBP"]
        }
        
    except Exception as e:
        logger.error(f"Error getting user import data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user data: {str(e)}")

@router.post("/csv/execute", response_model=ImportResult)
async def execute_csv_import(
    request: ImportExecuteRequest,
    current_user: User = Depends(get_current_user)
):
    """CSV import végrehajtása"""
    try:
        # Import végrehajtása
        result = await CSVImportService.execute_import(
            user_id=current_user.id,
            base64_data=request.file_data,
            configuration=request.configuration
        )
        
        # Import statisztikák logolása
        logger.info(f"Import completed for user {current_user.id}: "
                   f"{result.success_count} success, {result.error_count} errors, "
                   f"{result.duplicate_count} duplicates")
        
        return result
        
    except Exception as e:
        logger.error(f"Import execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.post("/csv/validate-mapping")
async def validate_column_mapping(
    mappings: List[ColumnMapping],
    current_user: User = Depends(get_current_user)
):
    """Oszlop leképezések validálása"""
    try:
        errors = []
        
        # Kötelező mezők ellenőrzése
        required_fields = ['date', 'amount', 'description']
        mapped_fields = [mapping.app_field.value for mapping in mappings 
                        if mapping.app_field.value != 'ignore']
        
        for required_field in required_fields:
            if required_field not in mapped_fields:
                errors.append(f"Required field '{required_field}' is not mapped")
        
        # Duplikált leképezések ellenőrzése
        field_counts = {}
        for mapping in mappings:
            if mapping.app_field.value == 'ignore':
                continue
            field_counts[mapping.app_field.value] = field_counts.get(mapping.app_field.value, 0) + 1
        
        for field, count in field_counts.items():
            if count > 1:
                errors.append(f"Field '{field}' is mapped multiple times")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Mapping validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")