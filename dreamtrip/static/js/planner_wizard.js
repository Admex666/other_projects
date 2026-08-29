/**
 * Optivoya — Master Travel Planner Wizard Engine v2
 * Fully unified intake, flatpickr date integration, modal criteria prioritization wizards (Destination & Stay),
 * circular + - steppers, and automated flight/stay chaining.
 */

window.Wizard = (function() {
    let state = {
        step: 0,
        date_mode: 'month',
        exact_fp: null,
        intake: {
            origin: "Budapest (BUD)",
            adults: 2,
            children: 0,
            date_mode: "month",
            month: "9",
            duration: 7,
            exact_out_date: "2026-09-10",
            exact_in_date: "2026-09-17",
            out_from: "2026-09-01",
            out_to: "2026-09-15",
            in_to: "2026-09-30",
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
                total_cost: 34.0,
                weather: 33.0,
                safety: 33.0
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
        selectedStay: null
    };

    let pollInterval = null;

    function setStep(stepNum) {
        state.step = stepNum;

        // Update Stepper UI
        for (let i = 0; i <= 4; i++) {
            const node = document.getElementById(`stepNode${i}`);
            const conn = document.getElementById(`stepConn${i}`);
            const sec = document.getElementById(`wizardStep${i}`);

            if (node) {
                node.classList.remove('active', 'completed');
                if (i < stepNum) node.classList.add('completed');
                else if (i === stepNum) node.classList.add('active');
            }

            if (conn) {
                conn.classList.remove('completed');
                if (i < stepNum) conn.classList.add('completed');
            }

            if (sec) {
                sec.style.display = (i === stepNum) ? 'block' : 'none';
            }
        }

        const loader = document.getElementById('wizardLoading');
        if (loader) loader.style.display = 'none';

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function showLoader(title, subtitle) {
        for (let i = 0; i <= 4; i++) {
            const sec = document.getElementById(`wizardStep${i}`);
            if (sec) sec.style.display = 'none';
        }
        const loader = document.getElementById('wizardLoading');
        if (loader) {
            loader.style.display = 'block';
            document.getElementById('wizardLoadingTitle').innerText = title || "Elemzés folyamatban...";
            document.getElementById('wizardLoadingSubtitle').innerText = subtitle || "Valós éghajlati, járat- és szállásadatok feldolgozása...";
            document.getElementById('wizardProgressBar').style.width = '20%';
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function setOrigin(city) {
        const inp = document.getElementById('origin');
        if (inp) inp.value = city;
        document.querySelectorAll('.quick-pill').forEach(el => {
            if (el.innerText.includes(city.split(' ')[0])) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });
    }

    function switchDateMode(mode) {
        state.date_mode = mode;
        state.intake.date_mode = mode;
        const modes = ['month', 'interval', 'exact'];
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
    }

    function onDurationSliderChange(val) {
        const numVal = parseInt(val, 10) || 7;
        const num = document.getElementById('month_duration_input');
        const disp = document.getElementById('month_duration_display');
        const badge = document.getElementById('month_duration_badge');
        const sl = document.getElementById('month_duration_slider');
        if (sl) sl.value = numVal;
        if (num) num.value = numVal;
        if (disp) disp.innerText = `${numVal} nap`;
        if (badge) badge.innerText = `${numVal} napos utazás`;
        state.intake.duration = numVal;
    }

    const MONTH_NAMES = [
        "Január", "Február", "Március", "Április", "Május", "Június",
        "Július", "Augusztus", "Szeptember", "Október", "November", "December"
    ];

    function initYearAndMonthPickers() {
        const yearSelect = document.getElementById('intake_year');
        const monthSelect = document.getElementById('intake_month');
        if (!yearSelect || !monthSelect) return;

        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1; // 1-12

        yearSelect.innerHTML = '';
        for (let y = currentYear; y <= currentYear + 2; y++) {
            const opt = document.createElement('option');
            opt.value = y;
            opt.innerText = y;
            if (y === currentYear) opt.selected = true;
            yearSelect.appendChild(opt);
        }

        updateMonthDropdown(currentYear, currentMonth);
    }

    function updateMonthDropdown(selectedYear, preferredMonth = null) {
        const monthSelect = document.getElementById('intake_month');
        if (!monthSelect) return;

        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;
        const currentDay = now.getDate();

        const isCurrentYear = (parseInt(selectedYear, 10) === currentYear);
        // Ha a hónap utolsó napjaiban járunk (24. nap után), a jelenlegi hónap helyett a következő hónaptól induljon
        const effectiveMinMonth = (isCurrentYear && currentDay >= 24) ? Math.min(12, currentMonth + 1) : currentMonth;
        const minMonth = isCurrentYear ? effectiveMinMonth : 1;

        const prevVal = preferredMonth !== null ? parseInt(preferredMonth, 10) : parseInt(monthSelect.value, 10);

        monthSelect.innerHTML = '';
        for (let m = minMonth; m <= 12; m++) {
            const opt = document.createElement('option');
            opt.value = m;
            opt.innerText = MONTH_NAMES[m - 1]; // Clean Hungarian month name only
            monthSelect.appendChild(opt);
        }

        if (prevVal && prevVal >= minMonth && prevVal <= 12) {
            monthSelect.value = prevVal;
        } else {
            monthSelect.value = minMonth;
        }

        state.intake.year = parseInt(selectedYear, 10);
        state.intake.month = String(monthSelect.value);
    }

    function onYearChange(year) {
        updateMonthDropdown(year);
    }

    function onMonthChange(month) {
        state.intake.month = String(month);
    }

    function applyExactPreset(daysFromNow, durationDays, btn) {
        if (state.exact_fp) {
            state.exact_fp.applyPreset(daysFromNow, durationDays);
            document.querySelectorAll('#panel_mode_exact .preset-pill').forEach(p => p.classList.remove('active'));
            if (btn) btn.classList.add('active');
        }
    }

    function toggleDeparturePref(checked) {
        const box = document.getElementById('departure_time_box');
        if (box) box.style.display = checked ? 'block' : 'none';
        state.intake.has_departure_pref = checked;
    }

    function onDepHourChange(val) {
        const hour = parseInt(val, 10) || 0;
        const badge = document.getElementById('dep_hour_badge');
        let label = `${String(hour).padStart(2, '0')}:00`;
        if (hour === 0) label += ' (Éjfél / Kora hajnal)';
        else if (hour > 0 && hour < 6) label += ' (Hajnal)';
        else if (hour >= 6 && hour < 12) label += ' (Reggel / Délelőtt)';
        else if (hour >= 12 && hour < 18) label += ' (Délután)';
        else label += ' (Este / Éjjel)';
        if (badge) badge.innerText = label;
        state.intake.departure_hour = hour;
    }

    function setMaxDuration(hours) {
        const input = document.getElementById('intake_max_flight_duration');
        const disp = document.getElementById('intake_max_flight_duration_display');
        if (input) input.value = hours;
        if (disp) disp.innerText = hours === 0 ? 'Korlátlan' : `${hours} óra`;
        document.querySelectorAll('.quick-pill').forEach(el => {
            if (hours === 0 && el.innerText === 'Korlátlan') el.classList.add('active');
            else if (el.innerText.includes(`${hours}ó`)) el.classList.add('active');
            else if (el.innerText.includes('ó') || el.innerText === 'Korlátlan') el.classList.remove('active');
        });
        state.intake.max_flight_duration_h = hours;
    }

    function onRatingChange(val) {
        const r = parseFloat(val) || 0;
        const badge = document.getElementById('hotel_rating_badge');
        let txt = `${r.toFixed(1)}+`;
        if (r >= 8.5) txt += ' Kiváló';
        else if (r >= 8.0) txt += ' Nagyon jó';
        else if (r >= 7.0) txt += ' Jó';
        else txt += ' Bármilyen';
        if (badge) badge.innerText = txt;
    }

    function updateAHPBadges(w) {
        state.criteria_completed = true;
        state.intake.ahp_weights = w;
        const bCost = document.getElementById('ahp_badge_cost');
        const bWeather = document.getElementById('ahp_badge_weather');
        const bSafety = document.getElementById('ahp_badge_safety');

        const costVal = w.total_cost !== undefined ? w.total_cost : (w.cost !== undefined ? (w.cost + (w.flight || 0)) : 34);
        if (bCost) bCost.innerText = `${Math.round(costVal)}%`;
        if (bWeather) bWeather.innerText = `${Math.round(w.weather || 33)}%`;
        if (bSafety) bSafety.innerText = `${Math.round(w.safety || 33)}%`;

        const box = document.getElementById('criteria_status_box');
        const txt = document.getElementById('criteria_status_text');
        const btnLabel = document.getElementById('criteria_btn_label');
        const lockWrapper = document.getElementById('details_progressive_lock_wrapper');

        if (box) {
            box.style.background = 'rgba(16, 185, 129, 0.1)';
            box.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        }
        if (txt) {
            txt.innerText = '✓ Prioritások sikeresen rögzítve! A 4. és 5. pont szűrői feloldva.';
        }
        if (btnLabel) {
            btnLabel.innerText = '✓ Prioritások Módosítása';
        }
        if (lockWrapper) {
            lockWrapper.style.opacity = '1.0';
            lockWrapper.style.pointerEvents = 'auto';
            lockWrapper.style.filter = 'none';
        }
    }

    function openAHPModal() {
        const backdrop = document.getElementById('ahpModalBackdrop');
        const container = document.getElementById('ahp_wizard_render_container');
        if (!backdrop || !container) return;

        backdrop.style.display = 'flex';
        container.innerHTML = '';

        const criteria = [
            { id: 'total_cost', name: 'Teljes Utazási Költség', icon: '💰', desc: 'Repülőjegy, szállás és helyi megélhetés (étkezés, közlekedés) teljes összege' },
            { id: 'weather', name: 'Időjárás / Klíma', icon: '☀️', desc: 'Ideális célhőmérséklethez és kellemes időjáráshoz való illeszkedés' },
            { id: 'safety', name: 'Közbiztonság', icon: '🛡️', desc: 'Biztonsági index, megbízhatóság és utazási nyugalom' }
        ];

        new AHPWizard({
            containerId: 'ahp_wizard_render_container',
            criteria: criteria,
            title: 'Döntési Szempontok Prioritása',
            subtitle: 'Hasonlítsd össze a 3 fő szempontot páronként (mindössze 3 gyors kérdés)',
            badge: 'Prioritási Kérdőív',
            introTitle: 'Mi a legfontosabb számodra a célállomás kiválasztásakor?',
            introDesc: 'A 3 fő pillér (Összköltség, Klíma, Biztonság) páros súlyozása alapján személyre szabjuk a rangsort és feloldjuk a további szűrőket.',
            ctaText: 'Prioritások mentése & Bezárás',
            onBack: () => closeAHPModal(),
            onComplete: function(result) {
                console.log("[DESTINATION CRITERIA COMPLETED]", result);
                if (result.cr !== undefined) console.log(`[CONFORMITY CHECK] CR=${result.cr.toFixed(4)}`);

                const rawW = result.weights || {};
                const total = (rawW.total_cost || 0.34) + (rawW.weather || 0.33) + (rawW.safety || 0.33);
                const w = {
                    total_cost: Math.round(((rawW.total_cost || 0.34) / total) * 100),
                    weather: Math.round(((rawW.weather || 0.33) / total) * 100),
                    safety: Math.round(((rawW.safety || 0.33) / total) * 100)
                };

                updateAHPBadges(w);
                closeAHPModal();
            }
        });
    }

    function openStayPrioritiesModal() {
        const backdrop = document.getElementById('ahpModalBackdrop');
        const container = document.getElementById('ahp_wizard_render_container');
        if (!backdrop || !container) return;

        backdrop.style.display = 'flex';
        container.innerHTML = '';

        const stayCriteria = [
            { id: 'price', name: 'Szállás Ára / Éjszaka', icon: '💳', desc: 'Kedvező éjszakánkénti ár előnyben részesítése' },
            { id: 'rating', name: 'Értékelés & Csillagok', icon: '⭐', desc: 'Magas vendégértékelés és megbízható minőség' },
            { id: 'location', name: 'Központi Elhelyezkedés', icon: '📍', desc: 'Városközpont vagy strand közelsége' },
            { id: 'amenities', name: 'Felszereltség & Reggeli', icon: '☕', desc: 'Ingyenes reggeli, medence vagy wellness megléte' }
        ];

        new AHPWizard({
            containerId: 'ahp_wizard_render_container',
            criteria: stayCriteria,
            title: 'Szállás Szempontok Prioritása',
            subtitle: 'Hasonlítsd össze a 4 szálláskritériumot páronként',
            badge: 'Szállás Prioritások',
            introTitle: 'Mi a legfontosabb számodra a szállás kiválasztásakor?',
            introDesc: 'Állítsd be, hogy az ár, a vendégértékelés, a központi elhelyezkedés vagy a reggeli/wellness a meghatározóbb a szállások rangsorolásakor.',
            ctaText: 'Szállás prioritások mentése & Bezárás',
            onBack: () => closeAHPModal(),
            onComplete: function(result) {
                console.log("[STAY CRITERIA COMPLETED]", result);
                if (result.cr !== undefined) console.log(`[CONFORMITY CHECK] CR=${result.cr.toFixed(4)}`);

                const rawW = result.weights || {};
                const total = (rawW.price || 0.25) + (rawW.rating || 0.25) + (rawW.location || 0.25) + (rawW.amenities || 0.25);
                state.intake.stay_weights = {
                    price: Math.round(((rawW.price || 0.25) / total) * 100),
                    rating: Math.round(((rawW.rating || 0.25) / total) * 100),
                    location: Math.round(((rawW.location || 0.25) / total) * 100),
                    amenities: Math.round(((rawW.amenities || 0.25) / total) * 100)
                };

                closeAHPModal();
            }
        });
    }

    function closeAHPModal() {
        const backdrop = document.getElementById('ahpModalBackdrop');
        if (backdrop) backdrop.style.display = 'none';
    }

    async function startPlanning() {
        if (!state.criteria_completed) {
            openAHPModal();
            return;
        }

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

        showLoader(
            "Célállomások Kiértékelése és Rangsorolása",
            "Open-Meteo klímaadatok, Kiwi repülőjegy árak és megélhetési indexek összehasonlítása az egyéni prioritások alapján..."
        );

        try {
            await fetch('/api/planner/init-destinations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(state.intake)
            });

            if (pollInterval) clearInterval(pollInterval);
            pollInterval = setInterval(pollDestinations, 1200);
        } catch (e) {
            alert("Hiba a keresés indításakor: " + e.message);
            setStep(0);
        }
    }

    async function pollDestinations() {
        try {
            const res = await fetch('/api/planner/destinations-status');
            const data = await res.json();

            const pBar = document.getElementById('wizardProgressBar');
            const pSub = document.getElementById('wizardLoadingSubtitle');

            if (data.status === 'running') {
                if (pBar) pBar.style.width = (data.progress || 30) + '%';
                if (pSub && data.status_text) pSub.innerText = data.status_text;
            } else if (data.status === 'done') {
                clearInterval(pollInterval);
                if (pBar) pBar.style.width = '100%';

                state.destinations = data.results || [];
                renderDestinations();
                setStep(1);
            } else if (data.status === 'error') {
                clearInterval(pollInterval);
                alert("Hiba történt a kalkuláció során: " + (data.error || 'Ismeretlen hiba'));
                setStep(0);
            }
        } catch (e) {
            console.error("Poll error:", e);
        }
    }

    function renderDestinations() {
        const grid = document.getElementById('destinationsGrid');
        if (!grid) return;

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
    }

    async function triggerFlightSearch(dest) {
        if (!dest) return;
        state.selectedDest = dest;
        const destName = dest.name || dest.city;

        const fCity = document.getElementById('flightContextCity');
        const fDetails = document.getElementById('flightContextDetails');
        if (fCity) fCity.innerText = destName;
        if (fDetails) fDetails.innerText = `${state.intake.origin} → ${destName} • ${state.intake.adults} felnőtt • ${state.intake.duration} nap`;

        showLoader(
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
                    weights: state.intake.ahp_weights
                })
            });

            const data = await res.json();
            if (data.status === 'ok') {
                state.flights = data.flights || [];
                renderFlights();
                setStep(2);
            } else {
                alert("Nem sikerült járatokat találni: " + (data.error || 'Hiba'));
                setStep(1);
            }
        } catch (e) {
            alert("Járatkeresési hiba: " + e.message);
            setStep(1);
        }
    }

    async function selectDestination(index) {
        const dest = state.destinations[index];
        if (!dest) return;

        state.selectedDest = dest;

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

        await triggerFlightSearch(dest);
    }

    function renderFlights() {
        const container = document.getElementById('flightsGrid');
        if (!container) return;

        if (state.flights.length === 0) {
            container.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--text-secondary);">Nem találtunk járatot a megadott szigorú feltételekkel. Kérlek módosíts az átszállás tolerancián a fenti menüben!</div>`;
            return;
        }

        container.innerHTML = state.flights.map((fl, idx) => {
            const outDate = (fl.out_dep_time || '').split('T')[0];
            const inDate = (fl.in_dep_time || '').split('T')[0];
            const outTime = (fl.out_dep_time || '').split('T')[1]?.slice(0, 5) || 'Reggel';
            const inTime = (fl.in_dep_time || '').split('T')[1]?.slice(0, 5) || 'Este';
            const nights = fl.stay_days || state.intake.duration;
            const priceTotal = fl.total_price_huf || 0;
            const pricePerPerson = Math.round(priceTotal / Math.max(1, state.intake.adults));

            return `
                <div class="advisor-main-card" style="background: var(--bg-surface); border: 1.5px solid var(--border-subtle); border-radius: 16px; padding: 20px 24px; display: grid; grid-template-columns: 1fr auto; gap: 20px; align-items: center;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                            <span style="font-size: 16px; font-weight: 900; color: var(--text-main);">${fl.out_airline || fl.in_airline || 'Légitársaság'}</span>
                            <span style="background: var(--bg-surface-subtle); font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; color: var(--primary);">
                                #${fl.rank || (idx + 1)} Ajánlat
                            </span>
                            <span style="font-size: 12px; font-weight: 700; color: var(--status-success, #10b981);">
                                ${Math.round((fl.phi_net || 0.85) * 100)}% Relevancia
                            </span>
                        </div>

                        <div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 13.5px; color: var(--text-secondary); margin-bottom: 6px;">
                            <div>🛫 <strong>Odaút:</strong> ${outDate} (${outTime}) • ${fl.out_stops === 0 ? 'Közvetlen' : fl.out_stops + ' átszállás'}</div>
                            <div>🛬 <strong>Visszaút:</strong> ${inDate} (${inTime}) • ${fl.in_stops === 0 ? 'Közvetlen' : fl.in_stops + ' átszállás'}</div>
                        </div>

                        <div style="font-size: 12px; color: var(--text-muted);">
                            🌙 Tartózkodás: <strong>${nights} éjszaka</strong> (${state.selectedDest?.name || 'Célállomás'})
                        </div>
                    </div>

                    <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
                        <div>
                            <div style="font-size: 22px; font-weight: 900; color: var(--primary); font-family: var(--font-mono);">${Math.round(priceTotal).toLocaleString()} Ft</div>
                            <div style="font-size: 12px; color: var(--text-muted); font-weight: 600;">~${pricePerPerson.toLocaleString()} Ft / fő</div>
                        </div>
                        <button type="button" class="btn btn-primary" onclick="Wizard.selectFlight(${idx})" style="padding: 10px 18px; font-size: 13px; font-weight: 700; border-radius: 10px; white-space: nowrap;">
                            <span>✈️ Járat Kiválasztása & Szállások →</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    async function triggerStaySearch(fl) {
        if (!fl) return;
        state.selectedFlight = fl;

        const outDate = (fl.out_dep_time || fl.out_date || '').split('T')[0];
        const inDate = (fl.in_dep_time || fl.in_date || '').split('T')[0];
        const nights = fl.stay_days || fl.exact_stay_nights || state.intake.duration;
        const destCity = state.selectedDest?.name || state.selectedDest?.city || 'Célállomás';
        const destCountry = state.selectedDest?.country || 'Olaszország';

        const sFl = document.getElementById('stayContextFlight');
        const sCity = document.getElementById('stayContextCity');
        const sNights = document.getElementById('stayNightsCount');
        if (sFl) sFl.innerText = `${fl.out_airline || fl.airline || 'Járat'} (${outDate} – ${inDate} · ${nights} éj)`;
        if (sCity) sCity.innerText = destCity;
        if (sNights) sNights.innerText = nights;

        showLoader(
            `Szállások keresése (${destCity})...`,
            `Szállások aggregálása a zárolt időszakra (${outDate} – ${inDate} · ${nights} éjszaka) a kiválasztott prioritásokkal...`
        );

        try {
            const res = await fetch('/api/planner/search-stays', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
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
                    amenities: state.intake.amenities
                })
            });

            const data = await res.json();
            if (data.status === 'ok') {
                state.stays = data.stays || [];
                renderStays();
                setStep(3);
            } else {
                alert("Szálláskeresési hiba: " + (data.error || 'Hiba'));
                setStep(2);
            }
        } catch (e) {
            alert("Szálláskeresési hiba: " + e.message);
            setStep(2);
        }
    }

    async function selectFlight(index) {
        const fl = state.flights[index];
        if (!fl) return;

        state.selectedFlight = fl;

        const outDate = (fl.out_dep_time || fl.out_date || '').split('T')[0];
        const inDate = (fl.in_dep_time || fl.in_date || '').split('T')[0];
        const nights = fl.stay_days || fl.exact_stay_nights || state.intake.duration;

        if (window.TripCart) {
            window.TripCart.setFlight({
                airline: fl.out_airline || fl.in_airline || fl.airline || 'Repülőjárat',
                price_huf: fl.total_price_huf || fl.price_huf || 0,
                total_price_huf: fl.total_price_huf || fl.price_total_huf || 0,
                out_date: outDate,
                in_date: inDate,
                out_time: (fl.out_dep_time || fl.out_time || '').split('T')[1]?.slice(0, 5) || '',
                in_time: (fl.in_dep_time || fl.in_time || '').split('T')[1]?.slice(0, 5) || '',
                out_airport: fl.out_dep_airport || 'BUD',
                in_airport: fl.out_arr_airport || '',
                exact_stay_nights: nights,
                stay_days: nights,
                adults: state.intake.adults
            });
        }

        await triggerStaySearch(fl);
    }

    function renderStays() {
        const container = document.getElementById('staysGrid');
        if (!container) return;

        if (state.stays.length === 0) {
            container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">Nem találtunk szállást a megadott szűrésekkel. Kérlek módosítsd a csillagszámot vagy értékelést a fenti szűrőben!</div>`;
            return;
        }

        container.innerHTML = state.stays.map((stay, idx) => {
            const priceTotal = stay.price_total_huf || (stay.price_per_night_huf ? stay.price_per_night_huf * (state.selectedFlight?.stay_days || 7) : stay.price_huf || 120000);
            const nights = state.selectedFlight?.stay_days || state.intake.duration;
            const pricePerNight = stay.price_per_night_huf || Math.round(priceTotal / nights);
            const rating = stay.rating_score ? (stay.rating_score > 10 ? (stay.rating_score / 10).toFixed(1) : stay.rating_score) : 8.5;
            const stars = stay.stars || 3;

            return `
                <div class="advisor-main-card" style="background: var(--bg-surface); border: 1.5px solid var(--border-subtle); border-radius: 18px; padding: 20px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s ease;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                            <h3 style="font-size: 17px; font-weight: 800; color: var(--text-main); margin: 0;">${stay.name || 'Szálloda'}</h3>
                            <span style="font-size: 13px; color: #eab308; font-weight: 800;">${'⭐'.repeat(stars)}</span>
                        </div>

                        <div style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 12px;">
                            📍 ${stay.address || stay.city || state.selectedDest?.name}
                        </div>

                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                            <span style="background: rgba(16, 185, 129, 0.1); color: var(--status-success, #10b981); font-weight: 800; font-size: 12px; padding: 3px 8px; border-radius: 6px;">
                                ★ ${rating} / 10
                            </span>
                            <span style="font-size: 12px; color: var(--text-secondary);">${stay.rating_text || 'Nagyon jó értékelés'}</span>
                        </div>
                    </div>

                    <div style="border-top: 1px solid var(--border-subtle); padding-top: 14px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 18px; font-weight: 900; color: var(--primary); font-family: var(--font-mono);">${Math.round(priceTotal).toLocaleString()} Ft</div>
                            <div style="font-size: 11px; color: var(--text-muted);">~${pricePerNight.toLocaleString()} Ft / éj (${nights} éj)</div>
                        </div>

                        <button type="button" class="btn btn-primary" onclick="Wizard.selectStay(${idx})" style="padding: 9px 16px; font-size: 13px; font-weight: 700; border-radius: 10px;">
                            <span>🏨 Kiválasztás →</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function selectStay(index) {
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
                nights: nights
            });
        }

        renderFinalSummary();
        setStep(4);
    }

    function renderFinalSummary() {
        const d = state.selectedDest;
        const f = state.selectedFlight;
        const s = state.selectedStay;

        const outDate = (f?.out_dep_time || '').split('T')[0];
        const inDate = (f?.in_dep_time || '').split('T')[0];
        const nights = f?.stay_days || state.intake.duration;

        document.getElementById('summarySubtitle').innerText = `${d?.name || 'Célállomás'} utazás • ${state.intake.adults} felnőtt • ${nights} éjszaka (${outDate} – ${inDate})`;

        document.getElementById('sumDestName').innerText = `${d?.name || ''}, ${d?.country || ''}`;
        document.getElementById('sumDestClimate').innerText = `☀️ Nappal: ~${d?.metrics?.temp_avg || 24}°C • Biztonság: ${Math.round(d?.metrics?.safety_raw || 60)}/100`;

        document.getElementById('sumFlightAirline').innerText = `${f?.out_airline || f?.in_airline || 'Repülőjárat'} Retúr`;
        document.getElementById('sumFlightDates').innerText = `${outDate} – ${inDate} • ${f?.out_stops === 0 ? 'Közvetlen járat' : f?.out_stops + ' átszállás'}`;
        document.getElementById('sumFlightPrice').innerText = `${Math.round(f?.total_price_huf || 0).toLocaleString()} Ft`;

        document.getElementById('sumStayName').innerText = `${s?.name || 'Szállás'} ${'⭐'.repeat(s?.stars || 4)}`;
        document.getElementById('sumStayRating').innerText = `${nights} éjszaka • Értékelés: ${s?.rating_score ? (s.rating_score > 10 ? (s.rating_score/10).toFixed(1) : s.rating_score) : 8.8}/10`;
        document.getElementById('sumStayPrice').innerText = `${Math.round(s?.price_total_huf || s?.price_huf || 120000).toLocaleString()} Ft`;

        const wrap = document.getElementById('sumBreakdownWrap');
        if (wrap && window.TripCart) {
            const b = window.TripCart.calculateBreakdown();
            wrap.innerHTML = `
                <div style="background: var(--bg-surface-subtle); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 24px; margin-top: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <h3 style="font-size: 16px; font-weight: 800; color: var(--text-main); margin: 0;">📊 Tételes Költségkalkuláció</h3>
                        <span style="font-size: 12px; font-weight: 700; color: var(--primary);">${b.days} nap / ${b.totalPersons} fő</span>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        ${b.items.map(it => `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: var(--bg-surface); border-radius: 10px; font-size: 13px;">
                                <div>
                                    <strong>${it.icon} ${it.name}</strong><br>
                                    <small style="color: var(--text-muted); font-family: monospace;">📐 ${it.formula}</small>
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
    }

    function exportProposal() {
        if (window.TripCart) {
            window.TripCart.exportProposal();
        }
    }

    function recalculateDestinations() {
        state.intake.target_temp = parseFloat(document.getElementById('mod_temp').value) || 24.0;
        state.intake.min_safety = parseInt(document.getElementById('mod_safety').value, 10) || 50;
        startPlanning();
    }

    function recalculateFlights() {
        state.intake.flight_direct_only = document.getElementById('mod_direct_only').checked;
        if (state.selectedDest) {
            selectDestination(state.destinations.indexOf(state.selectedDest));
        }
    }

    function recalculateStays() {
        state.intake.hotel_min_stars = parseInt(document.getElementById('mod_hotel_stars').value, 10) || 0;
        state.intake.hotel_min_rating = parseFloat(document.getElementById('mod_hotel_rating').value) || 0;
        if (state.selectedFlight) {
            selectFlight(state.flights.indexOf(state.selectedFlight));
        }
    }

    // Inicializálás az oldal betöltésekor
    document.addEventListener('DOMContentLoaded', () => {
        // 1. Central Location Autocomplete
        if (window.initLocationAutocomplete) {
            window.initLocationAutocomplete({
                inputId: 'origin',
                dropdownId: 'origin-dropdown',
                mode: 'origin'
            });
        }

        // 2. Central Date Range Picker Flatpickr wrapper
        if (window.initAdvisorDatePicker) {
            state.exact_fp = window.initAdvisorDatePicker({
                triggerElementId: 'exact_date_picker_trigger',
                datePrimaryLabelId: 'exact_date_primary',
                dateSubLabelId: 'exact_date_sub',
                hiddenStartInputId: 'exact_out_date',
                hiddenEndInputId: 'exact_in_date',
                defaultStartDays: 14,
                defaultDurationDays: 7
            });
        }

        // 3. Stepperek eseménykezelése
        ['adults_count', 'children_count'].forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                const sync = () => {
                    const displayId = id.replace('_count', '_display');
                    const disp = document.getElementById(displayId);
                    if (disp) disp.innerText = input.value;
                };
                input.addEventListener('input', sync);
                input.addEventListener('change', sync);
            }
        });

        // 4. Max menetidő stepper eseménykezelése
        const durInput = document.getElementById('intake_max_flight_duration');
        if (durInput) {
            const syncDur = () => {
                const val = parseInt(durInput.value, 10) || 0;
                setMaxDuration(val);
            };
            durInput.addEventListener('input', syncDur);
            durInput.addEventListener('change', syncDur);
        }

        // 5. Tartózkodási idő szinkronizálása
        const monthDurInput = document.getElementById('month_duration_input');
        if (monthDurInput) {
            const syncMonth = () => {
                const val = parseInt(monthDurInput.value, 10) || 7;
                onDurationSliderChange(val);
            };
            monthDurInput.addEventListener('input', syncMonth);
            monthDurInput.addEventListener('change', syncMonth);
        }

        const intMinInput = document.getElementById('interval_min_stay_input');
        if (intMinInput) {
            const syncMin = () => {
                const disp = document.getElementById('interval_min_stay_display');
                if (disp) disp.innerText = `${intMinInput.value} nap`;
            };
            intMinInput.addEventListener('input', syncMin);
            intMinInput.addEventListener('change', syncMin);
        }

        const intMaxInput = document.getElementById('interval_max_stay_input');
        if (intMaxInput) {
            const syncMax = () => {
                const disp = document.getElementById('interval_max_stay_display');
                if (disp) disp.innerText = `${intMaxInput.value} nap`;
            };
            intMaxInput.addEventListener('input', syncMax);
            intMaxInput.addEventListener('change', syncMax);
        }

        // 6. Chip select kattintás kezelés
        document.querySelectorAll('.chip-select-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const cb = btn.querySelector('input[type="checkbox"]');
                if (cb) {
                    cb.checked = !cb.checked;
                    btn.classList.toggle('active', cb.checked);
                }
            });
        });

        // 7. Initialize Year and Month pickers
        initYearAndMonthPickers();

        // 8. Auto-resume from TripCart session if present
        setTimeout(() => {
            resumeSessionFromCart();
        }, 150);
    });

    async function resumeSessionFromCart() {
        if (!window.TripCart) return;
        const trip = window.TripCart.getTrip();
        if (!trip || (!trip.destination && !trip.flight?.selected_flight && !trip.accommodation?.selected_accommodation)) {
            return;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const resumeMode = urlParams.get('resume');

        // Restore intake fields if present in cart
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

        // Auto-navigate ONLY if explicit resume param is present in URL
        if (resumeMode === 'summary' && trip.destination && trip.flight?.selected_flight && trip.accommodation?.selected_accommodation) {
            renderFinalSummary();
            setStep(4);
        } else if (resumeMode === 'stay' && trip.destination && trip.flight?.selected_flight) {
            if (state.stays.length === 0 && state.selectedFlight) {
                await triggerStaySearch(state.selectedFlight);
            } else {
                setStep(3);
            }
        } else if (resumeMode === 'flight' && trip.destination) {
            if (state.flights.length === 0 && state.selectedDest) {
                await triggerFlightSearch(state.selectedDest);
            } else {
                setStep(2);
            }
        }
    }

    return {
        startPlanning,
        goToStep: setStep,
        setOrigin,
        switchDateMode,
        onDurationSliderChange,
        onYearChange,
        onMonthChange,
        applyExactPreset,
        toggleDeparturePref,
        onDepHourChange,
        setMaxDuration,
        onRatingChange,
        openAHPModal,
        openStayPrioritiesModal,
        closeAHPModal,
        selectDestination,
        selectFlight,
        selectStay,
        exportProposal,
        recalculateDestinations,
        recalculateFlights,
        recalculateStays,
        resumeSessionFromCart
    };
})();
