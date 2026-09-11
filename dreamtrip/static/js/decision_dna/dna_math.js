/**
 * Optivoya — Decision DNA Mathematical Engine
 * Saaty Pairwise Comparison matrix geometric mean calculation & parameter stepping.
 */

(function () {
    const scaleValues = [9.0, 5.0, 3.0, 1.0, 1.0 / 3.0, 1.0 / 5.0, 1.0 / 9.0];

    const DNAMath = {
        calculateAllAHP(state) {
            // 1. Destination AHP (4x4: Total Cost, Weather, Safety, Experience)
            const a_cw = scaleValues[state.dest_ahp?.total_cost_vs_weather ?? 3];
            const a_cs = scaleValues[state.dest_ahp?.total_cost_vs_safety ?? 3];
            const a_ce = scaleValues[state.dest_ahp?.total_cost_vs_experience ?? 3];
            const a_ws = scaleValues[state.dest_ahp?.weather_vs_safety ?? 3];
            const a_we = scaleValues[state.dest_ahp?.weather_vs_experience ?? 3];
            const a_se = scaleValues[state.dest_ahp?.safety_vs_experience ?? 3];

            const mDest = [
                [1.0, a_cw, a_cs, a_ce],
                [1.0 / a_cw, 1.0, a_ws, a_we],
                [1.0 / a_cs, 1.0 / a_ws, 1.0, a_se],
                [1.0 / a_ce, 1.0 / a_we, 1.0 / a_se, 1.0]
            ];
            const gDest = [
                Math.pow(mDest[0][0] * mDest[0][1] * mDest[0][2] * mDest[0][3], 0.25),
                Math.pow(mDest[1][0] * mDest[1][1] * mDest[1][2] * mDest[1][3], 0.25),
                Math.pow(mDest[2][0] * mDest[2][1] * mDest[2][2] * mDest[2][3], 0.25),
                Math.pow(mDest[3][0] * mDest[3][1] * mDest[3][2] * mDest[3][3], 0.25)
            ];
            const tDest = gDest[0] + gDest[1] + gDest[2] + gDest[3];
            state.calculated_weights.dest = {
                total_cost: Math.round((gDest[0] / tDest) * 100),
                weather: Math.round((gDest[1] / tDest) * 100),
                safety: Math.round((gDest[2] / tDest) * 100),
                experience: Math.round((gDest[3] / tDest) * 100)
            };

            // 2. Flight AHP (3x3: Price, Duration, Stops)
            const mFlight = [
                [1.0, scaleValues[state.flight_ahp.price_vs_duration], scaleValues[state.flight_ahp.price_vs_stops]],
                [1.0 / scaleValues[state.flight_ahp.price_vs_duration], 1.0, scaleValues[state.flight_ahp.duration_vs_stops]],
                [1.0 / scaleValues[state.flight_ahp.price_vs_stops], 1.0 / scaleValues[state.flight_ahp.duration_vs_stops], 1.0]
            ];
            const gFlight = [
                Math.cbrt(mFlight[0][0] * mFlight[0][1] * mFlight[0][2]),
                Math.cbrt(mFlight[1][0] * mFlight[1][1] * mFlight[1][2]),
                Math.cbrt(mFlight[2][0] * mFlight[2][1] * mFlight[2][2])
            ];
            const tFlight = gFlight[0] + gFlight[1] + gFlight[2];
            state.calculated_weights.flight = {
                price: Math.round((gFlight[0] / tFlight) * 100),
                duration: Math.round((gFlight[1] / tFlight) * 100),
                stops: Math.round((gFlight[2] / tFlight) * 100)
            };

            // 3. Stay AHP (4x4: Price, Rating, Location, Amenities)
            const a_pr = scaleValues[state.stay_ahp.price_vs_rating];
            const a_pl = scaleValues[state.stay_ahp.price_vs_location];
            const a_pa = scaleValues[state.stay_ahp.price_vs_amenities];
            const a_rl = scaleValues[state.stay_ahp.rating_vs_location];
            const a_ra = scaleValues[state.stay_ahp.rating_vs_amenities];
            const a_la = scaleValues[state.stay_ahp.location_vs_amenities];

            const mStay = [
                [1.0, a_pr, a_pl, a_pa],
                [1.0 / a_pr, 1.0, a_rl, a_ra],
                [1.0 / a_pl, 1.0 / a_rl, 1.0, a_la],
                [1.0 / a_pa, 1.0 / a_ra, 1.0 / a_la, 1.0]
            ];
            const gStay = [
                Math.pow(mStay[0][0] * mStay[0][1] * mStay[0][2] * mStay[0][3], 0.25),
                Math.pow(mStay[1][0] * mStay[1][1] * mStay[1][2] * mStay[1][3], 0.25),
                Math.pow(mStay[2][0] * mStay[2][1] * mStay[2][2] * mStay[2][3], 0.25),
                Math.pow(mStay[3][0] * mStay[3][1] * mStay[3][2] * mStay[3][3], 0.25)
            ];
            const tStay = gStay[0] + gStay[1] + gStay[2] + gStay[3];
            state.calculated_weights.stay = {
                price: Math.round((gStay[0] / tStay) * 100),
                rating: Math.round((gStay[1] / tStay) * 100),
                location: Math.round((gStay[2] / tStay) * 100),
                amenities: Math.round((gStay[3] / tStay) * 100)
            };
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
