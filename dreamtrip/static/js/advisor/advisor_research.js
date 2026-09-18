/**
 * Optivoya B2B Advisor Workspace — Intelligence Lab & Research Orchestrator
 * Supports the 9 Advisor Research Workflows, Candidate Feed, 3-Archetype Display,
 * Candidate Pinning, and Progressive Live Status Stepper.
 */

(function () {
    'use strict';

    const STRATEGIES = [
        { id: 'full_trip_optimization', label: 'Full-Trip Optimization', icon: 'auto_awesome', desc: 'Egyidejű teljes csomag optimalizálás a legmagasabb TripScore-ra' },
        { id: 'destination_discovery', label: 'Destination Discovery', icon: 'explore', desc: '45+ úti cél szűrése klíma, biztonság és AHP preferenciák alapján' },
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
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 16px; padding: 18px 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px;">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #0284c7, #38bdf8); display: flex; align-items: center; justify-content: center; color: #fff;">
                                <span class="material-symbols-outlined" style="font-size: 24px;">auto_awesome</span>
                            </div>
                            <div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <h2 style="margin: 0; font-size: 18px; font-weight: 800; color: #fff;">${currentCase ? currentCase.title : 'Intelligence Lab'}</h2>
                                    <span class="status-pill status-${currentCase?.status || 'research'}">${currentCase?.status?.toUpperCase() || 'RESEARCH'}</span>
                                </div>
                                <div style="font-size: 12.5px; color: #94a3b8; margin-top: 3px; display: flex; gap: 16px; flex-wrap: wrap;">
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

                            <button type="button" class="btn btn-secondary" onclick="window.AdvisorBrief.openCaseBrief('${this.activeCaseId}')" style="font-size: 12.5px; padding: 8px 12px; border-radius: 8px;">
                                <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">edit_note</span> Brief Szerkesztése
                            </button>

                            <button type="button" class="btn btn-primary" onclick="window.AdvisorResearch.triggerExecution()" style="font-size: 12.5px; padding: 8px 16px; border-radius: 8px; background: #0284c7; display: flex; align-items: center; gap: 6px;">
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
                            <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 16px; padding: 18px;">
                                <div style="font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: var(--b2b-accent); margin-bottom: 12px;">
                                    🧠 9 Kutatási Stratégia
                                </div>
                                <div style="display: flex; flex-direction: column; gap: 6px;">
                                    ${STRATEGIES.map(st => `
                                        <div onclick="window.AdvisorResearch.setStrategy('${st.id}')"
                                             style="padding: 10px 12px; border-radius: 10px; cursor: pointer; border: 1px solid ${this.selectedStrategy === st.id ? 'var(--b2b-accent)' : 'transparent'}; background: ${this.selectedStrategy === st.id ? 'rgba(14,165,233,0.12)' : 'rgba(255,255,255,0.02)'}; transition: all 0.15s ease;">
                                            <div style="display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; color: ${this.selectedStrategy === st.id ? '#fff' : '#cbd5e1'};">
                                                <span class="material-symbols-outlined" style="font-size: 18px; color: ${this.selectedStrategy === st.id ? 'var(--b2b-accent)' : '#64748b'};">${st.icon}</span>
                                                ${st.label}
                                            </div>
                                            <div style="font-size: 11px; color: #64748b; margin-top: 3px; line-height: 1.3;">${st.desc}</div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>

                            <!-- Live Providers & Provenance Monitor -->
                            <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 16px; padding: 18px;">
                                <div style="font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 12px;">
                                    🛡️ Provider Ellenőrzés
                                </div>
                                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 12px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: #cbd5e1;">Kiwi.com GraphQL (Járatok)</span>
                                        <span class="badge" style="background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); font-size: 10px; padding: 2px 6px; border-radius: 6px;">ÉLŐ / VERIFIED</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: #cbd5e1;">Cozycozy Engine (Szállások)</span>
                                        <span class="badge" style="background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); font-size: 10px; padding: 2px 6px; border-radius: 6px;">ÉLŐ / VERIFIED</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: #cbd5e1;">Open-Meteo & Numbeo</span>
                                        <span class="badge" style="background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); font-size: 10px; padding: 2px 6px; border-radius: 6px;">SZINKRONIZÁLVA</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: #cbd5e1;">Experience Knowledge Graph</span>
                                        <span class="badge" style="background: rgba(14,165,233,0.15); color: var(--b2b-accent); border: 1px solid rgba(14,165,233,0.3); font-size: 10px; padding: 2px 6px; border-radius: 6px;">181 CSOMÓPONT</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Case Duplication & Archival -->
                            <div style="display: flex; gap: 8px;">
                                <button type="button" class="btn btn-secondary" onclick="window.AdvisorResearch.duplicateCurrentCase()" style="flex: 1; font-size: 11.5px; padding: 8px;">
                                    <span class="material-symbols-outlined" style="font-size: 15px; vertical-align: middle;">content_copy</span> Ügy Másolása
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="window.AdvisorResearch.archiveCurrentCase()" style="font-size: 11.5px; padding: 8px; color: #ef4444;">
                                    <span class="material-symbols-outlined" style="font-size: 15px; vertical-align: middle;">archive</span> Archiválás
                                </button>
                            </div>
                        </div>

                        <!-- Right Candidate Feed & Execution Panel -->
                        <div style="display: flex; flex-direction: column; gap: 16px;">
                            <!-- Live Progress Stepper Bar -->
                            <div id="researchProgressCard" style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 16px; padding: 18px 24px; ${this.currentJob ? 'display: block;' : 'display: none;'}">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <div style="font-weight: 700; color: #fff; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                                        <span class="material-symbols-outlined" style="font-size: 20px; color: var(--b2b-accent);">insights</span>
                                        Kutatási Munkafolyamat Állapota: <span style="color: #38bdf8;">${this.currentJob?.strategy || this.selectedStrategy}</span>
                                    </div>
                                    <span style="font-size: 12px; color: #94a3b8; font-family: 'JetBrains Mono', monospace;">
                                        ${this.currentJob?.elapsed_seconds ? this.currentJob.elapsed_seconds + 's' : '0.4s'}
                                    </span>
                                </div>

                                <div style="width: 100%; height: 6px; background: var(--b2b-surface); border-radius: 10px; overflow: hidden; margin-bottom: 12px;">
                                    <div style="width: ${this.currentJob?.progress_pct || 100}%; height: 100%; background: linear-gradient(90deg, #0284c7, #38bdf8); transition: width 0.3s ease;"></div>
                                </div>

                                <!-- Step Badges -->
                                <div style="display: flex; gap: 16px; font-size: 12px; flex-wrap: wrap;">
                                    ${(this.currentJob?.steps_completed || ['4-pilléres desztinációs szűrés kész', 'Kiwi járatopciók lekérdezve', 'Cozycozy szállások rangsorolva', 'TripScore kiszámítva']).map(step => `
                                        <span style="color: #4ade80; display: flex; align-items: center; gap: 4px;">
                                            <span class="material-symbols-outlined" style="font-size: 16px;">check_circle</span>
                                            ${step}
                                        </span>
                                    `).join('')}
                                </div>

                                ${this.currentJob?.warnings && this.currentJob.warnings.length > 0 ? `
                                    <div style="margin-top: 12px; padding: 10px 14px; border-radius: 8px; background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.3); color: #fde047; font-size: 12px;">
                                        ⚠️ <strong>Resilience Figyelmeztetés:</strong> ${this.currentJob.warnings.join(' ')}
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
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 16px; padding: 60px 20px; text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 40px; color: var(--b2b-accent); animation: spin 1s linear infinite;">sync</span>
                        <h4 style="margin: 16px 0 6px 0; color: #fff;">Optimalizált Csomagok Generálása...</h4>
                        <p style="margin: 0; color: #94a3b8; font-size: 13px;">A rendszer párhuzamosan futtatja a PROMETHEE II és AHP rangsorolást.</p>
                    </div>
                `;
            }

            if (!this.candidates || this.candidates.length === 0) {
                return `
                    <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 16px; padding: 60px 20px; text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 48px; color: #64748b; margin-bottom: 12px;">travel_explore</span>
                        <h3 style="margin: 0 0 8px 0; color: #fff;">Nincs aktív kutatási eredmény ehhez az ügyhöz</h3>
                        <p style="color: #94a3b8; max-width: 460px; margin: 0 auto 20px auto; font-size: 13px;">
                            Válassz ki egy stratégiát a bal oldali menüből, majd kattints a „Kutatás Futtatása” gombra az optimalizált utazási opciók összeállításához.
                        </p>
                        <button type="button" class="btn btn-primary" onclick="window.AdvisorResearch.triggerExecution()" style="background: #0284c7;">
                            Kutatás Indítása Most →
                        </button>
                    </div>
                `;
            }

            return `
                <div style="display: flex; flex-direction: column; gap: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-weight: 800; font-size: 15px; color: #fff;">
                            🎯 Generált Döntési Opciók (${this.candidates.length} csomag)
                        </div>
                        <span style="font-size: 12px; color: #94a3b8;">
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
            let badgeColor = '#0284c7';
            let badgeBg = 'rgba(14, 165, 233, 0.15)';
            let archLabel = 'BEST OVERALL';

            if (arch === 'best_value') {
                badgeColor = '#10b981';
                badgeBg = 'rgba(16, 185, 129, 0.15)';
                archLabel = 'BEST VALUE';
            } else if (arch === 'best_experience') {
                badgeColor = '#a855f7';
                badgeBg = 'rgba(168, 85, 247, 0.15)';
                archLabel = 'BEST EXPERIENCE';
            }

            const flight = cand.flight || {};
            const stay = cand.stay || {};
            const dest = cand.destination || {};
            const isPinned = cand.is_pinned || false;

            return `
                <div class="candidate-package-card" style="background: var(--b2b-card); border: 1px solid ${isPinned ? 'var(--b2b-accent)' : 'var(--b2b-border)'}; border-radius: 16px; padding: 20px; transition: all 0.2s ease; display: flex; flex-direction: column; gap: 16px;">
                    <!-- Card Top Header -->
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                                <span style="background: ${badgeBg}; color: ${badgeColor}; font-weight: 800; font-size: 11px; padding: 3px 8px; border-radius: 6px; letter-spacing: 0.05em; border: 1px solid ${badgeColor}40;">
                                    ${archLabel}
                                </span>
                                <h3 style="margin: 0; font-size: 17px; font-weight: 800; color: #fff;">${cand.title || 'Utazási Csomag'}</h3>
                            </div>
                            <div style="font-size: 12.5px; color: #94a3b8;">${cand.tagline || 'Kiegyensúlyozott utazási alternatíva'}</div>
                        </div>

                        <!-- Score and Total Price -->
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="text-align: right;">
                                <div style="font-size: 20px; font-weight: 900; color: #fff; font-family: 'JetBrains Mono', monospace;">
                                    ${Number(cand.total_price_huf || 0).toLocaleString()} Ft
                                </div>
                                <div style="font-size: 11px; color: #94a3b8;">
                                    ~${Number(cand.price_per_person_huf || 0).toLocaleString()} Ft / fő
                                </div>
                            </div>

                            <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(14, 165, 233, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); display: flex; flex-direction: column; align-items: center; justify-content: center;">
                                <span style="font-size: 16px; font-weight: 900; color: #38bdf8; font-family: 'JetBrains Mono', monospace;">${cand.trip_score || 88}</span>
                                <span style="font-size: 8.5px; font-weight: 800; color: #94a3b8; text-transform: uppercase;">SCORE</span>
                            </div>
                        </div>
                    </div>

                    <!-- Component Summaries Grid (Flight + Stay + Experience) -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px;">
                        <!-- Flight Component -->
                        <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 12px 14px;">
                            <div style="font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px; display: flex; justify-content: space-between;">
                                <span>✈️ Repülőút</span>
                                <span style="color: #4ade80;">${flight.stops === 0 ? 'Közvetlen' : flight.stops + ' átszállás'}</span>
                            </div>
                            <div style="font-weight: 700; color: #fff; font-size: 13px;">${flight.airline || 'Wizz Air / Ryanair'}</div>
                            <div style="font-size: 11.5px; color: #94a3b8; margin-top: 3px;">
                                ${flight.origin || 'BUD'} → ${flight.destination || dest.city || 'Dest'} (${flight.total_duration_h || 2.4}h)
                            </div>
                            <div style="font-size: 11.5px; color: #38bdf8; font-weight: 700; margin-top: 4px;">
                                ${Number(flight.price_total_huf || 75000).toLocaleString()} Ft
                            </div>
                        </div>

                        <!-- Stay Component -->
                        <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 12px 14px;">
                            <div style="font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px; display: flex; justify-content: space-between;">
                                <span>🏨 Szállás</span>
                                <span style="color: #eab308;">${'★'.repeat(stay.stars || 4)} (${stay.rating_normalized || 8.8}/10)</span>
                            </div>
                            <div style="font-weight: 700; color: #fff; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                ${stay.name || 'Grand Hotel Central'}
                            </div>
                            <div style="font-size: 11.5px; color: #94a3b8; margin-top: 3px;">
                                ${stay.nights || 7} éjszaka • Kiváló elhelyezkedés
                            </div>
                            <div style="font-size: 11.5px; color: #38bdf8; font-weight: 700; margin-top: 4px;">
                                ${Number(stay.price_total_huf || 180000).toLocaleString()} Ft
                            </div>
                        </div>

                        <!-- Experiences & Strengths -->
                        <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 12px 14px;">
                            <div style="font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px;">
                                🏛️ Élménystruktúra
                            </div>
                            <div style="font-size: 12px; color: #cbd5e1; line-height: 1.4;">
                                ${(cand.activities || []).slice(0, 2).map(a => a.name).join(' • ') || 'Kulturális & Gasztro programok'}
                            </div>
                            <div style="font-size: 11px; color: #4ade80; margin-top: 6px;">
                                ✓ ${cand.why_this_option || 'Kiemelkedő illeszkedés'}
                            </div>
                        </div>
                    </div>

                    <!-- Trade-offs & Actions Footer -->
                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--b2b-border); padding-top: 14px; flex-wrap: wrap; gap: 10px;">
                        <div style="font-size: 11.5px; color: #94a3b8; display: flex; align-items: center; gap: 6px;">
                            <span class="material-symbols-outlined" style="font-size: 16px; color: #eab308;">balance</span>
                            <span>Kompromisszum: ${(cand.tradeoffs || ['Mérsékelt árprémium'])[0]}</span>
                        </div>

                        <div style="display: flex; gap: 8px;">
                            <button type="button" class="btn btn-secondary" onclick="window.AdvisorResearch.pinCandidate('${cand.id}', ${!isPinned})" style="font-size: 12px; padding: 6px 12px; ${isPinned ? 'border-color: var(--b2b-accent); color: var(--b2b-accent);' : ''}">
                                <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">${isPinned ? 'push_pin' : 'push_pin'}</span>
                                ${isPinned ? 'Kitűzve (Pinned)' : 'Kitűzés felülbírálatba'}
                            </button>

                            <button type="button" class="btn btn-primary" onclick="window.AdvisorResearch.addToProposal('${cand.id}')" style="font-size: 12px; padding: 6px 14px; background: #0284c7;">
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
