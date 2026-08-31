/**
 * Optivoya — Fully Consistent Progressive Decision DNA Wizard v2.0 (Facade Controller)
 * Orchestrates DNAMath, DNADestStep, DNAFlightStep, DNAStayStep, and DNASummaryStep.
 * 100% backward-compatible API for window.DecisionDNAWizard.
 */

(function () {
    'use strict';

    class DecisionDNAWizard {
        constructor(options = {}) {
            this.containerId = options.containerId || 'decisionDnaModalBackdrop';
            this.onSave = options.onSave || function () { };

            this.state = {
                step: 0,
                unlocked: {
                    dest_temp: false,
                    dest_safety: false,
                    flight_dur: false,
                    flight_stops: false,
                    stay_rating: false,
                    stay_filters: false
                },
                chosen_cards: {
                    dest_cost: null,
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

            // Restore from localStorage
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
            } catch (e) { }

            // Override initial values
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
                modal.onclick = (e) => { if (e.target === modal) this.hide(); };

                modal.innerHTML = `
                    <div id="decisionDnaModalCard" style="background: var(--bg-card); width: 100%; max-width: 820px; border-radius: 24px; border: 1px solid var(--border-subtle); box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.6); overflow: hidden; display: flex; flex-direction: column; max-height: 92vh; animation: fadeInScale 0.25s ease;">
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

                        <div id="decisionDnaStepBody" style="padding: 24px; overflow-y: auto; flex: 1;"></div>

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
            } catch (e) { }
        }

        applyAndFinish() {
            if (window.DNAMath) window.DNAMath.calculateAllAHP(this.state);
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

        stepValue(obj, key, param, dir) {
            if (window.DNAMath) {
                window.DNAMath.stepValue(obj, key, param, dir, () => this.render());
            }
        }

        selectScenario(groupKey, chosenCard, typeNum) {
            this.state.chosen_cards[groupKey] = chosenCard;

            if (groupKey === 'dest_cost') {
                this.state.dest_promethee.cost.type = typeNum;
                this.state.unlocked.dest_temp = true;
            } else if (groupKey === 'dest_temp') {
                this.state.dest_promethee.temp.type = typeNum;
                this.state.unlocked.dest_safety = true;
            } else if (groupKey === 'dest_safety') {
                this.state.dest_promethee.safety.type = typeNum;
            } else if (groupKey === 'flight_price') {
                this.state.flight_promethee.price.type = typeNum;
                this.state.unlocked.flight_dur = true;
            } else if (groupKey === 'flight_dur') {
                this.state.flight_promethee.duration.type = typeNum;
                this.state.unlocked.flight_stops = true;
            } else if (groupKey === 'flight_stops') {
                this.state.flight_promethee.direct_only = (chosenCard === 'B');
            } else if (groupKey === 'stay_price') {
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

            if (this.state.step === 0 && window.DNADestStep) window.DNADestStep.renderDestAHP(this, body);
            else if (this.state.step === 1 && window.DNADestStep) window.DNADestStep.renderDestScenarios(this, body);
            else if (this.state.step === 2 && window.DNAFlightStep) window.DNAFlightStep.renderFlightAHP(this, body);
            else if (this.state.step === 3 && window.DNAFlightStep) window.DNAFlightStep.renderFlightScenarios(this, body);
            else if (this.state.step === 4 && window.DNAStayStep) window.DNAStayStep.renderStayAHP(this, body);
            else if (this.state.step === 5 && window.DNAStayStep) window.DNAStayStep.renderStayScenarios(this, body);
            else if (this.state.step === 6 && window.DNASummaryStep) window.DNASummaryStep.renderSummary(this, body);

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
    }

    window.DecisionDNAWizard = DecisionDNAWizard;
})();
