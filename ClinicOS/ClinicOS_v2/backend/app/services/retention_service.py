from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.domain import Patient, Appointment, PatientStatus, AppointmentStatus
from datetime import datetime, timedelta
from typing import List

class RetentionService:
    @staticmethod
    def identify_churn_risk(db: Session, dormant_days: int = 90, lost_days: int = 180):
        now = datetime.utcnow()
        dormant_threshold = now - timedelta(days=dormant_days)
        lost_threshold = now - timedelta(days=lost_days)
        
        # Patients with no appointments since dormant_threshold are "at risk"
        # We look at the latest appointment for each patient
        subquery = db.query(
            Appointment.patient_id,
            func.max(Appointment.date).label("last_appt")
        ).group_by(Appointment.patient_id).subquery()
        
        dormant_patients = db.query(Patient).join(
            subquery, Patient.id == subquery.c.patient_id
        ).filter(
            subquery.c.last_appt < dormant_threshold,
            subquery.c.last_appt >= lost_threshold
        ).all()
        
        lost_patients = db.query(Patient).join(
            subquery, Patient.id == subquery.c.patient_id
        ).filter(
            subquery.c.last_appt < lost_threshold
        ).all()
        
        return {
            "dormant": dormant_patients,
            "lost": lost_patients
        }

    @staticmethod
    def get_cohort_analysis(db: Session):
        # Group patients by their first visit month
        patients = db.query(Patient).all()
        if not patients:
            return []
            
        data = []
        for p in patients:
            month = p.first_visit_date.strftime("%Y-%m")
            data.append({"month": month, "patient_id": p.id, "ltv": p.ltv})
            
        import pandas as pd
        df = pd.DataFrame(data)
        cohorts = df.groupby("month").agg(
            total_patients=("patient_id", "count"),
            avg_ltv=("ltv", "mean"),
            total_revenue=("ltv", "sum")
        ).reset_index()
        
        return cohorts.to_dict(orient="records")

    @staticmethod
    def update_patient_statuses(db: Session):
        # Automatically update statuses based on activity
        risks = RetentionService.identify_churn_risk(db)
        
        for p in risks["dormant"]:
            p.status = PatientStatus.DORMANT
            
        for p in risks["lost"]:
            p.status = PatientStatus.LOST
            
        db.commit()
        return len(risks["dormant"]) + len(risks["lost"])
    @staticmethod
    def get_treatment_dropout_rate(db: Session):
        from app.models.domain import TreatmentCycle
        total = db.query(func.count(TreatmentCycle.id)).scalar() or 0
        dropped = db.query(func.count(TreatmentCycle.id)).filter(TreatmentCycle.is_dropped == True).scalar() or 0
        
        return {
            "total_cycles": total,
            "dropped_cycles": dropped,
            "dropout_rate": (dropped / total * 100) if total > 0 else 0
        }
