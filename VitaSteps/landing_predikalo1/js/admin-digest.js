// ===== ADMIN MODULE: VEZETŐI HETI KPI & ÜZLETI DIGEST =====

let kpiDigestData = null;
let isSendingKpiPush = false;

/**
 * Betölti a heti KPI digest adatokat a szerverről.
 * @param {boolean} force - Ha true, újragenerálja az adatokat a szerveren.
 */
async function loadKpiDigest(force = false) {
    const container = document.getElementById('digest-content');
    if (!container) return;

    if (!kpiDigestData || force) {
        container.innerHTML = `
            <div class="empty-state" style="padding: 3rem 1rem;">
                <span class="loading-spinner"></span>
                <div style="margin-top: 1rem; font-weight: 700; color: #fff; font-size: 1.1rem;">
                    📊 Vezetői heti KPI digest generálása folyamatban...
                </div>
                <div style="font-size: 0.85rem; color: var(--text-mid); margin-top: 0.35rem;">
                    Források ellenőrzése: Supabase rendelések, Stripe Live Balance, Meta marketing költések, Foxpost logisztika...
                </div>
            </div>
        `;
    }

    try {
        const res = await fetch(`/api/admin-data?type=kpi_digest&secret=${encodeURIComponent(adminSecret)}`);
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || `HTTP ${res.status}`);
        }

        const data = await res.json();
        if (!data.success || !data.digest) {
            throw new Error(data.error || 'Érvénytelen digest válasz a szervertől.');
        }

        kpiDigestData = data.digest;
        renderKpiDigest();

    } catch (err) {
        console.error('loadKpiDigest error:', err);
        container.innerHTML = `
            <div class="empty-state" style="color: var(--red); padding: 3rem 1.5rem;">
                <div style="font-size: 2.2rem; margin-bottom: 0.75rem;">⚠️</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #fff;">Nem sikerült betölteni a Vezetői Heti Digestet</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin: 0.5rem auto 1.25rem; max-width: 600px; line-height: 1.5;">
                    ${err.message}
                </div>
                <button class="btn btn-primary" onclick="loadKpiDigest(true)" style="width: auto; padding: 0.6rem 1.25rem; font-size: 0.88rem;">
                    🔄 Újrapróbálás
                </button>
            </div>
        `;
    }
}

/**
 * Kiküldi a heti digest értesítést Pushbulletre.
 */
async function sendKpiPushbullet() {
    if (isSendingKpiPush) return;

    if (!confirm('Biztosan elküldöd a heti KPI vezetői digest értesítést Pushbulletre a telefonodra?')) {
        return;
    }

    const btn = document.getElementById('btn-send-kpi-push');
    const originalText = btn ? btn.innerHTML : '📲 Heti Pushbullet Küldése Most';

    try {
        isSendingKpiPush = true;
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '⏳ Értesítés küldése...';
            btn.style.opacity = '0.7';
        }

        const res = await fetch('/api/admin-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'send_kpi_push',
                admin_secret: adminSecret
            })
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.success) {
            throw new Error(data.error || `HTTP ${res.status}`);
        }

        alert('✅ ' + (data.message || 'Pushbullet értesítés sikeresen elküldve!'));

    } catch (err) {
        console.error('sendKpiPushbullet error:', err);
        alert('❌ Hiba történt a Pushbullet értesítés küldése közben: ' + err.message);
    } finally {
        isSendingKpiPush = false;
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
            btn.style.opacity = '1';
        }
    }
}

/**
 * Formázott forint segédfüggvény ezres tagolással
 */
function digestFmtHUF(val) {
    if (val === undefined || val === null || isNaN(val)) return '0 Ft';
    return Math.round(Number(val)).toLocaleString('hu-HU') + ' Ft';
}

/**
 * Formázott százalék segédfüggvény
 */
function digestFmtPct(val) {
    if (val === undefined || val === null || isNaN(val)) return '0.0%';
    return Number(val).toFixed(1) + '%';
}

