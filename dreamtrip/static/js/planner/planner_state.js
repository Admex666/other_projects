/**
 * Optivoya — Master Planner State & Navigation Module
 * Central reactive state store, stepper synchronization, and cache management.
 */

(function () {
    const _now = new Date();
    _now.setHours(0, 0, 0, 0);
    const _addDays = (d, n) => {
        const r = new Date(d);
        r.setDate(r.getDate() + n);
        return r;
    };
    const _toIso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    
    // Default departure: 3 weeks (21 days) from today
    const _defOut = _addDays(_now, 21);
    const _defIn = _addDays(_defOut, 7);
    const _outWindowEnd = _addDays(_defOut, 14);
    const _inWindowStart = _addDays(_defOut, 7);
    const _inWindowEnd = _addDays(_defOut, 21);

    const PlannerState = {
        step: 0,
        date_mode: 'exact',
        exact_fp: null,
        interval_out_fp: null,
        interval_in_fp: null,
        criteria_completed: false,
        pollInterval: null,
        dummy_mode: localStorage.getItem('optivoya_dummy_mode') === 'true',

        toggleDummyMode(enabled) {
            this.dummy_mode = Boolean(enabled);
            localStorage.setItem('optivoya_dummy_mode', this.dummy_mode ? 'true' : 'false');
            this.updateDummyModeUI();
            if (typeof showToast === 'function') {
                showToast(this.dummy_mode ? 'Szimulációs mód aktív (Dummy adatok — 0 token).' : 'Élő keresések aktívak.', 'info');
            }
        },

        updateDummyModeUI() {
            const toggle = document.getElementById('dummyModeToggle');
            if (toggle) toggle.checked = this.dummy_mode;
            const label = document.getElementById('dummyModeStatusLabel');
            if (label) label.innerText = this.dummy_mode ? 'Dummy BE' : 'Dummy KI';
            const widget = document.getElementById('dummyModeWidget');
            if (widget) {
                widget.style.background = this.dummy_mode ? 'rgba(245, 158, 11, 0.12)' : 'var(--bg-surface-subtle)';
                widget.style.borderColor = this.dummy_mode ? 'rgba(245, 158, 11, 0.5)' : 'var(--border-subtle)';
            }
        },

        getSessionId() {
            return (window.OptivoyaTelemetry && window.OptivoyaTelemetry.sessionId) 
                || sessionStorage.getItem('optivoya_session_id') 
                || 'sess_planner';
        },

        intake: {
            origin: "Budapest (BUD)",
            adults: 2,
            children: 0,
            date_mode: "exact",
            month: String(_defOut.getMonth() + 1),
            year: _defOut.getFullYear(),
            duration: 7,
            exact_out_date: _toIso(_defOut),
            exact_in_date: _toIso(_defIn),
            out_from: _toIso(_defOut),
            out_to: _toIso(_outWindowEnd),
            in_from: _toIso(_inWindowStart),
            in_to: _toIso(_inWindowEnd),
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
                total_cost: 25.0,
                weather: 25.0,
                safety: 25.0,
                experience: 25.0
            },
            experience_preferences: {
                culture: 70,
                gastronomy: 80,
                beach: 50,
                nature: 60,
                nightlife: 40,
                authenticity: 75,
                relaxation: 60,
                adventure: 40
            },
            logistics_preferences: {
                day_start: "09:00",
                day_end: "20:00",
                lunch_window: "13:00-14:00",
                dinner_window: "19:30-21:00",
                max_walking_minutes: 30,
                preferred_transit: "walking"
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
        selectedActivities: [],

        canAccessStep(stepNum) {
            if (stepNum === 0) return true; // Preferenciák mindig elérhető
            if (stepNum === 1) {
                // Célállomások csak akkor, ha már lefutott a keresés és vannak célállomások
                return Boolean(this.destinations && this.destinations.length > 0);
            }
            if (stepNum === 2) {
                // Járatok csak akkor, ha van kiválasztott célállomás és vannak járatok
                return Boolean(this.selectedDest && this.flights && this.flights.length > 0);
            }
            if (stepNum === 3) {
                // Szállások csak akkor, ha van kiválasztott célállomás + járat és vannak szállások
                return Boolean(this.selectedDest && this.selectedFlight && this.stays && this.stays.length > 0);
            }
            if (stepNum === 4) {
                // Programok csak akkor, ha van kiválasztott célállomás + járat + szállás
                return Boolean(this.selectedDest && this.selectedFlight && this.selectedStay);
            }
            if (stepNum === 5) {
                // Kész Terv csak akkor, ha van kiválasztott célállomás + járat + szállás
                return Boolean(this.selectedDest && this.selectedFlight && this.selectedStay);
            }
            return false;
        },

        setStep(stepNum, force = false) {
            if (!force && !this.canAccessStep(stepNum)) {
                console.warn(`[STEP BLOCKED] Lépés (${stepNum}) még nem érhető el.`);
                // Ha a felhasználó egy még nem elérhető lépésre kattintott, jelezzük finoman
                const toastFn = window.showToast || (window.TripCart && window.TripCart.showToast);
                if (typeof toastFn === 'function') {
                    const stepNames = ["Preferenciák", "Célállomás", "Járat", "Szállás", "Programok", "Kész Terv"];
                    toastFn(`Kérlek először fejezd be a korábbi lépést a(z) "${stepNames[stepNum] || stepNum}" feloldásához!`, 'info');
                }
                return false;
            }

            if (window.OptivoyaTelemetry && this.step !== stepNum) {
                window.OptivoyaTelemetry.trackEvent('step_navigation', 'master_planner', {
                    to_step: stepNum,
                    from_step: this.step,
                    step_name: ["Preferenciák", "Célállomás", "Járat", "Szállás", "Programok", "Kész Terv"][stepNum] || String(stepNum)
                });
            }

            this.step = stepNum;

            // Ha visszalépünk egy korábbi lépésre, győződjünk meg róla, hogy a nézet ki van rajzolva
            if (stepNum === 1 && window.PlannerDestinations && this.destinations && this.destinations.length > 0) {
                window.PlannerDestinations.renderDestinations();
            } else if (stepNum === 2 && window.PlannerFlights && this.flights && this.flights.length > 0) {
                window.PlannerFlights.renderFlights();
            } else if (stepNum === 3 && window.PlannerStays && this.stays && this.stays.length > 0) {
                window.PlannerStays.renderStays();
            } else if (stepNum === 4 && window.PlannerActivities) {
                window.PlannerActivities.initActivities();
            } else if (stepNum === 5 && window.PlannerSummary) {
                window.PlannerSummary.renderFinalSummary();
            }

            this.updateStepperUI();

            const loader = document.getElementById('wizardLoading');
            if (loader) loader.style.display = 'none';

            window.scrollTo({ top: 0, behavior: 'smooth' });
            return true;
        },

        updateStepperUI() {
            for (let i = 0; i <= 5; i++) {
                const node = document.getElementById(`stepNode${i}`);
                const conn = document.getElementById(`stepConn${i}`);
                const sec = document.getElementById(`wizardStep${i}`);
                const isAccessible = this.canAccessStep(i);

                if (node) {
                    node.classList.remove('active', 'completed', 'disabled');
                    if (i < this.step) {
                        node.classList.add('completed');
                    } else if (i === this.step) {
                        node.classList.add('active');
                    }

                    if (!isAccessible && i > this.step) {
                        node.classList.add('disabled');
                        node.style.cursor = 'not-allowed';
                        node.style.opacity = '0.45';
                    } else {
                        node.style.cursor = 'pointer';
                        node.style.opacity = '1';
                    }
                }

                if (conn) {
                    conn.classList.remove('completed');
                    if (i < this.step) conn.classList.add('completed');
                }

                if (sec) {
                    sec.style.display = (i === this.step) ? 'block' : 'none';
                }
            }
        },


        showLoader(title, subtitle) {
            for (let i = 0; i <= 5; i++) {
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
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => PlannerState.updateDummyModeUI());
    } else {
        PlannerState.updateDummyModeUI();
    }
})();
