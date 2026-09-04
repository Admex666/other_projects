/**
 * Optivoya — Master Planner Stays Module
 * Handles Cozycozy stay search API, photo/badge overlays, card rendering, and selection.
 */

(function () {
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

    const PlannerStays = {
        async triggerStaySearch(fl, forceRefresh = false) {
            const state = window.PlannerState;
            if (!fl || !state) return;
            state.selectedFlight = fl;

            const outDate = (fl.out_dep_time || fl.out_date || '').split('T')[0];
            const inDate = (fl.in_dep_time || fl.in_date || '').split('T')[0];
            const nights = fl.stay_days || fl.exact_stay_nights || state.intake.duration || 7;
            const destCity = state.selectedDest?.name || state.selectedDest?.city || 'Célállomás';
            const destCountry = state.selectedDest?.country || 'Olaszország';

            const sFl = document.getElementById('stayContextFlight');
            const sCity = document.getElementById('stayContextCity');
            const sNights = document.getElementById('stayNightsCount');
            if (sFl) sFl.innerText = `${fl.out_airline || fl.airline || 'Járat'} (${outDate} – ${inDate} · ${nights} éj)`;
            if (sCity) sCity.innerText = destCity;
            if (sNights) sNights.innerText = nights;

            const cacheKey = `stays_${destCity}_${destCountry}_${outDate}_${inDate}_${nights}_${state.intake.adults}_${state.intake.hotel_min_stars}_${state.intake.hotel_min_rating}_${state.intake.breakfast}_${(state.intake.hotel_types || []).join(',')}_${(state.intake.amenities || []).join(',')}`;

            if (!forceRefresh) {
                const cached = state.getSessionCache(cacheKey);
                if (cached && cached.length > 0) {
                    state.stays = cached;
                    this.renderStays();
                    state.setStep(3);
                    return;
                }
            }

            state.showLoader(
                `Szállások keresése (${destCity})...`,
                `Szállások aggregálása a zárolt időszakra (${outDate} – ${inDate} · ${nights} éjszaka) a kiválasztott prioritásokkal...`
            );

            try {
                const res = await fetch('/api/planner/search-stays', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Planner-Dummy-Mode': state.dummy_mode ? 'true' : 'false',
                        'X-Session-ID': state.getSessionId()
                    },
                    body: JSON.stringify({
                        city: destCity,
                        country: destCountry,
                        checkin: outDate,
                        checkout: inDate,
                        adults: state.intake.adults,
                        min_stars: state.intake.hotel_min_stars,
                        min_rating: state.intake.hotel_min_rating,
                        hotel_types: state.intake.hotel_types,
                        breakfast: state.intake.breakfast,
                        amenities: state.intake.amenities,
                        dummy_mode: Boolean(state.dummy_mode)
                    })
                });

                const data = await res.json();
                if (data.status === 'ok') {
                    state.stays = data.stays || [];
                    state.setSessionCache(cacheKey, state.stays);
                    this.renderStays();
                    state.setStep(3);
                } else {
                    alert("Szálláskeresési hiba: " + (data.error || 'Hiba'));
                    state.setStep(2);
                }
            } catch (e) {
                alert("Szálláskeresési hiba: " + e.message);
                state.setStep(2);
            }
        },

        async prefetchStays(fl) {
            const state = window.PlannerState;
            if (!fl || !state) return;
            const outDate = (fl.out_dep_time || fl.out_date || '').split('T')[0];
            const inDate = (fl.in_dep_time || fl.in_date || '').split('T')[0];
            const nights = fl.stay_days || fl.exact_stay_nights || state.intake.duration || 7;
            const destCity = state.selectedDest?.name || state.selectedDest?.city || 'Célállomás';
            const destCountry = state.selectedDest?.country || 'Olaszország';
            const cacheKey = `stays_${destCity}_${destCountry}_${outDate}_${inDate}_${nights}_${state.intake.adults}_${state.intake.hotel_min_stars}_${state.intake.hotel_min_rating}_${state.intake.breakfast}_${(state.intake.hotel_types || []).join(',')}_${(state.intake.amenities || []).join(',')}`;

            if (state.getSessionCache(cacheKey)) return;

            try {
                const res = await fetch('/api/planner/search-stays', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Planner-Dummy-Mode': state.dummy_mode ? 'true' : 'false',
                        'X-Session-ID': state.getSessionId()
                    },
                    body: JSON.stringify({
                        city: destCity,
                        country: destCountry,
                        checkin: outDate,
                        checkout: inDate,
                        adults: state.intake.adults,
                        min_stars: state.intake.hotel_min_stars,
                        min_rating: state.intake.hotel_min_rating,
                        hotel_types: state.intake.hotel_types,
                        breakfast: state.intake.breakfast,
                        amenities: state.intake.amenities,
                        dummy_mode: Boolean(state.dummy_mode)
                    })
                });
                const data = await res.json();
                if (data.status === 'ok' && data.stays && data.stays.length > 0) {
                    state.setSessionCache(cacheKey, data.stays);
                    console.log(`[PREFETCH SUCCESS] Stays prefetched and cached for ${destCity} (${outDate} - ${inDate})`);
                }
            } catch (e) {
                // Silent prefetch failure
            }
        },


        renderStays() {
            const state = window.PlannerState;
            const container = document.getElementById('staysGrid');
            if (!container || !state) return;

            if (state.stays.length === 0) {
                container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">Nem találtunk szállást a megadott szűrésekkel. Kérlek módosítsd a csillagszámot vagy értékelést a fenti szűrőben!</div>`;
                return;
            }

            const destCity = state.selectedDest?.name || state.selectedDest?.city || 'Célállomás';

            const allStayPrices = state.stays.map(s => s.price_total_huf || s.price_huf || 0).filter(p => p > 0);
            const minStayPrice = allStayPrices.length ? Math.min(...allStayPrices) : 0;
            const maxStayPrice = allStayPrices.length ? Math.max(...allStayPrices) : 0;

            const allRatings = state.stays.map(s => {
                const raw = s.rating_score ? (s.rating_score > 10 ? s.rating_score / 10 : parseFloat(s.rating_score)) : 8.5;
                return isNaN(raw) ? 8.5 : raw;
            });
            const minRating = allRatings.length ? Math.min(...allRatings) : 7.0;
            const maxRating = allRatings.length ? Math.max(...allRatings) : 10.0;

            container.innerHTML = state.stays.map((stay, idx) => {
                const priceTotal = stay.price_total_huf || (stay.price_per_night_huf ? stay.price_per_night_huf * (state.selectedFlight?.stay_days || 7) : stay.price_huf || 120000);
                const nights = state.selectedFlight?.stay_days || state.intake.duration || 7;
                const pricePerNight = stay.price_per_night_huf || Math.round(priceTotal / nights);
                const rating = stay.rating_score ? (stay.rating_score > 10 ? (stay.rating_score / 10).toFixed(1) : parseFloat(stay.rating_score).toFixed(1)) : 8.5;
                const stars = stay.stars || (stay.accommodation_type === '$HOTEL' ? 4 : 3);
                const provider = stay.provider || 'Booking.com';
                
                const stayPriceHeatmap = getPercentileStyle(priceTotal, minStayPrice, maxStayPrice, true);
                const stayRatingHeatmap = getPercentileStyle(parseFloat(rating), minRating, maxRating, false);
                
                const defaultImg = `https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&auto=format&fit=crop&q=80`;
                const photoUrl = stay.image_url || stay.image || stay.photo_url || defaultImg;

                const bookingUrl = stay.booking_url && stay.booking_url !== '#' 
                    ? stay.booking_url 
                    : `https://www.google.com/search?q=${encodeURIComponent((stay.name || 'Hotel') + ' ' + destCity + ' booking')}`;

                return `
                    <div class="planner-stay-card">
                        <div class="stay-image-container">
                            <img src="${photoUrl}" alt="${stay.name || 'Szállás'}" class="stay-image-img" loading="lazy" onerror="this.src='${defaultImg}'">
                            <div class="stay-badge-overlay">
                                <span style="background: ${stayRatingHeatmap.bg}; color: ${stayRatingHeatmap.text}; border: 1px solid ${stayRatingHeatmap.border}; font-weight: 800; font-size: 11.5px; padding: 4px 8px; border-radius: 6px; backdrop-filter: blur(8px);">
                                    ★ ${rating} / 10 · ${stayRatingHeatmap.label}
                                </span>
                            </div>
                            <div class="stay-provider-overlay">
                                ${provider}
                            </div>
                        </div>

                        <div class="stay-card-content">
                            <div>
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; gap: 8px;">
                                    <h3 style="font-size: 16px; font-weight: 800; color: var(--text-main); margin: 0; line-height: 1.3;">
                                        ${stay.name || 'Szálloda'}
                                    </h3>
                                    <span style="font-size: 12px; color: #eab308; font-weight: 800; white-space: nowrap;">
                                        ${'⭐'.repeat(Math.min(5, Math.max(1, stars)))}
                                    </span>
                                </div>

                                <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">
                                    📍 ${stay.address || stay.location_text || stay.city || destCity}
                                </div>

                                <div style="font-size: 11.5px; color: var(--text-secondary); margin-bottom: 4px;">
                                    🌙 ${nights} éjszaka · ~${Math.round(pricePerNight).toLocaleString()} Ft / éj
                                </div>
                                <div style="margin-bottom: 12px;">
                                    <span style="font-size: 10.5px; font-weight: 800; padding: 2px 7px; border-radius: 6px; background: ${stayPriceHeatmap.bg}; color: ${stayPriceHeatmap.text}; border: 1px solid ${stayPriceHeatmap.border}; display: inline-block;">
                                        ${stayPriceHeatmap.label}
                                    </span>
                                </div>
                            </div>

                            <div>
                                <div style="margin-top: 12px; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: flex-end;">
                                    <div>
                                        <div style="font-size: 11px; color: var(--text-muted); font-weight: 600;">Teljes ár (${nights} éjszaka):</div>
                                        <div style="font-size: 20px; font-weight: 900; color: var(--primary); font-family: var(--font-mono); line-height: 1.1;">
                                            ${Math.round(priceTotal).toLocaleString()} Ft
                                        </div>
                                    </div>
                                    <div style="font-size: 11.5px; color: var(--text-muted); font-weight: 600; text-align: right;">
                                        ~${Math.round(pricePerNight).toLocaleString()} Ft / éj
                                    </div>
                                </div>

                                <div class="stay-card-actions">
                                    <a href="${bookingUrl}" target="_blank" rel="noopener noreferrer" class="stay-preview-link" title="Szállás megtekintése a szolgáltató külső oldalán (${provider})">
                                        <span>Megtekintés ↗</span>
                                    </a>
                                    <button type="button" class="btn btn-primary" onclick="Wizard.selectStay(${idx})" style="flex: 1; padding: 10px 14px; font-size: 13px; font-weight: 800; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; gap: 6px;">
                                        <span>🏨 Kiválasztás →</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        },

        selectStay(index) {
            const state = window.PlannerState;
            if (!state) return;
            const stay = state.stays[index];
            if (!stay) return;

            state.selectedStay = stay;
            const nights = state.selectedFlight?.stay_days || state.intake.duration;
            const priceTotal = stay.price_total_huf || (stay.price_per_night_huf ? stay.price_per_night_huf * nights : stay.price_huf || 120000);

            if (window.TripCart) {
                window.TripCart.setStay({
                    name: stay.name || 'Szállás',
                    price_huf: priceTotal,
                    price_total_huf: priceTotal,
                    rating: stay.rating_score ? (stay.rating_score > 10 ? Math.round(stay.rating_score / 10) : stay.rating_score) : 8.5,
                    stars: stay.stars || 4,
                    address: stay.address || '',
                    city: state.selectedDest?.name || '',
                    nights: nights,
                    image_url: stay.image_url || stay.image || '',
                    booking_url: stay.booking_url || ''
                });
            }

            if (window.PlannerSummary) {
                window.PlannerSummary.renderFinalSummary();
            }
            state.setStep(4);
        },

        recalculateStays() {
            const state = window.PlannerState;
            if (!state) return;
            const starsInput = document.getElementById('mod_hotel_stars');
            const ratingInput = document.getElementById('mod_hotel_rating');
            if (starsInput) state.intake.hotel_min_stars = parseInt(starsInput.value, 10) || 0;
            if (ratingInput) state.intake.hotel_min_rating = parseFloat(ratingInput.value) || 0;

            state.selectedStay = null;

            if (window.TripCart) {
                const trip = window.TripCart.getTrip();
                trip.accommodation.selected_accommodation = null;
                trip.accommodation.shortlist = [];
                trip.status = 'flight_selected';
                window.TripCart.saveTrip(trip);
            }

            if (state.selectedFlight) {
                this.triggerStaySearch(state.selectedFlight, true);
            }
        }
    };

    window.PlannerStays = PlannerStays;
})();
