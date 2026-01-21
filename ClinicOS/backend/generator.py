import random
from datetime import date, timedelta, datetime
import pandas as pd
from faker import Faker
from sqlalchemy.orm import Session
from backend.database import engine, SessionLocal, Base
from backend.models import *

fake = Faker('hu_HU') # Hungarian locale

# --- CONFIGURATION (The Hidden Anomalies) ---
START_DATE = date(2023, 1, 1)
END_DATE = date(2025, 12, 31)

def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def create_dimensions(db: Session):
    print("Creating Dimensions...")
    
    # --- LOCATIONS ---
    loc1 = DimClinicLocation(name="Buda Clinic", city="Budapest", capacity_rooms=5)
    loc2 = DimClinicLocation(name="Pest Clinic", city="Budapest", capacity_rooms=3)
    db.add_all([loc1, loc2])
    db.commit()

    # --- SERVICES (1. False Good Service, 6. Pricing Flaw) ---
    services = [
        # Normal
        DimService(name="General Consultation", category="Consultation", base_price=25000, base_cost=5000, duration_minutes=30),
        DimService(name="Dental Extraction", category="Treatment", base_price=45000, base_cost=10000, duration_minutes=60),
        
        # 1. False Good Service: High Revenue, Low Retention
        DimService(name="Premium Body Scan", category="Diagnostics", base_price=180000, base_cost=40000, duration_minutes=90),
        
        # 6. Pricing Flaw: "3-Step Therapy" - Good entry, but high dropout
        DimService(name="Physio Therapy Session", category="Rehab", base_price=15000, base_cost=8000, duration_minutes=45),
        
        # High Margin, Good Service
        DimService(name="Laser Whitening", category="Aesthetic", base_price=90000, base_cost=15000, duration_minutes=60),
    ]
    db.add_all(services)
    db.commit()

    # --- DOCTORS (3. Capacity Illusion, 7. Doctor-dependent Churn) ---
    doctors = [
        # 3. Capacity Illusion: Overworked Star
        DimDoctor(name="Dr. Kovács Béla", specialization="General", employment_type="Full-time", seniority_level="Senior", base_salary_monthly=1200000, commission_rate=0.15),
        # 3. Capacity Illusion: Underutilized (maybe new or unliked)
        DimDoctor(name="Dr. Szabó Anna", specialization="General", employment_type="Part-time", seniority_level="Junior", base_salary_monthly=600000, commission_rate=0.10),
        
        # 7. Doctor-dependent Churn: "The Grumpy One"
        DimDoctor(name="Dr. Nagy Péter", specialization="Diagnostics", employment_type="Contractor", seniority_level="Senior", base_salary_monthly=0, commission_rate=0.40),
        
        # Good Doctor (High retention)
        DimDoctor(name="Dr. Varga Éva", specialization="Dental", employment_type="Full-time", seniority_level="Head", base_salary_monthly=1500000, commission_rate=0.20),
    ]
    db.add_all(doctors)
    db.commit()

    # --- MARKETING SOURCES (5. Marketing Paradox) ---
    sources = [
        DimMarketingSource(channel_name="Organic", campaign_name="None", cost_per_acquisition_target=0),
        DimMarketingSource(channel_name="Referral", campaign_name="Partner Program", cost_per_acquisition_target=5000),
        # 5. Marketing Paradox: High Volume, Bad Quality
        DimMarketingSource(channel_name="Facebook Ads", campaign_name="Q1 Aggressive", cost_per_acquisition_target=12000),
        DimMarketingSource(channel_name="Google Ads", campaign_name="Search_HighIntent", cost_per_acquisition_target=25000),
    ]
    db.add_all(sources)
    db.commit()
    
    # --- PAYMENT TYPES ---
    payments = [
        DimPaymentType(method_name="Cash"),
        DimPaymentType(method_name="Card"),
        DimPaymentType(method_name="Health Fund"),
    ]
    db.add_all(payments)
    db.commit()
    
    # --- DATES ---
    # Generate dates for 3 years
    curr = START_DATE
    dates = []
    id_counter = 1
    while curr <= END_DATE:
        dates.append(DimDate(
            date_id=int(curr.strftime('%Y%m%d')),
            date_actual=curr,
            year=curr.year,
            month=curr.month,
            day=curr.day,
            quarter=(curr.month-1)//3 + 1,
            week_of_year=curr.isocalendar()[1],
            day_name=curr.strftime('%A'),
            month_name=curr.strftime('%B'),
            is_weekend=curr.weekday() >= 5
        ))
        curr += timedelta(days=1)
    db.add_all(dates)
    db.commit()

    return {
        "services": {s.name: s for s in services},
        "doctors": {d.name: d for d in doctors},
        "sources": {s.channel_name: s for s in sources},
    }

