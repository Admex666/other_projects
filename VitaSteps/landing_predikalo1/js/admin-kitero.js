// ===== ADMIN VITASTEPS KITÉRŐ FUNNEL MODULE =====

let kiteroFunnelData = null;
let kiteroRecipientFilter = 'all'; // 'all', 'opened', 'scrolled', 'pricing', 'leads', 'sent'
let kiteroSearchQuery = '';

async function loadKiteroFunnel() {
    const container = document.getElementById('kitero-content');
    if (container && (!kiteroFunnelData || !kiteroFunnelData.summary)) {
        container.innerHTML = '<div class="empty-state"><span class="loading-spinner"></span><div style="margin-top:0.5rem">Kitérő kampány funnel adatok betöltése Supabase-ből...</div></div>';
    }

    try {
        let data = null;
        const res = await fetch(`/api/admin-data?type=kitero_funnel&secret=${encodeURIComponent(adminSecret)}`);
        if (res.ok) {
            data = await res.json();
        } else {
            // Fallback közvetlenül a kitero api-ra
            const fallbackRes = await fetch('/api/kitero?action=funnel-data');
            if (fallbackRes.ok) {
                data = await fallbackRes.json();
            } else {
                throw new Error('Nem sikerült elérni a szerver funnel végpontját.');
            }
        }

        kiteroFunnelData = data;
        renderKiteroFunnel();
    } catch (err) {
        console.error('Kitero funnel load error:', err);
        if (container) {
            container.innerHTML = `
                <div class="empty-state" style="color: var(--red); padding: 2rem;">
                    <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">⚠️</div>
                    <div style="font-weight: 700;">Hiba a Kitérő funnel adatok betöltésekor</div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 0.35rem;">${err.message}</div>
                    <button class="btn btn-primary" onclick="loadKiteroFunnel()" style="margin-top: 1rem; width: auto;">🔄 Újrapróbálás</button>
                </div>
            `;
        }
    }
}

function setKiteroRecipientFilter(filter) {
    kiteroRecipientFilter = filter;
    document.querySelectorAll('#kitero-filter-tabs .mkt-tab').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById(`kitero-tab-${filter}`);
    if (btn) btn.classList.add('active');
    renderKiteroRecipientTable();
}

function handleKiteroSearch(e) {
    kiteroSearchQuery = (e.target.value || '').toLowerCase().trim();
    renderKiteroRecipientTable();
}

