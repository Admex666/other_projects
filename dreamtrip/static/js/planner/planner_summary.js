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

            // 1b. Unified TripScore calculation & banner rendering
            const destScore = d?.score || 75;
            const flightScore = f?.relevance_pct || 78;
            const stayScore = Math.min(99, (s?.rating || 8.8) * 10);
            const actsCount = (state.selectedActivities || []).length;
            const expScore = Math.min(98, 65 + (actsCount * 4));
            const effHours = f?.effective_vacation_hours || 16;
            
            const rawTripScore = (destScore * 0.25) + (flightScore * 0.25) + (stayScore * 0.25) + (expScore * 0.25);
            const finalTripScore = Math.round(Math.max(50, Math.min(99, rawTripScore)));
            
            const tsVal = document.getElementById('tripScoreValue');
            const tsTitle = document.getElementById('tripScoreTitle');
            const tsHigh = document.getElementById('tripScoreHighlights');
            const tsTime = document.getElementById('tripScoreEffectiveTime');
            
            if (tsVal) tsVal.innerText = `${finalTripScore}/100`;
            if (tsTime) tsTime.innerText = `+${Math.round(effHours)} óra hasznos idő`;
            if (tsTitle) {
                if (finalTripScore >= 88) tsTitle.innerText = "Kiemelkedő Összhang & Prémium Illeszkedés";
                else if (finalTripScore >= 78) tsTitle.innerText = "Kiváló Összhang & Kiegyensúlyozott Csomag";
                else tsTitle.innerText = "Jó Ár-Érték Arányú Utazási Terv";
            }
            if (tsHigh) {
                const highlights = [];
                if (d?.name) highlights.push(`${d.name} (${Math.round(destScore)}p desztináció)`);
                if (f?.airline || f?.out_airline) highlights.push(`${f.airline || f.out_airline} (${f.out_stops === 0 ? 'Közvetlen' : 'Átszállásos'})`);
                if (s?.name) highlights.push(`${s.name} (${s.rating || 8.5}★ szállás)`);
                if (actsCount > 0) highlights.push(`${actsCount} kiválasztott élmény`);
                tsHigh.innerText = highlights.join(' • ');
            }

            // Sync enriched TripScore & preferences to active trip store
            if (window.TripStore) {
                window.TripStore.setTripScore({
                    score: finalTripScore,
                    effective_vacation_hours: effHours,
                    title: tsTitle ? tsTitle.innerText : "Kiváló Összhang & Kiegyensúlyozott Csomag",
                    dest_score: destScore,
                    flight_score: flightScore,
                    stay_score: stayScore,
                    exp_score: expScore,
                    highlights: tsHigh ? tsHigh.innerText : ""
                });
                if (state.selectedActivities && state.selectedActivities.length > 0) {
                    window.TripStore.setActivities(state.selectedActivities);
                }
                if (state.intake?.experience_preferences || state.intake?.logistics_preferences) {
                    window.TripStore.setPreferences(state.intake.experience_preferences, state.intake.logistics_preferences);
                }
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

            // 4b. Programok & élmények kártya
            const acts = state.selectedActivities || (cartTrip?.activities?.selected_activities) || [];
            const sumActCount = document.getElementById('sumActivitiesCount');
            const sumActDuration = document.getElementById('sumActivitiesDuration');
            const sumActPrice = document.getElementById('sumActivitiesPrice');

            let totalActCostPerPerson = 0;
            acts.forEach(a => {
                const pl = String(a.price_level || '1').toLowerCase();
                if (pl === 'free' || pl === '0') totalActCostPerPerson += 0;
                else if (pl === 'budget' || pl === '1') totalActCostPerPerson += 2500;
                else if (pl === 'moderate' || pl === '2') totalActCostPerPerson += 6500;
                else if (pl === 'premium' || pl === '3' || pl === '4') totalActCostPerPerson += 18000;
                else totalActCostPerPerson += 3500;
            });
            const totalPersons = adults + (state.intake.children || cartTrip?.input?.children || 0);
            const totalActGroupCost = totalActCostPerPerson * totalPersons;

            if (sumActCount) sumActCount.innerText = `${acts.length} kiválasztott program`;
            if (sumActDuration) sumActDuration.innerText = acts.length > 0 ? `Napi ~${Math.max(2, Math.round(acts.length * 1.5 / Math.max(1, nights)))} óra aktív élmény` : 'Nincsenek rögzített programok';
            if (sumActPrice) sumActPrice.innerText = `${totalActGroupCost.toLocaleString()} Ft (~${totalActCostPerPerson.toLocaleString()} Ft / fő)`;

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

            // 6. Napi élmény útiterv betöltése és renderelése
            const destId = d?.dest_id || d?.id || 'IT_BARI';
            const persona = state.intake.dest_promethee?.experience?.persona || 'culture_aficionado';
            const personaSelect = document.getElementById('itineraryPersonaSelect');
            if (personaSelect) {
                personaSelect.value = persona;
            }
            this.loadItinerary(destId, nights, persona);
        },

        async loadItinerary(destId, days, persona) {
            const box = document.getElementById('itineraryContentBox');
            if (!box) return;

            let formattedDestId = String(destId).toUpperCase();
            if (!formattedDestId.includes('_') && formattedDestId.length > 3) {
                if (formattedDestId.includes('BARI')) formattedDestId = 'IT_BARI';
                else if (formattedDestId.includes('ROM')) formattedDestId = 'IT_ROME';
                else formattedDestId = 'IT_BARI';
            }

            box.innerHTML = `
                <div style="text-align: center; padding: 28px; color: var(--text-muted); font-size: 13.5px;">
                    <div style="display: inline-block; width: 28px; height: 28px; border: 3px solid var(--border-subtle); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 10px;"></div>
                    <div>Napi útiterv és sétaútvonalak generálása a desztináció élménygráfjából...</div>
                </div>
            `;

            try {
                const state = window.PlannerState;
                const numDays = Math.min(7, Math.max(1, parseInt(days, 10) || 3));
                const selectedIds = (state?.selectedActivities || []).map(a => a.entity_id).join(',');
                const queryParams = new URLSearchParams({
                    days: numDays,
                    persona: persona || 'culture_aficionado'
                });
                if (selectedIds) {
                    queryParams.set('selected_activities', selectedIds);
                }
                if (state?.intake?.logistics_preferences) {
                    const lp = state.intake.logistics_preferences;
                    if (lp.day_start) queryParams.set('day_start', lp.day_start);
                    if (lp.day_end) queryParams.set('day_end', lp.day_end);
                    if (lp.max_walking_minutes) queryParams.set('max_walk', lp.max_walking_minutes);
                }
                const res = await fetch(`/api/destinations/${encodeURIComponent(formattedDestId)}/itinerary?${queryParams.toString()}`);
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}`);
                }
                const data = await res.json();
                window.PlannerState.currentItinerary = data;
                window.PlannerState.activeItineraryDay = 0;
                this.renderItinerary(data, 0);
                if (window.TripStore) {
                    window.TripStore.setItinerary(data);
                }
            } catch (err) {
                console.warn("Could not load dynamic itinerary, rendering fallback:", err);
                box.innerHTML = `
                    <div style="text-align: center; padding: 20px; color: var(--text-secondary); font-size: 13px;">
                        A kiválasztott célállomáshoz a sétaútvonalak hamarosan elérhetők. 
                        Az alapvető látnivalók és gasztronómiai élmények a helyszínen rugalmasan felfedezhetők!
                    </div>
                `;
            }
        },

        reloadItineraryWithPersona(newPersona) {
            const state = window.PlannerState;
            const d = state.selectedDest || (window.TripCart ? window.TripCart.getTrip()?.destination : null);
            const nights = state.intake.duration || 3;
            const destId = d?.dest_id || d?.id || 'IT_BARI';
            this.loadItinerary(destId, nights, newPersona);
        },

        switchItineraryDay(dayIdx) {
            const state = window.PlannerState;
            if (!state.currentItinerary) return;
            state.activeItineraryDay = dayIdx;
            this.renderItinerary(state.currentItinerary, dayIdx);
        },

        renderItinerary(data, activeDayIdx = 0) {
            const box = document.getElementById('itineraryContentBox');
            if (!box || !data || !data.days || data.days.length === 0) return;

            const days = data.days;
            const safeDayIdx = Math.min(days.length - 1, Math.max(0, activeDayIdx));
            const currentDay = days[safeDayIdx];

            // 1. Day Tabs
            const tabsHtml = `
                <div class="itinerary-day-tabs">
                    ${days.map((d, idx) => {
                        const activeCls = idx === safeDayIdx ? 'active' : '';
                        return `
                            <button type="button" class="itinerary-day-tab ${activeCls}" onclick="window.PlannerSummary.switchItineraryDay(${idx})">
                                <span class="material-symbols-outlined" style="font-size: 16px;">calendar_today</span>
                                <span>${idx + 1}. Nap</span>
                                <span style="font-size: 11px; opacity: 0.8;">(${d.date || ''})</span>
                            </button>
                        `;
                    }).join('')}
                </div>
            `;

            // 2. Timeline Slots
            const slotsHtml = (currentDay.slots || []).map((slot) => {
                let icon = 'explore';
                let timeLabel = slot.time_window || '';
                
                if (slot.slot === 'morning') {
                    icon = 'wb_twilight';
                    timeLabel = 'Délelőtt • ' + timeLabel;
                } else if (slot.slot === 'lunch') {
                    icon = 'restaurant';
                    timeLabel = 'Ebédszünet • ' + timeLabel;
                } else if (slot.slot === 'afternoon') {
                    icon = 'attractions';
                    timeLabel = 'Délután • ' + timeLabel;
                } else if (slot.slot === 'sunset') {
                    icon = 'wb_twilight';
                    timeLabel = 'Naplemente • ' + timeLabel;
                } else if (slot.slot === 'dinner_evening') {
                    icon = 'nightlife';
                    timeLabel = 'Esti program • ' + timeLabel;
                }

                const rainSafeBadge = slot.weather_resilience === 'rain_safe' 
                    ? `<span class="itinerary-tag-pill itinerary-tag-rainsafe"><span class="material-symbols-outlined" style="font-size:13px;">umbrella</span> Esőbiztos</span>`
                    : `<span class="itinerary-tag-pill itinerary-tag-outdoor"><span class="material-symbols-outlined" style="font-size:13px;">wb_sunny</span> Szabadtéri</span>`;

                const priceBadge = slot.price_level 
                    ? `<span class="itinerary-tag-pill itinerary-tag-price">${slot.price_level === 'free' ? 'Ingyenes' : (slot.price_level === 'budget' ? 'Kedvező belépő' : 'Standard')}</span>`
                    : '';

                const ratingBadge = slot.rating 
                    ? `<span class="itinerary-tag-pill" style="background:rgba(245,158,11,0.12); color:#b45309; border:1px solid rgba(245,158,11,0.3); font-weight:800;">★ ${slot.rating.toFixed(1)}</span>`
                    : '';

                const walkDivider = (slot.walk_to_next_meters && slot.walk_to_next_meters > 0) ? `
                    <div class="itinerary-walk-divider">
                        <div class="itinerary-walk-line"></div>
                        <div class="itinerary-walk-badge">
                            <span class="material-symbols-outlined" style="font-size: 14px;">directions_walk</span>
                            <span>${slot.walk_to_next_meters} m séta (~${slot.walk_to_next_min || Math.round(slot.walk_to_next_meters / 80)} perc)</span>
                        </div>
                        <div class="itinerary-walk-line"></div>
                    </div>
                ` : '';

                return `
                    <div class="itinerary-slot-card">
                        <div class="itinerary-slot-icon-wrap">
                            <span class="material-symbols-outlined" style="font-size: 22px;">${icon}</span>
                        </div>
                        <div class="itinerary-slot-body">
                            <div class="itinerary-slot-header">
                                <span class="itinerary-slot-time">${timeLabel}</span>
                                <div style="display: flex; gap: 5px;">
                                    ${ratingBadge}
                                    ${priceBadge}
                                    ${rainSafeBadge}
                                </div>
                            </div>
                            <h4 class="itinerary-slot-title">${slot.title}</h4>
                            ${slot.description ? `<p style="margin: 4px 0 0; font-size: 12.5px; color: var(--text-secondary); line-height: 1.5;">${slot.description}</p>` : ''}
                            ${slot.transit_recommendation ? `
                            <div style="margin-top: 6px; font-size: 11px; font-weight: 700; color: #d97706; background: rgba(245, 158, 11, 0.1); padding: 3px 8px; border-radius: 6px; display: inline-flex; align-items: center; gap: 4px;">
                                <span class="material-symbols-outlined" style="font-size: 14px;">directions_bus</span>
                                <span>${slot.transit_recommendation}</span>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    ${walkDivider}
                `;
            }).join('');

            box.innerHTML = `
                ${tabsHtml}
                <div class="itinerary-timeline">
                    ${slotsHtml}
                </div>
            `;
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
                    targetResume = 'activities';
                } else {
                    targetResume = 'stay';
                }
            }

            if (targetResume === 'summary' && trip.destination && trip.flight?.selected_flight && trip.accommodation?.selected_accommodation) {
                this.renderFinalSummary();
                state.setStep(5);
            } else if (targetResume === 'activities' && trip.destination && trip.flight?.selected_flight && trip.accommodation?.selected_accommodation) {
                if (window.PlannerActivities) window.PlannerActivities.initActivities();
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
