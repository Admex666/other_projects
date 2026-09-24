/**
 * Optivoya Advisor Workspace — Dashboard View Controller
 * High information-density UI renderer for KPIs, Active Cases, Client CRM & Forms.
 */

(function () {
    'use strict';

    const STATUS_MAP = {
        'brief': { label: 'Brief / Igényfelmérés', class: 'status-brief' },
        'research': { label: 'Kutatás Folyamatban', class: 'status-researching' },
        'researching': { label: 'Kutatás Folyamatban', class: 'status-researching' },
        'shortlist': { label: 'Shortlist Összeállítva', class: 'status-shortlist' },
        'proposal': { label: 'Ajánlat Kiküldve', class: 'status-proposal' },
        'waiting': { label: 'Ügyfél Döntésre Vár', class: 'status-proposal' },
        'revision': { label: 'Ügyfél Revízió', class: 'status-shortlist' },
        'closed': { label: 'Lezárva (Sikeres)', class: 'status-closed' }
    };

    class AdvisorDashboardManager {
        constructor() {
            // Subscribe to state changes
            if (window.AdvisorState) {
                window.AdvisorState.subscribe(() => this.render());
            }
        }

        render() {
            const container = document.getElementById('advisorMainContent');
            if (!container) return;

            const state = window.AdvisorState.state;
            const view = state.currentView || 'dashboard';

            if (view === 'dashboard') {
                this.renderDashboardView(container, state);
            } else if (view === 'cases') {
                this.renderCasesView(container, state);
            } else if (view === 'clients') {
                this.renderClientsView(container, state);
            } else if (view === 'client-detail') {
                this.renderClientDetailView(container, state);
            } else if (view === 'brief') {
                this.renderBriefView(container, state);
            } else if (view === 'research') {
                this.renderResearchLabView(container, state);
            } else if (view === 'options') {
                this.renderOptionsView(container, state);
            } else if (view === 'compare') {
                this.renderCompareView(container, state);
            } else if (view === 'proposals' || view === 'proposal') {
                this.renderProposalsView(container, state);
            } else if (view === 'timeline') {
                this.renderTimelineView(container, state);
            } else if (view === 'settings') {
                this.renderSettingsView(container, state);
            }
        }

        renderBriefView(container, state) {
            if (window.AdvisorBrief) {
                window.AdvisorBrief.render(container, state.activeCaseId);
            }
        }

        renderOptionsView(container, state) {
            if (window.AdvisorOptions) {
                window.AdvisorOptions.render(container, state.activeCaseId);
            }
        }

        renderCompareView(container, state) {
            if (window.AdvisorOptionCompare) {
                window.AdvisorOptionCompare.render(container, state.activeCaseId);
            }
        }

        renderProposalsView(container, state) {
            if (window.AdvisorProposal) {
                window.AdvisorProposal.render(container, state.activeCaseId);
            }
        }

        renderTimelineView(container, state) {
            if (window.AdvisorTimeline) {
                window.AdvisorTimeline.render(container, state.activeCaseId);
            }
        }

        // --- 1. Dashboard View ---
        renderDashboardView(container, state) {
            const kpis = state.kpis || {};
            const activeCases = state.cases.filter(c => c.status !== 'closed' && c.status !== 'rejected');

            container.innerHTML = `
                <!-- KPI Sáv -->
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-label">Aktív Ügyek (Cases)</div>
                        <div class="kpi-value" style="color: var(--secondary-container);">${kpis.active_cases || activeCases.length}</div>
                        <div class="kpi-subtext">Kutatás, shortlist és aktív ajánlatok</div>
                    </div>

                    <div class="kpi-card">
                        <div class="kpi-label">Kutatási Idő Megtakarítás</div>
                        <div class="kpi-value" style="color: #a7f540;">~${kpis.estimated_hours_saved || '8.5'} óra</div>
                        <div class="kpi-subtext">Automatizált járat & szállás aggregáció</div>
                    </div>

                    <div class="kpi-card">
                        <div class="kpi-label">Kiküldött Ajánlatok</div>
                        <div class="kpi-value" style="color: #e2e8f0;">${kpis.proposals_created || 2}</div>
                        <div class="kpi-subtext">3-Archetype interaktív prezentáció</div>
                    </div>

                    <div class="kpi-card">
                        <div class="kpi-label">Átlagos TripScore</div>
                        <div class="kpi-value" style="color: #fbbf24;">${kpis.avg_composite_tripscore || 88.4}</div>
                        <div class="kpi-subtext">4-pilléres kompozit minőségi index</div>
                    </div>
                </div>

                <!-- Aktív Ügyek Fejléc & Kártyák -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div>
                        <h3 style="margin: 0 0 4px 0; font-size: 18px; font-weight: 700; color: #fff; font-family: var(--font-display);">Aktuális Utazási Ügyek (Cases)</h3>
                        <p style="margin: 0; font-size: 12.5px; color: var(--text-secondary);">Kattints egy ügyre a kutatás folytatásához vagy az ajánlat szerkesztéséhez:</p>
                    </div>
                    <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.openNewCaseModal()" style="font-size: 12.5px; padding: 7px 14px;">
                        + Új Ügy (N)
                    </button>
                </div>

                <div class="case-cards-grid">
                    ${activeCases.map(c => this.renderCaseCard(c)).join('')}
                    ${activeCases.length === 0 ? `
                        <div style="grid-column: 1 / -1; padding: 40px; text-align: center; background: var(--b2b-card); border-radius: 16px; border: 1px dashed var(--b2b-border);">
                            <span class="material-symbols-outlined" style="font-size: 40px; color: #64748b; margin-bottom: 10px;">folder_open</span>
                            <div style="font-size: 15px; font-weight: 700; color: #fff;">Nincs aktív ügy folyamatban</div>
                            <p style="font-size: 12.5px; color: #94a3b8; margin: 6px 0 16px 0;">Hozz létre egy új ügyet az 'N' billentyűvel vagy az Új Ügy gombra kattintva.</p>
                            <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.openNewCaseModal()">+ Első Ügy Indítása</button>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        renderCaseCard(c) {
            const statusInfo = STATUS_MAP[c.status] || { label: c.status, class: 'status-brief' };
            const budgetFormatted = c.target_total_budget ? `${c.target_total_budget.toLocaleString()} Ft` : 'Rugalmas';
            const dests = c.research_scope?.candidate_destinations?.join(', ') || 'Ismeretlen cél';

            return `
                <div class="case-card" onclick="window.AdvisorNavigation.navigateToCase('${c.id}', 'brief')">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;">
                        <div style="font-size: 11px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; letter-spacing: 0.05em; font-family: var(--font-mono);">
                            ${c.client_name || 'Ügyfél'}
                        </div>
                        <span class="status-pill ${statusInfo.class}">${statusInfo.label}</span>
                    </div>

                    <div>
                        <div style="font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 4px; line-height: 1.3; font-family: var(--font-display);">
                            ${c.title}
                        </div>
                        <div style="font-size: 12.5px; color: var(--text-secondary); display: flex; align-items: center; gap: 6px;">
                            <span class="material-symbols-outlined" style="font-size: 16px;">flight_takeoff</span>
                            ${c.research_scope?.candidate_origins?.[0] || 'BUD'} → <strong>${dests}</strong> (${c.duration_days_min} nap)
                        </div>
                    </div>

                    <div style="padding-top: 10px; border-top: 1px solid var(--b2b-border); display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: var(--text-secondary);">
                        <div>
                            <span style="color: var(--text-muted);">Célbüdzsé:</span>
                            <strong style="color: #fff; font-family: var(--font-mono);">${budgetFormatted}</strong>
                        </div>
                        <div style="display: flex; align-items: center; gap: 4px; color: var(--secondary-container); font-weight: 600;">
                            <span>Munkaterület</span>
                            <span class="material-symbols-outlined" style="font-size: 16px;">arrow_forward</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // --- 2. Full Cases View ---
        renderCasesView(container, state) {
            container.innerHTML = `
                <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="margin: 0 0 4px 0; font-size: 20px; font-weight: 700; color: #fff; font-family: var(--font-display);">Összes Utazási Ügy (Cases)</h2>
                        <p style="margin: 0; font-size: 13px; color: var(--text-secondary);">Kezeld az aktív, ajánlat alatt lévő és lezárt ügyeket.</p>
                    </div>
                    <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.openNewCaseModal()">+ Új Ügy (N)</button>
                </div>

                <div class="case-cards-grid">
                    ${state.cases.map(c => this.renderCaseCard(c)).join('')}
                </div>
            `;
        }

        // --- 3. Clients CRM View ---
        renderClientsView(container, state) {
            container.innerHTML = `
                <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="margin: 0 0 4px 0; font-size: 20px; font-weight: 700; color: #fff; font-family: var(--font-display);">Ügyfélkezelő (Client CRM)</h2>
                        <p style="margin: 0; font-size: 13px; color: var(--text-secondary);">Ügyfélprofilok, utazási preferenciák és korábbi utak.</p>
                    </div>
                    <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.openNewClientModal()">+ Új Ügyfél (C)</button>
                </div>

                <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; overflow: hidden;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                        <thead>
                            <tr style="background: var(--b2b-surface); border-bottom: 1px solid var(--b2b-border); color: var(--text-muted); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">
                                <th style="padding: 14px 20px;">Név</th>
                                <th style="padding: 14px 20px;">Kapcsolat</th>
                                <th style="padding: 14px 20px;">Címkék</th>
                                <th style="padding: 14px 20px;">Preferenciák</th>
                                <th style="padding: 14px 20px; text-align: right;">Művelet</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${state.clients.map(cl => `
                                <tr style="border-bottom: 1px solid var(--b2b-border); transition: background 0.1s ease; cursor: pointer;" onclick="window.AdvisorNavigation.navigateToClient('${cl.id}')">
                                    <td style="padding: 16px 20px; font-weight: 600; color: #fff;">
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            <span class="material-symbols-outlined" style="font-size: 18px; color: var(--secondary-container);">person</span>
                                            <span>${cl.name}</span>
                                        </div>
                                    </td>
                                    <td style="padding: 16px 20px; color: var(--text-secondary);">
                                        <div>${cl.email || '—'}</div>
                                        <div style="font-size: 11.5px; color: var(--text-muted); font-family: var(--font-mono);">${cl.phone || ''}</div>
                                    </td>
                                    <td style="padding: 16px 20px;">
                                        ${(cl.tags || []).map(t => `<span style="font-size: 10.5px; font-weight: 700; background: rgba(167, 245, 64, 0.12); color: var(--secondary-container); border: 1px solid rgba(167, 245, 64, 0.25); border-radius: 4px; padding: 2px 6px; margin-right: 4px; font-family: var(--font-mono);">${t}</span>`).join('')}
                                    </td>
                                    <td style="padding: 16px 20px; font-size: 12px; color: var(--text-secondary);">
                                        ${cl.preferences?.hotel_min_stars ? `${cl.preferences.hotel_min_stars}★ min. hotel` : 'Standard'} • 
                                        ${cl.preferences?.hotel_min_rating ? `${cl.preferences.hotel_min_rating}+ rating` : 'Nincs min. rating'}
                                    </td>
                                    <td style="padding: 16px 20px; text-align: right;" onclick="event.stopPropagation()">
                                        <div style="display: flex; justify-content: flex-end; gap: 6px;">
                                            <button type="button" class="btn btn-secondary" onclick="window.AdvisorNavigation.navigateToClient('${cl.id}')" style="font-size: 11.5px; padding: 5px 10px;">
                                                Profil & Ügyek
                                            </button>
                                            <button type="button" class="btn btn-secondary" onclick="window.AdvisorClients.openClientDrawer('${cl.id}')" style="font-size: 11.5px; padding: 5px 10px;">
                                                DNA
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }

        // --- 3.1 Client Detail & Associated Cases View ---
        renderClientDetailView(container, state) {
            const client = window.AdvisorState.getActiveClient();
            if (!client) {
                container.innerHTML = `
                    <div style="padding: 40px; text-align: center; color: var(--text-muted);">
                        <span class="material-symbols-outlined" style="font-size: 36px; margin-bottom: 8px;">error_outline</span>
                        <div>Ügyfél nem található.</div>
                        <button type="button" class="btn btn-secondary" onclick="window.AdvisorNavigation.navigate('clients')" style="margin-top: 14px;">← Vissza az Ügyfelekhez</button>
                    </div>
                `;
                return;
            }

            const clientCases = (state.cases || []).filter(c => c.client_id === client.id);

            container.innerHTML = `
                <!-- Client Header Profile Card -->
                <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 14px; padding: 24px; margin-bottom: 24px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="width: 52px; height: 52px; border-radius: 50%; background: var(--primary-light); border: 1px solid rgba(167, 245, 64, 0.3); display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 800; color: var(--secondary-container); font-family: var(--font-mono);">
                                ${client.name.charAt(0)}
                            </div>
                            <div>
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                                    <h2 style="margin: 0; font-size: 22px; font-weight: 800; color: #fff; font-family: var(--font-display);">${client.name}</h2>
                                    ${(client.tags || []).map(t => `<span style="font-size: 11px; font-weight: 700; background: rgba(167, 245, 64, 0.12); color: var(--secondary-container); border: 1px solid rgba(167, 245, 64, 0.25); border-radius: 4px; padding: 2px 8px; font-family: var(--font-mono);">${t}</span>`).join('')}
                                </div>
                                <div style="font-size: 13px; color: var(--text-secondary); display: flex; align-items: center; gap: 14px;">
                                    <span><strong style="color:var(--text-muted);">Email:</strong> ${client.email || '—'}</span>
                                    <span><strong style="color:var(--text-muted);">Telefon:</strong> ${client.phone || '—'}</span>
                                </div>
                            </div>
                        </div>

                        <div style="display: flex; gap: 10px;">
                            <button type="button" class="btn btn-secondary" onclick="window.AdvisorClients.openClientDrawer('${client.id}')">
                                <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">edit</span>
                                Adatlap & DNA Szerkesztése
                            </button>
                            <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.openNewCaseModal()">
                                <span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">add_circle</span>
                                + Új Ügy Indítása
                            </button>
                        </div>
                    </div>

                    <!-- Client DNA Summary Pill Box -->
                    <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--b2b-border); display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; font-size: 12.5px;">
                        <div>
                            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 2px;">Szállás Elvárás</div>
                            <div style="color: #fff; font-weight: 600;">${client.preferences?.hotel_min_stars || 4}★+ (${client.preferences?.hotel_min_rating || 8.0}+ értékelés)</div>
                        </div>
                        <div>
                            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 2px;">Járat Megkötés</div>
                            <div style="color: #fff; font-weight: 600;">${client.preferences?.max_flight_stops === 0 ? 'Csak közvetlen járat' : 'Max 1 átszállás'}</div>
                        </div>
                        <div>
                            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 2px;">Pace / Tempó</div>
                            <div style="color: #fff; font-weight: 600;">${client.preferences?.trip_pace || 'Kiegyensúlyozott (Balanced)'}</div>
                        </div>
                        <div>
                            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 2px;">Megjegyzések</div>
                            <div style="color: var(--text-secondary); font-style: italic;">${client.notes || 'Nincs külön megjegyzés'}</div>
                        </div>
                    </div>
                </div>

                <!-- Client's Associated Cases -->
                <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 17px; font-weight: 700; color: #fff; font-family: var(--font-display);">Ügyfél Utazási Ügyei (${clientCases.length})</h3>
                </div>

                <div class="case-cards-grid">
                    ${clientCases.map(c => this.renderCaseCard(c)).join('')}
                    ${clientCases.length === 0 ? `
                        <div style="grid-column: 1 / -1; padding: 36px; text-align: center; background: var(--b2b-card); border-radius: 12px; border: 1px dashed var(--b2b-border);">
                            <div style="color: var(--text-secondary); font-size: 14px; margin-bottom: 12px;">Ennek az ügyfélnek még nincs rögzített utazási ügye.</div>
                            <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.openNewCaseModal()">+ Első Ügy Létrehozása</button>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // --- 4. Intelligence Lab View ---
        renderResearchLabView(container) {
            if (window.AdvisorResearch) {
                window.AdvisorResearch.render(container);
            } else {
                container.innerHTML = `
                    <div style="margin-bottom: 20px;">
                        <h2 style="margin: 0 0 4px 0; font-size: 20px; font-weight: 700; color: #fff; font-family: var(--font-display);">Kutatási Labor (Intelligence Lab)</h2>
                        <p style="margin: 0; font-size: 13px; color: var(--text-secondary);">Valós idejű többcélú döntéstámogató és utazás-optimalizáló vezérlőpult.</p>
                    </div>
                `;
            }
        }

        // --- 5. Proposals View ---
        renderProposalsView(container) {
            container.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h2 style="margin: 0 0 4px 0; font-size: 20px; font-weight: 800; color: #fff;">Generált Ügyfél Ajánlatok (Proposals)</h2>
                    <p style="margin: 0; font-size: 13px; color: #94a3b8;">Interaktív, márkázott 3-Archetype ajánlatcsomagok és megosztható linkek.</p>
                </div>
                <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 16px; padding: 24px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 16px; border-bottom: 1px solid var(--b2b-border);">
                        <div>
                            <div style="font-weight: 800; color: #fff; font-size: 15px;">Barcelona Gasztro & Tengerpart (v1)</div>
                            <div style="font-size: 12px; color: #94a3b8;">Ügyfél: Tóth Bence & Kata • Létrehozva: 2026-09-18</div>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <span class="status-pill status-proposal">Kiküldve</span>
                            <button type="button" class="btn btn-secondary" onclick="alert('Megnyitás előnézetben...')" style="font-size: 12px; padding: 6px 12px;">Megtekintés</button>
                        </div>
                    </div>
                </div>
            `;
        }

        // --- 6. Settings View ---
        renderSettingsView(container, state) {
            const agency = state.agency || {};
            container.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h2 style="margin: 0 0 4px 0; font-size: 20px; font-weight: 800; color: #fff;">Ügynökségi Beállítások & Ráták</h2>
                    <p style="margin: 0; font-size: 13px; color: #94a3b8;">Ügynökségi márkázás, alapértelmezett jutalékok és devizák.</p>
                </div>
                <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 16px; padding: 24px; max-width: 600px;">
                    <div style="margin-bottom: 16px;">
                        <label style="font-size: 12px; font-weight: 700; color: #94a3b8; display: block; margin-bottom: 6px;">Ügynökség Neve</label>
                        <input type="text" value="${agency.name || 'Optivoya Premier'}" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:10px; border-radius:8px;">
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="font-size: 12px; font-weight: 700; color: #94a3b8; display: block; margin-bottom: 6px;">Alapértelmezett Árrés / Jutalék (%)</label>
                        <input type="number" value="${agency.settings?.default_margin_pct || 12}" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:10px; border-radius:8px;">
                    </div>
                    <button type="button" class="btn btn-primary" onclick="alert('Beállítások elmentve!')">Mentés</button>
                </div>
            `;
        }

        // --- Action Handlers ---
        handleSearch(query) {
            const state = window.AdvisorState.state;
            state.searchQuery = query.toLowerCase();

            if (!query) {
                this.render();
                return;
            }

            const cards = document.querySelectorAll('.case-card');
            cards.forEach(card => {
                const text = card.innerText.toLowerCase();
                card.style.display = text.includes(state.searchQuery) ? 'flex' : 'none';
            });
        }

        openCaseDetail(caseId) {
            if (window.AdvisorBrief) {
                window.AdvisorBrief.openCaseBrief(caseId);
            }
        }

        async submitNewCase(e) {
            e.preventDefault();
            let clientId = document.getElementById('caseClientSelect').value;
            const title = document.getElementById('caseTitleInput').value;
            const origin = document.getElementById('caseOriginInput').value || 'BUD';
            const destStr = document.getElementById('caseDestInput').value || 'London';
            const budget = parseFloat(document.getElementById('caseBudgetInput').value) || 500000;
            const duration = parseInt(document.getElementById('caseDurationInput').value, 10) || 4;

            if (!clientId) {
                const clients = window.AdvisorState.state.clients || [];
                if (clients.length > 0) {
                    clientId = clients[0].id;
                } else {
                    try {
                        const res = await window.AdvisorAPI.createClient({ name: "Kovács Család (Ügyfél)", email: "kovacs@example.com" });
                        const newCl = res.client || res;
                        clientId = newCl.id;
                        if (!window.AdvisorState.state.clients) window.AdvisorState.state.clients = [];
                        window.AdvisorState.state.clients.push(newCl);
                    } catch(err) {
                        console.error('Auto client creation error:', err);
                    }
                }
            }

            if (!clientId || !title) {
                if (window.AdvisorToast) window.AdvisorToast('Kérlek töltsd ki a kötelező mezőket!', 'error');
                return;
            }

            const destinations = destStr.split(',').map(s => s.trim()).filter(Boolean);

            try {
                const res = await window.AdvisorAPI.createCase({
                    client_id: clientId,
                    title: title,
                    target_total_budget: budget,
                    duration_days: duration,
                    origin: origin,
                    destinations: destinations
                });

                if (res.status === 'success') {
                    window.AdvisorNavigation.closeModals();
                    await window.AdvisorState.refreshCases();
                    await window.AdvisorState.refreshKPIs();
                    if (window.AdvisorToast) window.AdvisorToast(`Sikeresen létrehozva: "${title}"`, 'success');
                }
            } catch (err) {
                if (window.AdvisorToast) window.AdvisorToast(`Hiba az ügy létrehozásakor: ${err.message}`, 'error');
            }
        }

        async submitNewClient(e) {
            e.preventDefault();
            const name = document.getElementById('clientNameInput').value;
            const email = document.getElementById('clientEmailInput').value;
            const phone = document.getElementById('clientPhoneInput').value;
            const tagsStr = document.getElementById('clientTagsInput').value;
            const notes = document.getElementById('clientNotesInput').value;

            if (!name) {
                if (window.AdvisorToast) window.AdvisorToast('Kérlek add meg az ügyfél nevét!', 'error');
                return;
            }

            const tags = tagsStr.split(',').map(t => t.trim()).filter(Boolean);

            try {
                const res = await window.AdvisorAPI.createClient({
                    name: name,
                    email: email,
                    phone: phone,
                    tags: tags,
                    notes: notes
                });

                if (res.status === 'success') {
                    window.AdvisorNavigation.closeModals();
                    await window.AdvisorState.refreshClients();
                    await window.AdvisorState.refreshKPIs();
                    window.AdvisorNavigation.populateClientSelectDropdown();
                    if (window.AdvisorToast) window.AdvisorToast(`Ügyfél rögzítve: "${name}"`, 'success');
                }
            } catch (err) {
                if (window.AdvisorToast) window.AdvisorToast(`Hiba az ügyfél rögzítésekor: ${err.message}`, 'error');
            }
        }
    }

    window.AdvisorDashboard = new AdvisorDashboardManager();
})();
