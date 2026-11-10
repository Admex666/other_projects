const { getTrails, planTripFromLocation } = require('../lib/companion-service');

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();

    const action = req.query.action || req.body?.action || 'plan';

    try {
        if (action === 'trails') {
            const trails = getTrails().map(t => ({
                id: t.id,
                name: t.name,
                distance_km: t.distance_km,
                elevation_gain_m: t.elevation_gain_m,
                energy_km: t.energy_km,
                transit_line: t.transit_line,
                transit_hub: t.transit_hub,
                start_stop: t.start_stop
            }));
            return res.status(200).json({ success: true, trails });
        }

        const params = {
            homeLat: parseFloat(req.body?.homeLat || req.query.homeLat || 47.4979),
            homeLon: parseFloat(req.body?.homeLon || req.query.homeLon || 19.0402),
            homeAddress: req.body?.homeAddress || req.query.homeAddress || 'Budapest belváros',
            trailId: req.body?.trailId || req.query.trailId || 'kevely_klasszik',
            homeDeparture: req.body?.homeDeparture || req.query.homeDeparture || '08:00',
            paceKmh: parseFloat(req.body?.paceKmh || req.query.paceKmh || 4.0),
            breaksCount: parseInt(req.body?.breaksCount || req.query.breaksCount || 2, 10),
            breakDurationMin: parseInt(req.body?.breakDurationMin || req.query.breakDurationMin || 15, 10)
        };

        const result = planTripFromLocation(params);
        return res.status(200).json({ success: true, plan: result });
    } catch (err) {
        console.error('Companion API error:', err);
        return res.status(500).json({ success: false, error: err.message });
    }
};
