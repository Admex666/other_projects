from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case, and_
from backend.database import get_db
from backend.models import *

router = APIRouter()

@router.get("/kpi/executive")
def get_executive_summary(
    clinic_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    period: Optional[str] = "30d",
    db: Session = Depends(get_db)
):
    # 1. Total Revenue (Last 30 Days)
    # Date logic based on period
    delta = 30
    if period == "quarter": delta = 90
    elif period == "ytd": delta = 365
        
    start_date = int((date(2025, 12, 31) - timedelta(days=delta)).strftime('%Y%m%d'))
    
    # Previous Period (for trends)
    start_date_prev = int((date(2025, 12, 31) - timedelta(days=delta*2)).strftime('%Y%m%d'))
    end_date_prev = start_date # Approximate cut-off
    
    # --- 1. Total Revenue ---
    query = db.query(func.sum(FactRevenue.gross_revenue)).filter(FactRevenue.date_id >= start_date)
    query_prev = db.query(func.sum(FactRevenue.gross_revenue)).filter(FactRevenue.date_id >= start_date_prev, FactRevenue.date_id < start_date)
    
    if clinic_id:
        query = query.filter(FactRevenue.location_id == clinic_id)
        query_prev = query_prev.filter(FactRevenue.location_id == clinic_id)
        
    # Doctor filter simulation
    factor = 1.0
    if doctor_id: factor *= 0.25 
    
    revenue_total = (query.scalar() or 0) * factor
    revenue_prev = (query_prev.scalar() or 0) * factor
    
    rev_trend = ((revenue_total - revenue_prev) / revenue_prev * 100) if revenue_prev else 0
    
    # --- 2. Revenue at Risk ---
    # Current
    churn_risk_count = db.query(func.count(DimPatient.patient_id)).filter(DimPatient.segment == "Churn Risk").scalar() or 0
    avg_rev_per_patient = 45000 
    risk_rev = churn_risk_count * avg_rev_per_patient * factor
    
    # Previous (Approximation using a random fluctuation for demo as we don't have SCD Type 2 history for segments)
    risk_rev_prev = risk_rev * 0.95 
    risk_trend = ((risk_rev - risk_rev_prev) / risk_rev_prev * 100) if risk_rev_prev else 0

    # --- 3. Active Patients ---
    # Current
    active_pat_q = db.query(func.count(func.distinct(FactAppointment.patient_id))).filter(FactAppointment.date_id >= start_date)
    # Previous
    active_pat_prev_q = db.query(func.count(func.distinct(FactAppointment.patient_id))).filter(FactAppointment.date_id >= start_date_prev, FactAppointment.date_id < start_date)
    
    if clinic_id:
        active_pat_q = active_pat_q.filter(FactAppointment.location_id == clinic_id)
        active_pat_prev_q = active_pat_prev_q.filter(FactAppointment.location_id == clinic_id)
    if doctor_id:
        active_pat_q = active_pat_q.filter(FactAppointment.doctor_id == doctor_id)
        active_pat_prev_q = active_pat_prev_q.filter(FactAppointment.doctor_id == doctor_id)
        
    active_patients = active_pat_q.scalar() or 0
    active_patients_prev = active_pat_prev_q.scalar() or 0
    
    pat_trend = ((active_patients - active_patients_prev) / active_patients_prev * 100) if active_patients_prev else 0

    # --- 4. Utilization Rate ---
    # Current
    appt_count_q = db.query(func.count(FactAppointment.appointment_id)).filter(FactAppointment.date_id >= start_date)
    # Previous
    appt_count_prev_q = db.query(func.count(FactAppointment.appointment_id)).filter(FactAppointment.date_id >= start_date_prev, FactAppointment.date_id < start_date)

    if clinic_id:
        appt_count_q = appt_count_q.filter(FactAppointment.location_id == clinic_id)
        appt_count_prev_q = appt_count_prev_q.filter(FactAppointment.location_id == clinic_id)
    if doctor_id:
        appt_count_q = appt_count_q.filter(FactAppointment.doctor_id == doctor_id)
        appt_count_prev_q = appt_count_prev_q.filter(FactAppointment.doctor_id == doctor_id)
    
    total_appts = appt_count_q.scalar() or 0
    total_appts_prev = appt_count_prev_q.scalar() or 0
    
    # Capacity (same for both periods for simplicity)
    num_doctors = 4 if not doctor_id else 1
    days = 30
    if period == "quarter": days = 90
    elif period == "ytd": days = 365
    
    total_capacity = num_doctors * days * 12 
    
    utilization_rate = min(total_appts / total_capacity, 1.1) if total_capacity > 0 else 0
    utilization_rate_prev = min(total_appts_prev / total_capacity, 1.1) if total_capacity > 0 else 0
    
    util_trend = (utilization_rate - utilization_rate_prev) * 100 # Percentage point difference

    # --- 5. Chart Data (Revenue vs Cost) ---
    # Aggregate by date
    chart_q = db.query(
        FactRevenue.date_id,
        func.sum(FactRevenue.gross_revenue).label("revenue"),
        func.sum(FactRevenue.gross_margin).label("margin")
    ).filter(FactRevenue.date_id >= start_date)
    
    if clinic_id:
        chart_q = chart_q.filter(FactRevenue.location_id == clinic_id)
        
    chart_results = chart_q.group_by(FactRevenue.date_id).order_by(FactRevenue.date_id).all()
    
    chart_data = []
    # If too many days, we might want to aggregate by week, but for 30d/90d daily is okay-ish or we sample
    # Let's just return all points, frontend can handle 30-90 points easily.
    
    for r in chart_results:
        # Convert 20251201 to readable "Dec 01"
        s_date = str(r.date_id)
        d_obj = date(int(s_date[:4]), int(s_date[4:6]), int(s_date[6:]))
        fmt_date = d_obj.strftime("%b %d")
        
        rev = r.revenue * factor
        marg = r.margin * factor
        cost = rev - marg
        
        chart_data.append({
            "name": fmt_date,
            "revenue": int(rev),
            "cost": int(cost)
        })

    return {
        "revenue_total_30d": int(revenue_total),
        "revenue_at_risk": int(risk_rev),
        "active_patients": int(active_patients),
        "utilization_rate": round(utilization_rate, 2),
        "trends": {
            "revenue": round(rev_trend, 1),
            "risk": round(risk_trend, 1),
            "patients": round(pat_trend, 1),
            "utilization": round(util_trend, 1)
        },
        "chart_data": chart_data
    }

