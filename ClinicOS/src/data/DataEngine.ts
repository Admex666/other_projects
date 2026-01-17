import Papa from 'papaparse';
import type { Patient, Doctor, Appointment, FinancialTransaction, Lead, Resource } from '../types/models';

export interface OLAPData {
    fact_appointments: any[];
    dim_doctors: any[];
    dim_treatments: any[];
    dim_patients: any[];
    dim_dates: any[];
    dim_channels: any[];
}

export interface QueryConfig {
    dimension: string; // e.g., 'doctor_key', 'treatment_key', 'month', 'gender'
    metrics: string[]; // e.g., ['revenue', 'profit', 'wait_time']
    filters?: Record<string, any>;
}

export class DataEngine {
    patients: Patient[] = [];
    appointments: Appointment[] = [];
    transactions: FinancialTransaction[] = [];
    leads: Lead[] = [];
    resources: Resource[] = [];
    doctors: Doctor[] = [];

    olap: OLAPData | null = null;
    isLoaded = false;

    async loadData() {
        const fetchCSV = async (name: string) => {
            const resp = await fetch(`/data/csv/${name}.csv`);
            const csvText = await resp.text();
            return Papa.parse(csvText, { header: true, dynamicTyping: true }).data;
        };

        try {
            const [
                fact_appointments,
                dim_doctors,
                dim_treatments,
                dim_patients,
                dim_dates,
                dim_channels
            ] = await Promise.all([
                fetchCSV('fact_appointments'),
                fetchCSV('dim_doctors'),
                fetchCSV('dim_treatments'),
                fetchCSV('dim_patients'),
                fetchCSV('dim_dates'),
                fetchCSV('dim_channels')
            ]);

            this.olap = {
                fact_appointments: fact_appointments.filter((f: any) => f.transaction_id), // Clean empty rows
                dim_doctors: dim_doctors.filter((d: any) => d.doctor_key),
                dim_treatments: dim_treatments.filter((t: any) => t.treatment_key),
                dim_patients: dim_patients.filter((p: any) => p.patient_key),
                dim_dates: dim_dates.filter((d: any) => d.date_key),
                dim_channels: dim_channels.filter((c: any) => c.channel_key)
            };

            this.transformData();
            this.isLoaded = true;
        } catch (error) {
            console.error('Failed to load OLAP data:', error);
        }
    }

    /**
     * Dynamic OLAP Query Engine
     * Slices and dices the fact table based on dimensions and metrics
     */
    query(config: QueryConfig) {
        if (!this.olap) return [];

        let dataset = [...this.olap.fact_appointments];

        // 1. Apply Filters
        if (config.filters) {
            dataset = dataset.filter(row => {
                return Object.entries(config.filters!).every(([key, value]) => row[key] === value);
            });
        }

        // 2. Denormalize based on dimension (JOIN on the fly)
        const enrichedData = dataset.map(row => {
            const entry = { ...row };

            // Join Date context
            const dateDim = this.olap?.dim_dates.find(d => d.date_key === row.date_key);
            if (dateDim) {
                entry.month = dateDim.month;
                entry.year = dateDim.year;
                entry.is_weekend = dateDim.is_weekend;
            }

            // Join Patient context
            const patientDim = this.olap?.dim_patients.find(p => p.patient_key === row.patient_key);
            if (patientDim) {
                entry.gender = patientDim.gender;
                entry.age_group = Math.floor(patientDim.age / 10) * 10;
                entry.source_key = patientDim.source_key;
            }

            return entry;
        });

        // 3. Group and Aggregate
        const groups: Record<string, any> = {};

        enrichedData.forEach(row => {
            const groupKey = row[config.dimension] || 'Unknown';
            if (!groups[groupKey]) {
                groups[groupKey] = {
                    name: groupKey,
                    count: 0,
                    ...config.metrics.reduce((acc, m) => ({ ...acc, [m]: 0 }), {})
                };
            }

            groups[groupKey].count++;
            config.metrics.forEach(m => {
                groups[groupKey][m] += (row[m] || 0);
            });
        });

        // 4. Calculate Averages where applicable
        return Object.values(groups).map(g => {
            const result = { ...g };
            if (config.metrics.includes('wait_time_minutes')) {
                result.avg_wait_time = g.count > 0 ? g.wait_time_minutes / g.count : 0;
            }
            if (config.metrics.includes('revenue')) {
                result.avg_revenue = g.count > 0 ? g.revenue / g.count : 0;
            }
            return result;
        });
    }

