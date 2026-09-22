/**
 * Optivoya Advisor Workspace — "Find Better" Component Tuning Modal (Phase 6)
 * Enables advisors to replace a flight or stay with better alternatives from the pool.
 */

(function () {
    'use strict';

    class AdvisorFindBetterModal {
        constructor() {
            this.activeCaseId = null;
            this.activeOptionId = null;
            this.modalElement = null;
        }

        init() {
            // Check if modal already exists
            if (!document.getElementById('findBetterModal')) {
                const modalHtml = `
                    <div id="findBetterModal" class="modal-overlay">
                        <div class="modal-card" style="max-width: 680px;">
                            <div style="padding: 20px 24px; border-bottom: 1px solid var(--b2b-border); display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-size: 11px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono);">
                                        Célzott Komponens Finomhangolás
                                    </div>
                                    <h3 style="margin: 2px 0 0 0; color: #fff; font-size: 18px; font-family: var(--font-display);">Find Better Alternatívák</h3>
                                </div>
                                <button type="button" onclick="window.AdvisorFindBetter.close()" class="btn btn-secondary" style="padding: 4px 8px; font-size: 13px;">✕</button>
                            </div>

                            <div style="padding: 20px 24px; display: flex; flex-direction: column; gap: 16px;">
                                <div style="display: flex; gap: 10px;">
                                    <button type="button" id="findBetterFlightBtn" class="btn btn-secondary" style="flex: 1;" onclick="window.AdvisorFindBetter.search('flight')">
                                        <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">flight</span>
                                        Kényelmesebb Járat
                                    </button>
                                    <button type="button" id="findBetterStayBtn" class="btn btn-secondary" style="flex: 1;" onclick="window.AdvisorFindBetter.search('stay')">
                                        <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">hotel</span>
                                        Jobb Szállás (4-5★)
                                    </button>
                                    <button type="button" id="findBetterPriceBtn" class="btn btn-secondary" style="flex: 1;" onclick="window.AdvisorFindBetter.search('price')">
                                        <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">trending_down</span>
                                        Alacsonyabb Ár
                                    </button>
                                </div>

                                <div id="findBetterResults" style="min-height: 200px; max-height: 360px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px;">
                                    <div style="text-align: center; color: var(--text-secondary); padding: 40px 10px; font-size: 13px;">
                                        Válassz egy komponenst a fenti gombok közül a jobb alternatívák betöltéséhez.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                document.body.insertAdjacentHTML('beforeend', modalHtml);
            }
            this.modalElement = document.getElementById('findBetterModal');
        }

        open(caseId, optionId) {
            this.init();
            this.activeCaseId = caseId;
            this.activeOptionId = optionId;
            if (this.modalElement) {
                this.modalElement.style.display = 'flex';
                this.search('stay'); // Default search stays
            }
        }

        close() {
            if (this.modalElement) {
                this.modalElement.style.display = 'none';
            }
        }

        async search(targetComponent) {
            const resultsContainer = document.getElementById('findBetterResults');
            if (!resultsContainer) return;

            resultsContainer.innerHTML = `
                <div style="text-align: center; color: var(--secondary-container); padding: 40px 10px;">
                    <span class="material-symbols-outlined" style="font-size: 32px; animation: spin 1s linear infinite;">sync</span>
                    <div style="margin-top: 8px; font-size: 13px; color: var(--text-secondary);">Alternatívák keresése...</div>
                </div>
            `;

            try {
                const res = await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/find-better`, {
                    method: 'POST',
                    body: {
                        option_id: this.activeOptionId,
                        target_component: targetComponent,
                        goal: targetComponent === 'flight' ? 'direct_flight' : (targetComponent === 'stay' ? 'higher_stars' : 'lower_price')
                    }
                });

                const candidates = res.better_candidates || [];
                if (candidates.length === 0) {
                    resultsContainer.innerHTML = `
                        <div style="text-align: center; color: var(--text-secondary); padding: 40px 10px; font-size: 13px;">
                            Nem található közvetlen alternatíva a jelenlegi kutatási poolban.
                        </div>
                    `;
                    return;
                }

                resultsContainer.innerHTML = candidates.map(cand => {
                    const stay = cand.stay || {};
                    const flight = cand.flight || {};
                    return `
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 10px; padding: 14px; display: flex; justify-content: space-between; align-items: center; gap: 12px;">
                            <div>
                                <div style="font-weight: 700; color: #fff; font-size: 13.5px;">${stay.name || flight.airline || cand.title}</div>
                                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
                                    ${stay.stars ? '★'.repeat(stay.stars) + ' • ' + (stay.rating_normalized || 8.8) + '/10' : ''}
                                    ${flight.airline ? flight.airline + ' • ' + (flight.stops === 0 ? 'Közvetlen' : flight.stops + ' átszállás') : ''}
                                </div>
                                <div style="font-size: 13px; font-weight: 700; color: var(--secondary-container); margin-top: 4px; font-family: var(--font-mono);">
                                    ${Number(cand.total_price_huf || 0).toLocaleString()} Ft teljes ár
                                </div>
                            </div>
                            <button type="button" class="btn btn-primary" onclick="window.AdvisorFindBetter.swapIntoOption('${cand.id}', '${targetComponent}')" style="font-size: 12px; padding: 6px 12px;">
                                Cserélje Le Erre →
                            </button>
                        </div>
                    `;
                }).join('');

            } catch (err) {
                resultsContainer.innerHTML = `
                    <div style="text-align: center; color: #f87171; padding: 30px 10px; font-size: 13px;">
                        Hiba történt a keresés során: ${err.message}
                    </div>
                `;
            }
        }

        async swapIntoOption(candidateId, componentType) {
            try {
                await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/options/${this.activeOptionId}/swap-component`, {
                    method: 'POST',
                    body: {
                        component_type: componentType,
                        new_component_id: candidateId,
                        override_reason: `Tanácsadó által kiválasztott jobb alternatíva (${componentType})`
                    }
                });
                alert('Elem sikeresen kicserélve!');
                this.close();
                if (window.AdvisorOptionCompare) {
                    window.AdvisorOptionCompare.render(document.getElementById('advisorMainContent'), this.activeCaseId);
                }
            } catch (err) {
                alert('Csere sikertelen: ' + err.message);
            }
        }
    }

    window.AdvisorFindBetter = new AdvisorFindBetterModal();
})();
