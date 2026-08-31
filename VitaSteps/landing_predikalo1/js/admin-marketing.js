// ===== ADMIN MARKETING & UNIT ECONOMICS MODULE =====

let mktMetrics = [];
let allMktOrders = [];
let mktSelectedRange = 'all'; // '1d', '3d', '7d', 'all'
let mktSelectedCampaign = 'pilis'; // 'pilis', 'predikalo', 'all'
let creativeFilter = 'all'; // 'all', 'pilis', 'predikalo', 'retarget'
let creativeSortKey = 'spend';
let creativeSortAsc = false;

function fmt(n) {
    if (n === null || n === undefined || isNaN(n)) return '0 Ft';
    return Math.round(n).toLocaleString('hu-HU') + ' Ft';
}

function setMktRange(range) {
    mktSelectedRange = range;
    document.querySelectorAll('#mkt-time-tabs .mkt-tab').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById(`mkt-tab-${range}`);
    if (btn) btn.classList.add('active');
    renderMktCards();
}

function setMktCampaign(camp) {
    mktSelectedCampaign = camp;
    document.querySelectorAll('#mkt-campaign-tabs .mkt-tab').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById(`mkt-camp-${camp}`);
    if (btn) btn.classList.add('active');
    renderMktCards();
}

function setCreativeFilter(filter) {
    creativeFilter = filter;
    renderMktCards();
}

function setCreativeSort(key) {
    if (creativeSortKey === key) {
        creativeSortAsc = !creativeSortAsc;
    } else {
        creativeSortKey = key;
        creativeSortAsc = false;
    }
    renderMktCards();
}

function getDateRange() {
    const now = new Date();
    if (mktSelectedRange === '1d') {
        const d = new Date(now);
        d.setHours(0, 0, 0, 0);
        return { from: d, label: 'Ma / Tegnap' };
    }
    if (mktSelectedRange === '3d') {
        const d = new Date(now);
        d.setDate(d.getDate() - 3);
        d.setHours(0, 0, 0, 0);
        return { from: d, label: 'Elmúlt 3 nap' };
    }
    if (mktSelectedRange === '7d') {
        const d = new Date(now);
        d.setDate(d.getDate() - 7);
        d.setHours(0, 0, 0, 0);
        return { from: d, label: 'Elmúlt 7 nap' };
    }
    return { from: null, label: 'Kezdetektől (Összesített)' };
}

async function loadMarketing() {
    const cardsEl = document.getElementById('mkt-cards');
    if (cardsEl) cardsEl.innerHTML = '<div class="empty-state"><span class="loading-spinner"></span><div style="margin-top:0.5rem">Marketing adatok betöltése...</div></div>';

    try {
        const res = await fetch(`/api/admin-data?type=marketing&secret=${encodeURIComponent(adminSecret)}`);
        if (!res.ok) throw new Error('Nem sikerült betölteni a marketing adatokat');

        const data = await res.json();
        mktMetrics = data.metrics || [];
        allMktOrders = data.orders || [];

        const updatedEl = document.getElementById('mkt-last-updated');
        if (updatedEl && data.lastUpdated) {
            updatedEl.textContent = `Meta Marketing adatok szinkronizálva: ${new Date(data.lastUpdated).toLocaleString('hu-HU')}`;
        }

        renderMktCards();

    } catch (err) {
        console.error('Marketing load error:', err);
        if (cardsEl) cardsEl.innerHTML = `<div class="empty-state" style="color: var(--red);">Hiba történt: ${err.message}</div>`;
    }
}

function analyzeCustomerCohorts(orders, fromDate) {
    const sorted = [...orders].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    const customerFirstOrderTime = new Map();

    for (const o of sorted) {
        const email = (o.billing_email || '').toLowerCase().trim();
        if (!email) continue;
        if (!customerFirstOrderTime.has(email)) {
            customerFirstOrderTime.set(email, new Date(o.created_at));
        }
    }

    const orderCohort = new Map();
    for (const o of sorted) {
        const email = (o.billing_email || '').toLowerCase().trim();
        const firstTime = customerFirstOrderTime.get(email);
        const orderTime = new Date(o.created_at);
        if (firstTime && orderTime.getTime() === firstTime.getTime()) {
            orderCohort.set(o.id, 'new');
        } else {
            orderCohort.set(o.id, 'returning');
        }
    }

    const filtered = fromDate ? orders.filter(o => new Date(o.created_at) >= fromDate) : orders;
    let totalNew = 0;
    let totalReturning = 0;
    const byCamp = {};

    for (const o of filtered) {
        const cohort = orderCohort.get(o.id) || 'new';
        const camp = (o.campaign || 'unknown').toLowerCase().trim();
        if (!byCamp[camp]) byCamp[camp] = { newCount: 0, returningCount: 0, total: 0 };

        if (cohort === 'new') {
            totalNew++;
            byCamp[camp].newCount++;
        } else {
            totalReturning++;
            byCamp[camp].returningCount++;
        }
        byCamp[camp].total++;
    }

    return {
        totalNew,
        totalReturning,
        totalOrders: filtered.length,
        byCamp
    };
}