    private transformData() {
        if (!this.olap) return;

        // Legacy compatibility mappings
        this.doctors = this.olap.dim_doctors.map((d: any) => ({
            id: d.doctor_key,
            name: d.name,
            specialty: d.specialty,
            hourlyRate: d.hourly_rate,
            commissionRate: d.commission_rate,
            visitCount: 0,
            revenue: 0,
            profit: 0,
            avgTreatmentTime: 45,
            patientRetention: 0.85,
            avgWaitTime: 12
        }));

        this.patients = this.olap.dim_patients.map((p: any) => ({
            id: p.patient_key,
            age: p.age,
            gender: p.gender,
            source: this.olap?.dim_channels.find(c => c.channel_key === p.source_key)?.channel_name || 'Direct',
            firstVisitDate: p.first_visit_date,
            totalLTV: 0,
            visitCount: 0,
            lastActivity: '',
            churnScore: Math.random()
        }));

        this.appointments = this.olap.fact_appointments.map((f: any) => ({
            id: f.transaction_id,
            doctorId: f.doctor_key,
            patientId: f.patient_key,
            treatmentId: f.treatment_key,
            startTime: this.olap?.dim_dates.find(d => d.date_key === f.date_key)?.full_date || '',
            endTime: this.olap?.dim_dates.find(d => d.date_key === f.date_key)?.full_date || '',
            showed: f.showed === 1,
            waitTime: f.wait_time_minutes,
            revenue: f.revenue,
            cost: f.cost
        }));

        this.transactions = this.olap.fact_appointments.filter(f => f.showed === 1).map((f: any) => ({
            id: `tr${f.transaction_id}`,
            type: 'visit',
            amount: f.revenue,
            doctorId: f.doctor_key,
            treatmentId: f.treatment_key,
            marketingSource: this.patients.find(p => p.id === f.patient_key)?.source || '',
            margin: f.margin,
            date: this.olap?.dim_dates.find(d => d.date_key === f.date_key)?.full_date || ''
        }));

        this.doctors.forEach(d => {
            const docTrans = this.transactions.filter(t => t.doctorId === d.id);
            d.visitCount = docTrans.length;
            d.revenue = docTrans.reduce((sum, t) => sum + t.amount, 0);
            d.profit = docTrans.reduce((sum, t) => sum + t.margin, 0);

            const docApps = this.appointments.filter(a => a.doctorId === d.id && a.showed);
            d.avgWaitTime = docApps.length > 0 ? Math.floor(docApps.reduce((sum, a) => sum + a.waitTime, 0) / docApps.length) : 0;
        });

        this.resources = [
            { id: 'r1', type: 'room', name: 'Kezelő 1', utilization: 0.75, revenuePerHour: 25000, downtime: 5 },
            { id: 'r2', type: 'room', name: 'Kezelő 2', utilization: 0.65, revenuePerHour: 18000, downtime: 8 },
            { id: 'r3', type: 'machine', name: 'MRI Unit', utilization: 0.85, revenuePerHour: 45000, downtime: 12 },
        ];

        this.leads = [];
    }

    getDashboardData() {
        return {
            doctors: this.doctors,
            patients: this.patients,
            appointments: this.appointments,
            transactions: this.transactions,
            leads: this.leads,
            resources: this.resources,
            olap: this.olap
        };
    }
}

export const instance = new DataEngine();
export default instance;
