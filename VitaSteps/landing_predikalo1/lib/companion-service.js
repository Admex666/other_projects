const fs = require('fs');
const path = require('path');
const https = require('https');

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

function getSchedules() {
    try {
        const p = path.join(COMPANION_DIR, 'schedules.json');
        if (fs.existsSync(p)) {
            return JSON.parse(fs.readFileSync(p, 'utf8'));
        }
    } catch (e) {
        console.error('Error reading schedules.json:', e);
    }
    return {};
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

function findNextDeparture(schedList, targetMinutes, minBuffer = 5) {
    const threshold = targetMinutes + minBuffer;
    const sorted = schedList.map(parseTimeToMinutes).sort((a, b) => a - b);
    for (const dep of sorted) {
        if (dep >= threshold) {
            return dep;
        }
    }
    return sorted.length > 0 ? sorted[0] : threshold;
}

// Távolság koordinátákból (Haversine km)
function calculateDistanceKm(lat1, lon1, lat2, lon2) {
    const R = 6371; // km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// Csomópontok és Rajtpontok pontos koordinátái
const HUBS = {
    szentlelek: {
        id: 'szentlelek',
        name: 'Szentlélek tér H',
        lat: 47.5398,
        lon: 19.0463
    },
    batthyany: {
        id: 'batthyany',
        name: 'Batthyány tér M+H',
        lat: 47.5057,
        lon: 19.0393
    }
};

const TRAILHEADS = {
    kevely: {
        id: 'kevely',
        name: 'Pilisborosjenő, autóbusz-forduló (218-as)',
        lat: 47.6091,
        lon: 18.9897
    },
    predikalo: {
        id: 'predikalo',
        name: 'Pomáz H (H5 HÉV kapu)',
        lat: 47.6426,
        lon: 19.0315
    }
};

function planTripFromLocation({
    homeLat = 47.4979,
    homeLon = 19.0402,
    homeAddress = 'Budapest belváros',
    trailId = 'kevely_klasszik',
    homeDeparture = '08:00',
    paceKmh = 4.0,
    breaksCount = 2,
    breakDurationMin = 15
}) {
    const trails = getTrails();
    const trail = trails.find(t => t.id === trailId) || trails[0];
    const schedules = getSchedules();

    if (!trail) {
        throw new Error('Trail not found');
    }

    const isKevely = trail.id.includes('kevely');
    const trailhead = isKevely ? TRAILHEADS.kevely : TRAILHEADS.predikalo;
    const defaultHub = isKevely ? HUBS.szentlelek : HUBS.batthyany;

    // Távolság az otthontól a rajthelyig és a belvárosi hubig
    const distToTrailheadKm = calculateDistanceKm(homeLat, homeLon, trailhead.lat, trailhead.lon);
    const distToHubKm = calculateDistanceKm(homeLat, homeLon, defaultHub.lat, defaultHub.lon);

    // DÖNTÉS: Közvetlenül a rajthoz utazunk, vagy a belvárosi csomóponton (Hub) keresztül?
    // Ha a felhasználó közelebb van a túra rajtjához (pl. Pomáz, Szentendre, Üröm, Óbuda),
    // mint a belvárosi Hubhoz, vagy 12 km-en belül van, NEM visszük be feleslegesen a belvárosba!
    const isDirectLocalRoute = distToTrailheadKm < distToHubKm || distToTrailheadKm <= 12;

    const schedTo = schedules[trail.schedule_to_key] || [];
    const schedFrom = schedules[trail.schedule_from_key] || [];
    const trailTransitDuration = trail.transit_duration_min || 25;

    let bkkLegsTemplate = [];
    let homeDepMins = parseTimeToMinutes(homeDeparture);
    let trailStartMins = 0;
    let trailReturnDepMins = 0;
    let homeArrivalMins = 0;

    if (isDirectLocalRoute) {
        // -------------------------------------------------------------
        // KÖZVETLEN HELYI / AGGLOMERÁCIÓS UTAZÁS (pl. Pomáz, Szentendre, Solymár, Pilisvörösvár)
        // -------------------------------------------------------------
        let localTravelMin = Math.max(5, Math.round(distToTrailheadKm * 2.2)); // ~25-30 km/h helyi busz/autó/kerékpár
        let directModeBadge = 'HELYI';
        let directModeName = `Közvetlen eljutás a túra rajtjához (${distToTrailheadKm.toFixed(1)} km)`;
        let directColor = '#0284c7';

        if (distToTrailheadKm < 1.5) {
            localTravelMin = Math.max(5, Math.round(distToTrailheadKm / 4.0 * 60));
            directModeBadge = 'SÉTA';
            directModeName = `Gyalogos eljutás a túra rajtjához (${(distToTrailheadKm * 1000).toFixed(0)} m)`;
            directColor = '#64748b';
        } else if (distToTrailheadKm <= 8) {
            directModeBadge = 'BUSZ';
            directModeName = `Helyi agglomerációs csatlakozás (${distToTrailheadKm.toFixed(1)} km)`;
            directColor = '#f59e0b';
        }

        trailStartMins = homeDepMins + localTravelMin;

        // Túra számítás (Energy KM = D + E / 95)
        const energyKm = trail.energy_km;
        const totalBreakMins = breaksCount * breakDurationMin;

        const scenarios = {};
        const scenarioConfigs = [
            { key: 'faster', factor: 1.15, name: 'Gyorsabb tempó (+15%)' },
            { key: 'normal', factor: 1.00, name: 'Tervezett normál tempó' },
            { key: 'slower', factor: 0.85, name: 'Kényelmesebb tempó (-15%)' }
        ];

        scenarioConfigs.forEach(sc => {
            const effPace = paceKmh * sc.factor;
            const walkMinutes = (energyKm / effPace) * 60;
            const totalHikeMinutes = walkMinutes + totalBreakMins;
            const finishMins = trailStartMins + totalHikeMinutes;

            // Hazajutás közvetlenül (nem visszük be Budapestre!)
            const homeArrMins = finishMins + localTravelMin;

            const legs = [
                // 1. Odaút közvetlenül
                {
                    legIndex: 1,
                    legType: 'direct_local_transit',
                    badgeType: directModeBadge,
                    badgeColor: directColor,
                    lineName: directModeName,
                    directionText: `${trailhead.name} felé (közvetlen út)`,
                    depTime: homeDeparture,
                    arrTime: minutesToTimeStr(trailStartMins),
                    durationMin: localTravelMin,
                    fromStop: homeAddress,
                    toStop: trailhead.name,
                    note: `Közvetlen elérés (${distToTrailheadKm.toFixed(1)} km) • Nem szükséges belvárosi átszállás!`
                },
                // 2. A túra
                {
                    legIndex: 2,
                    legType: 'hiking_trail',
                    badgeType: 'TÚRA',
                    badgeColor: '#10b981',
                    lineName: trail.name,
                    directionText: `${trail.distance_km} km • +${trail.elevation_gain_m} m szint (${energyKm} Energy KM)`,
                    depTime: minutesToTimeStr(trailStartMins),
                    arrTime: minutesToTimeStr(finishMins),
                    durationMin: Math.round(totalHikeMinutes),
                    fromStop: `${trail.start_stop} (Rajt)`,
                    toStop: `${trail.start_stop} (Cél)`,
                    note: `Tempó: ${effPace.toFixed(1)} km/h • ${breaksCount}x${breakDurationMin}p (${totalBreakMins}p) pihenő beiktatva`
                },
                // 3. Hazaút közvetlenül
                {
                    legIndex: 3,
                    legType: 'direct_local_transit_return',
                    badgeType: directModeBadge,
                    badgeColor: directColor,
                    lineName: directModeName,
                    directionText: `${homeAddress} felé (hazatérés)`,
                    depTime: minutesToTimeStr(finishMins),
                    arrTime: minutesToTimeStr(homeArrMins),
                    durationMin: localTravelMin,
                    fromStop: trailhead.name,
                    toStop: homeAddress,
                    note: 'Közvetlen hazatérés a kiindulópontra! 🏅'
                }
            ];

            scenarios[sc.key] = {
                name: sc.name,
                pace_kmh: Number(effPace.toFixed(1)),
                walk_duration_str: `${Math.floor(walkMinutes / 60)}ó ${Math.round(walkMinutes % 60)}p`,
                total_hike_duration_str: `${Math.floor(totalHikeMinutes / 60)}ó ${Math.round(totalHikeMinutes % 60)}p`,
                trail_start_time: minutesToTimeStr(trailStartMins),
                trail_finish_time: minutesToTimeStr(finishMins),
                return_transit_dep: minutesToTimeStr(finishMins),
                buffer_at_stop_min: 0,
                home_departure_time: homeDeparture,
                home_arrival_time: minutesToTimeStr(homeArrMins),
                total_door_to_door_min: Math.round(homeArrMins - homeDepMins),
                total_door_to_door_str: `${Math.floor((homeArrMins - homeDepMins) / 60)}ó ${Math.round((homeArrMins - homeDepMins) % 60)}p`,
                legs
            };
        });

        return {
            home: {
                address: homeAddress,
                lat: homeLat,
                lon: homeLon,
                dist_to_trailhead_km: Number(distToTrailheadKm.toFixed(1)),
                route_type: 'direct_local'
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

    // -------------------------------------------------------------
    // TÁVOLABBI PONT / BELVÁROSI CSOMÓPONTOS UTAZÁS (pl. Pest, Dél-Buda, Vidék)
    // -------------------------------------------------------------
    let transitToHubMin = 20;
    let localLeg = {
        badgeType: 'M2',
        badgeColor: '#e11d48',
        name: 'BKK metró / tranzit csatlakozás'
    };

    if (distToHubKm <= 20) {
        transitToHubMin = Math.round(8 + (distToHubKm / 22.0 * 60));
        if (isKevely) {
            localLeg = { badgeType: '1-es', badgeColor: '#eab308', name: '1-es villamos / csatlakozás' };
        } else {
            localLeg = { badgeType: 'M2', badgeColor: '#e11d48', name: 'M2 metró csatlakozás' };
        }
    } else {
        transitToHubMin = Math.round(20 + (distToHubKm / 55.0 * 60));
        localLeg = { badgeType: 'MÁV', badgeColor: '#0284c7', name: `MÁV vonat / távolsági busz (${distToHubKm.toFixed(0)} km)` };
    }

    const hubArrivalMins = homeDepMins + transitToHubMin;
    const trailTransitDepMins = findNextDeparture(schedTo, hubArrivalMins, 5);
    const hubWaitMins = trailTransitDepMins - hubArrivalMins;
    trailStartMins = trailTransitDepMins + trailTransitDuration;

    const energyKm = trail.energy_km;
    const totalBreakMins = breaksCount * breakDurationMin;

    const scenarios = {};
    const scenarioConfigs = [
        { key: 'faster', factor: 1.15, name: 'Gyorsabb tempó (+15%)' },
        { key: 'normal', factor: 1.00, name: 'Tervezett normál tempó' },
        { key: 'slower', factor: 0.85, name: 'Kényelmesebb tempó (-15%)' }
    ];

    scenarioConfigs.forEach(sc => {
        const effPace = paceKmh * sc.factor;
        const walkMinutes = (energyKm / effPace) * 60;
        const totalHikeMinutes = walkMinutes + totalBreakMins;
        const finishMins = trailStartMins + totalHikeMinutes;

        const returnTransitDepMins = findNextDeparture(schedFrom, finishMins, 8);
        const bufferAtStop = returnTransitDepMins - finishMins;
        const hubReturnMins = returnTransitDepMins + trailTransitDuration;
        const homeArrMins = hubReturnMins + transitToHubMin;

        const legs = [
            {
                legIndex: 1,
                legType: 'local_transit',
                badgeType: localLeg.badgeType,
                badgeColor: localLeg.badgeColor,
                lineName: localLeg.name,
                directionText: `${defaultHub.name} felé`,
                depTime: homeDeparture,
                arrTime: minutesToTimeStr(hubArrivalMins),
                durationMin: transitToHubMin,
                fromStop: homeAddress,
                toStop: defaultHub.name,
                note: `Átszállási várakozás: ${hubWaitMins} perc`
            },
            {
                legIndex: 2,
                legType: 'trail_transit',
                badgeType: isKevely ? '218' : 'H5',
                badgeColor: isKevely ? '#2563eb' : '#059669',
                lineName: trail.transit_line,
                directionText: `${trail.start_stop} felé`,
                depTime: minutesToTimeStr(trailTransitDepMins),
                arrTime: minutesToTimeStr(trailStartMins),
                durationMin: trailTransitDuration,
                fromStop: defaultHub.name,
                toStop: trail.start_stop,
                note: 'Menetrend szerinti közvetlen BKK járat'
            },
            {
                legIndex: 3,
                legType: 'hiking_trail',
                badgeType: 'TÚRA',
                badgeColor: '#10b981',
                lineName: trail.name,
                directionText: `${trail.distance_km} km • +${trail.elevation_gain_m} m szint (${energyKm} Energy KM)`,
                depTime: minutesToTimeStr(trailStartMins),
                arrTime: minutesToTimeStr(finishMins),
                durationMin: Math.round(totalHikeMinutes),
                fromStop: `${trail.start_stop} (Rajt)`,
                toStop: `${trail.start_stop} (Cél)`,
                note: `Tempó: ${effPace.toFixed(1)} km/h • ${breaksCount}x${breakDurationMin}p pihenő • Puffer: ${Math.round(bufferAtStop)} perc`
            },
            {
                legIndex: 4,
                legType: 'trail_transit_return',
                badgeType: isKevely ? '218' : 'H5',
                badgeColor: isKevely ? '#2563eb' : '#059669',
                lineName: trail.transit_line,
                directionText: `${defaultHub.name} felé`,
                depTime: minutesToTimeStr(returnTransitDepMins),
                arrTime: minutesToTimeStr(hubReturnMins),
                durationMin: trailTransitDuration,
                fromStop: trail.start_stop,
                toStop: defaultHub.name,
                note: 'Menetrend szerinti közvetlen BKK hazajárat'
            },
            {
                legIndex: 5,
                legType: 'local_transit_return',
                badgeType: localLeg.badgeType,
                badgeColor: localLeg.badgeColor,
                lineName: localLeg.name,
                directionText: `${homeAddress} felé`,
                depTime: minutesToTimeStr(hubReturnMins),
                arrTime: minutesToTimeStr(homeArrMins),
                durationMin: transitToHubMin,
                fromStop: defaultHub.name,
                toStop: homeAddress,
                note: 'Hazaérkezés az ajtóba! 🏅'
            }
        ];

        scenarios[sc.key] = {
            name: sc.name,
            pace_kmh: Number(effPace.toFixed(1)),
            walk_duration_str: `${Math.floor(walkMinutes / 60)}ó ${Math.round(walkMinutes % 60)}p`,
            total_hike_duration_str: `${Math.floor(totalHikeMinutes / 60)}ó ${Math.round(totalHikeMinutes % 60)}p`,
            trail_start_time: minutesToTimeStr(trailStartMins),
            trail_finish_time: minutesToTimeStr(finishMins),
            return_transit_dep: minutesToTimeStr(returnTransitDepMins),
            buffer_at_stop_min: Math.round(bufferAtStop),
            home_departure_time: homeDeparture,
            home_arrival_time: minutesToTimeStr(homeArrMins),
            total_door_to_door_min: Math.round(homeArrMins - homeDepMins),
            total_door_to_door_str: `${Math.floor((homeArrMins - homeDepMins) / 60)}ó ${Math.round((homeArrMins - homeDepMins) % 60)}p`,
            legs
        };
    });

    return {
        home: {
            address: homeAddress,
            lat: homeLat,
            lon: homeLon,
            dist_to_hub_km: Number(distToHubKm.toFixed(1)),
            route_type: 'hub_based'
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
    getSchedules,
    planTripFromLocation
};
