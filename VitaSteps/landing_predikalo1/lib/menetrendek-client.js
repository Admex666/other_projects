/**
 * Menetrendek.hu Live API Client
 * Supports MÁV-START (trains, S76, S72), Volánbusz, and BKK HÉV (H5, etc.)
 */

const ALL_NETWORKS = [1, 2, 3, 10, 11, 12, 13, 14, 24, 25, 26];
const API_URL = 'https://menetrendek.hu/menetrend/newinterface/index.php';

const DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://menetrendek.hu/',
    'Origin': 'https://menetrendek.hu',
    'X-Requested-With': 'XMLHttpRequest'
};

/**
 * Resolve station/stop details from Menetrendek.hu
 */
async function searchStation(queryText, dateStr) {
    const payload = {
        func: 'getStationOrAddrByText',
        params: {
            inputText: queryText,
            searchIn: ['stations'],
            searchDate: dateStr,
            maxResults: 5,
            networks: ALL_NETWORKS
        }
    };

    const res = await fetch(API_URL, {
        method: 'POST',
        headers: DEFAULT_HEADERS,
        body: JSON.stringify(payload)
    });

    if (!res.ok) {
        throw new Error(`Menetrendek station search failed: ${res.status}`);
    }

    const data = await res.json();
    const results = data.results || [];
    if (!results.length) return null;

    // Prefer HÉV (13, 24), train (2), or direct station hits over town center
    let matched = results[0];
    for (const cand of results) {
        if ([13, 24, 2].includes(cand.network_id) || 
            (cand.lsname && (cand.lsname.includes('HÉV') || cand.lsname.includes('vá.') || cand.lsname.includes('autóbusz-állomás')))) {
            matched = cand;
            break;
        }
    }
    return matched;
}

/**
 * Query route between two points
 * @param {string} fromText - e.g. "Pomáz" or "Batthyány tér"
 * @param {string} toText - e.g. "Pilisborosjenő" or "Dobogókő"
 * @param {string} dateStr - YYYY-MM-DD
 * @param {string} timeStr - HH:MM
 */
async function getLiveRoutes(fromText, toText, dateStr, timeStr = '08:00') {
    const [hour, min] = timeStr.split(':').map(s => s.padStart(2, '0'));

    const stFrom = await searchStation(fromText, dateStr);
    if (!stFrom) throw new Error(`Kiindulási megálló nem található: ${fromText}`);

    const stTo = await searchStation(toText, dateStr);
    if (!stTo) throw new Error(`Érkezési megálló nem található: ${toText}`);

    const routePayload = {
        func: 'getRoutes',
        params: {
            networks: ALL_NETWORKS,
            datum: dateStr,
            erk_stype: 'megallo',
            ext_settings: 'block',
            filtering: 0,
            helyi: 'No',
            honnan: stFrom.lsname,
            honnan_eovx: '',
            honnan_eovy: '',
            honnan_ls_id: stFrom.ls_id,
            honnan_settlement_id: stFrom.settlement_id,
            honnan_site_code: stFrom.site_code || '',
            honnan_zoom: 0,
            hour: hour,
            min: min,
            hova: stTo.lsname,
            hova_eovx: '',
            hova_eovy: '',
            hova_ls_id: stTo.ls_id,
            hova_settlement_id: stTo.settlement_id,
            hova_site_code: stTo.site_code || '',
            hova_zoom: 0,
            ind_stype: 'megallo',
            keresztul: '',
            keresztul_eovx: '',
            keresztul_eovy: '',
            keresztul_ls_id: 0,
            keresztul_settlement_id: 0,
            keresztul_site_code: '',
            keresztul_zoom: 0,
            keresztul_stype: 'megallo',
            maxatszallas: '5',
            maxvar: '120',
            maxwalk: '1500',
            napszak: 3,
            naptipus: 0,
            odavissza: 0,
            preferencia: 0,
            rendezes: 1, // 1 = Departure time ascending (prioritizes fastest upcoming S76/HÉV connections)
            valasztottinterface: 'folyamatos'
        }
    };

    const res = await fetch(API_URL, {
        method: 'POST',
        headers: DEFAULT_HEADERS,
        body: JSON.stringify(routePayload)
    });

    if (!res.ok) {
        throw new Error(`Menetrendek getRoutes failed: ${res.status}`);
    }

    const data = await res.json();
    const talalatok = data.results?.talalatok || {};
    const parsedRoutes = [];

    for (const [k, r] of Object.entries(talalatok)) {
        const runs = r.kifejtes_postjson?.runs;
        if (!runs) continue;

        const legs = [];
        const runKeys = Object.keys(runs).sort((a, b) => parseInt(a, 10) - parseInt(b, 10));

        for (let idx = 0; idx < runKeys.length; idx++) {
            const run = runs[runKeys[idx]];
            const depMins = run['6'];
            const arrMins = run['7'];
            const depFormatted = `${String(Math.floor(depMins / 60)).padStart(2, '0')}:${String(depMins % 60).padStart(2, '0')}`;
            const arrFormatted = `${String(Math.floor(arrMins / 60)).padStart(2, '0')}:${String(arrMins % 60).padStart(2, '0')}`;

            let modeBadge = 'BUSZ';
            let badgeColor = '#f59e0b';
            const netId = run['11'];
            
            // run['38'] is the human-readable line code (pl. H5, S76, 218), fallback to run['15'] or run['2']
            const lineName = String(run['38'] || run['15'] || run['2'] || '');
            const fromStationName = run['23'] || 'Indulási megálló';
            const toStationName = run['24'] || 'Érkezési megálló';
            const explanation = run['29'] || '';

            if (lineName.startsWith('2') || lineName.startsWith('8') || netId === 1 || netId === 10) {
                modeBadge = 'BUSZ';
                badgeColor = '#f59e0b';
            } else if (netId === 13 || (netId === 24 && lineName.startsWith('H')) || lineName.startsWith('H')) {
                modeBadge = 'HÉV';
                badgeColor = '#059669';
            } else if (netId === 2 || lineName.startsWith('S') || lineName.startsWith('Z') || lineName.startsWith('G')) {
                modeBadge = 'VONAT';
                badgeColor = '#2563eb';
            } else if (netId === 12 || lineName === '1' || lineName === '1A') {
                modeBadge = 'VILLAMOS';
                badgeColor = '#eab308';
            } else if (netId === 14 || lineName.startsWith('M')) {
                modeBadge = 'METRÓ';
                badgeColor = '#dc2626';
            }

            legs.push({
                legIndex: idx + 1,
                legType: 'transit',
                badgeType: modeBadge,
                badgeColor: badgeColor,
                lineName: lineName,
                fromStop: fromStationName,
                toStop: toStationName,
                depTime: depFormatted,
                arrTime: arrFormatted,
                durationMin: arrMins - depMins,
                note: explanation
            });
        }

        if (legs.length > 0) {
            const firstLeg = legs[0];
            const lastLeg = legs[legs.length - 1];
            parsedRoutes.push({
                id: k,
                departureTime: firstLeg.depTime,
                arrivalTime: lastLeg.arrTime,
                durationStr: r.osszido,
                totalDistance: r.ossztav,
                totalFare: r.totalFare,
                transfersCount: r.atszallasok_szama,
                legs: legs
            });
        }
    }

    return {
        from: stFrom.lsname,
        to: stTo.lsname,
        date: dateStr,
        routes: parsedRoutes
    };
}

module.exports = {
    searchStation,
    getLiveRoutes
};
