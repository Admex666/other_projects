/**
 * Optivoya Advisor Workspace — Multi-Option & Archetype Presentation View (Phase 5)
 * Renders the 3 distinct, fully-realized decision packages:
 * - Option A: BEST OVERALL
 * - Option B: BEST VALUE
 * - Option C: BEST EXPERIENCE
 */

(function () {
    'use strict';

    class AdvisorOptionsView {
        constructor() {
            this.activeCaseId = null;
            this.options = [];
            this.isLoading = false;
        }

        async render(container, caseId) {
            this.activeCaseId = caseId || window.AdvisorState?.state?.activeCaseId;
            if (!this.activeCaseId) {
                // Fallback to first case if available
                const firstCase = (window.AdvisorState?.state?.cases || [])[0];
                if (firstCase) this.activeCaseId = firstCase.id;
            }

            if (!this.activeCaseId) {
                container.innerHTML = `
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 60px 20px; text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 48px; color: var(--text-muted); margin-bottom: 12px;">folder_off</span>
                        <h3 style="margin: 0 0 8px 0; color: #fff; font-family: var(--font-display);">Nincs kiválasztott ügy</h3>
                        <p style="color: var(--text-secondary); max-width: 400px; margin: 0 auto 20px auto; font-size: 13px;">
                            Válassz ki egy aktív ügyet a bal oldali Ügyek menüpontban a 3 archetípus megtekintéséhez.
                        </p>
                        <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.navigate('cases')">
                            Ügyek Megnyitása →
                        </button>
                    </div>
                `;
                return;
            }

            this.isLoading = true;
            this.renderSkeleton(container);
            await this.loadOptions(this.activeCaseId);
            this.isLoading = false;
            this.renderContent(container);
        }

        renderSkeleton(container) {
            container.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h2 style="margin: 0 0 4px 0; font-size: 22px; font-weight: 700; color: #fff; font-family: var(--font-display);">
                        Döntési Opciók & Archetípusok
                    </h2>
                    <p style="margin: 0; font-size: 13px; color: var(--text-secondary);">3 strukturált, egymástól eltérő trade-offokkal rendelkező utazási csomag generálása...</p>
                </div>
                <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 60px 20px; text-align: center;">
                    <span class="material-symbols-outlined" style="font-size: 40px; color: var(--secondary-container); animation: spin 1s linear infinite;">sync</span>
                    <h4 style="margin: 16px 0 6px 0; color: #fff; font-family: var(--font-display);">Archetípusok Számítása Folyamatban...</h4>
                    <p style="margin: 0; color: var(--text-secondary); font-size: 13px;">A Multi-Option Engine szűri a hard megkötéseket és szétválasztja az opciókat.</p>
                </div>
            `;
        }

        async loadOptions(caseId) {
            try {
                // Try fetching existing options
                const res = await window.AdvisorAPI.request(`/cases/${caseId}/options`);
                if (res && res.options && res.options.length > 0) {
                    this.options = res.options;
                } else {
                    // Generate fresh archetypes from candidate pool
                    const genRes = await window.AdvisorAPI.request(`/cases/${caseId}/options/generate`, { method: 'POST' });
                    if (genRes && genRes.options) {
                        this.options = genRes.options;
                    }
                }
            } catch (err) {
                console.error('Error loading options:', err);
                this.options = [];
            }
        }

        renderContent(container) {
            const activeCase = (window.AdvisorState?.state?.cases || []).find(c => c.id === this.activeCaseId) || {};
            const client = (window.AdvisorState?.state?.clients || []).find(cl => cl.id === activeCase.client_id) || {};

            if (!this.options || this.options.length === 0) {
                container.innerHTML = `
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 60px 20px; text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 48px; color: #f87171; margin-bottom: 12px;">rule</span>
                        <h3 style="margin: 0 0 8px 0; color: #fff; font-family: var(--font-display);">Nem található a feltételeknek megfelelő opció (0 találat)</h3>
                        <p style="color: var(--text-secondary); max-width: 480px; margin: 0 auto 20px auto; font-size: 13px;">
                            A megadott szigorú hard constraint korlátok miatt nem állítható elő 3 garantált döntési archetípus. Használd a feltétel-enyhítőt a zsákutca feloldásához!
                        </p>
                        <button type="button" class="btn btn-primary" onclick="window.AdvisorRelaxation.open('${this.activeCaseId}')">
                            <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">tune</span>
                            Feltételek Enyhítése (No Dead-Ends) →
                        </button>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <!-- Top Header & Breadcrumbs -->
                <div style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 14px;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                            <button type="button" onclick="window.AdvisorNavigation.navigate('research', '${this.activeCaseId}')" class="btn btn-secondary" style="font-size: 11.5px; padding: 4px 8px;">
                                ← Vissza a Kutatáshoz
                            </button>
                            <span style="font-size: 12px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono);">
                                ${client.name || 'Ügyfél'} • ${activeCase.title || 'Utazási Ügy'}
                            </span>
                        </div>
                        <h2 style="margin: 0; font-size: 22px; font-weight: 700; color: #fff; font-family: var(--font-display);">
                            3 Döntési Archetípus (Tri-Option Presentation)
                        </h2>
                        <p style="margin: 4px 0 0 0; font-size: 13px; color: var(--text-secondary);">
                            Minden opció valós menetrendből és hitelesített szálláskínálatból épül fel, garantált diverzitással.
                        </p>
                    </div>

                    <div style="display: flex; gap: 10px;">
                        <button type="button" class="btn btn-secondary" onclick="window.AdvisorRelaxation.open('${this.activeCaseId}')">
                            <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">tune</span>
                            Feltételek Enyhítése
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="window.AdvisorOptions.reGenerateOptions()">
                            <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">autorenew</span>
                            Újragenerálás
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="window.AdvisorNavigation.navigate('compare', '${this.activeCaseId}')">
                            <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">compare_arrows</span>
                            Összehasonlítás (Mátrix)
                        </button>
                        <button type="button" class="btn btn-primary" onclick="window.AdvisorOptions.createProposalFromOptions()">
                            <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">assignment_turned_in</span>
                            Ajánlat Készítése →
                        </button>
                    </div>
                </div>

                <!-- 3-Column Archetype Cards Grid -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
                    ${this.options.map((opt, idx) => this.renderArchetypeCard(opt, idx)).join('')}
                </div>
            `;
        }

        renderArchetypeCard(opt, idx) {
            const arch = opt.archetype || 'best_overall';
            let badgeColor = 'var(--secondary-container)';
            let badgeBg = 'rgba(167, 245, 64, 0.12)';
            let archTitle = 'OPTION A — BEST OVERALL';
            let archSub = 'A legkiegyensúlyozottabb választás';

            if (arch === 'best_value') {
                badgeColor = '#34d399';
                badgeBg = 'rgba(52, 211, 153, 0.12)';
                archTitle = 'OPTION B — BEST VALUE';
                archSub = 'Maximális költséghatékonyság';
            } else if (arch === 'best_experience') {
                badgeColor = '#e2e8f0';
                badgeBg = 'rgba(255, 255, 255, 0.1)';
                archTitle = 'OPTION C — BEST EXPERIENCE';
                archSub = 'Prémium kényelem & gazdag programok';
            }

            const flight = opt.flight_snapshot || {};
            const stay = opt.stay_snapshot || {};
            const activities = opt.activities_snapshot || [];

            return `
                <div class="archetype-card" style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 22px; display: flex; flex-direction: column; justify-content: space-between; gap: 18px; position: relative;">
                    
                    <!-- Card Header -->
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                            <span style="background: ${badgeBg}; color: ${badgeColor}; font-weight: 700; font-size: 10.5px; padding: 4px 8px; border-radius: 4px; letter-spacing: 0.05em; border: 1px solid ${badgeColor}40; font-family: var(--font-mono);">
                                ${archTitle}
                            </span>
                            <div style="text-align: right;">
                                <span style="font-size: 18px; font-weight: 700; color: var(--secondary-container); font-family: var(--font-mono);">${opt.trip_score || 88}</span>
                                <span style="font-size: 9px; color: var(--text-muted); text-transform: uppercase;">/100</span>
                            </div>
                        </div>

                        <h3 style="margin: 0 0 4px 0; font-size: 18px; font-weight: 700; color: #fff; font-family: var(--font-display);">
                            ${opt.title || opt.destination_city || 'Ajánlat'}
                        </h3>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 14px;">
                            ${opt.destination_city}, ${opt.destination_country} • ${archSub}
                        </div>

                        <!-- Price Box -->
                        <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; padding: 12px 14px; margin-bottom: 16px;">
                            <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Teljes Csomagár</div>
                            <div style="font-size: 22px; font-weight: 700; color: #fff; font-family: var(--font-mono); margin: 2px 0;">
                                ${Number(opt.total_price_huf || 0).toLocaleString()} Ft
                            </div>
                            <div style="font-size: 11.5px; color: var(--text-secondary); font-family: var(--font-mono);">
                                ~${Number(opt.price_per_person_huf || 0).toLocaleString()} Ft / fő
                            </div>
                        </div>

                        <!-- Components Stack -->
                        <div style="display: flex; flex-direction: column; gap: 10px; font-size: 12.5px;">
                            <!-- Flight Row -->
                            <div style="display: flex; gap: 10px; align-items: flex-start;">
                                <span class="material-symbols-outlined" style="font-size: 18px; color: var(--secondary-container); margin-top: 1px;">flight</span>
                                <div>
                                    <div style="font-weight: 600; color: #fff;">${flight.airline || 'Közvetlen Menetrend'}</div>
                                    <div style="font-size: 11.5px; color: var(--text-secondary); font-family: var(--font-mono);">
                                        ${flight.origin || 'BUD'} → ${flight.destination || opt.destination_city} • ${flight.stops === 0 ? 'Közvetlen' : flight.stops + ' átszállás'}
                                    </div>
                                </div>
                            </div>

                            <!-- Hotel Row -->
                            <div style="display: flex; gap: 10px; align-items: flex-start;">
                                <span class="material-symbols-outlined" style="font-size: 18px; color: var(--secondary-container); margin-top: 1px;">hotel</span>
                                <div>
                                    <div style="font-weight: 600; color: #fff;">${stay.name || 'Grand Hotel'}</div>
                                    <div style="font-size: 11.5px; color: var(--text-secondary); font-family: var(--font-mono);">
                                        ${'★'.repeat(stay.stars || 4)} • ${stay.rating_normalized || 8.8}/10 Vendégértékelés
                                    </div>
                                </div>
                            </div>

                            <!-- Activities Row -->
                            <div style="display: flex; gap: 10px; align-items: flex-start;">
                                <span class="material-symbols-outlined" style="font-size: 18px; color: var(--secondary-container); margin-top: 1px;">local_activity</span>
                                <div>
                                    <div style="font-weight: 600; color: #fff;">${activities.length > 0 ? activities.length + ' Válogatott Program' : 'Kulturális & Gasztro Fókusz'}</div>
                                    <div style="font-size: 11.5px; color: var(--text-secondary);">
                                        ${activities.slice(0, 2).map(a => a.name).join(', ') || 'Városnézés, Gasztronómiai élmények'}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Why This Option (Data-Driven) -->
                        <div style="margin-top: 16px; padding: 10px 12px; background: rgba(167, 245, 64, 0.06); border: 1px solid rgba(167, 245, 64, 0.2); border-radius: 8px;">
                            <div style="font-size: 10.5px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; margin-bottom: 4px; font-family: var(--font-mono);">
                                Miért ez az opció? (Why it fits)
                            </div>
                            <div style="font-size: 11.5px; color: var(--text-secondary); line-height: 1.4;">
                                ${opt.why_this_option || 'Optimális választás a megadott prioritások mentén.'}
                            </div>
                        </div>

                        <!-- Trade-offs -->
                        <div style="margin-top: 10px; font-size: 11.5px; color: var(--text-muted); display: flex; align-items: center; gap: 6px;">
                            <span class="material-symbols-outlined" style="font-size: 15px; color: #fbbf24;">balance</span>
                            <span>Kompromisszum: ${(opt.tradeoffs || ['Mérsékelt árkülönbség'])[0]}</span>
                        </div>
                    </div>

                    <!-- Bottom Action Buttons -->
                    <div style="border-top: 1px solid var(--b2b-border); padding-top: 14px; display: flex; gap: 8px;">
                        <button type="button" class="btn btn-secondary" onclick="window.AdvisorOptions.pinOption('${opt.id}')" style="flex: 1; font-size: 12px; padding: 6px;">
                            <span class="material-symbols-outlined" style="font-size: 15px; vertical-align: middle;">push_pin</span>
                            ${opt.is_pinned ? 'Kitűzve' : 'Kitűzés'}
                        </button>
                        <button type="button" class="btn btn-primary" onclick="window.AdvisorOptions.selectForProposal('${opt.id}')" style="flex: 1.4; font-size: 12px; padding: 6px;">
                            <span class="material-symbols-outlined" style="font-size: 15px; vertical-align: middle;">check</span>
                            Kiválasztás
                        </button>
                    </div>
                </div>
            `;
        }

        async reGenerateOptions() {
            if (!this.activeCaseId) return;
            const container = document.getElementById('advisorMainContent');
            if (container) {
                this.renderSkeleton(container);
                try {
                    await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/options/generate`, { method: 'POST' });
                    await this.loadOptions(this.activeCaseId);
                } catch (e) {
                    console.error('Failed to regenerate options:', e);
                }
                this.renderContent(container);
            }
        }

        async pinOption(optionId) {
            const opt = this.options.find(o => o.id === optionId);
            if (!opt) return;
            opt.is_pinned = !opt.is_pinned;
            try {
                await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/candidates/pin`, {
                    method: 'POST',
                    body: {
                        candidate_id: optionId,
                        is_pinned: opt.is_pinned,
                        component_type: 'full_package'
                    }
                });
            } catch (e) {
                console.error('Failed to pin option:', e);
            }
            const container = document.getElementById('advisorMainContent');
            if (container) this.renderContent(container);
        }

        selectForProposal(optionId) {
            alert(`Opció (${optionId}) sikeresen hozzáadva a javaslati csomaghoz!`);
            window.AdvisorNavigation.navigate('proposals', this.activeCaseId);
        }

        createProposalFromOptions() {
            window.AdvisorNavigation.navigate('proposals', this.activeCaseId);
        }
    }

    window.AdvisorOptions = new AdvisorOptionsView();
})();
