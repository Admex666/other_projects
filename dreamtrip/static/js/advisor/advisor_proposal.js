/**
 * Optivoya Advisor Workspace — Multi-Option Proposal Builder & Versioning (Phase 8)
 * Generates polished, customizable client proposals with 1-3 options and version tracking.
 */

(function () {
    'use strict';

    class AdvisorProposalManager {
        constructor() {
            this.activeCaseId = null;
            this.activeProposal = null;
            this.proposalsList = [];
            this.availableOptions = [];
            this.isLoading = false;
        }

        async render(container, caseId) {
            this.activeCaseId = caseId || window.AdvisorState?.state?.activeCaseId;
            if (!this.activeCaseId) {
                container.innerHTML = `
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 40px; text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 40px; color: var(--text-secondary); margin-bottom: 8px;">description</span>
                        <h3 style="margin: 0 0 8px 0; color: #fff;">Nincs Kiválasztott Utazási Ügy</h3>
                        <p style="color: var(--text-secondary); margin: 0 0 16px 0; font-size: 13px;">Válassz ki egy esetet a bal oldali sávból vagy a Vezérlőpultról.</p>
                        <button type="button" onclick="window.AdvisorNavigation.navigate('dashboard')" class="btn btn-primary">← Vissza a Dashboardra</button>
                    </div>
                `;
                return;
            }

            this.isLoading = true;
            this.renderSkeleton(container);
            await this.loadProposalData(this.activeCaseId);
            this.isLoading = false;
            this.renderContent(container);
        }

        renderSkeleton(container) {
            container.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h2 style="margin: 0 0 4px 0; font-size: 22px; font-weight: 700; color: #fff; font-family: var(--font-display);">
                        Multi-Option Ügyfélajánlat Szerkesztő
                    </h2>
                    <p style="margin: 0; font-size: 13px; color: var(--text-secondary);">Ajánlati dokumentum és verziók betöltése...</p>
                </div>
                <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 60px 20px; text-align: center;">
                    <span class="material-symbols-outlined" style="font-size: 40px; color: var(--secondary-container); animation: spin 1s linear infinite;">sync</span>
                    <h4 style="margin: 16px 0 6px 0; color: #fff; font-family: var(--font-display);">Ajánlat Betöltése...</h4>
                </div>
            `;
        }

        async loadProposalData(caseId) {
            try {
                // Fetch proposals list
                const propRes = await window.AdvisorAPI.request(`/cases/${caseId}/proposals`);
                this.proposalsList = propRes.proposals || [];

                // Fetch available options
                const optRes = await window.AdvisorAPI.request(`/cases/${caseId}/options`);
                this.availableOptions = optRes.options || [];

                if (this.proposalsList.length > 0) {
                    this.activeProposal = this.proposalsList[0];
                } else {
                    // Generate initial v1 proposal
                    const createRes = await window.AdvisorAPI.request(`/cases/${caseId}/proposals`, {
                        method: 'POST',
                        body: {}
                    });
                    this.activeProposal = createRes.proposal;
                    this.proposalsList = [this.activeProposal];
                }
            } catch (err) {
                console.error('Error loading proposal data:', err);
            }
        }

        renderContent(container) {
            const activeCase = (window.AdvisorState?.state?.cases || []).find(c => c.id === this.activeCaseId) || {};
            const client = (window.AdvisorState?.state?.clients || []).find(cl => cl.id === activeCase.client_id) || {};
            const prop = this.activeProposal || {};
            const options = prop.options_snapshot || this.availableOptions || [];

            container.innerHTML = `
                <!-- Top Header & Actions -->
                <div style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 14px;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                            <button type="button" onclick="window.AdvisorNavigation.navigate('options', '${this.activeCaseId}')" class="btn btn-secondary" style="font-size: 11.5px; padding: 4px 8px;">
                                ← Vissza az Opciókhoz
                            </button>
                            <span style="font-size: 12px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono);">
                                ${client.name || 'Ügyfél'} • ${activeCase.title || 'Utazási Ügy'}
                            </span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <h2 style="margin: 0; font-size: 22px; font-weight: 700; color: #fff; font-family: var(--font-display);">
                                Ügyfélajánlat Szerkesztő
                            </h2>
                            <span style="background: rgba(167, 245, 64, 0.15); color: var(--secondary-container); font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; font-family: var(--font-mono);">
                                v${prop.version || 1} • ${prop.status || 'DRAFT'}
                            </span>
                        </div>
                    </div>

                    <div style="display: flex; gap: 10px; align-items: center;">
                        <!-- Version Selector -->
                        ${this.proposalsList.length > 1 ? `
                            <select onchange="window.AdvisorProposal.switchVersion(this.value)" style="background: var(--b2b-card); color: #fff; border: 1px solid var(--b2b-border); border-radius: 8px; padding: 6px 10px; font-size: 12px; font-family: var(--font-mono);">
                                ${this.proposalsList.map(p => `
                                    <option value="${p.id}" ${p.id === prop.id ? 'selected' : ''}>Verzió: v${p.version}</option>
                                `).join('')}
                            </select>
                        ` : ''}

                        <button type="button" class="btn btn-secondary" onclick="window.AdvisorProposal.createNewVersion()">
                            <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">fork_right</span>
                            Új Verzió (v${(prop.version || 1) + 1})
                        </button>

                        <button type="button" class="btn btn-primary" onclick="window.AdvisorProposal.previewAndPrint('${prop.id}')">
                            <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">print</span>
                            Nyomtatás / PDF Előnézet ↗
                        </button>
                    </div>
                </div>

                <!-- Main Proposal Grid -->
                <div style="display: grid; grid-template-columns: 1fr 340px; gap: 24px; align-items: start;">
                    
                    <!-- Left Column: Proposal Editor -->
                    <div style="display: flex; flex-direction: column; gap: 20px;">
                        
                        <!-- Title & Client Intro Card -->
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 20px;">
                            <div style="font-size: 12px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 12px;">
                                Ügyfél Előlap & Személyes Bevezető
                            </div>
                            <div style="margin-bottom: 14px;">
                                <label style="display: block; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">Ajánlat Címe</label>
                                <input type="text" id="propTitleInput" value="${prop.title || ''}" style="width: 100%; background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; color: #fff; padding: 10px 12px; font-size: 14px; font-weight: 600; box-sizing: border-box;">
                            </div>
                            <div>
                                <label style="display: block; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">Személyes Bevezető Üzenet az Utazónak</label>
                                <textarea id="propIntroInput" rows="4" style="width: 100%; background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; color: #fff; padding: 10px 12px; font-size: 13px; line-height: 1.5; resize: vertical; box-sizing: border-box;">${prop.client_intro || ''}</textarea>
                            </div>
                        </div>

                        <!-- Included Options Selection -->
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 20px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                                <div style="font-size: 12px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono);">
                                    Ajánlatban Szereplő Opciók (${options.length} archetípus elérhető)
                                </div>
                                <div style="font-size: 11.5px; color: var(--text-secondary);">Jelöld be a kiküldeni kívánt opciókat</div>
                            </div>

                            <div style="display: flex; flex-direction: column; gap: 12px;">
                                ${options.map(opt => {
                                    const isSelected = !prop.selected_option_ids || prop.selected_option_ids.includes(opt.id);
                                    return `
                                        <div style="background: var(--b2b-surface); border: 1px solid ${isSelected ? 'var(--b2b-border)' : 'rgba(255,255,255,0.04)'}; border-radius: 10px; padding: 14px; display: flex; align-items: center; gap: 14px; opacity: ${isSelected ? '1' : '0.5'};">
                                            <input type="checkbox" id="chk_opt_${opt.id}" class="prop-opt-chk" data-optid="${opt.id}" ${isSelected ? 'checked' : ''} onchange="window.AdvisorProposal.toggleOptionSelection()" style="width: 18px; height: 18px; accent-color: var(--secondary-container); cursor: pointer;">
                                            <div style="flex: 1;">
                                                <div style="display: flex; align-items: center; gap: 8px;">
                                                    <span style="background: rgba(167, 245, 64, 0.2); color: var(--secondary-container); font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono); text-transform: uppercase;">
                                                        ${opt.archetype}
                                                    </span>
                                                    <span style="font-weight: 700; color: #fff; font-size: 14px;">${opt.title}</span>
                                                </div>
                                                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
                                                    ${opt.flight?.airline || 'Járat'} • ${opt.stay?.name || 'Hotel'} (${opt.stay?.stars || 4}★) • ${opt.destination?.city || ''}
                                                </div>
                                            </div>
                                            <div style="text-align: right;">
                                                <div style="font-weight: 700; color: var(--secondary-container); font-size: 15px; font-family: var(--font-mono);">
                                                    ${Math.round(opt.total_price_huf).toLocaleString('hu-HU')} Ft
                                                </div>
                                                <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">
                                                    ${Math.round(opt.price_per_person_huf || (opt.total_price_huf / 2)).toLocaleString('hu-HU')} Ft / fő
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>

                        <!-- Advisor Recommendation & Conclusion -->
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 20px;">
                            <div style="font-size: 12px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 12px;">
                                Szakértői Konklúzió & Tanácsadói Javaslat
                            </div>
                            <textarea id="propRecInput" rows="3" style="width: 100%; background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; color: #fff; padding: 10px 12px; font-size: 13px; line-height: 1.5; resize: vertical; box-sizing: border-box;">${prop.recommendation_summary || ''}</textarea>
                        </div>

                        <!-- Save Actions -->
                        <div style="display: flex; justify-content: flex-end; gap: 12px;">
                            <button type="button" class="btn btn-secondary" onclick="window.AdvisorProposal.saveDraft(false)">
                                Vázlat Mentése
                            </button>
                            <button type="button" class="btn btn-primary" onclick="window.AdvisorProposal.saveDraft(true)">
                                Mentés & Előnézet Megnyitása →
                            </button>
                        </div>
                    </div>

                    <!-- Right Column: Internal Advisor Notes & Metadata -->
                    <div style="display: flex; flex-direction: column; gap: 16px;">
                        
                        <!-- Internal Notes (Hidden from client) -->
                        <div style="background: var(--b2b-card); border: 1px solid rgba(234, 179, 8, 0.3); border-radius: 12px; padding: 18px;">
                            <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
                                <span class="material-symbols-outlined" style="color: #eab308; font-size: 18px;">lock</span>
                                <span style="font-size: 12px; font-weight: 700; color: #eab308; text-transform: uppercase; font-family: var(--font-mono);">
                                    Belső Tanácsadói Jegyzetek
                                </span>
                            </div>
                            <p style="margin: 0 0 10px 0; font-size: 11.5px; color: var(--text-secondary);">
                                Ez a szöveg szigorúan belső használatú, az ügyféldokumentumban és a nyomtatási képen <strong>nem jelenik meg</strong>.
                            </p>
                            <textarea id="propNotesInput" rows="6" placeholder="Belső megjegyzések, marzs kalkulációk, ügyfél reakciók..." style="width: 100%; background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; color: #fff; padding: 10px 12px; font-size: 12.5px; line-height: 1.4; resize: vertical; box-sizing: border-box;">${prop.advisor_notes || ''}</textarea>
                        </div>

                        <!-- Proposal Metadata Summary -->
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px;">
                            <div style="font-size: 12px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 12px;">
                                Ajánlat Metaadatok
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 8px; font-size: 12px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: var(--text-secondary);">Azonosító:</span>
                                    <span style="font-family: var(--font-mono); color: #fff;">${prop.id}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: var(--text-secondary);">Ügyfél:</span>
                                    <span style="font-weight: 600; color: #fff;">${client.name || '-'}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: var(--text-secondary);">Létrehozva:</span>
                                    <span style="color: #fff;">${prop.created_at ? prop.created_at.substring(0, 10) : 'Ma'}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: var(--text-secondary);">Utolsó módosítás:</span>
                                    <span style="color: #fff;">${prop.updated_at ? prop.updated_at.substring(0, 10) : 'Ma'}</span>
                                </div>
                            </div>
                        </div>

                    </div>

                </div>
            `;
        }

        async saveDraft(openPreview = false) {
            if (!this.activeProposal) return;

            const title = document.getElementById('propTitleInput')?.value;
            const client_intro = document.getElementById('propIntroInput')?.value;
            const recommendation_summary = document.getElementById('propRecInput')?.value;
            const advisor_notes = document.getElementById('propNotesInput')?.value;

            // Gather selected option IDs
            const checkboxes = document.querySelectorAll('.prop-opt-chk');
            const selected_option_ids = [];
            checkboxes.forEach(cb => {
                if (cb.checked && cb.dataset.optid) {
                    selected_option_ids.push(cb.dataset.optid);
                }
            });

            try {
                const res = await window.AdvisorAPI.request(`/proposals/${this.activeProposal.id}`, {
                    method: 'PUT',
                    body: {
                        title,
                        client_intro,
                        recommendation_summary,
                        advisor_notes,
                        selected_option_ids
                    }
                });

                this.activeProposal = res.proposal;
                alert('Ajánlat sikeresen elmentve!');

                if (openPreview) {
                    this.previewAndPrint(this.activeProposal.id);
                }
            } catch (err) {
                alert('Hiba a mentés során: ' + err.message);
            }
        }

        async createNewVersion() {
            if (!this.activeProposal) return;
            const reason = prompt('Add meg a verzióváltás okát (pl. "Ügyfél kérésre olcsóbb hotel opciók"):', '');
            if (reason === null) return;

            try {
                const res = await window.AdvisorAPI.request(`/proposals/${this.activeProposal.id}/new-version`, {
                    method: 'POST',
                    body: { reason }
                });

                this.activeProposal = res.proposal;
                this.proposalsList.unshift(this.activeProposal);
                this.renderContent(document.getElementById('advisorMainContent'));
                alert(`Új ajánlat verzió sikeresen létrehozva (v${this.activeProposal.version})!`);
            } catch (err) {
                alert('Verzió létrehozás sikertelen: ' + err.message);
            }
        }

        switchVersion(proposalId) {
            const found = this.proposalsList.find(p => p.id === proposalId);
            if (found) {
                this.activeProposal = found;
                this.renderContent(document.getElementById('advisorMainContent'));
            }
        }

        toggleOptionSelection() {
            // Live update visual opacity of unselected cards
            const checkboxes = document.querySelectorAll('.prop-opt-chk');
            checkboxes.forEach(cb => {
                const card = cb.closest('div[style*="border-radius: 10px"]');
                if (card) {
                    card.style.opacity = cb.checked ? '1' : '0.5';
                }
            });
        }

        previewAndPrint(proposalId) {
            window.open(`/api/advisor/proposals/${proposalId}/preview`, '_blank');
        }
    }

    window.AdvisorProposal = new AdvisorProposalManager();
})();
