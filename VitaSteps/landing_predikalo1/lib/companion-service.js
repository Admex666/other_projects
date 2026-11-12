const fs = require('fs');
const path = require('path');
const { getLiveRoutes } = require('./menetrendek-client');

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
    homeDeparture = '08:00',
    paceKmh = 4.0,
    breaksCount = 2,
    breakDurationMin = 15,
    useLiveTransit = true,
    date = null
}) {
    const trails = getTrails();
    const trail = trails.find(t => t.id === trailId) || trails[0];
    if (!trail) throw new Error('Trail not found');

    const isKevely = trail.id.includes('kevely');
    const trailhead = isKevely ? TRAILHEADS.kevely : TRAILHEADS.predikalo;
    const travelDate = date || new Date().toISOString().split('T')[0];

    // Clean home address for station searching if necessary (e.g. "Pomáz" instead of whole street if geocoding fails)
    let searchOrigin = homeAddress;
    if (homeAddress.includes(',')) {
        searchOrigin = homeAddress.split(',')[0].trim();
    }

    // 1. ODAÚT LEKÉRDEZÉSE AZ ÉLŐ MENETRENDEKBŐL (MÁV + HÉV + Volán)
    let outboundLegs = [];
    let trailArrivalMins = parseTimeToMinutes(homeDeparture) + 40; // fallback
    let liveOutboundFound = false;

    try {
        const liveOutbound = await getLiveRoutes(searchOrigin, trailhead.search_query, travelDate, homeDeparture);
        if (liveOutbound && liveOutbound.routes && liveOutbound.routes.length > 0) {
            const bestOut = liveOutbound.routes[0];
            outboundLegs = bestOut.legs.map((l, idx) => ({
                legIndex: idx + 1,
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
                note: l.note || 'Menetrendek.hu élő hivatalos járat'
            }));
            trailArrivalMins = parseTimeToMinutes(bestOut.arrivalTime);
            liveOutboundFound = true;
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
            const liveReturn = await getLiveRoutes(trailhead.search_query, searchOrigin, travelDate, finishTimeStr);
            if (liveReturn && liveReturn.routes && liveReturn.routes.length > 0) {
                const bestRet = liveReturn.routes[0];
                returnLegs = bestRet.legs.map((l, idx) => ({
                    legIndex: outboundLegs.length + 2 + idx,
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
                    note: l.note || 'Menetrendek.hu élő hazajárat'
                }));
                homeArrivalMins = parseTimeToMinutes(bestRet.arrivalTime);
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
        scenarios
    };
}

module.exports = {
    getTrails,
    planTripFromLocation
};
