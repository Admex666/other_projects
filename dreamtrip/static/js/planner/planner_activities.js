/**
 * Optivoya — Master Planner Activities & Experiences Module (Step 4)
 * Handles interactive program selection, category filtering, duration & cost estimation,
 * and passes selected programs to the final itinerary and budget breakdown (Step 5).
 */

(function () {
    const PlannerActivities = {
        allActivities: [],
        currentCategory: 'all',
        isLoading: false,

        getPriceEstimateHuf(priceLevel) {
            // Realistic European activity price estimation in HUF
            switch (String(priceLevel).toLowerCase()) {
                case 'free':
                case '0':
                    return 0;
                case 'budget':
                case '1':
                    return 2500;   // ~6 EUR
                case 'moderate':
                case '2':
                    return 6500;   // ~16 EUR
                case 'premium':
                case '3':
                case '4':
                    return 18000;  // ~45 EUR
                default:
                    return 3500;
            }
        },

        getPriceLabel(priceLevel) {
            switch (String(priceLevel).toLowerCase()) {
                case 'free':
                case '0':
                    return '<span style="color: #10b981; font-weight: 700;">Ingyenes (0 Ft)</span>';
                case 'budget':
                case '1':
                    return '<span style="color: #38bdf8; font-weight: 700;">~2 500 Ft / fő</span>';
                case 'moderate':
                case '2':
                    return '<span style="color: #f59e0b; font-weight: 700;">~6 500 Ft / fő</span>';
                case 'premium':
                case '3':
                case '4':
                    return '<span style="color: #ec4899; font-weight: 700;">~18 000 Ft / fő</span>';
                default:
                    return '~3 500 Ft / fő';
            }
        },

        getCategoryBadge(category) {
            switch (category) {
                case 'culture_history':
                    return { label: 'Kultúra & Múzeum', icon: 'account_balance', color: '#6366f1', bg: 'rgba(99, 102, 241, 0.12)' };
                case 'food_market':
                    return { label: 'Gasztró & Piac', icon: 'restaurant', color: '#f97316', bg: 'rgba(249, 115, 22, 0.12)' };
                case 'nature_viewpoint':
                    return { label: 'Természet & Panoráma', icon: 'landscape', color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)' };
                case 'beach_coastal':
                    return { label: 'Tengerpart & Strand', icon: 'beach_access', color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.12)' };
                case 'active_adventure':
                    return { label: 'Aktív Kaland', icon: 'hiking', color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.12)' };
                default:
                    return { label: 'Városi Élmény', icon: 'attractions', color: '#64748b', bg: 'rgba(100, 116, 139, 0.12)' };
            }
        },

        async initActivities() {
            const state = window.PlannerState;
            if (!state) return;

            const d = state.selectedDest || (window.TripCart ? window.TripCart.getTrip()?.destination : null);
            const destId = d?.dest_id || d?.id || 'IT_BARI';

            const grid = document.getElementById('activitiesGrid');
            if (grid) {
                grid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">
                        <div style="display: inline-block; width: 32px; height: 32px; border: 3px solid var(--border-subtle); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 12px;"></div>
                        <div style="font-size: 15px; font-weight: 600;">Programok és autentikus élmények betöltése (${d?.name || destId})...</div>
                    </div>
                `;
            }

            this.isLoading = true;
            try {
                let formattedDestId = String(destId).toUpperCase();
                if (!formattedDestId.includes('_') && formattedDestId.length > 3) {
                    if (formattedDestId.includes('BARI')) formattedDestId = 'IT_BARI';
                    else if (formattedDestId.includes('ROM')) formattedDestId = 'IT_ROME';
                }

                const res = await fetch(`/api/destinations/${encodeURIComponent(formattedDestId)}/activities`);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                
                const recMap = {};
                if (data.recommended && Array.isArray(data.recommended)) {
                    data.recommended.forEach(r => {
                        recMap[r.entity_id] = r;
                    });
                }
                this.allActivities = (data.activities || []).map(a => {
                    const r = recMap[a.entity_id];
                    if (r) {
                        return { ...a, fit_score: r.fit_score, recommendation_reason: r.recommendation_reason };
                    }
                    return a;
                });
                this.allActivities.sort((x, y) => (y.fit_score || 0) - (x.fit_score || 0));

                // Ha még nincsenek kijelölt programok, alapértelmezetten jelöljük ki az ajánlott/flagship helyeket (max 8-10 db)
                if (!state.selectedActivities || state.selectedActivities.length === 0) {
                    const defaultSelected = this.allActivities
                        .filter(a => (a.fit_score && a.fit_score >= 80) || a.metadata?.quality_tier === 'flagship' || (a.rating >= 4.5 && a.review_count > 200))
                        .slice(0, 8);
                    
                    state.selectedActivities = defaultSelected.length > 0 
                        ? defaultSelected 
                        : this.allActivities.slice(0, 6);
                }

                this.renderActivities();
                this.updateSummaryBadge();
            } catch (err) {
                console.warn("Could not load activities:", err);
                if (grid) {
                    grid.innerHTML = `
                        <div style="grid-column: 1 / -1; text-align: center; padding: 30px; color: var(--text-secondary); background: var(--bg-surface-subtle); border-radius: 16px;">
                            <span class="material-symbols-outlined" style="font-size: 32px; color: var(--text-muted); margin-bottom: 8px;">explore_off</span>
                            <div style="font-size: 14px; font-weight: 600;">Az online élménykatalógus átmenetileg nem elérhető ehhez a városhoz.</div>
                            <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">A kész útiterv ettől függetlenül elkészül az alapértelmezett látnivalókkal!</div>
                            <button type="button" class="btn btn-primary" onclick="Wizard.goToStep(5)" style="margin-top: 16px;">Tovább a kész tervhez →</button>
                        </div>
                    `;
                }
            } finally {
                this.isLoading = false;
            }
        },

        filterCategory(cat) {
            this.currentCategory = cat;
            // Update filter chips styling
            document.querySelectorAll('.activity-filter-chip').forEach(chip => {
                if (chip.getAttribute('data-cat') === cat) {
                    chip.classList.add('active');
                } else {
                    chip.classList.remove('active');
                }
            });
            this.renderActivities();
        },

        toggleActivity(entityId) {
            const state = window.PlannerState;
            if (!state) return;

            const activity = this.allActivities.find(a => a.entity_id === entityId);
            if (!activity) return;

            if (!state.selectedActivities) state.selectedActivities = [];

            const idx = state.selectedActivities.findIndex(a => a.entity_id === entityId);
            if (idx >= 0) {
                state.selectedActivities.splice(idx, 1);
            } else {
                state.selectedActivities.push(activity);
            }

            this.updateSummaryBadge();
            this.updateCardCheckedUI(entityId, idx < 0);
        },

        selectAll() {
            const state = window.PlannerState;
            if (!state) return;
            state.selectedActivities = [...this.allActivities];
            this.renderActivities();
            this.updateSummaryBadge();
        },

        deselectAll() {
            const state = window.PlannerState;
            if (!state) return;
            state.selectedActivities = [];
            this.renderActivities();
            this.updateSummaryBadge();
        },

        updateCardCheckedUI(entityId, isChecked) {
            const card = document.getElementById(`act-card-${entityId}`);
            const checkbox = document.getElementById(`act-chk-${entityId}`);
            if (checkbox) checkbox.checked = isChecked;
            if (card) {
                if (isChecked) {
                    card.style.borderColor = 'var(--primary)';
                    card.style.background = 'var(--bg-surface)';
                    card.style.boxShadow = '0 4px 14px rgba(0, 55, 16, 0.08)';
                } else {
                    card.style.borderColor = 'var(--border-subtle)';
                    card.style.background = 'var(--bg-surface-subtle)';
                    card.style.boxShadow = 'none';
                }
            }
        },

        updateSummaryBadge() {
            const state = window.PlannerState;
            const selected = state?.selectedActivities || [];
            const countEl = document.getElementById('selectedActCount');
            const costEl = document.getElementById('selectedActCost');
            const totalPersons = (state?.intake?.adults || 2) + (state?.intake?.children || 0);

            let totalPerPersonHuf = 0;
            selected.forEach(a => {
                totalPerPersonHuf += this.getPriceEstimateHuf(a.price_level);
            });

            const totalGroupHuf = totalPerPersonHuf * totalPersons;

            if (countEl) {
                countEl.innerText = `${selected.length} db`;
            }
            if (costEl) {
                costEl.innerText = `${totalGroupHuf.toLocaleString()} Ft (~${totalPerPersonHuf.toLocaleString()} Ft / fő)`;
            }

            // Sync to TripStore/TripCart if available
            if (window.TripStore) {
                const trip = window.TripStore.getTrip();
                if (trip) {
                    if (!trip.activities) trip.activities = {};
                    trip.activities.selected_activities = selected;
                    trip.activities.total_cost_huf = totalGroupHuf;
                    trip.activities.cost_per_person_huf = totalPerPersonHuf;
                    window.TripStore.saveTrip(trip);
                }
            }
        },

        renderActivities() {
            const grid = document.getElementById('activitiesGrid');
            if (!grid) return;

            const state = window.PlannerState;
            const selectedIds = new Set((state?.selectedActivities || []).map(a => a.entity_id));

            let filtered = this.allActivities;
            if (this.currentCategory !== 'all') {
                filtered = filtered.filter(a => a.category === this.currentCategory);
            }

            if (filtered.length === 0) {
                grid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-secondary);">
                        <span class="material-symbols-outlined" style="font-size: 32px; color: var(--text-muted); margin-bottom: 8px;">filter_list_off</span>
                        <div style="font-size: 14px; font-weight: 600;">Ebben a kategóriában nem található program.</div>
                        <button type="button" class="btn btn-secondary btn-sm" onclick="PlannerActivities.filterCategory('all')" style="margin-top: 10px;">Összes kategória mutatása</button>
                    </div>
                `;
                return;
            }

            grid.innerHTML = filtered.map(a => {
                const isChecked = selectedIds.has(a.entity_id);
                const catBadge = this.getCategoryBadge(a.category);
                const priceLabel = this.getPriceLabel(a.price_level);
                const duration = a.est_duration_hours ? `~${a.est_duration_hours} óra` : '~1.5 óra';
                const tier = a.metadata?.quality_tier;
                const tierLabel = tier === 'flagship' ? '⭐ Kiemelt Zászlóshajó' : (tier === 'recommended' ? '✓ Ajánlott' : '');
                const img = a.image_urls && a.image_urls.length > 0 ? a.image_urls[0] : null;

                const cardBorder = isChecked ? 'var(--primary)' : 'var(--border-subtle)';
                const cardBg = isChecked ? 'var(--bg-surface)' : 'var(--bg-surface-subtle)';
                const cardShadow = isChecked ? '0 4px 14px rgba(0, 55, 16, 0.08)' : 'none';

                return `
                    <div id="act-card-${a.entity_id}" class="activity-picker-card" onclick="PlannerActivities.toggleActivity('${a.entity_id}')" style="background: ${cardBg}; border: 1.5px solid ${cardBorder}; border-radius: 16px; padding: 16px; cursor: pointer; transition: all 0.2s ease; display: flex; flex-direction: column; justify-content: space-between; position: relative; box-shadow: ${cardShadow};">
                        
                        <div>
                            <!-- TOP ROW: CHECKBOX & BADGES -->
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 10px;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <input type="checkbox" id="act-chk-${a.entity_id}" ${isChecked ? 'checked' : ''} onclick="event.stopPropagation(); PlannerActivities.toggleActivity('${a.entity_id}')" style="width: 18px; height: 18px; accent-color: var(--primary); cursor: pointer;">
                                    <span style="display: inline-flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 700; color: ${catBadge.color}; background: ${catBadge.bg}; padding: 3px 8px; border-radius: 6px;">
                                        <span class="material-symbols-outlined" style="font-size: 13px;">${catBadge.icon}</span>
                                        <span>${catBadge.label}</span>
                                    </span>
                                </div>
                                ${tierLabel ? `<span style="font-size: 10.5px; font-weight: 700; color: #d97706; background: rgba(217, 119, 6, 0.1); padding: 2px 7px; border-radius: 6px;">${tierLabel}</span>` : ''}
                            </div>

                            <!-- TITLE -->
                            <h4 style="font-size: 15px; font-weight: 800; color: var(--text-main); margin: 0 0 6px; line-height: 1.3;">${a.canonical_name}</h4>
                            
                            <!-- RATING & REVIEWS -->
                            <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">
                                <span style="display: inline-flex; align-items: center; gap: 2px; color: #f59e0b; font-weight: 700;">
                                    ★ ${(a.rating || 4.5).toFixed(1)}
                                </span>
                                <span>•</span>
                                <span>${(a.review_count || 150).toLocaleString()} értékelés</span>
                            </div>

                            ${a.recommendation_reason ? `
                            <div style="margin-bottom: 10px; font-size: 11px; font-weight: 700; color: var(--primary); background: rgba(37, 99, 235, 0.08); padding: 4px 8px; border-radius: 6px; border: 1px solid rgba(37, 99, 235, 0.2); display: flex; align-items: center; gap: 5px;">
                                <span class="material-symbols-outlined" style="font-size: 13px;">auto_awesome</span>
                                <span>${a.recommendation_reason}</span>
                            </div>
                            ` : ''}

                            <!-- DESCRIPTION -->
                            <p style="font-size: 12.5px; color: var(--text-muted); line-height: 1.4; margin: 0 0 14px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                                ${a.description || 'Autentikus helyi élmény és látogatásra érdemes kulturális célpont.'}
                            </p>
                        </div>

                        <!-- BOTTOM ROW: DURATION & PRICE ESTIMATE -->
                        <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px; border-top: 1px dashed var(--border-subtle); font-size: 12px;">
                            <span style="color: var(--text-secondary); display: inline-flex; align-items: center; gap: 4px;">
                                <span class="material-symbols-outlined" style="font-size: 14px;">schedule</span>
                                <span>${duration}</span>
                            </span>
                            <span style="font-size: 12.5px;">
                                ${priceLabel}
                            </span>
                        </div>
                    </div>
                `;
            }).join('');
        },

        proceedToSummary() {
            const state = window.PlannerState;
            if (state) {
                state.setStep(5);
            }
        }
    };

    window.PlannerActivities = PlannerActivities;
})();
