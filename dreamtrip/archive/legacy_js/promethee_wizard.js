/**
 * Optivoya — Interactive PROMETHEE II Preference & Threshold Wizard
 * Allows users to choose preference function types in natural language and configure
 * indifference (q) and strict preference (p) thresholds via "Fill-in-the-Blank" sentences.
 */

(function() {
    'use strict';

    class PROMETHEEWizard {
        constructor(options = {}) {
            this.containerId = options.containerId || 'prometheeModalBackdrop';
            this.onSave = options.onSave || function() {};
            
            // Default PROMETHEE settings for flight dimensions
            this.state = {
                step: 0, // 0: Ár, 1: Menetidő, 2: Tartózkodás
                config: {
                    price: { type: 5, q: 5000, p: 35000, minQ: 0, maxQ: 25000, stepQ: 1000, minP: 5000, maxP: 100000, stepP: 5000, unit: 'Ft' },
                    duration: { type: 5, q: 0.5, p: 3.0, minQ: 0, maxQ: 2.0, stepQ: 0.25, minP: 0.5, maxP: 8.0, stepP: 0.5, unit: 'óra' },
                    stay: { type: 5, q: 1.0, p: 3.0, minQ: 0, maxQ: 3.0, stepQ: 0.5, minP: 1.0, maxP: 7.0, stepP: 0.5, unit: 'nap' }
                }
            };

            // Override with existing config if passed
            if (options.initialConfig) {
                if (options.initialConfig.price) Object.assign(this.state.config.price, options.initialConfig.price);
                if (options.initialConfig.duration) Object.assign(this.state.config.duration, options.initialConfig.duration);
                if (options.initialConfig.stay) Object.assign(this.state.config.stay, options.initialConfig.stay);
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
                modal.style.background = 'rgba(0, 0, 0, 0.65)';
                modal.style.backdropFilter = 'blur(8px)';
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
                    <div id="prometheeModalContent" style="background: var(--bg-card); width: 100%; max-width: 680px; border-radius: 20px; border: 1px solid var(--border-subtle); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.45); overflow: hidden; display: flex; flex-direction: column; max-height: 90vh; animation: fadeInScale 0.2s ease;">
                        <!-- Modal Header -->
                        <div style="padding: 20px 24px; border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; background: var(--bg-surface);">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="width: 36px; height: 36px; border-radius: 10px; background: rgba(37, 99, 235, 0.12); color: var(--primary); display: flex; align-items: center; justify-content: center; font-size: 18px;">
                                    ⚖️
                                </div>
                                <div>
                                    <h3 style="margin: 0; font-size: 17px; font-weight: 800; color: var(--text-main);">Döntési Toleranciák & Preferenciák</h3>
                                    <p style="margin: 0; font-size: 12px; color: var(--text-muted);">PROMETHEE II Finomhangolás emberi nyelven</p>
                                </div>
                            </div>
                            <button type="button" onclick="window.PrometheeWizardInstance.hide()" style="background: none; border: none; font-size: 20px; cursor: pointer; color: var(--text-muted); padding: 4px 8px; border-radius: 8px;">✕</button>
                        </div>

                        <!-- Step Progress -->
                        <div style="padding: 12px 24px; background: rgba(0,0,0,0.02); border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center;">
                            <div id="promStepPills" style="display: flex; gap: 8px;">
                                <span class="step-pill" data-step="0" style="padding: 4px 12px; border-radius: 20px; font-size: 11.5px; font-weight: 700;">1. 💰 Árérzékenység</span>
                                <span class="step-pill" data-step="1" style="padding: 4px 12px; border-radius: 20px; font-size: 11.5px; font-weight: 700;">2. ⏱️ Menetidő</span>
                                <span class="step-pill" data-step="2" style="padding: 4px 12px; border-radius: 20px; font-size: 11.5px; font-weight: 700;">3. 🌙 Tartózkodás</span>
                            </div>
                            <span id="promStepCounter" style="font-size: 12px; font-weight: 800; color: var(--primary);">1 / 3</span>
                        </div>

                        <!-- Step Body Container -->
                        <div id="prometheeStepBody" style="padding: 24px; overflow-y: auto; flex: 1;">
                            <!-- Rendered dynamically -->
                        </div>

                        <!-- Footer -->
                        <div style="padding: 16px 24px; border-top: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; background: var(--bg-surface);">
                            <button type="button" id="promBtnPrev" onclick="window.PrometheeWizardInstance.prevStep()" class="btn btn-secondary" style="padding: 10px 18px; font-size: 13px; font-weight: 700;">
                                ← Vissza
                            </button>
                            <div style="display: flex; gap: 10px;">
                                <button type="button" onclick="window.PrometheeWizardInstance.applyAndClose()" class="btn btn-secondary" style="padding: 10px 18px; font-size: 13px; font-weight: 700;">
                                    Mentés & Bezárás
                                </button>
                                <button type="button" id="promBtnNext" onclick="window.PrometheeWizardInstance.nextStep()" class="btn btn-primary" style="padding: 10px 22px; font-size: 13px; font-weight: 700;">
                                    Tovább →
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            }
            window.PrometheeWizardInstance = this;
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

        prevStep() {
            if (this.state.step > 0) {
                this.state.step--;
                this.render();
            }
        }

        nextStep() {
            if (this.state.step < 2) {
                this.state.step++;
                this.render();
            } else {
                this.applyAndClose();
            }
        }

        applyAndClose() {
            this.onSave(this.state.config);
            this.hide();
        }

        setType(criterionKey, typeNum) {
            this.state.config[criterionKey].type = typeNum;
            this.render();
        }

        stepValue(criterionKey, paramKey, direction) {
            const cfg = this.state.config[criterionKey];
            const isQ = paramKey === 'q';
            const step = isQ ? cfg.stepQ : cfg.stepP;
            const min = isQ ? cfg.minQ : cfg.minP;
            const max = isQ ? cfg.maxQ : cfg.maxP;

            let val = cfg[paramKey] + (direction * step);
            val = Math.max(min, Math.min(max, val));

            // Biztosítsuk, hogy q mindig < p
            if (isQ && val >= cfg.p) {
                val = cfg.p - step;
            } else if (!isQ && val <= cfg.q) {
                val = cfg.q + step;
            }

            cfg[paramKey] = parseFloat(val.toFixed(2));
            this.render();
        }

        render() {
            this.renderPills();
            const body = document.getElementById('prometheeStepBody');
            if (!body) return;

            const step = this.state.step;
            if (step === 0) this.renderPriceStep(body);
            else if (step === 1) this.renderDurationStep(body);
            else if (step === 2) this.renderStayStep(body);

            // Gombok frissítése
            const btnPrev = document.getElementById('promBtnPrev');
            const btnNext = document.getElementById('promBtnNext');
            if (btnPrev) btnPrev.style.visibility = step === 0 ? 'hidden' : 'visible';
            if (btnNext) btnNext.innerText = step === 2 ? '✓ Kész, Alkalmazás' : 'Következő Szempont →';
        }

        renderPills() {
            const pills = document.querySelectorAll('#promStepPills .step-pill');
            pills.forEach((p, idx) => {
                if (idx === this.state.step) {
                    p.style.background = 'var(--primary)';
                    p.style.color = '#ffffff';
                } else {
                    p.style.background = 'var(--bg-surface)';
                    p.style.color = 'var(--text-muted)';
                }
            });
            const counter = document.getElementById('promStepCounter');
            if (counter) counter.innerText = `${this.state.step + 1} / 3`;
        }

        // 1. ÁRÉRZÉKENYSÉG LÉPÉS
        renderPriceStep(container) {
            const cfg = this.state.config.price;
            const qStr = cfg.q.toLocaleString() + ' Ft';
            const pStr = cfg.p.toLocaleString() + ' Ft';

            container.innerHTML = `
                <div style="margin-bottom: 18px;">
                    <h4 style="margin: 0 0 6px 0; font-size: 16px; font-weight: 800; color: var(--text-main);">💰 1. Árérzékenység & Spórolási Hajlandóság</h4>
                    <p style="margin: 0; font-size: 13px; color: var(--text-muted);">Hogyan döntesz az árak tekintetében két hasonló repülőjárat között?</p>
                </div>

                <!-- Mintázat választó kártyák -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px;">
                    <div onclick="window.PrometheeWizardInstance.setType('price', 5)" style="cursor: pointer; padding: 14px; border-radius: 12px; border: 2px solid ${cfg.type === 5 ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${cfg.type === 5 ? 'rgba(37, 99, 235, 0.06)' : 'var(--bg-surface)'}; transition: all 0.2s ease;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 4px;">🟢 Racionális & Toleráns (Ajánlott)</div>
                        <div style="font-size: 11.5px; color: var(--text-muted); line-height: 1.4;">Kis árkülönbség még mindegy, de nagyobb összegnél fokozatosan előnybe kerül az olcsóbb.</div>
                    </div>
                    <div onclick="window.PrometheeWizardInstance.setType('price', 3)" style="cursor: pointer; padding: 14px; border-radius: 12px; border: 2px solid ${cfg.type === 3 ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${cfg.type === 3 ? 'rgba(37, 99, 235, 0.06)' : 'var(--bg-surface)'}; transition: all 0.2s ease;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 4px;">🔵 Szigorúan Lineáris</div>
                        <div style="font-size: 11.5px; color: var(--text-muted); line-height: 1.4;">Minden egyes forint árelőny azonnal számít a legelső forinttól kezdve.</div>
                    </div>
                </div>

                <!-- Kiemelt Behelyettesítős Mondat Kártya -->
                <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 22px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.4);">
                    <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; color: #38bdf8; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                        <span>✍️</span> A te egyéni döntési szabályod:
                    </div>

                    ${cfg.type === 5 ? `
                        <div style="font-size: 15px; font-weight: 500; line-height: 2.1; color: #f1f5f9;">
                            „Legfeljebb 
                            <span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(56, 189, 248, 0.18); border: 1px solid #38bdf8; border-radius: 8px; padding: 2px 8px; vertical-align: middle;">
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('price', 'q', -1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">−</button>
                                <strong style="color: #38bdf8; font-family: var(--font-mono); font-size: 15px;">${qStr}</strong>
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('price', 'q', 1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">+</button>
                            </span>
                            árkülönbség még <strong>nem számít</strong> nekem két járat között, de utána minden forint előnyt jelent, egészen 
                            <span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(56, 189, 248, 0.18); border: 1px solid #38bdf8; border-radius: 8px; padding: 2px 8px; vertical-align: middle;">
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('price', 'p', -1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">−</button>
                                <strong style="color: #38bdf8; font-family: var(--font-mono); font-size: 15px;">${pStr}</strong>
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('price', 'p', 1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">+</button>
                            </span>
                            különbségig, ahonnan már <strong>egyértelműen az olcsóbb járat</strong> felé billen a mérleg.”
                        </div>
                    ` : `
                        <div style="font-size: 15px; font-weight: 500; line-height: 2.1; color: #f1f5f9;">
                            „Már a legkisebb árelőny is számít nekem, és 
                            <span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(56, 189, 248, 0.18); border: 1px solid #38bdf8; border-radius: 8px; padding: 2px 8px; vertical-align: middle;">
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('price', 'p', -1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">−</button>
                                <strong style="color: #38bdf8; font-family: var(--font-mono); font-size: 15px;">${pStr}</strong>
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('price', 'p', 1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">+</button>
                            </span>
                            árkülönbségnél már <strong>100%-ban az olcsóbb opció</strong> a nyerő.”
                        </div>
                    `}
                </div>

                ${this.renderMiniGraph(cfg.type, cfg.q, cfg.p, 'Árkülönbség (Ft)')}
            `;
        }

        // 2. MENETIDŐ LÉPÉS
        renderDurationStep(container) {
            const cfg = this.state.config.duration;
            const qStr = cfg.q < 1 ? `${Math.round(cfg.q * 60)} perc` : `${cfg.q} óra`;
            const pStr = `${cfg.p} óra`;

            container.innerHTML = `
                <div style="margin-bottom: 18px;">
                    <h4 style="margin: 0 0 6px 0; font-size: 16px; font-weight: 800; color: var(--text-main);">⏱️ 2. Utazási Idő (Menetidő) Tolerancia</h4>
                    <p style="margin: 0; font-size: 13px; color: var(--text-muted);">Mennyi plusz menetidőt vállalsz be egy jobb vagy olcsóbb járatért?</p>
                </div>

                <!-- Mintázat választó kártyák -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px;">
                    <div onclick="window.PrometheeWizardInstance.setType('duration', 5)" style="cursor: pointer; padding: 14px; border-radius: 12px; border: 2px solid ${cfg.type === 5 ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${cfg.type === 5 ? 'rgba(37, 99, 235, 0.06)' : 'var(--bg-surface)'}; transition: all 0.2s ease;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 4px;">🟢 Rugalmas Időtűrés (Ajánlott)</div>
                        <div style="font-size: 11.5px; color: var(--text-muted); line-height: 1.4;">Egy kis menetidő-eltérés még nem rontja el az utazást, de a túl hosszú út már büntetendő.</div>
                    </div>
                    <div onclick="window.PrometheeWizardInstance.setType('duration', 3)" style="cursor: pointer; padding: 14px; border-radius: 12px; border: 2px solid ${cfg.type === 3 ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${cfg.type === 3 ? 'rgba(37, 99, 235, 0.06)' : 'var(--bg-surface)'}; transition: all 0.2s ease;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 4px;">⚡ Idő-Minimalista</div>
                        <div style="font-size: 11.5px; color: var(--text-muted); line-height: 1.4;">Minden plusz utazási perc azonnal ront a járat megítélésén.</div>
                    </div>
                </div>

                <!-- Kiemelt Behelyettesítős Mondat Kártya -->
                <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 22px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.4);">
                    <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; color: #38bdf8; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                        <span>✍️</span> A te egyéni döntési szabályod:
                    </div>

                    ${cfg.type === 5 ? `
                        <div style="font-size: 15px; font-weight: 500; line-height: 2.1; color: #f1f5f9;">
                            „Legfeljebb 
                            <span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(56, 189, 248, 0.18); border: 1px solid #38bdf8; border-radius: 8px; padding: 2px 8px; vertical-align: middle;">
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('duration', 'q', -1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">−</button>
                                <strong style="color: #38bdf8; font-family: var(--font-mono); font-size: 15px;">${qStr}</strong>
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('duration', 'q', 1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">+</button>
                            </span>
                            plusz utazási idő még <strong>belefér nekem</strong>, de ezen felül minden perc ront az élményen, és 
                            <span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(56, 189, 248, 0.18); border: 1px solid #38bdf8; border-radius: 8px; padding: 2px 8px; vertical-align: middle;">
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('duration', 'p', -1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">−</button>
                                <strong style="color: #38bdf8; font-family: var(--font-mono); font-size: 15px;">${pStr}</strong>
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('duration', 'p', 1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">+</button>
                            </span>
                            plusz menetidőnél már <strong>100%-ban a gyorsabb járat</strong> a jobb.”
                        </div>
                    ` : `
                        <div style="font-size: 15px; font-weight: 500; line-height: 2.1; color: #f1f5f9;">
                            „Már a legkisebb menetidő-többlet is számít, és 
                            <span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(56, 189, 248, 0.18); border: 1px solid #38bdf8; border-radius: 8px; padding: 2px 8px; vertical-align: middle;">
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('duration', 'p', -1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">−</button>
                                <strong style="color: #38bdf8; font-family: var(--font-mono); font-size: 15px;">${pStr}</strong>
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('duration', 'p', 1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">+</button>
                            </span>
                            plusz menetidőnél már <strong>teljes dominanciát</strong> élvez a rövidebb járat.”
                        </div>
                    `}
                </div>

                ${this.renderMiniGraph(cfg.type, cfg.q, cfg.p, 'Menetidő különbség (óra)')}
            `;
        }

        // 3. TARTÓZKODÁSI IDŐ LÉPÉS
        renderStayStep(container) {
            const cfg = this.state.config.stay;
            const qStr = `${cfg.q} nap`;
            const pStr = `${cfg.p} nap`;

            container.innerHTML = `
                <div style="margin-bottom: 18px;">
                    <h4 style="margin: 0 0 6px 0; font-size: 16px; font-weight: 800; color: var(--text-main);">🌙 3. Tartózkodási Idő Rugalmassága</h4>
                    <p style="margin: 0; font-size: 13px; color: var(--text-muted);">Mennyire ragaszkodsz a pontosan megcélzott kinttartózkodási napok számához?</p>
                </div>

                <!-- Mintázat választó kártyák -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px;">
                    <div onclick="window.PrometheeWizardInstance.setType('stay', 5)" style="cursor: pointer; padding: 14px; border-radius: 12px; border: 2px solid ${cfg.type === 5 ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${cfg.type === 5 ? 'rgba(37, 99, 235, 0.06)' : 'var(--bg-surface)'}; transition: all 0.2s ease;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 4px;">🌊 Rugalmas Utazó (Ajánlott)</div>
                        <div style="font-size: 11.5px; color: var(--text-muted); line-height: 1.4;">±1 nap eltérés még észrevétlen, de a túl rövid vagy túl hosszú út már nem ideális.</div>
                    </div>
                    <div onclick="window.PrometheeWizardInstance.setType('stay', 3)" style="cursor: pointer; padding: 14px; border-radius: 12px; border: 2px solid ${cfg.type === 3 ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${cfg.type === 3 ? 'rgba(37, 99, 235, 0.06)' : 'var(--bg-surface)'}; transition: all 0.2s ease;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 4px;">🎯 Fix Időkeret</div>
                        <div style="font-size: 11.5px; color: var(--text-muted); line-height: 1.4;">Minden egyes napos eltérés azonnal rontja a járat pontszámát.</div>
                    </div>
                </div>

                <!-- Kiemelt Behelyettesítős Mondat Kártya -->
                <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 22px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.4);">
                    <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; color: #38bdf8; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                        <span>✍️</span> A te egyéni döntési szabályod:
                    </div>

                    ${cfg.type === 5 ? `
                        <div style="font-size: 15px; font-weight: 500; line-height: 2.1; color: #f1f5f9;">
                            „Legfeljebb 
                            <span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(56, 189, 248, 0.18); border: 1px solid #38bdf8; border-radius: 8px; padding: 2px 8px; vertical-align: middle;">
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('stay', 'q', -1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">−</button>
                                <strong style="color: #38bdf8; font-family: var(--font-mono); font-size: 15px;">${qStr}</strong>
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('stay', 'q', 1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">+</button>
                            </span>
                            eltérés a kívánt napoktól még <strong>teljesen rendben van</strong>, de 
                            <span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(56, 189, 248, 0.18); border: 1px solid #38bdf8; border-radius: 8px; padding: 2px 8px; vertical-align: middle;">
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('stay', 'p', -1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">−</button>
                                <strong style="color: #38bdf8; font-family: var(--font-mono); font-size: 15px;">${pStr}</strong>
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('stay', 'p', 1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">+</button>
                            </span>
                            eltérés felett már <strong>határozottan gyengébbnek</strong> tekintem a járatot.”
                        </div>
                    ` : `
                        <div style="font-size: 15px; font-weight: 500; line-height: 2.1; color: #f1f5f9;">
                            „Már a legkisebb nap-eltérés is ront a járaton, és 
                            <span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(56, 189, 248, 0.18); border: 1px solid #38bdf8; border-radius: 8px; padding: 2px 8px; vertical-align: middle;">
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('stay', 'p', -1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">−</button>
                                <strong style="color: #38bdf8; font-family: var(--font-mono); font-size: 15px;">${pStr}</strong>
                                <button type="button" onclick="window.PrometheeWizardInstance.stepValue('stay', 'p', 1)" style="background: rgba(255,255,255,0.15); border: none; color: #fff; width: 22px; height: 22px; border-radius: 4px; cursor: pointer; font-weight: 900;">+</button>
                            </span>
                            nap eltérésnél már <strong>maximális büntetést</strong> kap a járat.”
                        </div>
                    `}
                </div>

                ${this.renderMiniGraph(cfg.type, cfg.q, cfg.p, 'Eltérés a kívánt napoktól')}
            `;
        }

        // Mini SVG diagram a preferencia görbéről
        renderMiniGraph(type, q, p, label) {
            // Rajzoljuk ki a PROMETHEE preferencia görbét (0 -> q -> p -> 1)
            let pathD = '';
            if (type === 5) {
                // (0, 70) -> (35, 70) -> (75, 10) -> (100, 10)
                pathD = `M 15 70 L 35 70 L 75 10 L 95 10`;
            } else if (type === 3) {
                // (0, 70) -> (75, 10) -> (100, 10)
                pathD = `M 15 70 L 75 10 L 95 10`;
            } else {
                pathD = `M 15 70 L 45 70 L 45 10 L 95 10`;
            }

            return `
                <div style="background: var(--bg-surface); padding: 14px 18px; border-radius: 12px; border: 1px solid var(--border-subtle); display: flex; align-items: center; justify-content: space-between; gap: 16px;">
                    <div>
                        <div style="font-size: 12px; font-weight: 800; color: var(--text-main); margin-bottom: 2px;">📈 Preferenciafüggvény Alakja</div>
                        <div style="font-size: 11px; color: var(--text-muted);">
                            ${type === 5 ? `q = ${q} alatt 0% előny · fokozatos emelkedés · p = ${p} felett 100% előny` : `0-tól p = ${p}-ig egyenletesen emelkedő előny`}
                        </div>
                    </div>
                    <svg viewBox="0 0 100 80" style="width: 100px; height: 50px; overflow: visible;">
                        <!-- Axes -->
                        <line x1="15" y1="70" x2="95" y2="70" stroke="var(--border-subtle)" stroke-width="2" />
                        <line x1="15" y1="10" x2="15" y2="70" stroke="var(--border-subtle)" stroke-width="2" />
                        <!-- Function Path -->
                        <path d="${pathD}" fill="none" stroke="var(--primary)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                </div>
            `;
        }
    }

    window.PROMETHEEWizard = PROMETHEEWizard;
})();
