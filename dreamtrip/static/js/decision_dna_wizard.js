/**
 * Optivoya — Fully Consistent Progressive Decision DNA Wizard
 * 
 * Rules:
 * 1. 100% CONSISTENT SCENARIOS: Every single criterion across Destination, Flight, and Accommodation
 *    has explicit A & B choice cards + dynamically adapting fill-in-the-blank sentences!
 * 2. ZERO ANALYSIS-PARALYSIS: Sequential progressive disclosure (answering item 1 unlocks item 2, etc.).
 * 3. NO PERCENTAGES MID-FLOW: Pure Hungarian natural language pairwise comparisons.
 * 4. SUMMARY STEP: saaty calculated weights & multi-dimensional rules overview.
 */

(function() {
    'use strict';

    class DecisionDNAWizard {
        constructor(options = {}) {
            this.containerId = options.containerId || 'decisionDnaModalBackdrop';
            this.onSave = options.onSave || function() {};

            // Wizard steps: 0..6
            this.state = {
                step: 0,
                // Track user selection progress per section to unlock next questions
                unlocked: {
                    dest_temp: false,
                    dest_safety: false,
                    flight_dur: false,
                    flight_stops: false,
                    stay_rating: false,
                    stay_filters: false
                },
                chosen_cards: {
                    dest_cost: null, // 'A' or 'B'
                    dest_temp: null,
                    dest_safety: null,
                    flight_price: null,
                    flight_dur: null,
                    flight_stops: null,
                    stay_price: null,
                    stay_rating: null,
                    stay_loc: null
                },
                dest_ahp: {
                    total_cost_vs_weather: 3,
                    total_cost_vs_safety: 3,
                    weather_vs_safety: 3
                },
                dest_promethee: {
                    cost: { type: 5, q: 20000, p: 80000, stepQ: 5000, stepP: 10000, unit: 'Ft' },
                    temp: { type: 5, q: 2, p: 6, stepQ: 1, stepP: 1, unit: '°C' },
                    safety: { type: 5, q: 5, p: 20, stepQ: 1, stepP: 5, unit: 'pont' }
                },
                flight_ahp: {
                    price_vs_duration: 3,
                    price_vs_stops: 3,
                    duration_vs_stops: 3
                },
                flight_promethee: {
                    price: { type: 5, q: 5000, p: 35000, stepQ: 1000, stepP: 5000, unit: 'Ft' },
                    duration: { type: 5, q: 0.5, p: 3.0, stepQ: 0.25, stepP: 0.5, unit: 'óra' },
                    stops_saving_needed: 15000,
                    direct_only: false
                },
                stay_ahp: {
                    price_vs_rating: 3,
                    price_vs_location: 3,
                    price_vs_amenities: 3,
                    rating_vs_location: 3,
                    rating_vs_amenities: 3,
                    location_vs_amenities: 3
                },
                stay_promethee: {
                    price: { type: 5, q: 3000, p: 15000, stepQ: 1000, stepP: 2000, unit: 'Ft' },
                    rating: { type: 5, q: 0.4, p: 1.5, stepQ: 0.1, stepP: 0.1, unit: 'pont' },
                    strict_center: false
                },
                stay_filters: {
                    hotel_min_stars: 3,
                    hotel_min_rating: 7.5,
                    breakfast: false,
                    hotel_types: ['hotel', 'apartment', 'resort', 'guesthouse'],
                    amenities: []
                },
                calculated_weights: {
                    dest: { total_cost: 34, weather: 33, safety: 33 },
                    flight: { price: 40, duration: 35, stops: 25 },
                    stay: { price: 35, rating: 30, location: 20, amenities: 15 }
                }
            };

            // Load persisted state from localStorage if available
            try {
                const savedRaw = localStorage.getItem('optivoya_decision_dna_state');
                if (savedRaw) {
                    const saved = JSON.parse(savedRaw);
                    if (saved && typeof saved === 'object') {
                        if (saved.chosen_cards) Object.assign(this.state.chosen_cards, saved.chosen_cards);
                        if (saved.unlocked) Object.assign(this.state.unlocked, saved.unlocked);
                        if (saved.dest_ahp) Object.assign(this.state.dest_ahp, saved.dest_ahp);
                        if (saved.dest_promethee) Object.assign(this.state.dest_promethee, saved.dest_promethee);
                        if (saved.flight_ahp) Object.assign(this.state.flight_ahp, saved.flight_ahp);
                        if (saved.flight_promethee) Object.assign(this.state.flight_promethee, saved.flight_promethee);
                        if (saved.stay_ahp) Object.assign(this.state.stay_ahp, saved.stay_ahp);
                        if (saved.stay_promethee) Object.assign(this.state.stay_promethee, saved.stay_promethee);
                        if (saved.stay_filters) Object.assign(this.state.stay_filters, saved.stay_filters);
                    }
                }
            } catch (e) {
                console.warn("[DNA WIZARD] Error loading saved DNA from localStorage", e);
            }

            // Override initial values if provided
            if (options.initialIntake) {
                const init = options.initialIntake;
                if (init.ahp_weights) Object.assign(this.state.calculated_weights.dest, init.ahp_weights);
                if (init.flight_ahp_weights) Object.assign(this.state.calculated_weights.flight, init.flight_ahp_weights);
                if (init.stay_ahp_weights) Object.assign(this.state.calculated_weights.stay, init.stay_ahp_weights);
                if (init.hotel_min_stars !== undefined) this.state.stay_filters.hotel_min_stars = init.hotel_min_stars;
                if (init.hotel_min_rating !== undefined) this.state.stay_filters.hotel_min_rating = init.hotel_min_rating;
                if (init.breakfast !== undefined) this.state.stay_filters.breakfast = init.breakfast;
            }

            this.initDOM();
        }


        initDOM() {
            let modal = document.getElementById(this.containerId);
            if (!modal) {
                modal = document.createElement('div');
                modal.id = this.containerId;
                modal.className = 'modal-backdrop';
                modal.style.position = 'fixed';
                modal.style.inset = '0';
                modal.style.background = 'rgba(0, 0, 0, 0.75)';
                modal.style.backdropFilter = 'blur(12px)';
                modal.style.zIndex = '999999';
                modal.style.display = 'none';
                modal.style.alignItems = 'center';
                modal.style.justifyContent = 'center';
                modal.style.padding = '16px';
                modal.style.opacity = '1';
                modal.style.visibility = 'visible';
                modal.onclick = (e) => {
                    if (e.target === modal) this.hide();
                };

                modal.innerHTML = `
                    <div id="decisionDnaModalCard" style="background: var(--bg-card); width: 100%; max-width: 820px; border-radius: 24px; border: 1px solid var(--border-subtle); box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.6); overflow: hidden; display: flex; flex-direction: column; max-height: 92vh; animation: fadeInScale 0.25s ease;">
                        
                        <!-- Modal Header -->
                        <div style="padding: 18px 24px; border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; background: var(--bg-surface);">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="width: 40px; height: 40px; border-radius: 12px; background: linear-gradient(135deg, rgba(37, 99, 235, 0.2), rgba(56, 189, 248, 0.2)); color: var(--primary); display: flex; align-items: center; justify-content: center; font-size: 20px; border: 1px solid rgba(37, 99, 235, 0.3);">
                                    ✨
                                </div>
                                <div>
                                    <h3 style="margin: 0; font-size: 17px; font-weight: 800; color: var(--text-main); letter-spacing: -0.02em;">Utazási Döntési DNS Létrehozása</h3>
                                    <p style="margin: 0; font-size: 12px; color: var(--text-muted);" id="dnaHeaderSubtitle">1/3. Célállomás Döntési Modell</p>
                                </div>
                            </div>
                            <button type="button" onclick="window.DecisionDNAInstance.hide()" style="background: none; border: none; font-size: 22px; cursor: pointer; color: var(--text-muted); padding: 4px 8px; border-radius: 8px; line-height: 1;">✕</button>
                        </div>

                        <!-- Step Tracker -->
                        <div style="padding: 10px 24px; background: rgba(0,0,0,0.03); border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                            <div id="dnaStepPills" style="display: flex; gap: 6px; flex-wrap: wrap;">
                                <span class="step-pill" data-step="0" onclick="window.DecisionDNAInstance.goToStep(0)">1. 🌍 Deszt. Prioritás</span>
                                <span class="step-pill" data-step="1" onclick="window.DecisionDNAInstance.goToStep(1)">2. 🌍 Deszt. Szituációk</span>
                                <span class="step-pill" data-step="2" onclick="window.DecisionDNAInstance.goToStep(2)">3. ✈️ Járat Prioritás</span>
                                <span class="step-pill" data-step="3" onclick="window.DecisionDNAInstance.goToStep(3)">4. ✈️ Járat Szituációk</span>
                                <span class="step-pill" data-step="4" onclick="window.DecisionDNAInstance.goToStep(4)">5. 🏨 Szállás Prioritás</span>
                                <span class="step-pill" data-step="5" onclick="window.DecisionDNAInstance.goToStep(5)">6. 🏨 Szállás Szituációk</span>
                                <span class="step-pill" data-step="6" onclick="window.DecisionDNAInstance.goToStep(6)">7. 🧬 Profil</span>
                            </div>
                            <span id="dnaStepIndicator" style="font-size: 12px; font-weight: 800; font-family: var(--font-mono); color: var(--primary);">1 / 7</span>
                        </div>

                        <!-- Step Body -->
                        <div id="decisionDnaStepBody" style="padding: 24px; overflow-y: auto; flex: 1;">
                            <!-- Dynamically Rendered -->
                        </div>

                        <!-- Footer -->
                        <div style="padding: 16px 24px; border-top: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; background: var(--bg-surface);">
                            <button type="button" id="dnaBtnPrev" onclick="window.DecisionDNAInstance.prevStep()" class="btn btn-secondary" style="padding: 10px 18px; font-size: 13px; font-weight: 700;">
                                ← Vissza
                            </button>
                            <div style="display: flex; gap: 10px;">
                                <button type="button" id="dnaBtnNext" onclick="window.DecisionDNAInstance.nextStep()" class="btn btn-primary" style="padding: 11px 24px; font-size: 13.5px; font-weight: 800; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);">
                                    Tovább →
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            }
            window.DecisionDNAInstance = this;
        }

        show(initialStep = 0) {
            this.state.step = initialStep;
            this.initDOM();
            const modal = document.getElementById(this.containerId);
            if (modal) {
                modal.style.display = 'flex';
                modal.style.opacity = '1';
                modal.style.visibility = 'visible';
                this.render();
            }
        }

        hide() {
            const modal = document.getElementById(this.containerId);
            if (modal) modal.style.display = 'none';
        }

        goToStep(stepNum) {
            this.state.step = stepNum;
            this.render();
        }

        prevStep() {
            if (this.state.step > 0) {
                this.state.step--;
                this.render();
            }
        }

        nextStep() {
            if (this.state.step < 6) {
                this.state.step++;
                this.render();
            } else {
                this.applyAndFinish();
            }
        }

        persistState() {
            try {
                localStorage.setItem('optivoya_decision_dna_state', JSON.stringify({
                    chosen_cards: this.state.chosen_cards,
                    unlocked: this.state.unlocked,
                    dest_ahp: this.state.dest_ahp,
                    dest_promethee: this.state.dest_promethee,
                    flight_ahp: this.state.flight_ahp,
                    flight_promethee: this.state.flight_promethee,
                    stay_ahp: this.state.stay_ahp,
                    stay_promethee: this.state.stay_promethee,
                    stay_filters: this.state.stay_filters
                }));
            } catch (e) {
                console.warn("[DNA WIZARD] Could not persist state to localStorage", e);
            }
        }

        applyAndFinish() {
            this.calculateAllAHP();
            this.persistState();
            this.onSave({
                ahp_weights: this.state.calculated_weights.dest,
                flight_ahp_weights: this.state.calculated_weights.flight,
                stay_ahp_weights: this.state.calculated_weights.stay,
                promethee_params: this.state.flight_promethee,
                dest_promethee: this.state.dest_promethee,
                stay_promethee: this.state.stay_promethee,
                stay: this.state.stay_filters
            });
            this.hide();
        }


        // ─────────────────────────────────────────────────────────────
        // AHP CALCULATIONS
        // ─────────────────────────────────────────────────────────────
        calculateAllAHP() {
            const scaleValues = [9.0, 5.0, 3.0, 1.0, 1.0/3.0, 1.0/5.0, 1.0/9.0];

            // 1. Destination AHP (3x3)
            const mDest = [
                [1.0, scaleValues[this.state.dest_ahp.total_cost_vs_weather], scaleValues[this.state.dest_ahp.total_cost_vs_safety]],
                [1.0 / scaleValues[this.state.dest_ahp.total_cost_vs_weather], 1.0, scaleValues[this.state.dest_ahp.weather_vs_safety]],
                [1.0 / scaleValues[this.state.dest_ahp.total_cost_vs_safety], 1.0 / scaleValues[this.state.dest_ahp.weather_vs_safety], 1.0]
            ];
            const gDest = [
                Math.cbrt(mDest[0][0] * mDest[0][1] * mDest[0][2]),
                Math.cbrt(mDest[1][0] * mDest[1][1] * mDest[1][2]),
                Math.cbrt(mDest[2][0] * mDest[2][1] * mDest[2][2])
            ];
            const tDest = gDest[0] + gDest[1] + gDest[2];
            this.state.calculated_weights.dest = {
                total_cost: Math.round((gDest[0] / tDest) * 100),
                weather: Math.round((gDest[1] / tDest) * 100),
                safety: Math.round((gDest[2] / tDest) * 100)
            };

            // 2. Flight AHP (3x3: Price, Duration, Stops)
            const mFlight = [
                [1.0, scaleValues[this.state.flight_ahp.price_vs_duration], scaleValues[this.state.flight_ahp.price_vs_stops]],
                [1.0 / scaleValues[this.state.flight_ahp.price_vs_duration], 1.0, scaleValues[this.state.flight_ahp.duration_vs_stops]],
                [1.0 / scaleValues[this.state.flight_ahp.price_vs_stops], 1.0 / scaleValues[this.state.flight_ahp.duration_vs_stops], 1.0]
            ];
            const gFlight = [
                Math.cbrt(mFlight[0][0] * mFlight[0][1] * mFlight[0][2]),
                Math.cbrt(mFlight[1][0] * mFlight[1][1] * mFlight[1][2]),
                Math.cbrt(mFlight[2][0] * mFlight[2][1] * mFlight[2][2])
            ];
            const tFlight = gFlight[0] + gFlight[1] + gFlight[2];
            this.state.calculated_weights.flight = {
                price: Math.round((gFlight[0] / tFlight) * 100),
                duration: Math.round((gFlight[1] / tFlight) * 100),
                stops: Math.round((gFlight[2] / tFlight) * 100)
            };

            // 3. Stay AHP (4x4: Price, Rating, Location, Amenities)
            const a_pr = scaleValues[this.state.stay_ahp.price_vs_rating];
            const a_pl = scaleValues[this.state.stay_ahp.price_vs_location];
            const a_pa = scaleValues[this.state.stay_ahp.price_vs_amenities];
            const a_rl = scaleValues[this.state.stay_ahp.rating_vs_location];
            const a_ra = scaleValues[this.state.stay_ahp.rating_vs_amenities];
            const a_la = scaleValues[this.state.stay_ahp.location_vs_amenities];

            const mStay = [
                [1.0, a_pr, a_pl, a_pa],
                [1.0/a_pr, 1.0, a_rl, a_ra],
                [1.0/a_pl, 1.0/a_rl, 1.0, a_la],
                [1.0/a_pa, 1.0/a_ra, 1.0/a_la, 1.0]
            ];
            const gStay = [
                Math.pow(mStay[0][0] * mStay[0][1] * mStay[0][2] * mStay[0][3], 0.25),
                Math.pow(mStay[1][0] * mStay[1][1] * mStay[1][2] * mStay[1][3], 0.25),
                Math.pow(mStay[2][0] * mStay[2][1] * mStay[2][2] * mStay[2][3], 0.25),
                Math.pow(mStay[3][0] * mStay[3][1] * mStay[3][2] * mStay[3][3], 0.25)
            ];
            const tStay = gStay[0] + gStay[1] + gStay[2] + gStay[3];
            this.state.calculated_weights.stay = {
                price: Math.round((gStay[0] / tStay) * 100),
                rating: Math.round((gStay[1] / tStay) * 100),
                location: Math.round((gStay[2] / tStay) * 100),
                amenities: Math.round((gStay[3] / tStay) * 100)
            };
        }

        // Stepper helpers
        stepValue(obj, key, param, dir) {
            const cfg = obj[key];
            const isQ = param === 'q';
            const step = isQ ? (cfg.stepQ || 1000) : (cfg.stepP || 5000);
            let val = cfg[param] + (dir * step);
            if (val < 0) val = 0;
            cfg[param] = parseFloat(val.toFixed(2));
            this.render();
        }

        // Progressive Selection helper
        selectScenario(groupKey, chosenCard, typeNum) {
            this.state.chosen_cards[groupKey] = chosenCard;
            
            // 1. Destination chain
            if (groupKey === 'dest_cost') {
                this.state.dest_promethee.cost.type = typeNum;
                this.state.unlocked.dest_temp = true;
            } else if (groupKey === 'dest_temp') {
                this.state.dest_promethee.temp.type = typeNum;
                this.state.unlocked.dest_safety = true;
            } else if (groupKey === 'dest_safety') {
                this.state.dest_promethee.safety.type = typeNum;
            } 
            // 2. Flight chain
            else if (groupKey === 'flight_price') {
                this.state.flight_promethee.price.type = typeNum;
                this.state.unlocked.flight_dur = true;
            } else if (groupKey === 'flight_dur') {
                this.state.flight_promethee.duration.type = typeNum;
                this.state.unlocked.flight_stops = true;
            } else if (groupKey === 'flight_stops') {
                this.state.flight_promethee.direct_only = (chosenCard === 'B');
            }
            // 3. Stay chain
            else if (groupKey === 'stay_price') {
                this.state.stay_promethee.price.type = typeNum;
                this.state.unlocked.stay_rating = true;
            } else if (groupKey === 'stay_rating') {
                this.state.stay_promethee.rating.type = typeNum;
                this.state.unlocked.stay_filters = true;
            } else if (groupKey === 'stay_loc') {
                this.state.stay_promethee.strict_center = (chosenCard === 'B');
            }

            this.render();
        }

        // Render controller
        render() {
            this.renderPills();
            const body = document.getElementById('decisionDnaStepBody');
            if (!body) return;

            const subtitle = document.getElementById('dnaHeaderSubtitle');
            if (subtitle) {
                const titles = [
                    '1/3. 🌍 Célállomás Prioritások (Páros Kérdések)',
                    '1/3. 🌍 Célállomás Döntési Helyzetek (Költség, Klíma, Biztonság)',
                    '2/3. ✈️ Repülőjárat Prioritások (Páros Kérdések)',
                    '2/3. ✈️ Repülőjárat Döntési Helyzetek (Ár, Menetidő, Átszállás)',
                    '3/3. 🏨 Szállás Prioritások (Páros Kérdések)',
                    '3/3. 🏨 Szállás Döntési Helyzetek (Ár, Értékelés, Elhelyezkedés)',
                    '🎯 Döntési DNS Profil Összefoglaló'
                ];
                subtitle.innerText = titles[this.state.step] || '';
            }

            if (this.state.step === 0) this.renderDestAHP(body);
            else if (this.state.step === 1) this.renderDestScenarios(body);
            else if (this.state.step === 2) this.renderFlightAHP(body);
            else if (this.state.step === 3) this.renderFlightScenarios(body);
            else if (this.state.step === 4) this.renderStayAHP(body);
            else if (this.state.step === 5) this.renderStayScenarios(body);
            else if (this.state.step === 6) this.renderSummary(body);

            // Buttons
            const btnPrev = document.getElementById('dnaBtnPrev');
            const btnNext = document.getElementById('dnaBtnNext');
            if (btnPrev) btnPrev.style.visibility = this.state.step === 0 ? 'hidden' : 'visible';
            if (btnNext) {
                if (this.state.step < 6) btnNext.innerText = 'Tovább →';
                else btnNext.innerText = '✓ Döntési DNS Alkalmazása & Indítás';
            }
        }

        renderPills() {
            const pills = document.querySelectorAll('#dnaStepPills .step-pill');
            pills.forEach((p, idx) => {
                p.style.cursor = 'pointer';
                p.style.padding = '4px 10px';
                p.style.borderRadius = '14px';
                p.style.fontSize = '11.5px';
                p.style.fontWeight = '700';
                p.style.transition = 'all 0.2s ease';

                if (idx === this.state.step) {
                    p.style.background = 'var(--primary)';
                    p.style.color = '#ffffff';
                } else if (idx < this.state.step) {
                    p.style.background = 'rgba(16, 185, 129, 0.15)';
                    p.style.color = '#10b981';
                } else {
                    p.style.background = 'var(--bg-surface)';
                    p.style.color = 'var(--text-muted)';
                }
            });
            const counter = document.getElementById('dnaStepIndicator');
            if (counter) counter.innerText = `${this.state.step + 1} / 7`;
        }

        // ─────────────────────────────────────────────────────────────
        // HUMAN-LANGUAGE PAIRWISE RENDERER (NO PERCENTAGES, ONLY LABELS)
        // ─────────────────────────────────────────────────────────────
        renderPairwiseMatrix(container, title, desc, pairs, storageKey) {
            const humanScale = [
                { idx: 0, label: 'Sokkal inkább' },
                { idx: 1, label: 'Kifejezetten inkább' },
                { idx: 2, label: 'Kissé inkább' },
                { idx: 3, label: 'Egyformán fontos' },
                { idx: 4, label: 'Kissé inkább' },
                { idx: 5, label: 'Kifejezetten inkább' },
                { idx: 6, label: 'Sokkal inkább' }
            ];

            container.innerHTML = `
                <div style="margin-bottom: 18px;">
                    <h4 style="margin: 0 0 4px 0; font-size: 16.5px; font-weight: 800; color: var(--text-main);">${title}</h4>
                    <p style="margin: 0; font-size: 12.5px; color: var(--text-muted);">${desc}</p>
                </div>

                <div style="display: flex; flex-direction: column; gap: 14px;">
                    ${pairs.map(p => {
                        const curAns = this.state[storageKey][p.id] ?? 3;
                        return `
                            <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 16px; padding: 16px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                    <strong style="font-size: 13.5px; color: var(--text-main);">${p.name1} <span style="color: var(--text-muted); font-weight: 500;">vs</span> ${p.name2}</strong>
                                    <span style="font-size: 12px; font-weight: 800; color: var(--primary);">
                                        ${curAns < 3 ? `👈 ${p.name1} (${humanScale[curAns].label})` : curAns > 3 ? `${p.name2} 👉 (${humanScale[curAns].label})` : '⚖️ Egyformán fontos'}
                                    </span>
                                </div>
                                <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">${p.desc}</div>

                                <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px;">
                                    ${humanScale.map(opt => {
                                        const isSel = curAns === opt.idx;
                                        return `
                                            <button type="button" onclick="window.DecisionDNAInstance.state['${storageKey}']['${p.id}'] = ${opt.idx}; window.DecisionDNAInstance.render();" style="padding: 8px 3px; border-radius: 8px; border: 1.5px solid ${isSel ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${isSel ? 'var(--primary)' : 'var(--bg-card)'}; color: ${isSel ? '#ffffff' : 'var(--text-main)'}; font-size: 10px; font-weight: 700; cursor: pointer; transition: all 0.15s ease; text-align: center; line-height: 1.2;">
                                                ${opt.label}
                                            </button>
                                        `;
                                    }).join('')}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        // 1. DESZTINÁCIÓ AHP
        renderDestAHP(container) {
            const pairs = [
                { id: 'total_cost_vs_weather', name1: '💰 Teljes Költség', name2: '☀️ Klíma / Időjárás', desc: 'Olcsóbb utazás vagy garantáltan tökéletes célhőmérséklet?' },
                { id: 'total_cost_vs_safety', name1: '💰 Teljes Költség', name2: '🛡️ Közbiztonság', desc: 'Alacsonyabb összköltség vagy kiemelkedő biztonsági index?' },
                { id: 'weather_vs_safety', name1: '☀️ Klíma / Időjárás', name2: '🛡️ Közbiztonság', desc: 'Ideális időjárás vagy a maximális biztonság a fontosabb?' }
            ];
            this.renderPairwiseMatrix(container, '🌍 1. Lépés: Célállomás Súlyozás (Páros Döntés)', 'Melyik szempont mennyire fontosabb számodra a desztináció kiválasztásakor?', pairs, 'dest_ahp');
        }

        // 2. DESZTINÁCIÓ DÖNTÉSI HELYZETEK (Költség, Hőmérséklet, Biztonság - 100% KONZISZTENS A/B)
        renderDestScenarios(container) {
            const cCost = this.state.dest_promethee.cost;
            const cTemp = this.state.dest_promethee.temp;
            const cSafe = this.state.dest_promethee.safety;

            const isCostChosen = this.state.chosen_cards.dest_cost !== null;
            const isTempUnlocked = this.state.unlocked.dest_temp || isCostChosen;
            const isTempChosen = this.state.chosen_cards.dest_temp !== null;
            const isSafeUnlocked = this.state.unlocked.dest_safety || isTempChosen;
            const isSafeChosen = this.state.chosen_cards.dest_safety !== null;

            container.innerHTML = `
                <div style="margin-bottom: 18px;">
                    <h4 style="margin: 0 0 4px 0; font-size: 16.5px; font-weight: 800; color: var(--text-main);">🌍 2. Lépés: Célállomás Döntési Helyzetek</h4>
                    <p style="margin: 0; font-size: 12.5px; color: var(--text-muted);">Minden kritériumnál válaszd ki a döntési stílusodat (A vagy B), majd finomhangold a mondatot:</p>
                </div>

                <!-- 1. KÖLTSÉG SZITUÁCIÓ -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px;">
                    <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 10px;">
                        💰 1. Hogyan gondolkodsz az úti cél összköltségéről?
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: ${isCostChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_cost', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.dest_cost === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.dest_cost === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Kisebb különbség még nem számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy kisebb eltérés még nem döntő, de egy bizonyos összeg felett már biztosan az olcsóbb úti célt választom.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_cost', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.dest_cost === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.dest_cost === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Minden forint azonnal számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Már a legelső forint különbség is azonnal előnyt jelent az olcsóbb célállomásnak.</div>
                        </div>
                    </div>

                    ${isCostChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${cCost.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cCost.q.toLocaleString()} Ft</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                összköltség különbség még <strong>nem számít</strong> nekem két város között, de 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cCost.p.toLocaleString()} Ft</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                felett már <strong>egyértelműen az olcsóbb úti cél</strong> a nyerő.”
                            ` : `
                                „Már a legkisebb költségkülönbség is számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cCost.p.toLocaleString()} Ft</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                különbségnél már <strong>100%-ban az olcsóbb desztináció</strong> felé billen a mérleg.”
                            `}
                        </div>
                    ` : ''}
                </div>

                <!-- 2. HŐMÉRSÉKLET SZITUÁCIÓ -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px; opacity: ${isTempUnlocked ? '1.0' : '0.45'}; pointer-events: ${isTempUnlocked ? 'auto' : 'none'}; filter: ${isTempUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">☀️ 2. Mennyire vagy szigorú az időjárással?</div>
                        ${!isTempUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">🔒 Válaszd ki az 1. pontot a feloldáshoz</span>' : ''}
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: ${isTempChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_temp', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.dest_temp === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.dest_temp === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Pár fok ide vagy oda még jó</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy kisebb eltérés még kellemes idő, csak a szélsőséges hideget vagy hőséget kerülöm.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_temp', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.dest_temp === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.dest_temp === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Pontosan az ideális hőfokot keresem</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Minden egyes fok eltérés azonnal ront a helyszín vonzerején.</div>
                        </div>
                    </div>

                    ${isTempChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${cTemp.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">±${cTemp.q} °C</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                eltérés a kívánt hőfoktól még <strong>ugyanolyan jó nekem</strong>, de 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">±${cTemp.p} °C</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                eltérés felett már <strong>kifejezetten gyengébbnek</strong> tekintem.”
                            ` : `
                                „Minden egyes fok eltérés azonnal számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">±${cTemp.p} °C</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                eltérésnél már <strong>100%-ban a pontosabb célpont</strong> a preferált.”
                            `}
                        </div>
                    ` : ''}
                </div>

                <!-- 3. BIZTONSÁG SZITUÁCIÓ (100% KONZISZTENS A/B KÁRTYÁKKAL) -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; opacity: ${isSafeUnlocked ? '1.0' : '0.45'}; pointer-events: ${isSafeUnlocked ? 'auto' : 'none'}; filter: ${isSafeUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">🛡️ 3. Hogyan tekintesz a közbiztonságra?</div>
                        ${!isSafeUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">🔒 Válaszd ki a 2. pontot a feloldáshoz</span>' : ''}
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: ${isSafeChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_safety', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.dest_safety === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.dest_safety === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Kisebb különbség még belefér</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Pár pont eltérés még nem döntő, de jelentős biztonsági különbségnél a biztonságosabb kell.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_safety', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.dest_safety === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.dest_safety === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Minden biztonsági pont számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Minden egyes pont biztonsági előny azonnal a biztonságosabb város felé billenti a mérleget.</div>
                        </div>
                    </div>
                    
                    ${isSafeChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${cSafe.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cSafe.q} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                biztonsági pontszám különbség még <strong>elhanyagolható</strong>, de 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cSafe.p} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                különbség felett már <strong>kizárólag a biztonságosabb város</strong> a preferált.”
                            ` : `
                                „Minden egyes pont biztonsági előny számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cSafe.p} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                pontkülönbségnél már <strong>100%-ban a biztonságosabb úti cél</strong> felé billen a mérleg.”
                            `}
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // 3. JÁRAT AHP (Ár vs Menetidő vs Átszállásszám)
        renderFlightAHP(container) {
            const pairs = [
                { id: 'price_vs_duration', name1: '💳 Repjegy Ár', name2: '⏱️ Menetidő (Időtartam)', desc: 'Olcsóbb repjegy vagy lényegesen rövidebb utazási idő?' },
                { id: 'price_vs_stops', name1: '💳 Repjegy Ár', name2: '🔄 Közvetlen Járat (0 átszállás)', desc: 'Spórolás egy átszállással vagy ragaszkodás a közvetlen járathoz?' },
                { id: 'duration_vs_stops', name1: '⏱️ Menetidő', name2: '🔄 Átszállások Száma', desc: 'Rövidebb menetidő vagy kényelmes, átszállásmentes út?' }
            ];
            this.renderPairwiseMatrix(container, '✈️ 3. Lépés: Repülőjárat Súlyozás (Páros Döntés)', 'Melyik tényező mennyire fontosabb számodra a járatok rangsorolásakor?', pairs, 'flight_ahp');
        }

        // 4. JÁRAT DÖNTÉSI HELYZETEK (Ár, Menetidő, Átszállás - MINDHÁROM AHP KRITÉRIUMRA KONZISZTENS A/B)
        renderFlightScenarios(container) {
            const priceCfg = this.state.flight_promethee.price;
            const durCfg = this.state.flight_promethee.duration;
            const pPriceQ = priceCfg.q.toLocaleString() + ' Ft';
            const pPriceP = priceCfg.p.toLocaleString() + ' Ft';
            const pDurQ = durCfg.q < 1 ? `${Math.round(durCfg.q * 60)} perc` : `${durCfg.q} óra`;
            const pDurP = `${durCfg.p} óra`;

            const isPriceChosen = this.state.chosen_cards.flight_price !== null;
            const isDurUnlocked = this.state.unlocked.flight_dur || isPriceChosen;
            const isDurChosen = this.state.chosen_cards.flight_dur !== null;
            const isStopsUnlocked = this.state.unlocked.flight_stops || isDurChosen;
            const isStopsChosen = this.state.chosen_cards.flight_stops !== null;

            container.innerHTML = `
                <div style="margin-bottom: 18px;">
                    <h4 style="margin: 0 0 4px 0; font-size: 16.5px; font-weight: 800; color: var(--text-main);">✈️ 4. Lépés: Járat Döntési Helyzetek</h4>
                    <p style="margin: 0; font-size: 12.5px; color: var(--text-muted);">Válaszd ki a döntési szabályokat a járat 3 fő kritériumára (Ár, Menetidő, Átszállás):</p>
                </div>

                <!-- 1. REPJEGY ÁR SZITUÁCIÓ -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px;">
                    <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 10px;">
                        💰 1. Hogyan gondolkodsz a repjegyárakról két járat között?
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: ${isPriceChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_price', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.flight_price === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.flight_price === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Pár ezer Ft még nem döntő</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy minimális árkülönbség még nem számít, de nagyobb összegnél már egyértelműen az olcsóbb kell.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_price', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.flight_price === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.flight_price === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) A legelső forint árelőny is számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Már a legkisebb árelőny is azonnal az olcsóbb járat felé billenti a mérleget.</div>
                        </div>
                    </div>

                    ${isPriceChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${priceCfg.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'price', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${pPriceQ}</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'price', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                árkülönbség még <strong>nem számít</strong> nekem két járat között, de utána minden forint számít, egészen 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'price', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${pPriceP}</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'price', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                különbségig, ahonnan már <strong>egyértelműen az olcsóbb járat</strong> a nyerő.”
                            ` : `
                                „Már a legkisebb árelőny is számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'price', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${pPriceP}</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'price', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                árkülönbségnél már <strong>100%-ban az olcsóbb járat</strong> dominál.”
                            `}
                        </div>
                    ` : ''}
                </div>

                <!-- 2. MENETIDŐ SZITUÁCIÓ -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px; opacity: ${isDurUnlocked ? '1.0' : '0.45'}; pointer-events: ${isDurUnlocked ? 'auto' : 'none'}; filter: ${isDurUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">⏱️ 2. Hogyan viszonyulsz a plusz utazási időhöz?</div>
                        ${!isDurUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">🔒 Válaszd ki az 1. pontot a feloldáshoz</span>' : ''}
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: ${isDurChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_dur', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.flight_dur === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.flight_dur === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Egy kis plusz idő még belefér</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy fél óra vagy 1 óra többlet még rendben van, de több órával hosszabb utat már nem szívesen vállalok be.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_dur', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.flight_dur === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.flight_dur === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Minden plusz perc számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Minden egyes felesleges utazási perc ront az élményen már a legelsőtől.</div>
                        </div>
                    </div>

                    ${isDurChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${durCfg.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'duration', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${pDurQ}</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'duration', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                plusz menetidő még <strong>belefér nekem</strong>, de 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'duration', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${pDurP}</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'duration', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                plusz menetidőnél már <strong>100%-ban a gyorsabb járat</strong> a jobb.”
                            ` : `
                                „Minden perc számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'duration', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${pDurP}</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.flight_promethee, 'duration', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                menetidő-többletnél már <strong>100%-ban a gyorsabb járat</strong> a nyerő.”
                            `}
                        </div>
                    ` : ''}
                </div>

                <!-- 3. ÁTSZÁLLÁSOK SZITUÁCIÓ (100% KONZISZTENS A/B KÁRTYÁKKAL) -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; opacity: ${isStopsUnlocked ? '1.0' : '0.45'}; pointer-events: ${isStopsUnlocked ? 'auto' : 'none'}; filter: ${isStopsUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">🔄 3. Hogyan viszonyulsz az átszálláshoz?</div>
                        ${!isStopsUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">🔒 Válaszd ki a 2. pontot a feloldáshoz</span>' : ''}
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: ${isStopsChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_stops', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.flight_stops === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.flight_stops === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Bevállalok átszállást spórolásért</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Ha jelentősen olcsóbb, szívesen utazom 1 átszállással is.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_stops', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.flight_stops === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.flight_stops === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Ragaszkodom a közvetlen járathoz</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Csak a közvetlen (0 átszállásos) kényelmes járatok jöhetnek szóba.</div>
                        </div>
                    </div>

                    ${isStopsChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${this.state.chosen_cards.flight_stops === 'A' ? `
                                „Szívesen bevállalok <strong>1 kényelmes átszállást</strong>, amennyiben legalább 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.state.flight_promethee.stops_saving_needed = Math.max(5000, window.DecisionDNAInstance.state.flight_promethee.stops_saving_needed - 5000); window.DecisionDNAInstance.render();" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${this.state.flight_promethee.stops_saving_needed.toLocaleString()} Ft</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.state.flight_promethee.stops_saving_needed += 5000; window.DecisionDNAInstance.render();" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                megtakarítást jelent a közvetlen repjegyhez képest.”
                            ` : `
                                „Kizárólag <strong>közvetlen, átszállásmentes járatokat</strong> keresek; átszállásos opciót csak akkor mutasson a rendszer, ha egyáltalán nincs közvetlen járat.”
                            `}
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // 5. SZÁLLÁS AHP
        renderStayAHP(container) {
            const pairs = [
                { id: 'price_vs_rating', name1: '💳 Ár / Éjszaka', name2: '⭐ Vendégértékelés (Minőség)', desc: 'Kedvezőbb ár vagy magasabb vendégértékelés?' },
                { id: 'price_vs_location', name1: '💳 Ár / Éjszaka', name2: '📍 Központi Elhelyezkedés', desc: 'Olcsóbb külvárosibb szállás vagy sétálóutcás belváros?' },
                { id: 'price_vs_amenities', name1: '💳 Ár / Éjszaka', name2: '☕ Reggeli & Wellness', desc: 'Alacsonyabb szobaár vagy gazdag reggeli és wellness szolgáltatások?' },
                { id: 'rating_vs_location', name1: '⭐ Vendégértékelés', name2: '📍 Központi Elhelyezkedés', desc: 'Kiváló 9.0+ értékelés vagy köpésnyire lévő belváros?' },
                { id: 'rating_vs_amenities', name1: '⭐ Vendégértékelés', name2: '☕ Reggeli & Wellness', desc: 'Magas minőségi pontszám vagy extra ellátási csomag?' },
                { id: 'location_vs_amenities', name1: '📍 Központi Elhelyezkedés', name2: '☕ Reggeli & Wellness', desc: 'Központi lokáció vagy kényelmi felszereltség a fontosabb?' }
            ];
            this.renderPairwiseMatrix(container, '🏨 5. Lépés: Szállás Súlyozás (Páros Döntés)', 'Melyik szempont mennyire fontosabb számodra a szállások rangsorolásakor?', pairs, 'stay_ahp');
        }

        // 6. SZÁLLÁS DÖNTÉSI HELYZETEK (Ár, Értékelés, Elhelyezkedés - 100% KONZISZTENS A/B)
        renderStayScenarios(container) {
            const sPrice = this.state.stay_promethee.price;
            const sRating = this.state.stay_promethee.rating;
            const filters = this.state.stay_filters;

            const isPriceChosen = this.state.chosen_cards.stay_price !== null;
            const isRatingUnlocked = this.state.unlocked.stay_rating || isPriceChosen;
            const isRatingChosen = this.state.chosen_cards.stay_rating !== null;
            const isLocUnlocked = this.state.unlocked.stay_filters || isRatingChosen;
            const isLocChosen = this.state.chosen_cards.stay_loc !== null;

            container.innerHTML = `
                <div style="margin-bottom: 18px;">
                    <h4 style="margin: 0 0 4px 0; font-size: 16.5px; font-weight: 800; color: var(--text-main);">🏨 6. Lépés: Szállás Döntési Helyzetek & Kategóriák</h4>
                    <p style="margin: 0; font-size: 12.5px; color: var(--text-muted);">Válaszd ki a szállás döntési szabályait (Ár, Értékelés, Elhelyezkedés):</p>
                </div>

                <!-- 1. SZÁLLÁS ÁR SZITUÁCIÓ -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px;">
                    <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 10px;">
                        💳 1. Hogyan viszonyulsz az éjszakánkénti szobaárhoz?
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: ${isPriceChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_price', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.stay_price === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.stay_price === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Pár ezer Ft még nem számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Pár ezer forint éjszakánként még nem oszt, nem szoroz, de nagyobb összegnél már az olcsóbb nyer.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_price', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.stay_price === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.stay_price === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Minden forint árelőny számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Már a legkisebb éjszakánkénti árelőny is azonnal előnyt jelent.</div>
                        </div>
                    </div>

                    ${isPriceChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${sPrice.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sPrice.q.toLocaleString()} Ft / éj</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                különbség még <strong>nem számít</strong> két szálloda között, de 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sPrice.p.toLocaleString()} Ft / éj</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                felett már <strong>kifejezetten az olcsóbb opció</strong> a nyerő.”
                            ` : `
                                „Minden forint árelőny azonnal számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sPrice.p.toLocaleString()} Ft / éj</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                árkülönbségnél már <strong>100%-ban az olcsóbb szállás</strong> a preferált.”
                            `}
                        </div>
                    ` : ''}
                </div>

                <!-- 2. VENDÉGÉRTÉKELÉS SZITUÁCIÓ (100% KONZISZTENS A/B KÁRTYÁKKAL) -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px; opacity: ${isRatingUnlocked ? '1.0' : '0.45'}; pointer-events: ${isRatingUnlocked ? 'auto' : 'none'}; filter: ${isRatingUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">⭐ 2. Hogyan viszonyulsz a vendégértékeléshez?</div>
                        ${!isRatingUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">🔒 Válaszd ki az 1. pontot a feloldáshoz</span>' : ''}
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: ${isRatingChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_rating', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.stay_rating === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.stay_rating === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Kisebb tizedes különbség még belefér</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy minimális pontkülönbség még nem számít, de nagyobb minőségi ugrásnál a magasabb értékelésű nyer.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_rating', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.stay_rating === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.stay_rating === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Minden tized pont azonnal számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Minden tized pont előny azonnal a magasabbra értékelt hotel felé billenti a mérleget.</div>
                        </div>
                    </div>
                    
                    ${isRatingChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${sRating.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sRating.q} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                értékelésbeli különbség még <strong>elhanyagolható</strong>, de 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sRating.p} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                előny már <strong>egyértelmű minőségi fölényt</strong> jelent.”
                            ` : `
                                „Minden tized pont előny számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sRating.p} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                pontelőnynél már <strong>100%-ban a magasabbra értékelt opció</strong> a preferált.”
                            `}
                        </div>
                    ` : ''}
                </div>

                <!-- 3. ELHELYEZKEDÉS & SZŰRŐK SZITUÁCIÓ (100% KONZISZTENS A/B KÁRTYÁKKAL) -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; opacity: ${isLocUnlocked ? '1.0' : '0.45'}; pointer-events: ${isLocUnlocked ? 'auto' : 'none'}; filter: ${isLocUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">📍 3. Elhelyezkedési és kategória preferenciák</div>
                        ${!isLocUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">🔒 Válaszd ki a 2. pontot a feloldáshoz</span>' : ''}
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px;">
                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_loc', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.stay_loc === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.stay_loc === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Rugalmas lokáció</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Nem feltétel a közvetlen belváros, ha jó a közlekedés vagy kedvezőbb az ár.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_loc', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${this.state.chosen_cards.stay_loc === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${this.state.chosen_cards.stay_loc === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Szigorúan központi lokáció</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Kifejezetten sétálótávolságra lévő, frekventált vagy belvárosi szállást keresek.</div>
                        </div>
                    </div>

                    <!-- Minőségi Kategória & Slider -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div style="background: var(--bg-card); padding: 12px; border-radius: 12px; border: 1px solid var(--border-subtle);">
                            <label class="form-label" style="font-weight: 700; margin-bottom: 6px; display: block; font-size: 11.5px;">Minimális Csillag:</label>
                            <select onchange="window.DecisionDNAInstance.state.stay_filters.hotel_min_stars = parseInt(this.value, 10)" class="form-control" style="width: 100%; padding: 8px; border-radius: 8px; background: var(--bg-surface); font-weight: 700;">
                                <option value="0" ${filters.hotel_min_stars === 0 ? 'selected' : ''}>Bármilyen kategória</option>
                                <option value="3" ${filters.hotel_min_stars === 3 ? 'selected' : ''}>3★ vagy jobb</option>
                                <option value="4" ${filters.hotel_min_stars === 4 ? 'selected' : ''}>4★ vagy jobb</option>
                                <option value="5" ${filters.hotel_min_stars === 5 ? 'selected' : ''}>5★ (Luxus)</option>
                            </select>
                        </div>

                        <div style="background: var(--bg-card); padding: 12px; border-radius: 12px; border: 1px solid var(--border-subtle);">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                                <label class="form-label" style="font-weight: 700; margin: 0; font-size: 11.5px;">Min. Vendégértékelés:</label>
                                <strong id="dnaRatingDisp" style="color: var(--primary); font-family: var(--font-mono); font-size: 12.5px;">${filters.hotel_min_rating}+</strong>
                            </div>
                            <input type="range" min="0" max="9.5" step="0.5" value="${filters.hotel_min_rating}" style="width: 100%;" oninput="window.DecisionDNAInstance.state.stay_filters.hotel_min_rating = parseFloat(this.value); document.getElementById('dnaRatingDisp').innerText = this.value + '+';">
                        </div>
                    </div>
                </div>
            `;
        }

        // 7. ÖSSZEFOGLALÓ DÖNTÉSI PROFIL
        renderSummary(container) {
            this.calculateAllAHP();
            const wDest = this.state.calculated_weights.dest;
            const wFlight = this.state.calculated_weights.flight;
            const wStay = this.state.calculated_weights.stay;

            container.innerHTML = `
                <div style="text-align: center; margin-bottom: 24px;">
                    <div style="font-size: 32px; margin-bottom: 6px;">🧬</div>
                    <h3 style="margin: 0 0 6px 0; font-size: 20px; font-weight: 800; color: var(--text-main);">Az Egyéni Utazási Döntési DNS-ed Készen Áll!</h3>
                    <p style="margin: 0 auto; max-width: 540px; font-size: 13px; color: var(--text-muted);">
                        Az AHP páros összehasonlítások és az életszerű döntési helyzetek alapján a rendszer kiszámította a személyre szabott súlyokat és toleranciákat.
                    </p>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; margin-bottom: 24px;">
                    <!-- 1. Desztináció Súlyok -->
                    <div style="background: var(--bg-surface); padding: 16px; border-radius: 16px; border: 1px solid var(--border-subtle);">
                        <div style="font-size: 11px; font-weight: 800; color: var(--primary); text-transform: uppercase; margin-bottom: 10px;">🌍 Célállomás Súlyok (AHP)</div>
                        <div style="display: flex; flex-direction: column; gap: 6px;">
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>💰 Teljes Költség:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wDest.total_cost}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>☀️ Klíma / Időjárás:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wDest.weather}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>🛡️ Közbiztonság:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wDest.safety}%</strong></div>
                        </div>
                    </div>

                    <!-- 2. Járat Súlyok -->
                    <div style="background: var(--bg-surface); padding: 16px; border-radius: 16px; border: 1px solid var(--border-subtle);">
                        <div style="font-size: 11px; font-weight: 800; color: var(--primary); text-transform: uppercase; margin-bottom: 10px;">✈️ Járat Súlyok (AHP)</div>
                        <div style="display: flex; flex-direction: column; gap: 6px;">
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>💳 Repjegy Ár:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wFlight.price}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>⏱️ Menetidő:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wFlight.duration}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>🔄 Átszállásszám:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wFlight.stops}%</strong></div>
                        </div>
                    </div>

                    <!-- 3. Szállás Súlyok -->
                    <div style="background: var(--bg-surface); padding: 16px; border-radius: 16px; border: 1px solid var(--border-subtle);">
                        <div style="font-size: 11px; font-weight: 800; color: var(--primary); text-transform: uppercase; margin-bottom: 10px;">🏨 Szállás Súlyok (AHP)</div>
                        <div style="display: flex; flex-direction: column; gap: 6px;">
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>💳 Szobaár / éj:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wStay.price}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>⭐ Vendégértékelés:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wStay.rating}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>📍 Lokáció:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wStay.location}%</strong></div>
                        </div>
                    </div>
                </div>

                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 14px; padding: 14px 18px; text-align: center; color: var(--text-main); font-size: 13px; font-weight: 700;">
                    ✅ A döntési szabályok és küszöbértékek készen állnak az intelligens desztináció-, járat- és szálláselemzésre!
                </div>
            `;
        }
    }

    window.DecisionDNAWizard = DecisionDNAWizard;
})();