function renderKiteroFunnel() {
    const container = document.getElementById('kitero-content');
    if (!container || !kiteroFunnelData) return;

    const summary = kiteroFunnelData.summary || {};
    const recipients = kiteroFunnelData.recipients || [];

    const totalInCsv = summary.total_recipients || recipients.length || 0;
    const sentCount = summary.sent_count || 0;
    const isLive = summary.is_live_campaign;

    const baseCount = sentCount > 0 ? sentCount : totalInCsv;

    const totalOpens = summary.total_opens || 0;
    const uniqueOpeners = summary.unique_openers || 0;
    const openRate = summary.open_rate_pct || 0;

    const uniqueClickers = summary.unique_clickers || 0;
    const clickRate = summary.click_rate_pct || 0;

    const uniqueScrollers = summary.unique_scrollers_50 || 0;
    const scrollRate = summary.scroll_50_rate_pct || 0;
    const scrollFromOpens = summary.scroll_50_from_opens_pct || 0;

    const uniquePricing = summary.unique_pricing_viewers || 0;
    const pricingRate = summary.pricing_view_rate_pct || 0;
    const pricingFromOpens = summary.pricing_from_opens_pct || 0;

    const uniqueLeads = summary.unique_leads || 0;
    const leadRate = summary.lead_rate_pct || 0;
    const leadFromPricing = summary.lead_from_pricing_pct || 0;

    container.innerHTML = `
        <!-- Fejléc & Vezérlő Sáv -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <div style="display: flex; align-items: center; gap: 0.65rem;">
                    <span style="font-size: 1.4rem;">🚶</span>
                    <h2 style="font-size: 1.3rem; font-weight: 800; color: #fff; margin: 0;">
                        VitaSteps Kitérő – NPS=10 Kampány Funnel
                    </h2>
                    <span style="background: ${isLive ? 'rgba(52, 211, 153, 0.15)' : 'rgba(250, 204, 21, 0.15)'}; color: ${isLive ? '#34d399' : '#facc15'}; border: 1px solid ${isLive ? 'rgba(52, 211, 153, 0.35)' : 'rgba(250, 204, 21, 0.35)'}; padding: 3px 10px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase;">
                        ${isLive ? '🟢 Éles Kampány Aktív' : '🟡 Kiküldés Előtti Mód'}
                    </span>
                </div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 0.4rem;">
                    A korábbi túraérmes NPS=10 vásárlók teljes viselkedési tölcsére és validációja (Pixel + Analytics Events + Leadek).
                </div>
            </div>

            <div style="display: flex; gap: 0.65rem; align-items: center;">
                <button class="btn btn-grey" onclick="loadKiteroFunnel()" style="padding: 0.55rem 1.1rem; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 0.4rem;">
                    <span>🔄</span> <span>Élő Adatok Frissítése</span>
                </button>
                <a href="/kitero" target="_blank" class="btn btn-primary" style="padding: 0.55rem 1.1rem; font-size: 0.85rem; text-decoration: none; display: inline-flex; align-items: center; gap: 0.4rem; background: #365A45; border-color: #294434;">
                    <span>↗️</span> <span>Landing Megnyitása</span>
                </a>
            </div>
        </div>

        <!-- 5 FŐ TÖLCSÉR KPI KÁRTYA -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
            
            <!-- 1. KIKÜLDÖTT EMAILEK -->
            <div style="background: var(--surface); border: 1px solid var(--border); border-top: 4px solid #94a3b8; border-radius: var(--radius-md); padding: 1.2rem;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">
                    1. Kiküldött E-mailek
                </div>
                <div style="font-size: 2.1rem; font-weight: 900; color: #fff; line-height: 1.1;">
                    ${sentCount} <span style="font-size: 1.05rem; font-weight: 600; color: #64748b;">/ ${totalInCsv}</span>
                </div>
                <div style="margin-top: 0.55rem; font-size: 0.78rem; color: #94a3b8;">
                    ${isLive ? '✅ Kiküldve a címzetteknek' : '⏳ Még nem indult a kiküldés'}
                </div>
                <div style="margin-top: 0.4rem; height: 4px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden;">
                    <div style="height: 100%; width: ${totalInCsv > 0 ? (sentCount / totalInCsv * 100) : 0}%; background: #94a3b8;"></div>
                </div>
            </div>

            <!-- 2. MEGNYITÁSOK -->
            <div style="background: var(--surface); border: 1px solid var(--border); border-top: 4px solid #38bdf8; border-radius: var(--radius-md); padding: 1.2rem;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">
                    2. Megnyitások (Open Rate)
                </div>
                <div style="font-size: 2.1rem; font-weight: 900; color: #38bdf8; line-height: 1.1;">
                    ${uniqueOpeners} <span style="font-size: 1.05rem; font-weight: 700; color: #7dd3fc;">(${openRate}%)</span>
                </div>
                <div style="margin-top: 0.55rem; font-size: 0.78rem; color: #94a3b8;">
                    Összes megnyitás: <strong style="color: #fff;">${totalOpens} db</strong> pixel esemény
                </div>
                <div style="margin-top: 0.4rem; height: 4px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden;">
                    <div style="height: 100%; width: ${openRate}%; background: #38bdf8;"></div>
                </div>
            </div>

            <!-- 3. 50% GÖRGETŐK -->
            <div style="background: var(--surface); border: 1px solid var(--border); border-top: 4px solid #facc15; border-radius: var(--radius-md); padding: 1.2rem;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #facc15; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">
                    3. 50% Fölé Görgetők
                </div>
                <div style="font-size: 2.1rem; font-weight: 900; color: #facc15; line-height: 1.1;">
                    ${uniqueScrollers} <span style="font-size: 1.05rem; font-weight: 700; color: #fde047;">(${scrollRate}%)</span>
                </div>
                <div style="margin-top: 0.55rem; font-size: 0.78rem; color: #94a3b8;">
                    Megnyitók <strong style="color: #fff;">${scrollFromOpens}%</strong>-a görgetett a feléig
                </div>
                <div style="margin-top: 0.4rem; height: 4px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden;">
                    <div style="height: 100%; width: ${scrollRate}%; background: #facc15;"></div>
                </div>
            </div>

            <!-- 4. ÉRTÉKAJÁNLATIG ELÉRŐK -->
            <div style="background: var(--surface); border: 1px solid var(--border); border-top: 4px solid #c084fc; border-radius: var(--radius-md); padding: 1.2rem;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #c084fc; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">
                    4. Értékajánlatig Elérők
                </div>
                <div style="font-size: 2.1rem; font-weight: 900; color: #c084fc; line-height: 1.1;">
                    ${uniquePricing} <span style="font-size: 1.05rem; font-weight: 700; color: #e9d5ff;">(${pricingRate}%)</span>
                </div>
                <div style="margin-top: 0.55rem; font-size: 0.78rem; color: #94a3b8;">
                    Látta az árat & értéket (pricing blokk)
                </div>
                <div style="margin-top: 0.4rem; height: 4px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden;">
                    <div style="height: 100%; width: ${pricingRate}%; background: #c084fc;"></div>
                </div>
            </div>

            <!-- 5. LEADET ADÓK -->
            <div style="background: var(--surface); border: 1px solid var(--border); border-top: 4px solid #34d399; border-radius: var(--radius-md); padding: 1.2rem;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #34d399; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">
                    5. Leadet Adók (Konverzió)
                </div>
                <div style="font-size: 2.1rem; font-weight: 900; color: #34d399; line-height: 1.1;">
                    ${uniqueLeads} <span style="font-size: 1.05rem; font-weight: 700; color: #a7f3d0;">(${leadRate}%)</span>
                </div>
                <div style="margin-top: 0.55rem; font-size: 0.78rem; color: #94a3b8;">
                    Ajánlatot látók <strong style="color: #fff;">${leadFromPricing}%</strong>-a adott leadet!
                </div>
                <div style="margin-top: 0.4rem; height: 4px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden;">
                    <div style="height: 100%; width: ${leadRate}%; background: #34d399;"></div>
                </div>
            </div>

        </div>

        <!-- VIZUÁLIS TÖLCSÉR FOLYAMAT ÁBRÁZOLÁS -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;">
            <div style="font-size: 0.92rem; font-weight: 800; color: #fff; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between;">
                <span>📈 Tölcsér Lépések & Lemorzsolódás</span>
                <span style="font-size: 0.78rem; color: #94a3b8; font-weight: 500;">Bázis: ${baseCount} fő</span>
            </div>

            <div style="display: flex; flex-direction: column; gap: 0.85rem;">
                <!-- Step 1 -->
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.3rem;">
                        <span style="color: #fff; font-weight: 600;">1. Kiküldött e-mailek</span>
                        <span style="color: #94a3b8;">${sentCount} fő (100%)</span>
                    </div>
                    <div style="height: 10px; background: rgba(255,255,255,0.06); border-radius: 5px; overflow: hidden;">
                        <div style="height: 100%; width: 100%; background: #94a3b8;"></div>
                    </div>
                </div>

                <!-- Step 2 -->
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.3rem;">
                        <span style="color: #38bdf8; font-weight: 600;">2. E-mail megnyitása (Open Pixel)</span>
                        <span style="color: #7dd3fc;">${uniqueOpeners} fő (${openRate}%) &bull; ${totalOpens} megnyitás</span>
                    </div>
                    <div style="height: 10px; background: rgba(255,255,255,0.06); border-radius: 5px; overflow: hidden;">
                        <div style="height: 100%; width: ${openRate}%; background: #38bdf8;"></div>
                    </div>
                </div>

                <!-- Step 2.5 -->
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.3rem;">
                        <span style="color: #60a5fa; font-weight: 600;">→ Átkattintás a Kitérő oldalra</span>
                        <span style="color: #93c5fd;">${uniqueClickers} fő (${clickRate}%)</span>
                    </div>
                    <div style="height: 10px; background: rgba(255,255,255,0.06); border-radius: 5px; overflow: hidden;">
                        <div style="height: 100%; width: ${clickRate}%; background: #60a5fa;"></div>
                    </div>
                </div>

                <!-- Step 3 -->
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.3rem;">
                        <span style="color: #facc15; font-weight: 600;">3. Legalább 50%-ig görgetett a bemutatón</span>
                        <span style="color: #fde047;">${uniqueScrollers} fő (${scrollRate}%)</span>
                    </div>
                    <div style="height: 10px; background: rgba(255,255,255,0.06); border-radius: 5px; overflow: hidden;">
                        <div style="height: 100%; width: ${scrollRate}%; background: #facc15;"></div>
                    </div>
                </div>

                <!-- Step 4 -->
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.3rem;">
                        <span style="color: #c084fc; font-weight: 600;">4. Elérte az értékajánlatot (Ár & Csomag szekció)</span>
                        <span style="color: #e9d5ff;">${uniquePricing} fő (${pricingRate}%)</span>
                    </div>
                    <div style="height: 10px; background: rgba(255,255,255,0.06); border-radius: 5px; overflow: hidden;">
                        <div style="height: 100%; width: ${pricingRate}%; background: #c084fc;"></div>
                    </div>
                </div>

                <!-- Step 5 -->
                <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.3rem;">
                        <span style="color: #34d399; font-weight: 700;">5. Korai hozzáférés lead beküldése (Név + Email)</span>
                        <span style="color: #a7f3d0; font-weight: 700;">${uniqueLeads} fő (${leadRate}%)</span>
                    </div>
                    <div style="height: 10px; background: rgba(255,255,255,0.06); border-radius: 5px; overflow: hidden;">
                        <div style="height: 100%; width: ${leadRate}%; background: #34d399;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- CÍMZETTI TÁBLÁZAT FEJLÉC ÉS SZŰRŐK -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.25rem 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.2rem;">
                <div>
                    <h3 style="font-size: 1.05rem; font-weight: 800; color: #fff; margin: 0;">
                        👥 Egyedi Címzetti Funnel Státuszok
                    </h3>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem;">
                        A CSV-ben szereplő ${recipients.length} vásárló egyedi lépései és pixelaktivitása
                    </div>
                </div>

                <div style="display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap;">
                    <!-- Keresőmező -->
                    <input type="text" 
                           placeholder="🔍 Keresés név, email vagy CID alapján..." 
                           oninput="handleKiteroSearch(event)" 
                           style="background: rgba(0,0,0,0.25); border: 1px solid var(--border); color: #fff; padding: 0.45rem 0.85rem; border-radius: 8px; font-size: 0.82rem; min-width: 250px;">

                    <!-- Szűrőgombok -->
                    <div style="display: flex; gap: 0.35rem;" id="kitero-filter-tabs">
                        <button class="mkt-tab ${kiteroRecipientFilter === 'all' ? 'active' : ''}" onclick="setKiteroRecipientFilter('all')" id="kitero-tab-all">Összes</button>
                        <button class="mkt-tab ${kiteroRecipientFilter === 'opened' ? 'active' : ''}" onclick="setKiteroRecipientFilter('opened')" id="kitero-tab-opened">Megnyitotta</button>
                        <button class="mkt-tab ${kiteroRecipientFilter === 'scrolled' ? 'active' : ''}" onclick="setKiteroRecipientFilter('scrolled')" id="kitero-tab-scrolled">Görgetett 50%</button>
                        <button class="mkt-tab ${kiteroRecipientFilter === 'pricing' ? 'active' : ''}" onclick="setKiteroRecipientFilter('pricing')" id="kitero-tab-pricing">Ajánlatig ért</button>
                        <button class="mkt-tab ${kiteroRecipientFilter === 'leads' ? 'active' : ''}" onclick="setKiteroRecipientFilter('leads')" id="kitero-tab-leads">🎯 Lead</button>
                    </div>
                </div>
            </div>

            <!-- Táblázat Konténer -->
            <div id="kitero-recipients-table-container">
                <!-- Rendered dynamically -->
            </div>
        </div>
    `;

    renderKiteroRecipientTable();
}

