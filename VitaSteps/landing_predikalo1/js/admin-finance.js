// ===== ADMIN FINANCE & REVOLUT / STRIPE CASHFLOW MODULE =====

let finData = null;
let finSubTab = 'pnl'; // 'pnl', 'cashflow', 'ledger'
let finPnlCampaign = 'pilis'; // 'pilis', 'predikalo', 'all'
let finPeriod = 'all'; // 'all', '30d', '7d', '2026-08', '2026-07', '2026-06', '2026-05'
let finAccount = 'all'; // 'all', 'revolut', 'stripe'
let finCategory = 'all';
let finSearchQuery = '';

function setFinSubTab(tab) {
    finSubTab = tab;
    renderFinance();
}

function setFinPnlCampaign(camp) {
    finPnlCampaign = camp;
    renderFinance();
}

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

function parseFinanceDate(str) {
    if (!str) return 0;
    const s = String(str).trim();
    const parts = s.split(' ');
    if (parts.length === 2 && parts[0].includes('-') && parts[1].includes(':')) {
        const [y, m, d] = parts[0].split('-').map(Number);
        const [hh, mm, ss] = parts[1].split(':').map(Number);
        return new Date(y, m - 1, d, hh || 0, mm || 0, ss || 0).getTime();
    }
    const t = new Date(s.replace(' ', 'T')).getTime();
    return isNaN(t) ? 0 : t;
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
        const time = parseFinanceDate(dateStr);
        if (!time) return true;

        if (finPeriod === '30d') {
            const past = new Date(now); past.setDate(now.getDate() - 30);
            return time >= past.getTime();
        }
        if (finPeriod === '7d') {
            const past = new Date(now); past.setDate(now.getDate() - 7);
            return time >= past.getTime();
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

        const time = parseFinanceDate(dateStr);
        unifiedLedger.push({
            id: `rev-${idx}`,
            rawDate: dateStr,
            time: time,
            dateDisplay: time ? new Date(time).toLocaleString('hu-HU', { dateStyle: 'short', timeStyle: 'short' }) : '–',
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

        const time = s.created || parseFinanceDate(dateStr);
        unifiedLedger.push({
            id: s.id,
            rawDate: dateStr,
            time: time,
            dateDisplay: time ? new Date(time).toLocaleString('hu-HU', { dateStyle: 'short', timeStyle: 'short' }) : '–',
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

    displayLedger.sort((a, b) => b.time - a.time);

    // Compute remaining medal inventory identically to admin-proofs.js (updateStats)
    const validRuns = (typeof allRuns !== 'undefined' ? allRuns : []).filter(r => !isTestRun(r));
    const pilisRuns = validRuns.filter(r => isPilisRun(r));
    const predikaloRuns = validRuns.filter(r => !isPilisRun(r));

    const pilisLimit = (typeof CAMPAIGNS_CONFIG !== 'undefined' && CAMPAIGNS_CONFIG.pilis?.limit) || 100;
    const predikaloLimit = (typeof CAMPAIGNS_CONFIG !== 'undefined' && CAMPAIGNS_CONFIG.predikaloszek?.limit) || 100;

    const pilisSold = pilisRuns.length;
    const b2Stock = Math.max(0, pilisLimit - pilisSold); // Nagy-Kevély Készlet

    const predikaloSold = predikaloRuns.length;
    const b1Stock = Math.max(0, predikaloLimit - predikaloSold); // Prédikálószék Készlet

    // Compute timeline and inventory breakdown to populate receipt values
    const { timeline: fullTimeline, stats: timelineStats } = calculateCashflowTimeline(revolutTxs, stripeTxs, finData.orders || [], allRuns);
    const b1UnitCost = timelineStats.batch1Cost || 1512.4453;
    const b2UnitCost = timelineStats.batch2Cost || 1628.6523;
    const b1Val = Math.round(b1Stock * b1UnitCost);
    const b2Val = Math.round(b2Stock * b2UnitCost);
    const osszesKeszletDb = b1Stock + b2Stock;
    const osszesKeszletErtek = Math.round(b1Val + b2Val);
    const jelenlegiLikvid = Math.round(revolutBal + stripeAvail);
    const likvidHamarosan = Math.round(jelenlegiLikvid + stripePending);
    const merlegFoosszeg = Math.round(likvidHamarosan + osszesKeszletErtek);

    // Build Main Sub-Tab Switcher
    let html = `
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 0.85rem 1.25rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;" id="fin-main-tabs">
                <button class="mkt-tab ${finSubTab === 'pnl' ? 'active' : ''}" onclick="setFinSubTab('pnl')" id="fin-tab-btn-pnl" style="font-weight: 700; font-size: 0.85rem;">📊 P&L & Kampány Audit</button>
                <button class="mkt-tab ${finSubTab === 'cashflow' ? 'active' : ''}" onclick="setFinSubTab('cashflow')" id="fin-tab-btn-cashflow" style="font-weight: 700; font-size: 0.85rem;">📈 Cashflow & Mérleg Kimutatás</button>
                <button class="mkt-tab ${finSubTab === 'ledger' ? 'active' : ''}" onclick="setFinSubTab('ledger')" id="fin-tab-btn-ledger" style="font-weight: 700; font-size: 0.85rem;">🧾 Nyers Tranzakciók (Főkönyv)</button>
            </div>
            <div style="font-size: 0.82rem; color: var(--text-mid); font-weight: 500;">
                ${finSubTab === 'pnl' ? '🎯 Kampány szintű egységfedezet, árbevétel & közvetlen költségek' : (finSubTab === 'cashflow' ? '🏦 Napi & havi cashflow idővonal és vállalkozási mérleg' : '📜 Revolut Pro és Stripe kártyás fizetések főkönyve')}
            </div>
        </div>
    `;

    // ── TAB 1: P&L & KAMPÁNY AUDIT ──────────────────────────────────────────
    if (finSubTab === 'pnl') {
        html += renderPnlAuditSection(revolutTxs, stripeTxs, finData.orders || [], allRuns);
    } 
    // ── TAB 2: CASHFLOW & MÉRLEG KIMUTATÁS ──────────────────────────────────
    else if (finSubTab === 'cashflow') {
        html += `
        <!-- PÉNZÜGYI NYUGTA / EGYENLEG ÉS MÉRLEG ÖSSZEGZŐ -->
        <div class="finance-receipt-box" style="background: linear-gradient(145deg, rgba(12, 15, 21, 0.98) 0%, rgba(18, 24, 36, 0.96) 100%); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 14px; padding: 1.5rem; max-width: 640px; margin: 0 auto 1.5rem; box-shadow: 0 12px 36px rgba(0,0,0,0.5); position: relative; overflow: hidden;">
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #38bdf8 0%, #22c55e 50%, #fbbf24 100%);"></div>

            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed rgba(255, 255, 255, 0.15); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                <div>
                    <div style="font-size: 0.7rem; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.08em;">🧾 VitaSteps Pénzügyi Mérlegkimutatás</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #fff; margin-top: 0.15rem;">Kasszaállás & Vállalkozási Mérleg</div>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 0.68rem; font-weight: 800; color: #4ade80; background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.3); padding: 0.2rem 0.55rem; border-radius: 4px;">ÉLŐ BANKI ADATOK</span>
                </div>
            </div>

            <!-- Receipt Rows -->
            <div style="display: flex; flex-direction: column; gap: 0.45rem; font-size: 0.9rem;">
                <!-- 1. Revolut Pro egyenleg -->
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #cbd5e1;">🔵 Revolut Pro egyenleg</span>
                    <span style="font-family: monospace; font-weight: 700; color: #fff; font-size: 0.95rem;">${fmt(revolutBal)}</span>
                </div>

                <!-- 2. Stripe elérhető egyenleg -->
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #cbd5e1;">🟢 + Stripe elérhető egyenleg</span>
                    <span style="font-family: monospace; font-weight: 700; color: #4ade80; font-size: 0.95rem;">+ ${fmt(stripeAvail)}</span>
                </div>

                <!-- Divider 1 -->
                <div style="border-top: 1px dashed rgba(255, 255, 255, 0.15); margin: 0.35rem 0;"></div>

                <!-- 3. Jelenlegi likvid tőke -->
                <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(56, 189, 248, 0.08); padding: 0.45rem 0.75rem; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.25);">
                    <span style="font-weight: 800; color: #38bdf8;">= Jelenlegi likvid tőke</span>
                    <span style="font-family: monospace; font-weight: 900; color: #38bdf8; font-size: 1.1rem;">${fmt(jelenlegiLikvid)}</span>
                </div>

                <!-- 4. Stripe jóváírás alatt álló -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.25rem;">
                    <span style="color: #cbd5e1;">⏳ + Stripe jóváírás alatt álló</span>
                    <span style="font-family: monospace; font-weight: 700; color: #94a3b8; font-size: 0.95rem;">+ ${fmt(stripePending)}</span>
                </div>

                <!-- Divider 2 -->
                <div style="border-top: 1px dashed rgba(255, 255, 255, 0.15); margin: 0.35rem 0;"></div>

                <!-- 5. Likvid tőke hamarosan -->
                <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(34, 197, 94, 0.08); padding: 0.45rem 0.75rem; border-radius: 6px; border: 1px solid rgba(34, 197, 94, 0.25);">
                    <span style="font-weight: 800; color: #4ade80;">= Likvid tőke hamarosan</span>
                    <span style="font-family: monospace; font-weight: 900; color: #4ade80; font-size: 1.15rem;">${fmt(likvidHamarosan)}</span>
                </div>

                <!-- 6. Prédikálószék Készlet -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.35rem;">
                    <div>
                        <span style="color: #cbd5e1;">🏔️ + Prédikálószék Készlet</span>
                        <span style="font-size: 0.75rem; color: var(--text-mid); margin-left: 0.35rem;">(${b1Stock} db × ${b1UnitCost.toFixed(2).replace('.', ',')} Ft)</span>
                    </div>
                    <span style="font-family: monospace; font-weight: 700; color: #38bdf8; font-size: 0.95rem;">+ ${fmt(b1Val)}</span>
                </div>

                <!-- 7. Nagy-Kevély Készlet -->
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #cbd5e1;">⭐ + Nagy-Kevély Készlet</span>
                        <span style="font-size: 0.75rem; color: var(--text-mid); margin-left: 0.35rem;">(${b2Stock} db × ${b2UnitCost.toFixed(2).replace('.', ',')} Ft)</span>
                    </div>
                    <span style="font-family: monospace; font-weight: 700; color: #c4ff00; font-size: 0.95rem;">+ ${fmt(b2Val)}</span>
                </div>

                <!-- 8. Készletek összesen (Fizikai raktárkészlet) -->
                <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(163, 230, 53, 0.08); padding: 0.45rem 0.75rem; border-radius: 6px; border: 1px solid rgba(163, 230, 53, 0.25); margin-top: 0.25rem;">
                    <div>
                        <span style="font-weight: 800; color: #a3e635;">📦 = Készletek összesen</span>
                        <span style="font-size: 0.75rem; color: #d9f99d; margin-left: 0.35rem;">(${osszesKeszletDb} db fizikai érem raktáron)</span>
                    </div>
                    <span style="font-family: monospace; font-weight: 900; color: #a3e635; font-size: 1.1rem;">+ ${fmt(osszesKeszletErtek)}</span>
                </div>

                <!-- Divider 3 (Double Solid Gold Line) -->
                <div style="border-top: 2px solid rgba(251, 191, 36, 0.45); margin: 0.6rem 0 0.45rem;"></div>

                <!-- 9. Mérleg főösszeg -->
                <div style="display: flex; justify-content: space-between; align-items: center; background: linear-gradient(90deg, rgba(251, 191, 36, 0.15) 0%, rgba(251, 191, 36, 0.05) 100%); padding: 0.65rem 0.85rem; border-radius: 8px; border: 1px solid rgba(251, 191, 36, 0.4);">
                    <div>
                        <span style="font-size: 1.05rem; font-weight: 900; color: #fbbf24; text-transform: uppercase; letter-spacing: 0.05em;">= Mérleg főösszeg</span>
                        <div style="font-size: 0.72rem; color: #fef08a;">Likvid tőke + Fizikai raktárkészlet értéke</div>
                    </div>
                    <span style="font-family: 'Outfit', monospace; font-size: 1.65rem; font-weight: 900; color: #fbbf24;">${fmt(merlegFoosszeg)}</span>
                </div>
            </div>
        </div>
        `;

        // Append the Cumulative Cashflow & Inventory Balance Sheet Timeline Section
        html += renderCashflowTimelineSection(revolutTxs, stripeTxs, finData.orders || []);
    }
    // ── TAB 3: NYERS TRANZAKCIÓK (FŐKÖNYV) ──────────────────────────────────
    else if (finSubTab === 'ledger') {
        html += `
        <!-- Filter Toolbar -->
        <div style="background: var(--surface); border: 1px solid var(--border); padding: 1rem; border-radius: 12px; margin-bottom: 1.25rem; display: flex; flex-direction: column; gap: 0.85rem;">
            <div style="display: flex; gap: 0.4rem; flex-wrap: wrap; align-items: center;">
                <span style="font-size: 0.75rem; color: var(--text-mid); font-weight: 700;">📅 Időszak:</span>
                <button class="logistics-sub-tab ${finPeriod === 'all' ? 'active' : ''}" onclick="setFinPeriod('all')">♾️ Kezdetektől (Összes)</button>
                <button class="logistics-sub-tab ${finPeriod === '30d' ? 'active' : ''}" onclick="setFinPeriod('30d')">📅 30 nap</button>
                <button class="logistics-sub-tab ${finPeriod === '7d' ? 'active' : ''}" onclick="setFinPeriod('7d')">🗓️ 7 nap</button>
                <button class="logistics-sub-tab ${finPeriod === '2026-09' ? 'active' : ''}" onclick="setFinPeriod('2026-09')">Szeptember</button>
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
    }

    cardsEl.innerHTML = html;
}

function fmtPnlAmount(sign, amount, color = '#fff', isBold = false, fontSize = '0.88rem') {
    if (amount === null || amount === undefined || isNaN(amount)) {
        return `<span style="font-family: monospace; color: #94a3b8; display: inline-block; min-width: 145px; text-align: right;">–&nbsp;&nbsp;&nbsp;&nbsp;</span>`;
    }
    const absVal = Math.abs(Math.round(amount));
    const numStr = absVal.toLocaleString('hu-HU').replace(/[\s\u00A0\u202F]/g, '&nbsp;');
    const signChar = sign ? sign : '&nbsp;';

    return `
        <span style="display: inline-flex; align-items: baseline; justify-content: flex-end; font-family: 'SF Mono', Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; font-variant-numeric: tabular-nums; font-size: ${fontSize}; font-weight: ${isBold ? 900 : 700}; color: ${color}; min-width: 145px;">
            <span style="width: 1.8ch; text-align: left; display: inline-block; opacity: 0.95;">${signChar}</span>
            <span style="width: 8.5ch; text-align: right; display: inline-block;">${numStr}</span>
            <span style="margin-left: 0.6ch; font-size: 0.85em; opacity: 0.85; font-weight: 600; width: 2.2ch; text-align: left;">Ft</span>
        </span>
    `;
}

// ── P&L & KAMPÁNY AUDIT ENGINE ──────────────────────────────────────────────
function renderPnlAuditSection(revolutTxs, stripeTxs, orders, runsInput) {
    const validRuns = (runsInput || (typeof allRuns !== 'undefined' ? allRuns : [])).filter(r => !isTestRun(r));
    const validOrders = (orders || []).filter(o => !o.is_test);
    const shipmentsList = (typeof allShipments !== 'undefined' ? allShipments : []);

    let targetRuns = validRuns;
    let targetOrders = validOrders;
    let campaignTitle = 'Összesített (Mindkét kihívás)';
    let isPilisActive = finPnlCampaign === 'pilis';
    let isPredikaloActive = finPnlCampaign === 'predikalo';

    if (isPilisActive) {
        targetRuns = validRuns.filter(r => isPilisRun(r));
        targetOrders = validOrders.filter(o => o.campaign === 'pilis');
        campaignTitle = '⭐ Nagy-Kevély csillagai';
    } else if (isPredikaloActive) {
        targetRuns = validRuns.filter(r => !isPilisRun(r));
        targetOrders = validOrders.filter(o => o.campaign !== 'pilis');
        campaignTitle = '🏔️ Prédikálószék Vertical';
    }

    const totalMedalsSold = targetRuns.length;
    const nominalGrossSales = totalMedalsSold * 7990;
    const actualRealizedRevenue = targetOrders.reduce((sum, o) => sum + (o.amount_total || 0), 0);

    // Basket analysis
    const runsByOrder = {};
    targetRuns.forEach(r => {
        if (r.order_id) {
            runsByOrder[r.order_id] = (runsByOrder[r.order_id] || 0) + 1;
        }
    });

    let singleBaskets = 0;
    let multi2Baskets = 0;
    let multi3PlusBaskets = 0;
    let multiMedalsCount = 0;

    targetOrders.forEach(o => {
        const count = runsByOrder[o.id] || 1;
        if (count === 1) singleBaskets++;
        else if (count === 2) { multi2Baskets++; multiMedalsCount += 2; }
        else { multi3PlusBaskets++; multiMedalsCount += count; }
    });

    // Home shipping surcharges
    let homeShippingCount = 0;
    targetRuns.forEach(r => {
        const s = shipmentsList.find(ship => ship.run_id === r.id);
        if (s && s.method === 'home') homeShippingCount++;
    });
    const homeShippingRevenue = homeShippingCount * 1200;

    // Discounts
    const expectedFullGross = nominalGrossSales + homeShippingRevenue;
    const totalDiscounts = Math.max(0, expectedFullGross - actualRealizedRevenue);

    // Direct Costs (COGS & Fulfillment)
    const b1UnitCost = 1512.4453;
    const b2UnitCost = 1628.6523;

    let totalCogs = 0;
    if (isPilisActive) {
        totalCogs = totalMedalsSold * b2UnitCost;
    } else if (isPredikaloActive) {
        totalCogs = totalMedalsSold * b1UnitCost;
    } else {
        const pilisCount = targetRuns.filter(r => isPilisRun(r)).length;
        const predCount = totalMedalsSold - pilisCount;
        totalCogs = (pilisCount * b2UnitCost) + (predCount * b1UnitCost);
    }

    const packagingCost = targetOrders.length * 150;
    const foxpostCount = Math.max(0, targetOrders.length - homeShippingCount);
    const shippingCost = (foxpostCount * 1140) + (homeShippingCount * 2400);
    const stripeFee = Math.round((targetOrders.length * 85) + (actualRealizedRevenue * 0.015));
    const szamlazzFee = targetOrders.length * 40;
    const totalFulfillment = packagingCost + shippingCost + stripeFee + szamlazzFee;
    const totalDirectCost = Math.round(totalCogs + totalFulfillment);

    // Marketing (Meta Ads)
    const metaCreatives = (finData && finData.meta) ? finData.meta : [];
    let metaSpendNet = 0;
    if (metaCreatives.length > 0) {
        metaCreatives.forEach(m => {
            const campLower = (m.campaign_name || m.Kampany || '').toLowerCase();
            const spend = parseFloat(m.spend || m.Koltes_HUF || 0) || 0;
            if (isPilisActive) {
                if (campLower.includes('kevély') || campLower.includes('kevely') || campLower.includes('pilis')) {
                    metaSpendNet += spend;
                }
            } else if (isPredikaloActive) {
                if (campLower.includes('prédikáló') || campLower.includes('predikalo')) {
                    metaSpendNet += spend;
                }
            } else {
                metaSpendNet += spend;
            }
        });
    }
    if (metaSpendNet === 0) {
        if (isPilisActive) metaSpendNet = 221404;
        else if (isPredikaloActive) metaSpendNet = 135628;
        else metaSpendNet = 221404 + 135628;
    }

    const metaVat = Math.round(metaSpendNet * 0.27);
    const totalMarketing = Math.round(metaSpendNet + metaVat);

    // Contribution Margins
    const cmBeforeVat = Math.round(actualRealizedRevenue - totalDirectCost - metaSpendNet);
    const cmAfterVat = Math.round(cmBeforeVat - metaVat);
    const profitMarginPct = actualRealizedRevenue > 0 ? ((cmAfterVat / actualRealizedRevenue) * 100).toFixed(1) : '0.0';
    const cpa = targetOrders.length > 0 ? Math.round(totalMarketing / targetOrders.length) : 0;
    const roas = metaSpendNet > 0 ? (actualRealizedRevenue / metaSpendNet).toFixed(2) : '0.00';

    // Inventory status
    const pilisLimit = (typeof CAMPAIGNS_CONFIG !== 'undefined' && CAMPAIGNS_CONFIG.pilis?.limit) || 100;
    const predikaloLimit = (typeof CAMPAIGNS_CONFIG !== 'undefined' && CAMPAIGNS_CONFIG.predikaloszek?.limit) || 100;
    const pilisSold = validRuns.filter(r => isPilisRun(r)).length;
    const predikaloSold = validRuns.filter(r => !isPilisRun(r)).length;
    const pilisLeft = Math.max(0, pilisLimit - pilisSold);
    const predikaloLeft = Math.max(0, predikaloLimit - predikaloSold);
    const totalLeft = pilisLeft + predikaloLeft;

    const pilisCostVal = 48398;
    const predikaloCostVal = 89576;
    const totalCostVal = pilisCostVal + predikaloCostVal;

    const pilisPotRev = pilisLeft * 7990;
    const predikaloPotRev = predikaloLeft * 7990;
    const totalPotRev = totalLeft * 7990;

    const isCmPos = cmAfterVat >= 0;
    const cmColor = isCmPos ? '#22c55e' : '#ef4444';

    return `
        <!-- Campaign Selector Bar -->
        <div style="background: var(--surface); border: 1px solid var(--border); padding: 0.85rem 1rem; border-radius: 12px; margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem;">
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;" id="pnl-campaign-tabs">
                <button class="mkt-tab ${finPnlCampaign === 'pilis' ? 'active' : ''}" onclick="setFinPnlCampaign('pilis')">⭐ Nagy-Kevély csillagai</button>
                <button class="mkt-tab ${finPnlCampaign === 'predikalo' ? 'active' : ''}" onclick="setFinPnlCampaign('predikalo')">🏔️ Prédikálószék Vertical</button>
                <button class="mkt-tab ${finPnlCampaign === 'all' ? 'active' : ''}" onclick="setFinPnlCampaign('all')">♾️ Mindkét kihívás (Összesített)</button>
            </div>
            <div style="font-size: 0.8rem; color: #38bdf8; font-weight: 700;">
                Aktív nézet: ${campaignTitle}
            </div>
        </div>

        <!-- 4 Top KPI Cards -->
        <div class="metrics-grid" style="grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
            <!-- 1. Realizált Árbevétel -->
            <div class="card" style="background: linear-gradient(145deg, rgba(18, 24, 36, 0.95) 0%, rgba(12, 16, 26, 0.95) 100%); border: 1px solid rgba(56, 189, 248, 0.25);">
                <div class="metric-title" style="color: #38bdf8; font-size: 0.75rem;">💰 Realizált Árbevétel</div>
                <div class="metric-value" style="color: #fff; font-size: 1.5rem; margin-top: 0.35rem;">${fmt(actualRealizedRevenue)}</div>
                <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.35rem;">
                    <strong>${totalMedalsSold} db</strong> érem (${targetOrders.length} rendelés)
                </div>
            </div>

            <!-- 2. Közvetlen Költségek -->
            <div class="card" style="background: linear-gradient(145deg, rgba(18, 24, 36, 0.95) 0%, rgba(12, 16, 26, 0.95) 100%); border: 1px solid rgba(249, 115, 22, 0.25);">
                <div class="metric-title" style="color: #f97316; font-size: 0.75rem;">📦 Közvetlen Költség (COGS + Fulfill)</div>
                <div class="metric-value" style="color: #fff; font-size: 1.5rem; margin-top: 0.35rem;">${fmt(totalDirectCost)}</div>
                <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.35rem;">
                    Érem: ${fmt(Math.round(totalCogs))} | Szállítás/díj: ${fmt(totalFulfillment)}
                </div>
            </div>

            <!-- 3. Marketing Költés -->
            <div class="card" style="background: linear-gradient(145deg, rgba(18, 24, 36, 0.95) 0%, rgba(12, 16, 26, 0.95) 100%); border: 1px solid rgba(239, 68, 68, 0.25);">
                <div class="metric-title" style="color: #f87171; font-size: 0.75rem;">📢 Marketing (+27% ÁFA)</div>
                <div class="metric-value" style="color: #fff; font-size: 1.5rem; margin-top: 0.35rem;">${fmt(totalMarketing)}</div>
                <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.35rem;">
                    CPA: <strong>${fmt(cpa)}</strong> | ROAS: <strong>${roas}x</strong>
                </div>
            </div>

            <!-- 4. Hozzájárulási Eredmény -->
            <div class="card" style="background: linear-gradient(145deg, rgba(18, 24, 36, 0.95) 0%, rgba(12, 16, 26, 0.95) 100%); border: 1px solid ${isCmPos ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'};">
                <div class="metric-title" style="color: ${cmColor}; font-size: 0.75rem;">🏆 Hozzájárulási Eredmény (Profit)</div>
                <div class="metric-value" style="color: ${cmColor}; font-size: 1.5rem; margin-top: 0.35rem;">
                    ${isCmPos ? '+' : ''}${fmt(cmAfterVat)}
                </div>
                <div style="font-size: 0.75rem; color: ${isCmPos ? '#4ade80' : '#f87171'}; margin-top: 0.35rem;">
                    Árrés: <strong>${profitMarginPct}%</strong> (ÁFA előtt: ${fmt(cmBeforeVat)})
                </div>
            </div>
        </div>

        <!-- P&L Breakdown Table Card -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                <h3 style="font-size: 1.05rem; font-weight: 800; color: #fff; margin: 0;">📑 Részletes P&L Eredménykimutatás</h3>
                <span style="font-size: 0.75rem; color: var(--text-mid);">${campaignTitle}</span>
            </div>

            <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem;">
                <!-- 1. BEVÉTEL -->
                <thead>
                    <tr style="background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38bdf8;">
                        <th style="text-align: left; padding: 0.6rem 0.8rem; color: #38bdf8; font-weight: 800;" colspan="2">📥 1. ÁRBEVÉTEL & KOSÁR ELEMZÉS</th>
                        <th style="text-align: right; padding: 0.6rem 0.8rem; color: #38bdf8; font-weight: 800;">ÖSSZEG (HUF)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; color: #cbd5e1;">Érmek eladása (Névleges alapár)</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">${totalMedalsSold} db érem × 7 990 Ft</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount('+', nominalGrossSales, '#fff', false)}
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; color: #cbd5e1;">Szállítási felár (Házhozszállítás)</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">${homeShippingCount} db rendelés (+1 200 Ft/csomag)</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount('+', homeShippingRevenue, '#4ade80', false)}
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; color: #cbd5e1;">Többérmes kosarak</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">1 érmes: ${singleBaskets} db | 2 érmes: ${multi2Baskets} db | 3+ érmes: ${multi3PlusBaskets} db</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount('', null)}
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; color: #cbd5e1;">Kedvezmények & Referral kuponok</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">Többérmes automatikus csomagár és ajánlói jóváírások</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount('−', totalDiscounts, '#f87171', false)}
                        </td>
                    </tr>
                    <tr style="background: rgba(34, 197, 94, 0.06); border-bottom: 1px solid var(--border);">
                        <td style="padding: 0.6rem 0.8rem; font-weight: 800; color: #4ade80;">= Tényleges realizált Árbevétel</td>
                        <td style="padding: 0.6rem 0.8rem; color: #86efac; font-size: 0.78rem;">${targetOrders.length} db fizetett rendelés</td>
                        <td style="text-align: right; padding: 0.6rem 0.8rem;">
                            ${fmtPnlAmount('=', actualRealizedRevenue, '#4ade80', true, '1rem')}
                        </td>
                    </tr>
                </tbody>

                <!-- 2. KÖZVETLEN KÖLTSÉGEK -->
                <thead>
                    <tr style="background: rgba(249, 115, 22, 0.08); border-left: 3px solid #f97316;">
                        <th style="text-align: left; padding: 0.6rem 0.8rem; color: #f97316; font-weight: 800; margin-top: 0.75rem;" colspan="2">📦 2. KÖZVETLEN KÖLTSÉGEK (COGS & FULFILLMENT)</th>
                        <th style="text-align: right; padding: 0.6rem 0.8rem; color: #f97316; font-weight: 800;">ÖSSZEG (HUF)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; color: #cbd5e1;">Érem bekerülési ára (COGS)</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">${totalMedalsSold} db eladott érem gyártása</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount('−', Math.round(totalCogs), '#f87171', false)}
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; color: #cbd5e1;">Csomagolás (doboz, kártya, boríték)</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">${targetOrders.length} db csomag × 150 Ft</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount('−', packagingCost, '#f87171', false)}
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; color: #cbd5e1;">Szállítás (Foxpost automata & Házhoz)</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">${foxpostCount} automata (~1 140 Ft) + ${homeShippingCount} házhoz (~2 400 Ft)</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount('−', shippingCost, '#f87171', false)}
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; color: #cbd5e1;">Stripe fizetési jutalék</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">1.5% + 85 Ft / tranzakció (${targetOrders.length} db)</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount('−', stripeFee, '#f87171', false)}
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; color: #cbd5e1;">Számlázz.hu e-számla díj</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">${targetOrders.length} db NAV e-számla × 40 Ft</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount('−', szamlazzFee, '#f87171', false)}
                        </td>
                    </tr>
                    <tr style="background: rgba(249, 115, 22, 0.06); border-bottom: 1px solid var(--border);">
                        <td style="padding: 0.6rem 0.8rem; font-weight: 800; color: #f97316;">= Közvetlen költségek összesen</td>
                        <td style="padding: 0.6rem 0.8rem; color: #fed7aa; font-size: 0.78rem;">COGS + Teljes Fulfillment</td>
                        <td style="text-align: right; padding: 0.6rem 0.8rem;">
                            ${fmtPnlAmount('−', totalDirectCost, '#f97316', true, '1rem')}
                        </td>
                    </tr>
                </tbody>

                <!-- 3. MARKETING -->
                <thead>
                    <tr style="background: rgba(239, 68, 68, 0.08); border-left: 3px solid #ef4444;">
                        <th style="text-align: left; padding: 0.6rem 0.8rem; color: #ef4444; font-weight: 800;" colspan="2">📢 3. MARKETING & HIRDETÉSEK</th>
                        <th style="text-align: right; padding: 0.6rem 0.8rem; color: #ef4444; font-weight: 800;">ÖSSZEG (HUF)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; color: #cbd5e1;">Meta Ads hirdetési költés (Nettó)</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">Kreatívok és hirdetéssorozatok összköltése</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount('−', metaSpendNet, '#f87171', false)}
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; color: #cbd5e1;">Meta Ads 27% ÁFA (Fordított adózás)</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">NAV ÁFA bevallási kötelezettség (27%)</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount('−', metaVat, '#f87171', false)}
                        </td>
                    </tr>
                    <tr style="background: rgba(239, 68, 68, 0.06); border-bottom: 1px solid var(--border);">
                        <td style="padding: 0.6rem 0.8rem; font-weight: 800; color: #ef4444;">= Marketing költség összesen</td>
                        <td style="padding: 0.6rem 0.8rem; color: #fca5a5; font-size: 0.78rem;">Meta Ads költés + 27% ÁFA</td>
                        <td style="text-align: right; padding: 0.6rem 0.8rem;">
                            ${fmtPnlAmount('−', totalMarketing, '#ef4444', true, '1rem')}
                        </td>
                    </tr>
                </tbody>

                <!-- 4. EREDMÉNY -->
                <thead>
                    <tr style="background: rgba(251, 191, 36, 0.12); border-left: 3px solid #fbbf24;">
                        <th style="text-align: left; padding: 0.6rem 0.8rem; color: #fbbf24; font-weight: 800;" colspan="2">🏆 4. HOZZÁJÁRULÁSI EREDMÉNY (CONTRIBUTION MARGIN)</th>
                        <th style="text-align: right; padding: 0.6rem 0.8rem; color: #fbbf24; font-weight: 800;">EREDMÉNY (HUF)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <td style="padding: 0.5rem 0.8rem; font-weight: 700; color: #fff;">Hozzájárulási eredmény (ÁFA előtt)</td>
                        <td style="padding: 0.5rem 0.8rem; color: var(--text-mid); font-size: 0.78rem;">Árbevétel − COGS − Fulfillment − Meta költés nettó</td>
                        <td style="text-align: right; padding: 0.5rem 0.8rem;">
                            ${fmtPnlAmount(cmBeforeVat >= 0 ? '+' : '−', cmBeforeVat, cmBeforeVat >= 0 ? '#4ade80' : '#f87171', true, '0.95rem')}
                        </td>
                    </tr>
                    <tr style="background: linear-gradient(90deg, rgba(251, 191, 36, 0.15) 0%, rgba(251, 191, 36, 0.05) 100%);">
                        <td style="padding: 0.75rem 0.8rem; font-weight: 900; color: #fbbf24; font-size: 1rem;">= Hozzájárulási eredmény (ÁFA után / Profit)</td>
                        <td style="padding: 0.75rem 0.8rem; color: #fef08a; font-size: 0.78rem;">Árrés: <strong>${profitMarginPct}%</strong> | Teljes adózott fedezet</td>
                        <td style="text-align: right; padding: 0.75rem 0.8rem;">
                            ${fmtPnlAmount(isCmPos ? '+' : '−', cmAfterVat, cmColor, true, '1.25rem')}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Inventory Stock Table Card -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                <div>
                    <h3 style="font-size: 1.05rem; font-weight: 800; color: #c4ff00; margin: 0;">📦 Készlet & Raktárérték Kimutatás</h3>
                    <div style="font-size: 0.78rem; color: var(--text-mid); margin-top: 0.2rem;">Fizikailag legyártott érmek, jelenlegi készlet és felszabadítható potenciális árbevétel.</div>
                </div>
                <span class="fin-badge" style="background: rgba(196, 255, 0, 0.15); color: #c4ff00; border: 1px solid rgba(196, 255, 0, 0.35);">
                    ${totalLeft} db érem készleten
                </span>
            </div>

            <table class="data-table">
                <thead>
                    <tr>
                        <th>Termék / Kihívás</th>
                        <th style="text-align:center;">Eladva</th>
                        <th style="text-align:center;">Maradt (Készlet)</th>
                        <th style="text-align:right;">Bekerülési érték</th>
                        <th style="text-align:right;">Potenciális árbevétel (7 990 Ft/db)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="font-weight: 700; color: #fff;">
                            ⭐ Nagy-Kevély csillagai
                        </td>
                        <td style="text-align:center; font-family: monospace; font-weight: 700; color: #38bdf8;">${pilisSold} db</td>
                        <td style="text-align:center; font-family: monospace; font-weight: 800; color: #c4ff00;">${pilisLeft} db</td>
                        <td style="text-align:right;">${fmtPnlAmount('', pilisCostVal, 'var(--text-mid)', false, '0.88rem')}</td>
                        <td style="text-align:right;">${fmtPnlAmount('', pilisPotRev, '#4ade80', true, '0.88rem')}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: 700; color: #fff;">
                            🏔️ Prédikálószék Vertical
                        </td>
                        <td style="text-align:center; font-family: monospace; font-weight: 700; color: #38bdf8;">${predikaloSold} db</td>
                        <td style="text-align:center; font-family: monospace; font-weight: 800; color: #c4ff00;">${predikaloLeft} db</td>
                        <td style="text-align:right;">${fmtPnlAmount('', predikaloCostVal, 'var(--text-mid)', false, '0.88rem')}</td>
                        <td style="text-align:right;">${fmtPnlAmount('', predikaloPotRev, '#4ade80', true, '0.88rem')}</td>
                    </tr>
                    <tr style="background: rgba(196, 255, 0, 0.05); font-weight: 800;">
                        <td style="color: #c4ff00; font-size: 0.95rem;">
                            📦 ÖSSZESEN
                        </td>
                        <td style="text-align:center; font-family: monospace; color: #38bdf8; font-size: 1rem;">${pilisSold + predikaloSold} db</td>
                        <td style="text-align:center; font-family: monospace; color: #c4ff00; font-size: 1rem;">${totalLeft} db</td>
                        <td style="text-align:right;">${fmtPnlAmount('', totalCostVal, '#fff', true, '0.95rem')}</td>
                        <td style="text-align:right;">${fmtPnlAmount('', totalPotRev, '#c4ff00', true, '1.15rem')}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
}


// ===== CASHFLOW & INVENTORY ASSET TIMELINE ENGINE =====
let timelinePeriod = 'all'; // 'all', '30d', '7d', '2026-09', '2026-08', '2026-07', '2026-06', '2026-05'
let timelineSort = 'asc';   // 'asc' = day 1 (May 07) to now, 'desc' = latest first
let timelineSearchQuery = '';
let timelineExpandedDays = new Set();
let cachedTimelinePoints = [];

function getDayOfWeekHu(dateStr) {
    if (!dateStr) return '';
    const days = ['vasárnap', 'hétfő', 'kedd', 'szerda', 'csütörtök', 'péntek', 'szombat'];
    const parts = dateStr.split('-');
    if (parts.length === 3) {
        const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
        return days[d.getDay()] || '';
    }
    return '';
}

function calculateCashflowTimeline(revolutTxs, stripeTxs, orders, runsInput) {
    const dayMap = {}; // dateStr -> day aggregation

    // Parse valid runs and group by date directly matching admin-proofs.js
    const runsList = runsInput || (typeof allRuns !== 'undefined' ? allRuns : []);
    const validRunsList = runsList.filter(r => !isTestRun(r));
    const runsByDate = {};
    validRunsList.forEach(r => {
        const d = (r.created_at || '').substring(0, 10);
        if (!d) return;
        if (!runsByDate[d]) runsByDate[d] = { pilis: 0, predikalo: 0 };
        if (isPilisRun(r)) runsByDate[d].pilis++;
        else runsByDate[d].predikalo++;
    });

    // Ensure all dates where runs occurred exist in dayMap
    Object.keys(runsByDate).forEach(d => {
        if (!dayMap[d]) {
            dayMap[d] = {
                date: d,
                revolutNet: 0,
                stripeNet: 0,
                medalsSold: 0,
                pilisMedalsSold: 0,
                batchesBought: [],
                revolutItems: [],
                stripeItems: [],
                skippedTransfers: []
            };
        }
    });

    // 1. DYNAMICALLY DISCOVER MEDAL BATCHES FROM REVOLUT CAPEX TRANSACTIONS
    const medalBatches = [];
    (revolutTxs || []).forEach(r => {
        const desc = (r.description || '').toLowerCase();
        const amt = r.amount || 0;
        const isMedalCapex = r.category === 'capex' || desc.includes('alibaba') || (desc.includes('devizaváltás') && amt < -100000);
        if (isMedalCapex && amt < 0) {
            const totalCost = Math.abs(amt);
            const qty = 100; // Standard production batch: 100 medals
            const unitCost = totalCost / qty;
            const rawDate = r.completedDate || r.startedDate || '';
            const dateStr = rawDate.substring(0, 10);
            medalBatches.push({
                batchId: medalBatches.length + 1,
                name: medalBatches.length === 0 ? '1. készlet (Prédikálószék)' : '2. készlet (Nagy-Kevély / Pilis)',
                date: dateStr,
                desc: r.description,
                totalCost: totalCost,
                qty: qty,
                remainingQty: qty,
                unitCost: unitCost
            });
        }
    });

    // Sort batches chronologically (Batch 1: 2026-05-07 ~1512.45 Ft, Batch 2: 2026-07-09 ~1628.65 Ft)
    medalBatches.sort((a, b) => a.date.localeCompare(b.date));

    // Fallbacks if not in statement
    const batch1UnitCost = medalBatches[0] ? medalBatches[0].unitCost : 1512.4453;
    const batch2UnitCost = medalBatches[1] ? medalBatches[1].unitCost : 1628.6523;

    // Index paid orders by date to identify Pilis vs Prédikálószék sales accurately
    const paidOrdersByDate = {};
    (orders || []).forEach(o => {
        const d = (o.created_at || '').substring(0, 10);
        if (!d) return;
        if (!paidOrdersByDate[d]) paidOrdersByDate[d] = [];
        paidOrdersByDate[d].push(o);
    });

    // 2. Process Revolut transactions (Primary operational debits & non-Stripe credits)
    (revolutTxs || []).forEach(r => {
        const rawDate = r.completedDate || r.startedDate || '';
        const dateStr = rawDate.substring(0, 10);
        if (!dateStr || dateStr.length < 10) return;

        if (!dayMap[dateStr]) {
            dayMap[dateStr] = {
                date: dateStr,
                revolutNet: 0,
                stripeNet: 0,
                medalsSold: 0,
                pilisMedalsSold: 0,
                batchesBought: [],
                revolutItems: [],
                stripeItems: [],
                skippedTransfers: []
            };
        }

        const descLower = (r.description || '').toLowerCase();
        const isStripePayout = r.category === 'stripe_payout' || 
                               descLower.includes('stripe') || 
                               descLower.includes('technology europe');

        if (isStripePayout) {
            // Internal transfer from Stripe to Revolut: skip to prevent duplicate revenue counting
            dayMap[dateStr].skippedTransfers.push({
                source: 'revolut',
                desc: r.description || 'Stripe jóváírás',
                amount: r.amount
            });
            return;
        }

        // Check if this transaction is a medal batch purchase
        const isMedalCapex = r.category === 'capex' || descLower.includes('alibaba') || (descLower.includes('devizaváltás') && r.amount < -100000);
        if (isMedalCapex && r.amount < 0) {
            const matchedBatch = medalBatches.find(b => b.date === dateStr && Math.abs(b.totalCost - Math.abs(r.amount)) < 1);
            if (matchedBatch) {
                dayMap[dateStr].batchesBought.push(matchedBatch);
            }
        }

        const net = (r.amount || 0) - (r.fee || 0);
        dayMap[dateStr].revolutNet += net;
        dayMap[dateStr].revolutItems.push({
            desc: r.description || r.type,
            categoryLabel: r.categoryLabel || r.category,
            categoryColor: r.categoryColor || '#94a3b8',
            amount: r.amount,
            fee: r.fee,
            net: net
        });
    });

    // 3. Process Stripe transactions (Credit sales on the exact date they happened)
    (stripeTxs || []).forEach(s => {
        let dateStr = '';
        if (s.created) {
            const d = new Date(s.created);
            const y = d.getFullYear();
            const m = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            dateStr = `${y}-${m}-${day}`;
        }
        if (!dateStr || dateStr.length < 10) return;

        if (!dayMap[dateStr]) {
            dayMap[dateStr] = {
                date: dateStr,
                revolutNet: 0,
                stripeNet: 0,
                medalsSold: 0,
                pilisMedalsSold: 0,
                batchesBought: [],
                revolutItems: [],
                stripeItems: [],
                skippedTransfers: []
            };
        }

        if (s.type === 'charge' || s.type === 'refund') {
            const net = s.net !== undefined ? s.net : (s.amount - (s.fee || 0));
            dayMap[dateStr].stripeNet += net;

            if (s.type === 'charge') {
                const qty = Math.max(1, Math.round(s.amount / 7990));
                dayMap[dateStr].medalsSold += qty;

                // Check if this date has Pilis orders in DB
                const dayOrders = paidOrdersByDate[dateStr] || [];
                const hasPilis = dayOrders.some(o => o.campaign === 'pilis');
                if (hasPilis || dateStr >= '2026-07-26') {
                    dayMap[dateStr].pilisMedalsSold += qty;
                }
            }

            dayMap[dateStr].stripeItems.push({
                desc: s.description || (s.type === 'charge' ? 'Stripe kártyás vásárlás' : 'Stripe visszatérítés'),
                type: s.type,
                gross: s.amount,
                fee: s.fee,
                net: net
            });
        } else if (s.type === 'payout') {
            dayMap[dateStr].skippedTransfers.push({
                source: 'stripe',
                desc: s.description || 'Stripe kifizetés a bankszámlára',
                amount: s.amount
            });
        }
    });

    // 4. CHRONOLOGICAL DAY-BY-DAY DUAL SIMULATION (CASHFLOW + INVENTORY ASSETS)
    const allDates = Object.keys(dayMap).sort();
    let cumulativeCash = 0;
    let cumulativeInventoryValue = 0;
    let inventoryQty = 0;

    // Track physical inventory batches: Batch 1 & Batch 2
    let b1Stock = 0;
    let b2Stock = 0;

    const fullTimeline = [];
    let totalStripeNet = 0;
    let totalRevolutNet = 0;
    let totalSkippedAmt = 0;
    let totalSkippedCount = 0;

    allDates.forEach(d => {
        const item = dayMap[d];
        const dayCashNet = item.revolutNet + item.stripeNet;
        cumulativeCash += dayCashNet;

        totalStripeNet += item.stripeNet;
        totalRevolutNet += item.revolutNet;
        item.skippedTransfers.forEach(st => {
            if (st.source === 'revolut') {
                totalSkippedAmt += Math.abs(st.amount);
                totalSkippedCount++;
            }
        });

        // 4A. Inflow of new inventory (Medal batch arrival)
        item.batchesBought.forEach(b => {
            if (b.batchId === 1) {
                b1Stock += b.qty;
            } else {
                b2Stock += b.qty;
            }
            inventoryQty += b.qty;
            cumulativeInventoryValue += b.totalCost;
        });

        // 4B. Outflow of inventory upon customer sales (COGS deduction)
        let dayCogs = 0;
        let dayB1Sold = 0;
        let dayB2Sold = 0;

        if (runsByDate[d]) {
            const takeB1 = runsByDate[d].predikalo;
            const takeB2 = runsByDate[d].pilis;
            if (takeB1 > 0) {
                dayB1Sold += takeB1;
                b1Stock = Math.max(0, b1Stock - takeB1);
                inventoryQty = Math.max(0, inventoryQty - takeB1);
                dayCogs += takeB1 * batch1UnitCost;
                cumulativeInventoryValue -= takeB1 * batch1UnitCost;
            }
            if (takeB2 > 0) {
                dayB2Sold += takeB2;
                b2Stock = Math.max(0, b2Stock - takeB2);
                inventoryQty = Math.max(0, inventoryQty - takeB2);
                dayCogs += takeB2 * batch2UnitCost;
                cumulativeInventoryValue -= takeB2 * batch2UnitCost;
            }
        } else if (item.medalsSold > 0 && Object.keys(runsByDate).length === 0) {
            let toDeduct = item.medalsSold;

            // If Pilis campaign (launched ~2026-07-26), draw from Batch 2 if available
            if (d >= '2026-07-26' && b2Stock > 0 && item.pilisMedalsSold > 0) {
                const takeB2 = Math.min(toDeduct, b2Stock);
                dayB2Sold += takeB2;
                b2Stock -= takeB2;
                toDeduct -= takeB2;
                inventoryQty -= takeB2;
                dayCogs += takeB2 * batch2UnitCost;
                cumulativeInventoryValue -= takeB2 * batch2UnitCost;
            }

            // Remainder draws from Batch 1 (Prédikálószék or FIFO)
            if (toDeduct > 0 && b1Stock > 0) {
                const takeB1 = Math.min(toDeduct, b1Stock);
                dayB1Sold += takeB1;
                b1Stock -= takeB1;
                toDeduct -= takeB1;
                inventoryQty -= takeB1;
                dayCogs += takeB1 * batch1UnitCost;
                cumulativeInventoryValue -= takeB1 * batch1UnitCost;
            }

            // If still remaining, draw from Batch 2
            if (toDeduct > 0 && b2Stock > 0) {
                const takeB2 = Math.min(toDeduct, b2Stock);
                dayB2Sold += takeB2;
                b2Stock -= takeB2;
                toDeduct -= takeB2;
                inventoryQty -= takeB2;
                dayCogs += takeB2 * batch2UnitCost;
                cumulativeInventoryValue -= takeB2 * batch2UnitCost;
            }
        }

        // Total Asset Value (Balance Sheet) = Liquid Cashflow + Current Inventory Value
        const totalAssetValue = cumulativeCash + cumulativeInventoryValue;

        fullTimeline.push({
            date: d,
            revolutNet: Math.round(item.revolutNet),
            stripeNet: Math.round(item.stripeNet),
            dayNet: Math.round(dayCashNet),
            cumulativeBalance: Math.round(cumulativeCash),
            // Inventory & Balance Sheet Metrics
            medalsSold: item.medalsSold,
            dayCogs: Math.round(dayCogs),
            dayB1Sold,
            dayB2Sold,
            inventoryQty,
            b1Stock,
            b2Stock,
            cumInventoryValue: Math.round(cumulativeInventoryValue),
            totalAssetValue: Math.round(totalAssetValue),
            batchesBought: item.batchesBought,
            revolutItems: item.revolutItems,
            stripeItems: item.stripeItems,
            skippedTransfers: item.skippedTransfers
        });
    });

    return {
        timeline: fullTimeline,
        stats: {
            firstDate: allDates[0] || '–',
            lastDate: allDates[allDates.length - 1] || '–',
            totalDays: allDates.length,
            currentCash: Math.round(cumulativeCash),
            currentInventoryValue: Math.round(cumulativeInventoryValue),
            currentInventoryQty: inventoryQty,
            currentTotalAsset: Math.round(cumulativeCash + cumulativeInventoryValue),
            batch1Cost: batch1UnitCost,
            batch2Cost: batch2UnitCost,
            totalStripeNet: Math.round(totalStripeNet),
            totalRevolutNet: Math.round(totalRevolutNet),
            totalSkippedAmt: Math.round(totalSkippedAmt),
            totalSkippedCount: totalSkippedCount
        }
    };
}

function renderCashflowSvg(timeline, stats) {
    if (!timeline || timeline.length === 0) {
        return '<div style="text-align: center; color: var(--text-mid); padding: 2rem;">Nincs megjeleníthető adat az idővonalhoz.</div>';
    }

    const width = 940;
    const height = 260;
    const pad = { top: 25, right: 30, bottom: 35, left: 85 };
    const chartW = width - pad.left - pad.right;
    const chartH = height - pad.top - pad.bottom;

    // Collect all values from both lines to set bounds
    const cashValues = timeline.map(t => t.cumulativeBalance);
    const assetValues = timeline.map(t => t.totalAssetValue);
    const allValues = [...cashValues, ...assetValues];

    const minVal = Math.min(0, ...allValues);
    let maxVal = Math.max(100000, ...allValues);
    maxVal = Math.ceil((maxVal * 1.08) / 50000) * 50000;
    const valSpan = maxVal - minVal || 1;

    // Zero baseline Y
    const zeroY = pad.top + chartH - ((0 - minVal) / valSpan) * chartH;

    // Cache coordinates for both curves
    cachedTimelinePoints = timeline.map((t, idx) => {
        const x = pad.left + (idx / (timeline.length - 1 || 1)) * chartW;
        const yCash = pad.top + chartH - ((t.cumulativeBalance - minVal) / valSpan) * chartH;
        const yAsset = pad.top + chartH - ((t.totalAssetValue - minVal) / valSpan) * chartH;
        return {
            x,
            yCash,
            yAsset,
            date: t.date,
            cumulativeBalance: t.cumulativeBalance,
            totalAssetValue: t.totalAssetValue,
            cumInventoryValue: t.cumInventoryValue,
            inventoryQty: t.inventoryQty,
            dayNet: t.dayNet,
            stripeNet: t.stripeNet,
            revolutNet: t.revolutNet,
            dayCogs: t.dayCogs,
            medalsSold: t.medalsSold,
            batchesBought: t.batchesBought,
            skippedCount: t.skippedTransfers.length
        };
    });

    // Generate gridlines (4 steps)
    const gridSteps = 4;
    let gridLinesHtml = '';
    for (let i = 0; i <= gridSteps; i++) {
        const val = Math.round(minVal + (valSpan / gridSteps) * i);
        const y = pad.top + chartH - ((val - minVal) / valSpan) * chartH;
        gridLinesHtml += `
            <line x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}" stroke="rgba(255, 255, 255, 0.07)" stroke-dasharray="3 4" />
            <text x="${pad.left - 10}" y="${y + 4}" fill="#7a8aa0" font-size="11" font-family="monospace" text-anchor="end">${val.toLocaleString('hu-HU')} Ft</text>
        `;
    }

    // Zero line highlight
    const zeroLineHtml = `<line x1="${pad.left}" y1="${zeroY}" x2="${width - pad.right}" y2="${zeroY}" stroke="rgba(255, 255, 255, 0.25)" stroke-width="1.5" stroke-dasharray="4 3" />`;

    // Path points for Cashflow Curve (Cyan)
    const pts = cachedTimelinePoints;
    const cashLinePathD = pts.map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.yCash.toFixed(1)}`).join(' ');
    const cashAreaPathD = `${cashLinePathD} L ${pts[pts.length - 1].x.toFixed(1)} ${zeroY.toFixed(1)} L ${pts[0].x.toFixed(1)} ${zeroY.toFixed(1)} Z`;

    // Path points for Total Asset / Inventory Balance Sheet Curve (Gold)
    const assetLinePathD = pts.map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.yAsset.toFixed(1)}`).join(' ');

    // X axis month ticks
    let xTicksHtml = '';
    const stepSize = Math.max(1, Math.floor(pts.length / 7));
    pts.forEach((p, idx) => {
        if (idx === 0 || idx === pts.length - 1 || idx % stepSize === 0) {
            xTicksHtml += `
                <text x="${p.x.toFixed(1)}" y="${height - 12}" fill="#7a8aa0" font-size="11" font-family="monospace" text-anchor="middle">${p.date.substring(5)}</text>
                <line x1="${p.x.toFixed(1)}" y1="${pad.top + chartH}" x2="${p.x.toFixed(1)}" y2="${pad.top + chartH + 5}" stroke="rgba(255,255,255,0.15)" />
            `;
        }
    });

    // Points on Cashflow Curve
    const cashDotsHtml = pts.map((p, idx) => `
        <circle cx="${p.x.toFixed(1)}" cy="${p.yCash.toFixed(1)}" r="4" fill="#0c0f15" stroke="#38bdf8" stroke-width="2" class="cf-dot" onmouseenter="showCfTooltip(event, ${idx})" onmousemove="showCfTooltip(event, ${idx})" onmouseleave="hideCfTooltip()" />
    `).join('');

    // Points on Asset Balance Sheet Curve
    const assetDotsHtml = pts.map((p, idx) => `
        <circle cx="${p.x.toFixed(1)}" cy="${p.yAsset.toFixed(1)}" r="4.5" fill="#0c0f15" stroke="#fbbf24" stroke-width="2.5" class="asset-dot" onmouseenter="showCfTooltip(event, ${idx})" onmousemove="showCfTooltip(event, ${idx})" onmouseleave="hideCfTooltip()" />
    `).join('');

    return `
        <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: auto; display: block; overflow: visible;">
            <defs>
                <linearGradient id="cfAreaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.25" />
                    <stop offset="85%" stop-color="#38bdf8" stop-opacity="0.03" />
                    <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.0" />
                </linearGradient>
            </defs>
            ${gridLinesHtml}
            ${zeroLineHtml}
            
            <!-- 1. Likvid Cashflow terület és vonal (Kék) -->
            <path d="${cashAreaPathD}" fill="url(#cfAreaGrad)" />
            <path d="${cashLinePathD}" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linejoin="round" />
            
            <!-- 2. Készlettel Növelt Mérleg / Vagyon görbe (Arany - Átfedésben) -->
            <path d="${assetLinePathD}" fill="none" stroke="#fbbf24" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />
            
            ${xTicksHtml}
            ${cashDotsHtml}
            ${assetDotsHtml}
        </svg>
    `;
}

function renderCashflowTimelineSection(revolutTxs, stripeTxs, orders) {
    const { timeline: fullTimeline, stats } = calculateCashflowTimeline(revolutTxs, stripeTxs, orders, typeof allRuns !== 'undefined' ? allRuns : []);

    // Filter by selected period
    let displayTimeline = fullTimeline.filter(t => {
        if (timelinePeriod === 'all') return true;
        if (timelinePeriod === '30d') {
            const past = new Date(); past.setDate(past.getDate() - 30);
            return new Date(t.date).getTime() >= past.getTime();
        }
        if (timelinePeriod === '7d') {
            const past = new Date(); past.setDate(past.getDate() - 7);
            return new Date(t.date).getTime() >= past.getTime();
        }
        if (timelinePeriod.startsWith('2026-')) {
            return t.date.startsWith(timelinePeriod);
        }
        return true;
    });

    // Search query filter
    if (timelineSearchQuery) {
        displayTimeline = displayTimeline.filter(t => 
            t.date.includes(timelineSearchQuery) ||
            String(t.dayNet).includes(timelineSearchQuery) ||
            String(t.cumulativeBalance).includes(timelineSearchQuery) ||
            String(t.totalAssetValue).includes(timelineSearchQuery) ||
            t.revolutItems.some(i => (i.desc || '').toLowerCase().includes(timelineSearchQuery)) ||
            t.stripeItems.some(i => (i.desc || '').toLowerCase().includes(timelineSearchQuery))
        );
    }

    // Sort order
    if (timelineSort === 'desc') {
        displayTimeline = [...displayTimeline].sort((a, b) => b.date.localeCompare(a.date));
    } else {
        displayTimeline = [...displayTimeline].sort((a, b) => a.date.localeCompare(b.date));
    }

    return `
        <!-- CASHFLOW & INVENTORY ASSET TIMELINE SECTION -->
        <div class="timeline-section" id="timeline-section">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 0.5rem;">
                <div>
                    <div style="display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.2rem 0.6rem; border-radius: 4px; background: rgba(251, 191, 36, 0.12); border: 1px solid rgba(251, 191, 36, 0.35); font-size: 0.72rem; font-weight: 800; color: #fbbf24; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.4rem;">
                        ⚡ Likvid Cashflow & Készletérték Átfedéses Mérleg
                    </div>
                    <h2 style="font-size: 1.35rem; font-weight: 800; color: #fff; margin: 0;">
                        📈 Időrendi Cashflow & Készlettel Növelt Mérleg Idővonal
                    </h2>
                    <div style="font-size: 0.8rem; color: var(--text-mid); margin-top: 0.25rem; max-width: 780px; line-height: 1.4;">
                        A grafikonon <strong>átfedésben</strong> látható a tiszta likvid cashflow és a fizikai éremkészletek értékével növelt <strong>vállalkozási mérleg (teljes vagyon)</strong>. Beszerzéskor a tőke készletbe megy át, így a vagyon megmarad; eladáskor a nettó árbevétel hozzáadódik a cashflow-hoz, miközben a készletről kikerülő érem bekerülési költsége dinamikusan levonódik.
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.72rem; color: #fbbf24; text-transform: uppercase; font-weight: 700;">👑 Mérleg Vagyon (Cash + Készlet):</div>
                    <div style="font-size: 1.7rem; font-weight: 900; font-family: 'Outfit', sans-serif; color: #fbbf24;">${fmt(stats.currentTotalAsset)}</div>
                    <div style="font-size: 0.75rem; color: #38bdf8;">Likvid cash: ${fmt(stats.currentCash)} | Készlet: ${fmt(stats.currentInventoryValue)}</div>
                </div>
            </div>

            <!-- KPI Bar with Inventory Valuation Breakdown -->
            <div class="timeline-kpi-bar">
                <div class="timeline-kpi-item" style="border-color: rgba(251, 191, 36, 0.35); background: linear-gradient(145deg, rgba(251, 191, 36, 0.05) 0%, rgba(12, 15, 21, 0.95) 100%);">
                    <div class="timeline-kpi-label" style="color: #fbbf24;">👑 Teljes Mérleg Vagyon</div>
                    <div class="timeline-kpi-val" style="color: #fbbf24;">${fmt(stats.currentTotalAsset)}</div>
                    <div style="font-size: 0.7rem; color: #fef08a; margin-top: 0.15rem;">Likvid pénz + Készletérték</div>
                </div>

                <div class="timeline-kpi-item">
                    <div class="timeline-kpi-label">💎 Likvid Cashflow</div>
                    <div class="timeline-kpi-val" style="color: #38bdf8;">${fmt(stats.currentCash)}</div>
                    <div style="font-size: 0.7rem; color: var(--text-mid); margin-top: 0.15rem;">Stripe + Revolut kasszaállás</div>
                </div>

                <div class="timeline-kpi-item" style="border-left: 3px solid #a3e635;">
                    <div class="timeline-kpi-label" style="color: #a3e635;">📦 Készletek Összesen</div>
                    <div class="timeline-kpi-val" style="color: #a3e635;">${fmt(stats.currentInventoryValue)}</div>
                    <div style="font-size: 0.72rem; color: #d9f99d; margin-top: 0.15rem;">
                        <strong>${stats.currentInventoryQty} db</strong> érem raktáron
                    </div>
                </div>

                <div class="timeline-kpi-item">
                    <div class="timeline-kpi-label">🏷️ Beszerzési Egységárak</div>
                    <div style="font-size: 0.85rem; font-weight: 800; color: #fff; margin-top: 0.3rem;">
                        1. készlet: <span style="color: #38bdf8;">${stats.batch1Cost.toFixed(2).replace('.', ',')} Ft</span><br>
                        2. készlet: <span style="color: #c4ff00;">${stats.batch2Cost.toFixed(2).replace('.', ',')} Ft</span>
                    </div>
                    <div style="font-size: 0.68rem; color: var(--text-mid); margin-top: 0.2rem;">Dinamikusan számolva számlákból</div>
                </div>

                <div class="timeline-kpi-item">
                    <div class="timeline-kpi-label">🟢 Stripe Eladások (Nettó)</div>
                    <div class="timeline-kpi-val" style="color: #4ade80;">+${fmt(stats.totalStripeNet)}</div>
                    <div style="font-size: 0.7rem; color: var(--text-mid); margin-top: 0.15rem;">Aznap jóváírva az eladáskor</div>
                </div>

                <div class="timeline-kpi-item" style="border-color: rgba(234, 179, 8, 0.35); background: rgba(234, 179, 8, 0.04);">
                    <div class="timeline-kpi-label" style="color: #facc15;">🛡️ Kiszűrt Belső Utalás</div>
                    <div class="timeline-kpi-val" style="color: #facc15;">${stats.totalSkippedCount} db (${fmt(stats.totalSkippedAmt)})</div>
                    <div style="font-size: 0.7rem; color: var(--text-mid); margin-top: 0.15rem;">Stripe ➔ Revolut duplikáció szűrve</div>
                </div>
            </div>

            <!-- Interactive Dual-Curve SVG Visual Timeline Chart -->
            <div class="timeline-chart-box" id="cf-chart-box">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
                    <!-- Legend -->
                    <div style="display: flex; gap: 1.25rem; align-items: center; flex-wrap: wrap; font-size: 0.8rem;">
                        <div style="display: flex; align-items: center; gap: 0.45rem;">
                            <span style="display: inline-block; width: 14px; height: 14px; border-radius: 3px; background: #fbbf24; border: 2px solid #fff;"></span>
                            <strong style="color: #fbbf24;">Mérleg Vagyon (Cashflow + Készlet):</strong>
                            <span style="color: #fff; font-family: monospace; font-weight: 800;">${fmt(stats.currentTotalAsset)}</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.45rem;">
                            <span style="display: inline-block; width: 14px; height: 14px; border-radius: 3px; background: #38bdf8; border: 2px solid #fff;"></span>
                            <strong style="color: #38bdf8;">Likvid Cashflow (Kasszaállás):</strong>
                            <span style="color: #fff; font-family: monospace; font-weight: 800;">${fmt(stats.currentCash)}</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.45rem; color: #a1a1aa;">
                            <span>📦 <strong>Készletérték:</strong> ${fmt(stats.currentInventoryValue)} (${stats.currentInventoryQty} db)</span>
                        </div>
                    </div>
                    <div style="font-size: 0.72rem; color: var(--text-mid);">
                        Kezdet: ${fullTimeline[0]?.date || '–'} ➔ Ma: ${fullTimeline[fullTimeline.length - 1]?.date || '–'}
                    </div>
                </div>
                ${renderCashflowSvg(fullTimeline, stats)}
                <div id="cf-chart-tooltip" class="timeline-tooltip"></div>
            </div>

            <!-- Timeline Filter Toolbar -->
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 0.85rem 1rem; border-radius: 10px; margin-bottom: 1rem; display: flex; flex-direction: column; gap: 0.75rem;">
                <div style="display: flex; gap: 0.4rem; flex-wrap: wrap; align-items: center;">
                    <span style="font-size: 0.75rem; color: var(--text-mid); font-weight: 700;">📅 Időszak:</span>
                    <button class="timeline-sub-tab ${timelinePeriod === 'all' ? 'active' : ''}" onclick="setTimelinePeriod('all')">♾️ Kezdetektől (${stats.firstDate}–)</button>
                    <button class="timeline-sub-tab ${timelinePeriod === '30d' ? 'active' : ''}" onclick="setTimelinePeriod('30d')">📅 Elmúlt 30 nap</button>
                    <button class="timeline-sub-tab ${timelinePeriod === '7d' ? 'active' : ''}" onclick="setTimelinePeriod('7d')">🗓️ 7 nap</button>
                    <button class="timeline-sub-tab ${timelinePeriod === '2026-09' ? 'active' : ''}" onclick="setTimelinePeriod('2026-09')">Szeptember</button>
                    <button class="timeline-sub-tab ${timelinePeriod === '2026-08' ? 'active' : ''}" onclick="setTimelinePeriod('2026-08')">Augusztus</button>
                    <button class="timeline-sub-tab ${timelinePeriod === '2026-07' ? 'active' : ''}" onclick="setTimelinePeriod('2026-07')">Július</button>
                    <button class="timeline-sub-tab ${timelinePeriod === '2026-06' ? 'active' : ''}" onclick="setTimelinePeriod('2026-06')">Június</button>
                    <button class="timeline-sub-tab ${timelinePeriod === '2026-05' ? 'active' : ''}" onclick="setTimelinePeriod('2026-05')">Május</button>
                </div>

                <div style="display: flex; gap: 0.6rem; flex-wrap: wrap; align-items: center; justify-content: space-between;">
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <button class="btn btn-grey" style="width: auto; padding: 0.35rem 0.75rem; font-size: 0.78rem;" onclick="toggleTimelineSort()">
                            ${timelineSort === 'asc' ? '📅 Időrendben: Első naptól máig ➔' : '🔄 Legfrissebb felül ⬅️'}
                        </button>
                        <span style="font-size: 0.75rem; color: var(--text-mid);">
                            Megjelenítve: <strong>${displayTimeline.length} nap</strong>
                        </span>
                    </div>
                    <div style="min-width: 220px; max-width: 320px; flex: 1;">
                        <input type="text" placeholder="🔍 Keresés dátum, tétel szerint..." value="${timelineSearchQuery}" oninput="handleTimelineSearch(event)" class="input-text" style="width: 100%; margin-bottom: 0; padding: 0.35rem 0.75rem; font-size: 0.8rem;">
                    </div>
                </div>
            </div>

            <!-- Detailed Day-by-Day Timeline Table with Asset & Inventory Columns -->
            <div class="table-container" style="margin-bottom: 0;">
                <div style="padding: 0.85rem 1rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--surface2);">
                    <span style="font-weight: 800; font-size: 0.9rem; color: #fff;">📋 Napi Cashflow & Készlet Napló</span>
                    <span style="font-size: 0.75rem; color: #38bdf8;">Kattints egy sorra a részletes napi tételekért</span>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Dátum</th>
                            <th style="text-align:right;">🔵 Revolut Tétel</th>
                            <th style="text-align:right;">🟢 Stripe Eladás</th>
                            <th style="text-align:right;">📦 Készlet / COGS</th>
                            <th style="text-align:right;">⚡ Napi Cash</th>
                            <th style="text-align:right;">💎 Likvid Cash</th>
                            <th style="text-align:right; color:#fbbf24;">👑 Mérleg Vagyon</th>
                            <th style="text-align:center;">Tételek</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${displayTimeline.length === 0 ? `
                            <tr><td colspan="8" class="empty-state">Nincs a szűrésnek megfelelő nap.</td></tr>
                        ` : displayTimeline.map(item => {
                            const isDayPos = item.dayNet > 0;
                            const isDayNeg = item.dayNet < 0;
                            const dayColor = isDayPos ? '#4ade80' : (isDayNeg ? '#f87171' : '#94a3b8');
                            const daySign = isDayPos ? '+' : '';

                            const revSign = item.revolutNet > 0 ? '+' : '';
                            const revColor = item.revolutNet > 0 ? '#4ade80' : (item.revolutNet < 0 ? '#f87171' : '#7a8aa0');

                            const stripeSign = item.stripeNet > 0 ? '+' : '';
                            const stripeColor = item.stripeNet > 0 ? '#4ade80' : '#7a8aa0';

                            const cumColor = item.cumulativeBalance >= 0 ? '#38bdf8' : '#f87171';
                            const isExpanded = timelineExpandedDays.has(item.date);
                            const itemCount = item.revolutItems.length + item.stripeItems.length + item.skippedTransfers.length;

                            return `
                                <tr class="timeline-day-row" onclick="toggleTimelineDay('${item.date}')">
                                    <td style="font-size: 0.82rem; font-weight: 700; font-family: monospace; color: #fff;">
                                        ${item.date} <span style="font-size: 0.72rem; color: var(--text-mid); font-weight: normal;">(${getDayOfWeekHu(item.date)})</span>
                                    </td>
                                    <td style="text-align: right; font-family: monospace; font-size: 0.82rem; color: ${revColor};">
                                        ${item.revolutNet !== 0 ? revSign + fmt(item.revolutNet) : '–'}
                                    </td>
                                    <td style="text-align: right; font-family: monospace; font-size: 0.82rem; color: ${stripeColor}; font-weight: 700;">
                                        ${item.stripeNet !== 0 ? stripeSign + fmt(item.stripeNet) : '–'}
                                    </td>
                                    <td style="text-align: right; font-family: monospace; font-size: 0.8rem; color: ${item.dayCogs > 0 ? '#f87171' : (item.batchesBought.length > 0 ? '#4ade80' : '#7a8aa0')};">
                                        ${item.dayCogs > 0 ? `−${fmt(item.dayCogs)}` : (item.batchesBought.length > 0 ? `+100 db` : '–')}
                                    </td>
                                    <td style="text-align: right; font-family: monospace; font-size: 0.82rem; color: ${dayColor}; font-weight: 700;">
                                        ${daySign}${fmt(item.dayNet)}
                                    </td>
                                    <td style="text-align: right; font-family: monospace; font-size: 0.88rem; font-weight: 800; color: ${cumColor};">
                                        ${fmt(item.cumulativeBalance)}
                                    </td>
                                    <td style="text-align: right; font-family: monospace; font-size: 0.92rem; font-weight: 900; color: #fbbf24;">
                                        ${fmt(item.totalAssetValue)}
                                    </td>
                                    <td style="text-align: center;">
                                        <button class="btn btn-grey" style="padding: 0.2rem 0.55rem; font-size: 0.72rem; width: auto;" onclick="event.stopPropagation(); toggleTimelineDay('${item.date}')">
                                            ${isExpanded ? '▲ Becsuk' : `👁️ ${itemCount} db`}
                                        </button>
                                    </td>
                                </tr>
                                ${isExpanded ? `
                                    <tr style="background: rgba(12, 15, 21, 0.95);">
                                        <td colspan="8" style="padding: 0.75rem 1.25rem;">
                                            ${renderTimelineDayDetails(item, stats)}
                                        </td>
                                    </tr>
                                ` : ''}
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function renderTimelineDayDetails(item, stats) {
    let out = `<div style="display: flex; flex-direction: column; gap: 0.5rem;">`;

    // 0. Inventory & Asset Summary on this day
    out += `
        <div style="background: rgba(251, 191, 36, 0.06); border: 1px solid rgba(251, 191, 36, 0.25); border-radius: 8px; padding: 0.6rem 0.85rem; font-size: 0.8rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div>
                <span style="font-weight: 800; color: #fbbf24;">👑 Aznapi Mérleg Záró Vagyon: ${fmt(item.totalAssetValue)}</span>
                <span style="color: var(--text-mid); margin-left: 0.5rem;">(Likvid pénz: ${fmt(item.cumulativeBalance)} + Készlet: ${fmt(item.cumInventoryValue)})</span>
            </div>
            <div style="color: #a3e635; font-weight: 700;">
                📦 Raktáron maradt: ${item.inventoryQty} db érem (1. készlet: ${item.b1Stock} db, 2. készlet: ${item.b2Stock} db)
            </div>
        </div>
    `;

    // If new batch arrived today
    if (item.batchesBought && item.batchesBought.length > 0) {
        item.batchesBought.forEach(b => {
            out += `
                <div class="timeline-details-box" style="border-left-color: #a3e635; background: rgba(163, 230, 53, 0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <span style="font-weight: 700; color: #a3e635;">🏅 Új éremkészlet beérkezett és aktiválva: +${b.qty} db érem</span>
                        <span style="font-family: monospace; font-weight: 800; color: #a3e635;">+${fmt(b.totalCost)} készletérték (Egységár: ${b.unitCost.toFixed(2).replace('.', ',')} Ft / db)</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #84cc16; margin-top: 0.2rem;">
                        ℹ️ A készlet beszerzési költsége levonódott a likvid pénzből, de azonnal megjelent a mérlegben készletvagyonként (a vállalkozás teljes vagyona nem csökkent).
                    </div>
                </div>
            `;
        });
    }

    // 1. Stripe items & COGS deduction
    if (item.stripeItems && item.stripeItems.length > 0) {
        out += `<div style="font-size: 0.75rem; font-weight: 800; color: #4ade80; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 0.2rem;">🟢 Stripe Értékesítések & Készletkivezetés (${item.stripeItems.length} db):</div>`;
        item.stripeItems.forEach(s => {
            out += `
                <div class="timeline-details-box" style="border-left-color: #22c55e;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <span style="font-weight: 600; color: #fff;">💳 ${s.desc}</span>
                        <span style="font-family: monospace; font-weight: 800; color: #4ade80;">
                            Bruttó: ${fmt(s.gross)} | Díj: −${fmt(s.fee)} ➔ Nettó: +${fmt(s.net)}
                        </span>
                    </div>
                </div>
            `;
        });
        if (item.dayCogs > 0) {
            out += `
                <div class="timeline-details-box" style="border-left-color: #f87171; background: rgba(239, 68, 68, 0.04);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <span style="font-weight: 600; color: #fca5a5;">📦 Készletcsökkenés (Eladott érmek bekerülési értéke): ${item.medalsSold} db érem</span>
                        <span style="font-family: monospace; font-weight: 800; color: #f87171;">−${fmt(item.dayCogs)} készletről kivezetve</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #f87171; margin-top: 0.15rem;">
                        ${item.dayB1Sold > 0 ? `1. készlet: ${item.dayB1Sold} db × ${stats.batch1Cost.toFixed(2).replace('.', ',')} Ft` : ''}
                        ${item.dayB1Sold > 0 && item.dayB2Sold > 0 ? ' | ' : ''}
                        ${item.dayB2Sold > 0 ? `2. készlet: ${item.dayB2Sold} db × ${stats.batch2Cost.toFixed(2).replace('.', ',')} Ft` : ''}
                    </div>
                </div>
            `;
        }
    }

    // 2. Revolut items
    if (item.revolutItems && item.revolutItems.length > 0) {
        out += `<div style="font-size: 0.75rem; font-weight: 800; color: #60a5fa; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 0.25rem;">🔵 Revolut Banki Tételek (${item.revolutItems.length} db):</div>`;
        item.revolutItems.forEach(r => {
            const isPos = r.net > 0;
            const amtColor = isPos ? '#4ade80' : '#f87171';
            const sign = isPos ? '+' : '';
            out += `
                <div class="timeline-details-box" style="border-left-color: #60a5fa;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <div>
                            <span class="fin-badge" style="background: ${r.categoryColor}15; color: ${r.categoryColor}; border: 1px solid ${r.categoryColor}40; margin-right: 0.4rem;">
                                ${r.categoryLabel}
                            </span>
                            <span style="font-weight: 600; color: #fff;">${r.desc}</span>
                        </div>
                        <span style="font-family: monospace; font-weight: 800; color: ${amtColor};">
                            ${sign}${fmt(r.net)}
                        </span>
                    </div>
                </div>
            `;
        });
    }

    // 3. Skipped internal transfers
    if (item.skippedTransfers && item.skippedTransfers.length > 0) {
        out += `<div style="font-size: 0.75rem; font-weight: 800; color: #facc15; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 0.25rem;">🛡️ Kiszűrt Belső Átutalások (Nem számítva duplikáció miatt):</div>`;
        item.skippedTransfers.forEach(st => {
            out += `
                <div class="timeline-details-box" style="border-left-color: #facc15; background: rgba(234, 179, 8, 0.04);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <span style="color: #fef08a;">🏦 ${st.desc}</span>
                        <span style="font-family: monospace; font-weight: 700; color: #facc15;">
                            ${st.source === 'revolut' ? '+' : '−'}${fmt(Math.abs(st.amount))} (Kiszűrve)
                        </span>
                    </div>
                    <div style="font-size: 0.7rem; color: #ca8a04; margin-top: 0.2rem;">
                        ℹ️ Ez egy Stripe ➔ Revolut belső tőkeáthelyezés. Mivel a Stripe eladásokat már a vásárlás napján jóváírtuk a cashflow-ban, ez a banki utalás ki van zárva, hogy a bevételed ne duplázódjon meg.
                    </div>
                </div>
            `;
        });
    }

    out += `</div>`;
    return out;
}

// Timeline event handlers
function setTimelinePeriod(period) {
    timelinePeriod = period;
    renderFinance();
    const el = document.getElementById('timeline-section');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
}

function toggleTimelineSort() {
    timelineSort = timelineSort === 'asc' ? 'desc' : 'asc';
    renderFinance();
    const el = document.getElementById('timeline-section');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
}

function handleTimelineSearch(e) {
    timelineSearchQuery = (e.target.value || '').toLowerCase().trim();
    renderFinance();
}

function toggleTimelineDay(date) {
    if (timelineExpandedDays.has(date)) {
        timelineExpandedDays.delete(date);
    } else {
        timelineExpandedDays.add(date);
    }
    renderFinance();
}

// Tooltip handlers for the SVG chart
window.showCfTooltip = function(e, idx) {
    const pt = cachedTimelinePoints[idx];
    if (!pt) return;
    const tt = document.getElementById('cf-chart-tooltip');
    const box = document.getElementById('cf-chart-box');
    if (!tt || !box) return;

    const rect = box.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    const isPos = pt.dayNet >= 0;
    const daySign = isPos ? '+' : '';
    const dayColor = isPos ? '#4ade80' : '#f87171';

    tt.innerHTML = `
        <div style="font-weight: 800; color: #fff; margin-bottom: 0.35rem; font-size: 0.88rem;">📅 ${pt.date} (${getDayOfWeekHu(pt.date)})</div>
        <div style="display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.4rem;">
            <div style="font-size: 0.85rem; color: #fbbf24; font-weight: 800; display: flex; justify-content: space-between; gap: 1rem;">
                <span>👑 Mérleg (Cash + Készlet):</span>
                <span>${fmt(pt.totalAssetValue)}</span>
            </div>
            <div style="font-size: 0.82rem; color: #38bdf8; font-weight: 800; display: flex; justify-content: space-between; gap: 1rem;">
                <span>💎 Likvid Cashflow (Pénzeszköz):</span>
                <span>${fmt(pt.cumulativeBalance)}</span>
            </div>
            <div style="font-size: 0.78rem; color: #a1a1aa; display: flex; justify-content: space-between; gap: 1rem;">
                <span>📦 Raktárkészlet Értéke:</span>
                <span>${fmt(pt.cumInventoryValue)} (${pt.inventoryQty} db érem)</span>
            </div>
        </div>
        <div style="font-size: 0.72rem; color: #94a3b8; border-top: 1px solid rgba(255,255,255,0.12); padding-top: 0.35rem; line-height: 1.4;">
            <div style="color: ${dayColor}; font-weight: 700;">⚡ Aznapi Cashflow: ${daySign}${fmt(pt.dayNet)}</div>
            🟢 Stripe eladás: +${fmt(pt.stripeNet)}<br>
            ${pt.medalsSold > 0 ? `🏷️ Érem COGS levonás: −${fmt(pt.dayCogs)} (${pt.medalsSold} db eladva)<br>` : ''}
            🔵 Revolut tétel: ${fmt(pt.revolutNet)}
            ${pt.batchesBought && pt.batchesBought.length > 0 ? `<br><span style="color:#a3e635; font-weight:700;">🏅 Új készlet beszerzés: +100 db (${fmt(pt.batchesBought[0].totalCost)})</span>` : ''}
            ${pt.skippedCount > 0 ? `<br><span style="color:#facc15;">🛡️ Kiszűrt belső utalás: ${pt.skippedCount} db</span>` : ''}
        </div>
    `;
    tt.style.left = `${clientX}px`;
    tt.style.top = `${clientY}px`;
    tt.style.display = 'block';
};

window.hideCfTooltip = function() {
    const tt = document.getElementById('cf-chart-tooltip');
    if (tt) tt.style.display = 'none';
};


