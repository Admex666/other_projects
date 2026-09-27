/**
 * Optivoya Advisor Workspace v2 — Dynamic Requirement Discovery & Preference Model (Phase 2)
 * =========================================================================================
 * Manages:
 * 1. Stage 1: Active Travel Dimension Selection (9 canonical dimensions).
 * 2. Stage 2: Focused Pairwise AHP Weighting sliders with live Consistency Ratio (CR) evaluation.
 * 3. 4-Level Structured Criteria Management (HARD, SOFT, AVOID, NICE_TO_HAVE).
 * 4. Phase Transition: DEFINE -> RESEARCH upon advisor approval.
 */

window.AdvisorCriteriaV2 = (() => {
    let currentCaseId = null;
    let criteriaData = null;
    let activeDimensions = [];
    let currentPairs = [];
    let pairComparisons = {}; // pair_id -> ratio (0.111 .. 9.0)

    /**
     * Initializes and loads the Criteria model for the given Case.
     */
    async function loadCriteria(caseId) {
        currentCaseId = caseId;
        const container = document.getElementById('criteriaDiscoveryContainer');
        if (!container) return;

        container.innerHTML = `
            <div style="padding: 24px; text-align: center; color: var(--text-muted);">
                <div class="spinner" style="margin: 0 auto 12px;"></div>
                <div style="font-size: 13px;">Döntési dimenziók és preferencia-modell betöltése...</div>
            </div>
        `;

        try {
            const res = await window.AdvisorAPI.fetchWithAuth(`/api/advisor/cases/${caseId}/criteria`);
            if (!res.ok) {
                container.innerHTML = `
                    <div style="padding: 16px; color: #ff6b6b; font-size: 13px;">
                        Nem sikerült betölteni a döntési kritériumokat.
                    </div>
                `;
                return;
            }

            criteriaData = await res.json();
            activeDimensions = criteriaData.selected_dimensions || ["price", "flight_comfort", "location", "hotel_quality"];
            currentPairs = criteriaData.ahp_pairs || [];
            
            // Initialize pair ratios from existing pairs
            pairComparisons = {};
            currentPairs.forEach(p => {
                pairComparisons[p.pair_id] = p.current_ratio || 1.0;
            });

            renderCriteriaDiscoveryView();
        } catch (err) {
            console.error('[AdvisorCriteriaV2] Error loading criteria:', err);
            container.innerHTML = `
                <div style="padding: 16px; color: #ff6b6b; font-size: 13px;">
                    Hiba történt: ${err.message}
                </div>
            `;
        }
    }

    /**
     * Renders the complete 2-stage preference discovery interface.
     */
    function renderCriteriaDiscoveryView() {
        const container = document.getElementById('criteriaDiscoveryContainer');
        if (!container || !criteriaData) return;

        const catalog = criteriaData.dimension_catalog || [];
        const weights = criteriaData.ahp_weights || {};
        const hard = criteriaData.hard_constraints || {};
        const soft = criteriaData.soft_preferences || {};
        const avoid = criteriaData.avoid_rules || {};
        const nice = criteriaData.nice_to_have || {};
        const isApproved = criteriaData.criteria_approved || false;

        container.innerHTML = `
            <div class="criteria-card" style="background: var(--b2b-card); border: 1px solid ${isApproved ? 'rgba(167, 245, 64, 0.3)' : 'rgba(255, 255, 255, 0.1)'}; border-radius: 14px; padding: 24px; margin-bottom: 24px; box-shadow: 0 8px 24px rgba(0,0,0,0.3);">
                
                <!-- Header Banner -->
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 20px; border-bottom: 1px solid var(--b2b-border); padding-bottom: 16px;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                            <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 3px 8px; border-radius: 6px;">
                                Phase 2: Döntési Kritériumok (DEFINE)
                            </span>
                            <span id="crStatusBadge" style="font-size: 11px; font-weight: 600; font-family: var(--font-mono); color: #4ade80; background: rgba(74, 222, 128, 0.1); padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(74, 222, 128, 0.25);">
                                AHP Konzisztens (CR: 0.04)
                            </span>
                        </div>
                        <h3 style="margin: 0 0 6px 0; font-size: 18px; font-family: var(--font-display); color: #fff; display: flex; align-items: center; gap: 8px;">
                            🎯 Mi számít igazán ezen az utazáson?
                        </h3>
                        <p style="margin: 0; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
                            Kétfázisú igényfelmérés: Válaszd ki a releváns dimenziókat, majd hangold be a fókuszált páros prioritásokat.
                        </p>
                    </div>

                    <div style="display: flex; gap: 10px; flex-shrink: 0;">
                        <button type="button" onclick="window.AdvisorCriteriaV2.approveCriteria()" class="btn btn-primary" style="padding: 10px 20px; font-weight: 700; font-size: 13px; display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 14px rgba(167, 245, 64, 0.3);">
                            <span class="material-symbols-outlined" style="font-size: 18px;">verified</span>
                            Kritériumok Jóváhagyása & Tovább a Kutatásra →
                        </button>
                    </div>
                </div>

                <!-- STAGE 1: Relevant Dimension Selection -->
                <div style="margin-bottom: 24px; background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px;">
                    <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--secondary-container); margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                        <span>1. Fázis: Releváns Döntési Dimenziók Kiválasztása</span>
                        <span style="font-size: 11px; color: var(--text-muted);">${activeDimensions.length} / ${catalog.length} aktív</span>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px;">
                        ${catalog.map(dim => {
                            const isActive = activeDimensions.includes(dim.id);
                            return `
                                <div onclick="window.AdvisorCriteriaV2.toggleDimension('${dim.id}')" style="cursor: pointer; padding: 10px 14px; border-radius: 8px; border: 1px solid ${isActive ? 'rgba(167, 245, 64, 0.4)' : 'rgba(255, 255, 255, 0.08)'}; background: ${isActive ? 'rgba(167, 245, 64, 0.08)' : 'rgba(255, 255, 255, 0.02)'}; display: flex; align-items: center; gap: 10px; transition: all 0.2s ease;">
                                    <span class="material-symbols-outlined" style="font-size: 20px; color: ${isActive ? 'var(--secondary-container)' : 'var(--text-muted)'};">
                                        ${dim.icon || 'star'}
                                    </span>
                                    <div style="flex: 1; min-width: 0;">
                                        <div style="font-size: 12.5px; font-weight: 600; color: ${isActive ? '#fff' : 'var(--text-secondary)'}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                            ${dim.name}
                                        </div>
                                        <div style="font-size: 10.5px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                            ${dim.description}
                                        </div>
                                    </div>
                                    <span class="material-symbols-outlined" style="font-size: 18px; color: ${isActive ? 'var(--secondary-container)' : 'rgba(255,255,255,0.2)'};">
                                        ${isActive ? 'check_circle' : 'radio_button_unchecked'}
                                    </span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>

                <!-- STAGE 2: Pairwise AHP Súlyozás & 4-Szintű Kritériumok Grid -->
                <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px;">
                    
                    <!-- Bal Oszlop: AHP Páros Összehasonlítások -->
                    <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px;">
                        <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--secondary-container); margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                            <span>2. Fázis: Fókuszált AHP Páros Súlyozás</span>
                            <span style="font-size: 11px; color: var(--text-muted);">${currentPairs.length} feszítő pár</span>
                        </div>

                        ${currentPairs.length === 0 ? `
                            <div style="padding: 20px; text-align: center; color: var(--text-muted); font-size: 12px;">
                                Válassz legalább 2 dimenziót a páros összehasonlításhoz!
                            </div>
                        ` : `
                            <div style="display: flex; flex-direction: column; gap: 14px;">
                                ${currentPairs.map(pair => {
                                    const val = pairComparisons[pair.pair_id] || 1.0;
                                    return `
                                        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 12px;">
                                            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; margin-bottom: 8px;">
                                                <span style="font-weight: 600; color: #fff; display: flex; align-items: center; gap: 4px;">
                                                    <span class="material-symbols-outlined" style="font-size: 16px; color: var(--secondary-container);">${pair.dim_a_icon}</span>
                                                    ${pair.dim_a_label}
                                                </span>
                                                <span id="disp_${pair.pair_id}" style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: ${val === 1.0 ? 'var(--text-muted)' : 'var(--secondary-container)'};">
                                                    ${getRatioDisplayLabel(val, pair.dim_a_label, pair.dim_b_label)}
                                                </span>
                                                <span style="font-weight: 600; color: #fff; display: flex; align-items: center; gap: 4px;">
                                                    ${pair.dim_b_label}
                                                    <span class="material-symbols-outlined" style="font-size: 16px; color: #38bdf8;">${pair.dim_b_icon}</span>
                                                </span>
                                            </div>
                                            <input type="range" min="0.111" max="9" step="0.1" value="${val}" 
                                                oninput="window.AdvisorCriteriaV2.onPairSliderChange('${pair.pair_id}', this.value)"
                                                style="width: 100%; accent-color: var(--secondary-container); cursor: pointer;">
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        `}

                        <!-- Számított AHP Súlyok Kijelzése -->
                        <div style="margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--b2b-border);">
                            <div style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px;">
                                Eredő Súlyvektor (Normalized Weights)
                            </div>
                            <div id="ahpWeightsBadges" style="display: flex; flex-wrap: wrap; gap: 6px;">
                                ${Object.entries(weights).map(([k, v]) => `
                                    <div style="font-size: 11px; background: rgba(167, 245, 64, 0.12); color: var(--secondary-container); border: 1px solid rgba(167, 245, 64, 0.25); padding: 3px 8px; border-radius: 6px; font-family: var(--font-mono);">
                                        <strong>${k}:</strong> ${(v * 100).toFixed(0)}%
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>

                    <!-- Jobb Oszlop: 4-Szintű Kritériumok (HARD, SOFT, AVOID, NICE_TO_HAVE) -->
                    <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px; display: flex; flex-direction: column; gap: 14px;">
                        <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--secondary-container);">
                            4-Szintű Kritérium Modell
                        </div>

                        <!-- 🔴 HARD CONSTRAINTS -->
                        <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 8px; padding: 12px;">
                            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #f87171; margin-bottom: 6px; display: flex; align-items: center; gap: 4px;">
                                <span class="material-symbols-outlined" style="font-size: 14px;">lock</span>
                                HARD: Kizáró Pass/Fail Feltételek
                            </div>
                            <div style="font-size: 11.5px; color: var(--text-secondary); line-height: 1.5;">
                                <div>• Max. átszállás: <strong>${hard.max_stops !== null ? (hard.max_stops === 0 ? 'Csak közvetlen' : hard.max_stops + ' átszállás') : 'Rugalmas'}</strong></div>
                                <div>• Min. hotel csillag: <strong>${hard.min_hotel_stars || 3}★</strong></div>
                                <div>• Büdzséplafon: <strong>${hard.max_total_budget_huf ? parseInt(hard.max_total_budget_huf).toLocaleString() + ' Ft' : 'Megadva a briefben'}</strong></div>
                            </div>
                        </div>

                        <!-- 🟢 SOFT PREFERENCES -->
                        <div style="background: rgba(167, 245, 64, 0.05); border: 1px solid rgba(167, 245, 64, 0.2); border-radius: 8px; padding: 12px;">
                            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--secondary-container); margin-bottom: 6px; display: flex; align-items: center; gap: 4px;">
                                <span class="material-symbols-outlined" style="font-size: 14px;">tune</span>
                                SOFT: Optimalizálandó Dimenziók
                            </div>
                            <div style="font-size: 11.5px; color: var(--text-secondary); line-height: 1.5;">
                                <div>• Aktív súlyozott dimenziók száma: <strong>${activeDimensions.length} db</strong></div>
                                <div>• Büdzsé tolerancia: <strong>${soft.budget_flexibility_pct || 10}%</strong></div>
                            </div>
                        </div>

                        <!-- 🟡 AVOID RULES -->
                        <div style="background: rgba(251, 191, 36, 0.05); border: 1px solid rgba(251, 191, 36, 0.2); border-radius: 8px; padding: 12px;">
                            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #fbbf24; margin-bottom: 6px; display: flex; align-items: center; gap: 4px;">
                                <span class="material-symbols-outlined" style="font-size: 14px;">block</span>
                                AVOID: Tiltások & Negatív Szűrők
                            </div>
                            <div style="font-size: 11.5px; color: var(--text-secondary); line-height: 1.5;">
                                <div>• Kerülendő korai indulás (&lt;06:00): <strong>${avoid.avoid_early_departures ? 'Igen' : 'Nem'}</strong></div>
                                <div>• Tiltott légitársaságok: <strong>${(avoid.avoid_airlines || []).length ? avoid.avoid_airlines.join(', ') : 'Nincs'}</strong></div>
                            </div>
                        </div>

                        <!-- 🔵 NICE_TO_HAVE -->
                        <div style="background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 12px;">
                            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #38bdf8; margin-bottom: 6px; display: flex; align-items: center; gap: 4px;">
                                <span class="material-symbols-outlined" style="font-size: 14px;">star</span>
                                NICE_TO_HAVE: Értéknövelő Bónuszok
                            </div>
                            <div style="font-size: 11.5px; color: var(--text-secondary); line-height: 1.5;">
                                <div>• Ingyenes lemondás: <strong>${nice.free_cancellation ? 'Igen (+Bónusz)' : 'Nem kritikus'}</strong></div>
                                <div>• Reggeli az árban: <strong>${nice.breakfast_included ? 'Preferált' : 'Opcionális'}</strong></div>
                            </div>
                        </div>

                    </div>
                </div>

            </div>
        `;
    }

    /**
     * Toggles an active dimension and dynamically recalculates minimal pairs.
     */
    async function toggleDimension(dimId) {
        if (activeDimensions.includes(dimId)) {
            if (activeDimensions.length <= 1) {
                alert('Legalább 1 döntési dimenziónak aktívnak kell maradnia!');
                return;
            }
            activeDimensions = activeDimensions.filter(d => d !== dimId);
        } else {
            activeDimensions.push(dimId);
        }

        // Regenerate pairs
        const catalog = criteriaData.dimension_catalog || [];
        const dimMap = {};
        catalog.forEach(d => dimMap[d.id] = d);

        const n = activeDimensions.length;
        currentPairs = [];
        for (let i = 0; i < n; i++) {
            for (let j = i + 1; j < n; j++) {
                const da = dimMap[activeDimensions[i]];
                const db = dimMap[activeDimensions[j]];
                if (da && db) {
                    const pid = `${da.id}__vs__${db.id}`;
                    currentPairs.push({
                        pair_id: pid,
                        dim_a: da.id,
                        dim_a_label: da.name,
                        dim_a_icon: da.icon,
                        dim_b: db.id,
                        dim_b_label: db.name,
                        dim_b_icon: db.icon,
                        current_ratio: pairComparisons[pid] || 1.0
                    });
                }
            }
        }

        await recalculateAHP();
        renderCriteriaDiscoveryView();
    }

    /**
     * Handles live change on a pairwise comparison slider.
     */
    function onPairSliderChange(pairId, value) {
        const ratio = parseFloat(value);
        pairComparisons[pairId] = ratio;

        const dispEl = document.getElementById(`disp_${pairId}`);
        if (dispEl) {
            const pair = currentPairs.find(p => p.pair_id === pairId);
            if (pair) {
                dispEl.innerText = getRatioDisplayLabel(ratio, pair.dim_a_label, pair.dim_b_label);
                dispEl.style.color = ratio === 1.0 ? 'var(--text-muted)' : 'var(--secondary-container)';
            }
        }

        // Debounced AHP calculation
        if (window._ahpCalcTimeout) clearTimeout(window._ahpCalcTimeout);
        window._ahpCalcTimeout = setTimeout(async () => {
            await recalculateAHP();
        }, 200);
    }

    /**
     * Calls backend to calculate exact AHP weights and consistency ratio.
     */
    async function recalculateAHP() {
        if (!currentCaseId || activeDimensions.length === 0) return;

        const comparisons = currentPairs.map(p => ({
            dim_a: p.dim_a,
            dim_b: p.dim_b,
            ratio: pairComparisons[p.pair_id] || 1.0
        }));

        try {
            const res = await window.AdvisorAPI.fetchWithAuth(`/api/advisor/cases/${currentCaseId}/criteria/calculate-ahp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    selected_dimensions: activeDimensions,
                    comparisons: comparisons
                })
            });

            if (res.ok) {
                const data = await res.json();
                criteriaData.ahp_weights = data.weights;

                // Update weights display
                const badgesEl = document.getElementById('ahpWeightsBadges');
                if (badgesEl) {
                    badgesEl.innerHTML = Object.entries(data.weights).map(([k, v]) => `
                        <div style="font-size: 11px; background: rgba(167, 245, 64, 0.12); color: var(--secondary-container); border: 1px solid rgba(167, 245, 64, 0.25); padding: 3px 8px; border-radius: 6px; font-family: var(--font-mono);">
                            <strong>${k}:</strong> ${(v * 100).toFixed(0)}%
                        </div>
                    `).join('');
                }

                // Update CR badge
                const crBadge = document.getElementById('crStatusBadge');
                if (crBadge) {
                    const cr = data.consistency_ratio || 0.0;
                    if (data.is_consistent) {
                        crBadge.style.color = '#4ade80';
                        crBadge.style.borderColor = 'rgba(74, 222, 128, 0.25)';
                        crBadge.style.background = 'rgba(74, 222, 128, 0.1)';
                        crBadge.innerText = `AHP Konzisztens (CR: ${cr.toFixed(2)})`;
                    } else {
                        crBadge.style.color = '#f87171';
                        crBadge.style.borderColor = 'rgba(248, 113, 113, 0.25)';
                        crBadge.style.background = 'rgba(248, 113, 113, 0.1)';
                        crBadge.innerText = `AHP Figyelmeztetés (CR: ${cr.toFixed(2)} > 0.12)`;
                    }
                }
            }
        } catch (err) {
            console.error('[AdvisorCriteriaV2] Error recalculating AHP:', err);
        }
    }

    /**
     * Formats ratio into human-readable comparison text.
     */
    function getRatioDisplayLabel(ratio, labelA, labelB) {
        if (Math.abs(ratio - 1.0) < 0.1) {
            return 'Egyenlő fontosságú';
        } else if (ratio > 1.0) {
            return `${ratio.toFixed(1)}x jobban számít: ${labelA}`;
        } else {
            const inv = (1.0 / ratio).toFixed(1);
            return `${inv}x jobban számít: ${labelB}`;
        }
    }

    /**
     * Approves the configured criteria model and transitions to RESEARCH phase.
     */
    async function approveCriteria() {
        if (!currentCaseId) return;

        try {
            // 1. Save criteria updates first
            await window.AdvisorAPI.fetchWithAuth(`/api/advisor/cases/${currentCaseId}/criteria/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    selected_dimensions: activeDimensions,
                    ahp_weights: criteriaData.ahp_weights
                })
            });

            // 2. Explicitly approve criteria
            const res = await window.AdvisorAPI.fetchWithAuth(`/api/advisor/cases/${currentCaseId}/criteria/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: 'Advisor approved dynamic requirements and AHP weights.' })
            });

            if (res.ok) {
                criteriaData.criteria_approved = true;
                alert('Döntési kritériumok és AHP súlyok sikeresen jóváhagyva! Átlépés a kutatási fázisba.');
                // Transition navigation to research lab
                if (window.AdvisorNavigation) {
                    window.AdvisorNavigation.navigate('research', { caseId: currentCaseId });
                }
            }
        } catch (err) {
            console.error('[AdvisorCriteriaV2] Error approving criteria:', err);
            alert('Hiba történt a jóváhagyás során: ' + err.message);
        }
    }

    return {
        loadCriteria,
        toggleDimension,
        onPairSliderChange,
        approveCriteria
    };
})();
