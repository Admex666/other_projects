from app.db.session import SessionLocal
from app.models import domain
from datetime import datetime, timedelta
import random

def seed_db():
    db = SessionLocal()
    print("Clearing existing data...")
    db.query(domain.RevenueEvent).delete()
    db.query(domain.Appointment).delete()
    db.query(domain.TreatmentCycle).delete()
    db.query(domain.Patient).delete()
    db.query(domain.Service).delete()
    db.query(domain.Doctor).delete()
    db.query(domain.Clinic).delete()
    db.commit()

    print("Seeding database...")
    
    # 1. Create Clinic
    clinic = domain.Clinic(name="Elite Clinic Budapest", location="Budapest, District V", capacity=50)
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    
    # 2. Create Doctors
    doctors = [
        domain.Doctor(name="Dr. Kovács János", specialization="Kardiológus", hourly_rate=25000, clinic_id=clinic.id),
        domain.Doctor(name="Dr. Szabó Anna", specialization="Bőrgyógyász", hourly_rate=20000, clinic_id=clinic.id),
        domain.Doctor(name="Dr. Nagy Péter", specialization="Ortopédus", hourly_rate=22000, clinic_id=clinic.id),
    ]
    db.add_all(doctors)
    db.commit()
    
    # 3. Create Services
    services = [
        domain.Service(name="Konzultáció", price=15000, cost=5000, margin=10000, clinic_id=clinic.id),
        domain.Service(name="Vizsgálat", price=25000, cost=8000, margin=17000, clinic_id=clinic.id),
        domain.Service(name="Kezelés", price=50000, cost=15000, margin=35000, clinic_id=clinic.id),
    ]
    db.add_all(services)
    db.commit()
    
    # 4. Create Patients
    patients = []
    statuses = [domain.PatientStatus.NEW, domain.PatientStatus.ACTIVE, domain.PatientStatus.DORMANT, domain.PatientStatus.LOST]
    sources = ["Google", "Facebook", "Ajánlás", "Instagram"]
    
    for i in range(50):
        status = random.choice(statuses)
        first_visit = datetime.utcnow() - timedelta(days=random.randint(1, 400))
        p = domain.Patient(
            name=f"Páciens {i+1}",
            email=f"patient{i+1}@example.com",
            first_visit_date=first_visit,
            status=status,
            ltv=random.uniform(15000, 500000),
            marketing_source=random.choice(sources)
        )
        patients.append(p)
    db.add_all(patients)
    db.commit()
    
    # 5. Create Appointments and Revenue Events
    for p in patients:
        # Create 1-5 appointments per patient
        for _ in range(random.randint(1, 5)):
            status = random.choice(list(domain.AppointmentStatus))
            doctor = random.choice(doctors)
            service = random.choice(services)
            date = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            
            appt = domain.Appointment(
                date=date,
                status=status,
                clinic_id=clinic.id,
                doctor_id=doctor.id,
                service_id=service.id,
                patient_id=p.id
            )
            db.add(appt)
            
            if status == domain.AppointmentStatus.COMPLETED:
                rev = domain.RevenueEvent(
                    patient_id=p.id,
                    amount=service.price,
                    cost=service.cost,
                    profit=service.margin,
                    source=p.marketing_source,
                    date=date
                )
                db.add(rev)
                
    # 6. Create Treatment Cycles (Leakage demo)
    for p in patients[:20]: # Only for some patients
        is_dropped = random.random() < 0.2 # 20% dropout rate
        cycle = domain.TreatmentCycle(
            patient_id=p.id,
            start_date=p.first_visit_date,
            is_completed=not is_dropped,
            is_dropped=is_dropped
        )
        db.add(cycle)
                
    db.commit()
    print("Database seeding completed.")
    db.close()

if __name__ == "__main__":
    seed_db()
