/**
 * Optivoya Advisor Workspace v2 — Candidate Pool & Provenance Explorer (Phase 3)
 * ==============================================================================
 * Renders the multi-tier Candidate Pool Explorer:
 * 1. Filter tabs for Flights, Stays, POIs/Experiences, and Packages.
 * 2. Detailed LocationScore badges with walkability, transit, and central proximity breakdown.
 * 3. Live Verification Provenance badges (Kiwi, Cozycozy, Open-Meteo, Places KG).
 * 4. Candidate pinning, component inspection, and smooth transition to Decision Phase.
 */

window.AdvisorCandidatePoolV2 = (() => {
    let currentCaseId = null;
    let poolData = null;
    let activeTab = 'all'; // 'all', 'flights', 'stays', 'experiences', 'packages'
    let searchQuery = '';
    let sortBy = 'location_score'; // 'location_score', 'price_asc', 'price_desc', 'rating'
    let isLoading = false;

    /**
     * Initializes and loads the Candidate Pool for the given Case.
     */
    async function loadCandidatePool(caseId, forceRegenerate = false) {
        currentCaseId = caseId;
        const container = document.getElementById('candidatePoolExplorerContainer');
        if (!container) return;

        isLoading = true;
        renderLoading(container);

        try {
            const url = forceRegenerate 
                ? `/api/advisor/cases/${caseId}/candidate-pool/generate`
                : `/api/advisor/cases/${caseId}/candidate-pool?auto_generate=true`;
            
            const method = forceRegenerate ? 'POST' : 'GET';
            const res = await window.AdvisorAPI.fetchWithAuth(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: forceRegenerate ? JSON.stringify({ custom_params: {} }) : undefined
            });

            if (!res.ok) {
                container.innerHTML = `
                    <div style="padding: 20px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; color: #fca5a5; font-size: 13px;">
                        Nem sikerült betölteni a jelölt készletet (Candidate Pool).
                    </div>
                `;
                return;
            }

            poolData = await res.json();
            isLoading = false;
            renderPoolView();
        } catch (err) {
            console.error('[AdvisorCandidatePoolV2] Error loading pool:', err);
            isLoading = false;
            container.innerHTML = `
                <div style="padding: 20px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; color: #fca5a5; font-size: 13px;">
                    Hiba történt: ${err.message}
                </div>
            `;
        }
    }

    /**
     * Loading spinner state.
     */
    function renderLoading(container) {
        container.innerHTML = `
            <div style="background: var(--b2b-card); border: 1px solid var(--b2b-border); border-radius: 14px; padding: 40px 20px; text-align: center;">
                <span class="material-symbols-outlined" style="font-size: 40px; color: var(--secondary-container); animation: spin 1s linear infinite;">sync</span>
                <h4 style="margin: 16px 0 6px 0; color: #fff; font-family: var(--font-display);">Kandidátus Készlet Feltárása & Hitelesítése...</h4>
                <p style="margin: 0; color: var(--text-secondary); font-size: 13px;">Párhuzamos lekérdezés a járat-, szállás- és élményforrásokból LocationScore kalkulációval.</p>
            </div>
        `;
    }

    /**
     * Main Renderer for the Candidate Pool Explorer.
     */
    function renderPoolView() {
        const container = document.getElementById('candidatePoolExplorerContainer');
        if (!container || !poolData) return;

        const counts = poolData.counts || {};
        const pool = poolData.candidate_pool || {};
        const verif = poolData.verification_summary || {};

        const flights = pool.flights || [];
        const stays = pool.stays || [];
        const experiences = pool.experiences || [];
        const packages = pool.packages || [];
        const destinations = pool.destinations || [];

        // Filter and Sort active items
        const visibleItems = getFilteredAndSortedItems(flights, stays, experiences, packages, destinations);

        container.innerHTML = `
            <div class="candidate-pool-panel" style="background: var(--b2b-card); border: 1px solid rgba(167, 245, 64, 0.25); border-radius: 14px; padding: 22px; margin-bottom: 24px; box-shadow: 0 8px 24px rgba(0,0,0,0.3);">
                
                <!-- Header Banner -->
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 18px; border-bottom: 1px solid var(--b2b-border); padding-bottom: 16px; flex-wrap: wrap;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                            <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; background: rgba(167, 245, 64, 0.12); color: var(--secondary-container); border: 1px solid rgba(167, 245, 64, 0.3); padding: 3px 8px; border-radius: 6px; font-family: var(--font-mono);">
                                Phase 3: Candidate Pool & Hitelesítés
                            </span>
                            <span style="font-size: 11px; font-weight: 600; font-family: var(--font-mono); color: #4ade80; background: rgba(74, 222, 128, 0.1); padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(74, 222, 128, 0.25); display: flex; align-items: center; gap: 4px;">
                                <span class="material-symbols-outlined" style="font-size: 14px;">verified</span>
                                ${verif.verified_count || (flights.length + stays.length)} Ellenőrizve (${verif.estimated_count || 0} becsült)
                            </span>
                        </div>
                        <h3 style="margin: 0 0 6px 0; font-size: 18px; font-family: var(--font-display); color: #fff; display: flex; align-items: center; gap: 8px;">
                            🧭 Készletkutató & Hitelesítési Explorer (Candidate Feed)
                        </h3>
                        <p style="margin: 0; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
                            Összesített komponens-készlet LocationScore minősítéssel, sétálhatósági indexekkel és élő forráshitelesítéssel.
                        </p>
                    </div>

                    <!-- Header Actions -->
                    <div style="display: flex; gap: 10px; align-items: center; flex-shrink: 0;">
                        <button type="button" onclick="window.AdvisorCandidatePoolV2.regeneratePool()" class="btn btn-secondary" style="font-size: 12.5px; padding: 8px 14px; display: flex; align-items: center; gap: 6px;">
                            <span class="material-symbols-outlined" style="font-size: 16px;">refresh</span>
                            Újra-pásztázás (Sweep)
                        </button>
                        <button type="button" onclick="window.AdvisorNavigation.navigate('options', { caseId: currentCaseId })" class="btn btn-primary" style="font-size: 12.5px; padding: 8px 16px; display: flex; align-items: center; gap: 6px; font-weight: 700;">
                            <span class="material-symbols-outlined" style="font-size: 16px;">auto_awesome</span>
                            Tovább a Döntési Opciókhoz (DECIDE) →
                        </button>
                    </div>
                </div>

                <!-- Filter Tabs & Quick Search Bar -->
                <div style="display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 18px; flex-wrap: wrap;">
                    
                    <!-- Tabs -->
                    <div style="display: flex; gap: 6px; background: var(--b2b-surface); padding: 4px; border-radius: 10px; border: 1px solid var(--b2b-border); overflow-x: auto;">
                        <button type="button" onclick="window.AdvisorCandidatePoolV2.setTab('all')" 
                            style="padding: 7px 12px; border-radius: 7px; border: none; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s ease; background: ${activeTab === 'all' ? 'var(--secondary-container)' : 'transparent'}; color: ${activeTab === 'all' ? 'var(--on-secondary-container)' : 'var(--text-secondary)'};">
                            Összes (${counts.destinations + counts.flights + counts.stays + counts.experiences})
                        </button>
                        <button type="button" onclick="window.AdvisorCandidatePoolV2.setTab('stays')" 
                            style="padding: 7px 12px; border-radius: 7px; border: none; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s ease; background: ${activeTab === 'stays' ? 'var(--secondary-container)' : 'transparent'}; color: ${activeTab === 'stays' ? 'var(--on-secondary-container)' : 'var(--text-secondary)'};">
                            🏨 Szállások (${counts.stays || 0})
                        </button>
                        <button type="button" onclick="window.AdvisorCandidatePoolV2.setTab('flights')" 
                            style="padding: 7px 12px; border-radius: 7px; border: none; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s ease; background: ${activeTab === 'flights' ? 'var(--secondary-container)' : 'transparent'}; color: ${activeTab === 'flights' ? 'var(--on-secondary-container)' : 'var(--text-secondary)'};">
                            🛫 Járatok (${counts.flights || 0})
                        </button>
                        <button type="button" onclick="window.AdvisorCandidatePoolV2.setTab('experiences')" 
                            style="padding: 7px 12px; border-radius: 7px; border: none; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s ease; background: ${activeTab === 'experiences' ? 'var(--secondary-container)' : 'transparent'}; color: ${activeTab === 'experiences' ? 'var(--on-secondary-container)' : 'var(--text-secondary)'};">
                            🏛️ Élmények (${counts.experiences || 0})
                        </button>
                        <button type="button" onclick="window.AdvisorCandidatePoolV2.setTab('packages')" 
                            style="padding: 7px 12px; border-radius: 7px; border: none; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s ease; background: ${activeTab === 'packages' ? 'var(--secondary-container)' : 'transparent'}; color: ${activeTab === 'packages' ? 'var(--on-secondary-container)' : 'var(--text-secondary)'};">
                            📦 Csomagok (${counts.packages || 0})
                        </button>
                    </div>

                    <!-- Search & Sort Controls -->
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <input type="text" placeholder="Keresés név, légitársaság vagy funkció szerint..." 
                            value="${searchQuery}" 
                            oninput="window.AdvisorCandidatePoolV2.onSearchChange(this.value)"
                            style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; padding: 7px 12px; color: #fff; font-size: 12.5px; width: 220px;">

                        <select onchange="window.AdvisorCandidatePoolV2.onSortChange(this.value)"
                            style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 8px; padding: 7px 10px; color: #fff; font-size: 12.5px;">
                            <option value="location_score" ${sortBy === 'location_score' ? 'selected' : ''}>LocationScore szerint</option>
                            <option value="price_asc" ${sortBy === 'price_asc' ? 'selected' : ''}>Ár (Legolcsóbb)</option>
                            <option value="price_desc" ${sortBy === 'price_desc' ? 'selected' : ''}>Ár (Prémium)</option>
                            <option value="rating" ${sortBy === 'rating' ? 'selected' : ''}>Értékelés szerint</option>
                        </select>
                    </div>
                </div>

                <!-- Component Cards Grid -->
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px;">
                    ${visibleItems.length === 0 ? `
                        <div style="grid-column: 1 / -1; padding: 30px; text-align: center; color: var(--text-muted); font-size: 13px; background: var(--b2b-surface); border-radius: 10px;">
                            Nincs a szűrésnek megfelelő elem ebben a kategóriában.
                        </div>
                    ` : visibleItems.map(item => renderItemCard(item)).join('')}
                </div>

            </div>
        `;
    }

    /**
     * Renders an individual Candidate Card (Flight, Stay, POI, Package, or Destination).
     */
    function renderItemCard(item) {
        const itemType = item._type || 'stay';
        const locScore = item.location_score || 88.0;
        const prov = item.provenance || {};
        const isVerified = (prov.verification_status === 'VERIFIED');
        const badgeText = item.location_score_badge || (locScore >= 90 ? 'Kiváló Lokáció' : 'Jó Minőség');

        if (itemType === 'stay') {
            const locDetails = item.location_details || {};
            const centerDist = locDetails.city_center_distance_km ? `${locDetails.city_center_distance_km} km a központtól` : 'Belvárosi';
            const walk = locDetails.walkability_score || 92;

            return `
                <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 10px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; gap: 12px; transition: all 0.2s ease;">
                    <div>
                        <!-- Top Type & Provenance Row -->
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: #fbbf24; background: rgba(251, 191, 36, 0.12); border: 1px solid rgba(251, 191, 36, 0.25); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">
                                🏨 SZÁLLÁS • ${'★'.repeat(item.stars || 4)}
                            </span>
                            <span style="font-size: 10px; font-weight: 600; color: ${isVerified ? '#4ade80' : '#fbbf24'}; background: ${isVerified ? 'rgba(74, 222, 128, 0.1)' : 'rgba(251, 191, 36, 0.1)'}; padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">
                                ${prov.provider || 'Cozycozy'} (${isVerified ? 'ÉLŐ' : 'BECSÜLT'})
                            </span>
                        </div>

                        <!-- Hotel Name & Rating -->
                        <div style="font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 4px; line-height: 1.3;">
                            ${item.name}
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">
                            ⭐ <strong>${item.rating_normalized || 8.8} / 10</strong> vendégértékelés • ${item.nights || 7} éj
                        </div>

                        <!-- LocationScore Pill Box -->
                        <div style="background: rgba(167, 245, 64, 0.06); border: 1px solid rgba(167, 245, 64, 0.2); border-radius: 8px; padding: 8px 10px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <span style="font-size: 11px; font-weight: 700; color: var(--secondary-container);">${badgeText}</span>
                                <span style="font-size: 12px; font-weight: 800; font-family: var(--font-mono); color: #a7f540;">${locScore} / 100</span>
                            </div>
                            <div style="font-size: 10.5px; color: var(--text-secondary); display: flex; justify-content: space-between;">
                                <span>🚶 Séta: ${walk}%</span>
                                <span>📍 ${centerDist}</span>
                                <span>🚇 Metró: ${locDetails.nearest_metro_min || 3}p</span>
                            </div>
                        </div>

                        <!-- Amenities -->
                        <div style="font-size: 11px; color: var(--text-muted); display: flex; flex-wrap: wrap; gap: 4px;">
                            ${(item.amenities || []).slice(0, 3).map(a => `<span style="background: rgba(255,255,255,0.04); padding: 2px 5px; border-radius: 3px;">${a}</span>`).join('')}
                        </div>
                    </div>

                    <!-- Bottom Price & Pin Button -->
                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--b2b-border); padding-top: 10px;">
                        <div>
                            <div style="font-size: 15px; font-weight: 700; font-family: var(--font-mono); color: #fff;">
                                ${Number(item.price_total_huf || 180000).toLocaleString()} Ft
                            </div>
                            <div style="font-size: 10.5px; color: var(--text-muted);">~${Number(item.price_per_night_huf || 25000).toLocaleString()} Ft / éj</div>
                        </div>
                        <button type="button" onclick="window.AdvisorCandidatePoolV2.pinComponent('stay', '${item.id}')" class="btn btn-secondary" style="font-size: 11px; padding: 4px 8px;">
                            <span class="material-symbols-outlined" style="font-size: 14px; margin-right: 3px;">push_pin</span> Rögzítés
                        </button>
                    </div>
                </div>
            `;
        }

        if (itemType === 'flight') {
            const isDirect = item.is_direct || (item.stops === 0);
            return `
                <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 10px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; gap: 12px; transition: all 0.2s ease;">
                    <div>
                        <!-- Top Type & Provenance Row -->
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: #38bdf8; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.25); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">
                                🛫 REPÜLŐJÁRAT • ${isDirect ? 'KÖZVETLEN' : item.stops + ' ÁTSZÁLLÁS'}
                            </span>
                            <span style="font-size: 10px; font-weight: 600; color: #4ade80; background: rgba(74, 222, 128, 0.1); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">
                                ${prov.provider || 'Kiwi.com'} (ÉLŐ)
                            </span>
                        </div>

                        <!-- Airline & Route -->
                        <div style="font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 4px;">
                            ${item.airline}
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; font-family: var(--font-mono);">
                            ${item.origin} → ${item.destination} (${item.out_duration_h || 2.4}h)
                        </div>

                        <!-- LocationScore / Airport Convenience -->
                        <div style="background: rgba(56, 189, 248, 0.06); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 8px 10px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 11px; font-weight: 700; color: #38bdf8;">Menetrendi Kényelem</span>
                                <span style="font-size: 12px; font-weight: 800; font-family: var(--font-mono); color: #38bdf8;">${locScore} / 100</span>
                            </div>
                            <div style="font-size: 10.5px; color: var(--text-secondary); margin-top: 3px;">
                                ${isDirect ? '✓ Nincs átszállási kockázat • Ideális nappali sáv' : 'Mérsékelt átszállási idő'}
                            </div>
                        </div>
                    </div>

                    <!-- Bottom Price & Pin Button -->
                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--b2b-border); padding-top: 10px;">
                        <div>
                            <div style="font-size: 15px; font-weight: 700; font-family: var(--font-mono); color: #fff;">
                                ${Number(item.price_total_huf || 75000).toLocaleString()} Ft
                            </div>
                            <div style="font-size: 10.5px; color: var(--text-muted);">~${Number(item.price_per_person_huf || 37500).toLocaleString()} Ft / fő</div>
                        </div>
                        <button type="button" onclick="window.AdvisorCandidatePoolV2.pinComponent('flight', '${item.id}')" class="btn btn-secondary" style="font-size: 11px; padding: 4px 8px;">
                            <span class="material-symbols-outlined" style="font-size: 14px; margin-right: 3px;">push_pin</span> Rögzítés
                        </button>
                    </div>
                </div>
            `;
        }

        if (itemType === 'experience') {
            return `
                <div style="background: var(--b2b-surface); border: 1px solid var(--b2b-border); border-radius: 10px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; gap: 12px; transition: all 0.2s ease;">
                    <div>
                        <!-- Top Type Row -->
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: #a78bfa; background: rgba(167, 139, 250, 0.12); border: 1px solid rgba(167, 139, 250, 0.25); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">
                                🏛️ ÉLMÉNY • ${item.category?.toUpperCase() || 'KULTÚRA'}
                            </span>
                            <span style="font-size: 10px; font-weight: 600; color: #a78bfa; background: rgba(167, 139, 250, 0.1); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">
                                Places KG
                            </span>
                        </div>

                        <!-- Experience Name -->
                        <div style="font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 4px; line-height: 1.3;">
                            ${item.name}
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">
                            ⭐ <strong>${item.rating || 4.7}</strong> értékelés • ~${item.duration_h || 2.5} óra időtartam
                        </div>

                        <div style="background: rgba(167, 139, 250, 0.06); border: 1px solid rgba(167, 139, 250, 0.2); border-radius: 8px; padding: 8px 10px;">
                            <div style="font-size: 11px; font-weight: 700; color: #a78bfa;">${item.location_score_badge || 'Kiemelt Program'}</div>
                            <div style="font-size: 10.5px; color: var(--text-secondary); margin-top: 2px;">
                                Várható költség: ~${item.estimated_cost_eur ? item.estimated_cost_eur + ' €' : 'Ingyenes'}
                            </div>
                        </div>
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--b2b-border); padding-top: 10px;">
                        <span style="font-size: 11px; color: #4ade80;">✓ Útitervbe illeszthető</span>
                        <button type="button" onclick="window.AdvisorCandidatePoolV2.pinComponent('experience', '${item.id}')" class="btn btn-secondary" style="font-size: 11px; padding: 4px 8px;">
                            Hozzáadás
                        </button>
                    </div>
                </div>
            `;
        }

        // Packages Fallback
        return `
            <div style="background: var(--b2b-surface); border: 1px solid rgba(167, 245, 64, 0.3); border-radius: 10px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; gap: 12px;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--secondary-container); background: rgba(167, 245, 64, 0.12); border: 1px solid rgba(167, 245, 64, 0.25); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono);">
                            📦 CSOMAG ARCHETÍPUS
                        </span>
                        <span style="font-size: 12px; font-weight: 800; font-family: var(--font-mono); color: #a7f540;">
                            TripScore: ${item.trip_score || 88}
                        </span>
                    </div>
                    <div style="font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 4px;">
                        ${item.title || 'Optimalizált Utazási Csomag'}
                    </div>
                    <div style="font-size: 12px; color: var(--text-secondary);">
                        ${item.tagline || 'Kiegyensúlyozott járat és belvárosi szállás'}
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--b2b-border); padding-top: 10px;">
                    <div style="font-size: 15px; font-weight: 700; font-family: var(--font-mono); color: #fff;">
                        ${Number(item.total_price_huf || 250000).toLocaleString()} Ft
                    </div>
                    <button type="button" onclick="window.AdvisorNavigation.navigate('options', { caseId: currentCaseId })" class="btn btn-primary" style="font-size: 11px; padding: 4px 10px;">
                        Kiválasztás →
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Filters and sorts items based on current active tab, search text, and sort criteria.
     */
    function getFilteredAndSortedItems(flights, stays, experiences, packages, destinations) {
        let items = [];

        if (activeTab === 'all') {
            items = [
                ...stays.map(s => ({ ...s, _type: 'stay' })),
                ...flights.map(f => ({ ...f, _type: 'flight' })),
                ...experiences.map(e => ({ ...e, _type: 'experience' })),
                ...packages.map(p => ({ ...p, _type: 'package' }))
            ];
        } else if (activeTab === 'stays') {
            items = stays.map(s => ({ ...s, _type: 'stay' }));
        } else if (activeTab === 'flights') {
            items = flights.map(f => ({ ...f, _type: 'flight' }));
        } else if (activeTab === 'experiences') {
            items = experiences.map(e => ({ ...e, _type: 'experience' }));
        } else if (activeTab === 'packages') {
            items = packages.map(p => ({ ...p, _type: 'package' }));
        }

        // Search Filter
        if (searchQuery.trim()) {
            const q = searchQuery.toLowerCase();
            items = items.filter(it => {
                const name = (it.name || it.title || it.airline || '').toLowerCase();
                const city = (it.city || it.destination || '').toLowerCase();
                return name.includes(q) || city.includes(q);
            });
        }

        // Sorting
        items.sort((a, b) => {
            if (sortBy === 'location_score') {
                return (b.location_score || b.trip_score || 0) - (a.location_score || a.trip_score || 0);
            } else if (sortBy === 'price_asc') {
                return (a.price_total_huf || a.total_price_huf || 0) - (b.price_total_huf || b.total_price_huf || 0);
            } else if (sortBy === 'price_desc') {
                return (b.price_total_huf || b.total_price_huf || 0) - (a.price_total_huf || a.total_price_huf || 0);
            } else if (sortBy === 'rating') {
                return (b.rating_normalized || b.rating || 0) - (a.rating_normalized || a.rating || 0);
            }
            return 0;
        });

        return items;
    }

    /**
     * Tab Switcher Handler
     */
    function setTab(tabName) {
        activeTab = tabName;
        renderPoolView();
    }

    /**
     * Search Input Handler
     */
    function onSearchChange(val) {
        searchQuery = val;
        renderPoolView();
    }

    /**
     * Sort Change Handler
     */
    function onSortChange(val) {
        sortBy = val;
        renderPoolView();
    }

    /**
     * Re-runs live sweep / pool generation.
     */
    async function regeneratePool() {
        if (!currentCaseId) return;
        await loadCandidatePool(currentCaseId, true);
        if (window.AdvisorToast) {
            window.AdvisorToast('Kandidátus készlet sikeresen újra-pásztázva!', 'success');
        }
    }

    /**
     * Pins a specific candidate component into Advisor Overrides.
     */
    async function pinComponent(type, id) {
        if (!currentCaseId) return;
        try {
            await window.AdvisorAPI.fetchWithAuth(`/api/advisor/cases/${currentCaseId}/candidates/pin`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate_id: id,
                    component_type: type,
                    is_pinned: true
                })
            });
            if (window.AdvisorToast) {
                window.AdvisorToast(`${type.toUpperCase()} elem sikeresen rögzítve az ügyhöz!`, 'info');
            }
        } catch (err) {
            console.error('Error pinning component:', err);
        }
    }

    return {
        loadCandidatePool,
        setTab,
        onSearchChange,
        onSortChange,
        regeneratePool,
        pinComponent
    };
})();
