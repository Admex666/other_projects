from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class AppointmentStatus(str, Enum):
    BOOKED = "booked"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"

class PatientStatus(str, Enum):
    NEW = "new"
    ACTIVE = "active"
    DORMANT = "dormant"
    LOST = "lost"

class ClinicBase(BaseModel):
    name: str
    location: Optional[str] = None
    capacity: Optional[int] = None

class ClinicCreate(ClinicBase):
    pass

class Clinic(ClinicBase):
    id: int
    
    class Config:
        from_attributes = True

class DoctorBase(BaseModel):
    name: str
    specialization: str
    hourly_rate: float
    clinic_id: int

class DoctorCreate(DoctorBase):
    pass

class Doctor(DoctorBase):
    id: int
    
    class Config:
        from_attributes = True

class ServiceBase(BaseModel):
    name: str
    price: float
    cost: float
    margin: float
    average_treatment_count: int = 1
    treatment_cycle_length_days: Optional[int] = None
    clinic_id: int

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    id: int
    
    class Config:
        from_attributes = True

class PatientBase(BaseModel):
    name: str
    email: EmailStr
    status: PatientStatus = PatientStatus.NEW
    ltv: float = 0.0
    marketing_source: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    first_visit_date: datetime
    
    class Config:
        from_attributes = True

class AppointmentBase(BaseModel):
    date: datetime
    status: AppointmentStatus = AppointmentStatus.BOOKED
    clinic_id: int
    doctor_id: int
    service_id: int
    patient_id: int

class AppointmentCreate(AppointmentBase):
    pass

class Appointment(AppointmentBase):
    id: int
    
    class Config:
        from_attributes = True

class RevenueEventBase(BaseModel):
    amount: float
    cost: float
    profit: float
    source: Optional[str] = None
    patient_id: int

class RevenueEventCreate(RevenueEventBase):
    pass

class RevenueEvent(RevenueEventBase):
    id: int
    date: datetime
    
    class Config:
        from_attributes = True

class SimulationParams(BaseModel):
    no_show_reduction_percent: float = 0.0
    new_patient_increase_percent: float = 0.0
    price_increase_percent: float = 0.0
