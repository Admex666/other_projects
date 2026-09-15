/**
 * Optivoya — Decision DNA Mathematical Engine
 * Saaty Pairwise Comparison matrix geometric mean calculation & parameter stepping.
 * Supports dynamic active criteria subsets: inactive criteria receive 0% weight,
 * while active criteria are computed via Saaty AHP geometric mean and normalized to 100%.
 */

(function () {
    // 9-point Saaty AHP scale: 9, 7, 5, 3, 1, 1/3, 1/5, 1/7, 1/9 (center index 4 = 1.0)
    const scaleValues = [9.0, 7.0, 5.0, 3.0, 1.0, 1.0 / 3.0, 1.0 / 5.0, 1.0 / 7.0, 1.0 / 9.0];

    function computeAHPWeights(allKeys, activeKeys, pairMap, storageObj) {
        const result = {};
        allKeys.forEach(k => { result[k] = 0; });
        const effectiveActive = (activeKeys && activeKeys.length > 0) 
            ? activeKeys.filter(k => allKeys.includes(k)) 
            : [...allKeys];

        if (effectiveActive.length === 0) {
            allKeys.forEach(k => { result[k] = Math.round(100 / allKeys.length); });
            return result;
        }

        if (effectiveActive.length === 1) {
            result[effectiveActive[0]] = 100;
            return result;
        }

        const n = effectiveActive.length;
        const M = [];
        for (let i = 0; i < n; i++) {
            M[i] = [];
            for (let j = 0; j < n; j++) {
                M[i][j] = (i === j) ? 1.0 : null;
            }
        }

        // Fill known direct and reverse pairs
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                if (i !== j) {
                    const k1 = effectiveActive[i];
                    const k2 = effectiveActive[j];
                    const directPair = pairMap[`${k1}:${k2}`];
                    const reversePair = pairMap[`${k2}:${k1}`];
                    if (directPair && storageObj?.[directPair] !== undefined) {
                        const sliderIdx = storageObj[directPair] ?? 4;
                        M[i][j] = scaleValues[sliderIdx] || 1.0;
                    } else if (reversePair && storageObj?.[reversePair] !== undefined) {
                        const sliderIdx = storageObj[reversePair] ?? 4;
                        const val = scaleValues[sliderIdx] || 1.0;
                        M[i][j] = 1.0 / val;
                    }
                }
            }
        }

        // Complete any missing pair (e.g. capped at 5 comparisons) using geometric transitivity
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                if (i !== j && M[i][j] === null) {
                    let prod = 1.0;
                    let count = 0;
                    for (let k = 0; k < n; k++) {
                        if (k !== i && k !== j && M[i][k] !== null && M[k][j] !== null) {
                            prod *= (M[i][k] * M[k][j]);
                            count++;
                        }
                    }
                    if (count > 0) {
                        M[i][j] = Math.pow(prod, 1.0 / count);
                    } else {
                        M[i][j] = 1.0;
                    }
                }
            }
        }

        const geom = [];
        let totalGeom = 0.0;
        for (let i = 0; i < n; i++) {
            let prod = 1.0;
            for (let j = 0; j < n; j++) {
                prod *= M[i][j];
            }
            geom[i] = Math.pow(prod, 1.0 / n);
            totalGeom += geom[i];
        }

        let sumW = 0;
        let maxIdx = 0;
        let maxVal = -1;
        for (let i = 0; i < n; i++) {
            const w = Math.round((geom[i] / totalGeom) * 100);
            result[effectiveActive[i]] = w;
            sumW += w;
            if (w > maxVal) {
                maxVal = w;
                maxIdx = i;
            }
        }

        if (sumW !== 100 && effectiveActive.length > 0) {
            result[effectiveActive[maxIdx]] += (100 - sumW);
        }
        return result;
    }

    const destKeys = ['total_cost', 'weather', 'safety', 'experience'];
    const destPairMap = {
        'total_cost:weather': 'total_cost_vs_weather',
        'total_cost:safety': 'total_cost_vs_safety',
        'total_cost:experience': 'total_cost_vs_experience',
        'weather:safety': 'weather_vs_safety',
        'weather:experience': 'weather_vs_experience',
        'safety:experience': 'safety_vs_experience'
    };

    const flightKeys = ['price', 'duration', 'stops'];
    const flightPairMap = {
        'price:duration': 'price_vs_duration',
        'price:stops': 'price_vs_stops',
        'duration:stops': 'duration_vs_stops'
    };

    const stayKeys = ['price', 'rating', 'location', 'amenities'];
    const stayPairMap = {
        'price:rating': 'price_vs_rating',
        'price:location': 'price_vs_location',
        'price:amenities': 'price_vs_amenities',
        'rating:location': 'rating_vs_location',
        'rating:amenities': 'rating_vs_amenities',
        'location:amenities': 'location_vs_amenities'
    };

    const DNAMath = {
        calculateAllAHP(state) {
            if (!state.calculated_weights) {
                state.calculated_weights = { dest: {}, flight: {}, stay: {} };
            }

            const activeDest = state.active_criteria?.dest || destKeys;
            state.calculated_weights.dest = computeAHPWeights(destKeys, activeDest, destPairMap, state.dest_ahp);

            const activeFlight = state.active_criteria?.flight || flightKeys;
            state.calculated_weights.flight = computeAHPWeights(flightKeys, activeFlight, flightPairMap, state.flight_ahp);

            const activeStay = state.active_criteria?.stay || stayKeys;
            state.calculated_weights.stay = computeAHPWeights(stayKeys, activeStay, stayPairMap, state.stay_ahp);
        },

        stepValue(obj, key, param, dir, callback) {
            const cfg = obj[key];
            const isQ = param === 'q';
            const step = isQ ? (cfg.stepQ || 1000) : (cfg.stepP || 5000);
            let val = cfg[param] + (dir * step);
            if (val < 0) val = 0;
            cfg[param] = parseFloat(val.toFixed(2));
            if (typeof callback === 'function') callback();
        }
    };

    window.DNAMath = DNAMath;
})();
