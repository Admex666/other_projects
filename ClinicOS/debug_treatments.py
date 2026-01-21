from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import FactTreatment, FactAppointment
# from backend.database import DATABASE_URL

engine = create_engine("sqlite:///./clinicos.db")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("Checking FactTreatment...")
count = db.query(FactTreatment).count()
print(f"Details: Found {count} treatment records.")

if count == 0:
    print("WARNING: Table is empty.")
    print("Checking FactAppointment count for comparison...")
    appt_count = db.query(FactAppointment).count()
    print(f"Found {appt_count} appointments.")
