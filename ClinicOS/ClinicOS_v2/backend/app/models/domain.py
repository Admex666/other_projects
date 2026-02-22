from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime
import enum

Base = declarative_base()

class AppointmentStatus(enum.Enum):
    BOOKED = "booked"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"

class PatientStatus(enum.Enum):
    NEW = "new"
    ACTIVE = "active"
    DORMANT = "dormant"
    LOST = "lost"

class Clinic(Base):
    __tablename__ = "clinics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    location = Column(String)
    capacity = Column(Integer)  # e.g., max appointments per day
    
    doctors = relationship("Doctor", back_populates="clinic")
    services = relationship("Service", back_populates="clinic")
    appointments = relationship("Appointment", back_populates="clinic")

class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    specialization = Column(String)
    hourly_rate = Column(Float)
    clinic_id = Column(Integer, ForeignKey("clinics.id"))
    
    clinic = relationship("Clinic", back_populates="doctors")
    appointments = relationship("Appointment", back_populates="doctor")

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)
    cost = Column(Float)
    margin = Column(Float)
    average_treatment_count = Column(Integer, default=1)
    treatment_cycle_length_days = Column(Integer)
    clinic_id = Column(Integer, ForeignKey("clinics.id"))
    
    clinic = relationship("Clinic", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    first_visit_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Enum(PatientStatus), default=PatientStatus.NEW)
    ltv = Column(Float, default=0.0)
    marketing_source = Column(String)
    
    appointments = relationship("Appointment", back_populates="patient")
    treatment_cycles = relationship("TreatmentCycle", back_populates="patient")
    revenue_events = relationship("RevenueEvent", back_populates="patient")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.BOOKED)
    clinic_id = Column(Integer, ForeignKey("clinics.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    
    clinic = relationship("Clinic", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

class TreatmentCycle(Base):
    __tablename__ = "treatment_cycles"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    start_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    is_dropped = Column(Boolean, default=False)
    
    patient = relationship("Patient", back_populates="treatment_cycles")

class RevenueEvent(Base):
    __tablename__ = "revenue_events"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    amount = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    source = Column(String)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="revenue_events")
