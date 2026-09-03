/**
 * Optivoya — Master Planner Destinations Module
 * Handles destination search API, polling, climate/safety/cost card rendering, and selection.
 */

(function () {
    const PlannerDestinations = {
        async startPlanning() {
            const state = window.PlannerState;
            if (!state) return;

            if (!state.criteria_completed) {
                if (window.PlannerIntake) window.PlannerIntake.openDecisionDNA();
                return;
            }

            // Invariant: Changing preferences and starting a new search clears all subsequent steps (Destinations, Flights, Stays)
            state.destinations = [];
            state.selectedDest = null;
            state.flights = [];
            state.selectedFlight = null;
            state.stays = [];
            state.selectedStay = null;

            if (window.TripCart) {
                const trip = window.TripCart.getTrip();
                trip.destination = null;
                trip.flight.selected_flight = null;
                trip.flight.shortlist = [];
                trip.accommodation.selected_accommodation = null;
                trip.accommodation.shortlist = [];
                trip.status = 'initialized';
                window.TripCart.saveTrip(trip);
            }

            // Invalidate flight & stay session caches
            try {
                Object.keys(sessionStorage).forEach(k => {
                    if (k.startsWith('optivoya_cache_')) {
                        sessionStorage.removeItem(k);
                    }
                });
            } catch (e) { }

            const stayTypeBoxes = document.querySelectorAll('input[name="stay_types"]:checked');
            const selectedStayTypes = Array.from(stayTypeBoxes).map(cb => cb.value);

            const amenityBoxes = document.querySelectorAll('input[name="amenities"]:checked');
            const selectedAmenities = Array.from(amenityBoxes).map(cb => cb.value);

            let durationVal = 7;
            if (state.date_mode === 'month') {
                durationVal = parseInt(document.getElementById('month_duration_input')?.value || 7, 10);
            } else if (state.date_mode === 'interval') {
                durationVal = parseInt(document.getElementById('interval_max_stay_input')?.value || 7, 10);
            } else if (state.date_mode === 'exact') {
                const d1 = new Date(document.getElementById('exact_out_date')?.value || '2026-09-10');
                const d2 = new Date(document.getElementById('exact_in_date')?.value || '2026-09-17');
                durationVal = Math.max(1, Math.round((d2 - d1) / (1000 * 60 * 60 * 24)));
            }

            state.intake = {
                origin: document.getElementById('origin')?.value || "Budapest (BUD)",
                adults: parseInt(document.getElementById('adults_count')?.value || 2, 10),
                children: parseInt(document.getElementById('children_count')?.value || 0, 10),
                date_mode: state.date_mode,
                year: parseInt(document.getElementById('intake_year')?.value || new Date().getFullYear(), 10),
                month: document.getElementById('intake_month')?.value || String(new Date().getMonth() + 1),
                duration: durationVal,
                exact_out_date: document.getElementById('exact_out_date')?.value || "2026-09-10",
                exact_in_date: document.getElementById('exact_in_date')?.value || "2026-09-17",
                out_from: document.getElementById('interval_out_from')?.value || "2026-09-01",
                out_to: document.getElementById('interval_out_to')?.value || "2026-09-15",
                in_from: document.getElementById('interval_in_from')?.value || "2026-09-08",
                in_to: document.getElementById('interval_in_to')?.value || "2026-09-30",
                min_stay: parseInt(document.getElementById('interval_min_stay_input')?.value || 5, 10),
                max_stay: parseInt(document.getElementById('interval_max_stay_input')?.value || 10, 10),
                target_temp: 24.0,
                min_safety: 50,
                preferred_regions: ["europe_south", "europe_west", "europe_central"],
                flight_direct_only: parseInt(document.getElementById('intake_flight_stops')?.value, 10) === 0,
                flight_max_stops: parseInt(document.getElementById('intake_flight_stops')?.value, 10) || 1,
                preferred_departure_time: state.intake.has_departure_pref ? (state.intake.departure_hour < 12 ? 'morning' : (state.intake.departure_hour < 18 ? 'afternoon' : 'evening')) : 'any',
                max_flight_duration_h: parseFloat(document.getElementById('intake_max_flight_duration')?.value) || 0,
                hotel_min_stars: parseInt(document.getElementById('intake_hotel_stars')?.value, 10) || 3,
                hotel_min_rating: parseFloat(document.getElementById('intake_hotel_rating')?.value) || 7.5,
                hotel_types: selectedStayTypes.length > 0 ? selectedStayTypes : ["hotel", "apartment", "resort", "guesthouse"],
                breakfast: document.getElementById('intake_breakfast')?.checked || false,
                amenities: selectedAmenities,
                ahp_weights: state.intake.ahp_weights,
                stay_weights: state.intake.stay_weights
            };

            state.showLoader(
                "Célállomások Kiértékelése és Rangsorolása",
                "Éghajlati adatok, repülőjegy árak és megélhetési indexek összehasonlítása az egyéni prioritások alapján..."
            );

            try {
                await fetch('/api/planner/init-destinations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(state.intake)
                });

                if (state.pollInterval) clearInterval(state.pollInterval);
                state.pollInterval = setInterval(this.pollDestinations.bind(this), 1200);
            } catch (e) {
                alert("Hiba a keresés indításakor: " + e.message);
                state.setStep(0);
            }
        },

        async pollDestinations() {
            const state = window.PlannerState;
            if (!state) return;

            try {
                const res = await fetch('/api/planner/destinations-status');
                const data = await res.json();

                const pBar = document.getElementById('wizardProgressBar');
                const pSub = document.getElementById('wizardLoadingSubtitle');

                if (data.status === 'running') {
                    if (pBar) pBar.style.width = (data.progress || 30) + '%';
                    if (pSub && data.status_text) pSub.innerText = data.status_text;
                } else if (data.status === 'done') {
                    clearInterval(state.pollInterval);
                    if (pBar) pBar.style.width = '100%';

                    state.destinations = data.results || [];
                    if (window.PlannerIntake) window.PlannerIntake.updateDecisionDNACard();
                    this.renderDestinations();
                    state.setStep(1);

                } else if (data.status === 'error') {
                    clearInterval(state.pollInterval);
                    alert("Hiba történt a kalkuláció során: " + (data.error || 'Ismeretlen hiba'));
                    state.setStep(0);
                }
            } catch (e) {
                console.error("Poll error:", e);
            }
        },

        renderDestinations() {
            const state = window.PlannerState;
            const grid = document.getElementById('destinationsGrid');
            if (!grid || !state) return;

            if (state.destinations.length === 0) {
                grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">Nem találtunk a szigorú feltételeknek megfelelő célállomást. Kérlek engedékenyebb szűrőket állíts be!</div>`;
                return;
            }

            // User target temperature
            const targetTemp = parseFloat(state.intake?.target_temp || 24.0);

            // Compute cohort distribution statistics (mean, std) for relative Z-score calculation
            const computeCohortStats = (arr) => {
                const valid = arr.filter(v => typeof v === 'number' && !isNaN(v));
                if (valid.length === 0) return { mean: 0, std: 0, count: 0 };
                const mean = valid.reduce((a, b) => a + b, 0) / valid.length;
                const variance = valid.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / valid.length;
                return { mean, std: Math.sqrt(variance), count: valid.length };
            };

            const tempDiffs = state.destinations.map(d => {
                const t = d.metrics?.temp_raw ?? d.metrics?.temp_celsius;
                return (t !== null && t !== undefined) ? Math.abs(t - targetTemp) : null;
            });
            const flightPrices = state.destinations.map(d => d.metrics?.flight_price_raw || d.metrics?.flight_price_huf || null);
            const safetyScores = state.destinations.map(d => d.metrics?.safety_raw ?? d.metrics?.safety ?? null);
            const dailyCosts = state.destinations.map(d => d.metrics?.daily_cost_raw_huf || ((d.metrics?.daily_cost_raw || 35) * 400));
            const scores = state.destinations.map(d => d.score ?? null);

            const tempStats = computeCohortStats(tempDiffs);
            const flightStats = computeCohortStats(flightPrices);
            const safetyStats = computeCohortStats(safetyScores);
            const costStats = computeCohortStats(dailyCosts);
            const scoreStats = computeCohortStats(scores);

            // Returns color-coded style based on relative standing (Z-score) within the returned cohort
            const getRelativeStyle = (val, stats, higherIsBetter = false) => {
                if (val === null || val === undefined || isNaN(val)) {
                    return {
                        color: 'var(--text-main)',
                        bg: 'var(--bg-surface-subtle)',
                        border: 'var(--border-subtle)'
                    };
                }
                // Fallback for uniform distribution or single result
                if (stats.count <= 1 || stats.std < 0.001) {
                    return {
                        color: '#16a34a',
                        bg: 'rgba(22, 163, 74, 0.08)',
                        border: 'rgba(22, 163, 74, 0.25)'
                    };
                }
                const z = (val - stats.mean) / stats.std;
                // ±0.35 Z-score splits cohort into roughly top 33%, middle 33%, bottom 33%
                const isGood = higherIsBetter ? (z >= 0.35) : (z <= -0.35);
                const isBad = higherIsBetter ? (z <= -0.35) : (z >= 0.35);

                if (isGood) {
                    return {
                        color: '#16a34a',
                        bg: 'rgba(22, 163, 74, 0.08)',
                        border: 'rgba(22, 163, 74, 0.25)'
                    };
                } else if (isBad) {
                    return {
                        color: '#dc2626',
                        bg: 'rgba(220, 38, 38, 0.08)',
                        border: 'rgba(220, 38, 38, 0.25)'
                    };
                } else {
                    return {
                        color: '#d97706',
                        bg: 'rgba(217, 119, 6, 0.08)',
                        border: 'rgba(217, 119, 6, 0.25)'
                    };
                }
            };

            const pillStyle = (styleObj) =>
                `background: ${styleObj.bg}; color: ${styleObj.color}; border: 1px solid ${styleObj.border}; padding: 5px 11px; border-radius: 8px; display: inline-flex; align-items: center; gap: 5px; font-size: 12px; font-weight: 600;`;

            grid.innerHTML = state.destinations.map((dest, idx) => {
                const m = dest.metrics || {};

                // Relative evaluation for each metric:
                const tempRaw = m.temp_raw ?? m.temp_celsius ?? null;
                const tempDiff = (tempRaw !== null && tempRaw !== undefined) ? Math.abs(tempRaw - targetTemp) : null;
                const tempStyle = getRelativeStyle(tempDiff, tempStats, false); // Lower distance to target temp is better

                const flightRaw = m.flight_price_raw || m.flight_price_huf || null;
                const flightStyle = getRelativeStyle(flightRaw, flightStats, false); // Lower flight price is better

                const safetyRaw = m.safety_raw ?? m.safety ?? null;
                const safetyStyle = getRelativeStyle(safetyRaw, safetyStats, true); // Higher safety is better

                const costRaw = m.daily_cost_raw_huf || ((m.daily_cost_raw || 35) * 400);
                const costStyle = getRelativeStyle(costRaw, costStats, false); // Lower daily cost is better

                const score = Math.round(dest.score || 85);
                const scoreStyle = getRelativeStyle(score, scoreStats, true);

                return `
                    <div class="advisor-main-card dest-card-hover" style="background: var(--bg-surface); border: 1.5px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 22px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.25s ease; position: relative;">
                        <div>
                            <!-- FEJLÉC & RANG -->
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px;">
                                <div>
                                    <span style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">#${dest.rank || (idx + 1)} Célállomás</span>
                                    <h3 style="font-size: 20px; font-weight: 800; color: var(--text-main); margin: 2px 0 0;">${dest.name}</h3>
                                    <div style="font-size: 13px; color: var(--text-secondary); font-weight: 500;">${dest.country}</div>
                                </div>
                                <div style="text-align: right; background: ${scoreStyle.bg}; padding: 7px 13px; border-radius: var(--radius-md); border: 1px solid ${scoreStyle.border}; flex-shrink: 0; margin-left: 12px;">
                                    <div style="font-size: 18px; font-weight: 800; color: ${scoreStyle.color}; font-family: var(--font-mono);">${score}/100</div>
                                    <div style="font-size: 10px; font-weight: 700; color: ${scoreStyle.color}; text-transform: uppercase; opacity: 0.85;">Illeszkedés</div>
                                </div>
                            </div>

                            <!-- RELATIVE COLOR-CODED METRIC PILLS -->
                            <div style="display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 14px;">
                                <span style="${pillStyle(tempStyle)}" title="Hőmérséklet a célállomáson (eltérés a preferált ${targetTemp}°C-hoz)">
                                    <span class="material-symbols-outlined" style="font-size: 14px;">wb_sunny</span>
                                    ${m.temp_formatted || (tempRaw !== null ? Math.round(tempRaw) + '°C' : '~24°C')}
                                </span>
                                <span style="${pillStyle(flightStyle)}" title="Repülőjegy ár a mezőny többi célállomásához viszonyítva">
                                    <span class="material-symbols-outlined" style="font-size: 14px;">flight</span>
                                    ${m.flight_price_formatted || 'Kedvező ár'}
                                </span>
                                <span style="${pillStyle(safetyStyle)}" title="Biztonsági index a mezőnyhöz viszonyítva">
                                    <span class="material-symbols-outlined" style="font-size: 14px;">shield</span>
                                    Biztonság: ${safetyRaw !== null ? Math.round(safetyRaw) : 60}/100
                                </span>
                                <span style="${pillStyle(costStyle)}" title="Napi megélhetési költségek a többi úti célhoz mérve">
                                    <span class="material-symbols-outlined" style="font-size: 14px;">payments</span>
                                    ${m.daily_cost_huf_formatted || m.daily_cost_formatted || '~16 000 Ft/nap'}
                                </span>
                            </div>

                            <!-- INDOKLÁS -->
                            <div style="font-size: 12.5px; color: var(--text-secondary); line-height: 1.55; margin-bottom: 18px; background: var(--bg-surface-subtle); padding: 10px 13px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
                                ${dest.explanation || 'Kiváló időjárás és kedvező megélhetési költségek.'}
                            </div>
                        </div>

                        <!-- CTA BUTTON -->
                        <button type="button" class="btn btn-primary" onclick="Wizard.selectDestination(${idx})" style="width: 100%; padding: 12px 16px; font-size: 13.5px; font-weight: 600; display: flex; justify-content: space-between; align-items: center; border-radius: var(--radius-md);">
                            <span>${dest.name} — Járatok keresése</span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <line x1="5" y1="12" x2="19" y2="12"></line>
                                <polyline points="12 5 19 12 12 19"></polyline>
                            </svg>
                        </button>
                    </div>
                `;
            }).join('');
        },


        async selectDestination(index) {
            const state = window.PlannerState;
            if (!state) return;
            const dest = state.destinations[index];
            if (!dest) return;

            state.selectedDest = dest;
            state.flights = [];
            state.selectedFlight = null;
            state.stays = [];
            state.selectedStay = null;

            if (window.TripCart) {
                window.TripCart.setDestination({
                    name: dest.name,
                    city: dest.city || dest.name,
                    country: dest.country,
                    region: dest.region,
                    rank: dest.rank,
                    score: dest.score,
                    duration: state.intake.duration,
                    adults: state.intake.adults,
                    children: state.intake.children,
                    origin: state.intake.origin,
                    daily_cost_eur: dest.metrics?.daily_cost_raw || 35.0,
                    flight_price_huf: dest.metrics?.flight_price_raw || 45000,
                    numbeo: dest.metrics?.numbeo_breakdown || {}
                });
            }

            if (window.PlannerFlights) {
                await window.PlannerFlights.triggerFlightSearch(dest);
            }
        },

        recalculateDestinations() {
            const state = window.PlannerState;
            if (!state) return;
            const tempInput = document.getElementById('mod_temp');
            const safetyInput = document.getElementById('mod_safety');
            if (tempInput) state.intake.target_temp = parseFloat(tempInput.value) || 24.0;
            if (safetyInput) state.intake.min_safety = parseInt(safetyInput.value, 10) || 50;
            this.startPlanning();
        }
    };

    window.PlannerDestinations = PlannerDestinations;
})();
