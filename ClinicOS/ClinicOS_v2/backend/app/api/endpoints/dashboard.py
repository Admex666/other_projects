from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.kpi_service import KPIService

router = APIRouter()

@router.get("/summary")
async def get_summary(db: Session = Depends(get_db)):
    return KPIService.get_executive_summary(db)

@router.get("/revenue-trend")
async def get_revenue_trend(db: Session = Depends(get_db), days: int = 30):
    return KPIService.get_revenue_trend(db, days)
