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
                "Open-Meteo klímaadatok, Kiwi repülőjegy árak és megélhetési indexek összehasonlítása az egyéni prioritások alapján..."
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

            grid.innerHTML = state.destinations.map((dest, idx) => {
                const m = dest.metrics || {};
                return `
                    <div class="advisor-main-card dest-card-hover" style="background: var(--bg-surface); border: 1.5px solid var(--border-subtle); border-radius: 20px; padding: 22px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.25s ease; position: relative;">
                        <div>
                            <!-- FEJLÉC & RANG -->
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                                <div>
                                    <span style="font-size: 11px; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.5px;">#${dest.rank || (idx + 1)} CÉLÁLLOMÁS</span>
                                    <h3 style="font-size: 20px; font-weight: 900; color: var(--text-main); margin: 2px 0 0;">${dest.name}</h3>
                                    <div style="font-size: 13px; color: var(--text-secondary); font-weight: 600;">${dest.country}</div>
                                </div>
                                <div style="text-align: right; background: var(--accent-glow); padding: 6px 12px; border-radius: 14px; border: 1px solid rgba(37, 99, 235, 0.2);">
                                    <div style="font-size: 17px; font-weight: 900; color: var(--primary); font-family: var(--font-mono);">${Math.round(dest.score || 85)}/100</div>
                                    <div style="font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Illeszkedés</div>
                                </div>
                            </div>

                            <!-- METRIKA PILLS -->
                            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; font-size: 12px; font-weight: 600;">
                                <span style="background: var(--bg-surface-subtle); padding: 4px 10px; border-radius: 8px; border: 1px solid var(--border-subtle);">☀️ ${m.temp_formatted || '~24°C'}</span>
                                <span style="background: var(--bg-surface-subtle); padding: 4px 10px; border-radius: 8px; border: 1px solid var(--border-subtle);">✈️ ${m.flight_price_formatted || 'Kedvező ár'}</span>
                                <span style="background: var(--bg-surface-subtle); padding: 4px 10px; border-radius: 8px; border: 1px solid var(--border-subtle);">🛡️ Biztonság: ${Math.round(m.safety_raw || 60)}/100</span>
                                <span style="background: var(--bg-surface-subtle); padding: 4px 10px; border-radius: 8px; border: 1px solid var(--border-subtle);">💰 Étel / megélhetés: ${m.daily_cost_huf_formatted || m.daily_cost_formatted || '~16 000 Ft / nap'}</span>
                            </div>

                            <!-- INDOKLÁS -->
                            <div style="font-size: 12.5px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 18px; background: rgba(0,0,0,0.02); padding: 10px 12px; border-radius: 10px;">
                                ${dest.explanation || 'Kiváló időjárás és kedvező megélhetési költségek.'}
                            </div>
                        </div>

                        <!-- CTA BUTTON -->
                        <button type="button" class="btn btn-primary" onclick="Wizard.selectDestination(${idx})" style="width: 100%; padding: 12px 16px; font-size: 13.5px; font-weight: 700; display: flex; justify-content: space-between; align-items: center; border-radius: 12px;">
                            <span>🏆 ${dest.name} Kiválasztása & Járatok</span>
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