function renderKiteroRecipientTable() {
    const tableContainer = document.getElementById('kitero-recipients-table-container');
    if (!tableContainer || !kiteroFunnelData) return;

    let recipients = kiteroFunnelData.recipients || [];

    // Szűrés típus alapján
    if (kiteroRecipientFilter === 'opened') {
        recipients = recipients.filter(r => r.opened);
    } else if (kiteroRecipientFilter === 'scrolled') {
        recipients = recipients.filter(r => r.scrolled_50);
    } else if (kiteroRecipientFilter === 'pricing') {
        recipients = recipients.filter(r => r.viewed_pricing);
    } else if (kiteroRecipientFilter === 'leads') {
        recipients = recipients.filter(r => r.is_lead);
    }

    // Szűrés keresőkifejezés alapján
    if (kiteroSearchQuery) {
        recipients = recipients.filter(r => 
            (r.email || '').toLowerCase().includes(kiteroSearchQuery) ||
            (r.name || '').toLowerCase().includes(kiteroSearchQuery) ||
            (r.all_names || '').toLowerCase().includes(kiteroSearchQuery) ||
            (r.cid || '').toLowerCase().includes(kiteroSearchQuery)
        );
    }

    if (recipients.length === 0) {
        tableContainer.innerHTML = `
            <div style="text-align: center; padding: 2.5rem; color: #94a3b8; font-size: 0.88rem;">
                Nincs a szűrésnek megfelelő címzett.
            </div>
        `;
        return;
    }

    let rowsHtml = '';
    recipients.forEach(r => {
        const sentBadge = r.sent 
            ? `<span style="background: rgba(52, 211, 153, 0.15); color: #34d399; padding: 2px 7px; border-radius: 4px; font-size: 0.72rem; font-weight: 700;">✅ Igen</span>`
            : `<span style="background: rgba(148, 163, 184, 0.15); color: #94a3b8; padding: 2px 7px; border-radius: 4px; font-size: 0.72rem;">❌ Nem</span>`;

        const openBadge = r.opened
            ? `<span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">✅ Igen (${r.open_count}x)</span>`
            : `<span style="color: #64748b; font-size: 0.75rem;">❌ Nem</span>`;

        const scrollBadge = r.scrolled_50
            ? `<span style="background: rgba(250, 204, 21, 0.15); color: #facc15; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">✅ Igen</span>`
            : `<span style="color: #64748b; font-size: 0.75rem;">❌ Nem</span>`;

        const pricingBadge = r.viewed_pricing
            ? `<span style="background: rgba(192, 132, 252, 0.15); color: #c084fc; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">✅ Igen</span>`
            : `<span style="color: #64748b; font-size: 0.75rem;">❌ Nem</span>`;

        const leadBadge = r.is_lead
            ? `<span style="background: rgba(52, 211, 153, 0.22); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.4); padding: 3px 9px; border-radius: 4px; font-size: 0.78rem; font-weight: 800;">🎯 LEAD!</span>`
            : `<span style="color: #64748b; font-size: 0.75rem;">❌ Nem</span>`;

        rowsHtml += `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.83rem; transition: background 0.15s ease;" onmouseover="this.style.background='rgba(255,255,255,0.02)'" onmouseout="this.style.background='transparent'">
                <td style="padding: 0.75rem 0.6rem;">
                    <div style="font-weight: 700; color: #fff;">${r.name}</div>
                    <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.15rem;">${r.email}</div>
                    ${r.all_names && r.all_names !== r.name ? `<div style="font-size: 0.68rem; color: #64748b;">${r.all_names}</div>` : ''}
                </td>
                <td style="padding: 0.75rem 0.6rem;">
                    <code style="background: rgba(0,0,0,0.3); padding: 2px 5px; border-radius: 4px; color: #7dd3fc; font-size: 0.72rem;">${r.cid}</code>
                </td>
                <td style="padding: 0.75rem 0.6rem; text-align: center;">
                    ${sentBadge}
                </td>
                <td style="padding: 0.75rem 0.6rem; text-align: center;">
                    ${openBadge}
                </td>
                <td style="padding: 0.75rem 0.6rem; text-align: center;">
                    ${scrollBadge}
                </td>
                <td style="padding: 0.75rem 0.6rem; text-align: center;">
                    ${pricingBadge}
                </td>
                <td style="padding: 0.75rem 0.6rem; text-align: center;">
                    ${leadBadge}
                </td>
            </tr>
        `;
    });

    tableContainer.innerHTML = `
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                <thead>
                    <tr style="border-bottom: 1px solid var(--border); font-size: 0.74rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">
                        <th style="padding: 0.65rem 0.6rem;">Címzett (Név & Email)</th>
                        <th style="padding: 0.65rem 0.6rem;">CID</th>
                        <th style="padding: 0.65rem 0.6rem; text-align: center;">Kiküldve?</th>
                        <th style="padding: 0.65rem 0.6rem; text-align: center;">Megnyitotta?</th>
                        <th style="padding: 0.65rem 0.6rem; text-align: center;">Görgetett 50%?</th>
                        <th style="padding: 0.65rem 0.6rem; text-align: center;">Elérte az ajánlatot?</th>
                        <th style="padding: 0.65rem 0.6rem; text-align: center;">Lead?</th>
                    </tr>
                </thead>
                <tbody>
                    ${rowsHtml}
                </tbody>
            </table>
        </div>
    `;
}
