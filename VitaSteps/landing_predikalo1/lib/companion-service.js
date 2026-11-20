const fs = require('fs');
const path = require('path');
const https = require('https');
const { getLiveRoutes, searchStation } = require('./menetrendek-client');

const COMPANION_DIR = path.resolve(__dirname, '../companion');

function getTrails() {
    try {
        const p = path.join(COMPANION_DIR, 'trails.json');
        if (fs.existsSync(p)) {
            return JSON.parse(fs.readFileSync(p, 'utf8'));
        }
    } catch (e) {
        console.error('Error reading trails.json:', e);
    }
    return [];
}

function parseTimeToMinutes(tStr) {
    if (!tStr) return 0;
    const parts = tStr.split(':');
    return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
}

function minutesToTimeStr(mins) {
    mins = Math.round(mins) % (24 * 60);
    if (mins < 0) mins += 24 * 60;
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
}

/**
 * Helyi kötöttpályás ráhordó vonalak (pl. 59-es villamos Farkasrétről)
 * Amikor a lakóhely közvetlen közelében nincs országos Volán/MÁV megálló, de van helyi villamos
 */
const LOCAL_FEEDER_LINES = [
    {
        name: 'Farkasréti temető',
        lat: 47.4843,
        lon: 19.0019,
        lineName: '59-es villamos',
        badgeType: 'VILLAMOS',
        badgeColor: '#eab308',
        hubTarget: 'Budapest-Déli pu.',
        hubCoord: [47.500, 19.025],
        durationMin: 12
    },
    {
        name: 'Márton Áron tér',
        lat: 47.4812,
        lon: 18.9982,
        lineName: '59-es villamos',
        badgeType: 'VILLAMOS',
        badgeColor: '#eab308',
        hubTarget: 'Budapest-Déli pu.',
        hubCoord: [47.500, 19.025],
        durationMin: 15
    },
    {
        name: 'Süveg utca',
        lat: 47.4868,
        lon: 19.0062,
        lineName: '59-es villamos',
        badgeType: 'VILLAMOS',
        badgeColor: '#eab308',
        hubTarget: 'Budapest-Déli pu.',
        hubCoord: [47.500, 19.025],
        durationMin: 10
    },
    {
        name: 'Apor Vilmos tér',
        lat: 47.4912,
        lon: 19.0135,
        lineName: '59-es villamos / 105-ös busz',
        badgeType: 'VILLAMOS',
        badgeColor: '#eab308',
        hubTarget: 'Budapest-Déli pu.',
        hubCoord: [47.500, 19.025],
        durationMin: 8
    }
];

function findNearbyLocalFeeder(lat, lon, maxDistanceKm = 1.0) {
    if (!lat || !lon) return null;
    const cosLat = Math.cos((lat * Math.PI) / 180);
    let best = null;
    let minDist = Infinity;
    for (const f of LOCAL_FEEDER_LINES) {
        const d = Math.hypot((f.lat - lat) * 111, (f.lon - lon) * 111 * cosLat);
        if (d < minDist) {
            minDist = d;
            best = f;
        }
    }
    if (minDist <= maxDistanceKm && best) {
        return { ...best, distKm: parseFloat(minDist.toFixed(2)) };
    }
    return null;
}
const TRANSIT_HUBS = [
    // Észak-Buda és Óbuda
    { name: 'Budapest, Bécsi út / Vörösvári út', lat: 47.545, lon: 19.027 },
    { name: 'Budapest, Flórián tér', lat: 47.540, lon: 19.040 },
    { name: 'Budapest, Szentlélek tér', lat: 47.537, lon: 19.043 },
    { name: 'Budapest, Batthyány tér', lat: 47.506, lon: 19.039 },
    { name: 'Budapest, Széll Kálmán tér (Várfok utca)', lat: 47.508, lon: 19.025 },

    // Közép- és Dél-Buda (Farkasrét, Gazdagrét, Újbuda, Kelenföld)
    { name: 'Budapest, BAH-csomópont', lat: 47.490, lon: 19.023 },
    { name: 'Budapest, Csörsz utca', lat: 47.491, lon: 19.023 },
    { name: 'Budapest, Budaörsi út / Villányi út', lat: 47.481, lon: 19.029 },
    { name: 'Budapest, Sasadi út', lat: 47.469, lon: 19.013 },
    { name: 'Budapest-Déli pu.', lat: 47.500, lon: 19.025 },
    { name: 'Budapest, Móricz Zsigmond körtér', lat: 47.474, lon: 19.046 },
    { name: 'Budapest, Kosztolányi Dezső tér', lat: 47.476, lon: 19.042 },
    { name: 'Kelenföld vá.', lat: 47.464, lon: 19.022 },

    // Észak-Pest
    { name: 'Budapest, Újpest-Központ', lat: 47.560, lon: 19.090 },
    { name: 'Rákospalota-Újpest vá.', lat: 47.562, lon: 19.106 },
    { name: 'Budapest (Rákospalota), Hubay Jenő tér', lat: 47.558, lon: 19.123 },
    { name: 'Budapest, Árpád híd autóbusz-állomás', lat: 47.534, lon: 19.068 },

    // Kelet- és Dél-Pest
    { name: 'Zugló vmh.', lat: 47.514, lon: 19.099 },
    { name: 'Budapest-Nyugati pu.', lat: 47.510, lon: 19.057 },
    { name: 'Budapest-Keleti pu.', lat: 47.500, lon: 19.083 },
    { name: 'Budapest, Örs vezér tere (Kőbánya)', lat: 47.503, lon: 19.136 },
    { name: 'Budapest, Stadion autóbusz-pályaudvar', lat: 47.501, lon: 19.102 },
    { name: 'Budapest, Kőbánya alsó vasútállomás', lat: 47.487, lon: 19.128 },
    { name: 'Boráros tér vá.', lat: 47.476, lon: 19.067 },
    { name: 'Kőbánya-Kispest vá.', lat: 47.464, lon: 19.149 },
    { name: 'Budapest (Csepel), Szent Imre tér HÉV-állomás', lat: 47.427, lon: 19.068 }
];

