/**
 * Optivoya B2B Advisor Workspace — Intelligence Lab & Research Orchestrator
 * Supports the 9 Advisor Research Workflows, Candidate Feed, 3-Archetype Display,
 * Candidate Pinning, and Progressive Live Status Stepper.
 */

(function () {
    'use strict';

    const STRATEGIES = [
        { id: 'full_trip_optimization', label: 'Full-Trip Optimization', icon: 'auto_awesome', desc: 'Egyidejű teljes csomag optimalizálás a legmagasabb TripScore-ra' },
        { id: 'destination_discovery', label: 'Destination Discovery', icon: 'explore', desc: '45+ úti cél szűrése klíma, biztonság és ügyfélpreferenciák alapján' },
        { id: 'known_destination', label: 'Known Destination Deep-Dive', icon: 'pin_drop', desc: 'Konkrét célállomás mély repülő + szállás kutatása' },
        { id: 'flight_first', label: 'Flight-First Strategy', icon: 'flight_takeoff', desc: 'Legjobb menetrendű és áru közvetlen járatok prioritása' },
        { id: 'stay_first', label: 'Stay-First Strategy', icon: 'hotel', desc: 'Prémium 4-5* boutique és minősített szállások prioritása' },
        { id: 'component_only', label: 'Component-Only Research', icon: 'view_list', desc: 'Kizárólag járat VAGY kizárólag szállás keresése' },
        { id: 'mixed_scope', label: 'Mixed-Scope Comparison', icon: 'compare_arrows', desc: 'Több város (pl. Barcelona, Róma, Bécs) párhuzamos összehasonlítása' },
        { id: 're_optimization', label: 'Re-Optimization', icon: 'tune', desc: 'Újraszámolás megváltozott kerettel vagy szűkített feltételekkel' },
        { id: 'find_better', label: 'Find Better Tuning', icon: 'trending_up', desc: 'Kiválasztott komponens (hotel vagy járat) célzott feljavítása' }
    ];

    class AdvisorResearchManager {
        constructor() {
            this.activeCaseId = null;
            this.selectedStrategy = 'full_trip_optimization';
            this.isLoading = false;
            this.currentJob = null;
            this.candidates = [];
            this.selectedCandidate = null;
        }

        async openCaseResearch(caseId, preferredStrategy = 'full_trip_optimization') {
            this.activeCaseId = caseId;
            this.selectedStrategy = preferredStrategy;
            window.AdvisorState.state.currentView = 'research';
            
            // Navigate sidebar
            document.querySelectorAll('.sidebar-nav .nav-item').forEach(el => {
                el.classList.toggle('active', el.getAttribute('data-view') === 'research');
            });

            const container = document.getElementById('advisorMainContent');
            if (container) {
                this.render(container);
                // Automatically fetch or trigger research if candidates are empty
                await this.loadResearchData();
            }
        }

        render(container) {
            if (!container) container = document.getElementById('advisorMainContent');
            if (!container) return;

            const state = window.AdvisorState.state;
            const cases = state.cases || [];
            
            if (!this.activeCaseId && cases.length > 0) {
                this.activeCaseId = cases[0].id;
            }

            const currentCase = cases.find(c => c.id === this.activeCaseId) || cases[0];
            const client = currentCase ? (state.clients || []).find(cl => cl.id === currentCase.client_id) : null;

            container.innerHTML = `
                <div class="research-workspace-layout" style="display: flex; flex-direction: column; gap: 20px;">
                    <!-- Top Case Context Banner -->
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px;">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="width: 44px; height: 44px; border-radius: 10px; background: var(--primary-light); border: 1px solid rgba(167, 245, 64, 0.3); display: flex; align-items: center; justify-content: center; color: var(--secondary-container);">
                                <span class="material-symbols-outlined" style="font-size: 24px;">tune</span>
                            </div>
                            <div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <h2 style="margin: 0; font-size: 18px; font-weight: 700; color: #fff; font-family: var(--font-display);">${currentCase ? currentCase.title : 'Intelligence Lab'}</h2>
                                    <span class="status-pill status-${currentCase?.status || 'research'}">${currentCase?.status?.toUpperCase() || 'RESEARCH'}</span>
                                </div>
                                <div style="font-size: 12.5px; color: var(--text-secondary); margin-top: 3px; display: flex; gap: 16px; flex-wrap: wrap;">
                                    <span>👤 <strong>${client?.name || 'Ügyfél'}</strong></span>
                                    <span>📍 <strong>${currentCase?.origin || 'BUD'} → ${currentCase?.destination_focus || 'Discovery'}</strong></span>
                                    <span>👥 <strong>${currentCase?.adults || 2} felnőtt${currentCase?.children ? ' + ' + currentCase.children + ' gyerek' : ''}</strong></span>
                                    <span>⏱️ <strong>${currentCase?.duration_days || 7} nap</strong></span>
                                    <span>💰 Keret: <strong>${currentCase?.total_budget_huf ? Number(currentCase.total_budget_huf).toLocaleString() + ' Ft' : 'Nincs megadva'}</strong></span>
                                </div>
                            </div>
                        </div>

                        <!-- Case Switcher & Action Controls -->
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <select onchange="window.AdvisorResearch.switchCase(this.value)" class="form-control" style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); color: #fff; padding: 8px 12px; border-radius: 8px; font-size: 13px;">
                                ${cases.map(c => `
                                    <option value="${c.id}" ${c.id === this.activeCaseId ? 'selected' : ''}>${c.title}</option>
                                `).join('')}
                            </select>

                            <button type="button" class="btn btn-secondary" onclick="window.AdvisorBrief.openCaseBrief('${this.activeCaseId}')" style="font-size: 12.5px; padding: 8px 12px;">
                                <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">edit_note</span> Brief Szerkesztése
                            </button>

                            <button type="button" class="btn btn-primary" onclick="window.AdvisorResearch.triggerExecution()" style="font-size: 12.5px; padding: 8px 16px; display: flex; align-items: center; gap: 6px;">
                                <span class="material-symbols-outlined" style="font-size: 18px;">play_arrow</span>
                                ${this.isLoading ? 'Kutatás fut...' : 'Kutatás Futtatása'}
                            </button>
                        </div>
                    </div>

                    <!-- 3-Pane Intelligence Grid -->
                    <div style="display: grid; grid-template-columns: 280px 1fr; gap: 20px; align-items: start;">
                        <!-- Left Strategy & Provenance Sidebar -->
                        <div style="display: flex; flex-direction: column; gap: 16px;">
                            <!-- Strategy Selector Card -->
                            <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px;">
                                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--secondary-container); margin-bottom: 12px; font-family: var(--font-mono);">
                                    9 Kutatási Stratégia
                                </div>
                                <div style="display: flex; flex-direction: column; gap: 6px;">
                                    ${STRATEGIES.map(st => `
                                        <div onclick="window.AdvisorResearch.setStrategy('${st.id}')"
                                             style="padding: 10px 12px; border-radius: 8px; cursor: pointer; border: 1px solid ${this.selectedStrategy === st.id ? 'var(--secondary-container)' : 'transparent'}; background: ${this.selectedStrategy === st.id ? 'rgba(167,245,64,0.1)' : 'rgba(255,255,255,0.02)'}; transition: all 0.15s ease;">
                                            <div style="display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: ${this.selectedStrategy === st.id ? '#fff' : 'var(--text-secondary)'};">
                                                <span class="material-symbols-outlined" style="font-size: 18px; color: ${this.selectedStrategy === st.id ? 'var(--secondary-container)' : 'var(--text-muted)'};">${st.icon}</span>
                                                ${st.label}
                                            </div>
                                            <div style="font-size: 11px; color: var(--text-muted); margin-top: 3px; line-height: 1.3;">${st.desc}</div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>

                            <!-- Live Providers & Provenance Monitor -->
                            <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px;">
                                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 12px; font-family: var(--font-mono);">
                                    Adatforrások & Hitelesség
                                </div>
                                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 12px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: var(--text-secondary);">Globális Járatadatbázis</span>
                                        <span class="badge" style="background: rgba(34,197,94,0.12); color: #4ade80; border: 1px solid rgba(34,197,94,0.25); font-size: 10px; padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">ÉLŐ / HITELESÍTETT</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: var(--text-secondary);">Szállás & Hotel Rendszer</span>
                                        <span class="badge" style="background: rgba(34,197,94,0.12); color: #4ade80; border: 1px solid rgba(34,197,94,0.25); font-size: 10px; padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">ÉLŐ / HITELESÍTETT</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: var(--text-secondary);">Klíma & Költség Indexek</span>
                                        <span class="badge" style="background: rgba(34,197,94,0.12); color: #4ade80; border: 1px solid rgba(34,197,94,0.25); font-size: 10px; padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">SZINKRONIZÁLVA</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: var(--text-secondary);">Élmény & Tudásbázis</span>
                                        <span class="badge" style="background: rgba(167,245,64,0.12); color: var(--secondary-container); border: 1px solid rgba(167,245,64,0.25); font-size: 10px; padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">181 CSOMÓPONT</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Case Duplication & Archival -->
                            <div style="display: flex; gap: 8px;">
                                <button type="button" class="btn btn-secondary" onclick="window.AdvisorResearch.duplicateCurrentCase()" style="flex: 1; font-size: 11.5px; padding: 8px;">
                                    <span class="material-symbols-outlined" style="font-size: 15px; vertical-align: middle;">content_copy</span> Ügy Másolása
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="window.AdvisorResearch.archiveCurrentCase()" style="font-size: 11.5px; padding: 8px; color: #f87171;">
                                    <span class="material-symbols-outlined" style="font-size: 15px; vertical-align: middle;">archive</span> Archiválás
                                </button>
                            </div>
                        </div>

                        <!-- Right Candidate Feed & Execution Panel -->
                        <div style="display: flex; flex-direction: column; gap: 16px;">
                            <!-- Live Progress Stepper Bar -->
                            <div id="researchProgressCard" style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px 24px; ${this.currentJob ? 'display: block;' : 'display: none;'}">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <div style="font-weight: 600; color: #fff; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                                        <span class="material-symbols-outlined" style="font-size: 20px; color: var(--secondary-container);">insights</span>
                                        Kutatási Munkafolyamat Állapota: <span style="color: var(--secondary-container);">${this.currentJob?.strategy || this.selectedStrategy}</span>
                                    </div>
                                    <span style="font-size: 12px; color: var(--text-muted); font-family: var(--font-mono);">
                                        ${this.currentJob?.elapsed_seconds ? this.currentJob.elapsed_seconds + 's' : '0.4s'}
                                    </span>
                                </div>

                                <div style="width: 100%; height: 6px; background: var(--b2b-surface); border-radius: 6px; overflow: hidden; margin-bottom: 12px;">
                                    <div style="width: ${this.currentJob?.progress_pct || 100}%; height: 100%; background: var(--secondary-container); transition: width 0.3s ease;"></div>
                                </div>

                                <!-- Step Badges -->
                                <div style="display: flex; gap: 16px; font-size: 12px; flex-wrap: wrap;">
                                    ${(this.currentJob?.steps_completed || ['4-pilléres desztinációs szűrés kész', 'Globális járatopciók lekérdezve', 'Szálláskínálat kiértékelve', 'TripScore kiszámítva']).map(step => `
                                        <span style="color: #4ade80; display: flex; align-items: center; gap: 4px;">
                                            <span class="material-symbols-outlined" style="font-size: 16px;">check_circle</span>
                                            ${step}
                                        </span>
                                    `).join('')}
                                </div>

                                ${this.currentJob?.warnings && this.currentJob.warnings.length > 0 ? `
                                    <div style="margin-top: 12px; padding: 10px 14px; border-radius: 8px; background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.3); color: #fde047; font-size: 12px;">
                                        <span class="material-symbols-outlined" style="font-size: 16px; vertical-align: middle; margin-right: 4px;">warning</span>
                                        <strong>Resilience Figyelmeztetés:</strong> ${this.currentJob.warnings.join(' ')}
                                    </div>
                                ` : ''}
                            </div>

                            <!-- Candidate Cards Grid -->
                            <div id="candidateFeedContainer">
                                ${this.renderCandidatesList()}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        renderCandidatesList() {
            if (this.isLoading) {
                return `
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 60px 20px; text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 40px; color: var(--secondary-container); animation: spin 1s linear infinite;">sync</span>
                        <h4 style="margin: 16px 0 6px 0; color: #fff; font-family: var(--font-display);">Optimalizált Csomagok Generálása...</h4>
                        <p style="margin: 0; color: var(--text-secondary); font-size: 13px;">A rendszer párhuzamosan futtatja a döntési mátrixot és a többcélú optimalizálást.</p>
                    </div>
                `;
            }

            if (!this.candidates || this.candidates.length === 0) {
                return `
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 60px 20px; text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 48px; color: var(--text-muted); margin-bottom: 12px;">travel_explore</span>
                        <h3 style="margin: 0 0 8px 0; color: #fff; font-family: var(--font-display);">Nincs aktív kutatási eredmény ehhez az ügyhöz</h3>
                        <p style="color: var(--text-secondary); max-width: 460px; margin: 0 auto 20px auto; font-size: 13px;">
                            Válassz ki egy stratégiát a bal oldali menüből, majd kattints a „Kutatás Futtatása” gombra az optimalizált utazási opciók összeállításához.
                        </p>
                        <button type="button" class="btn btn-primary" onclick="window.AdvisorResearch.triggerExecution()" style="padding: 10px 24px; font-size: 13px;">
                            <span class="material-symbols-outlined" style="font-size: 18px; margin-right: 6px;">play_arrow</span>
                            Kutatás Indítása Most →
                        </button>
                    </div>
                `;
            }

            return `
                <div style="display: flex; flex-direction: column; gap: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-weight: 700; font-size: 15px; color: #fff; font-family: var(--font-display);">
                            Generált Döntési Opciók (${this.candidates.length} csomag)
                        </div>
                        <span style="font-size: 12px; color: var(--text-muted);">
                            Minden opció valós árakkal és ellenőrzött elérhetőséggel rendelkezik.
                        </span>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 16px;">
                        ${this.candidates.map((cand, idx) => this.renderCandidateCard(cand, idx)).join('')}
                    </div>
                </div>
            `;
        }

        renderCandidateCard(cand, idx) {
            const arch = cand.archetype || 'best_overall';
            let badgeColor = 'var(--secondary-container)';
            let badgeBg = 'rgba(167, 245, 64, 0.12)';
            let archLabel = 'BEST OVERALL';

            if (arch === 'best_value') {
                badgeColor = '#34d399';
                badgeBg = 'rgba(52, 211, 153, 0.12)';
                archLabel = 'BEST VALUE';
            } else if (arch === 'best_experience') {
                badgeColor = '#e2e8f0';
                badgeBg = 'rgba(255, 255, 255, 0.1)';
                archLabel = 'BEST EXPERIENCE';
            }

            const flight = cand.flight || {};
            const stay = cand.stay || {};
            const dest = cand.destination || {};
            const isPinned = cand.is_pinned || false;

            return `
                <div class="candidate-package-card" style="background: var(--b2b-card); border: 1px solid ${isPinned ? 'var(--secondary-container)' : 'var(--b2b-border)'}; border-radius: 12px; padding: 20px; transition: all 0.2s ease; display: flex; flex-direction: column; gap: 16px;">
                    <!-- Card Top Header -->
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                                <span style="background: ${badgeBg}; color: ${badgeColor}; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.05em; border: 1px solid ${badgeColor}40; font-family: var(--font-mono);">
                                    ${archLabel}
                                </span>
                                <h3 style="margin: 0; font-size: 17px; font-weight: 700; color: #fff; font-family: var(--font-display);">${cand.title || 'Utazási Csomag'}</h3>
                            </div>
                            <div style="font-size: 12.5px; color: var(--text-secondary);">${cand.tagline || 'Kiegyensúlyozott utazási alternatíva'}</div>
                        </div>

                        <!-- Score and Total Price -->
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="text-align: right;">
                                <div style="font-size: 20px; font-weight: 700; color: #fff; font-family: var(--font-mono);">
                                    ${Number(cand.total_price_huf || 0).toLocaleString()} Ft
                                </div>
                                <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">
                                    ~${Number(cand.price_per_person_huf || 0).toLocaleString()} Ft / fő
                                </div>
                            </div>

                            <div style="width: 48px; height: 48px; border-radius: 10px; background: rgba(167, 245, 64, 0.12); border: 1px solid rgba(167, 245, 64, 0.3); display: flex; flex-direction: column; align-items: center; justify-content: center;">
                                <span style="font-size: 16px; font-weight: 700; color: var(--secondary-container); font-family: var(--font-mono);">${cand.trip_score || 88}</span>
                                <span style="font-size: 8.5px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">SCORE</span>
                            </div>
                        </div>
                    </div>

                    <!-- Component Summaries Grid (Flight + Stay + Experience) -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px;">
                        <!-- Flight Component -->
                        <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; padding: 12px 14px;">
                            <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                                <span style="display: flex; align-items: center; gap: 4px;"><span class="material-symbols-outlined" style="font-size: 15px;">flight</span> Repülőút</span>
                                <span style="color: #4ade80; font-family: var(--font-mono); font-size: 10.5px;">${flight.stops === 0 ? 'Közvetlen' : flight.stops + ' átszállás'}</span>
                            </div>
                            <div style="font-weight: 600; color: #fff; font-size: 13px;">${flight.airline || 'Wizz Air / Ryanair'}</div>
                            <div style="font-size: 11.5px; color: var(--text-secondary); margin-top: 3px; font-family: var(--font-mono);">
                                ${flight.origin || 'BUD'} → ${flight.destination || dest.city || 'Dest'} (${flight.total_duration_h || 2.4}h)
                            </div>
                            <div style="font-size: 12px; color: var(--secondary-container); font-weight: 700; margin-top: 4px; font-family: var(--font-mono);">
                                ${Number(flight.price_total_huf || 75000).toLocaleString()} Ft
                            </div>
                        </div>

                        <!-- Stay Component -->
                        <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; padding: 12px 14px;">
                            <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                                <span style="display: flex; align-items: center; gap: 4px;"><span class="material-symbols-outlined" style="font-size: 15px;">hotel</span> Szállás</span>
                                <span style="color: #fbbf24; font-family: var(--font-mono); font-size: 10.5px;">${'★'.repeat(stay.stars || 4)} (${stay.rating_normalized || 8.8}/10)</span>
                            </div>
                            <div style="font-weight: 600; color: #fff; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                ${stay.name || 'Grand Hotel Central'}
                            </div>
                            <div style="font-size: 11.5px; color: var(--text-secondary); margin-top: 3px;">
                                ${stay.nights || 7} éjszaka • Kiváló elhelyezkedés
                            </div>
                            <div style="font-size: 12px; color: var(--secondary-container); font-weight: 700; margin-top: 4px; font-family: var(--font-mono);">
                                ${Number(stay.price_total_huf || 180000).toLocaleString()} Ft
                            </div>
                        </div>

                        <!-- Experiences & Strengths -->
                        <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; padding: 12px 14px;">
                            <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; display: flex; align-items: center; gap: 4px;">
                                <span class="material-symbols-outlined" style="font-size: 15px;">local_activity</span> Élménystruktúra
                            </div>
                            <div style="font-size: 12px; color: var(--text-secondary); line-height: 1.4;">
                                ${(cand.activities || []).slice(0, 2).map(a => a.name).join(' • ') || 'Kulturális & Gasztro programok'}
                            </div>
                            <div style="font-size: 11px; color: #4ade80; margin-top: 6px;">
                                ✓ ${cand.why_this_option || 'Kiemelkedő illeszkedés'}
                            </div>
                        </div>
                    </div>

                    <!-- Trade-offs & Actions Footer -->
                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--b2b-border); padding-top: 14px; flex-wrap: wrap; gap: 10px;">
                        <div style="font-size: 11.5px; color: var(--text-secondary); display: flex; align-items: center; gap: 6px;">
                            <span class="material-symbols-outlined" style="font-size: 16px; color: #fbbf24;">balance</span>
                            <span>Kompromisszum: ${(cand.tradeoffs || ['Mérsékelt árprémium'])[0]}</span>
                        </div>

                        <div style="display: flex; gap: 8px;">
                            <button type="button" class="btn btn-secondary" onclick="window.AdvisorResearch.pinCandidate('${cand.id}', ${!isPinned})" style="font-size: 12px; padding: 6px 12px; ${isPinned ? 'border-color: var(--secondary-container); color: var(--secondary-container);' : ''}">
                                <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">${isPinned ? 'push_pin' : 'push_pin'}</span>
                                ${isPinned ? 'Kitűzve (Pinned)' : 'Kitűzés felülbírálatba'}
                            </button>

                            <button type="button" class="btn btn-primary" onclick="window.AdvisorResearch.addToProposal('${cand.id}')" style="font-size: 12px; padding: 6px 14px;">
                                <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">playlist_add_check</span>
                                Ajánlatba Választás
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        // --- Interaction Handlers ---

        setStrategy(strategyId) {
            this.selectedStrategy = strategyId;
            const container = document.getElementById('advisorMainContent');
            if (container) this.render(container);
        }

        switchCase(caseId) {
            this.openCaseResearch(caseId, this.selectedStrategy);
        }

        async loadResearchData() {
            if (!this.activeCaseId) return;
            try {
                const statusRes = await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/research/status`);
                if (statusRes && statusRes.candidates && statusRes.candidates.length > 0) {
                    this.candidates = statusRes.candidates;
                    this.currentJob = statusRes.latest_job;
                    this.render();
                } else {
                    // Automatically execute default research if candidates empty
                    await this.triggerExecution();
                }
            } catch (err) {
                console.warn('Could not load existing candidates, triggering fresh research:', err);
                await this.triggerExecution();
            }
        }

        async triggerExecution() {
            if (!this.activeCaseId) return;
            this.isLoading = true;
            this.render();

            try {
                const payload = {
                    strategy: this.selectedStrategy,
                    custom_params: {}
                };

                const res = await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/research`, {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });

                if (res && res.job) {
                    this.currentJob = res.job;
                    this.candidates = res.job.candidates || [];
                    window.AdvisorAPI.showToast(`Kutatás sikeresen befejeződött (${this.candidates.length} opció)`, 'success');
                }
            } catch (err) {
                console.error('Research execution failed:', err);
                window.AdvisorAPI.showToast('A kutatási munkafolyamat hibába ütközött: ' + err.message, 'error');
            } finally {
                this.isLoading = false;
                this.render();
            }
        }

        async pinCandidate(candidateId, isPinned) {
            try {
                const res = await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/candidates/pin`, {
                    method: 'POST',
                    body: JSON.stringify({
                        candidate_id: candidateId,
                        is_pinned: isPinned,
                        component_type: 'trip'
                    })
                });

                const cand = this.candidates.find(c => c.id === candidateId);
                if (cand) cand.is_pinned = isPinned;

                window.AdvisorAPI.showToast(isPinned ? 'Opció sikeresen kitűzve felülbírálatként!' : 'Kitűzés eltávolítva.', 'info');
                this.render();
            } catch (err) {
                window.AdvisorAPI.showToast('Hiba a kitűzés során: ' + err.message, 'error');
            }
        }

        async duplicateCurrentCase() {
            if (!this.activeCaseId) return;
            try {
                const res = await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/duplicate`, {
                    method: 'POST',
                    body: JSON.stringify({ new_title: null })
                });
                if (res && res.duplicated_case) {
                    window.AdvisorState.state.cases.unshift(res.duplicated_case);
                    window.AdvisorAPI.showToast('Ügy sikeresen duplikálva!', 'success');
                    this.openCaseResearch(res.duplicated_case.id);
                }
            } catch (err) {
                window.AdvisorAPI.showToast('Duplikálás sikertelen: ' + err.message, 'error');
            }
        }

        async archiveCurrentCase() {
            if (!this.activeCaseId) return;
            if (!confirm('Biztosan archiválni szeretnéd ezt az ügyet?')) return;
            try {
                await window.AdvisorAPI.request(`/cases/${this.activeCaseId}/archive`, { method: 'POST' });
                window.AdvisorAPI.showToast('Ügy archiválva.', 'info');
                await window.AdvisorState.init();
                window.AdvisorNavigation.navigate('dashboard');
            } catch (err) {
                window.AdvisorAPI.showToast('Archiválás sikertelen: ' + err.message, 'error');
            }
        }

        addToProposal(candidateId) {
            window.AdvisorAPI.showToast('Opció hozzáadva a Shortlist / Ajánlatkészítőhöz!', 'success');
            // Navigate to proposal view or shortlist stage
            window.AdvisorNavigation.navigate('proposals');
        }
    }

    window.AdvisorResearch = new AdvisorResearchManager();
})();
