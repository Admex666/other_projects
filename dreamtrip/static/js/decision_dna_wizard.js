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
                    dest_exp: null,
                    flight_price: null,
                    flight_dur: null,
                    flight_stops: null,
                    stay_price: null,
                    stay_rating: null,
                    stay_loc: null
                },
                dest_ahp: {
                    total_cost_vs_weather: 4,
                    total_cost_vs_safety: 4,
                    total_cost_vs_experience: 4,
                    weather_vs_safety: 4,
                    weather_vs_experience: 4,
                    safety_vs_experience: 4
                },
                dest_promethee: {
                    cost: { type: 5, q: 20000, p: 80000, stepQ: 5000, stepP: 10000, unit: 'Ft' },
                    temp: { type: 5, q: 2, p: 6, stepQ: 1, stepP: 1, unit: '°C' },
                    safety: { type: 5, q: 5, p: 20, stepQ: 1, stepP: 5, unit: 'pont' },
                    experience: { persona: 'culture_aficionado', style_name: 'Kulturális és ikonikus látnivalók' }
                },
                flight_ahp: {
                    price_vs_duration: 4,
                    price_vs_stops: 4,
                    duration_vs_stops: 4
                },
                flight_promethee: {
                    price: { type: 5, q: 5000, p: 35000, stepQ: 1000, stepP: 5000, unit: 'Ft' },
                    duration: { type: 5, q: 0.5, p: 3.0, stepQ: 0.25, stepP: 0.5, unit: 'óra' },
                    stops_saving_needed: 15000,
                    direct_only: false
                },
                stay_ahp: {
                    price_vs_rating: 4,
                    price_vs_location: 4,
                    price_vs_amenities: 4,
                    rating_vs_location: 4,
                    rating_vs_amenities: 4,
                    location_vs_amenities: 4
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
                active_criteria: {
                    dest: ['total_cost', 'weather', 'safety', 'experience'],
                    flight: ['price', 'duration', 'stops'],
                    stay: ['price', 'rating', 'location', 'amenities']
                },
                criteria_confirmed: {
                    dest: false,
                    flight: false,
                    stay: false
                },
                calculated_weights: {
                    dest: { total_cost: 25, weather: 25, safety: 25, experience: 25 },
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
                        if (saved.active_criteria) Object.assign(this.state.active_criteria, saved.active_criteria);
                        if (saved.criteria_confirmed) Object.assign(this.state.criteria_confirmed, saved.criteria_confirmed);
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
                    <div id="decisionDnaModalCard" style="background: var(--bg-card); width: 100%; max-width: 820px; border-radius: 24px; border: 1.5px solid var(--border-subtle); box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.6); overflow: hidden; display: flex; flex-direction: column; max-height: 92vh; animation: fadeInScale 0.25s ease;">
                        <div style="padding: 16px 22px; border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; background: var(--bg-surface);">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="width: 36px; height: 36px; border-radius: 10px; background: var(--accent-glow); color: var(--primary); display: flex; align-items: center; justify-content: center; font-size: 20px; border: 1px solid var(--border-strong);">
                                    <span class="material-symbols-outlined" style="font-size: 20px;">tune</span>
                                </div>
                                <div>
                                    <h3 style="margin: 0; font-size: 16px; font-weight: 800; color: var(--text-main); letter-spacing: -0.01em;">Utazási Preferenciák és Prioritások</h3>
                                    <p style="margin: 0; font-size: 11.5px; color: var(--text-muted);" id="dnaHeaderSubtitle">1/3. Célállomás Súlyozás</p>
                                </div>
                            </div>
                            <button type="button" onclick="window.DecisionDNAInstance.hide()" style="background: none; border: none; font-size: 20px; cursor: pointer; color: var(--text-muted); padding: 4px 8px; border-radius: 8px; line-height: 1;">✕</button>
                        </div>

                        <div style="padding: 10px 20px; background: var(--bg-surface-subtle); border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                            <div id="dnaStepPills" style="display: flex; gap: 6px; flex-wrap: wrap;">
                                <span class="step-pill" data-step="0" onclick="window.DecisionDNAInstance.goToStep(0)">1. Célállomás Súlyok</span>
                                <span class="step-pill" data-step="1" onclick="window.DecisionDNAInstance.goToStep(1)">2. Célállomás Döntések</span>
                                <span class="step-pill" data-step="2" onclick="window.DecisionDNAInstance.goToStep(2)">3. Járat Súlyok</span>
                                <span class="step-pill" data-step="3" onclick="window.DecisionDNAInstance.goToStep(3)">4. Járat Döntések</span>
                                <span class="step-pill" data-step="4" onclick="window.DecisionDNAInstance.goToStep(4)">5. Szállás Súlyok</span>
                                <span class="step-pill" data-step="5" onclick="window.DecisionDNAInstance.goToStep(5)">6. Szállás Döntések</span>
                                <span class="step-pill" data-step="6" onclick="window.DecisionDNAInstance.goToStep(6)">7. Összegzés</span>
                            </div>
                            <span id="dnaStepIndicator" style="font-size: 11.5px; font-weight: 800; font-family: var(--font-mono); color: var(--primary);">1 / 7</span>
                        </div>

                        <div id="decisionDnaStepBody" style="padding: 22px; overflow-y: auto; flex: 1;"></div>

                        <div id="dnaModalFooter" style="padding: 14px 22px; border-top: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; background: var(--bg-surface); gap: 10px;">
                            <button type="button" id="dnaBtnPrev" onclick="window.DecisionDNAInstance.prevStep()" class="btn btn-secondary" style="padding: 10px 18px; font-size: 13px; font-weight: 700; border-radius: var(--radius-md);">
                                ← Vissza
                            </button>
                            <div style="display: flex; gap: 8px;">
                                <button type="button" id="dnaBtnNext" onclick="window.DecisionDNAInstance.nextStep()" class="btn btn-primary" style="padding: 11px 22px; font-size: 13.5px; font-weight: 700; border-radius: var(--radius-md);">
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
            const pillarMap = { 0: 'dest', 2: 'flight', 4: 'stay' };
            const pillar = pillarMap[this.state.step];
            if (pillar && !this.state.criteria_confirmed?.[pillar]) {
                this.confirmCriteria(pillar);
                return;
            }

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
                    active_criteria: this.state.active_criteria,
                    criteria_confirmed: this.state.criteria_confirmed,
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

        confirmCriteria(pillar) {
            if (!this.state.criteria_confirmed) this.state.criteria_confirmed = {};
            const active = this.state.active_criteria?.[pillar] || [];
            if (active.length === 0) {
                alert("Legalább egy szempontot ki kell választanod!");
                return;
            }
            this.state.criteria_confirmed[pillar] = true;
            if (window.DNAMath) window.DNAMath.calculateAllAHP(this.state);
            this.persistState();
            this.render();
        }

        editCriteria(pillar) {
            if (!this.state.criteria_confirmed) this.state.criteria_confirmed = {};
            this.state.criteria_confirmed[pillar] = false;
            this.persistState();
            this.render();
        }

        toggleCriterion(pillar, key) {
            if (!this.state.active_criteria) {
                this.state.active_criteria = {
                    dest: ['total_cost', 'weather', 'safety', 'experience'],
                    flight: ['price', 'duration', 'stops'],
                    stay: ['price', 'rating', 'location', 'amenities']
                };
            }
            const list = this.state.active_criteria[pillar];
            const idx = list.indexOf(key);
            if (idx > -1) {
                if (list.length <= 1) {
                    alert("Legalább egy szempontnak aktívnak kell lennie!");
                    return;
                }
                list.splice(idx, 1);
            } else {
                list.push(key);
            }
            if (window.DNAMath) window.DNAMath.calculateAllAHP(this.state);
            this.persistState();
            this.render();
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
                this.state.unlocked.dest_exp = true;
            } else if (groupKey === 'dest_exp') {
                this.state.dest_promethee.experience = {
                    persona: typeNum,
                    style_name: chosenCard === 'A' ? 'Kulturális és ikonikus látnivalók' : 'Helyi gasztronómia & Séta'
                };
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

        handlePairwiseSlider(input, storageKey, pairId, name1, name2) {
            const val = parseInt(input.value, 10);
            if (!this.state[storageKey]) {
                this.state[storageKey] = {};
            }
            this.state[storageKey][pairId] = val;
            if (window.DNAMath) window.DNAMath.calculateAllAHP(this.state);
            this.persistState();

            const readoutEl = document.getElementById(`dna-readout-${pairId}`);
            if (readoutEl) {
                const labels = [
                    'Extrém mértékben inkább',
                    'Sokkal inkább',
                    'Kifejezetten inkább',
                    'Kissé inkább',
                    'Egyformán fontos',
                    'Kissé inkább',
                    'Kifejezetten inkább',
                    'Sokkal inkább',
                    'Extrém mértékben inkább'
                ];
                if (val < 4) {
                    readoutEl.textContent = `← ${name1} (${labels[val]})`;
                } else if (val > 4) {
                    readoutEl.textContent = `${name2} → (${labels[val]})`;
                } else {
                    readoutEl.textContent = 'Egyformán fontos';
                }
            }
        }

        renderPairwiseMatrix(container, title, desc, pairs, storageKey, pillar, criteriaList) {
            const humanScale = [
                { idx: 0, label: 'Extrém mértékben inkább' },
                { idx: 1, label: 'Sokkal inkább' },
                { idx: 2, label: 'Kifejezetten inkább' },
                { idx: 3, label: 'Kissé inkább' },
                { idx: 4, label: 'Egyformán fontos' },
                { idx: 5, label: 'Kissé inkább' },
                { idx: 6, label: 'Kifejezetten inkább' },
                { idx: 7, label: 'Sokkal inkább' },
                { idx: 8, label: 'Extrém mértékben inkább' }
            ];

            const getReadout = (val, name1, name2) => {
                if (val < 4) return `← ${name1} (${humanScale[val]?.label || 'Inkább'})`;
                if (val > 4) return `${name2} → (${humanScale[val]?.label || 'Inkább'})`;
                return 'Egyformán fontos';
            };

            const active = (pillar && this.state.active_criteria?.[pillar]) 
                ? this.state.active_criteria[pillar] 
                : (criteriaList ? criteriaList.map(c => c.key) : []);

            // FÁZIS 1: Ha a szempontok még nincsenek jóváhagyva, ELŐSZÖR a szempontválasztó jelenik meg!
            const isConfirmed = pillar ? (this.state.criteria_confirmed?.[pillar] === true) : true;

            if (pillar && criteriaList && !isConfirmed) {
                container.innerHTML = `
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            <span class="material-symbols-outlined" style="color: var(--primary); font-size: 22px;">checklist</span>
                            <h4 style="margin: 0; font-size: 17px; font-weight: 800; color: var(--text-main); font-family: var(--font-display);">1. Fázis: Mely szempontok számítanak neked?</h4>
                        </div>
                        <p style="margin: 0; font-size: 13px; color: var(--text-muted); line-height: 1.5;">
                            Jelöld be azokat a szempontokat, amelyeket figyelembe szeretnél venni. <strong>Csak a kiválasztott szempontok</strong> vesznek részt az összehasonlításban és a döntésben.
                        </p>
                    </div>

                    <div style="background: var(--bg-surface-subtle); border: 1.5px solid var(--border-subtle); border-radius: 20px; padding: 22px; margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px;">
                            <span style="font-size: 13px; font-weight: 800; color: var(--text-main); text-transform: uppercase; letter-spacing: 0.04em;">Választható szempontok</span>
                            <span style="font-size: 12px; font-weight: 800; color: var(--primary); font-family: var(--font-mono); background: rgba(37, 99, 235, 0.1); padding: 4px 10px; border-radius: 12px;">${active.length} szempont aktív</span>
                        </div>

                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-bottom: 22px;">
                            ${criteriaList.map(c => {
                                const isAct = active.includes(c.key);
                                return `
                                    <div onclick="window.DecisionDNAInstance.toggleCriterion('${pillar}', '${c.key}')"
                                         style="display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-radius: 14px; cursor: pointer; transition: all 0.2s ease; border: 2px solid ${isAct ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${isAct ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-surface)'}; box-shadow: ${isAct ? '0 4px 12px rgba(37, 99, 235, 0.15)' : 'none'};">
                                        <span style="font-size: 13.5px; font-weight: 700; color: ${isAct ? 'var(--text-main)' : 'var(--text-muted)'};">${c.label}</span>
                                        <span style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; background: ${isAct ? 'var(--primary)' : 'var(--bg-surface-subtle)'}; color: ${isAct ? '#ffffff' : 'var(--text-muted)'}; font-size: 14px; font-weight: 800; border: 1.5px solid ${isAct ? 'var(--primary)' : 'var(--border-subtle)'};">
                                            ${isAct ? '✓' : ''}
                                        </span>
                                    </div>
                                `;
                            }).join('')}
                        </div>

                        <button type="button" class="btn btn-primary" onclick="window.DecisionDNAInstance.confirmCriteria('${pillar}')" style="width: 100%; padding: 14px 20px; font-size: 15px; font-weight: 800; border-radius: 12px; display: flex; align-items: center; justify-content: center; gap: 8px; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);">
                            <span class="material-symbols-outlined" style="font-size: 20px;">check_circle</span>
                            <span>${active.length === 1 ? 'Szempont Jóváhagyása (100%-os prioritás) →' : 'Szempontok Jóváhagyása & Tovább a Súlyozáshoz →'}</span>
                        </button>
                    </div>
                `;
                return;
            }

            // FÁZIS 2: A szempontok jóváhagyva -> Páros összehasonlító csúszkák (MAXIMUM 5)
            const allFilteredPairs = (pillar && criteriaList) 
                ? pairs.filter(p => active.includes(p.c1) && active.includes(p.c2)) 
                : pairs;

            // Invariáns: MAXIMUM 5 összehasonlítás! A többit a rendszer tranzitivitással kiszámolja.
            const displayedPairs = allFilteredPairs.slice(0, 5);
            const hasOmittedPairs = allFilteredPairs.length > 5;

            const topBarHtml = (pillar && criteriaList) ? `
                <div style="background: var(--bg-surface-subtle); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 10px 16px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <span style="font-size: 12px; font-weight: 700; color: var(--text-muted);">Jóváhagyott szempontok:</span>
                        ${active.map(k => {
                            const cObj = criteriaList?.find(c => c.key === k);
                            return `<span style="font-size: 11.5px; font-weight: 700; color: var(--primary); background: rgba(37, 99, 235, 0.1); padding: 3px 9px; border-radius: 10px;">${cObj ? cObj.label : k}</span>`;
                        }).join('')}
                    </div>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="window.DecisionDNAInstance.editCriteria('${pillar}')" style="font-size: 11.5px; font-weight: 700; border-radius: 8px; padding: 5px 12px;">
                        ✎ Szempontok módosítása
                    </button>
                </div>
            ` : '';

            let pairsHtml = '';
            if (active.length === 1) {
                const singleKey = active[0];
                const singleObj = criteriaList ? criteriaList.find(c => c.key === singleKey) : null;
                const singleLabel = singleObj ? singleObj.label : singleKey;
                pairsHtml = `
                    <div style="background: rgba(16, 185, 129, 0.08); border: 1.5px dashed #10b981; border-radius: 16px; padding: 26px 20px; text-align: center; margin-top: 10px;">
                        <div style="font-size: 32px; margin-bottom: 8px;">🎯</div>
                        <div style="font-size: 15px; font-weight: 800; color: #059669; margin-bottom: 6px;">
                            Kizárólagos szempont: ${singleLabel}
                        </div>
                        <div style="font-size: 13px; color: var(--text-muted); max-width: 480px; margin: 0 auto; line-height: 1.5;">
                            Mivel egyetlen szempontot jelöltél meg, az automatikusan <strong>100%-os prioritást kap</strong>. Páros összehasonlításra nincs szükség, kattints a Tovább gombra!
                        </div>
                    </div>
                `;
            } else if (displayedPairs.length === 0) {
                pairsHtml = `<div style="padding: 16px; text-align: center; color: var(--text-muted);">Nincs összehasonlítandó szempontpár.</div>`;
            } else {
                pairsHtml = displayedPairs.map(p => {
                    const curAns = this.state[storageKey]?.[p.id] ?? 4;
                    const readoutText = getReadout(curAns, p.name1, p.name2);
                    const safeName1 = (p.name1 || '').replace(/'/g, "\\'");
                    const safeName2 = (p.name2 || '').replace(/'/g, "\\'");
                    return `
                        <div class="dna-pairwise-card">
                            <div class="dna-pairwise-desc">${p.desc}</div>
                            <div class="dna-pairwise-header">
                                <div class="dna-pairwise-name">${p.name1}</div>
                                <div class="dna-pairwise-vs">vs</div>
                                <div class="dna-pairwise-name right">${p.name2}</div>
                            </div>
                            <div class="dna-pairwise-slider-wrap">
                                <div class="dna-pairwise-track-labels" style="display: flex; justify-content: space-between; font-size: 10px; color: var(--text-muted); margin-bottom: 4px;">
                                    <span>← Extrém mértékben</span>
                                    <span style="font-weight: 700; color: var(--primary);">Egyformán fontos</span>
                                    <span>Extrém mértékben →</span>
                                </div>
                                <div class="dna-pairwise-ticks">
                                    <div class="dna-pairwise-tick"></div>
                                    <div class="dna-pairwise-tick"></div>
                                    <div class="dna-pairwise-tick"></div>
                                    <div class="dna-pairwise-tick"></div>
                                    <div class="dna-pairwise-tick center"></div>
                                    <div class="dna-pairwise-tick"></div>
                                    <div class="dna-pairwise-tick"></div>
                                    <div class="dna-pairwise-tick"></div>
                                    <div class="dna-pairwise-tick"></div>
                                </div>
                                <input class="dna-pairwise-range" type="range" min="0" max="8" value="${curAns}" step="1"
                                       aria-label="${p.name1} vs ${p.name2}"
                                       oninput="window.DecisionDNAInstance.handlePairwiseSlider(this, '${storageKey}', '${p.id}', '${safeName1}', '${safeName2}')">
                                <div class="dna-pairwise-readout" id="dna-readout-${p.id}">${readoutText}</div>
                            </div>
                        </div>
                    `;
                }).join('');
            }

            const omittedNote = hasOmittedPairs ? `
                <div style="font-size: 11.5px; color: var(--text-muted); background: var(--bg-surface-subtle); border-radius: 10px; padding: 8px 12px; margin-top: 10px; text-align: center; border: 1px solid var(--border-subtle);">
                    ℹ️ A kényelmes kitöltés érdekében legfeljebb 5 kulcspár jelenik meg. A további kapcsolatokat a döntési motor geometriai tranzitivitással automatikusan kiszámítja.
                </div>
            ` : '';

            container.innerHTML = `
                <div style="margin-bottom: 14px;">
                    <h4 style="margin: 0 0 4px 0; font-size: 16.5px; font-weight: 800; color: var(--text-main); font-family: var(--font-display);">${title}</h4>
                    <p style="margin: 0; font-size: 12.5px; color: var(--text-muted); font-family: var(--font-body);">${desc}</p>
                </div>

                ${topBarHtml}

                <div style="display: flex; flex-direction: column; gap: 14px;">
                    ${pairsHtml}
                </div>

                ${omittedNote}
            `;
        }

        render() {
            this.renderPills();
            const body = document.getElementById('decisionDnaStepBody');
            if (!body) return;

            const subtitle = document.getElementById('dnaHeaderSubtitle');
            if (subtitle) {
                const titles = [
                    '1/3. Célállomás Súlyok (Páros Összehasonlítás)',
                    '1/3. Célállomás Döntések (Költség, Klíma, Biztonság)',
                    '2/3. Repülőjárat Súlyok (Páros Összehasonlítás)',
                    '2/3. Repülőjárat Döntések (Ár, Menetidő, Átszállás)',
                    '3/3. Szállás Súlyok (Páros Összehasonlítás)',
                    '3/3. Szállás Döntések (Ár, Értékelés, Elhelyezkedés)',
                    'Profil Összefoglaló'
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
                else btnNext.innerText = 'Mentés és Tervezés indítása →';
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
