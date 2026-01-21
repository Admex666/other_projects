from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from backend.models import DimPatient, DimMarketingSource

engine = create_engine("sqlite:///./clinicos.db")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("Checking Patient Segments:")
segments = db.query(DimPatient.segment, func.count(DimPatient.patient_id)).group_by(DimPatient.segment).all()
for s in segments:
    print(s)

print("\nChecking Marketing Sources:")
sources = db.query(DimMarketingSource.channel_name, func.count(DimPatient.patient_id))\
    .join(DimPatient)\
    .group_by(DimMarketingSource.channel_name).all()
for s in sources:
    print(s)
