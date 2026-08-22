/**
 * OPTIVOYA TRIP BUILDER / WORKSPACE CART CONTROLLER
 * Persistent across Destination Matcher, Flight Intelligence & Accommodation Intelligence
 */

(function() {
    const STORAGE_KEY = 'optivoya_trip_workspace';

    const TripCart = {
        getCart() {
            try {
                const raw = localStorage.getItem(STORAGE_KEY);
                return raw ? JSON.parse(raw) : { destination: null, flight: null, stay: null };
            } catch (e) {
                console.error("TripCart read error:", e);
                return { destination: null, flight: null, stay: null };
            }
        },

        saveCart(cart) {
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
                this.render();
            } catch (e) {
                console.error("TripCart save error:", e);
            }
        },

        setDestination(data) {
            const cart = this.getCart();
            cart.destination = {
                name: data.name,
                city: data.city || data.name,
                country: data.country || '',
                region: data.region || '',
                month: data.month || '9',
                duration: parseInt(data.duration, 10) || 7,
                adults: parseInt(data.adults, 10) || 2,
                children: parseInt(data.children, 10) || 0,
                origin: data.origin || 'Budapest',
                daily_cost_eur: data.daily_cost_eur || 45,
                flight_est_huf: data.flight_price_huf || null,
                image: data.image || ''
            };
            this.saveCart(cart);
            this.showToast(`📍 ${data.name} rögzítve az aktív utazási tervhez!`, '📍');
        },

        setFlight(data) {
            const cart = this.getCart();
            cart.flight = {
                airline: data.airline || 'Járat',
                price_huf: parseFloat(data.price_huf) || 0,
                out_date: data.out_date || '',
                in_date: data.in_date || '',
                out_time: data.out_time || '',
                in_time: data.in_time || '',
                duration_h: data.duration_h || 0,
                stops: data.stops !== undefined ? data.stops : 0,
                adults: parseInt(data.adults, 10) || 2
            };
            this.saveCart(cart);
            this.showToast(`✈️ ${data.airline} járat hozzáadva az utazáshoz!`, '✈️');
        },

        setStay(data) {
            const cart = this.getCart();
            cart.stay = {
                name: data.name || 'Szállás',
                price_huf: parseFloat(data.price_huf) || 0,
                rating: data.rating || 0,
                stars: data.stars || 0,
                address: data.address || '',
                image: data.image || '',
                nights: parseInt(data.nights, 10) || (cart.destination ? cart.destination.duration : 7),
                city: data.city || ''
            };
            this.saveCart(cart);
            this.showToast(`🏨 ${data.name} hozzáadva az utazáshoz!`, '🏨');
        },

        removeDestination() {
            const cart = this.getCart();
            cart.destination = null;
            this.saveCart(cart);
            this.showToast("Célállomás eltávolítva a tervből.", "🗑️");
        },

        removeFlight() {
            const cart = this.getCart();
            cart.flight = null;
            this.saveCart(cart);
            this.showToast("Járat eltávolítva a tervből.", "🗑️");
        },

        removeStay() {
            const cart = this.getCart();
            cart.stay = null;
            this.saveCart(cart);
            this.showToast("Szállás eltávolítva a tervből.", "🗑️");
        },

        clearCart() {
            if (confirm("Biztosan törölni szeretnéd az egész aktív utazási tervet?")) {
                localStorage.removeItem(STORAGE_KEY);
                this.render();
                this.showToast("Utazási terv kiürítve.", "🧹");
                this.hideDrawer();
            }
        },

        calculateTotal() {
            const cart = this.getCart();
            let totalHuf = 0;
            let hasAny = false;

            if (cart.flight && cart.flight.price_huf) {
                totalHuf += cart.flight.price_huf;
                hasAny = true;
            } else if (cart.destination && cart.destination.flight_est_huf) {
                totalHuf += cart.destination.flight_est_huf;
            }

            if (cart.stay && cart.stay.price_huf) {
                totalHuf += cart.stay.price_huf;
                hasAny = true;
            }

            // Napi költségkeret becslés ha van desztináció (kb. 395 Ft/EUR)
            if (cart.destination) {
                const days = cart.destination.duration || 7;
                const adults = cart.destination.adults || 2;
                const dailyEur = cart.destination.daily_cost_eur || 45;
                const spendingHuf = dailyEur * days * adults * 395;
                totalHuf += spendingHuf;
                hasAny = true;
            }

            return { totalHuf, hasAny };
        },

        render() {
            const cart = this.getCart();
            const bar = document.getElementById('floatingTripBar');
            const drawerBody = document.getElementById('tripDrawerBody');
            const drawerTotal = document.getElementById('tripDrawerTotal');
            const barTotal = document.getElementById('tripBarTotal');
            const slotsGroup = document.getElementById('tripBarSlots');

            if (!bar) return;

            const hasItems = cart.destination || cart.flight || cart.stay;
            const reopenBtn = document.getElementById('tripFloatingReopenBtn');

            if (hasItems && !this.isBarHidden) {
                bar.classList.add('visible');
                if (reopenBtn) reopenBtn.classList.remove('visible');
            } else if (hasItems && this.isBarHidden) {
                bar.classList.remove('visible');
                if (reopenBtn) reopenBtn.classList.add('visible');
            } else {
                bar.classList.remove('visible');
                if (reopenBtn) reopenBtn.classList.remove('visible');
            }

            // 1. RENDER FLOATING BAR SLOTS
            if (slotsGroup) {
                let slotsHtml = '';

                // Célállomás Slot
                if (cart.destination) {
                    slotsHtml += `
                        <div class="trip-pill-slot active-filled" onclick="TripCart.showDrawer()">
                            <span>📍 ${cart.destination.name}</span>
                            <span style="font-size: 11px; opacity: 0.8;">(${cart.destination.duration} nap, ${cart.destination.adults} felnőtt)</span>
                        </div>
                    `;
                } else {
                    slotsHtml += `
                        <a href="/destination-matcher" class="trip-pill-slot empty-slot">
                            <span>📍 + Célállomás választása</span>
                        </a>
                    `;
                }

                // Járat Slot
                if (cart.flight) {
                    slotsHtml += `
                        <div class="trip-pill-slot active-filled" onclick="TripCart.showDrawer()">
                            <span>✈️ ${cart.flight.airline} (${Math.round(cart.flight.price_huf).toLocaleString()} Ft)</span>
                        </div>
                    `;
                } else if (cart.destination) {
                    const d = cart.destination;
                    slotsHtml += `
                        <a href="/flight-intelligence?destination=${encodeURIComponent(d.city || d.name)}&origin=${encodeURIComponent(d.origin)}&adults=${d.adults}&children=${d.children}&duration=${d.duration}&from_matcher=1" class="trip-pill-slot empty-slot">
                            <span>✈️ + Járat választása</span>
                        </a>
                    `;
                } else {
                    slotsHtml += `
                        <a href="/flight-intelligence" class="trip-pill-slot empty-slot">
                            <span>✈️ + Járat választása</span>
                        </a>
                    `;
                }

                // Szállás Slot
                if (cart.stay) {
                    slotsHtml += `
                        <div class="trip-pill-slot active-filled" onclick="TripCart.showDrawer()">
                            <span>🏨 ${cart.stay.name} (${Math.round(cart.stay.price_huf).toLocaleString()} Ft)</span>
                        </div>
                    `;
                } else if (cart.destination) {
                    const d = cart.destination;
                    slotsHtml += `
                        <a href="/accommodation-intelligence?city=${encodeURIComponent(d.city || d.name)}&country=${encodeURIComponent(d.country)}&adults=${d.adults}&children=${d.children}&from_matcher=1" class="trip-pill-slot empty-slot">
                            <span>🏨 + Szállás választása</span>
                        </a>
                    `;
                } else {
                    slotsHtml += `
                        <a href="/accommodation-intelligence" class="trip-pill-slot empty-slot">
                            <span>🏨 + Szállás választása</span>
                        </a>
                    `;
                }

                slotsGroup.innerHTML = slotsHtml;
            }

            // 2. RENDER TOTALS
            const { totalHuf } = this.calculateTotal();
            if (barTotal) {
                barTotal.innerText = totalHuf > 0 ? `${Math.round(totalHuf).toLocaleString()} Ft` : '0 Ft';
            }
            if (drawerTotal) {
                drawerTotal.innerText = totalHuf > 0 ? `${Math.round(totalHuf).toLocaleString()} Ft` : '0 Ft';
            }

            // 3. RENDER DRAWER BODY
            if (drawerBody) {
                let drawerHtml = '';

                // A) DESTINATION CARD
                if (cart.destination) {
                    const d = cart.destination;
                    drawerHtml += `
                        <div class="trip-card-slot filled">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type">📍 Kijelölt Célállomás</div>
                                <button type="button" class="trip-card-slot-remove" onclick="TripCart.removeDestination()">Eltávolítás</button>
                            </div>
                            <div class="trip-card-main-info">${d.name}, ${d.country}</div>
                            <div class="trip-card-sub-info">
                                🛫 Indulás: ${d.origin} • 🗓️ ${d.duration} napos időszak (${d.adults} felnőtt, ${d.children || 0} gyerek)
                            </div>
                            <div style="font-size: 12px; color: var(--text-muted); margin-top: 6px;">
                                💰 Becsült napi költőpénz kosár: ~€${d.daily_cost_eur}/nap/fő
                            </div>
                        </div>
                    `;
                } else {
                    drawerHtml += `
                        <div class="trip-card-slot">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type" style="color: var(--text-muted);">📍 Célállomás</div>
                            </div>
                            <div class="trip-card-empty-action">
                                <a href="/destination-matcher">
                                    <span>+ Célállomás választása a Matcherben</span>
                                </a>
                            </div>
                        </div>
                    `;
                }

                // B) FLIGHT CARD
                if (cart.flight) {
                    const f = cart.flight;
                    drawerHtml += `
                        <div class="trip-card-slot filled">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type">✈️ Rögzített Repülőjegy</div>
                                <button type="button" class="trip-card-slot-remove" onclick="TripCart.removeFlight()">Eltávolítás</button>
                            </div>
                            <div class="trip-card-main-info">${f.airline} (Retúr járat)</div>
                            <div class="trip-card-sub-info">
                                ${f.out_date ? `🛫 Odaút: ${f.out_date}` : ''} ${f.in_date ? `• 🛬 Visszaút: ${f.in_date}` : ''}
                                ${f.stops === 0 ? '• Közvetlen járat' : '• Átszállással'}
                            </div>
                            <div class="trip-card-price-badge">${Math.round(f.price_huf).toLocaleString()} Ft (${f.adults} főre)</div>
                        </div>
                    `;
                } else {
                    drawerHtml += `
                        <div class="trip-card-slot">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type" style="color: var(--text-muted);">✈️ Repülőjegy</div>
                            </div>
                            <div class="trip-card-empty-action">
                                <a href="${cart.destination ? `/flight-intelligence?destination=${encodeURIComponent(cart.destination.city || cart.destination.name)}&origin=${encodeURIComponent(cart.destination.origin)}&adults=${cart.destination.adults}&duration=${cart.destination.duration}&from_matcher=1` : '/flight-intelligence'}">
                                    <span>+ Járat keresése és hozzáadása</span>
                                </a>
                            </div>
                        </div>
                    `;
                }

                // C) STAY CARD
                if (cart.stay) {
                    const s = cart.stay;
                    drawerHtml += `
                        <div class="trip-card-slot filled">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type">🏨 Rögzített Szállás</div>
                                <button type="button" class="trip-card-slot-remove" onclick="TripCart.removeStay()">Eltávolítás</button>
                            </div>
                            <div class="trip-card-main-info">${s.name} ${s.stars ? '⭐'.repeat(s.stars) : ''}</div>
                            <div class="trip-card-sub-info">
                                ${s.rating ? `Értékelés: ${s.rating}/10 • ` : ''} ${s.nights} éjszaka
                            </div>
                            <div class="trip-card-price-badge">${Math.round(s.price_huf).toLocaleString()} Ft</div>
                        </div>
                    `;
                } else {
                    drawerHtml += `
                        <div class="trip-card-slot">
                            <div class="trip-card-slot-header">
                                <div class="trip-card-slot-type" style="color: var(--text-muted);">🏨 Szállás</div>
                            </div>
                            <div class="trip-card-empty-action">
                                <a href="${cart.destination ? `/accommodation-intelligence?city=${encodeURIComponent(cart.destination.city || cart.destination.name)}&country=${encodeURIComponent(cart.destination.country)}&adults=${cart.destination.adults}&from_matcher=1` : '/accommodation-intelligence'}">
                                    <span>+ Szállás keresése és hozzáadása</span>
                                </a>
                            </div>
                        </div>
                    `;
                }

                drawerBody.innerHTML = drawerHtml;
            }
        },

        isBarHidden: false,

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

        showToast(msg, icon = '✅') {
            let toast = document.getElementById('tripToast');
            if (!toast) {
                toast = document.createElement('div');
                toast.id = 'tripToast';
                toast.className = 'trip-toast';
                document.body.appendChild(toast);
            }
            toast.innerHTML = `<span style="font-size: 18px;">${icon}</span><span>${msg}</span>`;
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3200);
        },

        exportProposal() {
            const cart = this.getCart();
            if (!cart.destination && !cart.flight && !cart.stay) {
                alert("Kérlek, válassz ki legalább egy célállomást vagy járatot az ajánlathoz!");
                return;
            }
            const { totalHuf } = this.calculateTotal();

            const win = window.open('', '_blank');
            win.document.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Utazási Ajánlat — Optivoya</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 40px; color: #1e293b; max-width: 800px; margin: 0 auto; line-height: 1.6; }
                        .header { border-bottom: 2px solid #2563eb; padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }
                        .title { font-size: 24px; font-weight: 800; color: #0f172a; margin: 0; }
                        .subtitle { font-size: 14px; color: #64748b; margin-top: 4px; }
                        .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px 22px; margin-bottom: 16px; }
                        .card-title { font-size: 13px; font-weight: 700; color: #2563eb; text-transform: uppercase; margin-bottom: 6px; }
                        .card-val { font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 4px; }
                        .total-box { background: #eff6ff; border: 2px solid #2563eb; border-radius: 14px; padding: 20px; text-align: right; margin-top: 24px; }
                        .total-num { font-size: 28px; font-weight: 800; color: #2563eb; font-family: monospace; }
                        @media print { button { display: none; } }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div>
                            <h1 class="title">Optivoya — Személyre Szabott Utazási Ajánlat</h1>
                            <div class="subtitle">Készült: ${new Date().toLocaleDateString('hu-HU')}</div>
                        </div>
                        <button onclick="window.print()" style="padding: 10px 18px; background: #2563eb; color: #fff; border: none; border-radius: 8px; font-weight: 700; cursor: pointer;">Nyomtatás / PDF</button>
                    </div>

                    ${cart.destination ? `
                    <div class="card">
                        <div class="card-title">📍 Célállomás & Időszak</div>
                        <div class="card-val">${cart.destination.name}, ${cart.destination.country}</div>
                        <div>Indulás: ${cart.destination.origin} • Időtartam: ${cart.destination.duration} nap (${cart.destination.adults} felnőtt)</div>
                    </div>` : ''}

                    ${cart.flight ? `
                    <div class="card">
                        <div class="card-title">✈️ Repülőjegy & Menetrend</div>
                        <div class="card-val">${cart.flight.airline} Retúr Járat</div>
                        <div>${cart.flight.out_date ? `Odaút: ${cart.flight.out_date}` : ''} ${cart.flight.in_date ? `• Visszaút: ${cart.flight.in_date}` : ''} (${cart.flight.adults} főre)</div>
                        <div style="margin-top: 8px; font-weight: 700; color: #2563eb;">${Math.round(cart.flight.price_huf).toLocaleString()} Ft</div>
                    </div>` : ''}

                    ${cart.stay ? `
                    <div class="card">
                        <div class="card-title">🏨 Szállás</div>
                        <div class="card-val">${cart.stay.name} ${cart.stay.stars ? '⭐'.repeat(cart.stay.stars) : ''}</div>
                        <div>${cart.stay.nights} éjszaka ${cart.stay.rating ? `• Értékelés: ${cart.stay.rating}/10` : ''}</div>
                        <div style="margin-top: 8px; font-weight: 700; color: #2563eb;">${Math.round(cart.stay.price_huf).toLocaleString()} Ft</div>
                    </div>` : ''}

                    <div class="total-box">
                        <div style="font-size: 13px; color: #64748b; font-weight: 700; text-transform: uppercase;">Teljes Becsült Költség (Repülő + Szállás + Napi keret):</div>
                        <div class="total-num">${Math.round(totalHuf).toLocaleString()} Ft</div>
                    </div>
                </body>
                </html>
            `);
            win.document.close();
        },

        init() {
            this.render();
        }
    };

    window.TripCart = TripCart;

    document.addEventListener('DOMContentLoaded', () => {
        TripCart.init();
    });
})();
