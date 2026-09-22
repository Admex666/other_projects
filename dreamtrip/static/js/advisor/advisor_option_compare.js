/**
 * Optivoya Advisor Workspace — Side-by-Side Relative Comparison & Advisor Overrides (Phase 6)
 * Renders the relative trade-off matrix and whitebox editing controls.
 */

(function () {
    'use strict';

    class AdvisorOptionCompareView {
        constructor() {
            this.activeCaseId = null;
            this.comparisonData = null;
            this.isLoading = false;
        }

        async render(container, caseId) {
            this.activeCaseId = caseId || window.AdvisorState?.state?.activeCaseId;
            if (!this.activeCaseId) {
                const firstCase = (window.AdvisorState?.state?.cases || [])[0];
                if (firstCase) this.activeCaseId = firstCase.id;
            }

            if (!this.activeCaseId) {
                container.innerHTML = `
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 60px 20px; text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 48px; color: var(--text-muted); margin-bottom: 12px;">compare_arrows</span>
                        <h3 style="margin: 0 0 8px 0; color: #fff; font-family: var(--font-display);">Nincs kiválasztott ügy</h3>
                        <p style="color: var(--text-secondary); max-width: 400px; margin: 0 auto 20px auto; font-size: 13px;">
                            Válassz ki egy aktív ügyet az opciók összehasonlításához.
                        </p>
                    </div>
                `;
                return;
            }

            this.isLoading = true;
            this.renderSkeleton(container);
            await this.loadComparison(this.activeCaseId);
            this.isLoading = false;
            this.renderContent(container);
        }

        renderSkeleton(container) {
            container.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h2 style="margin: 0 0 4px 0; font-size: 22px; font-weight: 700; color: #fff; font-family: var(--font-display);">
                        Egymás Melletti Összehasonlítás (Side-by-Side Matrix)
                    </h2>
                    <p style="margin: 0; font-size: 13px; color: var(--text-secondary);">Relatív trade-offok és összehasonlító mátrix számítása...</p>
                </div>
                <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 60px 20px; text-align: center;">
                    <span class="material-symbols-outlined" style="font-size: 40px; color: var(--secondary-container); animation: spin 1s linear infinite;">sync</span>
                    <h4 style="margin: 16px 0 6px 0; color: #fff; font-family: var(--font-display);">Mátrix Számítása...</h4>
                </div>
            `;
        }

        async loadComparison(caseId) {
            try {
                const res = await window.AdvisorAPI.request(`/cases/${caseId}/compare`);
                if (res && res.comparison) {
                    this.comparisonData = res.comparison;
                }
            } catch (err) {
                console.error('Failed to load comparison matrix:', err);
                this.comparisonData = null;
            }
        }

        renderContent(container) {
            if (!this.comparisonData || !this.comparisonData.options || this.comparisonData.options.length === 0) {
                container.innerHTML = `
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 60px 20px; text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 48px; color: var(--text-muted); margin-bottom: 12px;">view_column</span>
                        <h3 style="margin: 0 0 8px 0; color: #fff; font-family: var(--font-display);">Nincsenek generált opciók</h3>
                        <p style="color: var(--text-secondary); max-width: 400px; margin: 0 auto 20px auto; font-size: 13px;">
                            Kérlek előbb generálj 3 archetípust az Opciók fülön az összehasonlításhoz.
                        </p>
                        <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.navigate('options')">
                            Opciók Generálása →
                        </button>
                    </div>
                `;
                return;
            }

            const options = this.comparisonData.options;
            const dimensions = this.comparisonData.dimensions || [];
            const narratives = this.comparisonData.relative_tradeoffs || [];

            container.innerHTML = `
                <!-- Header -->
                <div style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 14px;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                            <button type="button" onclick="window.AdvisorNavigation.navigate('options', '${this.activeCaseId}')" class="btn btn-secondary" style="font-size: 11.5px; padding: 4px 8px;">
                                ← Vissza az Opciókhoz
                            </button>
                            <span style="font-size: 12px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono);">
                                Whitebox Döntési Mátrix
                            </span>
                        </div>
                        <h2 style="margin: 0; font-size: 22px; font-weight: 700; color: #fff; font-family: var(--font-display);">
                            Egymás Melletti Összehasonlítás (Relative Comparison)
                        </h2>
                        <p style="margin: 4px 0 0 0; font-size: 13px; color: var(--text-secondary);">
                            Közvetlen trade-off elemzés és manuális tanácsadói finomhangolás (Advisor Override).
                        </p>
                    </div>

                    <div style="display: flex; gap: 10px;">
                        <button type="button" class="btn btn-secondary" onclick="window.AdvisorOptionCompare.openReorderModal()">
                            <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">swap_vert</span>
                            Sorrend Módosítása
                        </button>
                        <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.navigate('proposals', '${this.activeCaseId}')">
                            <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">send</span>
                            Ajánlat Elkészítése →
                        </button>
                    </div>
                </div>

                <!-- Relative Narrative Cards (Pros & Cons) -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 24px;">
                    ${narratives.map(n => this.renderNarrativeCard(n)).join('')}
                </div>

                <!-- Side-by-Side Comparison Table -->
                <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; overflow: hidden;">
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                            <thead>
                                <tr style="background: var(--b2b-surface); border-bottom: 2px solid var(--b2b-border);">
                                    <th style="padding: 16px 20px; font-weight: 700; color: var(--text-muted); font-size: 11px; text-transform: uppercase; width: 220px; font-family: var(--font-mono);">
                                        Döntési Dimenzió
                                    </th>
                                    ${options.map(opt => `
                                        <th style="padding: 16px 20px; color: #fff; font-family: var(--font-display); font-size: 14px; min-width: 240px;">
                                            <div style="font-size: 10px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 2px;">
                                                ${opt.archetype ? opt.archetype.replace('_', ' ').toUpperCase() : 'OPTION'}
                                            </div>
                                            <div>${opt.title || opt.destination?.city || 'Opció'}</div>
                                        </th>
                                    `).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${dimensions.map(dim => this.renderDimensionRow(dim)).join('')}
                                <!-- Actions Row -->
                                <tr style="background: var(--b2b-surface); border-top: 1px solid var(--b2b-border);">
                                    <td style="padding: 16px 20px; font-weight: 700; color: var(--text-muted); font-size: 11px; text-transform: uppercase; font-family: var(--font-mono);">
                                        Advisor Műveletek
                                    </td>
                                    ${options.map(opt => `
                                        <td style="padding: 14px 20px;">
                                            <div style="display: flex; flex-direction: column; gap: 6px;">
                                                <button type="button" class="btn btn-secondary" onclick="window.AdvisorOptionCompare.openEditModal('${opt.id}')" style="font-size: 11.5px; padding: 6px 10px; text-align: center;">
                                                    <span class="material-symbols-outlined" style="font-size: 14px; vertical-align: middle;">edit</span>
                                                    Kézi Szerkesztés
                                                </button>
                                                <button type="button" class="btn btn-secondary" onclick="window.AdvisorFindBetter.open('${this.activeCaseId}', '${opt.id}')" style="font-size: 11.5px; padding: 6px 10px; text-align: center; color: var(--secondary-container);">
                                                    <span class="material-symbols-outlined" style="font-size: 14px; vertical-align: middle;">tune</span>
                                                    Find Better (Finomhangolás)
                                                </button>
                                            </div>
                                        </td>
                                    `).join('')}
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }

        renderNarrativeCard(n) {
            return `
                <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="font-size: 11px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; font-family: var(--font-mono);">
                            ${n.archetype ? n.archetype.replace('_', ' ').toUpperCase() : 'OPTION'}
                        </div>
                        <h4 style="margin: 0 0 12px 0; color: #fff; font-size: 15px; font-family: var(--font-display);">${n.title}</h4>

                        <!-- Pros -->
                        <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px;">
                            ${n.pros.map(p => `
                                <div style="display: flex; align-items: flex-start; gap: 6px; font-size: 12px; color: #4ade80;">
                                    <span class="material-symbols-outlined" style="font-size: 16px; margin-top: 1px;">check_circle</span>
                                    <span>${p}</span>
                                </div>
                            `).join('')}
                        </div>

                        <!-- Cons / Trade-offs -->
                        <div style="display: flex; flex-direction: column; gap: 6px;">
                            ${n.cons.map(c => `
                                <div style="display: flex; align-items: flex-start; gap: 6px; font-size: 12px; color: #fde047;">
                                    <span class="material-symbols-outlined" style="font-size: 16px; margin-top: 1px;">balance</span>
                                    <span>${c}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }

        renderDimensionRow(dim) {
            return `
                <tr style="border-bottom: 1px solid var(--b2b-border);">
                    <td style="padding: 14px 20px; font-weight: 600; color: var(--text-secondary); font-size: 12.5px;">
                        ${dim.label}
                    </td>
                    ${dim.values.map(val => `
                        <td style="padding: 14px 20px; ${val.is_best ? 'background: rgba(167, 245, 64, 0.03);' : ''}">
                            <div style="font-weight: 600; color: #fff; font-family: ${dim.id.includes('price') || dim.id === 'trip_score' ? 'var(--font-mono)' : 'inherit'};">
                                ${val.formatted}
                            </div>
                            ${val.delta_pct !== undefined && val.delta_pct !== 0 ? `
                                <div style="font-size: 11px; margin-top: 2px; font-family: var(--font-mono); color: ${val.delta_pct < 0 ? '#4ade80' : '#f87171'};">
                                    ${val.delta_pct > 0 ? '+' : ''}${val.delta_pct}% (${val.delta_from_base > 0 ? '+' : ''}${Number(val.delta_from_base).toLocaleString()} Ft)
                                </div>
                            ` : ''}
                        </td>
                    `).join('')}
                </tr>
            `;
        }

        openEditModal(optionId) {
            const opt = (this.comparisonData?.options || []).find(o => o.id === optionId);
            if (!opt) return;

            const newTitle = prompt('Opció címe:', opt.title || '');
            if (newTitle === null) return;

            const newPrice = prompt('Módosított teljes ár (Ft):', opt.total_price_huf || '');
            if (newPrice === null) return;

            const reason = prompt('Tanácsadói indoklás a módosításhoz (Whitebox audit):', 'Ügyfél kérésre átszámítva');
            if (reason === null) return;

            this.submitOptionUpdate(optionId, {
                title: newTitle,
                total_price_huf: parseFloat(newPrice) || opt.total_price_huf,
                override_reason: reason
            });
        }

        async submitOptionUpdate(optionId, payload) {
            try {
                await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/options/${optionId}`, {
                    method: 'PUT',
                    body: payload
                });
                await this.render(document.getElementById('advisorMainContent'), this.activeCaseId);
            } catch (err) {
                alert('Nem sikerült frissíteni az opciót: ' + err.message);
            }
        }

        openReorderModal() {
            alert('A sorrend átrendezése: Fogd meg és húzd az archetípusokat a kívánt sorrendbe, vagy használd az Opciók nézetet.');
        }
    }

    window.AdvisorOptionCompare = new AdvisorOptionCompareView();
})();