/**
 * Megkeresi a lakóhelyhez légvonalban legközelebbi fő csomópontokat (valós geodéziai távolsággal)
 */
function getNearestTransitHubs(lat, lon, topN = 4) {
    if (!lat || !lon) return ['Budapest-Nyugati pu.'];
    const cosLat = Math.cos((lat * Math.PI) / 180);
    const sorted = [...TRANSIT_HUBS].sort((a, b) => {
        const da = Math.hypot((a.lat - lat) * 111, (a.lon - lon) * 111 * cosLat);
        const db = Math.hypot((b.lat - lat) * 111, (b.lon - lon) * 111 * cosLat);
        return da - db;
    });
    return sorted.slice(0, topN).map(h => h.name);
}

function getNearestTransitHub(lat, lon) {
    return getNearestTransitHubs(lat, lon, 1)[0];
}

/**
 * Ismert Pest vármegyei / Pilisi települések a rajtkoordinátákhoz
 */
/**
 * Ismert Pest vármegyei / Pilisi települések és túra-kapu megállók a rajtkoordinátákhoz
 */
const PILIS_TOWNS = [
    // Szentendre helyi és külső hegyi megállói
    { name: 'Dömörkapu, autóbusz-forduló', lat: 47.695, lon: 19.000 },
    { name: 'Szentendre, lajosforrási elágazás', lat: 47.693, lon: 19.018 },
    { name: 'Szentendre, Skanzen', lat: 47.694, lon: 19.048 },
    { name: 'Szentendre, izbégi elágazás', lat: 47.672, lon: 19.073 },
    { name: 'Szentendre, Kálvária tér', lat: 47.667, lon: 19.067 },
    { name: 'Szentendre, Barackvirág utca', lat: 47.691, lon: 19.087 },
    { name: 'Szentendre, pismányi üzletsor', lat: 47.685, lon: 19.085 },
    { name: 'Szentendre vá.', lat: 47.669, lon: 19.076 },

    // Dömös és Dunakanyar
    { name: 'Dömös', lat: 47.765, lon: 18.910 },
    { name: 'Visegrád', lat: 47.785, lon: 18.975 },
    { name: 'Esztergom', lat: 47.785, lon: 18.740 },

    // Magas-Pilis
    { name: 'Dobogókő', lat: 47.718, lon: 18.900 },
    { name: 'Pilisszentkereszt', lat: 47.693, lon: 18.905 },
    { name: 'Pilisszentlászló', lat: 47.715, lon: 19.005 },

    // Kevélyek és Pilis-medence
    { name: 'Pomáz vá.', lat: 47.643, lon: 19.032 },
    { name: 'Csobánka', lat: 47.645, lon: 18.965 },
    { name: 'Pilisborosjenő', lat: 47.609, lon: 18.990 },
    { name: 'Solymár vmh.', lat: 47.590, lon: 18.930 },
    { name: 'Nagykovácsi', lat: 47.575, lon: 18.885 },
    { name: 'Pilisvörösvár vá.', lat: 47.618, lon: 18.910 },
    { name: 'Piliscsaba', lat: 47.625, lon: 18.825 }
];

function findNearestTown(lat, lon) {
    if (!lat || !lon) return 'Pilisborosjenő';
    let best = PILIS_TOWNS[0];
    let minDist = Infinity;
    for (const t of PILIS_TOWNS) {
        const d = Math.hypot(t.lat - lat, t.lon - lon);
        if (d < minDist) {
            minDist = d;
            best = t;
        }
    }
    return best.name;
}

function findNearestTrailheadStop(lat, lon) {
    if (!lat || !lon) return { name: 'Pilisborosjenő', lat: 47.609, lon: 18.990, distKm: 0 };
    let best = PILIS_TOWNS[0];
    let minDist = Infinity;
    for (const t of PILIS_TOWNS) {
        const d = Math.hypot(t.lat - lat, t.lon - lon);
        if (d < minDist) {
            minDist = d;
            best = t;
        }
    }
    const distKm = parseFloat((minDist * 111).toFixed(2));
    return { name: best.name, lat: best.lat, lon: best.lon, distKm };
}

/**
 * Ismert megállók és vasútállomások koordináta szótára térképes kirajzoláshoz
 */
const KNOWN_STATION_COORDS = {
    'Rákospalota-Újpest': [47.562, 19.106],
    'Újpest-Központ': [47.560, 19.090],
    'Újpest-központ': [47.560, 19.090],
    'Újpest-Városkapu': [47.558, 19.083],
    'Hubay Jenő tér': [47.558, 19.123],
    'Nyugati': [47.510, 19.057],
    'Keleti': [47.500, 19.083],
    'Déli': [47.500, 19.025],
    'Kelenföld': [47.464, 19.022],
    'Kőbánya-Kispest': [47.464, 19.149],
    'Árpád híd': [47.534, 19.068],
    'Göncz Árpád': [47.534, 19.068],
    'Flórián tér': [47.540, 19.040],
    'Szentlélek tér': [47.537, 19.043],
    'Margit híd': [47.515, 19.039],
    'Batthyány tér': [47.506, 19.039],
    'Széll Kálmán tér': [47.508, 19.025],
    'Deák Ferenc tér': [47.498, 19.053],
    'Bécsi út': [47.545, 19.027],
    'Vörösvári út': [47.545, 19.027],
    'Zugló': [47.514, 19.099],
    'Stadion': [47.501, 19.102],
    'Boráros tér': [47.476, 19.067],
    'Móricz Zsigmond': [47.474, 19.046],
    // Buda és egyéb csomópontok
    'BAH-csomópont': [47.490, 19.023],
    'Csörsz utca': [47.491, 19.023],
    'Sasadi út': [47.469, 19.013],
    'Villányi út': [47.481, 19.029],
    'Kosztolányi': [47.476, 19.042],

    // Szentendre helyi megállók
    'Dömörkapu': [47.695, 19.000],
    'lajosforrás': [47.693, 19.018],
    'Lajosforrás': [47.693, 19.018],
    'Skanzen': [47.694, 19.048],
    'izbégi': [47.672, 19.073],
    'Kálvária tér': [47.667, 19.067],
    'Barackvirág': [47.691, 19.087],
    'pismány': [47.685, 19.085],
    'Pilisborosjenő': [47.609, 18.990],
    'Pomáz': [47.643, 19.032],
    'Szentendre': [47.669, 19.076],
    'Dömös': [47.765, 18.910],
    'Visegrád': [47.785, 18.975],
    'Pilisszentkereszt': [47.693, 18.905],
    'Dobogókő': [47.718, 18.900],
    'Solymár': [47.590, 18.930],
    'Pilisvörösvár': [47.618, 18.910],
    'Piliscsaba': [47.625, 18.825]
};