/**
 * Kirendereli a teljes heti digest dashboardot.
 */
function renderKpiDigest() {
    const container = document.getElementById('digest-content');
    if (!container || !kpiDigestData) return;

    const d = kpiDigestData;
    const fg = d.freshness_gate || {};
    const fin = d.financials || {};
    const inv = d.inventory || {};
    const fnl = d.funnel_and_leads || {};
    const ins = d.insights || {};
    const ops = d.operations || {};

    const genDateStr = d.generated_at ? new Date(d.generated_at).toLocaleString('hu-HU', {
        year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
    }) : '–';

    // ── 1. Adatfrissességi kapu kártyák ──
    const freshnessReports = (fg.reports || []).map(r => {
        const isFresh = (r.status || '').includes('Élő') || (r.status || '').includes('friss') || (r.status || '').includes('OK');
        const isWarn = (r.status || '').includes('Elavult') || (r.status || '').includes('⚠️');
        const badgeColor = isFresh ? '#4ade80' : (isWarn ? '#fbbf24' : '#f87171');
        const badgeBg = isFresh ? 'rgba(74, 222, 128, 0.12)' : (isWarn ? 'rgba(251, 191, 36, 0.12)' : 'rgba(248, 113, 113, 0.12)');
        const badgeBorder = isFresh ? 'rgba(74, 222, 128, 0.3)' : (isWarn ? 'rgba(251, 191, 36, 0.3)' : 'rgba(248, 113, 113, 0.3)');

        return `
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 0.85rem 1rem;">
                <div style="font-size: 0.72rem; color: var(--text-mid); text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em;">
                    ${r.source}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.4rem; gap: 0.5rem; flex-wrap: wrap;">
                    <span style="font-size: 0.82rem; color: #cbd5e1; font-family: monospace;">
                        ${r.last_entry || '–'}
                    </span>
                    <span style="background: ${badgeBg}; color: ${badgeColor}; border: 1px solid ${badgeBorder}; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.72rem; font-weight: 700;">
                        ${r.status}
                    </span>
                </div>
            </div>
        `;
    }).join('');

    const warningsHtml = (fg.warnings && fg.warnings.length > 0) ? `
        <div style="background: rgba(251, 191, 36, 0.08); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 8px; padding: 0.85rem 1.15rem; margin-top: 1rem;">
            <div style="font-size: 0.82rem; font-weight: 800; color: #fbbf24; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.4rem;">
                <span>⚠️</span> <span>Adatminőségi & Frissességi Figyelmeztetések:</span>
            </div>
            <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.8rem; color: #e2e8f0; line-height: 1.5;">
                ${fg.warnings.map(w => `<li>${w}</li>`).join('')}
            </ul>
        </div>
    ` : '';

    // ── 2. Készlet progress barok ──
    const predikaloSold = inv.predikalo?.sold || 0;
    const predikaloLimit = inv.predikalo?.limit || 100;
    const predikaloRem = inv.predikalo?.remaining || 0;
    const predikaloPct = Math.min(100, Math.round((predikaloSold / predikaloLimit) * 100));

    const pilisSold = inv.pilis?.sold || 0;
    const pilisLimit = inv.pilis?.limit || 100;
    const pilisRem = inv.pilis?.remaining || 0;
    const pilisPct = Math.min(100, Math.round((pilisSold / pilisLimit) * 100));

    // ── 3. HTML Összeállítás ──
    container.innerHTML = `
        <!-- FEJLÉC ÉS AKCIÓGOMBOK -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <div style="display: flex; align-items: center; gap: 0.65rem;">
                    <span style="font-size: 1.5rem;">📊</span>
                    <h2 style="font-size: 1.35rem; font-weight: 900; color: #fff; margin: 0; letter-spacing: -0.01em;">
                        Vezetői Heti KPI & Üzleti Digest
                    </h2>
                    <span style="background: rgba(196, 255, 0, 0.12); color: #c4ff00; border: 1px solid rgba(196, 255, 0, 0.35); padding: 2px 9px; border-radius: 9999px; font-size: 0.72rem; font-weight: 800; text-transform: uppercase;">
                        Élő Rendszer
                    </span>
                </div>
                <div style="font-size: 0.82rem; color: var(--text-mid); margin-top: 0.3rem;">
                    Időszak: <strong>Elmúlt ${d.period_days || 7} nap</strong> • Utolsó generálás: <strong>${genDateStr}</strong>
                </div>
            </div>

            <div style="display: flex; gap: 0.65rem; align-items: center; flex-wrap: wrap;">
                <button class="btn btn-grey" onclick="loadKpiDigest(true)" style="width: auto; padding: 0.5rem 1rem; font-size: 0.85rem; font-weight: 700; display: inline-flex; align-items: center; gap: 0.4rem;">
                    <span>🔄</span> <span>Újraszámolás</span>
                </button>
                <button class="btn btn-primary" id="btn-send-kpi-push" onclick="sendKpiPushbullet()" style="width: auto; padding: 0.5rem 1.25rem; font-size: 0.85rem; font-weight: 800; background: linear-gradient(135deg, #38bdf8 0%, #22c55e 100%); color: #020617; border: none; border-radius: 8px; cursor: pointer; display: inline-flex; align-items: center; gap: 0.45rem; box-shadow: 0 4px 14px rgba(56, 189, 248, 0.35);">
                    <span>📲</span> <span>Heti Pushbullet Küldése Most</span>
                </button>
            </div>
        </div>

        <!-- 1. SZEKCIÓ: ADATFRISSESSÉGI KAPU (DATA FRESHNESS GATE) -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.25rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.85rem;">
                <div style="font-size: 0.95rem; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 0.45rem;">
                    <span>🛡️</span> <span>1. Adatminőségi & Frissességi Kapu (Zero Hallucination Gate)</span>
                </div>
                <div>
                    ${fg.all_fresh ? 
                        '<span style="background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700;">🟢 Minden Forrás Friss</span>' : 
                        '<span style="background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700;">⚠️ Részleges Frissesség</span>'
                    }
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.75rem;">
                ${freshnessReports}
            </div>
            ${warningsHtml}
        </div>

        <!-- 2. SZEKCIÓ: HETI PÉNZÜGYI ÖSSZEFOGLALÓ & FEDEZETEK -->
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 0.95rem; font-weight: 800; color: #fff; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.45rem;">
                <span>💰</span> <span>2. Heti Pénzügyek & Fedezeti Elemzés (Elmúlt 7 nap)</span>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.85rem; margin-bottom: 0.85rem;">
                <!-- Árbevétel -->
                <div class="fin-card highlight" style="border-color: rgba(56, 189, 248, 0.4);">
                    <div class="fin-badge fin-badge-stripe">Árbevétel (7 nap)</div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #38bdf8; font-family: 'Outfit', sans-serif; margin-top: 0.2rem;">
                        ${digestFmtHUF(fin.gross_revenue_7d)}
                    </div>
                    <div style="font-size: 0.78rem; color: var(--text-mid);">
                        <strong>${fin.orders_count_7d || 0} db</strong> rendelés • Előző hét: ${digestFmtHUF(fin.prev_revenue_7d)}
                    </div>
                </div>

                <!-- Közvetlen költségek -->
                <div class="fin-card" style="border-color: rgba(244, 63, 94, 0.3); background: rgba(244, 63, 94, 0.04);">
                    <div style="font-size: 0.72rem; color: #fb7185; text-transform: uppercase; font-weight: 700;">Közvetlen Változó Költségek</div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #f43f5e; font-family: 'Outfit', sans-serif; margin-top: 0.2rem;">
                        ${digestFmtHUF(fin.costs_7d?.total_with_cogs)}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-mid); line-height: 1.3;">
                        Foxpost: ${digestFmtHUF(fin.costs_7d?.foxpost)} • Érem: ${digestFmtHUF(fin.costs_7d?.medal_cogs)}<br>
                        Stripe: ${digestFmtHUF(fin.costs_7d?.stripe)} • Doboz: ${digestFmtHUF(fin.costs_7d?.packing)}
                    </div>
                </div>

                <!-- Fedezet I (CM I) -->
                <div class="fin-card" style="border-color: rgba(34, 197, 94, 0.4); background: rgba(34, 197, 94, 0.05);">
                    <div style="font-size: 0.72rem; color: #4ade80; text-transform: uppercase; font-weight: 700;">Fedezet I. (CM I)</div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #22c55e; font-family: 'Outfit', sans-serif; margin-top: 0.2rem;">
                        ${digestFmtHUF(fin.cm1_7d)}
                    </div>
                    <div style="font-size: 0.78rem; color: var(--text-mid);">
                        Fedezeti hányad: <strong style="color: #4ade80;">${digestFmtPct(fin.cm1_pct_7d)}</strong>
                    </div>
                </div>

                <!-- Meta költés -->
                <div class="fin-card" style="border-color: rgba(196, 255, 0, 0.3); background: rgba(196, 255, 0, 0.04);">
                    <div style="font-size: 0.72rem; color: #c4ff00; text-transform: uppercase; font-weight: 700;">Meta Ads Költés</div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #c4ff00; font-family: 'Outfit', sans-serif; margin-top: 0.2rem;">
                        ${digestFmtHUF(fin.meta_spend_7d)}
                    </div>
                    <div style="font-size: 0.78rem; color: var(--text-mid);">
                        Blended CAC: <strong>${digestFmtHUF(fin.blended_cac)}</strong>
                    </div>
                </div>

                <!-- Fedezet II (CM II) -->
                <div class="fin-card" style="border-color: rgba(168, 85, 247, 0.4); background: rgba(168, 85, 247, 0.05);">
                    <div style="font-size: 0.72rem; color: #c084fc; text-transform: uppercase; font-weight: 700;">Fedezet II. (CM II)</div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #a855f7; font-family: 'Outfit', sans-serif; margin-top: 0.2rem;">
                        ${digestFmtHUF(fin.cm2_7d)}
                    </div>
                    <div style="font-size: 0.78rem; color: var(--text-mid);">
                        Marketing utáni: <strong style="color: #c084fc;">${digestFmtPct(fin.cm2_pct_7d)}</strong>
                    </div>
                </div>

                <!-- Stripe Live Balance -->
                <div class="fin-card highlight" style="border-color: rgba(99, 102, 241, 0.4);">
                    <div class="fin-badge" style="background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3);">
                        Stripe Élő Egyenleg
                    </div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #818cf8; font-family: 'Outfit', sans-serif; margin-top: 0.2rem;">
                        ${digestFmtHUF(fin.stripe?.available_huf)}
                    </div>
                    <div style="font-size: 0.78rem; color: var(--text-mid);">
                        Függőben: ${digestFmtHUF(fin.stripe?.pending_huf)} • All-Time: ${digestFmtHUF(fin.all_time_revenue)}
                    </div>
                </div>
            </div>
        </div>

        <!-- 3. ÉS 4. SZEKCIÓ: KÉSZLETKIMUTATÁS + FUNNEL & LOGISZTIKA (2 OSZLOP) -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 1.25rem; margin-bottom: 1.5rem;">
            <!-- KÉSZLET & RUNWAY -->
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.25rem;">
                <div style="font-size: 0.95rem; font-weight: 800; color: #fff; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between;">
                    <span style="display: flex; align-items: center; gap: 0.45rem;">
                        <span>📦</span> <span>3. Készletkimutatás & Kifutási Idő</span>
                    </span>
                    <span style="font-size: 0.78rem; color: #38bdf8; font-weight: 700;">
                        ${inv.runway_text || '–'}
                    </span>
                </div>

                <!-- Prédikálószék -->
                <div style="margin-bottom: 1.15rem;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.35rem;">
                        <span style="color: #fff; font-weight: 700;">🏔️ Prédikálószék Vertical</span>
                        <span style="color: #38bdf8; font-weight: 800;">${predikaloRem} db szabad / ${predikaloLimit} db (${predikaloSold} eladva)</span>
                    </div>
                    <div style="background: rgba(255, 255, 255, 0.08); height: 10px; border-radius: 9999px; overflow: hidden; position: relative;">
                        <div style="background: #38bdf8; width: ${predikaloPct}%; height: 100%; border-radius: 9999px;"></div>
                    </div>
                </div>

                <!-- Pilis / Nagy-Kevély -->
                <div style="margin-bottom: 1.15rem;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.35rem;">
                        <span style="color: #fff; font-weight: 700;">🌌 Nagy-Kevély / Pilis</span>
                        <span style="color: #c4ff00; font-weight: 800;">${pilisRem} db szabad / ${pilisLimit} db (${pilisSold} eladva)</span>
                    </div>
                    <div style="background: rgba(255, 255, 255, 0.08); height: 10px; border-radius: 9999px; overflow: hidden; position: relative;">
                        <div style="background: #c4ff00; width: ${pilisPct}%; height: 100%; border-radius: 9999px;"></div>
                    </div>
                </div>

                <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.82rem; color: var(--text-mid);">Összesen raktáron lévő készletérték (bekerülési áron):</span>
                    <span style="font-size: 1.1rem; font-weight: 800; color: #fff;">${digestFmtHUF(inv.total_inventory_cost_value_huf)}</span>
                </div>
            </div>

            <!-- TÖLCSÉR, LEADEK & LOGISZTIKA -->
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.25rem;">
                <div style="font-size: 0.95rem; font-weight: 800; color: #fff; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between;">
                    <span style="display: flex; align-items: center; gap: 0.45rem;">
                        <span>🎯</span> <span>4. Funnel, Leadek & Logisztika</span>
                    </span>
                    <button class="btn btn-grey" onclick="setFilter('logistics')" style="width: auto; padding: 0.25rem 0.65rem; font-size: 0.75rem;">
                        🦊 Logisztika megnyitása →
                    </button>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1rem;">
                    <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem;">
                        <div style="font-size: 0.72rem; color: var(--text-mid); text-transform: uppercase; font-weight: 700;">Leadek & Konverzió</div>
                        <div style="font-size: 1.25rem; font-weight: 900; color: #38bdf8; margin-top: 0.2rem;">
                            ${fnl.total_leads || 0} lead <span style="font-size: 0.85rem; color: #4ade80;">(${digestFmtPct(fnl.lead_conversion_rate_pct)})</span>
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.2rem;">
                            Vásárolt: <strong>${fnl.converted_leads || 0} fő</strong> • Új: +${fnl.new_leads_7d || 0}
                        </div>
                    </div>

                    <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem;">
                        <div style="font-size: 0.72rem; color: var(--text-mid); text-transform: uppercase; font-weight: 700;">NPS & Elégedettség</div>
                        <div style="font-size: 1.25rem; font-weight: 900; color: #facc15; margin-top: 0.2rem;">
                            ⭐ ${Number(fnl.avg_nps_score || 0).toFixed(2)} / 10
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.2rem;">
                            Összesen <strong>${fnl.feedbacks_count || 0} db</strong> beérkezett értékelés
                        </div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                    <!-- Kitérő Béta -->
                    <div style="background: rgba(52, 211, 153, 0.05); border: 1px solid rgba(52, 211, 153, 0.25); border-radius: 8px; padding: 0.75rem;">
                        <div style="font-size: 0.72rem; color: #34d399; text-transform: uppercase; font-weight: 700;">🚶 Kitérő Béta Kampány</div>
                        <div style="font-size: 1.05rem; font-weight: 800; color: #fff; margin-top: 0.2rem;">
                            ${fnl.kitero_nps10_campaign?.sent_count || 0} kiküldve • ${fnl.kitero_nps10_campaign?.unique_opens || 0} megnyitva
                        </div>
                        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.2rem;">
                            50% scroll: ${fnl.kitero_nps10_campaign?.unique_scroll_50 || 0} • Árazás nézet: ${fnl.kitero_nps10_campaign?.unique_pricing_view || 0}
                        </div>
                    </div>

                    <!-- Foxpost váró -->
                    <div style="background: rgba(249, 115, 22, 0.06); border: 1px solid rgba(249, 115, 22, 0.3); border-radius: 8px; padding: 0.75rem;">
                        <div style="font-size: 0.72rem; color: #f97316; text-transform: uppercase; font-weight: 700;">📦 Feladásra Váró Érmek</div>
                        <div style="font-size: 1.25rem; font-weight: 900; color: #f97316; margin-top: 0.2rem;">
                            ${ops.pending_unshipped_medals || 0} db csomag
                        </div>
                        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.2rem;">
                            Jóváhagyva, de még nincs Foxpost feladási címke
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 5. SZEKCIÓ: VEZETŐI DIAGNÓZIS ÉS DÖNTÉSI AKCIÓTERV -->
        <div>
            <div style="font-size: 0.95rem; font-weight: 800; color: #fff; margin-bottom: 0.85rem; display: flex; align-items: center; gap: 0.45rem;">
                <span>💡</span> <span>5. Vezetői Diagnózis & Döntési Akcióterv (Rule-Based Expert Insights)</span>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.25rem;">
                <!-- Kockázatok és Pénzveszteségek (Pirosas blokk) -->
                <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: var(--radius-md); padding: 1.25rem;">
                    <div style="font-size: 0.88rem; font-weight: 800; color: #f87171; display: flex; align-items: center; gap: 0.45rem; margin-bottom: 0.75rem;">
                        <span>🚨</span> <span>Hol veszít pénzt / Kockázatok:</span>
                    </div>
                    <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.84rem; color: #f1f5f9; line-height: 1.55; display: flex; flex-direction: column; gap: 0.6rem;">
                        ${(ins.leaks_and_risks || []).map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>

                <!-- Növekedési lehetőségek (Zöldes blokk) -->
                <div style="background: rgba(34, 197, 94, 0.05); border: 1px solid rgba(34, 197, 94, 0.35); border-radius: var(--radius-md); padding: 1.25rem;">
                    <div style="font-size: 0.88rem; font-weight: 800; color: #4ade80; display: flex; align-items: center; gap: 0.45rem; margin-bottom: 0.75rem;">
                        <span>🌱</span> <span>Növekedési Lehetőségek (Upsell & Árrés):</span>
                    </div>
                    <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.84rem; color: #f1f5f9; line-height: 1.55; display: flex; flex-direction: column; gap: 0.6rem;">
                        ${(ins.growth_opportunities || []).map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>

                <!-- Következő heti prioritások (Kékesszürke lista) -->
                <div style="background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: var(--radius-md); padding: 1.25rem;">
                    <div style="font-size: 0.88rem; font-weight: 800; color: #38bdf8; display: flex; align-items: center; gap: 0.45rem; margin-bottom: 0.75rem;">
                        <span>📋</span> <span>Következő Heti Prioritások (Akcióterv):</span>
                    </div>
                    <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.84rem; color: #f1f5f9; line-height: 1.55; display: flex; flex-direction: column; gap: 0.6rem;">
                        ${(ins.action_plan || []).map(item => `<li><strong>${item}</strong></li>`).join('')}
                    </ul>
                </div>
            </div>
        </div>
    `;
}
