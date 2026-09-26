/**
 * Optivoya Advisor Workspace v2 — Research Intent & Intent Confirmation Layer
 * =============================================================================
 * Handles automatic research intent reconstruction, human confirmation,
 * dynamic research plan preview, and component-level intent actions (KEEP/REPLACE/IMPROVE).
 */

window.AdvisorIntentV2 = (() => {
    let currentCaseId = null;
    let currentIntentData = null;

    /**
     * Loads the intent plan and research state for the active Case.
     */
    async function loadIntentPlan(caseId) {
        currentCaseId = caseId;
        const container = document.getElementById('intentConfirmationContainer');
        if (!container) return;

        container.innerHTML = `
            <div style="padding: 24px; text-align: center; color: var(--text-muted);">
                <div class="spinner" style="margin: 0 auto 12px;"></div>
                <div style="font-size: 13px;">Kutatási cél rekonstruálása és kutatási terv összeállítása...</div>
            </div>
        `;

        try {
            const [planRes, stateRes] = await Promise.all([
                window.AdvisorAPI.fetchWithAuth(`/api/advisor/cases/${caseId}/intent/plan`),
                window.AdvisorAPI.fetchWithAuth(`/api/advisor/cases/${caseId}/research-state`)
            ]);

            if (!planRes.ok || !stateRes.ok) {
                container.innerHTML = `
                    <div style="padding: 16px; color: #ff6b6b; font-size: 13px;">
                        Nem sikerült betölteni a kutatási célt. Kérjük, próbálja újra.
                    </div>
                `;
                return;
            }

            const planData = await planRes.json();
            const stateData = await stateRes.json();
            currentIntentData = { ...planData, ...stateData };

            renderIntentConfirmationCard(currentIntentData);
        } catch (err) {
            console.error('[AdvisorIntentV2] Load intent plan error:', err);
            container.innerHTML = `
                <div style="padding: 16px; color: #ff6b6b; font-size: 13px;">
                    Hiba történt a szándék elemzésekor: ${err.message}
                </div>
            `;
        }
    }

    /**
     * Renders the Intent Confirmation Card & Dynamic Research Plan.
     */
    function renderIntentConfirmationCard(data) {
        const container = document.getElementById('intentConfirmationContainer');
        if (!container) return;

        const isConfirmed = data.intent_confirmed || (data.research_state && data.research_state.intent_confirmed);
        const plan = data.research_plan || {};
        const steps = plan.steps || [];
        const matrix = data.missing_info_matrix || [];

        const intentBadgeColor = {
            'DESTINATION_DISCOVERY': '#38bdf8',
            'FLIGHT_FIRST': '#a7f540',
            'STAY_FIRST': '#fbbf24',
            'RE_OPTIMIZATION': '#c084fc',
            'FIND_BETTER_COMPONENT': '#f43f5e',
            'MIXED_SCOPE_COMPETITION': '#fb923c'
        }[data.resolved_intent] || '#a7f540';

        const intentTitle = {
            'DESTINATION_DISCOVERY': '🌍 Desztináció Felfedezés & Inspiráció',
            'FLIGHT_FIRST': '✈️ Járat-Központú Teljes Utazástervezés',
            'STAY_FIRST': '🏨 Szállás- és Élményfókusz (Rögzített Járat)',
            'RE_OPTIMIZATION': '⚡ Napi Útiterv & Logisztikai Re-optimalizálás',
            'FIND_BETTER_COMPONENT': '🔄 Komponens-csere / Jobb Alternatíva Keresés',
            'MIXED_SCOPE_COMPETITION': '⚖️ Célállomások Párhuzamos Versenyeztetése'
        }[data.resolved_intent] || data.resolved_intent;

        container.innerHTML = `
            <div class="intent-card" style="background: var(--b2b-card); border: 1px solid ${isConfirmed ? 'rgba(167, 245, 64, 0.3)' : 'rgba(255, 255, 255, 0.1)'}; border-radius: 14px; padding: 24px; margin-bottom: 24px; box-shadow: 0 8px 24px rgba(0,0,0,0.3);">
                
                <!-- Intent Header Banner -->
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 18px; border-bottom: 1px solid var(--b2b-border); padding-bottom: 16px;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                            <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; background: ${intentBadgeColor}22; color: ${intentBadgeColor}; border: 1px solid ${intentBadgeColor}44; padding: 3px 8px; border-radius: 6px;">
                                Rekonstruált Kutatási Cél
                            </span>
                            <span style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">
                                Becsült futásidő: ~${plan.total_estimated_sec || 5.0}s
                            </span>
                        </div>
                        <h3 style="margin: 0 0 6px 0; font-size: 18px; font-family: var(--font-display); color: #fff; display: flex; align-items: center; gap: 8px;">
                            ${intentTitle}
                        </h3>
                        <p style="margin: 0; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
                            „${data.intent_summary || 'A rendszer összeállította a kutatási stratégiát az ügyfél profilja és a megadott adatok alapján.'}”
                        </p>
                    </div>

                    <div style="display: flex; gap: 10px; flex-shrink: 0;">
                        ${!isConfirmed ? `
                            <button onclick="window.AdvisorIntentV2.confirmIntent(true)" class="btn btn-primary" style="padding: 10px 20px; font-weight: 700; font-size: 13px; display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 14px rgba(167, 245, 64, 0.3);">
                                <span class="material-symbols-outlined" style="font-size: 18px;">check_circle</span>
                                Igen, indulhat a kutatás →
                            </button>
                            <button onclick="window.AdvisorIntentV2.openModifyDrawer()" class="btn btn-secondary" style="padding: 10px 14px; font-size: 13px; display: flex; align-items: center; gap: 6px;">
                                <span class="material-symbols-outlined" style="font-size: 18px;">tune</span>
                                Feltételek módosítása
                            </button>
                        ` : `
                            <div style="display: flex; align-items: center; gap: 8px; background: rgba(167, 245, 64, 0.12); color: var(--secondary-container); padding: 8px 16px; border-radius: 8px; border: 1px solid rgba(167, 245, 64, 0.3); font-weight: 600; font-size: 13px;">
                                <span class="material-symbols-outlined" style="font-size: 18px;">verified</span>
                                Cél visszaigazolva (Phase 2: DEFINE aktív)
                            </div>
                        `}
                    </div>
                </div>

                <!-- Missing Info & Fixed Components Summary -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <!-- Mi van / Mi nincs Mátrix -->
                    <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 10px; padding: 16px;">
                        <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 12px; display: flex; justify-content: space-between;">
                            <span>📊 „Mi van / Mi nincs?” Állapotmátrix</span>
                            <span style="color: var(--secondary-container);">${matrix.filter(m => m.has_value).length}/${matrix.length} kitöltve</span>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            ${matrix.map(item => `
                                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; padding: 6px 10px; background: rgba(255,255,255,0.02); border-radius: 6px; border-left: 3px solid ${item.has_value ? '#a7f540' : (item.urgency === 'required' ? '#ff6b6b' : '#fbbf24')};">
                                    <div>
                                        <span style="font-weight: 600; color: #fff;">${item.label}:</span>
                                        <span style="color: var(--text-secondary); margin-left: 6px;">${item.current_value_repr}</span>
                                    </div>
                                    <span style="font-size: 11px; color: var(--text-muted); font-style: italic;">${item.system_action}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Dinamikus Kutatási Terv (Lépéssorrend) -->
                    <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 10px; padding: 16px;">
                        <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 12px; display: flex; justify-content: space-between;">
                            <span>⚡ Dinamikus Kutatási Pipeline</span>
                            <span>${steps.length} lépés tervezve</span>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            ${steps.map((step, idx) => `
                                <div style="display: flex; align-items: center; gap: 10px; font-size: 12px; padding: 6px 10px; background: rgba(255,255,255,0.02); border-radius: 6px;">
                                    <span style="width: 20px; height: 20px; border-radius: 50%; background: rgba(167, 245, 64, 0.15); color: var(--secondary-container); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 10px; font-family: var(--font-mono);">
                                        ${idx + 1}
                                    </span>
                                    <div style="flex: 1;">
                                        <div style="font-weight: 600; color: #fff;">${step.label}</div>
                                        <div style="font-size: 11px; color: var(--text-muted);">${step.details || ''} • <strong style="color: var(--secondary-container);">${step.provider}</strong></div>
                                    </div>
                                    <span style="font-size: 10px; font-family: var(--font-mono); color: var(--text-muted);">${step.estimated_duration_sec}s</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

            </div>
        `;
    }

    /**
     * Confirms the intent and transitions to DEFINE phase.
     */
    async function confirmIntent(confirmed = true) {
        if (!currentCaseId) return;

        try {
            const res = await window.AdvisorAPI.fetchWithAuth(`/api/advisor/cases/${currentCaseId}/intent/confirm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ confirmed })
            });

            if (!res.ok) throw new Error('Nem sikerült a szándék visszaigazolása.');
            const data = await res.json();

            // Re-render UI and advance phase
            await loadIntentPlan(currentCaseId);
            if (window.AdvisorNavigation && window.AdvisorNavigation.switchTab) {
                // Advance to define / criteria phase
                window.AdvisorNavigation.switchTab('criteria');
            }
        } catch (err) {
            alert(`Hiba a szándék jóváhagyásakor: ${err.message}`);
        }
    }

    /**
     * Updates an existing component's action (KEEP, REPLACE, IMPROVE).
     */
    async function updateComponentAction(componentType, action, componentId, title) {
        if (!currentCaseId) return;

        try {
            const res = await window.AdvisorAPI.fetchWithAuth(`/api/advisor/cases/${currentCaseId}/components/intent`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    component_type: componentType,
                    action: action,
                    component_id: componentId,
                    title: title
                })
            });

            if (!res.ok) throw new Error('Komponens módosítása sikertelen.');
            await loadIntentPlan(currentCaseId);
        } catch (err) {
            console.error('[AdvisorIntentV2] Component update error:', err);
        }
    }

    function openModifyDrawer() {
        if (window.AdvisorNavigation && window.AdvisorNavigation.switchTab) {
            window.AdvisorNavigation.switchTab('brief');
        }
    }

    return {
        loadIntentPlan,
        confirmIntent,
        updateComponentAction,
        openModifyDrawer
    };
})();