function aggregateCreativeMetrics(rows) {
    const byAd = {};
    for (const r of rows) {
        const adName = (r.ad_name || 'Ismeretlen kreatív').trim();
        const campName = (r.campaign_name || 'Ismeretlen kampány').trim();
        const adsetName = (r.adset_name || '').trim();
        const key = `${campName}___${adsetName}___${adName}`;
        if (!byAd[key]) {
            byAd[key] = {
                key,
                ad_name: adName,
                ad_id: r.ad_id,
                adset_name: adsetName,
                campaign_name: campName,
                spend: 0,
                impressions: 0,
                reach: 0,
                clicks: 0,
                link_clicks: 0,
                purchases: 0,
                revenue: 0,
                ctr_sum: 0,
                cpm_sum: 0,
                cpc_sum: 0,
                count: 0
            };
        }
        const a = byAd[key];
        a.spend       += Number(r.spend || 0);
        a.impressions += Number(r.impressions || 0);
        a.reach       += Number(r.reach || 0);
        a.clicks      += Number(r.clicks || 0);
        a.link_clicks += Number(r.link_clicks || 0);
        a.purchases   += Number(r.purchases || 0);
        a.revenue     += Number(r.revenue || 0);
        a.ctr_sum     += Number(r.ctr || 0);
        a.cpm_sum     += Number(r.cpm || 0);
        a.cpc_sum     += Number(r.cpc || 0);
        a.count++;
    }

    return Object.values(byAd).map(a => {
        const spendVat = Math.round(a.spend * 1.27);
        const purchases = a.purchases;
        const revenue = a.revenue;
        const cpa = purchases > 0 ? Math.round(spendVat / purchases) : 0;
        const roas = a.spend > 0 ? Number((revenue / a.spend).toFixed(2)) : 0;
        const ctr = a.impressions > 0 ? Number(((a.link_clicks / a.impressions) * 100).toFixed(2)) : (a.count > 0 ? Number((a.ctr_sum / a.count).toFixed(2)) : 0);
        const cpc = a.link_clicks > 0 ? Math.round(spendVat / a.link_clicks) : (a.count > 0 ? Math.round(a.cpc_sum / a.count) : 0);
        const cpm = a.impressions > 0 ? Math.round((spendVat / a.impressions) * 1000) : (a.count > 0 ? Math.round(a.cpm_sum / a.count) : 0);

        const shipping = purchases * 1250;
        const stripe = Math.round(revenue * 0.015 + 50 * purchases);
        const otherVar = purchases * 155;
        const totalVar = spendVat + shipping + stripe + otherVar;
        const netContrib = revenue - totalVar;
        const marginPct = revenue > 0 ? Number(((netContrib / revenue) * 100).toFixed(1)) : 0;

        let status = { label: '⚪ Teszt', color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.1)' };
        if (purchases >= 1) {
            if (roas >= 3.0 && (cpa <= 2500 || cpa === 0)) {
                status = { label: '🟢 Skálázható', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.12)' };
            } else if (roas >= 2.0 && cpa <= 3500) {
                status = { label: '🟡 Megfelelő', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)' };
            } else {
                status = { label: '🔴 Drága', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.12)' };
            }
        } else if (spendVat >= 3500) {
            status = { label: '🔴 Nem konvertál', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.12)' };
        }

        return {
            ...a,
            spendVat,
            ctr,
            cpc,
            cpm,
            cpa,
            roas,
            netContrib,
            marginPct,
            status
        };
    });
}

