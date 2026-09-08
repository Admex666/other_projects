const { createClient } = require('@supabase/supabase-js');

module.exports = async (req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    const { serial } = req.query;
    if (!serial) {
        return res.status(400).json({ error: 'Hiányzó sorszám paraméter (serial).' });
    }

    try {
        const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

        // Normalize serial (e.g. ensure '#' prefix if user entered without)
        const cleanSerial = serial.trim();
        const searchSerial = cleanSerial.startsWith('#') ? cleanSerial : `#${cleanSerial}`;

        const { data: run, error } = await supabase
            .from('runs')
            .select(`
                id,
                name,
                serial_number,
                distance_km,
                completion_date,
                received_date,
                campaign,
                completed,
                runners (
                    name
                )
            `)
            .ilike('serial_number', searchSerial)
            .maybeSingle();

        if (error) {
            console.error('[oklevel-data] Supabase error:', error);
            return res.status(500).json({ error: 'Adatbázis hiba' });
        }

        if (!run) {
            return res.status(404).json({ error: 'Nem található futás ezzel a sorszámmal.' });
        }

function formatDistanceLabel(distanceKm, campaign) {
    if (distanceKm == null || distanceKm === '') return '';
    const isPilis = String(campaign || '').toLowerCase().includes('pilis') || 
                    String(campaign || '').toLowerCase().includes('kevely');
    const num = typeof distanceKm === 'number' ? distanceKm : parseFloat(distanceKm);
    if (isNaN(num)) return String(distanceKm);

    if (isPilis) {
        if (num <= 6) return `Családi (${num} km)`;
        if (num >= 9 && num <= 11) return `Klasszikus (${num} km)`;
        if (num >= 12 && num <= 15) return `Extra (${num} km)`;
        if (num >= 20) return `Félmaraton (${num} km)`;
        return `Kevély (${num} km)`;
    } else {
        if (num <= 11) return `Klasszikus (${num} km)`;
        if (num >= 14 && num <= 16) return `Félmaraton (${num} km)`;
        if (num >= 19 && num <= 21) return `Hosszú (${num} km)`;
        if (num >= 24) return `Ultra (${num} km)`;
        return `Prédikáló (${num} km)`;
    }
}

        const runnerName = run.name || run.runners?.name || 'Futó Partner';
        const formattedDate = run.completion_date || run.received_date || null;
        const distanceLabel = formatDistanceLabel(run.distance_km, run.campaign);

        return res.status(200).json({
            success: true,
            serial: run.serial_number,
            name: runnerName,
            distance_km: run.distance_km,
            distance_label: distanceLabel,
            completion_date: formattedDate,
            campaign: run.campaign,
            completed: run.completed
        });
    } catch (err) {
        console.error('[oklevel-data] Unexpected error:', err);
        return res.status(500).json({ error: 'Szerverhiba' });
    }
};
