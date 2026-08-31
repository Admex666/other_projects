/**
 * Optivoya — Master Planner State & Navigation Module
 * Central reactive state store, stepper synchronization, and cache management.
 */

(function () {
    const PlannerState = {
        step: 0,
        date_mode: 'exact',
        exact_fp: null,
        interval_out_fp: null,
        interval_in_fp: null,
        criteria_completed: false,
        pollInterval: null,

        intake: {
            origin: "Budapest (BUD)",
            adults: 2,
            children: 0,
            date_mode: "exact",
            month: "9",
            duration: 7,
            exact_out_date: "2026-09-10",
            exact_in_date: "2026-09-17",
            out_from: "2026-09-01",
            out_to: "2026-09-15",
            in_from: "2026-09-08",
            in_to: "2026-09-30",
            min_stay: 5,
            max_stay: 10,
            has_departure_pref: false,
            departure_hour: 0,
            flight_direct_only: false,
            flight_max_stops: 1,
            max_flight_duration_h: 0,
            hotel_min_stars: 3,
            hotel_min_rating: 7.5,
            hotel_types: ["hotel", "apartment", "resort", "guesthouse"],
            breakfast: false,
            amenities: [],
            ahp_weights: {
                total_cost: 34.0,
                weather: 33.0,
                safety: 33.0
            },
            promethee_params: {
                price: { type: 5, q: 5000, p: 35000 },
                duration: { type: 5, q: 0.5, p: 3.0 },
                stay: { type: 5, q: 1.0, p: 3.0 }
            },
            stay_weights: {
                price: 35.0,
                rating: 30.0,
                location: 20.0,
                amenities: 15.0
            }
        },

        destinations: [],
        selectedDest: null,
        flights: [],
        selectedFlight: null,
        stays: [],
        selectedStay: null,

        setStep(stepNum) {
            this.step = stepNum;

            // Update Stepper UI (Nodes 0..4)
            for (let i = 0; i <= 4; i++) {
                const node = document.getElementById(`stepNode${i}`);
                const conn = document.getElementById(`stepConn${i}`);
                const sec = document.getElementById(`wizardStep${i}`);

                if (node) {
                    node.classList.remove('active', 'completed');
                    if (i < stepNum) node.classList.add('completed');
                    else if (i === stepNum) node.classList.add('active');
                }

                if (conn) {
                    conn.classList.remove('completed');
                    if (i < stepNum) conn.classList.add('completed');
                }

                if (sec) {
                    sec.style.display = (i === stepNum) ? 'block' : 'none';
                }
            }

            const loader = document.getElementById('wizardLoading');
            if (loader) loader.style.display = 'none';

            window.scrollTo({ top: 0, behavior: 'smooth' });
        },

        showLoader(title, subtitle) {
            for (let i = 0; i <= 4; i++) {
                const sec = document.getElementById(`wizardStep${i}`);
                if (sec) sec.style.display = 'none';
            }
            const loader = document.getElementById('wizardLoading');
            if (loader) {
                loader.style.display = 'block';
                const tEl = document.getElementById('wizardLoadingTitle');
                const sEl = document.getElementById('wizardLoadingSubtitle');
                const pEl = document.getElementById('wizardProgressBar');
                if (tEl) tEl.innerText = title || "Elemzés folyamatban...";
                if (sEl) sEl.innerText = subtitle || "Valós adatok feldolgozása...";
                if (pEl) pEl.style.width = '20%';
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },

        getSessionCache(key) {
            try {
                const raw = sessionStorage.getItem(`optivoya_cache_${key}`);
                if (!raw) return null;
                const item = JSON.parse(raw);
                if (Date.now() - item.ts > 30 * 60 * 1000) { // 30 perc TTL
                    sessionStorage.removeItem(`optivoya_cache_${key}`);
                    return null;
                }
                return item.data;
            } catch (e) {
                return null;
            }
        },

        setSessionCache(key, data) {
            try {
                sessionStorage.setItem(`optivoya_cache_${key}`, JSON.stringify({
                    ts: Date.now(),
                    data: data
                }));
            } catch (e) { }
        }
    };

    window.PlannerState = PlannerState;
})();
