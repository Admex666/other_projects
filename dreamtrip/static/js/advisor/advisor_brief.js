/**
 * Optivoya Advisor Workspace — Deep Trip Brief & Constraint Editor
 * Allows deep customization of 3-mode budgets, hard/soft rules, avoid lists, and overrides.
 */

(function () {
    'use strict';

    class AdvisorBriefManager {
        constructor() {
            this.activeCaseId = null;
            this.activeCase = null;
            this.resolvedPrefs = null;
        }

        render(container, caseId) {
            const targetId = caseId || window.AdvisorState.state.activeCaseId || (this.activeCase ? this.activeCase.id : null);
            if (targetId) {
                this.openCaseBrief(targetId);
            } else {
                const firstCase = window.AdvisorState.state.cases[0];
                if (firstCase) {
                    this.openCaseBrief(firstCase.id);
                } else {
                    if (!container) container = document.getElementById('advisorMainContent');
                    if (container) {
                        container.innerHTML = `
                            <div style="padding: 40px; text-align: center; color: var(--text-muted);">
                                <span class="material-symbols-outlined" style="font-size: 36px; color: var(--text-muted); margin-bottom: 8px;">folder_open</span>
                                <div>Nincs kiválasztott ügy. Válassz egy ügyet a listából vagy a Dashboardról!</div>
                            </div>
                        `;
                    }
                }
            }
        }

        async openCaseBrief(caseId) {
            this.activeCaseId = caseId;
            window.AdvisorState.setActiveCase(caseId);
            const container = document.getElementById('advisorMainContent');
            if (!container) return;

            container.innerHTML = `
                <div style="padding: 40px; text-align: center; color: #94a3b8;">
                    <div class="spinner" style="margin-bottom: 12px;"></div>
                    <div>Ügy és preferencia-hierarchia betöltése...</div>
                </div>
            `;

            try {
                const [caseRes, prefsRes] = await Promise.all([
                    window.AdvisorAPI.getCaseDetails(caseId),
                    window.AdvisorAPI.request(`/cases/${caseId}/resolved-preferences`)
                ]);

                this.activeCase = caseRes.case;
                this.client = caseRes.client;
                this.resolvedPrefs = prefsRes.resolved_preferences;

                this.renderBriefView(container);
            } catch (err) {
                container.innerHTML = `
                    <div style="padding: 30px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; color: #fca5a5;">
                        <h3>Hiba történt a brief betöltésekor</h3>
                        <p>${err.message}</p>
                        <button type="button" class="btn btn-secondary" onclick="window.AdvisorNavigation.navigate('cases')">← Vissza az ügyekhez</button>
                    </div>
                `;
            }
        }

        renderBriefView(container) {
            const c = this.activeCase;
            const cl = this.client || {};
            const hard = c.preferences?.hard || {};
            const soft = c.preferences?.soft || {};
            const avoid = c.preferences?.avoid || {};
            const nice = c.preferences?.nice_to_have || {};
            const budgetMode = c.budget_mode || 'total';

            container.innerHTML = `
                <!-- Fejléc & Navigáció vissza -->
                <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                            <button type="button" onclick="window.AdvisorNavigation.navigate('cases')" class="btn btn-secondary" style="font-size: 11.5px; padding: 4px 8px;">
                                ← Ügyek
                            </button>
                            <span style="font-size: 12px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; font-family: var(--font-mono);">
                                ${cl.name || 'Ismeretlen Ügyfél'}
                            </span>
                        </div>
                        <h2 style="margin: 0; font-size: 22px; font-weight: 700; color: #fff; font-family: var(--font-display);">${c.title}</h2>
                    </div>

                    <div style="display: flex; gap: 10px;">
                        <button type="button" class="btn btn-secondary" onclick="window.AdvisorBrief.saveBrief(false)">
                            Mentés Vázlatként
                        </button>
                        <button type="button" class="btn btn-primary" onclick="window.AdvisorBrief.saveBrief(true)">
                            Mentés & Futtatás az Intelligence Lab-ben →
                        </button>
                    </div>
                </div>

                <!-- 2-Oszlopos Grid: Balra Brief Beállítások, Jobbra Élő Hierarchia Inspector -->
                <div style="display: grid; grid-template-columns: 1fr 340px; gap: 20px;">
                    <!-- Bal Oszlop: Brief Űrlap -->
                    <form id="deepBriefForm" onsubmit="event.preventDefault();" style="display: flex; flex-direction: column; gap: 16px;">
                        
                        <!-- 1. Alapadatok & Logisztika -->
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 20px;">
                            <div style="font-weight: 700; font-size: 14px; color: #fff; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; font-family: var(--font-display);">
                                <span class="material-symbols-outlined" style="font-size: 18px; color: var(--secondary-container);">flight</span>
                                Logisztika & Időtartam
                            </div>

                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                                <div>
                                    <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Indulási Hely</label>
                                    <input type="text" id="briefOrigin" value="${c.origin || 'BUD'}" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px; font-family:var(--font-mono);">
                                </div>
                                <div>
                                    <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Célállomás / Fókusz</label>
                                    <input type="text" id="briefDest" value="${c.destination_focus || 'London'}" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px;">
                                </div>
                                <div>
                                    <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Időtartam (napok)</label>
                                    <input type="number" id="briefDuration" value="${c.duration_days || 4}" min="1" max="30" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px; font-family:var(--font-mono);">
                                </div>
                            </div>

                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                                <div>
                                    <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Felnőttek száma</label>
                                    <input type="number" id="briefAdults" value="${c.adults || 2}" min="1" max="20" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px; font-family:var(--font-mono);">
                                </div>
                                <div>
                                    <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Gyermekek száma</label>
                                    <input type="number" id="briefChildren" value="${c.children || 0}" min="0" max="20" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px; font-family:var(--font-mono);">
                                </div>
                            </div>
                        </div>

                        <!-- 2. Költségvetési Mód (3-Mode Budget) -->
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 20px;">
                            <div style="font-weight: 700; font-size: 14px; color: #fff; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; font-family: var(--font-display);">
                                <span class="material-symbols-outlined" style="font-size: 18px; color: var(--secondary-container);">payments</span>
                                Költségvetési Mód (3-Mode Budget)
                            </div>

                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 16px;">
                                <div onclick="window.AdvisorBrief.setBudgetMode('total')" id="bModeTotal" style="cursor: pointer; padding: 12px; border-radius: 8px; border: 2px solid ${budgetMode === 'total' ? 'var(--secondary-container)' : 'var(--b2b-border)'}; background: ${budgetMode === 'total' ? 'rgba(167, 245, 64, 0.1)' : 'var(--b2b-surface)'};">
                                    <div style="font-weight: 700; font-size: 12px; color: #fff; margin-bottom: 2px;">Mode A: Teljes Keret</div>
                                    <div style="font-size: 11px; color: var(--text-muted);">Egyösszegű felső plafon a teljes útra.</div>
                                </div>

                                <div onclick="window.AdvisorBrief.setBudgetMode('component')" id="bModeComponent" style="cursor: pointer; padding: 12px; border-radius: 8px; border: 2px solid ${budgetMode === 'component' ? 'var(--secondary-container)' : 'var(--b2b-border)'}; background: ${budgetMode === 'component' ? 'rgba(167, 245, 64, 0.1)' : 'var(--b2b-surface)'};">
                                    <div style="font-weight: 700; font-size: 12px; color: #fff; margin-bottom: 2px;">Mode B: Komponens Plafon</div>
                                    <div style="font-size: 11px; color: var(--text-muted);">Külön repjegy és szállás limit.</div>
                                </div>

                                <div onclick="window.AdvisorBrief.setBudgetMode('scope_only')" id="bModeScope" style="cursor: pointer; padding: 12px; border-radius: 8px; border: 2px solid ${budgetMode === 'scope_only' ? 'var(--secondary-container)' : 'var(--b2b-border)'}; background: ${budgetMode === 'scope_only' ? 'rgba(167, 245, 64, 0.1)' : 'var(--b2b-surface)'};">
                                    <div style="font-weight: 700; font-size: 12px; color: #fff; margin-bottom: 2px;">Mode C: Rugalmas / Nyitott</div>
                                    <div style="font-size: 11px; color: var(--text-muted);">Nincs felső plafon, TripScore fókusz.</div>
                                </div>
                            </div>

                            <div id="budgetInputsContainer">
                                ${this.renderBudgetInputs(budgetMode, c)}
                            </div>
                        </div>

                        <!-- 3. Preferencia-Hierarchia (Hard, Soft, Avoid, Nice-to-have, Overrides) -->
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 20px;">
                            <div style="font-weight: 700; font-size: 14px; color: #fff; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; font-family: var(--font-display);">
                                <span class="material-symbols-outlined" style="font-size: 18px; color: var(--secondary-container);">tune</span>
                                Részletes Preferenciák & Szabályrendszer
                            </div>

                            <!-- Hard Constraints Section -->
                            <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--b2b-border);">
                                <div style="font-size: 12px; font-weight: 700; color: #f87171; margin-bottom: 8px; text-transform: uppercase; font-family: var(--font-mono); display: flex; align-items: center; gap: 6px;">
                                    <span class="material-symbols-outlined" style="font-size: 16px;">lock</span>
                                    Hard Constraints (Kizáró / Kötelező feltételek)
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                                    <div>
                                        <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Max. Átszállás (Repülő)</label>
                                        <select id="hardMaxStops" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px;">
                                            <option value="0" ${hard.max_flight_stops === 0 ? 'selected' : ''}>Kizárólag Közvetlen Járat (0 átszállás)</option>
                                            <option value="1" ${hard.max_flight_stops === 1 ? 'selected' : ''}>Legfeljebb 1 átszállás</option>
                                            <option value="2" ${hard.max_flight_stops === 2 ? 'selected' : ''}>Bármennyi átszállás engedélyezett</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Min. Hotel Csillag & Értékelés</label>
                                        <select id="hardHotelStars" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px;">
                                            <option value="3" ${hard.min_hotel_stars === 3 ? 'selected' : ''}>Legalább 3 csillag</option>
                                            <option value="4" ${hard.min_hotel_stars === 4 ? 'selected' : ''}>Legalább 4 csillag</option>
                                            <option value="5" ${hard.min_hotel_stars === 5 ? 'selected' : ''}>Kizárólag 5 csillag (Luxus)</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <!-- Soft Preferences Section -->
                            <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--b2b-border);">
                                <div style="font-size: 12px; font-weight: 700; color: var(--secondary-container); margin-bottom: 8px; text-transform: uppercase; font-family: var(--font-mono); display: flex; align-items: center; gap: 6px;">
                                    <span class="material-symbols-outlined" style="font-size: 16px;">tune</span>
                                    Soft Preferences (Súlyozott preferenciák)
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                                    <div>
                                        <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Preferált Légitársaságok (vesszővel)</label>
                                        <input type="text" id="softAirlines" value="${(soft.preferred_airlines || []).join(', ')}" placeholder="pl. Wizz, Ryanair, Lufthansa" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px;">
                                    </div>
                                    <div>
                                        <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Szállástípus</label>
                                        <input type="text" id="softStayType" value="${(soft.stay_types || []).join(', ')}" placeholder="pl. Hotel, Boutique, Resort" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px;">
                                    </div>
                                </div>
                            </div>

                            <!-- Avoid Lists & Advisor Overrides -->
                            <div>
                                <div style="font-size: 12px; font-weight: 700; color: #fbbf24; margin-bottom: 8px; text-transform: uppercase; font-family: var(--font-mono); display: flex; align-items: center; gap: 6px;">
                                    <span class="material-symbols-outlined" style="font-size: 16px;">block</span>
                                    Tiltólista & Tanácsadói Felülbírálat (Avoid & Overrides)
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                                    <div>
                                        <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Kerülendő Légitársaságok / Városok</label>
                                        <input type="text" id="avoidItems" value="${(avoid.airlines || []).concat(avoid.destinations || []).join(', ')}" placeholder="pl. Késő esti indulás, átszállásos repjegy" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px;">
                                    </div>
                                    <div>
                                        <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Advisor Megjegyzés / Specifikus Utasítás</label>
                                        <input type="text" id="advisorOverrideNotes" value="${c.advisor_notes || ''}" placeholder="pl. Ügyfél csendes szobát kér a felső emeleten" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px;">
                                    </div>
                                </div>
                            </div>

                        </div>
                    </form>

                    <!-- Jobb Oszlop: Élő Preferencia-Hierarchia Inspector -->
                    <div style="display: flex; flex-direction: column; gap: 14px;">
                        <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px;">
                            <div style="font-size: 11px; font-weight: 700; color: var(--secondary-container); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; font-family: var(--font-mono);">
                                Öröklési Hierarchia
                            </div>
                            <div style="font-size: 12px; color: var(--text-secondary); line-height: 1.6;">
                                <div style="margin-bottom: 6px;"><strong>1. Ügyfél Alapprofil:</strong> ${cl.name || 'Alap'} (${cl.preferences?.hotel_min_stars || 3}★, ${cl.preferences?.hotel_min_rating || 7.5}+)</div>
                                <div style="margin-bottom: 6px; color: var(--secondary-container);"><strong>2. Ügy Brief Felülírás:</strong> Aktív</div>
                                <div style="color: #4ade80;"><strong>3. Végső Számított Szabályok:</strong> 100% Validált</div>
                            </div>
                        </div>

                        <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 12px; padding: 18px; font-size: 12px;">
                            <div style="font-weight: 700; color: #fff; margin-bottom: 8px; font-family: var(--font-display);">Gyors Tipp</div>
                            <div style="color: var(--text-secondary); line-height: 1.5;">
                                A mentés után a rendszer azonnal lefuttatja a többcélú döntéstámogató motort és az élő járat- és szállásaggregációt a megadott korlátokkal.
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        renderBudgetInputs(mode, c) {
            if (mode === 'total') {
                return `
                    <div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Teljes Összbüdzsé (Ft):</label>
                            <strong id="briefTotalBudgetDisp" style="color: var(--secondary-container); font-family: var(--font-mono);">${(c.total_budget_huf || 500000).toLocaleString()} Ft</strong>
                        </div>
                        <input type="number" id="briefTotalBudgetInput" value="${c.total_budget_huf || 500000}" step="10000" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px; font-family:var(--font-mono);" oninput="document.getElementById('briefTotalBudgetDisp').innerText = parseInt(this.value||0).toLocaleString() + ' Ft';">
                    </div>
                `;
            } else if (mode === 'component') {
                return `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div>
                            <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Max. Repjegy Keret (Ft)</label>
                            <input type="number" id="briefFlightBudget" value="${c.flight_budget_huf || 90000}" step="5000" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px; font-family:var(--font-mono);">
                        </div>
                        <div>
                            <label class="form-label" style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary);">Max. Szállás Keret (Ft)</label>
                            <input type="number" id="briefStayBudget" value="${c.stay_budget_huf || 250000}" step="10000" class="form-control" style="width:100%; background:var(--b2b-surface); border-color:var(--b2b-border); color:#fff; padding:8px; border-radius:8px; font-family:var(--font-mono);">
                        </div>
                    </div>
                `;
            } else {
                return `
                    <div style="padding: 12px; background: rgba(167, 245, 64, 0.08); border-radius: 8px; color: var(--secondary-container); font-size: 12px;">
                        Nincs kötelező felső költségplafon. A keresőmotor a több szempont szerint leginkább optimalizált kombinációkat fogja bemutatni.
                    </div>
                `;
            }
        }

        setBudgetMode(mode) {
            this.activeCase.budget_mode = mode;
            const container = document.getElementById('budgetInputsContainer');
            if (container) {
                container.innerHTML = this.renderBudgetInputs(mode, this.activeCase);
            }

            ['total', 'component', 'scope_only'].forEach(m => {
                const el = document.getElementById(`bMode${m.charAt(0).toUpperCase() + m.slice(1)}`) || document.getElementById(`bMode${m === 'scope_only' ? 'Scope' : (m === 'total' ? 'Total' : 'Component')}`);
                if (el) {
                    el.style.borderColor = (m === mode) ? 'var(--secondary-container)' : 'var(--b2b-border)';
                    el.style.background = (m === mode) ? 'rgba(167, 245, 64, 0.1)' : 'var(--b2b-surface)';
                }
            });
        }

        async saveBrief(triggerResearch = false) {
            const caseId = this.activeCaseId;
            const budgetMode = this.activeCase.budget_mode || 'total';

            let totalBudget = null;
            let flightBudget = null;
            let stayBudget = null;

            if (budgetMode === 'total') {
                totalBudget = parseFloat(document.getElementById('briefTotalBudgetInput')?.value || 500000);
            } else if (budgetMode === 'component') {
                flightBudget = parseFloat(document.getElementById('briefFlightBudget')?.value || 90000);
                stayBudget = parseFloat(document.getElementById('briefStayBudget')?.value || 250000);
            }

            const origin = document.getElementById('briefOrigin')?.value || 'BUD';
            const dest = document.getElementById('briefDest')?.value || 'London';
            const duration = parseInt(document.getElementById('briefDuration')?.value || 4, 10);
            const adults = parseInt(document.getElementById('briefAdults')?.value || 2, 10);
            const children = parseInt(document.getElementById('briefChildren')?.value || 0, 10);

            const minStars = parseInt(document.getElementById('briefMinStars')?.value || 3, 10);
            const minRating = parseFloat(document.getElementById('briefMinRating')?.value || 8.0);
            const directOnly = !!document.getElementById('briefDirectOnly')?.checked;
            const breakfast = !!document.getElementById('briefBreakfast')?.checked;
            const pool = !!document.getElementById('briefPool')?.checked;
            const central = !!document.getElementById('briefCentral')?.checked;

            try {
                const res = await window.AdvisorAPI.request(`/cases/${caseId}/brief`, {
                    method: 'PUT',
                    body: JSON.stringify({
                        budget_mode: budgetMode,
                        total_budget_huf: totalBudget,
                        flight_budget_huf: flightBudget,
                        stay_budget_huf: stayBudget,
                        origin: origin,
                        destination_focus: dest,
                        duration_days: duration,
                        adults: adults,
                        children: children,
                        hard_constraints: {
                            max_total_budget_huf: totalBudget,
                            max_flight_budget_huf: flightBudget,
                            max_stay_budget_huf: stayBudget,
                            direct_flights_only: directOnly,
                            min_hotel_stars: minStars,
                            min_hotel_rating: minRating
                        },
                        nice_to_have: {
                            breakfast_included: breakfast,
                            pool_available: pool,
                            central_location: central
                        }
                    })
                });

                if (res.status === 'success') {
                    await window.AdvisorState.refreshCases();

                    if (triggerResearch && window.AdvisorResearch) {
                        window.AdvisorAPI.showToast(`Brief elmentve! Kutatás indítása: ${dest}...`, 'success');
                        window.AdvisorResearch.openCaseResearch(this.activeCaseId);
                    } else {
                        window.AdvisorAPI.showToast('Brief sikeresen elmentve!', 'success');
                    }
                }
            } catch (err) {
                window.AdvisorAPI.showToast(`Hiba a brief mentésekor: ${err.message}`, 'error');
            }
        }
                window.AdvisorAPI.showToast(`Hiba a brief mentésekor: ${err.message}`, 'error');
            }
        }
    }

    window.AdvisorBrief = new AdvisorBriefManager();
})();
