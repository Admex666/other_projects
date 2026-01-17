const fs = require('fs');
const path = require('path');

const outputDir = path.join(__dirname, 'public', 'data', 'csv');
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

// Helpers
const randomDate = (start, end) => new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
const toCSV = (data) => {
    if (data.length === 0) return '';
    const headers = Object.keys(data[0]);
    const rows = data.map(obj => headers.map(h => {
        let val = obj[h];
        if (typeof val === 'string' && val.includes(',')) return `"${val}"`;
        return val;
    }).join(','));
    return [headers.join(','), ...rows].join('\n');
};

// 1. dim_doctors.csv
const doctors = [
    { doctor_key: 'd1', name: 'Dr. Kovács János', specialty: 'Fogászat', hourly_rate: 15000, commission_rate: 0.3 },
    { doctor_key: 'd2', name: 'Dr. Nagy Emese', specialty: 'Esztétika', hourly_rate: 20000, commission_rate: 0.35 },
    { doctor_key: 'd3', name: 'Dr. Szabó Péter', specialty: 'Radiológia', hourly_rate: 12000, commission_rate: 0.25 },
    { doctor_key: 'd4', name: 'Dr. Kiss László', specialty: 'Ortopédia', hourly_rate: 18000, commission_rate: 0.3 },
];
fs.writeFileSync(path.join(outputDir, 'dim_doctors.csv'), toCSV(doctors));

// 2. dim_treatments.csv
const treatments = [
    { treatment_key: 't1', category: 'Fogászat', name: 'Fogkő-eltávolítás', price: 15000, material_cost: 2000 },
    { treatment_key: 't2', category: 'Fogászat', name: 'Tömés', price: 25000, material_cost: 5000 },
    { treatment_key: 't3', category: 'Esztétika', name: 'Botox kezelés', price: 85000, material_cost: 35000 },
    { treatment_key: 't4', category: 'Radiológia', name: 'MRI vizsgálat', price: 55000, material_cost: 15000 },
    { treatment_key: 't5', category: 'Ortopédia', name: 'Szakorvosi konzultáció', price: 22000, material_cost: 500 },
];
fs.writeFileSync(path.join(outputDir, 'dim_treatments.csv'), toCSV(treatments));

// 3. dim_channels.csv
const channels = [
    { channel_key: 'c1', channel_name: 'Facebook Ads' },
    { channel_key: 'c2', channel_name: 'Google Search' },
    { channel_key: 'c3', channel_name: 'SEO' },
    { channel_key: 'c4', channel_name: 'Referral' },
    { channel_key: 'c5', channel_name: 'Walk-in' },
];
fs.writeFileSync(path.join(outputDir, 'dim_channels.csv'), toCSV(channels));

// 4. dim_patients.csv
const patients = [];
for (let i = 1; i <= 500; i++) {
    patients.push({
        patient_key: `p${i}`,
        age: Math.floor(Math.random() * 60) + 18,
        gender: Math.random() > 0.5 ? 'F' : 'M',
        source_key: `c${Math.floor(Math.random() * 5) + 1}`,
        first_visit_date: randomDate(new Date(2025, 0, 1), new Date(2025, 11, 31)).toISOString().split('T')[0]
    });
}
fs.writeFileSync(path.join(outputDir, 'dim_patients.csv'), toCSV(patients));

// 5. dim_dates.csv (Time dimension)
const dateDim = [];
let curr = new Date(2025, 0, 1);
const end = new Date(2025, 11, 31);
while (curr <= end) {
    const dStr = curr.toISOString().split('T')[0];
    dateDim.push({
        date_key: dStr.replace(/-/g, ''),
        full_date: dStr,
        day: curr.getDate(),
        month: curr.getMonth() + 1,
        year: curr.getFullYear(),
        quarter: Math.floor(curr.getMonth() / 3) + 1,
        is_weekend: curr.getDay() === 0 || curr.getDay() === 6 ? 1 : 0
    });
    curr.setDate(curr.getDate() + 1);
}
fs.writeFileSync(path.join(outputDir, 'dim_dates.csv'), toCSV(dateDim));

// 6. fact_appointments.csv
const factAppointments = [];
for (let i = 1; i <= 2000; i++) {
    const date = randomDate(new Date(2025, 0, 1), new Date(2025, 11, 31));
    const dateKey = date.toISOString().split('T')[0].replace(/-/g, '');
    const doctor = doctors[Math.floor(Math.random() * doctors.length)];
    const treatment = treatments[Math.floor(Math.random() * treatments.length)];
    const patient = patients[Math.floor(Math.random() * patients.length)];
    const showed = Math.random() > 0.15 ? 1 : 0;

    factAppointments.push({
        transaction_id: `T${i}`,
        date_key: dateKey,
        patient_key: patient.patient_key,
        doctor_key: doctor.doctor_key,
        treatment_key: treatment.treatment_key,
        revenue: showed ? treatment.price : 0,
        cost: showed ? (treatment.material_cost + (treatment.price * doctor.commission_rate)) : 0,
        margin: showed ? (treatment.price - (treatment.material_cost + (treatment.price * doctor.commission_rate))) : 0,
        wait_time_minutes: showed ? Math.floor(Math.random() * 30) : 0,
        showed: showed
    });
}
fs.writeFileSync(path.join(outputDir, 'fact_appointments.csv'), toCSV(factAppointments));

console.log('OLAP CSV Data generated successfully in public/data/csv/');