@router.get("/kpi/retention")
def get_retention_kpis(
    clinic_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # 1. Marketing Paradox: Retention by Source
    # We must count DISTINCT patients to match "New Patients" definition (Humans, not visits)
    # Filter: Patients who have had AT LEAST ONE appointment matching criteria
    
    # Base query on Patients
    query = db.query(
        DimMarketingSource.channel_name,
        func.count(func.distinct(DimPatient.patient_id)).label("total_acquired"),
        func.count(func.distinct(case((DimPatient.segment == "Churn Risk", DimPatient.patient_id), else_=None))).label("risk_count")
    ).join(DimMarketingSource)
    
    # Always join FactAppointment to ensure we are looking at actual visitors, not just leads
    # If filtering, apply filters to this join
    
    if doctor_id or clinic_id:
        match_stmt = []
        if doctor_id: match_stmt.append(FactAppointment.doctor_id == doctor_id)
        if clinic_id: match_stmt.append(FactAppointment.location_id == clinic_id)
        
        query = query.join(FactAppointment, FactAppointment.patient_id == DimPatient.patient_id).filter(and_(*match_stmt))
    else:
        # For "All", we still want only patients with appointments? 
        # Or do we include all registered?
        # User complaint: "All" rate is higher than average -> likely ghosts with 0 appointments.
        # Let's enforce JOIN FactAppointment even for ALL to ignore 0-visit ghosts if that's the issue.
        query = query.join(FactAppointment, FactAppointment.patient_id == DimPatient.patient_id)

    source_stats = query.group_by(DimMarketingSource.channel_name).all()
    
    marketing_risk = [
        {
            "channel": s.channel_name, 
            "volume": s.total_acquired, 
            "churn_rate": round(s.risk_count / s.total_acquired, 2) if s.total_acquired > 0 else 0
        }
        for s in source_stats
    ]

    # 2. Invisible Churn (Ghost Rate)
    # Patients with only 1 visit > 90 days ago (or just general churn logic as defined before)
    
    # DISTINCT Counts for consistency
    q_ghosts = db.query(func.count(func.distinct(DimPatient.patient_id))).filter(
        DimPatient.segment.in_(["Lost", "Churn Risk"])
    )
    q_total = db.query(func.count(func.distinct(DimPatient.patient_id)))
    
    if doctor_id or clinic_id:
        q_ghosts = q_ghosts.join(FactAppointment)
        q_total = q_total.join(FactAppointment)
        
        if doctor_id:
            q_ghosts = q_ghosts.filter(FactAppointment.doctor_id == doctor_id)
            q_total = q_total.filter(FactAppointment.doctor_id == doctor_id)
        if clinic_id:
            q_ghosts = q_ghosts.filter(FactAppointment.location_id == clinic_id)
            q_total = q_total.filter(FactAppointment.location_id == clinic_id)
    else:
        # Enforce consistency for "All" - only count patients who have actually visited
        q_ghosts = q_ghosts.join(FactAppointment)
        q_total = q_total.join(FactAppointment)

    ghosts = q_ghosts.scalar() or 0
    total_patients = q_total.scalar() or 0
    ghost_rate = round(ghosts / total_patients, 2) if total_patients else 0
    
    return {
        "marketing_analysis": marketing_risk,
        "ghost_rate": ghost_rate,
        "cohorts": [
            {"month": "Jan", "retention": 100},
            {"month": "Feb", "retention": 88},
            {"month": "Mar", "retention": 76},
            {"month": "Apr", "retention": 65},
            {"month": "May", "retention": 58}, 
            {"month": "Jun", "retention": 52},
        ]
    }

@router.get("/kpi/operations")
def get_ops_kpis(
    clinic_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # 3. Capacity Illusion: Utilization Rate per Doctor
    last_month_start = int((date(2025, 12, 1)).strftime('%Y%m%d'))
    
    query = db.query(
        DimDoctor.name,
        DimDoctor.employment_type,
        func.count(FactAppointment.appointment_id).label("appointments"),
        func.sum(case((FactAppointment.status == "No_Show", 1), else_=0)).label("no_shows")
    ).join(DimDoctor, FactAppointment.doctor_id == DimDoctor.doctor_id)\
     .filter(FactAppointment.date_id >= last_month_start)
    
    if clinic_id:
        query = query.filter(FactAppointment.location_id == clinic_id)

    doc_stats = query.group_by(DimDoctor.name, DimDoctor.employment_type).all()
    
    # Hardcoded capacities for demo calculation (simulating the "Illusion")
    capacities = {
        "Dr. Kovács Béla": 240, # 20 days * 12 slots
        "Dr. Szabó Anna": 160,
        "Dr. Nagy Péter": 200,
        "Dr. Varga Éva": 200
    }
    
    results = []
    for r in doc_stats:
        cap = capacities.get(r.name, 100)
        utilization = min(r.appointments / cap, 1.1) # Cap at 110%
        
        # 7. Doctor-dependent Churn risk flag
        churn_risk_score = "Low"
        if r.name == "Dr. Nagy Péter": # The Grumpy One
            churn_risk_score = "High"
            
        results.append({
            "doctor": r.name,
            "role": r.employment_type,
            "utilization": round(utilization * 100, 1),
            "no_show_rate": round(r.no_shows / r.appointments, 2) if r.appointments else 0,
            "churn_risk": churn_risk_score
        })
        
    return results

@router.get("/kpi/finance")
def get_finance_kpis(db: Session = Depends(get_db)):
    # 1. Service Profitability Bubble Chart
    # Shows Revenue vs Margin %
    results = db.query(
        DimService.name,
        DimService.category,
        func.sum(FactRevenue.gross_revenue).label("revenue"),
        func.sum(FactRevenue.gross_margin).label("margin")
    ).join(DimService, FactRevenue.service_id == DimService.service_id)\
     .group_by(DimService.name, DimService.category).all()
    
    bubbles = []
    for r in results:
        margin_pct = (r.margin / r.revenue) if r.revenue else 0
        
        # 1. False Good Service Detection
        # High Revenue, Low LTV (Simulated here by referencing predefined logic or just hardcoding the insight trigger)
        anomaly = None
        if r.name == "Premium Body Scan":
            anomaly = "High Churn Driver"
        elif r.name == "Physio Therapy Session":
            anomaly = "Pricing Flaw"
            
        bubbles.append({
            "service": r.name,
            "category": r.category,
            "revenue": r.revenue,
            "margin_pct": round(margin_pct * 100, 1),
            "anomaly": anomaly
        })
    
    return bubbles

@router.get("/kpi/forecast")
def get_forecast_kpis(db: Session = Depends(get_db)):
    # Simple What-If Scenario: "What if we fix the Marketing Paradox?"
    # Identify revenue lost to churned patients from paid channels
    
    # 1. Total lost revenue from churned patients (simulated)
    # real query would sum value of all patients in 'Churn Risk' segment
    current_annual_revenue = 125000000 # 125M Ft
    
    churn_loss = 15000000 # 15M lost to churn
    
    # Scenarios
    scenarios = [
        {
            "name": "Baseline (Do Nothing)",
            "revenue": current_annual_revenue,
            "growth": 0.05 # 5% organic
        },
        {
            "name": "Fix 'False Good' Services",
            "revenue": current_annual_revenue + (churn_loss * 0.4), # Recover 40%
            "growth": 0.12,
            "impact": "High"
        },
        {
            "name": "Optimize Utilization",
            "revenue": current_annual_revenue + 8000000,
            "growth": 0.08,
            "impact": "Medium"
        }
    ]
    
    return scenarios

@router.get("/options")
def get_filter_options(db: Session = Depends(get_db)):
    clinics = db.query(DimClinicLocation.location_id, DimClinicLocation.name, DimClinicLocation.city).all()
    doctors = db.query(DimDoctor.doctor_id, DimDoctor.name).all()
    
    return {
        "clinics": [{"id": c.location_id, "name": f"{c.name} ({c.city})", "value": c.location_id} for c in clinics],
        "doctors": [{"id": d.doctor_id, "name": d.name, "value": d.doctor_id} for d in doctors]
    }
