from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base

# --- DIMENSIONS ---

class DimDate(Base):
    __tablename__ = "dim_date"
    date_id = Column(Integer, primary_key=True) # YYYYMMDD
    date_actual = Column(Date, unique=True, nullable=False)
    year = Column(Integer)
    month = Column(Integer)
    day = Column(Integer)
    quarter = Column(Integer)
    week_of_year = Column(Integer)
    day_name = Column(String)
    month_name = Column(String)
    is_weekend = Column(Boolean)

class DimClinicLocation(Base):
    __tablename__ = "dim_clinic_location"
    location_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    city = Column(String)
    capacity_rooms = Column(Integer)

class DimDoctor(Base):
    __tablename__ = "dim_doctor"
    doctor_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    specialization = Column(String)
    employment_type = Column(String) # Full-time, Part-time, Contractor
    seniority_level = Column(String) # Junior, Senior, Head
    base_salary_monthly = Column(Float)
    commission_rate = Column(Float)

class DimService(Base):
    __tablename__ = "dim_service"
    service_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    category = Column(String) # Diagnostics, Treatment, surgery, etc.
    base_price = Column(Float)
    base_cost = Column(Float) # Material cost + overhead
    duration_minutes = Column(Integer)
    required_equipment = Column(String)

class DimMarketingSource(Base):
    __tablename__ = "dim_marketing_source"
    source_id = Column(Integer, primary_key=True, index=True)
    channel_name = Column(String) # Facebook, Google Ads, Referral, Organic
    campaign_name = Column(String)
    cost_per_acquisition_target = Column(Float)

class DimPatient(Base):
    __tablename__ = "dim_patient"
    patient_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String) # Fake
    phone = Column(String) # Fake
    birth_date = Column(Date)
    gender = Column(String)
    acquisition_date = Column(Date)
    marketing_source_id = Column(Integer, ForeignKey("dim_marketing_source.source_id"))
    
    # Segment Labels (Calculated/Updated periodically)
    segment = Column(String, default="New") # New, Recurring, Loyal, Churn Risk, Lost
    total_lifetime_value = Column(Float, default=0.0)
    last_visit_date = Column(Date, nullable=True)

class DimPaymentType(Base):
    __tablename__ = "dim_payment_type"
    payment_type_id = Column(Integer, primary_key=True, index=True)
    method_name = Column(String) # Cash, Card, Insurance, Installment

# --- FACTS ---

class FactAppointment(Base):
    __tablename__ = "fact_appointment"
    appointment_id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    date_id = Column(Integer, ForeignKey("dim_date.date_id"))
    patient_id = Column(Integer, ForeignKey("dim_patient.patient_id"))
    doctor_id = Column(Integer, ForeignKey("dim_doctor.doctor_id"))
    service_id = Column(Integer, ForeignKey("dim_service.service_id"))
    location_id = Column(Integer, ForeignKey("dim_clinic_location.location_id"))
    
    # Metrics
    appointment_datetime = Column(DateTime)
    status = Column(String) # Scheduled, Completed, Cancelled_Patient, Cancelled_Clinic, No_Show
    created_at = Column(DateTime)
    lead_time_days = Column(Integer) # Days between booking and appointment

class FactTreatment(Base):
    """
    Detailed treatment log - often 1:1 with completed appointments, 
    but allows for multiple procedures per visit if needed.
    """
    __tablename__ = "fact_treatment"
    treatment_id = Column(Integer, primary_key=True, index=True)
    
    appointment_id = Column(Integer, ForeignKey("fact_appointment.appointment_id"))
    patient_id = Column(Integer, ForeignKey("dim_patient.patient_id"))
    doctor_id = Column(Integer, ForeignKey("dim_doctor.doctor_id"))
    service_id = Column(Integer, ForeignKey("dim_service.service_id"))
    date_id = Column(Integer, ForeignKey("dim_date.date_id"))
    
    outcome = Column(String) # Successful, Complication, Referral
    patient_satisfaction_score = Column(Integer) # 1-10

class FactRevenue(Base):
    __tablename__ = "fact_revenue"
    revenue_id = Column(Integer, primary_key=True, index=True)
    
    appointment_id = Column(Integer, ForeignKey("fact_appointment.appointment_id"))
    patient_id = Column(Integer, ForeignKey("dim_patient.patient_id"))
    doctor_id = Column(Integer, ForeignKey("dim_doctor.doctor_id"))
    service_id = Column(Integer, ForeignKey("dim_service.service_id"))
    date_id = Column(Integer, ForeignKey("dim_date.date_id"))
    location_id = Column(Integer, ForeignKey("dim_clinic_location.location_id"))
    payment_type_id = Column(Integer, ForeignKey("dim_payment_type.payment_type_id"))
    
    # Money
    gross_revenue = Column(Float)
    discount_amount = Column(Float)
    net_revenue = Column(Float) # Gross - Discount
    material_cost = Column(Float)
    doctor_commission = Column(Float)
    gross_margin = Column(Float) # Net - (Material + Commission)
    
    is_refund = Column(Boolean, default=False)
