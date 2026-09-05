/**
 * Optivoya — Trip Drawer & Floating Bar UI Module
 * Handles floating trip bar slots, drawer modal rendering, interactive dining profile switches & toasts.
 */

(function () {
    const TripDrawer = {
        isBarHidden: false,

        getNextStepCTA(trip) {
            if (!trip) trip = window.TripStore ? window.TripStore.getTrip() : null;
            const d = trip?.destination;
            const f = trip?.flight?.selected_flight;
            const s = trip?.accommodation?.selected_accommodation;

            if (!d) {
                return {
                    step: 1,
                    text: 'Tervezés indítása / Célállomás →',
                    url: '/planner',
                    icon: '',
                    badge: '1. Lépés'
                };
            }

            if (!f) {
                return {
                    step: 2,
                    text: `Járatok keresése (${d.name}) →`,
                    url: '/planner?resume=flight',
                    icon: '',
                    badge: '2. Lépés'
                };
            }

            if (!s) {
                return {
                    step: 3,
                    text: 'Szállások keresése →',
                    url: '/planner?resume=stay',
                    icon: '',
                    badge: '3. Lépés'
                };
            }

            return {
                step: 4,
                text: 'Összesített terv →',
                url: '/planner?resume=summary',
                icon: '',
                badge: 'Ajánlatkész'
            };
        },

        render() {
            if (!window.TripStore || !window.TripCalculator) return;
            const trip = window.TripStore.getTrip();
            const d = trip.destination;
            const f = trip.flight?.selected_flight;
            const s = trip.accommodation?.selected_accommodation;

            const bar = document.getElementById('floatingTripBar');
            const drawerBody = document.getElementById('tripDrawerBody');
            const drawerTotal = document.getElementById('tripDrawerTotal');
            const barTotal = document.getElementById('tripBarTotal');
            const slotsGroup = document.getElementById('tripBarSlots');
            const nextBtn = document.getElementById('tripBarNextBtn');

            if (!bar) return;

            const hasItems = d || f || s;
            const reopenBtn = document.getElementById('tripFloatingReopenBtn');

            if (hasItems && !this.isBarHidden) {
                bar.classList.add('visible');
                document.body.classList.add('floating-bar-visible');
                if (reopenBtn) reopenBtn.classList.remove('visible');
            } else if (hasItems && this.isBarHidden) {
                bar.classList.remove('visible');
                document.body.classList.remove('floating-bar-visible');
                if (reopenBtn) reopenBtn.classList.add('visible');
            } else {
                bar.classList.remove('visible');
                document.body.classList.remove('floating-bar-visible');
                if (reopenBtn) reopenBtn.classList.remove('visible');
            }

            // 1. RENDER FLOATING BAR SLOTS
            if (slotsGroup) {
                let slotsHtml = '';

                // Célállomás Slot
                if (d) {
                    slotsHtml += `
                        <div class="trip-pill-slot active-filled" onclick="TripCart.goToPlannerStep('destination')">
                            <span>${d.name}</span>
                            <span style="font-size: 11px; opacity: 0.85;">(${d.duration || 7} nap, ${d.adults || 2} felnőtt)</span>
                        </div>
                    `;
                } else {
                    slotsHtml += `
                        <a href="/planner" class="trip-pill-slot empty-slot">
                            <span>+ Célállomás</span>
                        </a>
                    `;
                }

                // Járat Slot
                if (f) {
                    slotsHtml += `
                        <div class="trip-pill-slot active-filled" onclick="TripCart.goToPlannerStep('flight')">
                            <span>${f.airline} (${Math.round(f.price_total_huf || f.price_huf).toLocaleString()} Ft)</span>
                        </div>
                    `;
                } else if (d) {
                    slotsHtml += `
                        <a href="/planner?resume=flight" class="trip-pill-slot empty-slot" onclick="if(window.location.pathname.startsWith('/planner') && window.Wizard){ event.preventDefault(); window.Wizard.goToStep(2); }">
                            <span>+ Járat</span>
                        </a>
                    `;
                } else {
                    slotsHtml += `
                        <a href="/planner?resume=flight" class="trip-pill-slot empty-slot">
                            <span>+ Járat</span>
                        </a>
                    `;
                }

                // Szállás Slot
                if (s) {
                    slotsHtml += `
                        <div class="trip-pill-slot active-filled" onclick="TripCart.goToPlannerStep('stay')">
                            <span>${s.name} (${Math.round(s.price_total_huf || s.price_huf).toLocaleString()} Ft)</span>
                        </div>
                    `;
                } else if (f && d) {
                    slotsHtml += `
                        <a href="/planner?resume=stay" class="trip-pill-slot empty-slot" onclick="if(window.location.pathname.startsWith('/planner') && window.Wizard){ event.preventDefault(); window.Wizard.goToStep(3); }">
                            <span>+ Szállás</span>
                        </a>
                    `;
                } else if (d) {
                    slotsHtml += `
                        <a href="/planner?resume=stay" class="trip-pill-slot empty-slot" onclick="if(window.location.pathname.startsWith('/planner') && window.Wizard){ event.preventDefault(); window.Wizard.goToStep(3); }">
                            <span>+ Szállás</span>
                        </a>
                    `;
                } else {
                    slotsHtml += `
                        <a href="/planner?resume=stay" class="trip-pill-slot empty-slot">
                            <span>+ Szállás</span>
                        </a>
                    `;
                }

                slotsGroup.innerHTML = slotsHtml;
            }

            // 2. RENDER NEXT STEP CTA IN BAR
            const nextCta = this.getNextStepCTA(trip);
            if (nextBtn) {
                nextBtn.innerText = nextCta.text;
                if (window.location.pathname.startsWith('/planner') && window.Wizard) {
                    nextBtn.onclick = (e) => {
                        e.preventDefault();
                        if (nextCta.step === 2) window.Wizard.goToStep(2);
                        else if (nextCta.step === 3) window.Wizard.goToStep(3);
                        else if (nextCta.step === 4) window.Wizard.goToStep(4);
                        else window.Wizard.goToStep(1);
                    };
                    nextBtn.removeAttribute('href');
                } else {
                    if (nextCta.action === 'open_drawer') {
                        nextBtn.onclick = () => this.showDrawer();
                        nextBtn.removeAttribute('href');
                    } else {
                        nextBtn.onclick = null;
                        nextBtn.href = nextCta.url;
                    }
                }
            }

            // 3. RENDER TOTALS & BREAKDOWN
            const breakdown = window.TripCalculator.calculateBreakdown(trip);
            if (barTotal) {
                barTotal.innerText = breakdown.totalHuf > 0 ? `${breakdown.totalHuf.toLocaleString()} Ft` : '0 Ft';
            }
            if (drawerTotal) {
                drawerTotal.innerHTML = `
                    <span>${breakdown.totalHuf.toLocaleString()} Ft</span>
                    ${breakdown.totalPersons > 1 ? `<span style="font-size: 13px; font-weight: 600; color: var(--text-muted); display: block;">(~${breakdown.perPersonTotal.toLocaleString()} Ft / fő)</span>` : ''}
                `;
            }

            // 4. RENDER DRAWER BODY & STATUS STEPPER
            if (drawerBody) {
                let drawerHtml = `
                    <!-- STEP PROGRESS INDICATOR -->
                    <div class="trip-workflow-stepper">
                        <div class="step-node ${d ? 'completed' : 'active'}">
                            <span class="step-num">${d ? '✓' : '1'}</span>
                            <span class="step-label">Célállomás</span>
                        </div>
                        <div class="step-connector ${f ? 'completed' : ''}"></div>
                        <div class="step-node ${f ? 'completed' : (d ? 'active' : '')}">
                            <span class="step-num">${f ? '✓' : '2'}</span>
                            <span class="step-label">Járat</span>
                        </div>
                        <div class="step-connector ${s ? 'completed' : ''}"></div>
                        <div class="step-node ${s ? 'completed' : (f ? 'active' : '')}">
                            <span class="step-num">${s ? '✓' : '3'}</span>
                            <span class="step-label">Szállás</span>
                        </div>
                    </div>
                `;

                // A) DESTINATION CARD
                if (d) {
                    drawerHtml += `
                        <div class="trip-card-slot filled">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type">1. Kijelölt Célállomás</div>
                                <button type="button" class="trip-card-slot-remove" onclick="TripCart.removeDestination()">Eltávolítás</button>
                            </div>
                            <div class="trip-card-main-info">${d.name}, ${d.country}</div>
                            <div class="trip-card-sub-info">
                                Indulás: ${d.origin} • ${d.duration} nap (${d.adults} felnőtt${d.children > 0 ? `, ${d.children} gyerek` : ''})
                            </div>
                            ${d.explanation ? `<div style="font-size: 11.5px; color: var(--primary); margin-top: 4px;">${d.explanation}</div>` : ''}
                        </div>
                    `;
                } else {
                    drawerHtml += `
                        <div class="trip-card-slot">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type" style="color: var(--text-muted);">1. Célállomás</div>
                            </div>
                            <div class="trip-card-empty-action">
                                <a href="/planner">
                                    <span>+ Célállomás választása a Plannerben</span>
                                </a>
                            </div>
                        </div>
                    `;
                }

                // B) FLIGHT CARD
                if (f) {
                    drawerHtml += `
                        <div class="trip-card-slot filled">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type">2. Rögzített Repülőjegy</div>
                                <button type="button" class="trip-card-slot-remove" onclick="TripCart.removeFlight()">Eltávolítás</button>
                            </div>
                            <div class="trip-card-main-info">${f.airline || 'Légitársaság'} (Retúr járat)</div>
                            <div class="trip-card-sub-info">
                                ${f.out_date ? `Odaút: ${String(f.out_date).split('T')[0].split(' ')[0]}` : ''} ${f.in_date ? `• Visszaút: ${String(f.in_date).split('T')[0].split(' ')[0]}` : ''}
                                (${f.exact_stay_nights || f.stay_days || 7} éjszaka)
                            </div>
                            <div class="trip-card-price-badge">${Math.round(f.price_total_huf || f.price_huf || 0).toLocaleString()} Ft (${f.adults || 1} főre)</div>
                        </div>
                    `;
                } else {
                    drawerHtml += `
                        <div class="trip-card-slot">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type" style="color: var(--text-muted);">2. Járat kiválasztása</div>
                            </div>
                            <div class="trip-card-empty-action">
                                <a href="/planner?resume=flight">
                                    <span>+ Járat keresése és kiválasztása (${d ? d.name : 'Planner'})</span>
                                </a>
                            </div>
                        </div>
                    `;
                }

                // C) STAY CARD
                if (s) {
                    drawerHtml += `
                        <div class="trip-card-slot filled">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type">3. Rögzített Szállás</div>
                                <button type="button" class="trip-card-slot-remove" onclick="TripCart.removeStay()">Eltávolítás</button>
                            </div>
                            <div class="trip-card-main-info">${s.name} ${s.stars ? '★'.repeat(s.stars) : ''}</div>
                            <div class="trip-card-sub-info">
                                ${s.address || s.city} • ${s.nights} éjszaka ${s.rating ? `• Értékelés: ${s.rating}/10` : ''}
                            </div>
                            <div class="trip-card-price-badge">${Math.round(s.price_total_huf || s.price_huf).toLocaleString()} Ft</div>
                        </div>
                    `;
                } else {
                    drawerHtml += `
                        <div class="trip-card-slot">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type" style="color: var(--text-muted);">3. Szállás kiválasztása</div>
                            </div>
                            <div class="trip-card-empty-action">
                                <a href="/planner?resume=stay">
                                    <span>+ Szállás keresése és rögzítése</span>
                                </a>
                            </div>
                        </div>
                    `;
                }

                // D) MATHEMATICAL BREAKDOWN CARD
                if (breakdown.hasAny) {
                    const activeProf = trip.dining_profile || 'standard';
                    drawerHtml += `
                        <div class="trip-breakdown-card">
                            <div class="trip-breakdown-header">
                                <span>Tételes Költségkalkuláció</span>
                                <span style="font-size: 11px; font-weight: 600; color: var(--primary);">${breakdown.days} nap / ${breakdown.totalPersons} fő</span>
                            </div>

                            <!-- DINING PROFILE SELECTOR -->
                            <div style="margin-bottom: 12px; padding: 8px 10px; background: var(--bg-surface-subtle); border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
                                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px; display: flex; justify-content: space-between;">
                                    <span>Étkezési profil</span>
                                    <span style="color: var(--primary); font-size: 10.5px;">Válassz profilt</span>
                                </div>
                                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px;">
                                    <button type="button" onclick="TripCart.setDiningProfile('budget')" style="padding: 6px 8px; font-size: 11.5px; font-weight: 700; border-radius: var(--radius-sm); border: 1px solid ${activeProf === 'budget' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${activeProf === 'budget' ? 'var(--primary-light)' : 'var(--bg-surface)'}; color: ${activeProf === 'budget' ? 'var(--primary)' : 'var(--text-secondary)'}; cursor: pointer; transition: all 0.15s ease;">
                                        Takarékos
                                    </button>
                                    <button type="button" onclick="TripCart.setDiningProfile('standard')" style="padding: 6px 8px; font-size: 11.5px; font-weight: 700; border-radius: var(--radius-sm); border: 1px solid ${activeProf === 'standard' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${activeProf === 'standard' ? 'var(--primary-light)' : 'var(--bg-surface)'}; color: ${activeProf === 'standard' ? 'var(--primary)' : 'var(--text-secondary)'}; cursor: pointer; transition: all 0.15s ease;">
                                        Átlagos
                                    </button>
                                    <button type="button" onclick="TripCart.setDiningProfile('comfort')" style="padding: 6px 8px; font-size: 11.5px; font-weight: 700; border-radius: var(--radius-sm); border: 1px solid ${activeProf === 'comfort' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${activeProf === 'comfort' ? 'var(--primary-light)' : 'var(--bg-surface)'}; color: ${activeProf === 'comfort' ? 'var(--primary)' : 'var(--text-secondary)'}; cursor: pointer; transition: all 0.15s ease;">
                                        Kényelmes
                                    </button>
                                </div>
                            </div>

                            <div class="trip-breakdown-list">
                                ${breakdown.items.map(it => `
                                    <div class="breakdown-row">
                                        <div class="breakdown-left">
                                            <div class="breakdown-item-name">
                                                <span>${it.name}</span>
                                                <span class="breakdown-badge-tag">${it.badge}</span>
                                            </div>
                                            <div class="breakdown-formula">
                                                ${it.formula}
                                            </div>
                                        </div>
                                        <div class="breakdown-right">
                                            <div class="breakdown-amount">${it.amount.toLocaleString()} Ft</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }

                // E) SHORTLIST ALTERNATIVES (IF ANY)
                const flightShortlist = trip.flight?.shortlist || [];
                const stayShortlist = trip.accommodation?.shortlist || [];
                if (flightShortlist.length > 0 || stayShortlist.length > 0) {
                    drawerHtml += `
                        <div style="margin-top: 14px; padding: 12px; background: rgba(0,0,0,0.02); border-radius: 12px; border: 1px dashed rgba(0,0,0,0.1);">
                            <div style="font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">
                                ⭐ Megjelölt Alternatívák (Shortlist)
                            </div>
                            ${flightShortlist.map(fl => `
                                <div style="font-size: 12px; display: flex; justify-content: space-between; margin-bottom: 4px;">
                                    <span>✈️ ${fl.airline} (${fl.out_date})</span>
                                    <strong>${Math.round(fl.price_total_huf || fl.price_huf).toLocaleString()} Ft</strong>
                                </div>
                            `).join('')}
                            ${stayShortlist.map(st => `
                                <div style="font-size: 12px; display: flex; justify-content: space-between; margin-bottom: 4px;">
                                    <span>🏨 ${st.name}</span>
                                    <strong>${Math.round(st.price_total_huf || st.price_huf).toLocaleString()} Ft</strong>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }

                drawerBody.innerHTML = drawerHtml;
            }
        },

        hideBar() {
            this.isBarHidden = true;
            const bar = document.getElementById('floatingTripBar');
            const reopenBtn = document.getElementById('tripFloatingReopenBtn');
            if (bar) bar.classList.remove('visible');
            if (reopenBtn) reopenBtn.classList.add('visible');
        },

        showBar() {
            this.isBarHidden = false;
            const bar = document.getElementById('floatingTripBar');
            const reopenBtn = document.getElementById('tripFloatingReopenBtn');
            if (bar) bar.classList.add('visible');
            if (reopenBtn) reopenBtn.classList.remove('visible');
        },

        showDrawer() {
            const drawer = document.getElementById('tripDrawerBackdrop');
            if (drawer) {
                this.render();
                drawer.classList.add('open');
            }
        },

        hideDrawer() {
            const drawer = document.getElementById('tripDrawerBackdrop');
            if (drawer) drawer.classList.remove('open');
        },

        showToast(message, icon = '✨') {
            if (typeof document === 'undefined' || !document.body) return;
            const toast = document.createElement('div');
            toast.className = 'trip-cart-toast';
            toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
            document.body.appendChild(toast);
            setTimeout(() => { if (toast.classList) toast.classList.add('show'); }, 10);
            setTimeout(() => {
                if (toast.classList) toast.classList.remove('show');
                setTimeout(() => { if (toast.remove) toast.remove(); }, 300);
            }, 3000);
        },

        goToPlannerStep(step) {
            const trip = window.TripStore ? window.TripStore.getTrip() : null;
            if (window.location.pathname.startsWith('/planner') && window.Wizard) {
                if (step === 'flight') window.Wizard.goToStep(2);
                else if (step === 'stay') window.Wizard.goToStep(3);
                else if (step === 'summary') window.Wizard.goToStep(4);
                else window.Wizard.goToStep(1);
            } else {
                if (step === 'flight' && trip?.flight?.selected_flight) {
                    window.location.href = `/planner?resume=flight&change=flight`;
                } else {
                    window.location.href = `/planner?resume=${step}`;
                }
            }
        }
    };

    window.TripDrawer = TripDrawer;
})();
