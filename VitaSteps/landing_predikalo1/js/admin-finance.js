// ===== ADMIN FINANCE & REVOLUT / STRIPE CASHFLOW MODULE =====

let finData = null;
let finPeriod = 'all'; // 'all', '30d', '7d', '2026-08', '2026-07', '2026-06', '2026-05'
let finAccount = 'all'; // 'all', 'revolut', 'stripe'
let finCategory = 'all';
let finSearchQuery = '';

async function loadFinance() {
    const cardsEl = document.getElementById('fin-cards');
    if (cardsEl) cardsEl.innerHTML = '<div class="empty-state"><span class="loading-spinner"></span><div style="margin-top:0.5rem">Pénzügyi és banki adatok betöltése...</div></div>';

    try {
        const res = await fetch(`/api/admin-data?type=finance&secret=${encodeURIComponent(adminSecret)}`);
        if (!res.ok) throw new Error('Nem sikerült betölteni a pénzügyi adatokat.');

        const data = await res.json();
        finData = data;
        renderFinance();

    } catch (error) {
        console.error('Finance load error:', error);
        if (cardsEl) cardsEl.innerHTML = `<div class="empty-state" style="color: var(--red);">❌ Hiba: ${error.message}</div>`;
    }
}

async function handleRevolutFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
        const csvContent = e.target.result;
        const cardsEl = document.getElementById('fin-cards');
        if (cardsEl) cardsEl.innerHTML = '<div class="empty-state"><span class="loading-spinner"></span><div style="margin-top:0.5rem">Revolut CSV feldolgozása...</div></div>';

        try {
            const res = await fetch('/api/admin-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ admin_secret: adminSecret, type: 'upload_revolut', csv_content: csvContent })
            });
            const resData = await res.json();
            if (res.ok) {
                alert(`Sikeres feltöltés! ${resData.count} db Revolut tranzakció sikeresen beolvasva.`);
                loadFinance();
            } else {
                alert('Hiba a feltöltés során: ' + (resData.error || 'Ismeretlen hiba'));
                loadFinance();
            }
        } catch (err) {
            alert('Feltöltési hiba: ' + err.message);
            loadFinance();
        }
    };
    reader.readAsText(file);
}

function setFinPeriod(period) {
    finPeriod = period;
    renderFinance();
}

function setFinAccount(acc) {
    finAccount = acc;
    renderFinance();
}

function setFinCategory(cat) {
    finCategory = cat;
    renderFinance();
}

function handleFinSearch(e) {
    finSearchQuery = e.target.value.toLowerCase().trim();
    renderFinance();
}

