from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.domain import RevenueEvent, Appointment, AppointmentStatus, Patient, PatientStatus, Service
from app.models.schemas import SimulationParams
from datetime import datetime, timedelta

class ScenarioService:
    @staticmethod
    def run_simulation(db: Session, params: SimulationParams):
        # 1. Baseline - Last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Current Revenue
        baseline_revenue = db.query(func.sum(RevenueEvent.amount)).filter(
            RevenueEvent.date >= thirty_days_ago
        ).scalar() or 0.0
        
        # Current No-shows
        total_appts = db.query(func.count(Appointment.id)).filter(
            Appointment.date >= thirty_days_ago
        ).scalar() or 0
        no_shows = db.query(func.count(Appointment.id)).filter(
            Appointment.date >= thirty_days_ago,
            Appointment.status == AppointmentStatus.NO_SHOW
        ).scalar() or 0
        
        # Current Avg Service Value
        avg_service_value = db.query(func.avg(Service.price)).scalar() or 0.0
        
        # --- Forecast Logic ---
        
        # A. Revenue from No-show reduction
        # If we reduce no-shows, we assume these slots are filled with avg service price
        recovered_appts = no_shows * (params.no_show_reduction_percent / 100)
        revenue_from_no_show_reduction = recovered_appts * avg_service_value
        
        # B. Revenue from Price increase
        # Apply price increase to baseline revenue
        revenue_from_price_increase = baseline_revenue * (params.price_increase_percent / 100)
        
        # C. Revenue from New patients
        # Assuming new patients bring baseline avg revenue per patient
        new_patient_revenue = baseline_revenue * (params.new_patient_increase_percent / 100)
        
        forecasted_revenue = baseline_revenue + revenue_from_no_show_reduction + revenue_from_price_increase + new_patient_revenue
        
        return {
            "baseline_revenue": baseline_revenue,
            "forecasted_revenue": forecasted_revenue,
            "delta": forecasted_revenue - baseline_revenue,
            "breakdown": {
                "no_show_recovery": revenue_from_no_show_reduction,
                "price_optimization": revenue_from_price_increase,
                "new_patient_growth": new_patient_revenue
            }
        }