function renderMktCards() {
    const STRIPE_PCT   = 0.015;
    const STRIPE_FIXED = 50;
    const FOXPOST_UNIT = 1250;
    const OTHER_VAR_UNIT = 155; // 35 Ft Számlázz + 120 Ft Csomagolás

    let TOTAL_FIXED_COSTS = 193000;
    let campaignHeaderTitle = '🌌 Nagy-Kevély csillagai – Eredménykimutatás';
    let challengeBatchLabel = '100 db Nagy-Kevély érem (163k gyártás + 30k könyvelés = 193 000 Ft)';
    let capexLabel = 'Induló Éremgyártás (100 db)';
    let capexAmount = 163000;
    let opexLabel = 'Fix Könyvelés (2 hó)';
    let opexAmount = 30000;

    if (mktSelectedCampaign === 'predikalo') {
        TOTAL_FIXED_COSTS = 193000;
        campaignHeaderTitle = '🏔️ Prédikálószék Vertical – Eredménykimutatás';
        challengeBatchLabel = '100 db Prédikálószék érem (163k gyártás + 30k könyvelés = 193 000 Ft)';
        capexLabel = 'Induló Éremgyártás (100 db)';
        capexAmount = 163000;
        opexLabel = 'Fix Könyvelés (2 hó)';
        opexAmount = 30000;
    } else if (mktSelectedCampaign === 'all') {
        TOTAL_FIXED_COSTS = 386000;
        campaignHeaderTitle = '♾️ Összesített Vállalkozási Eredmény (Mindkét Kihívás)';
        challengeBatchLabel = '200 db érem (2 × 163k gyártás + 2 × 30k könyvelés = 386 000 Ft)';
        capexLabel = '2 Széria Éremgyártás (200 db)';
        capexAmount = 326000;
        opexLabel = 'Fix Könyvelés (2 kampány)';
        opexAmount = 60000;
    }

    const cardsEl = document.getElementById('mkt-cards');
    if (!cardsEl) return;
    const { from, label } = getDateRange();

    const timeFilteredOrders = from ? allMktOrders.filter(o => new Date(o.created_at) >= from) : allMktOrders;
    const timeFilteredMetrics = from ? mktMetrics.filter(r => new Date(r.date) >= from) : mktMetrics;

    let activeOrders = timeFilteredOrders;
    let activeMetrics = timeFilteredMetrics;

    if (mktSelectedCampaign === 'pilis') {
        activeOrders = timeFilteredOrders.filter(o => (o.campaign || '').toLowerCase().match(/pilis|kevely|kevély/));
        activeMetrics = timeFilteredMetrics.filter(r => (r.campaign_name || '').toLowerCase().match(/pilis|kevely|kevély/));
    } else if (mktSelectedCampaign === 'predikalo') {
        activeOrders = timeFilteredOrders.filter(o => (o.campaign || '').toLowerCase().match(/predikalo|prédikáló/));
        activeMetrics = timeFilteredMetrics.filter(r => (r.campaign_name || '').toLowerCase().match(/predikalo|prédikáló/));
    }

    if (!activeOrders.length && !activeMetrics.length) {
        cardsEl.innerHTML = `<div class="empty-state">📭 Nincs adat a(z) <strong>${label}</strong> időszakra ehhez a kihíváshoz.</div>`;
        return;
    }

    const totRev = activeOrders.reduce((sum, o) => sum + Number(o.amount_total || 7990), 0);
    const totPurchases = activeOrders.length;

    let totSpend = 0, totImpressions = 0, totReach = 0, totLinkClicks = 0;
    for (const r of activeMetrics) {
        totSpend       += Number(r.spend || 0);
        totImpressions += Number(r.impressions || 0);
        totReach       += Number(r.reach || 0);
        totLinkClicks  += Number(r.link_clicks || 0);
    }

    const totMetaVat    = Math.round(totSpend * 1.27);
    const totStripe     = Math.round(totRev * STRIPE_PCT + STRIPE_FIXED * totPurchases);
    const totShipping   = Math.round(totPurchases * FOXPOST_UNIT);
    const totOtherVar   = Math.round(totPurchases * OTHER_VAR_UNIT);
    const totVarCosts   = totMetaVat + totStripe + totShipping + totOtherVar;
    
    const totNetContrib = Math.round(totRev - totVarCosts);
    const totMarginPct  = totRev > 0 ? (totNetContrib / totRev * 100).toFixed(1) : 0;
    
    const blendedCPA    = totPurchases > 0 ? Math.round(totMetaVat / totPurchases) : 0;
    const blendedROAS   = totSpend > 0 ? (totRev / totSpend).toFixed(2) : '0.00';

    const paybackPct    = Math.min(100, Math.max(0, (totNetContrib / TOTAL_FIXED_COSTS) * 100)).toFixed(1);
    const remainingToBe = Math.max(0, TOTAL_FIXED_COSTS - totNetContrib);
    const unitNetProfit = totPurchases > 0 ? (totNetContrib / totPurchases) : 0;
    const ordersNeeded  = (remainingToBe > 0 && unitNetProfit > 0) ? Math.ceil(remainingToBe / unitNetProfit) : 0;

    const isFullyPaid   = totNetContrib >= TOTAL_FIXED_COSTS;
    const netProfitAfterFC = totNetContrib - TOTAL_FIXED_COSTS;
    const paybackColor  = isFullyPaid ? '#22c55e' : (paybackPct > 50 ? '#f59e0b' : '#ef4444');
    const profitSign    = netProfitAfterFC >= 0 ? '+' : '';

    // Creatives
    const allCreatives = aggregateCreativeMetrics(activeMetrics);
    let displayCreatives = [...allCreatives];
    if (creativeFilter === 'pilis') {
        displayCreatives = allCreatives.filter(c => (c.campaign_name || '').toLowerCase().match(/pilis|kevely|kevély/));
    } else if (creativeFilter === 'retarget') {
        displayCreatives = allCreatives.filter(c => (c.campaign_name + c.adset_name).toLowerCase().includes('retarget'));
    }

    displayCreatives.sort((a, b) => {
        let valA = a[creativeSortKey];
        let valB = b[creativeSortKey];
        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();
        if (valA < valB) return creativeSortAsc ? -1 : 1;
        if (valA > valB) return creativeSortAsc ? 1 : -1;
        return 0;
    });

    function sortIcon(key) {
        if (creativeSortKey !== key) return '<span style="opacity:0.3;font-size:0.7rem;"> ↕</span>';
        return creativeSortAsc ? '<span style="color:var(--accent);font-size:0.75rem;"> ▲</span>' : '<span style="color:var(--accent);font-size:0.75rem;"> ▼</span>';
    }

    let html = `
        <div class="card" style="border-color: rgba(255,255,255,0.15); margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
                <div>
                    <h3 style="font-size: 1.15rem; font-weight: 800; color: #fff;">${campaignHeaderTitle} (${label})</h3>
                    <div style="color: var(--text-mid); font-size: 0.78rem; margin-top: 0.2rem;">${challengeBatchLabel}</div>
                </div>
                <div style="font-size: 0.85rem; font-weight: 700; color: ${paybackColor}; background: rgba(255,255,255,0.05); padding: 0.35rem 0.85rem; border-radius: 20px; border: 1px solid ${paybackColor};">
                    ${isFullyPaid ? `✅ Break-Even elérve! (+${fmt(netProfitAfterFC)} profit)` : `${paybackPct}% Megtérült`}
                </div>
            </div>

            <div class="mkt-summary-grid">
                <div class="mkt-card">
                    <div class="mkt-card-title">Összes Bruttó Bevétel</div>
                    <div class="mkt-card-value" style="color: #22c55e;">+${fmt(totRev)}</div>
                    <div class="mkt-card-sub">${totPurchases} db eladott érem</div>
                </div>
                <div class="mkt-card">
                    <div class="mkt-card-title">Meta Hirdetés (+ÁFA)</div>
                    <div class="mkt-card-value" style="color: #f87171;">−${fmt(totMetaVat)}</div>
                    <div class="mkt-card-sub">nettó: ${fmt(totSpend)}</div>
                </div>
                <div class="mkt-card">
                    <div class="mkt-card-title">Blended CPA</div>
                    <div class="mkt-card-value" style="color: ${blendedCPA <= 2500 ? '#22c55e' : (blendedCPA <= 3500 ? '#f59e0b' : '#ef4444')};">
                        ${blendedCPA > 0 ? fmt(blendedCPA) : '–'}
                    </div>
                    <div class="mkt-card-sub">átl. költség / vásárlás</div>
                </div>
                <div class="mkt-card">
                    <div class="mkt-card-title">Blended ROAS</div>
                    <div class="mkt-card-value" style="color: ${Number(blendedROAS) >= 3 ? '#22c55e' : (Number(blendedROAS) >= 2 ? '#f59e0b' : '#ef4444')};">
                        ${Number(blendedROAS) > 0 ? blendedROAS + 'x' : '–'}
                    </div>
                    <div class="mkt-card-sub">bevétel / nettó költés</div>
                </div>
                <div class="mkt-card">
                    <div class="mkt-card-title">Termelt Nettó Fedezet</div>
                    <div class="mkt-card-value" style="color: #38bdf8;">+${fmt(totNetContrib)}</div>
                    <div class="mkt-card-sub">${totMarginPct}% fedezeti árrés</div>
                </div>
            </div>

            <!-- Progress Bar -->
            <div style="margin-top: 1.25rem;">
                <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text-mid); margin-bottom:0.35rem;">
                    <span>Fix Költség Megtérülés (${fmt(TOTAL_FIXED_COSTS)})</span>
                    <strong style="color:${paybackColor};">
                        ${isFullyPaid ? `100% Megtérült (+${fmt(netProfitAfterFC)} profit)` : `${paybackPct}% (Még hiányzik: ${fmt(remainingToBe)}${ordersNeeded > 0 ? ` ~${ordersNeeded} db eladás` : ''})`}
                    </strong>
                </div>
                <div style="height: 8px; background: rgba(255,255,255,0.08); border-radius: 6px; overflow: hidden;">
                    <div style="height: 100%; width: ${paybackPct}%; background: ${paybackColor}; transition: width 0.5s;"></div>
                </div>
            </div>
        </div>

        <!-- Creative Performance Table -->
        ${mktSelectedCampaign === 'predikalo' ? '' : `
        <div class="table-container" style="margin-top: 1.5rem;">
            <div style="padding: 1rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                <h4 style="font-size: 1rem; font-weight: 700; color: #fff;">🎨 Hirdetési Kreatívok Teljesítménye</h4>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="logistics-sub-tab ${creativeFilter === 'all' ? 'active' : ''}" onclick="setCreativeFilter('all')">Összes (${allCreatives.length})</button>
                    <button class="logistics-sub-tab ${creativeFilter === 'pilis' ? 'active' : ''}" onclick="setCreativeFilter('pilis')">🌌 Nagy-Kevély</button>
                    <button class="logistics-sub-tab ${creativeFilter === 'retarget' ? 'active' : ''}" onclick="setCreativeFilter('retarget')">🎯 Retargeting</button>
                </div>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th onclick="setCreativeSort('ad_name')" style="cursor: pointer;">Kreatív ${sortIcon('ad_name')}</th>
                        <th onclick="setCreativeSort('spend')" style="cursor: pointer;">Költés (+ÁFA) ${sortIcon('spend')}</th>
                        <th onclick="setCreativeSort('purchases')" style="cursor: pointer;">Vásárlás ${sortIcon('purchases')}</th>
                        <th onclick="setCreativeSort('cpa')" style="cursor: pointer;">CPA ${sortIcon('cpa')}</th>
                        <th onclick="setCreativeSort('roas')" style="cursor: pointer;">ROAS ${sortIcon('roas')}</th>
                        <th onclick="setCreativeSort('netContrib')" style="cursor: pointer;">Nettó Fedezet ${sortIcon('netContrib')}</th>
                        <th>Minősítés</th>
                    </tr>
                </thead>
                <tbody>
                    ${displayCreatives.map(c => `
                        <tr>
                            <td style="font-weight: 600;">
                                <div>${c.ad_name}</div>
                                <div style="font-size: 0.72rem; color: var(--text-mid);">${c.campaign_name}</div>
                            </td>
                            <td>${fmt(c.spendVat)}</td>
                            <td><strong>${c.purchases} db</strong></td>
                            <td>${c.cpa > 0 ? fmt(c.cpa) : '–'}</td>
                            <td><strong>${c.roas > 0 ? c.roas + 'x' : '–'}</strong></td>
                            <td style="color: ${c.netContrib >= 0 ? '#22c55e' : '#ef4444'}; font-weight: 700;">${c.netContrib >= 0 ? '+' : ''}${fmt(c.netContrib)}</td>
                            <td>
                                <span style="background: ${c.status.bg}; color: ${c.status.color}; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">
                                    ${c.status.label}
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        `}
    `;

    cardsEl.innerHTML = html;
}
