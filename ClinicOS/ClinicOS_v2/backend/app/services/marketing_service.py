from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import domain
from datetime import datetime

class MarketingService:
    @staticmethod
    def get_marketing_roi(db: Session):
        # Group patients by marketing source and calculate revenue metrics
        stats = db.query(
            domain.Patient.marketing_source,
            func.count(domain.Patient.id).label('patient_count'),
            func.sum(domain.RevenueEvent.amount).label('total_revenue'),
            func.avg(domain.Patient.ltv).label('avg_ltv')
        ).join(domain.RevenueEvent, domain.Patient.id == domain.RevenueEvent.patient_id)\
         .group_by(domain.Patient.marketing_source).all()

        return [
            {
                "source": s.marketing_source or "Unknown",
                "volume": s.patient_count,
                "revenue": float(s.total_revenue or 0),
                "avg_ltv": float(s.avg_ltv or 0)
            } for s in stats
        ]
