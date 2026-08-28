/**
 * Optivoya — Master Travel Planner Wizard Engine
 * Controls end-to-end 4-step progressive travel generation.
 */

window.Wizard = (function() {
    let state = {
        step: 0,
        intake: {
            origin: "Budapest",
            adults: 2,
            children: 0,
            month: 9,
            duration: 7,
            target_temp: 24.0,
            min_safety: 50,
            preferred_regions: ["europe_south", "europe_west", "europe_central"],
            flight_direct_only: false,
            flight_max_stops: 1,
            hotel_min_stars: 3,
            hotel_min_rating: 7.5
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

    async function startPlanning() {
        // Collect intake
        const regionBoxes = document.querySelectorAll('input[name="regions"]:checked');
        const selectedRegions = Array.from(regionBoxes).map(cb => cb.value);

        state.intake = {
            origin: document.getElementById('intake_origin').value,
            adults: parseInt(document.getElementById('intake_adults').value, 10) || 2,
            children: parseInt(document.getElementById('intake_children').value, 10) || 0,
            month: parseInt(document.getElementById('intake_month').value, 10) || 9,
            duration: parseInt(document.getElementById('intake_duration').value, 10) || 7,
            target_temp: parseFloat(document.getElementById('intake_temp').value) || 24.0,
            min_safety: parseInt(document.getElementById('intake_safety').value, 10) || 50,
            preferred_regions: selectedRegions.length > 0 ? selectedRegions : ["europe_south", "europe_west", "europe_central"],
            flight_direct_only: document.getElementById('intake_flight_direct').checked,
            flight_max_stops: parseInt(document.getElementById('intake_flight_stops').value, 10) || 1,
            hotel_min_stars: parseInt(document.getElementById('intake_hotel_stars').value, 10) || 3,
            hotel_min_rating: parseFloat(document.getElementById('intake_hotel_rating').value) || 7.5
        };

        showLoader(
            "Célállomások Értékelése & Rangsorolása",
            "Open-Meteo klímaadatok, Kiwi repülőjegy árak és Numbeo megélhetési indexek összehasonlítása..."
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
                                <div style="font-size: 18px; font-weight: 900; color: var(--primary); font-family: var(--font-mono);">${Math.round(dest.score || 85)}p</div>
                                <div style="font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Illeszkedés</div>
                            </div>
                        </div>

                        <!-- METRIKA PILLS -->
                        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; font-size: 12px; font-weight: 600;">
                            <span style="background: var(--bg-surface-subtle); padding: 4px 10px; border-radius: 8px; border: 1px solid var(--border-subtle);">☀️ ${m.temp_formatted || '~24°C'}</span>
                            <span style="background: var(--bg-surface-subtle); padding: 4px 10px; border-radius: 8px; border: 1px solid var(--border-subtle);">✈️ ${m.flight_price_formatted || 'Kedvező ár'}</span>
                            <span style="background: var(--bg-surface-subtle); padding: 4px 10px; border-radius: 8px; border: 1px solid var(--border-subtle);">🛡️ Biztonság: ${Math.round(m.safety_raw || 60)}/100</span>
                            <span style="background: var(--bg-surface-subtle); padding: 4px 10px; border-radius: 8px; border: 1px solid var(--border-subtle);">💰 Étel: ~${Math.round(m.daily_cost_raw || 35)}€/nap</span>
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

    async function selectDestination(index) {
        const dest = state.destinations[index];
        if (!dest) return;

        state.selectedDest = dest;

        // Store into global TripCart if present
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

        // Update context banner
        document.getElementById('flightContextCity').innerText = dest.name;
        document.getElementById('flightContextDetails').innerText = `${state.intake.adults} felnőtt • ${state.intake.duration} napos utazás • 2026. szept.`;

        showLoader(
            `Járatok keresése (${dest.name})...`,
            `Valós Kiwi retúr járatok aggregálása és PROMETHEE II relevancia elemzése...`
        );

        try {
            const res = await fetch('/api/planner/search-flights', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    origin: state.intake.origin,
                    destination: dest.name,
                    month: state.intake.month,
                    duration: state.intake.duration,
                    adults: state.intake.adults,
                    children: state.intake.children,
                    direct_only: state.intake.flight_direct_only,
                    max_stops: state.intake.flight_max_stops
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

    function renderFlights() {
        const container = document.getElementById('flightsGrid');
        if (!container) return;

        if (state.flights.length === 0) {
            container.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--text-secondary);">Nem találtunk járatot a megadott feltételekkel. Kérlek engedélyezz átszállást a fenti beállításokban!</div>`;
            return;
        }

        container.innerHTML = state.flights.map((fl, idx) => {
            const outDate = (fl.out_dep_time || '').split('T')[0];
            const inDate = (fl.in_dep_time || '').split('T')[0];
            const outTime = (fl.out_dep_time || '').split('T')[1]?.slice(0, 5) || 'Reggel';
            const inTime = (fl.in_dep_time || '').split('T')[1]?.slice(0, 5) || 'Este';
            const nights = fl.stay_days || state.intake.duration;
            const priceTotal = fl.total_price_huf || 0;
            const pricePerPerson = Math.round(priceTotal / max(1, state.intake.adults));

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

    function max(a, b) { return a > b ? a : b; }

    async function selectFlight(index) {
        const fl = state.flights[index];
        if (!fl) return;

        state.selectedFlight = fl;

        const outDate = (fl.out_dep_time || '').split('T')[0];
        const inDate = (fl.in_dep_time || '').split('T')[0];
        const nights = fl.stay_days || state.intake.duration;

        // Store into global TripCart
        if (window.TripCart) {
            window.TripCart.setFlight({
                airline: fl.out_airline || fl.in_airline || 'Repülőjárat',
                price_huf: fl.total_price_huf || 0,
                total_price_huf: fl.total_price_huf || 0,
                out_date: outDate,
                in_date: inDate,
                out_time: (fl.out_dep_time || '').split('T')[1]?.slice(0, 5) || '',
                in_time: (fl.in_dep_time || '').split('T')[1]?.slice(0, 5) || '',
                out_airport: fl.out_dep_airport || 'BUD',
                in_airport: fl.out_arr_airport || '',
                exact_stay_nights: nights,
                stay_days: nights,
                adults: state.intake.adults
            });
        }

        // Update context banner
        document.getElementById('stayContextFlight').innerText = `${fl.out_airline || 'Járat'} (${outDate} – ${inDate} · ${nights} éj)`;
        document.getElementById('stayContextCity').innerText = state.selectedDest?.name || 'Célállomás';
        document.getElementById('stayNightsCount').innerText = nights;

        showLoader(
            `Szállások keresése (${state.selectedDest?.name})...`,
            `Cozycozy szállásaggregáció a zárolt időszakra (${outDate} – ${inDate} · ${nights} éjszaka)...`
        );

        try {
            const res = await fetch('/api/planner/search-stays', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    city: state.selectedDest?.name || 'Róma',
                    country: state.selectedDest?.country || 'Olaszország',
                    checkin: outDate,
                    checkout: inDate,
                    adults: state.intake.adults,
                    min_stars: state.intake.hotel_min_stars,
                    min_rating: state.intake.hotel_min_rating
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

    function renderStays() {
        const container = document.getElementById('staysGrid');
        if (!container) return;

        if (state.stays.length === 0) {
            container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">Nem találtunk szállást a megadott szűrésekkel. Kérlek módosítsd a csillagszámot vagy értékelést a fenti szűrőben!</div>`;
            return;
        }

        container.innerHTML = state.stays.map((stay, idx) => {
            const priceTotal = stay.price_huf || (stay.price_per_night_huf ? stay.price_per_night_huf * (state.selectedFlight?.stay_days || 7) : 120000);
            const nights = state.selectedFlight?.stay_days || state.intake.duration;
            const pricePerNight = Math.round(priceTotal / nights);
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
        const priceTotal = stay.price_huf || (stay.price_per_night_huf ? stay.price_per_night_huf * nights : 120000);

        // Store into global TripCart
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
        document.getElementById('sumDestClimate').innerText = `☀️ Nappal: ~${d?.metrics?.temp_avg || 24}°C • Numbeo biztonság: ${Math.round(d?.metrics?.safety_raw || 60)}/100`;

        document.getElementById('sumFlightAirline').innerText = `${f?.out_airline || f?.in_airline || 'Repülőjárat'} Retúr`;
        document.getElementById('sumFlightDates').innerText = `${outDate} – ${inDate} • ${f?.out_stops === 0 ? 'Közvetlen járat' : f?.out_stops + ' átszállás'}`;
        document.getElementById('sumFlightPrice').innerText = `${Math.round(f?.total_price_huf || 0).toLocaleString()} Ft`;

        document.getElementById('sumStayName').innerText = `${s?.name || 'Szállás'} ${'⭐'.repeat(s?.stars || 4)}`;
        document.getElementById('sumStayRating').innerText = `${nights} éjszaka • Értékelés: ${s?.rating_score ? (s.rating_score > 10 ? (s.rating_score/10).toFixed(1) : s.rating_score) : 8.8}/10`;
        document.getElementById('sumStayPrice').innerText = `${Math.round(s?.price_huf || s?.price_total_huf || 120000).toLocaleString()} Ft`;

        // Render Breakdown
        const wrap = document.getElementById('sumBreakdownWrap');
        if (wrap && window.TripCart) {
            const b = window.TripCart.calculateBreakdown();
            wrap.innerHTML = `
                <div style="background: var(--bg-surface-subtle); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 24px; margin-top: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <h3 style="font-size: 16px; font-weight: 800; color: var(--text-main); margin: 0;">📊 Tételes Numbeo Költségkalkuláció</h3>
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

    return {
        startPlanning,
        goToStep: setStep,
        selectDestination,
        selectFlight,
        selectStay,
        exportProposal,
        recalculateDestinations,
        recalculateFlights,
        recalculateStays
    };
})();