function resolveStopCoordinate(stopName, fallbackLat, fallbackLon) {
    if (!stopName) return [fallbackLat, fallbackLon];
    const sLower = stopName.toLowerCase();
    for (const [key, coord] of Object.entries(KNOWN_STATION_COORDS)) {
        if (sLower.includes(key.toLowerCase())) {
            return coord;
        }
    }
    return [fallbackLat, fallbackLon];
}

/**
 * Dinamikus megálló-koordináta feloldás Photon API-val
 */
async function geocodeStopName(stopName, latHint = 47.5, lonHint = 19.1) {
    if (!stopName) return null;
    let url = 'https://photon.komoot.io/api/?q=' + encodeURIComponent(stopName) + '&limit=1';
    if (latHint && lonHint) {
        url += `&lat=${latHint}&lon=${lonHint}`;
    }
    return new Promise(r => {
        const req = https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try {
                    const j = JSON.parse(d);
                    if (j.features && j.features[0]) {
                        const [lon, lat] = j.features[0].geometry.coordinates;
                        // Csak akkor fogadjuk el, ha Magyarországon (vagy Pest térségében) van!
                        if (lat >= 45.5 && lat <= 48.8 && lon >= 16.0 && lon <= 23.0) {
                            r([lat, lon]);
                            return;
                        }
                    }
                } catch(e) {}
                r(null);
            });
        });
        req.on('error', () => r(null));
        req.setTimeout(2500, () => { req.destroy(); r(null); });
    });
}

/**
 * Automatikusan feloldja a lakóhelyhez legközelebbi valós BKK / helyi megállót
 * 1. Nominatim bus_stop keresés a pontos koordináta körzetében
 * 2. Photon Reverse Geocoding fallback
 * 3. Menetrendek.hu állomás feloldása
 */
async function resolveDirectNearbyStop(lat, lon, rawAddress) {
    if (!lat || !lon) return null;
    const candidates = [];

    // 1. Nominatim megállókeresés a lakóhely körül (0.015 fokos körzet ~1.2 km)
    try {
        const delta = 0.015;
        const viewbox = (lon - delta) + ',' + (lat + delta) + ',' + (lon + delta) + ',' + (lat - delta);
        const url = 'https://nominatim.openstreetmap.org/search?format=json&q=bus_stop&bounded=1&viewbox=' + viewbox;
        const nomData = await new Promise((resolve) => {
            const req = https.get(url, { headers: { 'User-Agent': 'VitaSteps-App/1.0' } }, (res) => {
                let d = '';
                res.on('data', c => d += c);
                res.on('end', () => {
                    try { resolve(JSON.parse(d)); } catch(e) { resolve([]); }
                });
            });
            req.on('error', () => resolve([]));
            req.setTimeout(2500, () => { req.destroy(); resolve([]); });
        });

        if (Array.isArray(nomData) && nomData.length > 0) {
            const sortedStops = nomData.map(e => {
                const sLat = parseFloat(e.lat), sLon = parseFloat(e.lon);
                const dist = Math.hypot((sLat - lat) * 111, (sLon - lon) * 75);
                const cleanName = (e.display_name || '').split(',')[0].trim();
                return { name: cleanName, lat: sLat, lon: sLon, distKm: dist };
            }).sort((a, b) => a.distKm - b.distKm);

            for (const s of sortedStops.slice(0, 5)) {
                candidates.push({ query: 'Budapest, ' + s.name, coord: [s.lat, s.lon] });
                candidates.push({ query: s.name, coord: [s.lat, s.lon] });
            }
        }
    } catch (e) {}

    // 2. Photon Reverse Geocoding fallback
    try {
        const url = 'https://photon.komoot.io/reverse?lon=' + lon + '&lat=' + lat;
        const photonData = await new Promise((resolve) => {
            const req = https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (res) => {
                let d = '';
                res.on('data', c => d += c);
                res.on('end', () => {
                    try { resolve(JSON.parse(d)); } catch(e) { resolve(null); }
                });
            });
            req.on('error', () => resolve(null));
            req.setTimeout(2000, () => { req.destroy(); resolve(null); });
        });

        if (photonData && photonData.features && photonData.features[0]) {
            const p = photonData.features[0].properties;
            if (p.street) {
                candidates.push({ query: 'Budapest, ' + p.street, coord: [lat, lon] });
                candidates.push({ query: p.street, coord: [lat, lon] });
            }
            if (p.name && p.name !== p.street) {
                candidates.push({ query: 'Budapest, ' + p.name, coord: [lat, lon] });
                candidates.push({ query: p.name, coord: [lat, lon] });
            }
        }
    } catch (e) {}

    if (rawAddress) {
        const clean = rawAddress.replace(/\s+\d+[\/\w\.-]*.*$/, '').trim();
        candidates.push({ query: clean, coord: [lat, lon] });
        if (!clean.toLowerCase().includes('budapest')) candidates.push({ query: 'Budapest, ' + clean, coord: [lat, lon] });
    }

    for (const c of candidates) {
        try {
            const st = await searchStation(c.query);
            if (st && st.lsname) {
                let stopCoord = c.coord;
                if (!stopCoord || (stopCoord[0] === lat && stopCoord[1] === lon)) {
                    stopCoord = await geocodeStopName(st.lsname, lat, lon);
                    if (!stopCoord && st.geomEov && st.geomEov.coordinates) {
                        const [eovX, eovY] = st.geomEov.coordinates;
                        stopCoord = [47.143 + ((eovY - 200000) / 111180), 19.048 + ((eovX - 650000) / 75500)];
                    }
                }
                return {
                    name: st.lsname,
                    coord: stopCoord || [lat, lon],
                    queryName: c.query
                };
            }
        } catch(e) {}
    }
    return null;
}

