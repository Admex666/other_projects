/**
 * OPTIVOYA UNIFIED TRIP ENGINE & WORKSPACE CONTROLLER
 * Single Source of Truth for Destination Matcher, Flight Intelligence & Accommodation Intelligence
 */

(function() {
    const STORAGE_KEY = 'optivoya_trip_workspace';

    // HIVATALOS NUMBEO ADATBÁZIS (Éttermi és megélhetési adatok EUR-ban)
    const NUMBEO_DB = {
        "barcelona": { meal_inexpensive: 15.0, meal_midrange: 30.0, coffee: 2.2, transport: 2.55 },
        "rome": { meal_inexpensive: 16.0, meal_midrange: 32.0, coffee: 1.6, transport: 1.50 },
        "róma": { meal_inexpensive: 16.0, meal_midrange: 32.0, coffee: 1.6, transport: 1.50 },
        "paris": { meal_inexpensive: 18.0, meal_midrange: 40.0, coffee: 3.8, transport: 2.15 },
        "párizs": { meal_inexpensive: 18.0, meal_midrange: 40.0, coffee: 3.8, transport: 2.15 },
        "budapest": { meal_inexpensive: 9.5, meal_midrange: 22.0, coffee: 2.0, transport: 1.20 },
        "vienna": { meal_inexpensive: 15.0, meal_midrange: 35.0, coffee: 3.9, transport: 2.40 },
        "bécs": { meal_inexpensive: 15.0, meal_midrange: 35.0, coffee: 3.9, transport: 2.40 },
        "london": { meal_inexpensive: 22.0, meal_midrange: 45.0, coffee: 4.2, transport: 3.40 },
        "tokyo": { meal_inexpensive: 7.5, meal_midrange: 24.0, coffee: 3.2, transport: 1.40 },
        "tokió": { meal_inexpensive: 7.5, meal_midrange: 24.0, coffee: 3.2, transport: 1.40 },
        "funchal": { meal_inexpensive: 11.0, meal_midrange: 24.0, coffee: 1.4, transport: 1.95 },
        "madeira": { meal_inexpensive: 11.0, meal_midrange: 24.0, coffee: 1.4, transport: 1.95 },
        "bali": { meal_inexpensive: 3.5, meal_midrange: 12.0, coffee: 2.2, transport: 0.80 },
        "reykjavik": { meal_inexpensive: 24.0, meal_midrange: 58.0, coffee: 4.8, transport: 4.10 },
        "reykjavík": { meal_inexpensive: 24.0, meal_midrange: 58.0, coffee: 4.8, transport: 4.10 },
        "prague": { meal_inexpensive: 10.0, meal_midrange: 24.0, coffee: 2.8, transport: 1.30 },
        "prága": { meal_inexpensive: 10.0, meal_midrange: 24.0, coffee: 2.8, transport: 1.30 },
        "lisbon": { meal_inexpensive: 12.5, meal_midrange: 26.0, coffee: 1.6, transport: 1.80 },
        "lisszabon": { meal_inexpensive: 12.5, meal_midrange: 26.0, coffee: 1.6, transport: 1.80 },
        "athens": { meal_inexpensive: 13.0, meal_midrange: 25.0, coffee: 3.4, transport: 1.20 },
        "athén": { meal_inexpensive: 13.0, meal_midrange: 25.0, coffee: 3.4, transport: 1.20 },
        "santorini": { meal_inexpensive: 16.0, meal_midrange: 35.0, coffee: 4.0, transport: 2.20 },
        "szantorini": { meal_inexpensive: 16.0, meal_midrange: 35.0, coffee: 4.0, transport: 2.20 },
        "amsterdam": { meal_inexpensive: 20.0, meal_midrange: 42.0, coffee: 3.9, transport: 3.40 },
        "amszterdam": { meal_inexpensive: 20.0, meal_midrange: 42.0, coffee: 3.9, transport: 3.40 },
        "dubai": { meal_inexpensive: 14.0, meal_midrange: 38.0, coffee: 4.9, transport: 1.80 },
        "dubaj": { meal_inexpensive: 14.0, meal_midrange: 38.0, coffee: 4.9, transport: 1.80 },
        "new york": { meal_inexpensive: 25.0, meal_midrange: 60.0, coffee: 5.2, transport: 2.80 },
        "bangkok": { meal_inexpensive: 3.2, meal_midrange: 15.0, coffee: 2.1, transport: 1.10 },
        "valletta": { meal_inexpensive: 15.0, meal_midrange: 30.0, coffee: 2.5, transport: 2.00 },
        "málta": { meal_inexpensive: 15.0, meal_midrange: 30.0, coffee: 2.5, transport: 2.00 },
        "berlin": { meal_inexpensive: 14.0, meal_midrange: 32.0, coffee: 3.4, transport: 3.50 },
        "brussels": { meal_inexpensive: 18.0, meal_midrange: 38.0, coffee: 3.6, transport: 2.60 },
        "brüsszel": { meal_inexpensive: 18.0, meal_midrange: 38.0, coffee: 3.6, transport: 2.60 },
        "copenhagen": { meal_inexpensive: 22.0, meal_midrange: 52.0, coffee: 5.5, transport: 3.40 },
        "koppenhága": { meal_inexpensive: 22.0, meal_midrange: 52.0, coffee: 5.5, transport: 3.40 },
        "stockholm": { meal_inexpensive: 14.5, meal_midrange: 40.0, coffee: 4.1, transport: 3.60 },
        "oslo": { meal_inexpensive: 20.0, meal_midrange: 50.0, coffee: 4.6, transport: 3.80 },
        "helsinki": { meal_inexpensive: 16.0, meal_midrange: 42.0, coffee: 4.2, transport: 3.10 },
        "dublin": { meal_inexpensive: 18.0, meal_midrange: 42.0, coffee: 3.9, transport: 2.30 },
        "warsaw": { meal_inexpensive: 9.5, meal_midrange: 22.0, coffee: 3.2, transport: 1.10 },
        "varsó": { meal_inexpensive: 9.5, meal_midrange: 22.0, coffee: 3.2, transport: 1.10 },
        "tallinn": { meal_inexpensive: 12.0, meal_midrange: 28.0, coffee: 3.4, transport: 1.50 },
        "riga": { meal_inexpensive: 11.0, meal_midrange: 25.0, coffee: 3.2, transport: 1.50 },
        "vilnius": { meal_inexpensive: 11.5, meal_midrange: 26.0, coffee: 3.1, transport: 0.90 },
        "istanbul": { meal_inexpensive: 7.0, meal_midrange: 18.0, coffee: 2.5, transport: 0.60 },
        "isztambul": { meal_inexpensive: 7.0, meal_midrange: 18.0, coffee: 2.5, transport: 0.60 },
        "larnaca": { meal_inexpensive: 14.0, meal_midrange: 28.0, coffee: 3.4, transport: 1.50 },
        "luxembourg": { meal_inexpensive: 20.0, meal_midrange: 45.0, coffee: 4.2, transport: 0.00 },
        "split": { meal_inexpensive: 13.0, meal_midrange: 28.0, coffee: 2.2, transport: 1.70 },
        "sofia": { meal_inexpensive: 8.5, meal_midrange: 20.0, coffee: 2.1, transport: 0.85 },
        "szófia": { meal_inexpensive: 8.5, meal_midrange: 20.0, coffee: 2.1, transport: 0.85 },
        "bucharest": { meal_inexpensive: 9.5, meal_midrange: 22.0, coffee: 2.6, transport: 0.65 },
        "bukarest": { meal_inexpensive: 9.5, meal_midrange: 22.0, coffee: 2.6, transport: 0.65 },
        "belgrade": { meal_inexpensive: 8.0, meal_midrange: 20.0, coffee: 2.2, transport: 0.45 },
        "belgrád": { meal_inexpensive: 8.0, meal_midrange: 20.0, coffee: 2.2, transport: 0.45 },
        "tirana": { meal_inexpensive: 7.0, meal_midrange: 18.0, coffee: 1.4, transport: 0.40 },
        "ljubljana": { meal_inexpensive: 12.0, meal_midrange: 28.0, coffee: 2.2, transport: 1.30 },
        "sarajevo": { meal_inexpensive: 6.5, meal_midrange: 16.0, coffee: 1.6, transport: 0.90 },
        "szarajevó": { meal_inexpensive: 6.5, meal_midrange: 16.0, coffee: 1.6, transport: 0.90 },
        "zurich": { meal_inexpensive: 28.0, meal_midrange: 65.0, coffee: 5.8, transport: 4.50 },
        "zürich": { meal_inexpensive: 28.0, meal_midrange: 65.0, coffee: 5.8, transport: 4.50 },
        "sydney": { meal_inexpensive: 16.0, meal_midrange: 42.0, coffee: 3.4, transport: 2.80 }
    };

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

    const TripEngine = {
        isBarHidden: false,

        getTrip() {
            try {
                const raw = localStorage.getItem(STORAGE_KEY);
                if (!raw) return createDefaultTrip();
                const parsed = JSON.parse(raw);
                
                // Migráció ha régi cart struktúra lenne
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
                this.render();
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
                }).catch(() => {});
            } catch (e) {}
        },

        // Backwards compatibility layer
        getCart() {
            const trip = this.getTrip();
            return {
                destination: trip.destination,
                flight: trip.flight?.selected_flight,
                stay: trip.accommodation?.selected_accommodation,
                trip: trip
            };
        },

        // STEP 1: DESTINATION MATCHER -> TRIP
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

            // Előkészítjük a Flight és Accommodation keresési paramétereket
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

            trip.status = 'destination_selected';
            this.saveTrip(trip);
            this.showToast(`📍 ${data.name} rögzítve az aktív utazáshoz!`, '📍');
        },

        // STEP 2: FLIGHT INTELLIGENCE -> TRIP
        setFlight(data) {
            const trip = this.getTrip();
            const adults = parseInt(data.adults, 10) || trip.input.adults || 2;
            const flightPrice = parseFloat(data.price_huf || data.total_price_huf) || 0;
            const perPerson = Math.round(flightPrice / Math.max(1, adults));

            const flightItem = {
                id: data.id || 'fl_' + Date.now(),
                airline: data.airline || data.out_airline || 'Járat',
                price_total_huf: flightPrice,
                price_huf: flightPrice, // compat
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

            // ✅ AUTOMATIKUS DÁTUMZÁROLÁS A SZÁLLÁSKERESŐNEK:
            // A szálláskereső pontosan a járat érkezési és indulási dátumát kapja!
            if (flightItem.out_date && flightItem.in_date) {
                trip.accommodation.search_params.checkin = flightItem.out_date;
                trip.accommodation.search_params.checkout = flightItem.in_date;
                trip.accommodation.search_params.nights = flightItem.exact_stay_nights;
            }

            trip.status = 'flight_selected';
            this.saveTrip(trip);
            this.showToast(`✈️ ${flightItem.airline} járat rögzítve az utazáshoz!`, '✈️');
        },

        addFlightShortlist(data) {
            const trip = this.getTrip();
            if (!trip.flight.shortlist) trip.flight.shortlist = [];
            const exists = trip.flight.shortlist.some(f => f.airline === data.airline && f.out_date === data.out_date);
            if (!exists) {
                trip.flight.shortlist.push(data);
                if (trip.flight.shortlist.length > 4) trip.flight.shortlist.shift();
                this.saveTrip(trip);
                this.showToast(`⭐ Járat hozzáadva a shortlisthez`, '⭐');
            }
        },

        // STEP 3: ACCOMMODATION INTELLIGENCE -> TRIP
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
                price_huf: price, // compat
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
            this.showToast(`🏨 ${stayItem.name} hozzáadva az utazáshoz!`, '🏨');
        },

        addAccommodationShortlist(data) {
            const trip = this.getTrip();
            if (!trip.accommodation.shortlist) trip.accommodation.shortlist = [];
            const exists = trip.accommodation.shortlist.some(s => s.name === data.name);
            if (!exists) {
                trip.accommodation.shortlist.push(data);
                if (trip.accommodation.shortlist.length > 4) trip.accommodation.shortlist.shift();
                this.saveTrip(trip);
                this.showToast(`⭐ Szállás hozzáadva a shortlisthez`, '⭐');
            }
        },

        removeDestination() {
            const trip = this.getTrip();
            trip.destination = null;
            trip.status = 'initialized';
            this.saveTrip(trip);
            this.showToast("Célállomás eltávolítva a tervből.", "🗑️");
        },

        removeFlight() {
            const trip = this.getTrip();
            trip.flight.selected_flight = null;
            trip.status = trip.destination ? 'destination_selected' : 'initialized';
            this.saveTrip(trip);
            this.showToast("Járat eltávolítva a tervből.", "🗑️");
        },

        removeStay() {
            const trip = this.getTrip();
            trip.accommodation.selected_accommodation = null;
            trip.status = trip.flight.selected_flight ? 'flight_selected' : (trip.destination ? 'destination_selected' : 'initialized');
            this.saveTrip(trip);
            this.showToast("Szállás eltávolítva a tervből.", "🗑️");
        },

        clearCart() {
            if (confirm("Biztosan törölni szeretnéd az egész aktív utazási tervet?")) {
                const fresh = createDefaultTrip();
                localStorage.setItem(STORAGE_KEY, JSON.stringify(fresh));
                
                // Töröljük a kliensoldali keresési gyorsítótárakat is
                try {
                    Object.keys(sessionStorage).forEach(k => {
                        if (k.startsWith('optivoya_cache_')) {
                            sessionStorage.removeItem(k);
                        }
                    });
                } catch (e) {}

                this.render();
                this.syncToServer(fresh);
                this.showToast("Utazási terv kiürítve.", "🧹");
                this.hideDrawer();

                // Ha a /planner vagy bármely eredményoldalon vagyunk, azonnali átirányítás a főoldalra
                if (window.location.pathname.startsWith('/planner') || 
                    window.location.pathname.includes('-results')) {
                    window.location.href = '/home';
                }
            }
        },


        getNumbeoMetrics(cityName) {
            if (!cityName) return { meal_inexpensive: 14.0, meal_midrange: 28.0, coffee: 2.8, transport: 2.0 };
            const lower = cityName.toLowerCase().trim();
            for (let k in NUMBEO_DB) {
                if (lower.includes(k) || k.includes(lower)) {
                    return NUMBEO_DB[k];
                }
            }
            return { meal_inexpensive: 14.0, meal_midrange: 28.0, coffee: 2.8, transport: 2.0 };
        },

        // MATHEMATICAL BREAKDOWN & FORMULA CALCULATION
        calculateBreakdown() {
            const trip = this.getTrip();
            const items = [];
            let totalHuf = 0;
            let hasAny = false;

            const days = trip.flight?.selected_flight?.exact_stay_nights || trip.destination?.duration || trip.input.duration_days || 7;
            const adults = trip.input.adults || (trip.destination ? trip.destination.adults : 2) || 2;
            const children = trip.input.children || 0;
            const totalPersons = Math.max(1, adults + children);

            // 1. ODAJUTÁS ÉS VISSZAJUTÁS (REPÜLŐJEGY)
            const selFlight = trip.flight?.selected_flight;
            if (selFlight && (selFlight.price_total_huf || selFlight.price_huf)) {
                const flightTotal = Math.round(selFlight.price_total_huf || selFlight.price_huf);
                const flightPersons = parseInt(selFlight.adults, 10) || adults || 1;
                const perPerson = Math.round(flightTotal / flightPersons);
                items.push({
                    key: 'flight',
                    icon: '✈️',
                    name: 'Odajutás és visszajutás (Repülőjegy)',
                    desc: `${selFlight.airline} (Retúr járat)`,
                    formula: `${perPerson.toLocaleString()} Ft / fő × ${flightPersons} fő`,
                    amount: flightTotal,
                    badge: 'Rögzített',
                    isEstimated: false
                });
                totalHuf += flightTotal;
                hasAny = true;
            } else if (trip.destination && trip.destination.flight_est_huf) {
                const flightEst = Math.round(trip.destination.flight_est_huf);
                const perPerson = Math.round(flightEst / adults);
                items.push({
                    key: 'flight',
                    icon: '✈️',
                    name: 'Odajutás és visszajutás (Repülőjegy irányár)',
                    desc: `Irányadó Kiwi retúr járat ${trip.destination.origin} indulással`,
                    formula: `~${perPerson.toLocaleString()} Ft / fő × ${adults} felnőtt`,
                    amount: flightEst,
                    badge: 'Irányár',
                    isEstimated: true
                });
                totalHuf += flightEst;
                hasAny = true;
            }

            // 2. SZÁLLÁSKÖLTSÉG
            const selStay = trip.accommodation?.selected_accommodation;
            if (selStay && (selStay.price_total_huf || selStay.price_huf)) {
                const stayTotal = Math.round(selStay.price_total_huf || selStay.price_huf);
                const nights = parseInt(selStay.nights, 10) || days;
                const perNight = Math.round(stayTotal / Math.max(1, nights));
                items.push({
                    key: 'stay',
                    icon: '🏨',
                    name: 'Szállásköltség',
                    desc: `${selStay.name} (${nights} éjszaka)`,
                    formula: `${perNight.toLocaleString()} Ft / éj × ${nights} éjszaka`,
                    amount: stayTotal,
                    badge: 'Rögzített',
                    isEstimated: false
                });
                totalHuf += stayTotal;
                hasAny = true;
            } else if (trip.destination) {
                const estNightHuf = 28000;
                const stayEst = estNightHuf * days;
                items.push({
                    key: 'stay',
                    icon: '🏨',
                    name: 'Szállásköltség (Irányadó 3-4 csillagos hotel)',
                    desc: `Átlagos 3-4 csillagos szállodai éjszaka`,
                    formula: `~${estNightHuf.toLocaleString()} Ft / éj × ${days} éjszaka`,
                    amount: stayEst,
                    badge: 'Irányár',
                    isEstimated: true
                });
                totalHuf += stayEst;
                hasAny = true;
            }

            // 3. ÉTELEK ÉS ÉTKEZÉSEK (NUMBEO SERVICE)
            if (trip.destination) {
                const numbeoData = (trip.destination.numbeo && trip.destination.numbeo.meal_inexpensive) 
                    ? trip.destination.numbeo 
                    : this.getNumbeoMetrics(trip.destination.city || trip.destination.name);

                const mealInexpensive = numbeoData.meal_inexpensive || 14.0;
                const mealMidrange = numbeoData.meal_midrange || 28.0;
                const coffee = numbeoData.coffee || 2.5;

                const dailyFoodEur = Math.round(((1.5 * mealInexpensive) + (0.5 * mealMidrange) + (2.0 * coffee)) * 10) / 10;
                const dailyFoodHuf = Math.round(dailyFoodEur * 395);
                const foodTotalHuf = dailyFoodHuf * days * totalPersons;

                items.push({
                    key: 'food',
                    icon: '🍽️',
                    name: `Ételek & étkezések (Numbeo Cost of Living — ${trip.destination.name})`,
                    desc: `Numbeo árak: Olcsó étkezés: €${mealInexpensive.toFixed(1)} | Középk. vacsora: €${mealMidrange.toFixed(1)} | Kávé: €${coffee.toFixed(1)}`,
                    formula: `${dailyFoodHuf.toLocaleString()} Ft / nap / fő (1.5× olcsó étk. + 0.5× vacsora + 2× kávé) × ${days} nap × ${totalPersons} fő`,
                    amount: foodTotalHuf,
                    badge: 'Numbeo Index',
                    isEstimated: false
                });
                totalHuf += foodTotalHuf;
                hasAny = true;
            }

            // 4. HELYI KÖZLEKEDÉS (NUMBEO TRANZIT JEGYEK)
            if (trip.destination) {
                const numbeoData = (trip.destination.numbeo && trip.destination.numbeo.transport_ticket) 
                    ? trip.destination.numbeo 
                    : this.getNumbeoMetrics(trip.destination.city || trip.destination.name);

                const ticketEur = numbeoData.transport || numbeoData.transport_ticket || 2.0;
                const ticketHuf = Math.round(ticketEur * 395);
                const transitDailyHuf = ticketHuf * 2;
                const transitTotalHuf = transitDailyHuf * days * totalPersons;

                items.push({
                    key: 'transit',
                    icon: '🚇',
                    name: `Helyi tömegközlekedés (Numbeo jegyár — ${trip.destination.name})`,
                    desc: `Numbeo vonaljegy: €${ticketEur.toFixed(2)} (~${ticketHuf.toLocaleString()} Ft / jegy)`,
                    formula: `${transitDailyHuf.toLocaleString()} Ft / nap / fő (2 jegy/nap) × ${days} nap × ${totalPersons} fő`,
                    amount: transitTotalHuf,
                    badge: 'Numbeo Index',
                    isEstimated: false
                });
                totalHuf += transitTotalHuf;
                hasAny = true;
            }

            const perPersonTotal = totalPersons > 0 ? Math.round(totalHuf / totalPersons) : totalHuf;

            return {
                items,
                totalHuf,
                perPersonTotal,
                days,
                adults,
                children,
                totalPersons,
                hasAny
            };
        },

        // SINGLE PRIMARY NEXT STEP CTA GENERATOR
        // SINGLE PRIMARY NEXT STEP CTA GENERATOR (Master Planner Integration)
        getNextStepCTA() {
            const trip = this.getTrip();
            const d = trip.destination;
            const f = trip.flight?.selected_flight;
            const s = trip.accommodation?.selected_accommodation;

            if (!d) {
                return {
                    step: 1,
                    text: 'Tervezés indítása / Célállomás →',
                    url: '/planner',
                    icon: '📍',
                    badge: '1. Lépés'
                };
            }

            if (!f) {
                return {
                    step: 2,
                    text: `Járatok keresése (${d.name}) →`,
                    url: '/planner?resume=flight',
                    icon: '✈️',
                    badge: '2. Lépés'
                };
            }

            if (!s) {
                return {
                    step: 3,
                    text: 'Szállások keresése →',
                    url: '/planner?resume=stay',
                    icon: '🏨',
                    badge: '3. Lépés'
                };
            }

            return {
                step: 4,
                text: 'Összesített terv & B2B Ajánlat →',
                url: '/planner?resume=summary',
                icon: '📄',
                badge: 'Ajánlatkész'
            };
        },

        render() {
            const trip = this.getTrip();
            const d = trip.destination;
            const f = trip.flight?.selected_flight;
            const s = trip.accommodation?.selected_accommodation;

            const bar = document.getElementById('floatingTripBar');
            const drawerBody = document.getElementById('tripDrawerBody');
            const drawerTotal = document.getElementById('tripDrawerTotal');
            const barTotal = document.getElementById('tripBarTotal');
            const slotsGroup = document.getElementById('tripBarSlots');
            const nextBtn = document.getElementById('tripBarNextBtn');

            if (!bar) return;

            const hasItems = d || f || s;
            const reopenBtn = document.getElementById('tripFloatingReopenBtn');

            if (hasItems && !this.isBarHidden) {
                bar.classList.add('visible');
                if (reopenBtn) reopenBtn.classList.remove('visible');
            } else if (hasItems && this.isBarHidden) {
                bar.classList.remove('visible');
                if (reopenBtn) reopenBtn.classList.add('visible');
            } else {
                bar.classList.remove('visible');
                if (reopenBtn) reopenBtn.classList.remove('visible');
            }

            // 1. RENDER FLOATING BAR SLOTS
            if (slotsGroup) {
                let slotsHtml = '';

                // Célállomás Slot
                if (d) {
                    slotsHtml += `
                        <div class="trip-pill-slot active-filled" onclick="TripCart.goToPlannerStep('destination')">
                            <span>📍 ${d.name}</span>
                            <span style="font-size: 11px; opacity: 0.85;">(${d.duration || 7}n, ${d.adults || 2}fő)</span>
                        </div>
                    `;
                } else {
                    slotsHtml += `
                        <a href="/planner" class="trip-pill-slot empty-slot">
                            <span>📍 + Célállomás</span>
                        </a>
                    `;
                }

                // Járat Slot
                if (f) {
                    slotsHtml += `
                        <div class="trip-pill-slot active-filled" onclick="TripCart.goToPlannerStep('flight')">
                            <span>✈️ ${f.airline} (${Math.round(f.price_total_huf || f.price_huf).toLocaleString()} Ft)</span>
                        </div>
                    `;
                } else if (d) {
                    slotsHtml += `
                        <a href="/planner?resume=flight" class="trip-pill-slot empty-slot" onclick="if(window.location.pathname.startsWith('/planner') && window.Wizard){ event.preventDefault(); window.Wizard.goToStep(2); }">
                            <span>✈️ + Járat</span>
                        </a>
                    `;
                } else {
                    slotsHtml += `
                        <a href="/planner?resume=flight" class="trip-pill-slot empty-slot">
                            <span>✈️ + Járat</span>
                        </a>
                    `;
                }

                // Szállás Slot
                if (s) {
                    slotsHtml += `
                        <div class="trip-pill-slot active-filled" onclick="TripCart.goToPlannerStep('stay')">
                            <span>🏨 ${s.name} (${Math.round(s.price_total_huf || s.price_huf).toLocaleString()} Ft)</span>
                        </div>
                    `;
                } else if (f && d) {
                    slotsHtml += `
                        <a href="/planner?resume=stay" class="trip-pill-slot empty-slot" onclick="if(window.location.pathname.startsWith('/planner') && window.Wizard){ event.preventDefault(); window.Wizard.goToStep(3); }">
                            <span>🏨 + Szállás</span>
                        </a>
                    `;
                } else if (d) {
                    slotsHtml += `
                        <a href="/planner?resume=stay" class="trip-pill-slot empty-slot" onclick="if(window.location.pathname.startsWith('/planner') && window.Wizard){ event.preventDefault(); window.Wizard.goToStep(3); }">
                            <span>🏨 + Szállás</span>
                        </a>
                    `;
                } else {
                    slotsHtml += `
                        <a href="/planner?resume=stay" class="trip-pill-slot empty-slot">
                            <span>🏨 + Szállás</span>
                        </a>
                    `;
                }

                slotsGroup.innerHTML = slotsHtml;
            }

            // 2. RENDER NEXT STEP CTA IN BAR
            const nextCta = this.getNextStepCTA();
            if (nextBtn) {
                nextBtn.innerText = nextCta.text;
                if (window.location.pathname.startsWith('/planner') && window.Wizard) {
                    nextBtn.onclick = (e) => {
                        e.preventDefault();
                        if (nextCta.step === 2) window.Wizard.goToStep(2);
                        else if (nextCta.step === 3) window.Wizard.goToStep(3);
                        else if (nextCta.step === 4) window.Wizard.goToStep(4);
                        else window.Wizard.goToStep(1);
                    };
                    nextBtn.removeAttribute('href');
                } else {
                    if (nextCta.action === 'open_drawer') {
                        nextBtn.onclick = () => this.showDrawer();
                        nextBtn.removeAttribute('href');
                    } else {
                        nextBtn.onclick = null;
                        nextBtn.href = nextCta.url;
                    }
                }
            }

            // 3. RENDER TOTALS & BREAKDOWN
            const breakdown = this.calculateBreakdown();
            if (barTotal) {
                barTotal.innerText = breakdown.totalHuf > 0 ? `${breakdown.totalHuf.toLocaleString()} Ft` : '0 Ft';
            }
            if (drawerTotal) {
                drawerTotal.innerHTML = `
                    <span>${breakdown.totalHuf.toLocaleString()} Ft</span>
                    ${breakdown.totalPersons > 1 ? `<span style="font-size: 13px; font-weight: 600; color: var(--text-muted); display: block;">(~${breakdown.perPersonTotal.toLocaleString()} Ft / fő)</span>` : ''}
                `;
            }

            // 4. RENDER DRAWER BODY & STATUS STEPPER
            if (drawerBody) {
                let drawerHtml = `
                    <!-- STEP PROGRESS INDICATOR -->
                    <div class="trip-workflow-stepper">
                        <div class="step-node ${d ? 'completed' : 'active'}">
                            <span class="step-num">${d ? '✓' : '1'}</span>
                            <span class="step-label">Célállomás</span>
                        </div>
                        <div class="step-connector ${f ? 'completed' : ''}"></div>
                        <div class="step-node ${f ? 'completed' : (d ? 'active' : '')}">
                            <span class="step-num">${f ? '✓' : '2'}</span>
                            <span class="step-label">Járat</span>
                        </div>
                        <div class="step-connector ${s ? 'completed' : ''}"></div>
                        <div class="step-node ${s ? 'completed' : (f ? 'active' : '')}">
                            <span class="step-num">${s ? '✓' : '3'}</span>
                            <span class="step-label">Szállás</span>
                        </div>
                    </div>
                `;

                // A) DESTINATION CARD
                if (d) {
                    drawerHtml += `
                        <div class="trip-card-slot filled">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type">📍 1. Kijelölt Célállomás</div>
                                <button type="button" class="trip-card-slot-remove" onclick="TripCart.removeDestination()">Eltávolítás</button>
                            </div>
                            <div class="trip-card-main-info">${d.name}, ${d.country}</div>
                            <div class="trip-card-sub-info">
                                🛫 Indulás: ${d.origin} • 🗓️ ${d.duration} nap (${d.adults} felnőtt${d.children > 0 ? `, ${d.children} gyerek` : ''})
                            </div>
                            ${d.explanation ? `<div style="font-size: 11.5px; color: var(--primary); margin-top: 4px;">✨ ${d.explanation}</div>` : ''}
                        </div>
                    `;
                } else {
                    drawerHtml += `
                        <div class="trip-card-slot">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type" style="color: var(--text-muted);">📍 1. Célállomás</div>
                            </div>
                            <div class="trip-card-empty-action">
                                <a href="/planner">
                                    <span>+ Célállomás választása a Plannerben</span>
                                </a>
                            </div>
                        </div>
                    `;
                }

                // B) FLIGHT CARD
                if (f) {
                    drawerHtml += `
                        <div class="trip-card-slot filled">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type">✈️ 2. Rögzített Repülőjegy</div>
                                <button type="button" class="trip-card-slot-remove" onclick="TripCart.removeFlight()">Eltávolítás</button>
                            </div>
                            <div class="trip-card-main-info">${f.airline || 'Légitársaság'} (Retúr járat)</div>
                            <div class="trip-card-sub-info">
                                ${f.out_date ? `🛫 Odaút: ${String(f.out_date).split('T')[0].split(' ')[0]}` : ''} ${f.in_date ? `• 🛬 Visszaút: ${String(f.in_date).split('T')[0].split(' ')[0]}` : ''}
                                (${f.exact_stay_nights || f.stay_days || 7} éjszaka)
                            </div>
                            <div class="trip-card-price-badge">${Math.round(f.price_total_huf || f.price_huf || 0).toLocaleString()} Ft (${f.adults || 1} főre)</div>

                        </div>
                    `;
                } else {
                    drawerHtml += `
                        <div class="trip-card-slot">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type" style="color: var(--text-muted);">✈️ 2. Járat kiválasztása</div>
                            </div>
                            <div class="trip-card-empty-action">
                                <a href="/planner?resume=flight">
                                    <span>+ Járat keresése és kiválasztása (${d ? d.name : 'Planner'})</span>
                                </a>
                            </div>
                        </div>
                    `;
                }

                // C) STAY CARD
                if (s) {
                    drawerHtml += `
                        <div class="trip-card-slot filled">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type">🏨 3. Rögzített Szállás</div>
                                <button type="button" class="trip-card-slot-remove" onclick="TripCart.removeStay()">Eltávolítás</button>
                            </div>
                            <div class="trip-card-main-info">${s.name} ${s.stars ? '⭐'.repeat(s.stars) : ''}</div>
                            <div class="trip-card-sub-info">
                                📍 ${s.address || s.city} • 🌙 ${s.nights} éjszaka ${s.rating ? `• Értékelés: ${s.rating}/10` : ''}
                            </div>
                            <div class="trip-card-price-badge">${Math.round(s.price_total_huf || s.price_huf).toLocaleString()} Ft</div>
                        </div>
                    `;
                } else {
                    drawerHtml += `
                        <div class="trip-card-slot">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type" style="color: var(--text-muted);">🏨 3. Szállás kiválasztása</div>
                            </div>
                            <div class="trip-card-empty-action">
                                <a href="/planner?resume=stay">
                                    <span>+ Szállás keresése és rögzítése</span>
                                </a>
                            </div>
                        </div>
                    `;
                }

                // D) MATHEMATICAL BREAKDOWN CARD
                if (breakdown.hasAny) {
                    drawerHtml += `
                        <div class="trip-breakdown-card">
                            <div class="trip-breakdown-header">
                                <span>📊 Tételes Költségkalkuláció</span>
                                <span style="font-size: 11px; font-weight: 600; color: var(--primary);">${breakdown.days} nap / ${breakdown.totalPersons} fő</span>
                            </div>
                            <div class="trip-breakdown-list">
                                ${breakdown.items.map(it => `
                                    <div class="breakdown-row">
                                        <div class="breakdown-left">
                                            <div class="breakdown-item-name">
                                                <span>${it.icon}</span>
                                                <span>${it.name}</span>
                                                <span class="breakdown-badge-tag">${it.badge}</span>
                                            </div>
                                            <div class="breakdown-formula">
                                                📐 ${it.formula}
                                            </div>
                                        </div>
                                        <div class="breakdown-right">
                                            <div class="breakdown-amount">${it.amount.toLocaleString()} Ft</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }

                // E) SHORTLIST ALTERNATIVES (IF ANY)
                const flightShortlist = trip.flight?.shortlist || [];
                const stayShortlist = trip.accommodation?.shortlist || [];
                if (flightShortlist.length > 0 || stayShortlist.length > 0) {
                    drawerHtml += `
                        <div style="margin-top: 14px; padding: 12px; background: rgba(0,0,0,0.02); border-radius: 12px; border: 1px dashed rgba(0,0,0,0.1);">
                            <div style="font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">
                                ⭐ Megjelölt Alternatívák (Shortlist)
                            </div>
                            ${flightShortlist.map(fl => `
                                <div style="font-size: 12px; display: flex; justify-content: space-between; margin-bottom: 4px;">
                                    <span>✈️ ${fl.airline} (${fl.out_date})</span>
                                    <strong>${Math.round(fl.price_total_huf || fl.price_huf).toLocaleString()} Ft</strong>
                                </div>
                            `).join('')}
                            ${stayShortlist.map(st => `
                                <div style="font-size: 12px; display: flex; justify-content: space-between; margin-bottom: 4px;">
                                    <span>🏨 ${st.name}</span>
                                    <strong>${Math.round(st.price_total_huf || st.price_huf).toLocaleString()} Ft</strong>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }

                drawerBody.innerHTML = drawerHtml;
            }
        },

        hideBar() {
            this.isBarHidden = true;
            const bar = document.getElementById('floatingTripBar');
            const reopenBtn = document.getElementById('tripFloatingReopenBtn');
            if (bar) bar.classList.remove('visible');
            if (reopenBtn) reopenBtn.classList.add('visible');
        },

        showBar() {
            this.isBarHidden = false;
            const bar = document.getElementById('floatingTripBar');
            const reopenBtn = document.getElementById('tripFloatingReopenBtn');
            if (bar) bar.classList.add('visible');
            if (reopenBtn) reopenBtn.classList.remove('visible');
        },

        showDrawer() {
            const drawer = document.getElementById('tripDrawerBackdrop');
            if (drawer) {
                this.render();
                drawer.classList.add('open');
            }
        },

        hideDrawer() {
            const drawer = document.getElementById('tripDrawerBackdrop');
            if (drawer) drawer.classList.remove('open');
        },

        showToast(message, icon = '✨') {
            if (typeof document === 'undefined' || !document.body) return;
            const toast = document.createElement('div');
            toast.className = 'trip-cart-toast';
            toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
            document.body.appendChild(toast);
            setTimeout(() => { if (toast.classList) toast.classList.add('show'); }, 10);
            setTimeout(() => {
                if (toast.classList) toast.classList.remove('show');
                setTimeout(() => { if (toast.remove) toast.remove(); }, 300);
            }, 3000);
        },

        // EXPORT B2B PROPOSAL (PDF / PRINT VIEW)
        exportProposal() {
            const trip = this.getTrip();
            const d = trip.destination;
            const f = trip.flight?.selected_flight;
            const s = trip.accommodation?.selected_accommodation;
            const breakdown = this.calculateBreakdown();

            const win = window.open('', '_blank');
            if (!win) {
                alert("Kérjük engedélyezd a felugró ablakokat az ajánlat megnyitásához!");
                return;
            }

            win.document.write(`
                <!DOCTYPE html>
                <html lang="hu">
                <head>
                    <meta charset="UTF-8">
                    <title>Optivoya Utazási Ajánlat — ${d ? d.name : 'Tervezet'}</title>
                    <style>
                        body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; margin: 40px; color: #1e293b; background: #fff; line-height: 1.5; }
                        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 30px; }
                        .logo { font-size: 24px; font-weight: 900; color: #0284c7; letter-spacing: -0.5px; }
                        .card { border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; background: #f8fafc; }
                        .card-title { font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
                        .card-val { font-size: 20px; font-weight: 800; color: #0284c7; }
                        .total-box { margin-top: 30px; padding: 24px; background: #0f172a; color: #fff; border-radius: 16px; display: flex; justify-content: space-between; align-items: center; }
                        .total-label { font-size: 14px; text-transform: uppercase; font-weight: 700; color: #94a3b8; }
                        .total-num { font-size: 32px; font-weight: 900; color: #38bdf8; }
                        .per-person-text { font-size: 15px; color: #cbd5e1; font-weight: 600; text-align: right; }
                        .calc-table { width: 100%; border-collapse: collapse; margin-top: 16px; background: #fff; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }
                        .calc-table th, .calc-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #f1f5f9; font-size: 13.5px; }
                        .calc-table th { background: #f8fafc; font-weight: 700; color: #475569; }
                        .formula-text { font-family: monospace; font-size: 12px; color: #0284c7; background: #f0f9ff; padding: 3px 8px; border-radius: 6px; }
                        @media print { .no-print { display: none; } body { margin: 20px; } }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div>
                            <div class="logo">✦ OPTIVOYA TRAVEL INTELLIGENCE</div>
                            <div style="color: #64748b; font-size: 13px; margin-top: 4px;">Hivatalos Utazási Ajánlat & Költségvetés</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: 700; font-size: 14px;">Azonosító: ${trip.trip_id}</div>
                            <div style="color: #64748b; font-size: 12px;">Dátum: ${new Date().toLocaleDateString('hu-HU')}</div>
                            <button class="no-print" onclick="window.print()" style="margin-top: 8px; padding: 6px 14px; background: #0284c7; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Nyomtatás / PDF mentés</button>
                        </div>
                    </div>

                    ${d ? `
                    <div class="card">
                        <div class="card-title">📍 Célállomás</div>
                        <div class="card-val">${d.name}, ${d.country}</div>
                        <div>Indulás: ${trip.input.origin} • ${breakdown.days} napos időszak (${breakdown.totalPersons} fő)</div>
                        ${d.explanation ? `<div style="margin-top: 6px; font-size: 12px; color: #64748b;">${d.explanation}</div>` : ''}
                    </div>` : ''}

                    ${f ? `
                    <div class="card">
                        <div class="card-title">✈️ Repülőjegy & Menetrend</div>
                        <div class="card-val">${f.airline} Retúr Járat</div>
                        <div>${f.out_date ? `Odaút: ${f.out_date}` : ''} ${f.in_date ? `• Visszaút: ${f.in_date}` : ''} (${f.adults} főre)</div>
                        <div style="margin-top: 8px; font-weight: 700; color: #0284c7;">${Math.round(f.price_total_huf || f.price_huf).toLocaleString()} Ft</div>
                    </div>` : ''}

                    ${s ? `
                    <div class="card">
                        <div class="card-title">🏨 Szállás</div>
                        <div class="card-val">${s.name} ${s.stars ? '⭐'.repeat(s.stars) : ''}</div>
                        <div>${s.nights} éjszaka ${s.rating ? `• Értékelés: ${s.rating}/10` : ''}</div>
                        <div style="margin-top: 8px; font-weight: 700; color: #0284c7;">${Math.round(s.price_total_huf || s.price_huf).toLocaleString()} Ft</div>
                    </div>` : ''}

                    <!-- DETAILED BREAKDOWN TABLE -->
                    <h3 style="margin-top: 28px; margin-bottom: 8px; font-size: 16px; color: #0f172a;">📊 Részletes Matematikai Költségkalkuláció (Numbeo + Valós Árak)</h3>
                    <table class="calc-table">
                        <thead>
                            <tr>
                                <th>Költségtétel</th>
                                <th>Számítási Képlet</th>
                                <th style="text-align: right;">Összeg</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${breakdown.items.map(it => `
                                <tr>
                                    <td><strong>${it.icon} ${it.name}</strong><br><small style="color: #64748b;">${it.desc}</small></td>
                                    <td><span class="formula-text">${it.formula}</span></td>
                                    <td style="text-align: right; font-weight: 800; font-family: monospace;">${it.amount.toLocaleString()} Ft</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>

                    <div class="total-box">
                        <div class="total-label">Becsült teljes utazási költség:</div>
                        <div>
                            <div class="total-num">${breakdown.totalHuf.toLocaleString()} Ft</div>
                            ${breakdown.totalPersons > 1 ? `<div class="per-person-text">~${breakdown.perPersonTotal.toLocaleString()} Ft / fő</div>` : ''}
                        </div>
                    </div>
                </body>
                </html>
            `);
            win.document.close();
        },

        goToPlannerStep(step) {
            const trip = this.getTrip();
            if (window.location.pathname.startsWith('/planner') && window.Wizard) {
                if (step === 'flight') window.Wizard.goToStep(2);
                else if (step === 'stay') window.Wizard.goToStep(3);
                else if (step === 'summary') window.Wizard.goToStep(4);
                else window.Wizard.goToStep(1);
            } else {
                if (step === 'flight' && trip.flight?.selected_flight) {
                    window.location.href = `/planner?resume=flight&change=flight`;
                } else {
                    window.location.href = `/planner?resume=${step}`;
                }
            }
        }

    };

    window.TripCart = TripEngine;
    window.TripEngine = TripEngine;

    document.addEventListener('DOMContentLoaded', () => {
        TripEngine.render();
    });
})();
