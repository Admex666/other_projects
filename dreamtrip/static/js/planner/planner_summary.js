/**
 * Optivoya — Master Planner Summary & Session Resume Module
 * Handles step 4 final trip summary view, proposal export, and auto-resuming from TripCart.
 */

(function () {
    const PlannerSummary = {
        renderFinalSummary() {
            const state = window.PlannerState;
            const cartTrip = window.TripCart ? window.TripCart.getTrip() : null;
            if (!state) return;

            const d = state.selectedDest || cartTrip?.destination;
            const f = state.selectedFlight || cartTrip?.flight?.selected_flight || cartTrip?.flight;
            const s = state.selectedStay || cartTrip?.accommodation?.selected_accommodation || cartTrip?.accommodation;

            // 1. Dátumok & éjszakák
            const outDate = (f?.out_date || f?.out_dep_time || state.intake.exact_out_date || '').split('T')[0];
            const inDate = (f?.in_date || f?.in_dep_time || state.intake.exact_in_date || '').split('T')[0];
            const nights = f?.exact_stay_nights || f?.stay_days || f?.nights || s?.nights || state.intake.duration || 7;
            const adults = state.intake.adults || cartTrip?.input?.adults || 2;

            const subEl = document.getElementById('summarySubtitle');
            if (subEl) {
                subEl.innerText = `${d?.name || d?.city || 'Célállomás'} utazás • ${adults} felnőtt • ${nights} éjszaka ${outDate ? `(${outDate} – ${inDate})` : ''}`;
            }

            // 2. Célállomás kártya
            const sumDestName = document.getElementById('sumDestName');
            if (sumDestName) sumDestName.innerText = `${d?.name || d?.city || ''}${d?.country ? ', ' + d.country : ''}`;
            const avgTemp = d?.metrics?.temp_avg || d?.temp_avg || 24;
            const safetyScore = Math.round(d?.metrics?.safety_raw || d?.safety_score || d?.numbeo?.safety_index || 60);
            const sumDestClimate = document.getElementById('sumDestClimate');
            if (sumDestClimate) sumDestClimate.innerText = `Nappal: ~${avgTemp}°C • Biztonság: ${safetyScore}/100`;

            // 3. Repülő kártya
            const airline = f?.airline || f?.out_airline || f?.in_airline || f?.carrier || 'Repülőjárat';
            const stopsCount = (f?.out_stops !== undefined) ? f.out_stops : ((f?.stops !== undefined) ? f.stops : 0);
            const stopsText = stopsCount === 0 ? 'Közvetlen járat' : `${stopsCount} átszállás`;
            const flightPrice = Math.round(f?.total_price_huf || f?.price_total_huf || f?.price_huf || f?.price || 0);

            const sumFlightAirline = document.getElementById('sumFlightAirline');
            const sumFlightDates = document.getElementById('sumFlightDates');
            const sumFlightPrice = document.getElementById('sumFlightPrice');
            if (sumFlightAirline) sumFlightAirline.innerText = `${airline} Retúr`;
            if (sumFlightDates) sumFlightDates.innerText = `${outDate || 'Időpont'} – ${inDate || 'Időpont'} • ${stopsText}`;
            if (sumFlightPrice) sumFlightPrice.innerText = `${flightPrice.toLocaleString()} Ft`;

            // 4. Szállás kártya
            const stayStars = s?.stars || s?.stars_raw || 4;
            const stayRating = s?.rating_score ? (s.rating_score > 10 ? (s.rating_score / 10).toFixed(1) : s.rating_score) : (s?.rating || 8.8);
            const stayPrice = Math.round(s?.price_total_huf || s?.price_huf || s?.price || 120000);

            const sumStayName = document.getElementById('sumStayName');
            const sumStayRating = document.getElementById('sumStayRating');
            const sumStayPrice = document.getElementById('sumStayPrice');
            if (sumStayName) sumStayName.innerText = `${s?.name || 'Szálloda'} ${'★'.repeat(stayStars)}`;
            if (sumStayRating) sumStayRating.innerText = `${nights} éjszaka • Értékelés: ${stayRating}/10`;
            if (sumStayPrice) sumStayPrice.innerText = `${stayPrice.toLocaleString()} Ft`;

            // 5. Tételes költségkalkuláció blokk
            const wrap = document.getElementById('sumBreakdownWrap');
            if (wrap && window.TripCart) {
                const b = window.TripCart.calculateBreakdown();
                wrap.innerHTML = `
                    <div style="background: var(--bg-surface-subtle); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 24px; margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <h3 style="font-size: 16px; font-weight: 800; color: var(--text-main); margin: 0;">Tételes Költségkalkuláció</h3>
                            <span style="font-size: 12px; font-weight: 700; color: var(--primary);">${b.days} nap / ${b.totalPersons} fő</span>
                        </div>

                        <div style="display: flex; flex-direction: column; gap: 12px;">
                            ${b.items.map(it => `
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: var(--bg-surface); border-radius: 10px; font-size: 13px;">
                                    <div>
                                        <strong>${it.name}</strong><br>
                                        <small style="color: var(--text-muted); font-family: monospace;">${it.formula}</small>
                                    </div>
                                    <div style="font-weight: 800; font-family: var(--font-mono); font-size: 14px; color: var(--text-main);">${it.amount.toLocaleString()} Ft</div>
                                </div>
                            `).join('')}
                        </div>

                        <div style="margin-top: 20px; padding: 18px; background: #0f172a; color: #ffffff; border-radius: 14px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #94a3b8;">Becsült Teljes Utazási Költség</div>
                                <div style="font-size: 28px; font-weight: 900; color: #38bdf8; font-family: var(--font-mono);">${b.totalHuf.toLocaleString()} Ft</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 14px; font-weight: 700; color: #e2e8f0;">~${b.perPersonTotal.toLocaleString()} Ft / fő</div>
                                <div style="font-size: 11px; color: #94a3b8;">(${b.totalPersons} utazóra összesen)</div>
                            </div>
                        </div>
                    </div>
                `;
            }
        },

        exportProposal() {
            if (window.TripCart) {
                window.TripCart.exportProposal();
            }
        },

        async resumeSessionFromCart() {
            const state = window.PlannerState;
            if (!window.TripCart || !state) return;
            const trip = window.TripCart.getTrip();
            if (!trip || (!trip.destination && !trip.flight?.selected_flight && !trip.accommodation?.selected_accommodation)) {
                return;
            }

            const urlParams = new URLSearchParams(window.location.search);
            const resumeMode = urlParams.get('resume');

            if (trip.input) {
                if (trip.input.origin) state.intake.origin = trip.input.origin;
                if (trip.input.adults) state.intake.adults = trip.input.adults;
                if (trip.input.children) state.intake.children = trip.input.children;
                if (trip.input.duration_days) state.intake.duration = trip.input.duration_days;
                if (trip.input.date_mode) state.intake.date_mode = trip.input.date_mode;
            }

            // 1. Destination
            if (trip.destination) {
                state.selectedDest = trip.destination;
                const destName = trip.destination.name || trip.destination.city;
                const flightCity = document.getElementById('flightContextCity');
                const flightDetails = document.getElementById('flightContextDetails');
                if (flightCity) flightCity.innerText = destName;
                if (flightDetails) flightDetails.innerText = `${state.intake.origin} → ${destName} • ${state.intake.adults} felnőtt • ${state.intake.duration} nap`;
                const stayCity = document.getElementById('stayContextCity');
                if (stayCity) stayCity.innerText = destName;
            }

            // 2. Flight
            if (trip.flight?.selected_flight) {
                state.selectedFlight = trip.flight.selected_flight;
                const fl = trip.flight.selected_flight;
                const stayFl = document.getElementById('stayContextFlight');
                if (stayFl) stayFl.innerText = `${fl.airline || 'Járat'} (${fl.out_date} – ${fl.in_date} · ${fl.exact_stay_nights || state.intake.duration} éj)`;
                const stayNights = document.getElementById('stayNightsCount');
                if (stayNights) stayNights.innerText = fl.exact_stay_nights || state.intake.duration;
            }

            // 3. Stay
            if (trip.accommodation?.selected_accommodation) {
                state.selectedStay = trip.accommodation.selected_accommodation;
            }

            const isExplicitChangeFlight = urlParams.get('change') === 'flight';
            
            // Csak akkor ugrunk automatikusan lépésre, ha a felhasználó kifejezetten a folytatásra kattintott (?resume=...)
            if (!resumeMode && !isExplicitChangeFlight) {
                // Alapesetben a 0. lépésen (Preferenciák) indulunk tiszta lappal
                state.setStep(0);
                return;
            }

            let targetResume = resumeMode;
            if (targetResume === 'flight' && trip.flight?.selected_flight && !isExplicitChangeFlight) {
                if (trip.accommodation?.selected_accommodation) {
                    targetResume = 'summary';
                } else {
                    targetResume = 'stay';
                }
            }

            if (targetResume === 'summary' && trip.destination && trip.flight?.selected_flight && trip.accommodation?.selected_accommodation) {
                this.renderFinalSummary();
                state.setStep(4);
            } else if (targetResume === 'stay' && trip.destination && trip.flight?.selected_flight) {
                if (state.stays.length === 0 && state.selectedFlight) {
                    await window.PlannerStays.triggerStaySearch(state.selectedFlight);

                } else {
                    window.PlannerStays.renderStays();
                    state.setStep(3);
                }
            } else if (targetResume === 'flight' && trip.destination) {
                if (state.flights.length === 0 && state.selectedDest) {
                    await window.PlannerFlights.triggerFlightSearch(state.selectedDest);
                } else {
                    window.PlannerFlights.renderFlights();
                    state.setStep(2);
                }
            }
        }
    };

    window.PlannerSummary = PlannerSummary;
})();