/**
 * Intelligens címjelöltek felépítése a Menetrendek.hu hivatalos megálló-adatbázisához
 */
function buildAddressCandidates(rawAddress, homeLat, homeLon) {
    const list = [];
    const nearestHubs = getNearestTransitHubs(homeLat, homeLon, 4);

    if (!rawAddress) {
        return nearestHubs;
    }
    const clean = rawAddress.trim();
    // Budapesten belül vagyunk koordináta alapján is? (47.35 - 47.62 és 18.90 - 19.33)
    const isBudapestCoord = homeLat >= 47.35 && homeLat <= 47.62 && homeLon >= 18.90 && homeLon <= 19.33;
    const isBudapest = clean.toLowerCase().includes('budapest') || isBudapestCoord;

    if (isBudapest) {
        // Ha budapesti címről van szó
        const parts = clean.split(',').map(p => p.trim());
        const nonBp = parts.filter(p => !p.toLowerCase().includes('budapest'));
        if (nonBp.length > 0) {
            const streetClean = nonBp[0].replace(/\s+\d+[\/\w\.-]*.*$/, '').trim();
            if (streetClean) {
                list.push('Budapest, ' + streetClean);
                list.push(streetClean);
            }
        }
        // A lakóhelyhez legközelebbi valós csomópontokat tesszük be prioritásként (pl. BKK busz, villamos, vonat)
        nearestHubs.forEach(h => list.push(h));
        list.push('Budapest, Deák Ferenc tér');
        list.push('Budapest');
    } else {
        // Vidéki cím esetén
        if (clean.includes(',')) {
            const parts = clean.split(',').map(p => p.trim());
            const townCandidate = parts.find(p => !p.match(/\b(utca|út|tér|sor|fasor|köz|krt|körút|dűlő)\b/i));
            if (townCandidate) list.push(townCandidate);
        }
        list.push(clean.replace(/\s+\d+[\/\w\.-]*.*$/, '').trim());
        list.push(clean);
        nearestHubs.forEach(h => list.push(h));
    }
    return [...new Set(list.filter(Boolean))];
}

/**
 * Kiválasztja a túra befejezéséhez legközelebbi, életszerű indulású járatot
 */
function findBestUpcomingRoute(routes, minDepartureTimeStr) {
    if (!routes || !routes.length) return null;
    const minMins = parseTimeToMinutes(minDepartureTimeStr);

    // Kiszűrjük azokat a járatokat, amelyek a túra vége után indulnak (max 3-4 órán belül)
    const upcoming = routes.filter(r => {
        const depMins = parseTimeToMinutes(r.departureTime);
        return depMins >= minMins && (depMins - minMins) < 240;
    });

    if (upcoming.length > 0) {
        upcoming.sort((a, b) => parseTimeToMinutes(a.departureTime) - parseTimeToMinutes(b.departureTime));
        return upcoming[0];
    }
    return null;
}

const TRAILHEADS = {
    kevely: {
        id: 'kevely',
        name: 'Pilisborosjenő, autóbusz-forduló',
        search_query: 'Pilisborosjenő',
        lat: 47.6091,
        lon: 18.9897
    },
    predikalo: {
        id: 'predikalo',
        name: 'Pomáz vá.',
        search_query: 'Pomáz',
        lat: 47.6426,
        lon: 19.0315
    }
};

/**
 * Plan door-to-door trip using LIVE Menetrendek.hu multi-modal transit
 */
