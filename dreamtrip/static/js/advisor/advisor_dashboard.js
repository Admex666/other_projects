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
            } else if (view === 'research') {
                this.renderResearchLabView(container, state);
            } else if (view === 'proposals') {
                this.renderProposalsView(container, state);
            } else if (view === 'settings') {
                this.renderSettingsView(container, state);
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
                        <div class="kpi-value" style="color: var(--b2b-accent);">${kpis.active_cases || activeCases.length}</div>
                        <div class="kpi-subtext">Kutatás, shortlist és aktív ajánlatok</div>
                    </div>

                    <div class="kpi-card">
                        <div class="kpi-label">Kutatási Idő Megtakarítás</div>
                        <div class="kpi-value" style="color: #34d399;">~${kpis.estimated_hours_saved || '8.5'} óra</div>
                        <div class="kpi-subtext">Automatizált járat & szállás aggregáció</div>
                    </div>

                    <div class="kpi-card">
                        <div class="kpi-label">Kiküldött Ajánlatok</div>
                        <div class="kpi-value" style="color: #c084fc;">${kpis.proposals_created || 2}</div>
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
                        <h3 style="margin: 0 0 4px 0; font-size: 18px; font-weight: 800; color: #fff;">Aktuális Utazási Ügyek (Cases)</h3>
                        <p style="margin: 0; font-size: 12.5px; color: #94a3b8;">Kattints egy ügyre a kutatás folytatásához vagy az ajánlat szerkesztéséhez:</p>
                    </div>
                    <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.openNewCaseModal()" style="font-size: 12.5px; padding: 7px 14px; border-radius: 8px; background: #0284c7;">
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
                <div class="case-card" onclick="window.AdvisorDashboard.openCaseDetail('${c.id}')">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;">
                        <div style="font-size: 11px; font-weight: 800; color: var(--b2b-accent); text-transform: uppercase; letter-spacing: 0.05em;">
                            ${c.client_name || 'Ügyfél'}
                        </div>
                        <span class="status-pill ${statusInfo.class}">${statusInfo.label}</span>
                    </div>

                    <div>
                        <div style="font-size: 15px; font-weight: 800; color: #fff; margin-bottom: 4px; line-height: 1.3;">
                            ${c.title}
                        </div>
                        <div style="font-size: 12.5px; color: #94a3b8; display: flex; align-items: center; gap: 6px;">
                            <span class="material-symbols-outlined" style="font-size: 16px;">flight_takeoff</span>
                            ${c.research_scope?.candidate_origins?.[0] || 'BUD'} → <strong>${dests}</strong> (${c.duration_days_min} nap)
                        </div>
                    </div>

                    <div style="padding-top: 10px; border-top: 1px solid var(--b2b-border); display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #cbd5e1;">
                        <div>
                            <span style="color: #64748b;">Célbüdzsé:</span>
                            <strong style="color: #fff; font-family: 'JetBrains Mono', monospace;">${budgetFormatted}</strong>
                        </div>
                        <div style="display: flex; align-items: center; gap: 4px; color: var(--b2b-accent); font-weight: 700;">
                            <span>Megnyitás</span>
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
                        <h2 style="margin: 0 0 4px 0; font-size: 20px; font-weight: 800; color: #fff;">Összes Utazási Ügy (Cases)</h2>
                        <p style="margin: 0; font-size: 13px; color: #94a3b8;">Kezeld az aktív, ajánlat alatt lévő és lezárt ügyeket.</p>
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
                        <h2 style="margin: 0 0 4px 0; font-size: 20px; font-weight: 800; color: #fff;">Ügyfélkezelő (Client CRM)</h2>
                        <p style="margin: 0; font-size: 13px; color: #94a3b8;">Ügyfélprofilok, utazási preferenciák és korábbi utak.</p>
                    </div>
                    <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.openNewClientModal()">+ Új Ügyfél (C)</button>
                </div>

                <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 16px; overflow: hidden;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                        <thead>
                            <tr style="background: var(--b2b-surface); border-bottom: 1px solid var(--b2b-border); color: #94a3b8; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">
                                <th style="padding: 14px 20px;">Név</th>
                                <th style="padding: 14px 20px;">Kapcsolat</th>
                                <th style="padding: 14px 20px;">Címkék</th>
                                <th style="padding: 14px 20px;">Preferenciák</th>
                                <th style="padding: 14px 20px; text-align: right;">Művelet</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${state.clients.map(cl => `
                                <tr style="border-bottom: 1px solid var(--b2b-border); transition: background 0.1s ease;">
                                    <td style="padding: 16px 20px; font-weight: 700; color: #fff;">
                                        ${cl.name}
                                    </td>
                                    <td style="padding: 16px 20px; color: #cbd5e1;">
                                        <div>${cl.email || '—'}</div>
                                        <div style="font-size: 11.5px; color: #64748b;">${cl.phone || ''}</div>
                                    </td>
                                    <td style="padding: 16px 20px;">
                                        ${(cl.tags || []).map(t => `<span style="font-size: 10.5px; font-weight: 700; background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 4px; padding: 2px 6px; margin-right: 4px;">${t}</span>`).join('')}
                                    </td>
                                    <td style="padding: 16px 20px; font-size: 12px; color: #94a3b8;">
                                        ${cl.preferences?.hotel_min_stars ? `${cl.preferences.hotel_min_stars}★ min. hotel` : 'Standard'} • 
                                        ${cl.preferences?.hotel_min_rating ? `${cl.preferences.hotel_min_rating}+ rating` : 'Nincs min. rating'}
                                    </td>
                                    <td style="padding: 16px 20px; text-align: right; display: flex; justify-content: flex-end; gap: 6px;">
                                        <button type="button" class="btn btn-secondary" onclick="window.AdvisorClients.openClientDrawer('${cl.id}')" style="font-size: 11.5px; padding: 5px 10px;">
                                            Adatlap & DNA
                                        </button>
                                        <button type="button" class="btn btn-primary" onclick="window.AdvisorNavigation.openNewCaseModal()" style="font-size: 11.5px; padding: 5px 10px; background: #0284c7;">
                                            + Új Ügy
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }

        // --- 4. Intelligence Lab View ---
        renderResearchLabView(container) {
            if (window.AdvisorResearch) {
                window.AdvisorResearch.render(container);
                return;
            }
            container.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h2 style="margin: 0 0 4px 0; font-size: 20px; font-weight: 800; color: #fff;">Intelligence Lab (MCDA Engine)</h2>
                    <p style="margin: 0; font-size: 13px; color: #94a3b8;">PROMETHEE II outranking, Kiwi járat-intelligencia és Cozycozy aggregáció vezérlőpult.</p>
                </div>
            `;
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
            const clientId = document.getElementById('caseClientSelect').value;
            const title = document.getElementById('caseTitleInput').value;
            const origin = document.getElementById('caseOriginInput').value || 'BUD';
            const destStr = document.getElementById('caseDestInput').value || 'London';
            const budget = parseFloat(document.getElementById('caseBudgetInput').value) || 500000;
            const duration = parseInt(document.getElementById('caseDurationInput').value, 10) || 4;

            if (!clientId || !title) {
                alert('Kérlek töltsd ki a kötelező mezőket!');
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
                    alert(`✅ Sikeresen létrehozva: "${title}"`);
                }
            } catch (err) {
                alert(`Hiba az ügy létrehozásakor: ${err.message}`);
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
                alert('Kérlek add meg az ügyfél nevét!');
                return;
            }

            const tags = tagsStr.split(',').map(s => s.trim()).filter(Boolean);

            try {
                const res = await window.AdvisorAPI.createClient({
                    name,
                    email,
                    phone,
                    tags,
                    notes
                });

                if (res.status === 'success') {
                    window.AdvisorNavigation.closeModals();
                    await window.AdvisorState.refreshClients();
                    window.AdvisorNavigation.populateClientSelectDropdown();
                    alert(`✅ Ügyfél rögzítve: "${name}"`);
                }
            } catch (err) {
                alert(`Hiba az ügyfél rögzítésekor: ${err.message}`);
            }
        }
    }

    window.AdvisorDashboard = new AdvisorDashboardManager();
})();
