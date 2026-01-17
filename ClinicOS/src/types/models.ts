export interface Patient {
  id: string;
  age: number;
  gender: 'M' | 'F' | 'O';
  source: string;
  firstVisitDate: string;
  totalLTV: number;
  visitCount: number;
  lastActivity: string;
  churnScore: number;
}

export interface Doctor {
  id: string;
  name: string;
  specialty: string;
  hourlyRate: number;
  commissionRate: number;
  visitCount: number;
  revenue: number;
  profit: number;
  avgTreatmentTime: number;
  patientRetention: number;
  avgWaitTime: number;
}

export interface Treatment {
  id: string;
  category: string;
  name: string;
  duration: number;
  price: number;
  materialCost: number;
  doctorCost: number;
  profit: number;
  followUpRate: number;
}

export interface Appointment {
  id: string;
  doctorId: string;
  patientId: string;
  treatmentId: string;
  startTime: string;
  endTime: string;
  showed: boolean;
  waitTime: number;
  revenue: number;
  cost: number;
}

export interface FinancialTransaction {
  id: string;
  type: 'visit' | 'package' | 'insurance';
  amount: number;
  doctorId: string;
  treatmentId: string;
  marketingSource: string;
  margin: number;
  date: string;
}

export interface Lead {
  id: string;
  channel: string;
  campaign: string;
  converted: boolean;
  showed: boolean;
  revenue: number;
  timeToFirstVisit: number; // in days
}

export interface Resource {
  id: string;
  type: 'room' | 'machine';
  name: string;
  utilization: number;
  revenuePerHour: number;
  downtime: number;
}
