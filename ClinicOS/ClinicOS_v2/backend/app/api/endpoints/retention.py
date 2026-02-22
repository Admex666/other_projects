from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.retention_service import RetentionService

router = APIRouter()

@router.get("/churn-risk")
async def get_churn_risk(db: Session = Depends(get_db)):
    risks = RetentionService.identify_churn_risk(db)
    return {
        "dormant": [{"id": r.id, "name": r.name, "ltv": r.ltv} for r in risks["dormant"]],
        "lost": [{"id": r.id, "name": r.name, "ltv": r.ltv} for r in risks["lost"]],
        "dormant_count": len(risks["dormant"]),
        "lost_count": len(risks["lost"])
    }

@router.get("/cohorts")
async def get_cohorts(db: Session = Depends(get_db)):
    return RetentionService.get_cohort_analysis(db)

@router.post("/update-statuses")
async def update_statuses(db: Session = Depends(get_db)):
    count = RetentionService.update_patient_statuses(db)
    return {"message": f"Updated status for {count} patients"}
