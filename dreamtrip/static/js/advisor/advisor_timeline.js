/**
 * Optivoya Advisor Workspace — Case Timeline, Audit Log & Re-Optimization (Phase 9)
 * Logs lifecycle events, captures client feedback, and triggers 1-click re-optimization.
 */

(function () {
    'use strict';

    const EVENT_ICON_MAP = {
        'CASE_CREATED': { icon: 'folder_open', color: 'var(--secondary-container)', bg: 'rgba(167, 245, 64, 0.15)' },
        'BRIEF_RECORDED': { icon: 'edit_note', color: '#60a5fa', bg: 'rgba(96, 165, 250, 0.15)' },
        'RESEARCH_EXECUTED': { icon: 'travel_explore', color: '#c084fc', bg: 'rgba(192, 132, 252, 0.15)' },
        'OPTIONS_GENERATED': { icon: 'view_carousel', color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.15)' },
        'PROPOSAL_CREATED': { icon: 'description', color: '#a7f540', bg: 'rgba(167, 245, 64, 0.2)' },
        'CLIENT_FEEDBACK': { icon: 'rate_review', color: '#fbbf24', bg: 'rgba(251, 191, 36, 0.15)' },
        'REOPTIMIZATION_EXECUTED': { icon: 'autorenew', color: '#34d399', bg: 'rgba(52, 211, 153, 0.15)' },
        'MANUAL_NOTE': { icon: 'sticky_note_2', color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.15)' },
        'CASE_CLOSED': { icon: 'check_circle', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' }
    };

    class AdvisorTimelineManager {
        constructor() {
            this.activeCaseId = null;
            this.timelineEvents = [];
            this.proposalsList = [];
            this.isLoading = false;
        }

        async render(container, caseId) {
            this.activeCaseId = caseId || window.AdvisorState?.state?.activeCaseId;
            if (!this.activeCaseId) {
                container.innerHTML = `
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 40px; text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 40px; color: var(--text-secondary); margin-bottom: 8px;">timeline</span>
                        <h3 style="margin: 0 0 8px 0; color: #fff;">Nincs Kiválasztott Utazási Ügy</h3>
                        <p style="color: var(--text-secondary); margin: 0 0 16px 0; font-size: 13px;">Válassz ki egy esetet a bal oldali sávból az idővonal megtekintéséhez.</p>
                        <button type="button" onclick="window.AdvisorNavigation.navigate('dashboard')" class="btn btn-primary">← Vissza a Dashboardra</button>
                    </div>
                `;
                return;
            }

            this.isLoading = true;
            this.renderSkeleton(container);
            await this.loadTimelineData(this.activeCaseId);
            this.isLoading = false;
            this.renderContent(container);
        }

        renderSkeleton(container) {
            container.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h2 style="margin: 0 0 4px 0; font-size: 22px; font-weight: 700; color: #fff; font-family: var(--font-display);">
                        Eset Idővonal & Visszajelzés Kezelő
                    </h2>
                    <p style="margin: 0; font-size: 13px; color: var(--text-secondary);">Audit napló és események betöltése...</p>
                </div>
                <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 60px 20px; text-align: center;">
                    <span class="material-symbols-outlined" style="font-size: 40px; color: var(--secondary-container); animation: spin 1s linear infinite;">sync</span>
                    <h4 style="margin: 16px 0 6px 0; color: #fff; font-family: var(--font-display);">Idővonal Betöltése...</h4>
                </div>
            `;
        }

        async loadTimelineData(caseId) {
            try {
                const res = await window.AdvisorAPI.request(`/cases/${caseId}/timeline`);
                this.timelineEvents = res.timeline || [];

                const propRes = await window.AdvisorAPI.request(`/cases/${caseId}/proposals`);
                this.proposalsList = propRes.proposals || [];
            } catch (err) {
                console.error('Error loading timeline:', err);
            }
        }

        renderContent(container) {
            const activeCase = (window.AdvisorState?.state?.cases || []).find(c => c.id === this.activeCaseId) || {};
            const client = (window.AdvisorState?.state?.clients || []).find(cl => cl.id === activeCase.client_id) || {};

            container.innerHTML = `
                <!-- Top Header & Actions -->
                <div style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 14px;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                            <button type="button" onclick="window.AdvisorNavigation.navigate('cases')" class="btn btn-secondary" style="font-size: 11.5px; padding: 4px 8px;">
                                ← Vissza az Ügyekhez
                            </button>
                            <span style="font-size: 12px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono);">
                                ${client.name || 'Ügyfél'} • ${activeCase.title || 'Utazási Ügy'}
                            </span>
                        </div>
                        <h2 style="margin: 0; font-size: 22px; font-weight: 700; color: #fff; font-family: var(--font-display);">
                            Eset Idővonal & Audit Napló
                        </h2>
                    </div>

                    <div style="display: flex; gap: 10px; align-items: center;">
                        <button type="button" class="btn btn-secondary" onclick="window.AdvisorTimeline.openFeedbackModal()">
                            <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">rate_review</span>
                            Ügyfél Visszajelzés Rögzítése
                        </button>
                        <button type="button" class="btn btn-primary" onclick="window.AdvisorTimeline.openReoptimizeModal()">
                            <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">autorenew</span>
                            1-Kattintásos Újratervezés (v2)
                        </button>
                    </div>
                </div>

                <!-- Grid Layout: Timeline Left + Action Panels Right -->
                <div style="display: grid; grid-template-columns: 1fr 340px; gap: 24px; align-items: start;">
                    
                    <!-- Left: Timeline Events Stream -->
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 24px;">
                        <div style="font-size: 13px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                            <span>Kronologikus Eseménynapló (${this.timelineEvents.length} bejegyzés)</span>
                            <span style="font-size: 11.5px; color: var(--text-secondary); text-transform: none;">Legfrissebb felül</span>
                        </div>

                        <div style="position: relative; padding-left: 28px;">
                            <!-- Vertical Timeline Line -->
                            <div style="position: absolute; left: 11px; top: 8px; bottom: 8px; width: 2px; background: rgba(255, 255, 255, 0.08);"></div>

                            <div style="display: flex; flex-direction: column; gap: 20px;">
                                ${this.timelineEvents.map(evt => {
                                    const conf = EVENT_ICON_MAP[evt.event_type] || EVENT_ICON_MAP['MANUAL_NOTE'];
                                    return `
                                        <div style="position: relative;">
                                            <!-- Event Dot / Icon -->
                                            <div style="position: absolute; left: -28px; top: 0; width: 24px; height: 24px; border-radius: 50%; background: ${conf.bg}; border: 1px solid ${conf.color}; display: flex; align-items: center; justify-content: center;">
                                                <span class="material-symbols-outlined" style="font-size: 14px; color: ${conf.color};">${conf.icon}</span>
                                            </div>

                                            <!-- Event Content Box -->
                                            <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 10px; padding: 14px 16px;">
                                                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
                                                    <div style="font-weight: 700; color: #fff; font-size: 13.5px;">${evt.title}</div>
                                                    <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">
                                                        ${evt.created_at ? evt.created_at.replace('T', ' ').substring(0, 16) : 'Most'}
                                                    </div>
                                                </div>
                                                <div style="font-size: 12.5px; color: var(--text-secondary); line-height: 1.5; white-space: pre-line;">
                                                    ${evt.description}
                                                </div>
                                                ${evt.metadata && Object.keys(evt.metadata).length > 0 ? `
                                                    <div style="margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap;">
                                                        ${Object.entries(evt.metadata).map(([k, v]) => `
                                                            <span style="font-size: 10.5px; background: rgba(255, 255, 255, 0.05); color: var(--text-muted); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">
                                                                ${k}: ${v}
                                                            </span>
                                                        `).join('')}
                                                    </div>
                                                ` : ''}
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    </div>

                    <!-- Right Column: Quick Note & Audit Summary -->
                    <div style="display: flex; flex-direction: column; gap: 20px;">
                        
                        <!-- Manual Note Box -->
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px;">
                            <div style="font-size: 12px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 10px;">
                                Jegyzet Hozzáadása a Naplóhoz
                            </div>
                            <input type="text" id="manualNoteTitle" placeholder="Jegyzet tárgya (pl. Telefonos egyeztetés)" style="width: 100%; background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; color: #fff; padding: 8px 10px; font-size: 12px; margin-bottom: 8px; box-sizing: border-box;">
                            <textarea id="manualNoteDesc" rows="3" placeholder="Részletek..." style="width: 100%; background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; color: #fff; padding: 8px 10px; font-size: 12px; resize: vertical; box-sizing: border-box; margin-bottom: 10px;"></textarea>
                            <button type="button" class="btn btn-secondary" onclick="window.AdvisorTimeline.saveManualNote()" style="width: 100%; justify-content: center; font-size: 12px;">
                                + Jegyzet Mentése az Idővonalra
                            </button>
                        </div>

                        <!-- Savings & Productivity Metrics -->
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px;">
                            <div style="font-size: 12px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 12px;">
                                Eset Termelékenység
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 10px; font-size: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="color: var(--text-secondary);">Kutatási Idő Megtakarítás:</span>
                                    <span style="font-weight: 700; color: var(--secondary-container); font-family: var(--font-mono);">~2.5 óra</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="color: var(--text-secondary);">Generált Verziók:</span>
                                    <span style="font-weight: 700; color: #fff; font-family: var(--font-mono);">${this.proposalsList.length} db</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="color: var(--text-secondary);">Események Száma:</span>
                                    <span style="font-weight: 700; color: #fff; font-family: var(--font-mono);">${this.timelineEvents.length}</span>
                                </div>
                            </div>
                        </div>

                    </div>

                </div>

                <!-- Feedback Modal -->
                <div id="feedbackModal" class="modal-overlay" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1000; align-items: center; justify-content: center;">
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 24px; width: 460px; max-width: 90%;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <h3 style="margin: 0; color: #fff; font-size: 16px; font-family: var(--font-display);">Ügyfél Visszajelzés Rögzítése</h3>
                            <button type="button" onclick="document.getElementById('feedbackModal').style.display='none'" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 18px;">✕</button>
                        </div>
                        
                        <div style="display: flex; flex-direction: column; gap: 12px;">
                            <div>
                                <label style="display: block; font-size: 11.5px; color: var(--text-secondary); margin-bottom: 4px;">Kategória</label>
                                <select id="fbCategorySelect" style="width: 100%; background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; color: #fff; padding: 8px 10px; font-size: 12px;">
                                    <option value="hotel_change">Szállás módosítás (pl. olcsóbb vagy közelebbi)</option>
                                    <option value="budget_limit">Költségkeret szűkítés / bővítés</option>
                                    <option value="flight_schedule">Járat menetrend preferencia</option>
                                    <option value="activities">Programok és élmények</option>
                                    <option value="general">Általános észrevétel</option>
                                </select>
                            </div>

                            <div>
                                <label style="display: block; font-size: 11.5px; color: var(--text-secondary); margin-bottom: 4px;">Hangulat / Értékelés</label>
                                <select id="fbSentimentSelect" style="width: 100%; background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; color: #fff; padding: 8px 10px; font-size: 12px;">
                                    <option value="POSITIVE">Pozitív (Tetszik az irány, finomhangolás)</option>
                                    <option value="NEUTRAL" selected>Semleges / Érdeklődő</option>
                                    <option value="CRITICAL">Kritikus (Jelentős változtatást kér)</option>
                                </select>
                            </div>

                            <div>
                                <label style="display: block; font-size: 11.5px; color: var(--text-secondary); margin-bottom: 4px;">Ügyfél Szöveges Visszajelzése</label>
                                <textarea id="fbTextInput" rows="4" placeholder="Pl. 'A szállás tetszik, de a járat túl korán indul reggel...'" style="width: 100%; background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; color: #fff; padding: 8px 10px; font-size: 12.5px; box-sizing: border-box;"></textarea>
                            </div>

                            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px;">
                                <button type="button" class="btn btn-secondary" onclick="document.getElementById('feedbackModal').style.display='none'">Mégse</button>
                                <button type="button" class="btn btn-primary" onclick="window.AdvisorTimeline.submitFeedback()">Visszajelzés Mentése</button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Reoptimize Modal -->
                <div id="reoptModal" class="modal-overlay" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1000; align-items: center; justify-content: center;">
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 24px; width: 480px; max-width: 90%;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <h3 style="margin: 0; color: #fff; font-size: 16px; font-family: var(--font-display);">1-Kattintásos Újratervezés (Re-Optimize)</h3>
                            <button type="button" onclick="document.getElementById('reoptModal').style.display='none'" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 18px;">✕</button>
                        </div>
                        
                        <div style="display: flex; flex-direction: column; gap: 12px;">
                            <p style="margin: 0; font-size: 12px; color: var(--text-secondary); line-height: 1.4;">
                                Az újratervezés frissíti a 3 döntési archetípust és automatikusan létrehozza a <strong>Proposal v${(this.proposalsList.length || 1) + 1}</strong>-et anélkül, hogy elölről kellene kezdened a folyamatot.
                            </p>

                            <div>
                                <label style="display: block; font-size: 11.5px; color: var(--text-secondary); margin-bottom: 4px;">Újratervezés Oka / Indoklás</label>
                                <input type="text" id="reoptReasonInput" value="Ügyféli visszajelzés alapján módosított preferenciák" style="width: 100%; background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; color: #fff; padding: 8px 10px; font-size: 12px; box-sizing: border-box;">
                            </div>

                            <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; padding: 12px;">
                                <div style="font-size: 11.5px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 8px;">
                                    Gyors Megkötés Módosítások
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                    <div>
                                        <label style="font-size: 11px; color: var(--text-secondary);">Új Keretösszeg (Ft)</label>
                                        <input type="number" id="reoptBudgetInput" value="${activeCase.total_budget_huf || 450000}" style="width: 100%; background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 6px; color: #fff; padding: 6px 8px; font-size: 12px; box-sizing: border-box;">
                                    </div>
                                    <div>
                                        <label style="font-size: 11px; color: var(--text-secondary);">Min. Hotel Csillag</label>
                                        <select id="reoptStarsInput" style="width: 100%; background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 6px; color: #fff; padding: 6px 8px; font-size: 12px;">
                                            <option value="3">3★+</option>
                                            <option value="4" selected>4★+</option>
                                            <option value="5">5★ Luxus</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px;">
                                <button type="button" class="btn btn-secondary" onclick="document.getElementById('reoptModal').style.display='none'">Mégse</button>
                                <button type="button" class="btn btn-primary" onclick="window.AdvisorTimeline.submitReoptimization()">Újratervezés Indítása 🚀</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        openFeedbackModal() {
            const modal = document.getElementById('feedbackModal');
            if (modal) modal.style.display = 'flex';
        }

        openReoptimizeModal() {
            const modal = document.getElementById('reoptModal');
            if (modal) modal.style.display = 'flex';
        }

        async saveManualNote() {
            const title = document.getElementById('manualNoteTitle')?.value;
            const description = document.getElementById('manualNoteDesc')?.value;
            if (!title || !description) {
                alert('Add meg a jegyzet címét és szövegét!');
                return;
            }

            try {
                await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/timeline`, {
                    method: 'POST',
                    body: { title, description, event_type: 'MANUAL_NOTE' }
                });
                await this.render(document.getElementById('advisorMainContent'), this.activeCaseId);
            } catch (err) {
                alert('Hiba a jegyzet mentésekor: ' + err.message);
            }
        }

        async submitFeedback() {
            const category = document.getElementById('fbCategorySelect')?.value;
            const sentiment = document.getElementById('fbSentimentSelect')?.value;
            const feedback_text = document.getElementById('fbTextInput')?.value;

            if (!feedback_text) {
                alert('Kérlek írd be a visszajelzés szövegét!');
                return;
            }

            const activeProp = this.proposalsList[0] || { id: 'prop_current' };

            try {
                await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/feedback`, {
                    method: 'POST',
                    body: {
                        proposal_id: activeProp.id,
                        feedback_category: category,
                        client_sentiment: sentiment,
                        feedback_text: feedback_text
                    }
                });

                document.getElementById('feedbackModal').style.display = 'none';
                alert('Visszajelzés sikeresen rögzítve az eseménynaplóban!');
                await this.render(document.getElementById('advisorMainContent'), this.activeCaseId);
            } catch (err) {
                alert('Hiba a visszajelzés mentésekor: ' + err.message);
            }
        }

        async submitReoptimization() {
            const reason = document.getElementById('reoptReasonInput')?.value;
            const newBudget = document.getElementById('reoptBudgetInput')?.value;
            const newStars = document.getElementById('reoptStarsInput')?.value;

            const activeProp = this.proposalsList[0] || { id: 'prop_current' };

            try {
                const res = await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/reoptimize`, {
                    method: 'POST',
                    body: {
                        proposal_id: activeProp.id,
                        reoptimization_reason: reason,
                        constraint_overrides: {
                            total_budget_huf: parseFloat(newBudget),
                            min_hotel_stars: parseInt(newStars, 10)
                        }
                    }
                });

                document.getElementById('reoptModal').style.display = 'none';
                alert(`Újratervezés sikeres! Új ajánlat verzió: v${res.version}`);
                window.AdvisorNavigation.navigate('proposals');
            } catch (err) {
                alert('Újratervezés sikertelen: ' + err.message);
            }
        }
    }

    window.AdvisorTimeline = new AdvisorTimelineManager();
})();
