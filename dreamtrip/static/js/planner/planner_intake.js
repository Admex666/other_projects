/**
 * Optivoya — Master Planner Intake & Preferences Module
 * Handles origin autocomplete, date mode tabs, intake duration, steppers and Decision DNA card.
 */

(function () {
    const MONTH_NAMES = [
        "Január", "Február", "Március", "Április", "Május", "Június",
        "Július", "Augusztus", "Szeptember", "Október", "November", "December"
    ];

    const PlannerIntake = {
        setOrigin(city) {
            const inp = document.getElementById('origin');
            if (inp) inp.value = city;
            document.querySelectorAll('.quick-pill').forEach(el => {
                if (el.innerText.includes(city.split(' ')[0])) {
                    el.classList.add('active');
                } else {
                    el.classList.remove('active');
                }
            });
            if (window.PlannerState) window.PlannerState.intake.origin = city;
        },

        switchDateMode(mode) {
            if (!window.PlannerState) return;
            window.PlannerState.date_mode = mode;
            window.PlannerState.intake.date_mode = mode;
            const modes = ['exact', 'interval'];
            modes.forEach(m => {
                const btn = document.getElementById(`tab_mode_${m}`);
                const pnl = document.getElementById(`panel_mode_${m}`);
                const isActive = (m === mode);
                if (btn) {
                    btn.classList.toggle('active', isActive);
                    if (isActive) {
                        btn.style.background = 'var(--bg-surface)';
                        btn.style.color = 'var(--primary)';
                        btn.style.border = '1.5px solid var(--primary)';
                        btn.style.boxShadow = '0 2px 10px var(--accent-glow)';
                    } else {
                        btn.style.background = 'transparent';
                        btn.style.color = 'var(--text-muted)';
                        btn.style.border = '1.5px solid transparent';
                        btn.style.boxShadow = 'none';
                    }
                }
                if (pnl) {
                    pnl.style.display = isActive ? 'block' : 'none';
                }
            });
        },

        onDurationSliderChange(val) {
            const numVal = parseInt(val, 10) || 7;
            const num = document.getElementById('month_duration_input');
            const disp = document.getElementById('month_duration_display');
            const badge = document.getElementById('month_duration_badge');
            const sl = document.getElementById('month_duration_slider');
            if (sl) sl.value = numVal;
            if (num) num.value = numVal;
            if (disp) disp.innerText = `${numVal} nap`;
            if (badge) badge.innerText = `${numVal} napos utazás`;
            if (window.PlannerState) window.PlannerState.intake.duration = numVal;
        },

        initYearAndMonthPickers() {
            const yearSelect = document.getElementById('intake_year');
            const monthSelect = document.getElementById('intake_month');
            if (!yearSelect || !monthSelect) return;

            const now = new Date();
            const currentYear = now.getFullYear();
            const currentMonth = now.getMonth() + 1;

            yearSelect.innerHTML = '';
            for (let y = currentYear; y <= currentYear + 2; y++) {
                const opt = document.createElement('option');
                opt.value = y;
                opt.innerText = y;
                if (y === currentYear) opt.selected = true;
                yearSelect.appendChild(opt);
            }

            this.updateMonthDropdown(currentYear, currentMonth);
        },

        updateMonthDropdown(selectedYear, preferredMonth = null) {
            const monthSelect = document.getElementById('intake_month');
            if (!monthSelect) return;

            const now = new Date();
            const currentYear = now.getFullYear();
            const currentMonth = now.getMonth() + 1;
            const currentDay = now.getDate();

            const isCurrentYear = (parseInt(selectedYear, 10) === currentYear);
            const effectiveMinMonth = (isCurrentYear && currentDay >= 24) ? Math.min(12, currentMonth + 1) : currentMonth;
            const minMonth = isCurrentYear ? effectiveMinMonth : 1;

            const prevVal = preferredMonth !== null ? parseInt(preferredMonth, 10) : parseInt(monthSelect.value, 10);

            monthSelect.innerHTML = '';
            for (let m = minMonth; m <= 12; m++) {
                const opt = document.createElement('option');
                opt.value = m;
                opt.innerText = MONTH_NAMES[m - 1];
                monthSelect.appendChild(opt);
            }

            if (prevVal && prevVal >= minMonth && prevVal <= 12) {
                monthSelect.value = prevVal;
            } else {
                monthSelect.value = minMonth;
            }

            if (window.PlannerState) {
                window.PlannerState.intake.year = parseInt(selectedYear, 10);
                window.PlannerState.intake.month = String(monthSelect.value);
            }
        },

        onYearChange(year) {
            this.updateMonthDropdown(year);
        },

        onMonthChange(month) {
            if (window.PlannerState) window.PlannerState.intake.month = String(month);
        },

        applyExactPreset(daysFromNow, durationDays, btn) {
            if (window.PlannerState && window.PlannerState.exact_fp) {
                window.PlannerState.exact_fp.applyPreset(daysFromNow, durationDays);
                document.querySelectorAll('#panel_mode_exact .preset-pill').forEach(p => p.classList.remove('active'));
                if (btn) btn.classList.add('active');
            }
        },

        toggleDeparturePref(checked) {
            const box = document.getElementById('departure_time_box');
            if (box) box.style.display = checked ? 'block' : 'none';
            if (window.PlannerState) window.PlannerState.intake.has_departure_pref = checked;
        },

        onDepHourChange(val) {
            const hour = parseInt(val, 10) || 0;
            const badge = document.getElementById('dep_hour_badge');
            let label = `${String(hour).padStart(2, '0')}:00`;
            if (hour === 0) label += ' (Éjfél / Kora hajnal)';
            else if (hour > 0 && hour < 6) label += ' (Hajnal)';
            else if (hour >= 6 && hour < 12) label += ' (Reggel / Délelőtt)';
            else if (hour >= 12 && hour < 18) label += ' (Délután)';
            else label += ' (Este / Éjjel)';
            if (badge) badge.innerText = label;
            if (window.PlannerState) window.PlannerState.intake.departure_hour = hour;
        },

        setMaxDuration(hours) {
            const input = document.getElementById('intake_max_flight_duration');
            const disp = document.getElementById('intake_max_flight_duration_display');
            if (input) input.value = hours;
            if (disp) disp.innerText = hours === 0 ? 'Korlátlan' : `${hours} óra`;
            document.querySelectorAll('.quick-pill').forEach(el => {
                if (hours === 0 && el.innerText === 'Korlátlan') el.classList.add('active');
                else if (el.innerText.includes(`${hours}ó`)) el.classList.add('active');
                else if (el.innerText.includes('ó') || el.innerText === 'Korlátlan') el.classList.remove('active');
            });
            if (window.PlannerState) window.PlannerState.intake.max_flight_duration_h = hours;
        },

        onRatingChange(val) {
            const r = parseFloat(val) || 0;
            const badge = document.getElementById('hotel_rating_badge');
            let txt = `${r.toFixed(1)}+`;
            if (r >= 8.5) txt += ' Kiváló';
            else if (r >= 8.0) txt += ' Nagyon jó';
            else if (r >= 7.0) txt += ' Jó';
            else txt += ' Bármilyen';
            if (badge) badge.innerText = txt;
        },

        updateDecisionDNACard() {
            const unconf = document.getElementById('dna_unconfigured_view');
            const conf = document.getElementById('dna_configured_view');
            const submitBtn = document.getElementById('btn_submit_main_planner');
            const state = window.PlannerState;
            if (!state) return;

            if (state.criteria_completed) {
                if (unconf) unconf.style.display = 'none';
                if (conf) conf.style.display = 'block';

                const ahpEl = document.getElementById('dna_card_ahp_summary');
                if (ahpEl && state.intake.ahp_weights) {
                    const w = state.intake.ahp_weights;
                    ahpEl.innerHTML = `💰 ${w.total_cost}% · ☀️ ${w.weather}% · 🛡️ ${w.safety}%`;
                }

                const promEl = document.getElementById('dna_card_prom_summary');
                if (promEl && state.intake.promethee_params) {
                    const pPrice = state.intake.promethee_params.price;
                    const pDur = state.intake.promethee_params.duration;
                    const qPStr = pPrice.type === 5 ? `≤${(pPrice.q / 1000)}k Ft közömbös` : `Lineáris`;
                    const qDStr = pDur.type === 5 ? `≤${Math.round(pDur.q * 60)}p tűrés` : `Lineáris`;
                    promEl.innerHTML = `Ár: ${qPStr} · Menetidő: ${qDStr}`;
                }

                const stayEl = document.getElementById('dna_card_stay_summary');
                if (stayEl) {
                    const stars = state.intake.hotel_min_stars ? `${state.intake.hotel_min_stars}★+` : 'Bármilyen kategória';
                    const rating = `${state.intake.hotel_min_rating}+ Értékelés`;
                    const bf = state.intake.breakfast ? '· ☕ Reggelivel' : '';
                    stayEl.innerHTML = `${stars} · ${rating} ${bf}`;
                }

                if (submitBtn) {
                    submitBtn.innerHTML = `<span>2. Célállomások Keresése & Tervezés Indítása →</span>`;
                    submitBtn.onclick = () => window.PlannerDestinations.startPlanning();
                }
            } else {
                if (unconf) unconf.style.display = 'flex';
                if (conf) conf.style.display = 'none';

                if (submitBtn) {
                    submitBtn.innerHTML = `<span>1. Saját szempontok és prioritások beállítása →</span>`;
                    submitBtn.onclick = () => this.openDecisionDNA();
                }
            }
        },

        openDecisionDNA() {
            if (!window.DecisionDNAWizard || !window.PlannerState) return;
            const state = window.PlannerState;
            new window.DecisionDNAWizard({
                initialIntake: state.intake,
                onSave: function (savedDNA) {
                    if (savedDNA.ahp_weights) state.intake.ahp_weights = savedDNA.ahp_weights;
                    if (savedDNA.flight_ahp_weights) state.intake.flight_ahp_weights = savedDNA.flight_ahp_weights;
                    if (savedDNA.stay_ahp_weights) state.intake.stay_ahp_weights = savedDNA.stay_ahp_weights;
                    if (savedDNA.promethee_params) state.intake.promethee_params = savedDNA.promethee_params;
                    if (savedDNA.dest_promethee) state.intake.dest_promethee = savedDNA.dest_promethee;
                    if (savedDNA.stay_promethee) state.intake.stay_promethee = savedDNA.stay_promethee;
                    if (savedDNA.stay) {
                        state.intake.hotel_min_stars = savedDNA.stay.hotel_min_stars;
                        state.intake.hotel_min_rating = savedDNA.stay.hotel_min_rating;
                        state.intake.breakfast = savedDNA.stay.breakfast;
                        state.intake.hotel_types = savedDNA.stay.hotel_types;
                        state.intake.amenities = savedDNA.stay.amenities;
                    }
                    state.criteria_completed = true;
                    PlannerIntake.updateDecisionDNACard();

                    if (window.TripCart) {
                        window.TripCart.showToast("Döntési DNS élesítve! Célállomások betöltése...", "🧬");
                    }

                    // Invariant: Changing DNA triggers a fresh destination search and clears downstream selections
                    window.PlannerDestinations.startPlanning();
                }
            }).show();
        }
    };

    window.PlannerIntake = PlannerIntake;
})();
