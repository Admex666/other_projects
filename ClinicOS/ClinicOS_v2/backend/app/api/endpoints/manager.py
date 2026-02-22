from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.kpi_service import KPIService
from app.services.marketing_service import MarketingService

router = APIRouter()

@router.get("/doctor-performance")
async def get_doctor_performance(db: Session = Depends(get_db)):
    return KPIService.get_doctor_performance(db)

@router.get("/utilization")
async def get_utilization(db: Session = Depends(get_db)):
    return KPIService.get_utilization(db)

@router.get("/marketing-deepdive")
async def get_marketing_deepdive(db: Session = Depends(get_db)):
    return MarketingService.get_marketing_roi(db)

@router.get("/leakage")
async def get_leakage(db: Session = Depends(get_db)):
    from app.services.retention_service import RetentionService
    return RetentionService.get_treatment_dropout_rate(db)
