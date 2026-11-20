const { getTrails, planTripFromLocation } = require('../lib/companion-service');
const { getLiveRoutes } = require('../lib/menetrendek-client');

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();

    const action = req.query?.action || req.body?.action || 'plan';

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

        if (action === 'live_transit' || action === 'menetrendek') {
            const fromText = req.body?.from || req.query.from || 'Pomáz';
            const toText = req.body?.to || req.query.to || 'Pilisborosjenő';
            const dateStr = req.body?.date || req.query.date || new Date().toISOString().split('T')[0];
            const timeStr = req.body?.time || req.query.time || '08:00';

            const result = await getLiveRoutes(fromText, toText, dateStr, timeStr);
            return res.status(200).json({ success: true, ...result });
        }

        if (action === 'water_sources' || action === 'pois') {
            const south = parseFloat(req.query?.south || req.body?.south);
            const west = parseFloat(req.query?.west || req.body?.west);
            const north = parseFloat(req.query?.north || req.body?.north);
            const east = parseFloat(req.query?.east || req.body?.east);

            if (isNaN(south) || isNaN(west) || isNaN(north) || isNaN(east)) {
                return res.status(400).json({ success: false, error: 'Hiányzó koordináta határok (south, west, north, east)' });
            }

            // Bbox méretkorlát (max 0.5 fok (~40km)), hogy gyors maradjon
            const latDiff = Math.abs(north - south);
            const lonDiff = Math.abs(east - west);
            if (latDiff > 0.6 || lonDiff > 0.8) {
                return res.status(400).json({ success: false, error: 'A térképnézet túl nagy, nagyíts közelebb a forrásokhoz!' });
            }

            const overpassQuery = `[out:json][timeout:15];(node["amenity"="drinking_water"](${south},${west},${north},${east});node["natural"="spring"](${south},${west},${north},${east});node["man_made"="water_tap"](${south},${west},${north},${east}););out center 80;`;

            // Overpass tükörszerverek listája redundanciához
            const mirrors = [
                'https://overpass-api.de/api/interpreter',
                'https://overpass.kumi.systems/api/interpreter',
                'https://maps.mail.ru/osm/tools/overpass/api/interpreter'
            ];

            let overpassData = null;
            for (const mirror of mirrors) {
                try {
                    const fetchRes = await fetch(`${mirror}?data=${encodeURIComponent(overpassQuery)}`, {
                        headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) VitaStepsCompanion/1.0' }
                    });
                    if (fetchRes.ok) {
                        overpassData = await fetchRes.json();
                        if (overpassData && overpassData.elements) break;
                    }
                } catch (e) {
                    // Try next mirror
                }
            }

            if (!overpassData || !overpassData.elements) {
                return res.status(200).json({ success: true, elements: [], note: 'Overpass API ideiglenesen nem elérhető' });
            }
            const elements = (overpassData.elements || []).map(el => {
                const tags = el.tags || {};
                const isSpring = tags.natural === 'spring';
                const isDrinkingWater = tags.amenity === 'drinking_water' || tags.drinking_water === 'yes';
                
                let typeName = isSpring ? 'Természetes forrás' : 'Közkút / Ivóvízvételi hely';
                let name = tags.name || (isSpring ? 'Névtelen erdei forrás' : 'Közkút');
                let desc = isDrinkingWater ? 'Ivóvíz elérhető' : (tags.drinking_water === 'no' ? 'Nem bevizsgált / Nem ivóvíz' : 'Természetes víz');

                return {
                    id: el.id,
                    lat: el.lat,
                    lon: el.lon,
                    name,
                    typeName,
                    desc,
                    isSpring,
                    isDrinkingWater,
                    icon: isSpring ? 'ph-tree' : 'ph-drop',
                    color: isDrinkingWater ? '#38bdf8' : '#94a3b8'
                };
            });

            return res.status(200).json({ success: true, count: elements.length, elements });
        }

        const params = {
            homeLat: parseFloat(req.body?.homeLat || req.query?.homeLat || 47.4979),
            homeLon: parseFloat(req.body?.homeLon || req.query?.homeLon || 19.0402),
            homeAddress: req.body?.homeAddress || req.query?.homeAddress || 'Budapest belváros',
            trailId: req.body?.trailId || req.query?.trailId || 'kevely_klasszik',
            customTrail: req.body?.customTrail || null, // Egyénileg tervezett vagy GPX-ből feltöltött túra
            homeDeparture: req.body?.homeDeparture || req.query?.homeDeparture || '08:00',
            paceKmh: parseFloat(req.body?.paceKmh || req.query?.paceKmh || 4.0),
            breaksCount: parseInt(req.body?.breaksCount || req.query?.breaksCount || 2, 10),
            breakDurationMin: parseInt(req.body?.breakDurationMin || req.query?.breakDurationMin || 15, 10),
            useLiveTransit: req.body?.useLiveTransit === true || req.query?.useLiveTransit === 'true',
            date: req.body?.date || req.query?.date
        };

        const result = await planTripFromLocation(params);
        return res.status(200).json({ success: true, plan: result });
    } catch (err) {
        console.error('Companion API error:', err);
        return res.status(500).json({ success: false, error: err.message });
    }
};
