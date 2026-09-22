/**
 * Optivoya Advisor Workspace — Constraint Relaxation & Diagnosis Modal (Phase 7)
 * Eliminates dead-ends with actionable, quantified constraint adjustments.
 */

(function () {
    'use strict';

    class AdvisorRelaxationModal {
        constructor() {
            this.activeCaseId = null;
            this.modalElement = null;
            this.diagnosisData = null;
        }

        init() {
            if (!document.getElementById('relaxationModal')) {
                const modalHtml = `
                    <div id="relaxationModal" class="modal-overlay">
                        <div class="modal-card" style="max-width: 650px;">
                            <div style="padding: 20px 24px; border-bottom: 1px solid var(--b2b-border); display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-size: 11px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono);">
                                        Zsákutca Megszüntetése (No Dead-Ends)
                                    </div>
                                    <h3 style="margin: 2px 0 0 0; color: #fff; font-size: 18px; font-family: var(--font-display);">Szűrési Feltételek Enyhítése</h3>
                                </div>
                                <button type="button" onclick="window.AdvisorRelaxation.close()" class="btn btn-secondary" style="padding: 4px 8px; font-size: 13px;">✕</button>
                            </div>

                            <div style="padding: 20px 24px; display: flex; flex-direction: column; gap: 16px;">
                                <div id="relaxationDiagnosisBox" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 10px; padding: 14px; display: flex; align-items: flex-start; gap: 10px;">
                                    <span class="material-symbols-outlined" style="color: #f87171; font-size: 20px; margin-top: 1px;">error</span>
                                    <div>
                                        <div style="font-weight: 700; color: #fff; font-size: 13px;" id="relaxationDiagnosisTitle">Szűrési Diagnózis</div>
                                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;" id="relaxationDiagnosisDesc">
                                            A jelenlegi szigorú megkötések mellett nem található megfelelő opció.
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <div style="font-size: 12px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 8px;">
                                        Javasolt 1-Kattintásos Enyhítési Útvonalak:
                                    </div>
                                    <div id="relaxationList" style="display: flex; flex-direction: column; gap: 10px; max-height: 320px; overflow-y: auto;">
                                        <!-- Dynamic Suggestions -->
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                document.body.insertAdjacentHTML('beforeend', modalHtml);
            }
            this.modalElement = document.getElementById('relaxationModal');
        }

        async open(caseId) {
            this.init();
            this.activeCaseId = caseId || window.AdvisorState?.state?.activeCaseId;
            if (this.modalElement) {
                this.modalElement.style.display = 'flex';
                await this.loadDiagnosis();
            }
        }

        close() {
            if (this.modalElement) {
                this.modalElement.style.display = 'none';
            }
        }

        async loadDiagnosis() {
            const listEl = document.getElementById('relaxationList');
            const descEl = document.getElementById('relaxationDiagnosisDesc');
            if (!listEl) return;

            listEl.innerHTML = `
                <div style="text-align: center; color: var(--secondary-container); padding: 30px;">
                    <span class="material-symbols-outlined" style="font-size: 32px; animation: spin 1s linear infinite;">sync</span>
                    <div style="margin-top: 8px; font-size: 13px; color: var(--text-secondary);">Feltételrendszer diagnosztizálása...</div>
                </div>
            `;

            try {
                const res = await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/diagnose-constraints`, { method: 'POST' });
                this.diagnosisData = res.diagnosis;

                if (descEl) descEl.textContent = this.diagnosisData.diagnosis;

                const suggestions = this.diagnosisData.suggested_relaxations || [];
                if (suggestions.length === 0) {
                    listEl.innerHTML = `
                        <div style="text-align: center; color: var(--text-secondary); padding: 30px; font-size: 13px;">
                            Nem található további automatikus enyhítési javaslat.
                        </div>
                    `;
                    return;
                }

                listEl.innerHTML = suggestions.map(sug => `
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 10px; padding: 14px; display: flex; justify-content: space-between; align-items: center; gap: 14px;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-weight: 700; color: #fff; font-size: 13.5px;">${sug.title}</span>
                                <span style="background: rgba(167, 245, 64, 0.15); color: var(--secondary-container); font-size: 10.5px; font-weight: 700; padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">
                                    +${sug.unlocked_count} ÚJ OPCIÓ
                                </span>
                            </div>
                            <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">${sug.description}</div>
                        </div>
                        <button type="button" class="btn btn-primary" onclick="window.AdvisorRelaxation.apply('${sug.id}')" style="font-size: 12px; padding: 6px 12px; white-space: nowrap;">
                            Feltétel Enyhítése →
                        </button>
                    </div>
                `).join('');

            } catch (err) {
                listEl.innerHTML = `
                    <div style="text-align: center; color: #f87171; padding: 30px; font-size: 13px;">
                        Hiba a diagnózis lekérésekor: ${err.message}
                    </div>
                `;
            }
        }

        async apply(relaxationId) {
            const sug = (this.diagnosisData?.suggested_relaxations || []).find(s => s.id === relaxationId);
            if (!sug) return;

            try {
                await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/apply-relaxation`, {
                    method: 'POST',
                    body: {
                        relaxation_id: relaxationId,
                        patch: sug.patch
                    }
                });

                alert(`Feltétel sikeresen enyhítve! ${sug.unlocked_count} új opció került a választékba.`);
                this.close();
                if (window.AdvisorOptions) {
                    window.AdvisorOptions.render(document.getElementById('advisorMainContent'), this.activeCaseId);
                }
            } catch (err) {
                alert('Enyhítés sikertelen: ' + err.message);
            }
        }
    }

    window.AdvisorRelaxation = new AdvisorRelaxationModal();
})();
