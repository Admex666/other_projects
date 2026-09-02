/**
 * Optivoya — Trip Store & State Management Module
 * Canonical LocalStorage persistence and state transitions for active trip workspace.
 */

(function () {
    const STORAGE_KEY = 'optivoya_trip_workspace';

    function generateTripId() {
        return 'trip_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 5);
    }

    function createDefaultTrip() {
        return {
            trip_id: generateTripId(),
            user_id: 'default_user',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            status: 'initialized',
            dining_profile: 'standard',
            input: {
                origin: 'Budapest',
                origin_airport: 'BUD',
                adults: 2,
                children: 0,
                date_mode: 'month',
                month: '9',
                duration_days: 7,
                daily_budget_eur: 150.0,
                budget_strictness: 'soft',
                exclusions: []
            },
            destination: null,
            flight: {
                search_params: {},
                ahp_weights: {},
                shortlist: [],
                selected_flight: null
            },
            accommodation: {
                search_params: {},
                preferences: {},
                shortlist: [],
                selected_accommodation: null
            },
            budget: {
                flight_total_huf: 0,
                accommodation_total_huf: 0,
                food_total_huf: 0,
                transport_total_huf: 0,
                total_huf: 0,
                per_person_huf: 0,
                items: []
            }
        };
    }

    const TripStore = {
        STORAGE_KEY,

        getTrip() {
            try {
                const raw = localStorage.getItem(STORAGE_KEY);
                if (!raw) return createDefaultTrip();
                const parsed = JSON.parse(raw);

                // Session Expiration: 2 óránál régebbi vagy előző napi terv automatikus törlése
                const lastUpdated = parsed.updated_at ? new Date(parsed.updated_at).getTime() : 0;
                const SESSION_TTL_MS = 2 * 60 * 60 * 1000; // 2 óra
                if (lastUpdated > 0 && (Date.now() - lastUpdated > SESSION_TTL_MS)) {
                    console.log("[TripStore] Previous trip session expired (>2 hours). Resetting workspace.");
                    localStorage.removeItem(STORAGE_KEY);
                    return createDefaultTrip();
                }

                if (!parsed.trip_id) {
                    const fresh = createDefaultTrip();
                    if (parsed.destination) fresh.destination = parsed.destination;
                    if (parsed.flight) fresh.flight.selected_flight = parsed.flight;
                    if (parsed.stay) fresh.accommodation.selected_accommodation = parsed.stay;
                    return fresh;
                }
                return parsed;
            } catch (e) {
                console.error("Trip read error:", e);
                return createDefaultTrip();
            }
        },


        saveTrip(trip) {
            try {
                trip.updated_at = new Date().toISOString();
                localStorage.setItem(STORAGE_KEY, JSON.stringify(trip));
                if (window.TripDrawer) {
                    window.TripDrawer.render();
                }
                this.syncToServer(trip);
            } catch (e) {
                console.error("Trip save error:", e);
            }
        },

        async syncToServer(trip) {
            try {
                fetch('/api/trip/sync', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(trip)
                }).catch(() => { });
            } catch (e) { }
        },

        getCart() {
            const trip = this.getTrip();
            return {
                destination: trip.destination,
                flight: trip.flight?.selected_flight,
                stay: trip.accommodation?.selected_accommodation,
                trip: trip
            };
        },

        setDestination(data) {
            const trip = this.getTrip();
            const adults = parseInt(data.adults, 10) || trip.input.adults || 2;
            const children = parseInt(data.children, 10) || trip.input.children || 0;
            const duration = parseInt(data.duration, 10) || trip.input.duration_days || 7;
            const origin = data.origin || trip.input.origin || 'Budapest';
            const month = data.month || trip.input.month || '9';

            trip.input.origin = origin;
            trip.input.adults = adults;
            trip.input.children = children;
            trip.input.duration_days = duration;
            trip.input.month = month;

            trip.destination = {
                name: data.name,
                city: data.city || data.name,
                country: data.country || '',
                region: data.region || '',
                month: month,
                duration: duration,
                adults: adults,
                children: children,
                origin: origin,
                daily_cost_eur: data.daily_cost_eur || 45,
                flight_est_huf: data.flight_price_huf || null,
                numbeo: data.numbeo || null,
                rank: data.rank || 1,
                score: data.score || null,
                highlights: data.highlights || [],
                tradeoff: data.tradeoff || '',
                explanation: data.explanation || '',
                image: data.image || ''
            };

            trip.flight.search_params = {
                origin: origin,
                destination: trip.destination.city || trip.destination.name,
                adults: adults,
                children: children,
                month: month,
                duration_days: duration
            };

            trip.accommodation.search_params = {
                city: trip.destination.city || trip.destination.name,
                country: trip.destination.country,
                adults: adults,
                children: children,
                nights: duration
            };

            // Invariant: Setting/changing a destination invalidates downstream flight and accommodation selections
            trip.flight.selected_flight = null;
            trip.flight.shortlist = [];
            trip.accommodation.selected_accommodation = null;
            trip.accommodation.shortlist = [];

            trip.status = 'destination_selected';
            this.saveTrip(trip);
            if (window.TripDrawer) window.TripDrawer.showToast(`📍 ${data.name} rögzítve az aktív utazáshoz!`, '📍');
        },

        setFlight(data) {
            const trip = this.getTrip();
            const adults = parseInt(data.adults, 10) || trip.input.adults || 2;
            const flightPrice = parseFloat(data.price_huf || data.total_price_huf) || 0;
            const perPerson = Math.round(flightPrice / Math.max(1, adults));

            const flightItem = {
                id: data.id || 'fl_' + Date.now(),
                airline: data.airline || data.out_airline || 'Járat',
                price_total_huf: flightPrice,
                price_huf: flightPrice,
                price_per_person_huf: perPerson,
                out_date: data.out_date || data.out_dep_time?.split('T')[0] || '',
                in_date: data.in_date || data.in_dep_time?.split('T')[0] || '',
                out_time: data.out_time || (data.out_dep_time ? data.out_dep_time.substring(11, 16) : ''),
                in_time: data.in_time || (data.in_dep_time ? data.in_dep_time.substring(11, 16) : ''),
                out_airport: data.out_airport || data.out_dep_airport || 'BUD',
                in_airport: data.in_airport || data.in_dep_airport || (trip.destination?.city || ''),
                duration_h: parseFloat(data.duration_h || data.out_duration_h) || 0,
                stops: data.stops !== undefined ? data.stops : (data.out_stops || 0),
                adults: adults,
                phi_net: data.phi_net || null,
                rank: data.rank || null,
                exact_stay_nights: data.stay_days || data.exact_stay_nights || trip.input.duration_days || 7,
                booking_token: data.booking_token || null
            };

            trip.flight.selected_flight = flightItem;

            if (flightItem.out_date && flightItem.in_date) {
                trip.accommodation.search_params.checkin = flightItem.out_date;
                trip.accommodation.search_params.checkout = flightItem.in_date;
                trip.accommodation.search_params.nights = flightItem.exact_stay_nights;
            }

            // Invariant: Setting/changing a flight invalidates downstream accommodation selection
            trip.accommodation.selected_accommodation = null;
            trip.accommodation.shortlist = [];

            trip.status = 'flight_selected';
            this.saveTrip(trip);
            if (window.TripDrawer) window.TripDrawer.showToast(`✈️ ${flightItem.airline} járat rögzítve az utazáshoz!`, '✈️');
        },

        addFlightShortlist(data) {
            const trip = this.getTrip();
            if (!trip.flight.shortlist) trip.flight.shortlist = [];
            const exists = trip.flight.shortlist.some(f => f.airline === data.airline && f.out_date === data.out_date);
            if (!exists) {
                trip.flight.shortlist.push(data);
                if (trip.flight.shortlist.length > 4) trip.flight.shortlist.shift();
                this.saveTrip(trip);
                if (window.TripDrawer) window.TripDrawer.showToast(`⭐ Járat hozzáadva a shortlisthez`, '⭐');
            }
        },

        setStay(data) {
            const trip = this.getTrip();
            const price = parseFloat(data.price_huf || data.price_total_huf) || 0;
            const nights = parseInt(data.nights, 10) || trip.flight?.selected_flight?.exact_stay_nights || trip.input.duration_days || 7;
            const perNight = Math.round(price / Math.max(1, nights));

            const stayItem = {
                id: data.id || 'stay_' + Date.now(),
                name: data.name || 'Szállás',
                stars: parseInt(data.stars, 10) || 3,
                rating: parseFloat(data.rating) || 8.0,
                review_count: parseInt(data.review_count, 10) || 0,
                price_total_huf: price,
                price_huf: price,
                price_per_night_huf: perNight,
                nights: nights,
                address: data.address || '',
                city: data.city || trip.destination?.city || '',
                lat: data.lat || null,
                lon: data.lon || null,
                image: data.image || '',
                amenities: data.amenities || [],
                booking_url: data.booking_url || null
            };

            trip.accommodation.selected_accommodation = stayItem;
            trip.status = 'accommodation_selected';
            this.saveTrip(trip);
            if (window.TripDrawer) window.TripDrawer.showToast(`🏨 ${stayItem.name} hozzáadva az utazáshoz!`, '🏨');
        },

        addAccommodationShortlist(data) {
            const trip = this.getTrip();
            if (!trip.accommodation.shortlist) trip.accommodation.shortlist = [];
            const exists = trip.accommodation.shortlist.some(s => s.name === data.name);
            if (!exists) {
                trip.accommodation.shortlist.push(data);
                if (trip.accommodation.shortlist.length > 4) trip.accommodation.shortlist.shift();
                this.saveTrip(trip);
                if (window.TripDrawer) window.TripDrawer.showToast(`⭐ Szállás hozzáadva a shortlisthez`, '⭐');
            }
        },

        removeDestination() {
            const trip = this.getTrip();
            trip.destination = null;
            trip.status = 'initialized';
            this.saveTrip(trip);
            if (window.TripDrawer) window.TripDrawer.showToast("Célállomás eltávolítva a tervből.", "🗑️");
        },

        removeFlight() {
            const trip = this.getTrip();
            trip.flight.selected_flight = null;
            trip.status = trip.destination ? 'destination_selected' : 'initialized';
            this.saveTrip(trip);
            if (window.TripDrawer) window.TripDrawer.showToast("Járat eltávolítva a tervből.", "🗑️");
        },

        removeStay() {
            const trip = this.getTrip();
            trip.accommodation.selected_accommodation = null;
            trip.status = trip.flight.selected_flight ? 'flight_selected' : (trip.destination ? 'destination_selected' : 'initialized');
            this.saveTrip(trip);
            if (window.TripDrawer) window.TripDrawer.showToast("Szállás eltávolítva a tervből.", "🗑️");
        },

        setDiningProfile(profileKey) {
            const trip = this.getTrip();
            trip.dining_profile = profileKey;
            this.saveTrip(trip);
            const names = { 'budget': 'Takarékos', 'standard': 'Átlagos', 'comfort': 'Kényelmes' };
            if (window.TripDrawer) window.TripDrawer.showToast(`🍽️ Étkezési profil: ${names[profileKey] || profileKey}`, '🍽️');
        },

        clearCart() {
            if (confirm("Biztosan törölni szeretnéd az egész aktív utazási tervet?")) {
                const fresh = createDefaultTrip();
                localStorage.setItem(STORAGE_KEY, JSON.stringify(fresh));

                try {
                    Object.keys(sessionStorage).forEach(k => {
                        if (k.startsWith('optivoya_cache_')) {
                            sessionStorage.removeItem(k);
                        }
                    });
                } catch (e) { }

                if (window.TripDrawer) {
                    window.TripDrawer.render();
                    window.TripDrawer.showToast("Utazási terv kiürítve.", "🧹");
                    window.TripDrawer.hideDrawer();
                }
                this.syncToServer(fresh);

                if (window.location.pathname.startsWith('/planner') ||
                    window.location.pathname.includes('-results')) {
                    window.location.href = '/home';
                }
            }
        }
    };

    window.TripStore = TripStore;
})();
