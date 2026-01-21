from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import DimPatient, FactAppointment, DimMarketingSource
from datetime import date, timedelta
import random

engine = create_engine("sqlite:///./clinicos.db")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("Updating Patient Segments...")

# Simplified Logic for Demo:
# 1. "Marketing Paradox" -> Facebook Ads + Short tenure = Churn Risk
# 2. "Invisible Churn" -> 1 visit > 90 days ago = Lost
# 3. "Loyal" -> > 3 visits

# Get recent date for calculation
today = date(2025, 12, 31)
ninety_days_ago = date(2025, 10, 1)

patients = db.query(DimPatient).all()

count = 0
for p in patients:
    # Get visit count
    visit_count = db.query(FactAppointment).filter(FactAppointment.patient_id == p.patient_id).count()
    
    new_segment = "New"
    
    if visit_count == 0:
        new_segment = "New"
    elif visit_count == 1:
        # Check if ghost
        # We need check date but simplified: random ghost if acquisition was long ago
        if p.acquisition_date < ninety_days_ago:
             new_segment = "Lost" # Ghost
    elif visit_count > 3:
        new_segment = "Loyal"
    else:
        new_segment = "Recurring"
        
    # Get IDs
    fb_ads = db.query(DimMarketingSource).filter(DimMarketingSource.channel_name == "Facebook Ads").first()
    google_ads = db.query(DimMarketingSource).filter(DimMarketingSource.channel_name == "Google Ads").first()
    
    fb_id = fb_ads.source_id if fb_ads else -1
    google_id = google_ads.source_id if google_ads else -1

    p.segment = new_segment
    count += 1
    
    # Force "Churn Risk" for Marketing Paradox demo
    if p.marketing_source_id == fb_id: 
        if visit_count < 3 and visit_count > 0:
             if random.random() < 0.65: # High churn rate for FB
                 new_segment = "Churn Risk"
    
    # Add some risk to Google too for variety, but less
    if p.marketing_source_id == google_id:
         if visit_count < 3 and visit_count > 0:
             if random.random() < 0.2: 
                 new_segment = "Churn Risk"

    p.segment = new_segment

    p.segment = new_segment
    count += 1

db.commit()
print(f"Updated {count} patient segments.")
