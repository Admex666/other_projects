from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import RevenueEvent, Appointment, AppointmentStatus, Patient, PatientStatus
from datetime import datetime, timedelta
import pandas as pd

class KPIService:
    @staticmethod
    def get_executive_summary(db: Session):
        # 1. Total Revenue
        total_revenue = db.query(func.sum(RevenueEvent.amount)).scalar() or 0.0
        
        # 2. No-show Rate
        total_appointments = db.query(func.count(Appointment.id)).scalar() or 0
        no_shows = db.query(func.count(Appointment.id)).filter(
            Appointment.status == AppointmentStatus.NO_SHOW
        ).scalar() or 0
        no_show_rate = (no_shows / total_appointments * 100) if total_appointments > 0 else 0.0
        
        # 3. Patient Retention (Returning vs New)
        total_patients = db.query(func.count(Patient.id)).scalar() or 0
        new_patients = db.query(func.count(Patient.id)).filter(
            Patient.status == PatientStatus.NEW
        ).scalar() or 0
        returning_patients = total_patients - new_patients
        
        # 4. Revenue at Risk (LTV of Lost/Dormant patients)
        revenue_at_risk = db.query(func.sum(Patient.ltv)).filter(
            Patient.status.in_([PatientStatus.LOST, PatientStatus.DORMANT])
        ).scalar() or 0.0
        
        return {
            "total_revenue": total_revenue,
            "no_show_rate": no_show_rate,
            "patient_mix": {
                "new": new_patients,
                "returning": returning_patients
            },
            "revenue_at_risk": revenue_at_risk
        }

    @staticmethod
    def get_revenue_trend(db: Session, days: int = 30):
        start_date = datetime.utcnow() - timedelta(days=days)
        revenue_events = db.query(RevenueEvent).filter(RevenueEvent.date >= start_date).all()
        
        if not revenue_events:
            return []
            
        df = pd.DataFrame([{
            "date": r.date.strftime("%Y-%m-%d"),
            "amount": r.amount
        } for r in revenue_events])
        
        trend = df.groupby("date")["amount"].sum().reset_index()
        return trend.to_dict(orient="records")

    @staticmethod
    def get_doctor_performance(db: Session):
        from app.models import domain
        performance = db.query(
            domain.Doctor.name.label('doctor_name'),
            domain.Doctor.specialization,
            func.sum(domain.RevenueEvent.amount).label('total_revenue'),
            func.sum(domain.RevenueEvent.profit).label('total_profit'),
            func.avg(domain.RevenueEvent.profit / domain.RevenueEvent.amount).label('avg_margin'),
            func.count(domain.Appointment.id).label('appointment_count')
        ).join(domain.Appointment, domain.Doctor.id == domain.Appointment.doctor_id)\
         .outerjoin(domain.RevenueEvent, domain.Appointment.id == domain.RevenueEvent.id)\
         .group_by(domain.Doctor.id).all()

        return [
            {
                "name": p.doctor_name,
                "specialization": p.specialization,
                "revenue": float(p.total_revenue or 0),
                "profit": float(p.total_profit or 0),
                "margin": float(p.avg_margin or 0) * 100,
                "appointments": p.appointment_count
            } for p in performance
        ]

    @staticmethod
    def get_utilization(db: Session):
        from app.models import domain
        # Calculate utilization for the last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Get appointments per day
        daily_appts = db.query(
            func.date(domain.Appointment.date).label('date'),
            func.count(domain.Appointment.id).label('count')
        ).filter(domain.Appointment.date >= seven_days_ago)\
         .group_by(func.date(domain.Appointment.date)).all()

        clinic = db.query(domain.Clinic).first()
        if not clinic:
            return []

        daily_capacity = clinic.capacity # appointments per day max
        
        return [
            {
                "date": str(d.date),
                "utilization": (d.count / daily_capacity) * 100 if daily_capacity > 0 else 0
            } for d in daily_appts
        ]
