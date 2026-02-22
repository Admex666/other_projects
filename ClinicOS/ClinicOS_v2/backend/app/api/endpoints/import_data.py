from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.import_service import ImportService
from typing import List

router = APIRouter()

@router.post("/csv/{model_type}")
async def import_csv(
    model_type: str, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        count = ImportService.import_from_csv(db, content, model_type)
        return {"message": f"Successfully imported {count} records for {model_type}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/json/{model_type}")
async def import_json(
    model_type: str, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        count = ImportService.import_from_json(db, content, model_type)
        return {"message": f"Successfully imported {count} records for {model_type}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