function renderFinance() {
    if (!finData) return;
    const cardsEl = document.getElementById('fin-cards');
    if (!cardsEl) return;

    // Extract Stripe
    const stripeAvail = (finData.stripe?.balance?.available || []).reduce((s, b) => b.currency.toLowerCase() === 'huf' ? s + (b.amount / 100) : s, 0);
    const stripePending = (finData.stripe?.balance?.pending || []).reduce((s, b) => b.currency.toLowerCase() === 'huf' ? s + (b.amount / 100) : s, 0);
    const stripeTxs = finData.stripe?.transactions || [];

    // Extract Revolut
    const revolutTxs = finData.revolut?.transactions || [];
    const revolutBal = finData.revolut?.currentBalance || 0;

    // Total liquid cash
    const totalLiquid = stripeAvail + revolutBal;

    // Date filtering helper
    const now = new Date();
    function matchPeriod(dateStr) {
        if (finPeriod === 'all') return true;
        if (!dateStr) return true;
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return true;

        if (finPeriod === '30d') {
            const past = new Date(now); past.setDate(now.getDate() - 30);
            return d >= past;
        }
        if (finPeriod === '7d') {
            const past = new Date(now); past.setDate(now.getDate() - 7);
            return d >= past;
        }
        if (finPeriod.startsWith('2026-')) {
            return dateStr.startsWith(finPeriod);
        }
        return true;
    }

    // Filtered transactions for the ledger table
    const unifiedLedger = [];

    // 1. Convert Revolut rows
    revolutTxs.forEach((r, idx) => {
        const dateStr = r.completedDate || r.startedDate;
        if (!matchPeriod(dateStr)) return;
        if (finAccount === 'stripe') return;
        if (finCategory !== 'all' && r.category !== finCategory) return;

        unifiedLedger.push({
            id: `rev-${idx}`,
            rawDate: dateStr,
            dateDisplay: dateStr ? new Date(dateStr).toLocaleString('hu-HU', { dateStyle: 'short', timeStyle: 'short' }) : '–',
            source: 'revolut',
            sourceLabel: '🔵 Revolut Pro',
            category: r.category,
            categoryLabel: r.categoryLabel,
            categoryColor: r.categoryColor,
            description: r.description || r.type,
            type: r.type,
            grossAmount: r.amount,
            fee: r.fee,
            netAmount: r.amount - r.fee,
            currency: r.currency,
            balance: r.balance
        });
    });

    // 2. Convert Stripe transactions
    stripeTxs.forEach((s) => {
        const dateStr = s.created ? new Date(s.created).toISOString().replace('T', ' ').substring(0, 19) : '';
        if (!matchPeriod(dateStr)) return;
        if (finAccount === 'revolut') return;

        let cat = 'direct_sale';
        let catLabel = '💳 Stripe Vásárlás';
        let catColor = '#22c55e';

        if (s.type === 'payout') {
            cat = 'stripe_payout';
            catLabel = '💸 Stripe Kiutalás';
            catColor = '#38bdf8';
        } else if (s.type === 'refund') {
            cat = 'refund';
            catLabel = '↩️ Visszatérítés';
            catColor = '#ef4444';
        } else if (s.type === 'stripe_fee') {
            cat = 'stripe_fee';
            catLabel = '🏦 Stripe Díj';
            catColor = '#94a3b8';
        }

        if (finCategory !== 'all' && cat !== finCategory && !(finCategory === 'stripe_payout' && cat === 'stripe_payout')) return;

        unifiedLedger.push({
            id: s.id,
            rawDate: dateStr,
            dateDisplay: dateStr ? new Date(s.created).toLocaleString('hu-HU', { dateStyle: 'short', timeStyle: 'short' }) : '–',
            source: 'stripe',
            sourceLabel: '🟢 Stripe',
            category: cat,
            categoryLabel: catLabel,
            categoryColor: catColor,
            description: s.description || (s.type === 'charge' ? 'Kártyás fizetés (Stripe Checkout)' : (s.type === 'payout' ? 'Automatikus bankszámla kifizetés' : s.type)),
            type: s.type,
            grossAmount: s.amount,
            fee: s.fee,
            netAmount: s.net,
            currency: s.currency,
            balance: null
        });
    });

    // Search filtering
    let displayLedger = unifiedLedger;
    if (finSearchQuery) {
        displayLedger = displayLedger.filter(t => 
            (t.description || '').toLowerCase().includes(finSearchQuery) ||
            (t.categoryLabel || '').toLowerCase().includes(finSearchQuery) ||
            (t.type || '').toLowerCase().includes(finSearchQuery) ||
            String(t.grossAmount).includes(finSearchQuery)
        );
    }

    displayLedger.sort((a, b) => new Date(b.rawDate || 0) - new Date(a.rawDate || 0));

    // Calculate Period Totals (Revolut Cashflow)
    const periodRevolut = revolutTxs.filter(r => matchPeriod(r.completedDate || r.startedDate));
    const periodInflow = periodRevolut.filter(r => r.amount > 0).reduce((s, r) => s + r.amount, 0);
    const periodOutflow = periodRevolut.filter(r => r.amount < 0).reduce((s, r) => s + r.amount, 0);

    const periodCatSummary = {};
    periodRevolut.forEach(r => {
        periodCatSummary[r.category] = (periodCatSummary[r.category] || 0) + r.amount;
    });

    let html = `
        <!-- Top Liquidity Grid -->
        <div class="fin-summary-grid">
            <div class="fin-card highlight">
                <div style="font-size: 0.75rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.05em; display: flex; justify-content: space-between;">
                    <span>💎 Összes Likvid Tőke</span>
                    <span style="font-size: 0.68rem; color: #38bdf8; font-weight: 800;">ÉLŐ</span>
                </div>
                <div style="font-size: 1.8rem; font-weight: 900; font-family: 'Outfit', sans-serif; color: #fff;">${fmt(totalLiquid)}</div>
                <div style="font-size: 0.75rem; color: var(--text-mid);">Revolut Pro (${fmt(revolutBal)}) + Stripe (${fmt(stripeAvail)})</div>
            </div>

            <div class="fin-card">
                <div style="font-size: 0.75rem; font-weight: 700; color: #4ade80; text-transform: uppercase; letter-spacing: 0.05em;">
                    <span>🟢 Stripe Elérhető Egyenleg</span>
                </div>
                <div style="font-size: 1.5rem; font-weight: 900; font-family: 'Outfit', sans-serif; color: #4ade80;">${fmt(stripeAvail)}</div>
                <div style="font-size: 0.75rem; color: var(--text-mid);">+ ${fmt(stripePending)} jóváírás alatt</div>
            </div>

            <div class="fin-card">
                <div style="font-size: 0.75rem; font-weight: 700; color: #60a5fa; text-transform: uppercase; letter-spacing: 0.05em;">
                    <span>🔵 Revolut Pro Egyenleg</span>
                </div>
                <div style="font-size: 1.5rem; font-weight: 900; font-family: 'Outfit', sans-serif; color: #60a5fa;">${fmt(revolutBal)}</div>
                <div style="font-size: 0.75rem; color: var(--text-mid);">${revolutTxs.length} könyvelt banki tranzakció</div>
            </div>

            <div class="fin-card">
                <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-mid); text-transform: uppercase; letter-spacing: 0.05em;">
                    <span>📈 Időszaki Pénzbeáramlás</span>
                </div>
                <div style="font-size: 1.5rem; font-weight: 900; font-family: 'Outfit', sans-serif; color: #22c55e;">+${fmt(periodInflow)}</div>
                <div style="font-size: 0.75rem; color: var(--text-mid);">Stripe kifizetések & feltöltések</div>
            </div>

            <div class="fin-card">
                <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-mid); text-transform: uppercase; letter-spacing: 0.05em;">
                    <span>📉 Időszaki Pénzkiáramlás</span>
                </div>
                <div style="font-size: 1.5rem; font-weight: 900; font-family: 'Outfit', sans-serif; color: #ef4444;">${fmt(periodOutflow)}</div>
                <div style="font-size: 0.75rem; color: var(--text-mid);">Meta, Foxpost, Éremgyártás, Opex</div>
            </div>
        </div>

        <!-- Filter Toolbar -->
        <div style="background: var(--surface); border: 1px solid var(--border); padding: 1rem; border-radius: 12px; margin-bottom: 1.25rem; display: flex; flex-direction: column; gap: 0.85rem;">
            <div style="display: flex; gap: 0.4rem; flex-wrap: wrap; align-items: center;">
                <span style="font-size: 0.75rem; color: var(--text-mid); font-weight: 700;">📅 Időszak:</span>
                <button class="logistics-sub-tab ${finPeriod === 'all' ? 'active' : ''}" onclick="setFinPeriod('all')">♾️ Kezdetektől (Összes)</button>
                <button class="logistics-sub-tab ${finPeriod === '30d' ? 'active' : ''}" onclick="setFinPeriod('30d')">📅 30 nap</button>
                <button class="logistics-sub-tab ${finPeriod === '7d' ? 'active' : ''}" onclick="setFinPeriod('7d')">🗓️ 7 nap</button>
                <button class="logistics-sub-tab ${finPeriod === '2026-08' ? 'active' : ''}" onclick="setFinPeriod('2026-08')">Augusztus</button>
                <button class="logistics-sub-tab ${finPeriod === '2026-07' ? 'active' : ''}" onclick="setFinPeriod('2026-07')">Július</button>
                <button class="logistics-sub-tab ${finPeriod === '2026-06' ? 'active' : ''}" onclick="setFinPeriod('2026-06')">Június</button>
                <button class="logistics-sub-tab ${finPeriod === '2026-05' ? 'active' : ''}" onclick="setFinPeriod('2026-05')">Május</button>
            </div>

            <div style="display: flex; gap: 0.6rem; flex-wrap: wrap; align-items: center; justify-content: space-between;">
                <div style="display: flex; gap: 0.4rem; flex-wrap: wrap; align-items: center;">
                    <span style="font-size: 0.75rem; color: var(--text-mid); font-weight: 700;">🏦 Forrás:</span>
                    <select onchange="setFinAccount(this.value)" class="input-text" style="width: auto; margin-bottom: 0; padding: 0.35rem 0.65rem; font-size: 0.8rem;">
                        <option value="all" ${finAccount === 'all' ? 'selected' : ''}>Összes számla (Revolut + Stripe)</option>
                        <option value="revolut" ${finAccount === 'revolut' ? 'selected' : ''}>🔵 Csak Revolut Pro</option>
                        <option value="stripe" ${finAccount === 'stripe' ? 'selected' : ''}>🟢 Csak Stripe</option>
                    </select>

                    <span style="font-size: 0.75rem; color: var(--text-mid); font-weight: 700; margin-left: 0.4rem;">🏷️ Kategória:</span>
                    <select onchange="setFinCategory(this.value)" class="input-text" style="width: auto; margin-bottom: 0; padding: 0.35rem 0.65rem; font-size: 0.8rem;">
                        <option value="all" ${finCategory === 'all' ? 'selected' : ''}>Összes kategória</option>
                        <option value="marketing" ${finCategory === 'marketing' ? 'selected' : ''}>📢 Marketing (Meta)</option>
                        <option value="shipping" ${finCategory === 'shipping' ? 'selected' : ''}>🦊 Foxpost Szállítás</option>
                        <option value="capex" ${finCategory === 'capex' ? 'selected' : ''}>🏅 Éremgyártás (Capex)</option>
                        <option value="accounting" ${finCategory === 'accounting' ? 'selected' : ''}>💼 Könyvelés</option>
                        <option value="tax" ${finCategory === 'tax' ? 'selected' : ''}>🏛️ NAV ÁFA</option>
                        <option value="stripe_payout" ${finCategory === 'stripe_payout' ? 'selected' : ''}>💰 Stripe Kifizetés</option>
                        <option value="deposit" ${finCategory === 'deposit' ? 'selected' : ''}>🏦 Kezdőtőke</option>
                    </select>
                </div>

                <div style="flex: 1; min-width: 200px; max-width: 320px;">
                    <input type="text" placeholder="🔍 Keresés leírás, összeg..." value="${finSearchQuery}" oninput="handleFinSearch(event)" class="input-text" style="width: 100%; margin-bottom: 0; padding: 0.35rem 0.75rem; font-size: 0.8rem;">
                </div>
            </div>
        </div>

        <!-- Transactions Ledger Table -->
        <div class="table-container">
            <div style="padding: 1rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 800; font-size: 0.95rem; color: #fff;">📜 Kombinált Pénzügyi Főkönyv</span>
                <span style="font-size: 0.75rem; color: var(--text-mid);">(${displayLedger.length} tranzakció)</span>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Dátum</th>
                        <th>Forrás</th>
                        <th>Kategória</th>
                        <th>Partner / Leírás</th>
                        <th>Típus</th>
                        <th style="text-align:right;">Összeg</th>
                        <th style="text-align:right;">Díj</th>
                        <th style="text-align:right;">Nettó Tétel</th>
                        <th style="text-align:right;">Egyenleg</th>
                    </tr>
                </thead>
                <tbody>
                    ${displayLedger.length === 0 ? `
                        <tr><td colspan="9" class="empty-state">Nincs a szűrésnek megfelelő tranzakció.</td></tr>
                    ` : displayLedger.map(t => {
                        const isPos = t.netAmount > 0;
                        const isNeg = t.netAmount < 0;
                        const amtColor = isPos ? '#4ade80' : (isNeg ? '#f87171' : '#94a3b8');
                        const amtSign = isPos ? '+' : '';

                        return `
                        <tr>
                            <td style="font-size: 0.75rem; color: var(--text-mid); font-family: monospace;">${t.dateDisplay}</td>
                            <td>
                                <span class="fin-badge ${t.source === 'revolut' ? 'fin-badge-revolut' : 'fin-badge-stripe'}">
                                    ${t.sourceLabel}
                                </span>
                            </td>
                            <td>
                                <span class="fin-badge" style="background: ${t.categoryColor}15; color: ${t.categoryColor}; border: 1px solid ${t.categoryColor}40;">
                                    ${t.categoryLabel}
                                </span>
                            </td>
                            <td style="font-weight: 600; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${t.description}">
                                ${t.description}
                            </td>
                            <td style="font-size: 0.75rem; color: var(--text-mid);">${t.type}</td>
                            <td style="text-align:right; font-family: monospace; font-weight: 700; color: ${amtColor};">
                                ${amtSign}${fmt(t.grossAmount)}
                            </td>
                            <td style="text-align:right; font-size: 0.75rem; color: var(--text-mid); font-family: monospace;">
                                ${t.fee > 0 ? '−' + fmt(t.fee) : '–'}
                            </td>
                            <td style="text-align:right; font-family: monospace; font-weight: 800; color: ${amtColor};">
                                ${amtSign}${fmt(t.netAmount)}
                            </td>
                            <td style="text-align:right; font-family: monospace; font-size: 0.8rem; color: #fff;">
                                ${t.balance !== null && t.balance !== undefined ? fmt(t.balance) : '–'}
                            </td>
                        </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;

    cardsEl.innerHTML = html;
}
