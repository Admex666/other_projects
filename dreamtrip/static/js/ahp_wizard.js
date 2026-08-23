/**
 * Optivoya AHP (Analytic Hierarchy Process) Wizard Engine
 * 7-point scale pairwise decision framework
 */

(function (window) {
    'use strict';

    // Random Consistency Index (RI) based on matrix size n
    const RI_TABLE = {
        1: 0.0,
        2: 0.0,
        3: 0.58,
        4: 0.90,
        5: 1.12,
        6: 1.24,
        7: 1.32,
        8: 1.41,
        9: 1.45,
        10: 1.49
    };

    // 7-point Saaty scale definitions — clean, no emoji/arrows
    // NOTE: 'sub' is omitted here; generated dynamically from pair names at render time
    const SCALE_7 = [
        { label: 'Sokkal fontosabb', value: 7.0,  dir: 'left',  level: 3, num: '1' },
        { label: 'Kifejezetten',     value: 5.0,  dir: 'left',  level: 2, num: '2' },
        { label: 'Kicsit fontosabb', value: 3.0,  dir: 'left',  level: 1, num: '3' },
        { label: 'Egyformán fontos', value: 1.0,  dir: 'equal', level: 0, num: '4' },
        { label: 'Kicsit fontosabb', value: 1/3,  dir: 'right', level: 1, num: '5' },
        { label: 'Kifejezetten',     value: 1/5,  dir: 'right', level: 2, num: '6' },
        { label: 'Sokkal fontosabb', value: 1/7,  dir: 'right', level: 3, num: '7' }
    ];

    // Helper: resolve the 'sub' label for a scale option given the current criterion pair
    function getScaleSub(opt, c1Name, c2Name) {
        if (opt.dir === 'left')  return c1Name;
        if (opt.dir === 'right') return c2Name;
        return 'Azonos súly';
    }


    class AHPWizard {
        /**
         * @param {Object} options
         * @param {string} options.containerId - Root container ID
         * @param {Array} options.criteria - Array of criteria objects [{ id, name, icon, desc }]
         * @param {string} options.title - Header title
         * @param {string} options.subtitle - Header subtitle
         * @param {string} options.badge - Header badge text
         * @param {string} options.introTitle - Intro heading
         * @param {string} options.introDesc - Intro text
         * @param {string} options.introSlotHtml - Custom HTML to render in the intro (e.g. climate selector)
         * @param {string} options.ctaText - Final submission button text
         * @param {string} options.backLinkUrl - URL for back link
         * @param {string} options.backLinkText - Text for back link
         * @param {Function} options.onComplete - Callback when submitted (receives { weights, criteria, cr, ci })
         */
        constructor(options) {
            this.container = document.getElementById(options.containerId);
            if (!this.container) {
                console.error(`AHPWizard: Container #${options.containerId} not found.`);
                return;
            }

            this.criteria = options.criteria || [];
            this.title = options.title || 'Preferenciák & Súlyozás';
            this.subtitle = options.subtitle || 'Hasonlítsd össze a szempontokat párban';
            this.badge = options.badge || 'Döntési Modell';
            this.introTitle = options.introTitle || 'Mi fontos számodra a döntésnél?';
            this.introDesc = options.introDesc || 'Nincs jó vagy rossz válasz. Hasonlítsd össze a szempontokat páronként, és mi ezek alapján személyre szabjuk az eredményeket.';
            this.introSlotHtml = options.introSlotHtml || '';
            this.ctaText = options.ctaText || 'Kalkuláció Indítása';
            this.backLinkUrl = options.backLinkUrl || '/home';
            this.backLinkText = options.backLinkText || 'Vissza az alapadatokhoz';
            this.onComplete = options.onComplete || function () {};

            // Build list of pairs
            this.pairs = [];
            for (let i = 0; i < this.criteria.length; i++) {
                for (let j = i + 1; j < this.criteria.length; j++) {
                    this.pairs.push({
                        idx1: i,
                        idx2: j,
                        c1: this.criteria[i],
                        c2: this.criteria[j],
                        id: `${this.criteria[i].id}_vs_${this.criteria[j].id}`
                    });
                }
            }

            // Storage key for session persistence
            this.storageKey = options.storageKey || ('ahp_wizard_' + (window.location.pathname.replace(/[^a-zA-Z0-9_-]/g, '_') || 'default'));

            // State
            this.answers = {}; // pairId -> optionIndex (0..6)
            this.currentStep = 0; // 0: Intro, 1..N: Wizard steps, N+1: Clarification (if needed), N+2: Summary
            this.clarificationPair = null;
            this.cr = 0.0;
            this.ci = 0.0;
            this.weights = {}; // criterionId -> weight (0..1)
            this.weightsList = [];

            this.init();
        }

        /**
         * Persist current wizard state to sessionStorage and reflect step in URL
         */
        saveState() {
            try {
                const state = {
                    currentStep: this.currentStep,
                    answers: this.answers,
                    clarificationPairId: this.clarificationPair ? this.clarificationPair.id : null,
                    weights: this.weights,
                    weightsList: this.weightsList,
                    cr: this.cr,
                    ci: this.ci,
                    timestamp: Date.now()
                };
                sessionStorage.setItem(this.storageKey, JSON.stringify(state));

                // Sync step to URL query param
                if (typeof window !== 'undefined' && window.history && window.history.replaceState) {
                    const url = new URL(window.location.href);
                    if (this.currentStep > 0) {
                        url.searchParams.set('step', this.currentStep);
                    } else {
                        url.searchParams.delete('step');
                    }
                    window.history.replaceState(null, '', url.toString());
                }
            } catch (e) {
                console.warn('[AHP Wizard] Failed to save state to sessionStorage:', e);
            }
        }

        /**
         * Restore wizard state from sessionStorage / URL query on page load / refresh
         */
        restoreState() {
            try {
                const raw = sessionStorage.getItem(this.storageKey);
                if (!raw) return false;
                const state = JSON.parse(raw);
                if (!state || typeof state !== 'object') return false;

                if (state.answers && typeof state.answers === 'object') {
                    this.answers = state.answers;
                }

                // Check URL query first, then fallback to stored currentStep
                const urlParams = new URLSearchParams(window.location.search);
                const urlStep = parseInt(urlParams.get('step'), 10);

                if (!isNaN(urlStep) && urlStep >= 0 && urlStep <= this.pairs.length + 1) {
                    this.currentStep = urlStep;
                } else if (typeof state.currentStep === 'number') {
                    this.currentStep = state.currentStep;
                }

                if (state.weights && Object.keys(state.weights).length > 0) {
                    this.weights = state.weights;
                    this.weightsList = state.weightsList || [];
                    this.cr = state.cr || 0;
                    this.ci = state.ci || 0;
                }

                // Safety validation: if user jumps to a step where previous answers are missing,
                // adjust to the earliest unanswered step
                if (this.currentStep >= 1 && this.currentStep <= this.pairs.length) {
                    const targetIdx = this.currentStep - 1;
                    for (let i = 0; i < targetIdx; i++) {
                        if (this.answers[this.pairs[i].id] === undefined) {
                            this.currentStep = i + 1;
                            break;
                        }
                    }
                }

                // If restored to summary but weights not yet calculated, calculate now
                if (this.currentStep === this.pairs.length + 1 && (!this.weightsList || this.weightsList.length === 0)) {
                    this.calculateAHP(false);
                }

                return true;
            } catch (e) {
                console.warn('[AHP Wizard] Failed to restore state from sessionStorage:', e);
                return false;
            }
        }

        /**
         * Clear stored wizard state from sessionStorage and remove step query param
         */
        clearState() {
            try {
                sessionStorage.removeItem(this.storageKey);
                if (typeof window !== 'undefined' && window.history && window.history.replaceState) {
                    const url = new URL(window.location.href);
                    url.searchParams.delete('step');
                    window.history.replaceState(null, '', url.toString());
                }
            } catch (e) {
                console.warn('[AHP Wizard] Failed to clear sessionStorage state:', e);
            }
        }

        init() {
            this.restoreState();
            this.render();
            this.bindGlobalKeys();
            this.bindHistoryEvents();
        }

        bindHistoryEvents() {
            window.addEventListener('popstate', () => {
                const urlParams = new URLSearchParams(window.location.search);
                const urlStep = parseInt(urlParams.get('step'), 10);
                if (!isNaN(urlStep) && urlStep >= 0 && urlStep <= this.pairs.length + 1) {
                    this.currentStep = urlStep;
                    this.render();
                } else if (!urlParams.has('step') && this.currentStep !== 0) {
                    this.currentStep = 0;
                    this.render();
                }
            });
        }

        bindGlobalKeys() {
            window.addEventListener('keydown', (e) => {
                if (this.currentStep >= 1 && this.currentStep <= this.pairs.length) {
                    const key = e.key;
                    if (['1', '2', '3', '4', '5', '6', '7'].includes(key)) {
                        const optIdx = parseInt(key, 10) - 1;
                        this.selectOption(optIdx);
                    } else if (key === 'ArrowRight' || key === 'Enter') {
                        this.nextStep();
                    } else if (key === 'ArrowLeft') {
                        this.prevStep();
                    }
                }
            });
        }

        renderFlowProgress(percent, activeLabel) {
            return `
                <div class="flow-progress-bar-container" style="margin-bottom: 24px;">
                    <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 700; color: var(--text-muted); margin-bottom: 8px;">
                        <span style="color: ${percent >= 35 ? 'var(--text-main)' : 'var(--text-muted)'};">Alapadatok & Szűrés</span>
                        <span style="color: ${percent >= 50 && percent < 100 ? 'var(--primary)' : (percent === 100 ? 'var(--text-main)' : 'var(--text-muted)')}; font-weight: ${percent >= 50 && percent < 100 ? '800' : '700'};">Döntési Preferenciák</span>
                        <span style="color: ${percent >= 98 ? 'var(--primary)' : 'var(--text-muted)'}; font-weight: ${percent >= 98 ? '800' : '700'};">Személyre Szabott Eredmények</span>
                    </div>
                    <div style="height: 6px; background: var(--border-subtle); border-radius: 10px; overflow: hidden;">
                        <div style="width: ${percent}%; height: 100%; background: linear-gradient(90deg, var(--primary), var(--accent, #6366f1)); border-radius: 10px; transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);"></div>
                    </div>
                </div>
            `;
        }

        render() {
            if (this.currentStep === 0) {
                this.renderIntro();
            } else if (this.currentStep >= 1 && this.currentStep <= this.pairs.length) {
                this.renderWizardStep(this.currentStep - 1);
            } else {
                this.renderSummary();
            }
        }


        renderIntro() {
            this.container.innerHTML = `
                <div class="advisor-container">
                    <!-- VISSZA GOMB FENT -->
                    <a href="${this.backLinkUrl}" class="btn-back-link">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="19" y1="12" x2="5" y2="12"></line>
                            <polyline points="12 19 5 12 12 5"></polyline>
                        </svg>
                        <span>${this.backLinkText}</span>
                    </a>

                    <div class="page-header" style="text-align: left; margin-bottom: 20px;">
                        <div style="display: inline-flex; align-items: center; gap: 8px; background: var(--accent-glow); color: var(--primary); padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 10px;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
                            </svg>
                            <span>${this.badge}</span>
                        </div>
                        <h1 class="page-title" style="margin-bottom: 6px;">${this.title}</h1>
                        <p class="page-subtitle" style="margin: 0;">${this.subtitle}</p>
                    </div>

                    <!-- FOLYAMAT PROGRESS BAR -->
                    ${this.renderFlowProgress(50, 'Döntési Preferenciák')}

                    <div class="advisor-main-card">
                        <!-- INTRO HERO BANNER -->
                        <div class="ahp-intro-card">
                            <div class="ahp-intro-icon">🎯</div>
                            <div class="ahp-intro-content">
                                <h3>${this.introTitle}</h3>
                                <p>${this.introDesc}</p>
                            </div>
                        </div>

                        <!-- OPTIONAL EXTRA SLOT (e.g. Climate temperature) -->
                        ${this.introSlotHtml ? `<div class="ahp-intro-slot">${this.introSlotHtml}</div>` : ''}

                        <!-- CRITERIA PILLS OVERVIEW -->
                        <div class="advisor-section-label" style="margin-top: 24px;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="3" y1="9" x2="21" y2="9"></line>
                                <line x1="9" y1="21" x2="9" y2="9"></line>
                            </svg>
                            <span>Összehasonlítandó Szempontok</span>
                        </div>

                        <div class="ahp-criteria-overview-grid">
                            ${this.criteria.map(c => `
                                <div class="ahp-criterion-mini-card">
                                    <span class="mini-icon">${c.icon || '📌'}</span>
                                    <div class="mini-text">
                                        <strong>${c.name}</strong>
                                        <small>${c.desc || ''}</small>
                                    </div>
                                </div>
                            `).join('')}
                        </div>

                        <!-- START CTA BUTTON -->
                        <button type="button" class="btn btn-primary btn-block ahp-start-btn" onclick="window._ahpInstance.startWizard()">
                            <span>Összehasonlítás Indítása</span>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <line x1="5" y1="12" x2="19" y2="12"></line>
                                <polyline points="12 5 19 12 12 19"></polyline>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
        }

        startWizard() {
            this.currentStep = 1;
            this.saveState();
            this.render();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        renderWizardStep(pairIndex) {
            const pair = this.pairs[pairIndex];
            const currentAnswer = this.answers[pair.id];
            const totalSteps = this.pairs.length;
            const stepNum = pairIndex + 1;
            const progressPct = 50 + Math.round((stepNum / totalSteps) * 40);

            // Progress dots
            const dotsHtml = this.pairs.map((p, idx) => {
                let statusClass = '';
                if (idx < pairIndex) statusClass = 'completed';
                else if (idx === pairIndex) statusClass = 'active';
                return `<span class="ahp-dot ${statusClass}" title="${idx + 1}. kérdés"></span>`;
            }).join('');

            this.container.innerHTML = `
                <div class="advisor-container ahp-step-container">
                    <!-- VISSZA GOMB FENT -->
                    <a href="javascript:void(0)" onclick="window._ahpInstance.prevStep()" class="btn-back-link">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="19" y1="12" x2="5" y2="12"></line>
                            <polyline points="12 19 5 12 12 5"></polyline>
                        </svg>
                        <span>${stepNum === 1 ? this.backLinkText : 'Vissza az előző kérdésre'}</span>
                    </a>

                    <!-- FEJLÉC -->
                    <div class="page-header" style="text-align: left; margin-bottom: 20px;">
                        <div style="display: inline-flex; align-items: center; gap: 8px; background: var(--accent-glow); color: var(--primary); padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 10px;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
                            </svg>
                            <span>${this.badge}</span>
                        </div>
                        <h1 class="page-title" style="margin-bottom: 6px;">${this.title}</h1>
                        <p class="page-subtitle" style="margin: 0;">${this.subtitle}</p>
                    </div>

                    <!-- FOLYAMAT PROGRESS BAR -->
                    ${this.renderFlowProgress(progressPct, 'Döntési Preferenciák')}

                    <!-- MAIN ADVISOR CARD -->
                    <div class="advisor-main-card">
                        
                        <!-- SZEKCIÓ CÍMKE -->
                        <div class="advisor-section-label" style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                                </svg>
                                <span>Páros Összehasonlítás</span>
                            </div>
                            <div class="ahp-dots-row">
                                ${dotsHtml}
                            </div>
                        </div>

                        <!-- 2 BENTO KÁRTYA FACEOFF DISPLAY -->
                        <div class="ahp-faceoff-grid" style="margin-bottom: 24px;">
                            <!-- BAL OLDALI KRITÉRIUM BENTO -->
                            <div class="advisor-panel ahp-crit-panel ${currentAnswer !== undefined && currentAnswer < 3 ? 'crit-favored' : ''}">
                                <div>
                                    <div class="panel-header-title" style="font-size: 17px;">
                                        <span style="font-size: 22px;">${pair.c1.icon || '✈️'}</span>
                                        <span>${pair.c1.name}</span>
                                    </div>
                                    <div class="panel-header-desc" style="margin-bottom: 0;">${pair.c1.desc || ''}</div>
                                </div>
                                <div style="margin-top: 14px; display: flex; align-items: center; justify-content: space-between;">
                                    <span class="chip-select-btn ${currentAnswer !== undefined && currentAnswer < 3 ? 'active' : ''}" style="pointer-events: none; padding: 6px 14px; font-size: 11.5px;">
                                        ${currentAnswer !== undefined && currentAnswer < 3 ? '✓ Preferált szempont' : 'A szempont'}
                                    </span>
                                </div>
                            </div>

                            <!-- KÖZÉPSŐ VS JELVÉNY -->
                            <div class="ahp-vs-badge">
                                <span>VS</span>
                            </div>

                            <!-- JOBB OLDALI KRITÉRIUM BENTO -->
                            <div class="advisor-panel ahp-crit-panel ${currentAnswer !== undefined && currentAnswer > 3 ? 'crit-favored' : ''}">
                                <div>
                                    <div class="panel-header-title" style="font-size: 17px;">
                                        <span style="font-size: 22px;">${pair.c2.icon || '💰'}</span>
                                        <span>${pair.c2.name}</span>
                                    </div>
                                    <div class="panel-header-desc" style="margin-bottom: 0;">${pair.c2.desc || ''}</div>
                                </div>
                                <div style="margin-top: 14px; display: flex; align-items: center; justify-content: space-between;">
                                    <span class="chip-select-btn ${currentAnswer !== undefined && currentAnswer > 3 ? 'active' : ''}" style="pointer-events: none; padding: 6px 14px; font-size: 11.5px;">
                                        ${currentAnswer !== undefined && currentAnswer > 3 ? '✓ Preferált szempont' : 'B szempont'}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <!-- 7 FOKOZATÚ SKÁLA KONTÉNER -->
                        <div class="advisor-panel ahp-scale-outer-panel" style="padding: 0; margin-bottom: 24px; overflow: hidden;">
                            <!-- LEGEND HEADER -->
                            <div class="ahp-scale-legend-bar">
                                <div class="legend-side legend-amber">
                                    <span class="legend-dot amber"></span>
                                    <span><strong>${pair.c1.name}</strong> fontosabb</span>
                                </div>
                                <div class="legend-center-label">Egyforma súly</div>
                                <div class="legend-side legend-indigo" style="text-align: right;">
                                    <span><strong>${pair.c2.name}</strong> fontosabb</span>
                                    <span class="legend-dot indigo"></span>
                                </div>
                            </div>

                            <!-- 7 BUTTONS GRID -->
                            <div style="padding: 14px;">
                                <div class="ahp-scale-7-grid">
                                    ${SCALE_7.map((opt, idx) => {
                                        const isSelected = currentAnswer === idx;
                                        let dirClass = opt.dir === 'left'  ? `opt-left opt-lvl-${opt.level}`
                                                      : opt.dir === 'right' ? `opt-right opt-lvl-${opt.level}`
                                                      : 'opt-equal';
                                        const sub = getScaleSub(opt, pair.c1.name, pair.c2.name);
                                        const dots = opt.dir === 'equal'
                                            ? `<div class="chip-intensity-row equal"><span class="idot f"></span><span class="idot f"></span><span class="idot f"></span></div>`
                                            : `<div class="chip-intensity-row ${opt.dir}">
                                                <span class="idot ${opt.level >= 1 ? 'f' : ''}"></span>
                                                <span class="idot ${opt.level >= 2 ? 'f' : ''}"></span>
                                                <span class="idot ${opt.level >= 3 ? 'f' : ''}"></span>
                                               </div>`;
                                        return `
                                            <button type="button"
                                                class="ahp-scale-chip-btn ${dirClass} ${isSelected ? 'selected' : ''}"
                                                onclick="window._ahpInstance.selectOption(${idx})"
                                                data-idx="${idx}">
                                                <div class="chip-key-badge">${opt.num}</div>
                                                ${dots}
                                                <div class="chip-title-row">${opt.label}</div>
                                                <div class="chip-sub-row">${sub}</div>
                                            </button>
                                        `;
                                    }).join('')}
                                </div>
                            </div>
                        </div>


                        <!-- LÁBLÉC NAVIGÁCIÓ -->
                        <div class="ahp-wizard-nav">
                            <button type="button" class="btn btn-secondary ahp-btn-back" onclick="window._ahpInstance.prevStep()">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="19" y1="12" x2="5" y2="12"></line>
                                    <polyline points="12 19 5 12 12 5"></polyline>
                                </svg>
                                <span>${stepNum === 1 ? 'Bevezető' : 'Előző kérdés'}</span>
                            </button>

                            <div class="ahp-keyboard-tip">
                                💡 Billentyűzet: Nyomj <strong>1-7</strong> gombokat vagy <strong>Nyilakat</strong>!
                            </div>

                            <button type="button" 
                                class="btn btn-primary ahp-btn-next ${currentAnswer === undefined ? 'btn-disabled' : ''}" 
                                onclick="window._ahpInstance.nextStep()"
                                ${currentAnswer === undefined ? 'disabled' : ''}>
                                <span>${stepNum === totalSteps ? 'Összegzés megtekintése' : 'Következő döntés'}</span>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="5" y1="12" x2="19" y2="12"></line>
                                    <polyline points="12 5 19 12 12 19"></polyline>
                                </svg>
                            </button>
                        </div>

                    </div>
                </div>
            `;
        }

        selectOption(optIndex) {
            const pairIndex = this.currentStep - 1;
            const pair = this.pairs[pairIndex];
            this.answers[pair.id] = optIndex;
            this.saveState();
            this.render();

            // Auto-advance after brief visual feedback (300ms)
            setTimeout(() => {
                if (this.currentStep === pairIndex + 1 && this.answers[pair.id] === optIndex) {
                    this.nextStep();
                }
            }, 300);
        }

        prevStep() {
            if (this.currentStep > 0) {
                this.currentStep--;
                this.saveState();
                this.render();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        }

        nextStep() {
            const pairIndex = this.currentStep - 1;
            if (pairIndex >= 0 && pairIndex < this.pairs.length) {
                const pair = this.pairs[pairIndex];
                if (this.answers[pair.id] === undefined) {
                    return; // Must select an answer
                }
            }

            if (this.currentStep < this.pairs.length) {
                this.currentStep++;
                this.saveState();
                this.render();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            } else {
                // All pairs answered, calculate AHP
                this.calculateAHP(true);
            }
        }

        calculateAHP(autoRender = true) {
            const n = this.criteria.length;
            const matrix = Array.from({ length: n }, () => Array(n).fill(1.0));

            // Populate matrix
            for (const pair of this.pairs) {
                const optIdx = this.answers[pair.id] !== undefined ? this.answers[pair.id] : 3;
                const saatyVal = SCALE_7[optIdx].value;
                matrix[pair.idx1][pair.idx2] = saatyVal;
                matrix[pair.idx2][pair.idx1] = 1.0 / saatyVal;
            }

            // 1. Geometric mean eigenvector calculation
            const r = [];
            for (let i = 0; i < n; i++) {
                let prod = 1.0;
                for (let j = 0; j < n; j++) {
                    prod *= matrix[i][j];
                }
                r.push(Math.pow(prod, 1.0 / n));
            }
            const sumR = r.reduce((a, b) => a + b, 0);
            const weightsArray = r.map(val => (sumR > 0 ? val / sumR : 1.0 / n));

            // 2. Calculate Lambda max
            let lambdaMax = 0.0;
            for (let i = 0; i < n; i++) {
                let sumRow = 0.0;
                for (let j = 0; j < n; j++) {
                    sumRow += matrix[i][j] * weightsArray[j];
                }
                lambdaMax += sumRow / weightsArray[i];
            }
            lambdaMax = lambdaMax / n;

            // 3. Consistency Index & Ratio
            this.ci = n > 1 ? (lambdaMax - n) / (n - 1) : 0.0;
            const ri = RI_TABLE[n] || 0.90;
            this.cr = ri > 0 ? this.ci / ri : 0.0;

            console.log(`[AHP ENGINE] Weights:`, weightsArray, `LambdaMax: ${lambdaMax.toFixed(3)}, CI: ${this.ci.toFixed(3)}, CR: ${this.cr.toFixed(3)}`);

            // Store weights
            this.weights = {};
            this.weightsList = this.criteria.map((c, idx) => {
                const w = weightsArray[idx];
                this.weights[c.id] = w;
                return {
                    id: c.id,
                    name: c.name,
                    icon: c.icon,
                    weight: w,
                    percent: Math.round(w * 100)
                };
            });

            // Normalize percentages to sum to exactly 100%
            const sumPct = this.weightsList.reduce((a, b) => a + b.percent, 0);
            if (sumPct !== 100 && this.weightsList.length > 0) {
                const diff = 100 - sumPct;
                this.weightsList[0].percent += diff;
            }

            // Consistency logging for quality control (hidden from user)
            const crStatus = this.cr < 0.10 ? 'Kiváló (CR < 0.10)' : (this.cr < 0.20 ? 'Elfogadható (CR < 0.20)' : 'Enyhén inkonzisztens (CR >= 0.20)');
            console.groupCollapsed(`%c[AHP Quality Control] Döntési Konzisztencia Elemzés`, 'color: #10b981; font-weight: bold;');
            console.log(`Lambda Max: ${lambdaMax.toFixed(4)}`);
            console.log(`Consistency Index (CI): ${this.ci.toFixed(4)}`);
            console.log(`Consistency Ratio (CR): ${this.cr.toFixed(4)} -> ${crStatus}`);
            console.log(`Súlyok megoszlása:`, this.weights);
            console.groupEnd();

            // Proceed directly to Summary
            this.currentStep = this.pairs.length + 1;

            this.saveState();
            if (autoRender) {
                this.render();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        }


        generateInsightText() {
            const sorted = [...this.weightsList].sort((a, b) => b.weight - a.weight);
            if (sorted.length < 2) return '';

            const top = sorted[0];
            const second = sorted[1];
            const lowest = sorted[sorted.length - 1];

            if (top.percent >= 38) {
                return `Nálad kiemelkedően a <strong>${top.name}</strong> a legmeghatározóbb szempont (${top.percent}%), ami jelentősen formálja a végső rangsort. A második legfontosabb tényező a <strong>${second.name}</strong> (${second.percent}%).`;
            } else {
                return `A döntési profilod kiegyensúlyozott: a <strong>${top.name}</strong> (${top.percent}%) és a <strong>${second.name}</strong> (${second.percent}%) vezetik a szempontjaidat, míg a <strong>${lowest.name}</strong> (${lowest.percent}%) kapta a legkisebb súlyt.`;
            }
        }

        renderSummary() {
            const sortedWeights = [...this.weightsList].sort((a, b) => b.weight - a.weight);
            const insight = this.generateInsightText();

            this.container.innerHTML = `
                <div class="advisor-container">
                    <!-- VISSZA GOMB FENT -->
                    <a href="javascript:void(0)" onclick="window._ahpInstance.restartWizard()" class="btn-back-link">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="19" y1="12" x2="5" y2="12"></line>
                            <polyline points="12 19 5 12 12 5"></polyline>
                        </svg>
                        <span>Újrakezdés</span>
                    </a>

                    <div class="page-header" style="text-align: left; margin-bottom: 20px;">
                        <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 10px;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                            <span>Preferenciák Készre Számolva</span>
                        </div>
                        <h1 class="page-title" style="margin-bottom: 6px;">Személyre Szabott Súlyozásod</h1>
                        <p class="page-subtitle" style="margin: 0;">A válaszaid alapján meghatároztuk az egyéni döntési profilodat</p>
                    </div>

                    <!-- FOLYAMAT PROGRESS BAR (100%) -->
                    ${this.renderFlowProgress(100, 'Személyre Szabott Eredmények')}

                    <div class="advisor-main-card">
                        <!-- SUMMARY HERO -->
                        <div class="ahp-intro-card" style="border-color: rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.05);">
                            <div class="ahp-intro-icon" style="background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.3);">✨</div>
                            <div class="ahp-intro-content">
                                <h3 style="color: var(--text-main);">Kész! A válaszaid alapján optimalizáltuk a rangsorolást</h3>
                                <p style="color: var(--text-secondary);">${insight}</p>
                            </div>
                        </div>

                        <!-- WEIGHT DISTRIBUTION BARS -->
                        <div class="advisor-section-label" style="margin-top: 24px;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <line x1="18" y1="20" x2="18" y2="10"></line>
                                <line x1="12" y1="20" x2="12" y2="4"></line>
                                <line x1="6" y1="20" x2="6" y2="14"></line>
                            </svg>
                            <span>Szempontok Súlya a Te Értékelésedben</span>
                        </div>

                        <div class="ahp-summary-weights-list">
                            ${sortedWeights.map(item => `
                                <div class="ahp-summary-weight-row">
                                    <div class="weight-row-meta">
                                        <span class="weight-row-name">
                                            <span class="weight-icon">${item.icon || '📌'}</span>
                                            <strong>${item.name}</strong>
                                        </span>
                                        <span class="weight-row-val">${item.percent}%</span>
                                    </div>
                                    <div class="weight-row-track">
                                        <div class="weight-row-fill" style="width: ${item.percent}%;"></div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>

                        <!-- ACTIONS -->
                        <div class="ahp-summary-actions">
                            <button type="button" class="btn btn-secondary ahp-btn-restart" onclick="window._ahpInstance.restartWizard()">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
                                </svg>
                                <span>Újrakezdés</span>
                            </button>

                            <button type="button" class="btn btn-primary ahp-btn-submit" onclick="window._ahpInstance.submitResults()">
                                <span>${this.ctaText}</span>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                    <line x1="5" y1="12" x2="19" y2="12"></line>
                                    <polyline points="12 5 19 12 12 19"></polyline>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        restartWizard() {
            this.clearState();
            this.answers = {};
            this.currentStep = 1;
            this.clarificationPair = null;
            this.weights = {};
            this.weightsList = [];
            this.saveState();
            this.render();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        submitResults() {
            this.clearState();
            if (typeof this.onComplete === 'function') {
                this.onComplete({
                    weights: this.weights,
                    weightsList: this.weightsList,
                    cr: this.cr,
                    ci: this.ci,
                    answers: this.answers
                });
            }
        }
    }

    // Expose to global
    window.AHPWizard = AHPWizard;

})(window);
