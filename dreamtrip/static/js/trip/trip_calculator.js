/**
 * Optivoya — Trip Calculator & Cost Engine Module
 * Single Source of Truth for 3 Numbeo dining profiles, transit formulas, flights & stay costs.
 */

(function () {
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

    const TripCalculator = {
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

        calculateBreakdown(trip) {
            if (!trip) trip = window.TripStore ? window.TripStore.getTrip() : null;
            if (!trip) return { items: [], totalHuf: 0, perPersonTotal: 0, days: 7, adults: 2, children: 0, totalPersons: 2, hasAny: false };

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
                    icon: '',
                    name: 'Odajutás és visszajutás (Repülőjegy irányár)',
                    desc: `Irányadó retúr járat ${trip.destination.origin} indulással`,
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
                    icon: '',
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
                    icon: '',
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

            // 3. ÉTELEK ÉS ÉTKEZÉSEK
            if (trip.destination) {
                const numbeoData = (trip.destination.numbeo && trip.destination.numbeo.meal_inexpensive)
                    ? trip.destination.numbeo
                    : this.getNumbeoMetrics(trip.destination.city || trip.destination.name);

                const eurRate = numbeoData.eur_rate || window.OPTIVOYA_EUR_RATE || 395;
                const mealInexpensive = numbeoData.meal_inexpensive || 14.0;
                const mealMidrange = numbeoData.meal_midrange || 28.0;
                const coffee = numbeoData.coffee || 2.5;

                const activeProfileKey = trip.dining_profile || 'standard';
                let profileInfo = null;

                if (numbeoData.profiles && numbeoData.profiles[activeProfileKey]) {
                    profileInfo = numbeoData.profiles[activeProfileKey];
                } else {
                    if (activeProfileKey === 'budget') {
                        const foodEur = Math.round((mealInexpensive * 2.5 + coffee * 1.0) * 10) / 10;
                        profileInfo = {
                            name: 'Takarékos',
                            icon: '',
                            daily_food_eur: foodEur,
                            daily_food_huf: Math.round(foodEur * eurRate),
                            formula: '2.5 × olcsó étkezés + 1 × kávé'
                        };
                    } else if (activeProfileKey === 'comfort') {
                        const foodEur = Math.round((mealInexpensive * 1.0 + mealMidrange * 1.0 + coffee * 2.0) * 10) / 10;
                        profileInfo = {
                            name: 'Kényelmes',
                            icon: '',
                            daily_food_eur: foodEur,
                            daily_food_huf: Math.round(foodEur * eurRate),
                            formula: '1 × olcsó étkezés + 1 × 2-személyes étkezés + 2 × kávé'
                        };
                    } else {
                        const foodEur = Math.round((mealInexpensive * 2.0 + mealMidrange * 0.5 + coffee * 1.0) * 10) / 10;
                        profileInfo = {
                            name: 'Átlagos',
                            icon: '',
                            daily_food_eur: foodEur,
                            daily_food_huf: Math.round(foodEur * eurRate),
                            formula: '2 × olcsó étkezés + 0.5 × 2-személyes vacsora + 1 × kávé'
                        };
                    }
                }

                const dailyFoodHuf = profileInfo.daily_food_huf;
                const foodTotalHuf = dailyFoodHuf * days * totalPersons;

                items.push({
                    key: 'food',
                    icon: '',
                    name: `Ételek & étkezések [${profileInfo.name} profil] (${trip.destination.name})`,
                    desc: `Helyi árszínvonal: Olcsó étkezés: €${mealInexpensive.toFixed(1)} | 3-fogásos vacsora (2 fő): €${mealMidrange.toFixed(1)} | Kávé: €${coffee.toFixed(1)}`,
                    formula: `${dailyFoodHuf.toLocaleString()} Ft / nap / fő (${profileInfo.formula}) × ${days} nap × ${totalPersons} fő`,
                    amount: foodTotalHuf,
                    badge: `Profil: ${profileInfo.name}`,
                    isEstimated: false
                });
                totalHuf += foodTotalHuf;
                hasAny = true;
            }

            // 4. HELYI KÖZLEKEDÉS
            if (trip.destination) {
                const numbeoData = (trip.destination.numbeo && (trip.destination.numbeo.transport_ticket || trip.destination.numbeo.transport))
                    ? trip.destination.numbeo
                    : this.getNumbeoMetrics(trip.destination.city || trip.destination.name);

                const eurRate = numbeoData.eur_rate || window.OPTIVOYA_EUR_RATE || 395;
                const ticketEur = numbeoData.transport_ticket || numbeoData.transport || 2.0;
                const transitDailyHuf = numbeoData.daily_transit_huf || Math.round((ticketEur * 2) * eurRate);
                const ticketHuf = Math.round(ticketEur * eurRate);
                const transitTotalHuf = transitDailyHuf * days * totalPersons;

                items.push({
                    key: 'transit',
                    icon: '',
                    name: `Helyi tömegközlekedés (${trip.destination.name})`,
                    desc: `Helyi vonaljegy: €${ticketEur.toFixed(2)} (~${ticketHuf.toLocaleString()} Ft / jegy)`,
                    formula: `${transitDailyHuf.toLocaleString()} Ft / nap / fő (2 jegy/nap) × ${days} nap × ${totalPersons} fő`,
                    amount: transitTotalHuf,
                    badge: 'Helyi árak',
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
        }
    };

    window.TripCalculator = TripCalculator;
})();
