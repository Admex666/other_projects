/**
 * Optivoya — Master Planner Flights Module
 * Handles Kiwi flight search API, time/date formatters, heatmap percentiles, card rendering, and selection.
 */

(function () {
    function formatFlightTime(raw) {
        if (!raw) return '--:--';
        const str = String(raw).trim();
        const parts = str.includes('T') ? str.split('T') : str.split(' ');
        if (parts.length > 1) return parts[1].slice(0, 5);
        if (str.includes(':')) return str.slice(0, 5);
        return str;
    }

    function formatFlightDate(raw) {
        if (!raw) return '';
        const str = String(raw).trim().split('T')[0].split(' ')[0];
        const parts = str.split('-');
        if (parts.length === 3) {
            const months = ['jan.', 'febr.', 'márc.', 'ápr.', 'máj.', 'jún.', 'júl.', 'aug.', 'szept.', 'okt.', 'nov.', 'dec.'];
            const mIdx = parseInt(parts[1], 10) - 1;
            const mName = months[mIdx] || parts[1];
            return `${parts[0]}. ${mName} ${parseInt(parts[2], 10)}.`;
        }
        return str;
    }

    function formatFlightDuration(hours) {
        if (!hours && hours !== 0) return '';
        const h = Math.floor(hours);
        const m = Math.round((hours - h) * 60);
        return `${h}ó ${m}p`;
    }

    function getPercentileStyle(val, minVal, maxVal, lowerIsBetter = true) {
        if (minVal === maxVal || isNaN(val)) {
            return { bg: 'rgba(16, 185, 129, 0.12)', text: '#059669', border: 'rgba(16, 185, 129, 0.25)', label: 'Kiváló' };
        }
        const ratio = lowerIsBetter ? (val - minVal) / (maxVal - minVal) : (maxVal - val) / (maxVal - minVal);
        
        if (ratio <= 0.28) {
            return { bg: 'rgba(16, 185, 129, 0.14)', text: '#059669', border: 'rgba(16, 185, 129, 0.3)', label: 'Top 25% (Legjobb)' };
        } else if (ratio <= 0.65) {
            return { bg: 'rgba(245, 158, 11, 0.14)', text: '#d97706', border: 'rgba(245, 158, 11, 0.3)', label: 'Átlagos mezőny' };
        } else {
            return { bg: 'rgba(239, 68, 68, 0.14)', text: '#dc2626', border: 'rgba(239, 68, 68, 0.3)', label: 'Magasabb érték' };
        }
    }

    const PlannerFlights = {
        async triggerFlightSearch(dest, forceRefresh = false) {
            const state = window.PlannerState;
            if (!dest || !state) return;
            state.selectedDest = dest;
            const destName = dest.name || dest.city;

            const fCity = document.getElementById('flightContextCity');
            const fDetails = document.getElementById('flightContextDetails');
            if (fCity) fCity.innerText = destName;
            if (fDetails) fDetails.innerText = `${state.intake.origin} → ${destName} • ${state.intake.adults} felnőtt • ${state.intake.duration} nap`;

            const cacheKey = `fl_${destName}_${state.intake.origin}_${state.intake.date_mode}_${state.intake.exact_out_date}_${state.intake.exact_in_date}_${state.intake.out_from}_${state.intake.out_to}_${state.intake.in_to}_${state.intake.min_stay}_${state.intake.max_stay}_${state.intake.adults}_${state.intake.flight_direct_only}_${state.intake.flight_max_stops}_${state.intake.preferred_departure_time}_${JSON.stringify(state.intake.ahp_weights || {})}_${JSON.stringify(state.intake.promethee_params || {})}`;

            if (!forceRefresh) {
                const cached = state.getSessionCache(cacheKey);
                if (cached && cached.length > 0) {
                    state.flights = cached;
                    this.renderFlights();
                    state.setStep(2);
                    return;
                }
            }

            state.showLoader(
                `Járatok keresése (${destName})...`,
                `Kiwi retúr járatok aggregálása (${state.intake.origin} → ${destName}) és intelligens rangsorolása...`
            );

            try {
                const res = await fetch('/api/planner/search-flights', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        origin: state.intake.origin,
                        destination: destName,
                        date_mode: state.intake.date_mode,
                        month: parseInt(state.intake.month, 10) || (new Date().getMonth() + 1),
                        year: state.intake.year || parseInt(document.getElementById('intake_year')?.value, 10) || new Date().getFullYear(),
                        duration: state.intake.duration,
                        exact_out_date: state.intake.exact_out_date,
                        exact_in_date: state.intake.exact_in_date,
                        out_from: state.intake.out_from,
                        out_to: state.intake.out_to,
                        in_from: state.intake.in_from || null,
                        in_to: state.intake.in_to,
                        min_stay: state.intake.min_stay,
                        max_stay: state.intake.max_stay,
                        adults: state.intake.adults,
                        children: state.intake.children,
                        direct_only: state.intake.flight_direct_only,
                        max_stops: state.intake.flight_max_stops,
                        departure_pref: state.intake.preferred_departure_time,
                        max_duration_h: state.intake.max_flight_duration_h,
                        weights: state.intake.ahp_weights,
                        promethee_params: state.intake.promethee_params
                    })
                });

                const data = await res.json();
                if (data.status === 'ok') {
                    state.flights = data.flights || [];
                    state.setSessionCache(cacheKey, state.flights);
                    this.renderFlights();
                    state.setStep(2);
                } else {
                    alert("Nem sikerült járatokat találni: " + (data.error || 'Hiba'));
                    state.setStep(1);
                }
            } catch (e) {
                alert("Járatkeresési hiba: " + e.message);
                state.setStep(1);
            }
        },

        renderFlights() {
            const state = window.PlannerState;
            const container = document.getElementById('flightsGrid');
            if (!container || !state) return;

            if (state.flights.length === 0) {
                container.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--text-secondary); background: var(--bg-surface); border-radius: 16px; border: 1px dashed var(--border-subtle);">Nem találtunk járatot a megadott szigorú feltételekkel. Kérlek módosíts az átszállás tolerancián a fenti menüben!</div>`;
                return;
            }

            const originCity = state.intake.origin || 'Budapest';
            const destCity = state.selectedDest?.name || state.selectedDest?.city || 'Célállomás';

            const allPrices = state.flights.map(f => f.total_price_huf || f.price_huf || 0).filter(p => p > 0);
            const minPrice = allPrices.length ? Math.min(...allPrices) : 0;
            const maxPrice = allPrices.length ? Math.max(...allPrices) : 0;

            const allDurs = state.flights.map(f => (f.out_duration_h || 0) + (f.in_duration_h || 0)).filter(d => d > 0);
            const minDur = allDurs.length ? Math.min(...allDurs) : 0;
            const maxDur = allDurs.length ? Math.max(...allDurs) : 0;

            container.innerHTML = state.flights.map((fl, idx) => {
                const outDepTime = formatFlightTime(fl.out_dep_time);
                const outArrTime = formatFlightTime(fl.out_arr_time);
                const outDate = formatFlightDate(fl.out_dep_time || fl.out_date);
                const outArrDate = formatFlightDate(fl.out_arr_time || fl.out_dep_time);
                const outDur = formatFlightDuration(fl.out_duration_h);

                const inDepTime = formatFlightTime(fl.in_dep_time);
                const inArrTime = formatFlightTime(fl.in_arr_time);
                const inDate = formatFlightDate(fl.in_dep_time || fl.in_date);
                const inArrDate = formatFlightDate(fl.in_arr_time || fl.in_dep_time);
                const inDur = formatFlightDuration(fl.in_duration_h);

                const outDepAirport = fl.out_dep_airport || (originCity.includes('(') ? originCity.split('(')[1].replace(')', '') : 'BUD');
                const outArrAirport = fl.out_arr_airport || (destCity.length <= 4 ? destCity : destCity.slice(0, 3).toUpperCase());
                const inDepAirport = fl.in_dep_airport || outArrAirport;
                const inArrAirport = fl.in_arr_airport || outDepAirport;

                const airline = fl.out_carriers || fl.out_airline || fl.in_carriers || fl.in_airline || 'Légitársaság';
                const nights = fl.stay_days || fl.exact_stay_nights || state.intake.duration || 7;
                const priceTotal = fl.total_price_huf || fl.price_total_huf || fl.price_huf || 0;
                const adults = Math.max(1, state.intake.adults || 1);
                const pricePerPerson = Math.round(priceTotal / adults);
                const relevancePct = fl.relevance_pct || Math.round((fl.phi_net !== undefined ? (fl.phi_net + 1) / 2 : 0.85) * 100);
                const isTop = idx === 0;
                const stayDiff = fl.stay_diff_days !== undefined ? fl.stay_diff_days : 0;
                const stayFitText = stayDiff === 0 ? 'Tökéletes időtartam' : `±${stayDiff} nap eltérés`;

                const totalDur = (fl.out_duration_h || 0) + (fl.in_duration_h || 0);
                const priceHeatmap = getPercentileStyle(priceTotal, minPrice, maxPrice, true);
                const relevanceHeatmap = relevancePct >= 80 
                    ? { bg: 'rgba(16, 185, 129, 0.15)', text: '#059669', border: 'rgba(16, 185, 129, 0.3)' }
                    : (relevancePct >= 65 ? { bg: 'rgba(245, 158, 11, 0.15)', text: '#d97706', border: 'rgba(245, 158, 11, 0.3)' } : { bg: 'rgba(100, 116, 139, 0.15)', text: '#64748b', border: 'rgba(100, 116, 139, 0.3)' });

                return `
                    <div class="planner-flight-card ${isTop ? 'top-match' : ''}">
                        <div class="flight-card-header">
                            <div class="flight-carrier-badge-wrap">
                                <span class="flight-carrier-name">✈️ ${airline}</span>
                                <span class="flight-rank-badge ${isTop ? 'top-rank' : ''}">
                                    #${fl.rank || (idx + 1)} Ajánlat
                                </span>
                                <span class="flight-relevance-pill" style="background: ${relevanceHeatmap.bg}; color: ${relevanceHeatmap.text}; border: 1px solid ${relevanceHeatmap.border}; font-weight: 800;">
                                    ⭐ ${relevancePct}% Prioritás Illeszkedés
                                </span>
                            </div>
                            <div class="flight-stay-badge" title="${stayFitText}">
                                🌙 <strong>${nights} éjszaka</strong> · ${destCity} <span style="opacity: 0.75; font-size: 11px;">(${stayFitText})</span>
                            </div>
                        </div>

                        <div class="flight-card-body">
                            <div class="flight-segments-container">
                                <!-- ODAÚT -->
                                <div class="flight-segment-row">
                                    <div class="segment-tag tag-outbound">
                                        <span>🛫 Odaút</span>
                                    </div>
                                    <div class="segment-times-grid">
                                        <div class="flight-time-col dep">
                                            <span class="time-large">${outDepTime}</span>
                                            <span class="airport-code">${outDepAirport} (${originCity.split('(')[0].trim()})</span>
                                            <span class="date-sub">${outDate}</span>
                                        </div>

                                        <div class="flight-path-wrap">
                                            <span class="flight-duration">${outDur}</span>
                                            <div class="flight-line">
                                                <span class="line-dot"></span>
                                                <span class="line-bar"></span>
                                                <span class="line-plane">✈</span>
                                                <span class="line-bar"></span>
                                                <span class="line-dot"></span>
                                            </div>
                                            <span class="flight-stops ${fl.out_stops === 0 ? 'direct' : 'with-stops'}">
                                                ${fl.out_stops === 0 ? 'Közvetlen' : fl.out_stops + ' átszállás'}
                                            </span>
                                        </div>

                                        <div class="flight-time-col arr">
                                            <span class="time-large">${outArrTime}</span>
                                            <span class="airport-code">${outArrAirport} (${destCity.split('(')[0].trim()})</span>
                                            <span class="date-sub">${outArrDate}</span>
                                        </div>
                                    </div>
                                </div>

                                <!-- VISSZAÚT -->
                                <div class="flight-segment-row">
                                    <div class="segment-tag tag-inbound">
                                        <span>🛬 Visszaút</span>
                                    </div>
                                    <div class="segment-times-grid">
                                        <div class="flight-time-col dep">
                                            <span class="time-large">${inDepTime}</span>
                                            <span class="airport-code">${inDepAirport} (${destCity.split('(')[0].trim()})</span>
                                            <span class="date-sub">${inDate}</span>
                                        </div>

                                        <div class="flight-path-wrap">
                                            <span class="flight-duration">${inDur}</span>
                                            <div class="flight-line">
                                                <span class="line-dot"></span>
                                                <span class="line-bar"></span>
                                                <span class="line-plane" style="transform: scaleX(-1);">✈</span>
                                                <span class="line-bar"></span>
                                                <span class="line-dot"></span>
                                            </div>
                                            <span class="flight-stops ${fl.in_stops === 0 ? 'direct' : 'with-stops'}">
                                                ${fl.in_stops === 0 ? 'Közvetlen' : fl.in_stops + ' átszállás'}
                                            </span>
                                        </div>

                                        <div class="flight-time-col arr">
                                            <span class="time-large">${inArrTime}</span>
                                            <span class="airport-code">${inArrAirport} (${originCity.split('(')[0].trim()})</span>
                                            <span class="date-sub">${inArrDate}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="flight-pricing-cta-box">
                                <div class="flight-price-wrap">
                                    <div class="total-price-tag">${Math.round(priceTotal).toLocaleString()} Ft</div>
                                    <div class="per-person-tag">~${pricePerPerson.toLocaleString()} Ft / fő · ${adults} felnőtt</div>
                                    <div style="margin-top: 4px;">
                                        <span style="font-size: 10.5px; font-weight: 800; padding: 2px 7px; border-radius: 6px; background: ${priceHeatmap.bg}; color: ${priceHeatmap.text}; border: 1px solid ${priceHeatmap.border}; display: inline-block;">${priceHeatmap.label}</span>
                                    </div>
                                </div>
                                <button type="button" class="btn btn-primary select-flight-btn" onclick="Wizard.selectFlight(${idx})">
                                    <span>Járat Kiválasztása</span>
                                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                        <line x1="5" y1="12" x2="19" y2="12"></line>
                                        <polyline points="12 5 19 12 12 19"></polyline>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            // Proactive Background Prefetching: Stays for the top-ranked flight
            if (state.flights && state.flights.length > 0 && window.PlannerStays && window.PlannerStays.prefetchStays) {
                window.PlannerStays.prefetchStays(state.flights[0]);
            }
        },

        async selectFlight(index) {

            const state = window.PlannerState;
            if (!state) return;
            const fl = state.flights[index];
            if (!fl) return;

            state.selectedFlight = fl;
            state.stays = [];
            state.selectedStay = null;

            const outDate = (fl.out_dep_time || fl.out_date || '').split('T')[0];
            const inDate = (fl.in_dep_time || fl.in_date || '').split('T')[0];
            const nights = fl.stay_days || fl.exact_stay_nights || state.intake.duration;

            if (window.TripCart) {
                const flightPrice = fl.total_price_huf || fl.price_total_huf || fl.price_huf || 0;
                const stopsCount = (fl.out_stops !== undefined) ? fl.out_stops : ((fl.stops !== undefined) ? fl.stops : 0);
                window.TripCart.setFlight({
                    airline: fl.out_airline || fl.in_airline || fl.airline || 'Repülőjárat',
                    price_huf: flightPrice,
                    price_total_huf: flightPrice,
                    out_date: outDate,
                    in_date: inDate,
                    out_time: (fl.out_dep_time || fl.out_time || '').split('T')[1]?.slice(0, 5) || '',
                    in_time: (fl.in_dep_time || fl.in_time || '').split('T')[1]?.slice(0, 5) || '',
                    out_airport: fl.out_dep_airport || 'BUD',
                    in_airport: fl.out_arr_airport || '',
                    stops: stopsCount,
                    out_stops: stopsCount,
                    exact_stay_nights: nights,
                    stay_days: nights,
                    adults: state.intake.adults
                });
            }

            if (window.PlannerStays) {
                await window.PlannerStays.triggerStaySearch(fl);
            }
        },

        recalculateFlights() {
            const state = window.PlannerState;
            if (!state) return;
            const directCb = document.getElementById('mod_direct_only');
            if (directCb) state.intake.flight_direct_only = directCb.checked;

            state.selectedFlight = null;
            state.stays = [];
            state.selectedStay = null;

            if (window.TripCart) {
                const trip = window.TripCart.getTrip();
                trip.flight.selected_flight = null;
                trip.accommodation.selected_accommodation = null;
                trip.accommodation.shortlist = [];
                trip.status = 'destination_selected';
                window.TripCart.saveTrip(trip);
            }

            if (state.selectedDest) {
                this.triggerFlightSearch(state.selectedDest, true);
            }
        }
    };

    window.PlannerFlights = PlannerFlights;
})();