async function planTripFromLocation({
    homeLat = 47.4979,
    homeLon = 19.0402,
    homeAddress = 'Budapest, Deák Ferenc tér',
    trailId = 'kevely_klasszik',
    customTrail = null,
    homeDeparture = '08:00',
    paceKmh = 4.0,
    breaksCount = 2,
    breakDurationMin = 15,
    useLiveTransit = true,
    date = null
}) {
    const trails = getTrails();
    let trail = customTrail;
    if (!trail) {
        trail = trails.find(t => t.id === trailId) || trails[0];
    }
    if (!trail) throw new Error('Trail not found');

    // Ha egyéni túráról van szó, a rajt koordinátákból határozzuk meg a célállomást
    let trailhead;
    if (customTrail) {
        const startCoord = (customTrail.coordinates && customTrail.coordinates[0]) || [47.6091, 18.9897];
        const townName = findNearestTown(startCoord[0], startCoord[1]);
        const customName = customTrail.name || 'Egyéni túra rajtja';
        trailhead = {
            id: 'custom_trailhead',
            name: `${customName} (${townName})`,
            search_query: townName,
            lat: startCoord[0],
            lon: startCoord[1]
        };
    } else {
        const isKevely = trail.id.includes('kevely');
        trailhead = isKevely ? TRAILHEADS.kevely : TRAILHEADS.predikalo;
    }
    const travelDate = date || new Date().toISOString().split('T')[0];

    // Intelligens kiindulási címjelöltek összeállítása
    let originCandidates = buildAddressCandidates(homeAddress, homeLat, homeLon);

    // 0. DINAMIKUS HELYI MEGÁLLÓ FELOLDÁSA (Bárhol is dobja le a felhasználó a pontot)
    const directStop = await resolveDirectNearbyStop(homeLat, homeLon, homeAddress);
    let directStopWalkLeg = null;

    if (directStop) {
        originCandidates = [directStop.name, ...originCandidates];
        if (directStop.coord) {
            KNOWN_STATION_COORDS[directStop.name] = directStop.coord;
            const dLat = (directStop.coord[0] - homeLat) * 111;
            const dLon = (directStop.coord[1] - homeLon) * 111 * Math.cos(homeLat * Math.PI / 180);
            const distToStopKm = parseFloat(Math.hypot(dLat, dLon).toFixed(2));
            if (distToStopKm >= 0.1) {
                const walkMins = Math.max(2, Math.round((distToStopKm / 4.0) * 60));
                directStopWalkLeg = {
                    stopName: directStop.name,
                    stopCoord: directStop.coord,
                    distKm: distToStopKm,
                    walkMins
                };
            }
        }
    }

    // Megvizsgáljuk, hogy közvetlenül elérhető-e helyi kötöttpályás ráhordó (pl. 59-es villamos Farkasrétről)
    const localFeeder = findNearbyLocalFeeder(homeLat, homeLon, 0.8);
    let feederOutboundLeg = null;
    let effectiveDepartureStr = homeDeparture;

    if (localFeeder) {
        // Ha van helyi villamos a lakóhelytől 800 méteren belül, azt közvetlen eljutásként kezeljük a Déli pu.-ig
        const feederWalkMins = localFeeder.distKm >= 0.15 ? Math.max(3, Math.round((localFeeder.distKm / 4.0) * 60)) : 0;
        const feederDepMins = parseTimeToMinutes(homeDeparture) + feederWalkMins;
        const feederArrMins = feederDepMins + localFeeder.durationMin;
        effectiveDepartureStr = minutesToTimeStr(feederArrMins + 5); // +5 perc átszállási idő

        // A csomóponti keresést közvetlenül a villamos célállomásától (pl. Déli pu.) indítjuk
        originCandidates = [localFeeder.hubTarget, ...originCandidates];

        feederOutboundLeg = {
            walkMins: feederWalkMins,
            feederDepMins,
            feederArrMins,
            feeder: localFeeder
        };
    } else if (directStopWalkLeg) {
        // Ha nem villamos ráhordó, de van séta a helyi BKK megállóig, a menetrendi keresést a gyaloglás után indítjuk
        effectiveDepartureStr = minutesToTimeStr(parseTimeToMinutes(homeDeparture) + directStopWalkLeg.walkMins);
    }

    // 1. ODAÚT LEKÉRDEZÉSE AZ ÉLŐ MENETRENDEKBŐL (MÁV + HÉV + Volán)
    let outboundLegs = [];
    let trailArrivalMins = parseTimeToMinutes(effectiveDepartureStr) + 40; // fallback
    let liveOutboundFound = false;
    let alternativeRoutes = [];

    // Célállomás keresési jelöltek: a legközelebbi hegyi/külterületi megálló ÉS a központi településnév
    const targetCandidates = [trailhead.search_query];
    const townFallback = findNearestTown(trailhead.lat, trailhead.lon);
    if (townFallback && !targetCandidates.includes(townFallback)) {
        targetCandidates.push(townFallback);
    }
    if (townFallback.includes('Szentendre') && !targetCandidates.includes('Szentendre vá.')) {
        targetCandidates.push('Szentendre vá.');
    }

    // Segédfüggvény: egy adott nyers útvonalból összeállítja az odaút szakaszait (legs)
    function buildOutboundLegs(rawRoute) {
        const legs = [];
        let curTrailArrivalMins = parseTimeToMinutes(rawRoute.arrivalTime);

        if (feederOutboundLeg) {
            const { walkMins, feeder } = feederOutboundLeg;
            const transitFirstDepMins = parseTimeToMinutes(rawRoute.legs[0]?.depTime || rawRoute.departureTime);
            const tramArrMins = transitFirstDepMins - 5;
            const tramDepMins = tramArrMins - feeder.durationMin;
            const walkDepMins = Math.max(parseTimeToMinutes(homeDeparture), tramDepMins - walkMins);

            if (walkMins > 0) {
                legs.push({
                    legIndex: 1,
                    legType: 'walk_to_stop',
                    badgeType: 'SÉTA',
                    badgeColor: '#0ea5e9',
                    lineName: `Séta a villamosig (~${(feeder.distKm * 1000).toFixed(0)}m)`,
                    directionText: `${feeder.name} felé`,
                    depTime: minutesToTimeStr(walkDepMins),
                    arrTime: minutesToTimeStr(tramDepMins),
                    durationMin: walkMins,
                    fromStop: homeAddress,
                    toStop: feeder.name,
                    fromCoord: [homeLat, homeLon],
                    toCoord: [feeder.lat, feeder.lon],
                    note: 'Gyalogos eljutás a járat indulásához igazítva'
                });
            }
            legs.push({
                legIndex: legs.length + 1,
                legType: 'local_feeder',
                badgeType: feeder.badgeType,
                badgeColor: feeder.badgeColor,
                lineName: feeder.lineName,
                directionText: `${feeder.hubTarget} felé`,
                depTime: minutesToTimeStr(tramDepMins),
                arrTime: minutesToTimeStr(tramArrMins),
                durationMin: feeder.durationMin,
                fromStop: feeder.name,
                toStop: feeder.hubTarget,
                fromCoord: [feeder.lat, feeder.lon],
                toCoord: feeder.hubCoord,
                note: 'Közvetlen helyi villamosjárat a csomópontig'
            });
        } else if (directStopWalkLeg && rawRoute.legs[0]?.fromStop.includes(directStopWalkLeg.stopName.split(',')[0])) {
            const transitFirstDepMins = parseTimeToMinutes(rawRoute.legs[0]?.depTime || rawRoute.departureTime);
            const walkArrMins = transitFirstDepMins - 2; // 2 perc átszállási puffer
            const walkDepMins = Math.max(parseTimeToMinutes(homeDeparture), walkArrMins - directStopWalkLeg.walkMins);

            legs.push({
                legIndex: 1,
                legType: 'walk_to_stop',
                badgeType: 'SÉTA',
                badgeColor: '#0ea5e9',
                lineName: `Séta a megállóig (~${(directStopWalkLeg.distKm * 1000).toFixed(0)}m)`,
                directionText: `${directStopWalkLeg.stopName} felé`,
                depTime: minutesToTimeStr(walkDepMins),
                arrTime: minutesToTimeStr(walkArrMins),
                durationMin: directStopWalkLeg.walkMins,
                fromStop: homeAddress,
                toStop: directStopWalkLeg.stopName,
                fromCoord: [homeLat, homeLon],
                toCoord: directStopWalkLeg.stopCoord,
                note: 'Gyalogos indulás pontosan a járat érkezéséhez hangolva'
            });
        }

        rawRoute.legs.forEach((l) => {
            const fromCoord = resolveStopCoordinate(l.fromStop, homeLat, homeLon);
            const toCoord = resolveStopCoordinate(l.toStop, trailhead.lat, trailhead.lon);
            legs.push({
                legIndex: legs.length + 1,
                legType: 'transit',
                badgeType: l.badgeType,
                badgeColor: l.badgeColor,
                lineName: l.lineName,
                directionText: `${l.toStop} felé`,
                depTime: l.depTime,
                arrTime: l.arrTime,
                durationMin: l.durationMin,
                fromStop: l.fromStop,
                toStop: l.toStop,
                fromCoord,
                toCoord,
                note: l.note || 'Menetrendek.hu élő hivatalos járat'
            });
        });

        // Séta a célállomástól a túra rajtjáig (>200m esetén)
        const lastLeg = legs[legs.length - 1];
        if (lastLeg && lastLeg.toCoord) {
            const endTransitCoord = lastLeg.toCoord;
            const dLat = (trailhead.lat - endTransitCoord[0]) * 111;
            const dLon = (trailhead.lon - endTransitCoord[1]) * 75;
            const distToTrailKm = parseFloat(Math.hypot(dLat, dLon).toFixed(2));

            if (distToTrailKm >= 0.2) {
                const walkMins = Math.max(3, Math.round((distToTrailKm / 4.0) * 60));
                const walkDepMins = curTrailArrivalMins;
                const walkArrMins = curTrailArrivalMins + walkMins;
                curTrailArrivalMins = walkArrMins;

                legs.push({
                    legIndex: legs.length + 1,
                    legType: 'walk_to_trail',
                    badgeType: 'SÉTA',
                    badgeColor: '#0ea5e9',
                    lineName: `Séta a túra rajtjáig (~${(distToTrailKm * 1000).toFixed(0)}m)`,
                    directionText: `${trail.name} rajtja felé`,
                    depTime: minutesToTimeStr(walkDepMins),
                    arrTime: minutesToTimeStr(walkArrMins),
                    durationMin: walkMins,
                    fromStop: lastLeg.toStop,
                    toStop: `${trail.name} rajtja`,
                    fromCoord: endTransitCoord,
                    toCoord: [trailhead.lat, trailhead.lon],
                    note: 'Gyalogos eljutás az állomástól a túra rajtjáig'
                });
            }
        }

        return { legs, trailArrivalMins: curTrailArrivalMins };
    }

    try {
        let bestOut = null;
        const allOutboundCandidates = [];

        for (const target of targetCandidates) {
            for (const cand of originCandidates) {
                try {
                    const res = await getLiveRoutes(cand, target, travelDate, effectiveDepartureStr);
                    if (res && res.routes && res.routes.length > 0) {
                        const minMins = parseTimeToMinutes(effectiveDepartureStr);
                        const upcoming = res.routes.filter(r => {
                            const [h, m] = r.departureTime.split(':').map(Number);
                            const mins = h * 60 + m;
                            return mins >= minMins && (mins - minMins) < 240;
                        });
                        upcoming.forEach(r => allOutboundCandidates.push(r));
                        if (allOutboundCandidates.length >= 3) break;
                    }
                } catch (e) {}
            }
            if (allOutboundCandidates.length >= 3) break;
        }

        if (allOutboundCandidates.length > 0) {
            // Egyedi útvonalak szűrése indulási és érkezési idő szerint
            const seen = new Set();
            const uniqueRoutes = [];
            for (const r of allOutboundCandidates) {
                const key = r.departureTime + '_' + r.arrivalTime;
                if (!seen.has(key)) {
                    seen.add(key);
                    uniqueRoutes.push(r);
                }
            }
            uniqueRoutes.sort((a, b) => parseTimeToMinutes(a.departureTime) - parseTimeToMinutes(b.departureTime));

            bestOut = uniqueRoutes[0];
            const primaryBuilt = buildOutboundLegs(bestOut);
            outboundLegs = primaryBuilt.legs;
            trailArrivalMins = primaryBuilt.trailArrivalMins;
            liveOutboundFound = true;

            // 3 alternatív útvonal (Google Maps jellegű választóhoz)
            alternativeRoutes = uniqueRoutes.slice(0, 3).map((r, idx) => {
                const built = buildOutboundLegs(r);
                const firstDep = built.legs[0]?.depTime || r.departureTime;
                const arrTime = minutesToTimeStr(built.trailArrivalMins);
                const durMin = built.trailArrivalMins - parseTimeToMinutes(firstDep);
                const transCount = r.transfersCount !== undefined ? r.transfersCount : (r.legs.length - 1);
                const mainLines = r.legs.map(l => ({ badgeType: l.badgeType, badgeColor: l.badgeColor, lineName: l.lineName }));

                return {
                    id: idx,
                    title: `Útvonal ${idx + 1}`,
                    departureTime: firstDep,
                    arrivalTime: arrTime,
                    durationMin: durMin,
                    durationStr: `${Math.floor(durMin / 60)}ó ${durMin % 60}p`,
                    transfersCount: transCount,
                    mainLines,
                    legs: built.legs,
                    trailArrivalMins: built.trailArrivalMins
                };
            });
        }
    } catch (err) {
        console.warn('Live outbound transit query fallback:', err.message);
    }

    // Fallback if live transit returned nothing (e.g. network offline)
    if (!liveOutboundFound) {
        outboundLegs = [{
            legIndex: 1,
            legType: 'direct_local_transit',
            badgeType: 'HELYI',
            badgeColor: '#0284c7',
            lineName: 'Helyi eljutás a túra rajtjához',
            directionText: `${trailhead.name} felé`,
            depTime: homeDeparture,
            arrTime: minutesToTimeStr(trailArrivalMins),
            durationMin: 40,
            fromStop: homeAddress,
            toStop: trailhead.name,
            fromCoord: [homeLat, homeLon],
            toCoord: [trailhead.lat, trailhead.lon],
            note: 'Becsült közvetlen utazási idő'
        }];
    }

    // 2. TÚRA SZÁMÍTÁSA (Energy KM = D + E / 95)
    const energyKm = trail.energy_km;
    const totalBreakMins = breaksCount * breakDurationMin;

    const scenarios = {};
    const scenarioConfigs = [
        { key: 'faster', factor: 1.15, name: 'Gyorsabb tempó (+15%)' },
        { key: 'normal', factor: 1.00, name: 'Tervezett normál tempó' },
        { key: 'slower', factor: 0.85, name: 'Kényelmesebb tempó (-15%)' }
    ];

    for (const sc of scenarioConfigs) {
        const effPace = paceKmh * sc.factor;
        const walkMinutes = (energyKm / effPace) * 60;
        const totalHikeMinutes = walkMinutes + totalBreakMins;
        const trailFinishMins = trailArrivalMins + totalHikeMinutes;
        const finishTimeStr = minutesToTimeStr(trailFinishMins);

        // 3. HAZAÚT LEKÉRDEZÉSE AZ ÉLŐ MENETRENDEKBŐL A TÚRA VÉGZÉSI IDEJÉTŐL
        let returnLegs = [];
        let homeArrivalMins = trailFinishMins + 45; // fallback
        let liveReturnFound = false;

        try {
            // Hazaútnál célállomás jelöltjei - a túra vége utáni legkorábbi valós járatot keressük
            let bestRet = null;
            for (const target of targetCandidates) {
                for (const cand of originCandidates) {
                    try {
                        const res = await getLiveRoutes(target, cand, travelDate, finishTimeStr);
                        if (res && res.routes && res.routes.length > 0) {
                            bestRet = findBestUpcomingRoute(res.routes, finishTimeStr);
                            if (bestRet) break;
                        }
                    } catch (e) {}
                }
                if (bestRet) break;
            }

            if (bestRet) {
                // Ha a túra vége és az első hazainduló tömegközlekedési megálló között séta van
                const firstRetStopCoord = resolveStopCoordinate(bestRet.legs[0]?.fromStop, trailhead.lat, trailhead.lon);
                const dLat = (trailhead.lat - firstRetStopCoord[0]) * 111;
                const dLon = (trailhead.lon - firstRetStopCoord[1]) * 75;
                const distFromTrailKm = parseFloat(Math.hypot(dLat, dLon).toFixed(2));

                const legsList = [];
                let currentFinishTimeMins = trailFinishMins;

                if (distFromTrailKm >= 0.2) {
                    const walkMins = Math.max(3, Math.round((distFromTrailKm / 4.0) * 60));
                    const walkDepMins = currentFinishTimeMins;
                    const walkArrMins = currentFinishTimeMins + walkMins;

                    legsList.push({
                        legIndex: outboundLegs.length + 2,
                        legType: 'walk_from_trail',
                        badgeType: 'SÉTA',
                        badgeColor: '#0ea5e9',
                        lineName: `Séta a megállóhoz (~${(distFromTrailKm * 1000).toFixed(0)}m)`,
                        directionText: `${bestRet.legs[0]?.fromStop} felé`,
                        depTime: minutesToTimeStr(walkDepMins),
                        arrTime: minutesToTimeStr(walkArrMins),
                        durationMin: walkMins,
                        fromStop: `${trail.name} célja`,
                        toStop: bestRet.legs[0]?.fromStop,
                        fromCoord: [trailhead.lat, trailhead.lon],
                        toCoord: firstRetStopCoord,
                        note: 'Gyalogos visszajutás a megállóba'
                    });
                }

                bestRet.legs.forEach((l, idx) => {
                    const fromCoord = resolveStopCoordinate(l.fromStop, trailhead.lat, trailhead.lon);
                    const toCoord = resolveStopCoordinate(l.toStop, homeLat, homeLon);
                    legsList.push({
                        legIndex: outboundLegs.length + 2 + legsList.length,
                        legType: 'transit_return',
                        badgeType: l.badgeType,
                        badgeColor: l.badgeColor,
                        lineName: l.lineName,
                        directionText: `${l.toStop} felé (hazaút)`,
                        depTime: l.depTime,
                        arrTime: l.arrTime,
                        durationMin: l.durationMin,
                        fromStop: l.fromStop,
                        toStop: l.toStop,
                        fromCoord,
                        toCoord,
                        note: l.note || 'Menetrendek.hu élő hazajárat'
                    });
                });

                // Ha volt helyi ráhordó (pl. 59-es villamos), a hazaútnál is visszavisszük a Déli pu.-tól az otthonig!
                if (localFeeder) {
                    const lastTransitArrMins = parseTimeToMinutes(bestRet.arrivalTime);
                    const tramDepMins = lastTransitArrMins + 5;
                    const tramArrMins = tramDepMins + localFeeder.durationMin;
                    const feederWalkMins = localFeeder.distKm >= 0.15 ? Math.max(3, Math.round((localFeeder.distKm / 4.0) * 60)) : 0;
                    const finalHomeArrMins = tramArrMins + feederWalkMins;

                    legsList.push({
                        legIndex: outboundLegs.length + 2 + legsList.length,
                        legType: 'local_feeder_return',
                        badgeType: localFeeder.badgeType,
                        badgeColor: localFeeder.badgeColor,
                        lineName: localFeeder.lineName,
                        directionText: `${localFeeder.name} felé (hazaút)`,
                        depTime: minutesToTimeStr(tramDepMins),
                        arrTime: minutesToTimeStr(tramArrMins),
                        durationMin: localFeeder.durationMin,
                        fromStop: localFeeder.hubTarget,
                        toStop: localFeeder.name,
                        fromCoord: localFeeder.hubCoord,
                        toCoord: [localFeeder.lat, localFeeder.lon],
                        note: 'Közvetlen helyi villamosjárat hazafelé'
                    });

                    if (feederWalkMins > 0) {
                        legsList.push({
                            legIndex: outboundLegs.length + 2 + legsList.length,
                            legType: 'walk_to_home',
                            badgeType: 'SÉTA',
                            badgeColor: '#0ea5e9',
                            lineName: `Séta haza (~${(localFeeder.distKm * 1000).toFixed(0)}m)`,
                            directionText: `${homeAddress} felé`,
                            depTime: minutesToTimeStr(tramArrMins),
                            arrTime: minutesToTimeStr(finalHomeArrMins),
                            durationMin: feederWalkMins,
                            fromStop: localFeeder.name,
                            toStop: homeAddress,
                            fromCoord: [localFeeder.lat, localFeeder.lon],
                            toCoord: [homeLat, homeLon],
                            note: 'Gyalogos hazaérkezés a villamostól'
                        });
                    }
                    homeArrivalMins = finalHomeArrMins;
                } else {
                    homeArrivalMins = parseTimeToMinutes(bestRet.arrivalTime);
                }
                returnLegs = legsList;
                liveReturnFound = true;
            }
        } catch (err) {
            console.warn('Live return transit query fallback:', err.message);
        }

        if (!liveReturnFound) {
            returnLegs = [{
                legIndex: outboundLegs.length + 2,
                legType: 'direct_local_transit_return',
                badgeType: 'HELYI',
                badgeColor: '#0284c7',
                lineName: 'Hazatérés a túra rajtjától',
                directionText: `${homeAddress} felé`,
                depTime: finishTimeStr,
                arrTime: minutesToTimeStr(homeArrivalMins),
                durationMin: 45,
                fromStop: trailhead.name,
                toStop: homeAddress,
                fromCoord: [trailhead.lat, trailhead.lon],
                toCoord: [homeLat, homeLon],
                note: 'Becsült hazautazási idő'
            }];
        }

        // Túra szakasz
        const hikeLeg = {
            legIndex: outboundLegs.length + 1,
            legType: 'hiking_trail',
            badgeType: 'TÚRA',
            badgeColor: '#10b981',
            lineName: trail.name,
            directionText: `${trail.distance_km} km • +${trail.elevation_gain_m} m szint (${energyKm} Energy KM)`,
            depTime: minutesToTimeStr(trailArrivalMins),
            arrTime: finishTimeStr,
            durationMin: Math.round(totalHikeMinutes),
            fromStop: `${trail.start_stop} (Rajt)`,
            toStop: `${trail.start_stop} (Cél)`,
            note: `Tempó: ${effPace.toFixed(1)} km/h • ${breaksCount}x${breakDurationMin}p (${totalBreakMins}p) pihenő beiktatva`
        };

        const allLegs = [...outboundLegs, hikeLeg, ...returnLegs];

        const firstDep = outboundLegs[0]?.depTime || homeDeparture;
        const finalArr = minutesToTimeStr(homeArrivalMins);
        const totalDurationMins = homeArrivalMins - parseTimeToMinutes(firstDep);

        scenarios[sc.key] = {
            name: sc.name,
            pace_kmh: Number(effPace.toFixed(1)),
            walk_duration_str: `${Math.floor(walkMinutes / 60)}ó ${Math.round(walkMinutes % 60)}p`,
            total_hike_duration_str: `${Math.floor(totalHikeMinutes / 60)}ó ${Math.round(totalHikeMinutes % 60)}p`,
            trail_start_time: minutesToTimeStr(trailArrivalMins),
            trail_finish_time: finishTimeStr,
            return_transit_dep: returnLegs[0]?.depTime || finishTimeStr,
            buffer_at_stop_min: Math.max(0, parseTimeToMinutes(returnLegs[0]?.depTime || finishTimeStr) - trailFinishMins),
            home_departure_time: firstDep,
            home_arrival_time: finalArr,
            total_door_to_door_min: Math.round(totalDurationMins),
            total_door_to_door_str: `${Math.floor(totalDurationMins / 60)}ó ${Math.round(totalDurationMins % 60)}p`,
            legs: allLegs
        };
    }

    return {
        home: {
            address: homeAddress,
            lat: homeLat,
            lon: homeLon,
            dist_to_hub_km: 0,
            route_type: 'live_transit'
        },
        trail: {
            id: trail.id,
            name: trail.name,
            distance_km: trail.distance_km,
            elevation_gain_m: trail.elevation_gain_m,
            energy_km: trail.energy_km,
            transit_line: trail.transit_line,
            transit_hub: trail.transit_hub,
            start_stop: trail.start_stop,
            coordinates: trail.coordinates || []
        },
        alternatives: alternativeRoutes,
        scenarios
    };
}

module.exports = {
    getTrails,
    planTripFromLocation
};