def generate_patients(db: Session, num_patients=500):
    print(f"Generating {num_patients} patients...")
    sources = db.query(DimMarketingSource).all()
    source_weights = [0.2, 0.3, 0.4, 0.1] # High weight on FB Ads (index 2)
    
    patients = []
    for _ in range(num_patients):
        src = random.choices(sources, weights=source_weights, k=1)[0]
        
        # 2. Invisible Churn & 4. Bad Patient Mix logic embedded in segments
        # Assign hidden 'persona'
        persona = "Normal"
        if src.channel_name == "Facebook Ads" and random.random() < 0.6:
            persona = "Discount Hunter" # High churn, no-show
        elif random.random() < 0.15:
            persona = "High Value"
            
        p = DimPatient(
            name=fake.name(),
            email=fake.email(),
            phone=fake.phone_number(),
            birth_date=fake.date_of_birth(minimum_age=18, maximum_age=80),
            gender=random.choice(['M', 'F']),
            acquisition_date=fake.date_between(start_date=START_DATE, end_date=END_DATE),
            marketing_source_id=src.source_id,
            segment=persona # Storing our secret persona in segment for now, logic will use it
        )
        patients.append(p)
    
    db.add_all(patients)
    db.commit()

def simulate_activity(db: Session, dim_map):
    print("Simulating 3 years of clinic activity...")
    
    patients = db.query(DimPatient).all()
    dates = db.query(DimDate).order_by(DimDate.date_id).all()
    # payments = db.query(DimPaymentType).all()
    
    # Pre-fetch objects for speed
    doc_kovacs = dim_map['doctors']["Dr. Kovács Béla"] # Overworked
    doc_szabo = dim_map['doctors']["Dr. Szabó Anna"]   # Underused
    doc_nagy = dim_map['doctors']["Dr. Nagy Péter"]    # Grumpy/Churn
    doc_varga = dim_map['doctors']["Dr. Varga Éva"]    # Good
    
    srv_scan = dim_map['services']["Premium Body Scan"] # False Good
    srv_physio = dim_map['services']["Physio Therapy Session"] # Pricing Flaw
    
    appointments = []
    revenue_entries = []
    
    # Simulation State
    active_patient_pool = []
    
    for d in dates:
        # 1. New Patient Inflow (Drifts up over time - 8. False Growth)
        # 2023: 1/day, 2025: 3/day
        growth_factor = (d.year - 2023) + 1
        daily_new_limit = int(growth_factor * random.uniform(0.5, 1.5))
        
        # Introduce new patients who 'acquired' on or before this date
        # (Simplification: just picking from our pre-gen pool who match date)
        # Actually better: Just pick random existing patients to 'activate' if we didn't use acquisition_date strictly
        # Let's filter pre-generated patients by acquisition date
        new_today = [p for p in patients if p.acquisition_date == d.date_actual]
        active_patient_pool.extend(new_today)
        
        if not active_patient_pool:
            continue
            
        # 2. Booking Logic
        # Iterate over doctors to fill slots
        todays_appts = 0
        
        # Define capacity per doctor
        doc_capacity = {
            doc_kovacs.doctor_id: 12, # Popular
            doc_szabo.doctor_id: 8,   # Unpopular
            doc_nagy.doctor_id: 10,
            doc_varga.doctor_id: 10
        }
        
        daily_demand = len(active_patient_pool) * 0.05 # 5% of active base wants appt today? Adjusted for realism
        if d.is_weekend:
            daily_demand *= 0.1
            
        # Allocating patients to doctors
        potential_visits = random.sample(active_patient_pool, k=min(len(active_patient_pool), int(daily_demand)))
        
        for p in potential_visits:
            # DECISION: Who do they see?
            # 3. Capacity Illusion: Everyone wants Kovacs
            if p.segment == "High Value":
                physician = doc_varga
            elif random.random() < 0.6:
                physician = doc_kovacs
            else:
                physician = random.choice([doc_szabo, doc_nagy])
            
            # Check Capacity
            current_doc_load = sum(1 for a in appointments if a.doctor_id == physician.doctor_id and a.date_id == d.date_id) # Inefficient search, optimize if slow
            
            # If Kovacs is full, spillover to Szabo or LOST?
            if current_doc_load >= doc_capacity[physician.doctor_id]:
                if physician == doc_kovacs:
                    # 3. Capacity Illusion: Wait times increase -> Churn?
                    # or they just don't book today (lost revenue opportunity)
                    continue 
                else:
                    # Others rarely full
                    pass
            
            # DECISION: What service?
            # 1. False Good Service bias
            if random.random() < 0.15:
                service = srv_scan
            elif p.segment == "Discount Hunter":
                service = srv_physio
            else:
                service = random.choice(list(dim_map['services'].values()))
                
            # DECISION: Show or No-Show?
            # 4. Bad Patient Mix & 5. Marketing Paradox
            status = "Completed"
            if p.segment == "Discount Hunter" or p.segment == "New":
                 if random.random() < 0.3: # High no-show
                     status = "No_Show"
            
            # 7. Doctor Dependent Churn
            # If they see Nagy, high chance they don't come back (handled in 'next visit' logic implicitly by not re-entering pool)
            # Actually, we need to mark them as 'churned' so they are removed from active_pool
            
            # Create Appointment
            appt = FactAppointment(
                date_id=d.date_id,
                patient_id=p.patient_id,
                doctor_id=physician.doctor_id,
                service_id=service.service_id,
                location_id=1, # Simplified
                appointment_datetime=datetime.combine(d.date_actual, datetime.min.time()) + timedelta(hours=9),
                status=status,
                created_at=datetime.combine(d.date_actual, datetime.min.time()) - timedelta(days=random.randint(1, 14)),
                lead_time_days=random.randint(1, 14)
            )
            
            # Money (only if completed or late cancel/no-show fee)
            if status == "Completed":
                rev = FactRevenue(
                    date_id=d.date_id,
                    patient_id=p.patient_id,
                    doctor_id=physician.doctor_id,
                    service_id=service.service_id,
                    location_id=1,
                    payment_type_id=random.randint(1, 3),
                    gross_revenue=service.base_price,
                    discount_amount=0,
                    net_revenue=service.base_price,
                    material_cost=service.base_cost,
                    doctor_commission=service.base_price * physician.commission_rate,
                    gross_margin=service.base_price - (service.base_cost + (service.base_price * physician.commission_rate))
                )
                revenue_entries.append(rev)
                
                # CHURN LOGIC
                # 1. False Good Service: Scan users think "done, bye"
                if service == srv_scan and random.random() < 0.9:
                    if p in active_patient_pool: active_patient_pool.remove(p)
                
                # 7. Doctor Churn: Nagy makes people leave
                if physician == doc_nagy and random.random() < 0.4:
                    if p in active_patient_pool: active_patient_pool.remove(p)
                    
                # 2. Invisible Churn (Discount Hunters from FB)
                if p.segment == "Discount Hunter" and random.random() < 0.7:
                     if p in active_patient_pool: active_patient_pool.remove(p)
            
            elif status == "No_Show":
                 # No revenue, but opportunity cost
                 pass
                 
            appointments.append(appt)

        # Bulk add every month to save memory/speed?
        # For this demo script, just keeping in list is risky for memory if 3 years.
        # Let's flush every month.
        if d.day == 28:
            db.add_all(appointments)
            db.add_all(revenue_entries)
            db.commit()
            appointments = []
            revenue_entries = []
            print(f"Processed {d.year}-{d.month}")

    # Final flush
    if appointments:
        db.add_all(appointments)
        db.add_all(revenue_entries)
        db.commit()

if __name__ == "__main__":
    db = SessionLocal()
    setup_db()
    dims = create_dimensions(db)
    generate_patients(db, num_patients=1200) # 3 years worth of patients
    simulate_activity(db, dims)
    print("Data Generation Complete.")
