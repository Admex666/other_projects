// ===== ADMIN EMAILS & LEAD BROADCAST MODULE =====

let emailData = null;
let selectedTemplateId = 'email_1_3_days_before';
let customSubject = '';
let isBroadcasting = false;

async function loadEmails() {
    const container = document.getElementById('emails-content');
    if (container) {
        container.innerHTML = '<div class="empty-state"><span class="loading-spinner"></span><div style="margin-top:0.5rem">Leadek és e-mail sablonok betöltése...</div></div>';
    }

    try {
        const res = await fetch(`/api/admin-data?type=leads_email&secret=${encodeURIComponent(adminSecret)}`);
        if (!res.ok) throw new Error('Nem sikerült betölteni a hírlevél és lead adatokat.');

        const data = await res.json();
        emailData = data;
        renderEmails();

    } catch (error) {
        console.error('Emails load error:', error);
        if (container) {
            container.innerHTML = `<div class="empty-state" style="color: var(--red);">❌ Hiba: ${error.message}</div>`;
        }
    }
}

function selectEmailTemplate(templateId) {
    selectedTemplateId = templateId;
    const t = emailData?.templates?.find(tmpl => tmpl.id === templateId);
    if (t) {
        customSubject = t.defaultSubject;
    }
    renderEmails();
}

function handleSubjectChange(e) {
    customSubject = e.target.value;
}

function renderEmails() {
    const container = document.getElementById('emails-content');
    if (!container || !emailData) return;

    const stats = emailData.stats || { total: 0, targetActive: 0, converted: 0, unsubscribed: 0 };
    const funnel = emailData.funnel || {
        totalSubscribers: stats.totalRecords || stats.total || 0,
        totalUniqueLeads: stats.total || 0,
        emailClicks: 0,
        checkoutStarts: 0,
        convertedCount: stats.converted || 0,
        convRate: 0,
        unsubscribedCount: stats.unsubscribed || 0,
        unsubRate: 0,
        clickRate: 0,
        checkoutRate: 0,
        nurture: {
            steps: { day0: 0, day1: 0, day3: 0, day5: 0, day7: 0, day10: 0 },
            activeWarmOctoberCount: 0,
            totalOctoberLeads: 0
        }
    };
    const sentMap = emailData.sentEmailsMap || {};
    const templates = emailData.templates || [];
    const activeTemplate = templates.find(t => t.id === selectedTemplateId) || templates[0] || {};

    const alreadySentList = sentMap[selectedTemplateId] || [];
    const alreadySentCount = alreadySentList.length;
    const targetAudienceSize = activeTemplate.targetOnlySentOf
        ? (sentMap[activeTemplate.targetOnlySentOf] || []).length
        : stats.targetActive;
    const pendingToSendCount = Math.max(0, targetAudienceSize - alreadySentCount);
    
    if (!customSubject && activeTemplate.defaultSubject) {
        customSubject = activeTemplate.defaultSubject;
    }

    let previewHtml = activeTemplate.previewHtml || '';
    if (previewHtml) {
        const testName = 'Kovács Péter (Minta)';
        const unsubUrl = `https://vitastepsss.vercel.app/api/unsubscribe?email=pelda@domain.com`;
        const landingUrl = 'https://vitastepsss.vercel.app/nagykevely/index.html';
        const deadlineStr = '2026. szeptember 27.';
        const daysLeft = emailData.daysRemaining || '3 napod';

        previewHtml = previewHtml
            .replace(/\{\{NAME\}\}/g, testName)
            .replace(/\{\{FIRST_NAME\}\}/g, testName)
            .replace(/\{\{DAYS_LEFT\}\}/g, daysLeft)
            .replace(/\{\{DEADLINE\}\}/g, deadlineStr)
            .replace(/\{\{CHECKOUT_URL\}\}/g, landingUrl)
            .replace(/\{\{LANDING_URL\}\}/g, landingUrl)
            .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl);
    }

    const nurtureSteps = funnel.nurture?.steps || { day0: 0, day1: 0, day3: 0, day5: 0, day7: 0, day10: 0 };
    const activeWarmOctCount = funnel.nurture?.activeWarmOctoberCount ?? 19;

    let html = `
        <!-- 0. Lead Funnel & Nurture Lifecycle Visualizer Card -->
        <div style="background: linear-gradient(135deg, rgba(20, 27, 45, 0.95) 0%, rgba(13, 17, 28, 0.98) 100%); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 14px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 1rem; margin-bottom: 1.25rem;">
                <div>
                    <div style="font-size: 1.15rem; font-weight: 900; color: #fff; display: flex; align-items: center; gap: 0.5rem;">
                        <span>🌪️</span> <span>Lead Tölcsér (Funnel) & Konverziós Életciklus</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;">
                        Kalandfüzet lead magnet feliratkozók teljes útja: megnyitás → CTA kattintás → checkout → vásárlás
                    </div>
                </div>
                <div style="display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap;">
                    <span style="font-size: 0.75rem; background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.35); padding: 4px 10px; border-radius: 20px; font-weight: 700;">
                        🎯 Konverzió: ${funnel.convRate}% (${funnel.convertedCount} vásárló)
                    </span>
                    <span style="font-size: 0.75rem; background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); padding: 4px 10px; border-radius: 20px; font-weight: 700;">
                        🔥 Októberi meleg leadek: ${activeWarmOctCount} fő
                    </span>
                </div>
            </div>

            <!-- Funnel Progression Pipeline -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1.25rem;">
                <!-- Step 1: Subscribers -->
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 1rem; position: relative;">
                    <div style="font-size: 0.72rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.04em;">
                        1. Feliratkozás
                    </div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #fff; margin-top: 0.35rem; font-family: 'Outfit', monospace;">
                        ${funnel.totalSubscribers} <span style="font-size: 0.82rem; color: #94a3b8; font-weight: 500;">(${funnel.totalUniqueLeads} egyedi)</span>
                    </div>
                    <div style="font-size: 0.73rem; color: #64748b; margin-top: 0.25rem;">
                        100% bázis (Kalandfüzet)
                    </div>
                    <div style="height: 4px; background: #3b82f6; border-radius: 2px; margin-top: 0.6rem; width: 100%;"></div>
                </div>

                <!-- Step 2: Email Clicks / Kalandkonyv open -->
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 1rem; position: relative;">
                    <div style="font-size: 0.72rem; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.04em;">
                        2. Email CTA / Füzet
                    </div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #38bdf8; margin-top: 0.35rem; font-family: 'Outfit', monospace;">
                        ${funnel.emailClicks} <span style="font-size: 0.82rem; color: #7dd3fc; font-weight: 600;">kattintás</span>
                    </div>
                    <div style="font-size: 0.73rem; color: #7dd3fc; margin-top: 0.25rem;">
                        lead_email_clicked (${funnel.clickRate}% CTR)
                    </div>
                    <div style="height: 4px; background: #38bdf8; border-radius: 2px; margin-top: 0.6rem; width: ${Math.min(100, Math.max(15, funnel.clickRate * 2))}%;"></div>
                </div>

                <!-- Step 3: Checkout Started -->
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 1rem; position: relative;">
                    <div style="font-size: 0.72rem; font-weight: 800; color: #fbbf24; text-transform: uppercase; letter-spacing: 0.04em;">
                        3. Pénztárba lépés
                    </div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #fbbf24; margin-top: 0.35rem; font-family: 'Outfit', monospace;">
                        ${funnel.checkoutStarts} <span style="font-size: 0.82rem; color: #fde68a; font-weight: 600;">indítás</span>
                    </div>
                    <div style="font-size: 0.73rem; color: #fde68a; margin-top: 0.25rem;">
                        lead_checkout_started (${funnel.checkoutRate}% int.)
                    </div>
                    <div style="height: 4px; background: #fbbf24; border-radius: 2px; margin-top: 0.6rem; width: ${Math.min(100, Math.max(15, (funnel.checkoutStarts / Math.max(1, funnel.totalUniqueLeads)) * 100 * 3))}%;"></div>
                </div>

                <!-- Step 4: Converted Buyers -->
                <div style="background: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.35); border-radius: 10px; padding: 1rem; position: relative;">
                    <div style="font-size: 0.72rem; font-weight: 800; color: #4ade80; text-transform: uppercase; letter-spacing: 0.04em;">
                        4. Vásárolt (Konvertált)
                    </div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #4ade80; margin-top: 0.35rem; font-family: 'Outfit', monospace;">
                        ${funnel.convertedCount} <span style="font-size: 0.82rem; color: #86efac; font-weight: 600;">fő</span>
                    </div>
                    <div style="font-size: 0.73rem; color: #86efac; margin-top: 0.25rem;">
                        Konverziós ráta: <strong>${funnel.convRate}%</strong>
                    </div>
                    <div style="height: 4px; background: #4ade80; border-radius: 2px; margin-top: 0.6rem; width: 100%;"></div>
                </div>

                <!-- Step 5: Unsubscribed Exit -->
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 1rem; position: relative;">
                    <div style="font-size: 0.72rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.04em;">
                        5. Leiratkozott
                    </div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #cbd5e1; margin-top: 0.35rem; font-family: 'Outfit', monospace;">
                        ${funnel.unsubscribedCount} <span style="font-size: 0.82rem; color: #94a3b8; font-weight: 500;">fő</span>
                    </div>
                    <div style="font-size: 0.73rem; color: #94a3b8; margin-top: 0.25rem;">
                        Veszteség: ${funnel.unsubRate}% (biztonságos)
                    </div>
                    <div style="height: 4px; background: #64748b; border-radius: 2px; margin-top: 0.6rem; width: 10%;"></div>
                </div>
            </div>

            <!-- Nurture V1 Sequence Progress Pipeline -->
            <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
                    <div style="font-size: 0.85rem; font-weight: 800; color: #f1f5f9; display: flex; align-items: center; gap: 0.45rem;">
                        <span>📬</span> <span>Nurture V1 6-Lépéses Automatizáció Állapota:</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #cbd5e1;">
                        Aktív októberi meleg lead várakozik: <strong style="color: #c4ff00; font-size: 0.85rem;">${activeWarmOctCount} fő</strong>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0.5rem;">
                    <!-- Day 0 -->
                    <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 0.6rem 0.75rem;">
                        <div style="font-size: 0.68rem; color: #38bdf8; font-weight: 800;">DAY 0 • AZONNAL</div>
                        <div style="font-size: 1.15rem; font-weight: 900; color: #fff; margin: 0.2rem 0;">${nurtureSteps.day0} <span style="font-size: 0.72rem; color: #94a3b8;">kiküldve</span></div>
                        <div style="font-size: 0.68rem; color: #94a3b8;">Kalandfüzet + GPX</div>
                    </div>

                    <!-- Day 1 -->
                    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 0.6rem 0.75rem;">
                        <div style="font-size: 0.68rem; color: #cbd5e1; font-weight: 800;">DAY 1 • +24 ÓRA</div>
                        <div style="font-size: 1.15rem; font-weight: 900; color: ${nurtureSteps.day1 > 0 ? '#4ade80' : '#94a3b8'}; margin: 0.2rem 0;">${nurtureSteps.day1} <span style="font-size: 0.72rem; color: #94a3b8;">kiküldve</span></div>
                        <div style="font-size: 0.68rem; color: #94a3b8;">Hasznos túratippek</div>
                    </div>

                    <!-- Day 3 -->
                    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 0.6rem 0.75rem;">
                        <div style="font-size: 0.68rem; color: #cbd5e1; font-weight: 800;">DAY 3 • +72 ÓRA</div>
                        <div style="font-size: 1.15rem; font-weight: 900; color: ${nurtureSteps.day3 > 0 ? '#4ade80' : '#94a3b8'}; margin: 0.2rem 0;">${nurtureSteps.day3} <span style="font-size: 0.72rem; color: #94a3b8;">kiküldve</span></div>
                        <div style="font-size: 0.68rem; color: #94a3b8;">Inspiráció & legendák</div>
                    </div>

                    <!-- Day 5 -->
                    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 0.6rem 0.75rem;">
                        <div style="font-size: 0.68rem; color: #cbd5e1; font-weight: 800;">DAY 5 • +120 ÓRA</div>
                        <div style="font-size: 1.15rem; font-weight: 900; color: ${nurtureSteps.day5 > 0 ? '#4ade80' : '#94a3b8'}; margin: 0.2rem 0;">${nurtureSteps.day5} <span style="font-size: 0.72rem; color: #94a3b8;">kiküldve</span></div>
                        <div style="font-size: 0.68rem; color: #94a3b8;">Célkitűzés & büszkeség</div>
                    </div>

                    <!-- Day 7 -->
                    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 0.6rem 0.75rem;">
                        <div style="font-size: 0.68rem; color: #cbd5e1; font-weight: 800;">DAY 7 • +168 ÓRA</div>
                        <div style="font-size: 1.15rem; font-weight: 900; color: ${nurtureSteps.day7 > 0 ? '#4ade80' : '#94a3b8'}; margin: 0.2rem 0;">${nurtureSteps.day7} <span style="font-size: 0.72rem; color: #94a3b8;">kiküldve</span></div>
                        <div style="font-size: 0.68rem; color: #94a3b8;">Érem emlékajánlat</div>
                    </div>

                    <!-- Day 10 -->
                    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 0.6rem 0.75rem;">
                        <div style="font-size: 0.68rem; color: #cbd5e1; font-weight: 800;">DAY 10 • +240 ÓRA</div>
                        <div style="font-size: 1.15rem; font-weight: 900; color: ${nurtureSteps.day10 > 0 ? '#4ade80' : '#94a3b8'}; margin: 0.2rem 0;">${nurtureSteps.day10} <span style="font-size: 0.72rem; color: #94a3b8;">kiküldve</span></div>
                        <div style="font-size: 0.68rem; color: #94a3b8;">100 db limitált széria</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 1. KPI Summary Cards -->
        <div class="metrics-grid" style="grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
            <!-- Még Kiküldendő Lead -->
            <div class="card" style="background: linear-gradient(145deg, rgba(34, 197, 94, 0.12) 0%, rgba(12, 16, 26, 0.95) 100%); border: 1px solid rgba(34, 197, 94, 0.4);">
                <div class="metric-title" style="color: #4ade80; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">
                    🎯 Még Kiküldendő (Aktív)
                </div>
                <div class="metric-value" style="color: #4ade80; font-size: 1.75rem; font-family: 'Outfit', monospace; margin-top: 0.35rem;">
                    ${pendingToSendCount} <span style="font-size: 0.9rem; color: #86efac; font-weight: 600;">fő</span>
                </div>
                <div style="font-size: 0.75rem; color: #86efac; margin-top: 0.25rem;">
                    ${alreadySentCount > 0 ? `+ ${alreadySentCount} főnek már elküldve` : 'Még egyetlen lead sem kapta meg'}
                </div>
            </div>

            <!-- Összes regisztrált lead -->
            <div class="card" style="background: var(--surface); border: 1px solid var(--border);">
                <div class="metric-title" style="color: var(--text-mid); font-size: 0.75rem; font-weight: 700;">
                    📥 Összes Egyedi Lead
                </div>
                <div class="metric-value" style="color: #fff; font-size: 1.5rem; margin-top: 0.35rem;">
                    ${stats.total} <span style="font-size: 0.85rem; color: var(--text-mid);">fő</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.25rem;">
                    ${stats.totalRecords ? `(${stats.totalRecords} letöltésből összevonva)` : 'Útvonalat & Kalandfüzetet letöltők'}
                </div>
            </div>

            <!-- Már vásárolt -->
            <div class="card" style="background: var(--surface); border: 1px solid var(--border);">
                <div class="metric-title" style="color: #38bdf8; font-size: 0.75rem; font-weight: 700;">
                    🏅 Már Konvertált (Vásárolt)
                </div>
                <div class="metric-value" style="color: #38bdf8; font-size: 1.5rem; margin-top: 0.35rem;">
                    ${stats.converted} <span style="font-size: 0.85rem; color: var(--text-mid);">fő</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.25rem;">
                    Automatikusan kizárva a küldésből
                </div>
            </div>

            <!-- Leiratkozott -->
            <div class="card" style="background: var(--surface); border: 1px solid var(--border);">
                <div class="metric-title" style="color: #94a3b8; font-size: 0.75rem; font-weight: 700;">
                    🚫 Leiratkozott
                </div>
                <div class="metric-value" style="color: #cbd5e1; font-size: 1.5rem; margin-top: 0.35rem;">
                    ${stats.unsubscribed} <span style="font-size: 0.85rem; color: var(--text-mid);">fő</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.25rem;">
                    unsubscribed=TRUE (kizárva)
                </div>
            </div>
        </div>

        <!-- 2. Campaign & Template Selector Bar -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem;">
            <div style="font-size: 0.95rem; font-weight: 800; color: #fff; margin-bottom: 0.85rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
                <span>📑 Válassz kiküldendő E-mail Sablont:</span>
                <span style="font-size: 0.75rem; color: var(--text-mid); font-weight: 500;">Hátralévő idő: <strong>${emailData.daysRemaining || '3 nap'}</strong> (Zárás: Szept. 27.)</span>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.75rem;">
                ${templates.map(t => {
                    const isSelected = t.id === selectedTemplateId;
                    const tSentCount = (sentMap[t.id] || []).length;
                    const tAudienceSize = t.targetOnlySentOf
                        ? (sentMap[t.targetOnlySentOf] || []).length
                        : stats.targetActive;
                    const tPendingCount = Math.max(0, tAudienceSize - tSentCount);
                    return `
                    <div onclick="selectEmailTemplate('${t.id}')" style="cursor: pointer; padding: 0.85rem 1rem; border-radius: 8px; border: 2px solid ${isSelected ? '#c4ff00' : 'var(--border)'}; background: ${isSelected ? 'rgba(196, 255, 0, 0.08)' : 'rgba(255, 255, 255, 0.02)'}; transition: all 0.2s;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.25rem;">
                            <div style="font-weight: 800; font-size: 0.88rem; color: ${isSelected ? '#c4ff00' : '#fff'};">
                                ${t.title}
                            </div>
                            ${tSentCount > 0 ? `<span style="font-size: 0.7rem; background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); padding: 2px 6px; border-radius: 4px; font-weight: 700;">${tSentCount} elküldve</span>` : ''}
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-mid); line-height: 1.4;">
                            ${t.description}
                        </div>
                        <div style="font-size: 0.72rem; color: ${tPendingCount > 0 ? '#4ade80' : '#94a3b8'}; margin-top: 0.4rem; font-weight: 600;">
                            ${tPendingCount > 0 ? `⚡ ${tPendingCount} lead várja` : '✅ Mindenkinek elküldve'}
                        </div>
                    </div>
                    `;
                }).join('')}
            </div>

            <!-- Subject Line Editor -->
            <div style="margin-top: 1.25rem; padding-top: 1rem; border-top: 1px solid var(--border);">
                <label style="display: block; font-size: 0.78rem; font-weight: 700; color: var(--text-mid); margin-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.04em;">
                    ✉️ E-mail Tárgymező (Subject):
                </label>
                <input type="text" value="${customSubject || ''}" oninput="handleSubjectChange(event)" class="input-text" style="width: 100%; margin-bottom: 0; font-size: 0.9rem; font-weight: 600; padding: 0.55rem 0.85rem;" placeholder="E-mail tárgysor...">
                <div style="font-size: 0.72rem; color: var(--text-mid); margin-top: 0.35rem;">
                    Tipp: A <code style="color: #c4ff00; background: rgba(0,0,0,0.3); padding: 2px 4px; border-radius: 3px;">{{NAME}}</code> változó automatikusan a címzett keresztnevére cserélődik.
                </div>
            </div>
        </div>

        <!-- 3. Broadcast Action Control Card with Safety Modal Trigger -->
        <div style="background: linear-gradient(145deg, rgba(18, 24, 36, 0.98) 0%, rgba(12, 16, 26, 0.98) 100%); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; box-shadow: 0 8px 30px rgba(0,0,0,0.4);">
            <div>
                <div style="font-size: 1.05rem; font-weight: 900; color: #fff;">
                    🚀 Kampány Kiküldési Vezérlő
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem;">
                    Kiválasztott sablon: <strong style="color: #c4ff00;">${activeTemplate.title}</strong> | Még kiküldendő: <strong style="color: #38bdf8;">${pendingToSendCount} fő</strong> ${alreadySentCount > 0 ? `| Már megkapta: <strong style="color: #a855f7;">${alreadySentCount} fő</strong>` : ''}
                </div>
            </div>

            <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
                <button class="btn btn-grey" onclick="triggerEmailConfirmation('test')" style="width: auto; padding: 0.65rem 1.25rem; font-size: 0.88rem; font-weight: 700; border: 1px solid rgba(255,255,255,0.2);">
                    🧪 Teszt Küldés (admexgm@gmail.com)
                </button>
                <button class="btn btn-primary" onclick="triggerEmailConfirmation('live')" ${pendingToSendCount === 0 ? 'disabled style="opacity:0.5;"' : ''} style="width: auto; padding: 0.65rem 1.5rem; font-size: 0.88rem; font-weight: 900; background: #c4ff00; color: #000; box-shadow: 0 4px 20px rgba(196, 255, 0, 0.35);">
                    🚀 Éles Kiküldés (${pendingToSendCount} fő még nem kapta meg)
                </button>
            </div>
        </div>

        <!-- 4. Real-time Live Broadcast Progress Log (Hidden by default) -->
        <div id="broadcast-status-box" style="display: none; margin-bottom: 1.5rem;"></div>

        <!-- 5. Live Email Template Preview Box -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                <div style="font-weight: 800; font-size: 0.95rem; color: #fff;">
                    👁️ E-mail Élő Előnézet (Mintával kitöltve)
                </div>
                <div style="font-size: 0.75rem; color: var(--text-mid);">
                    Reszponzív HTML nézet
                </div>
            </div>

            <div style="background: #0b0f19; border: 1px solid var(--border); border-radius: 8px; padding: 10px; overflow-x: auto;">
                <iframe id="email-preview-iframe" style="width: 100%; min-height: 520px; border: none; background: #0b0f19; border-radius: 6px;"></iframe>
            </div>
        </div>

        <!-- 6. Confirmation Safety Modal -->
        <div id="email-confirm-modal" class="modal-backdrop" style="display: none;" onclick="closeEmailConfirmModal()">
            <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 520px; background: #121824; border: 1px solid rgba(196, 255, 0, 0.4); border-radius: 14px; padding: 1.75rem; text-align: left; box-shadow: 0 20px 50px rgba(0,0,0,0.7);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.6rem;">
                    <div id="modal-title" style="font-size: 1.15rem; font-weight: 900; color: #fff;">
                        ⚠️ Biztonsági Megerősítés
                    </div>
                    <button class="modal-close" onclick="closeEmailConfirmModal()" style="position: static; font-size: 1.2rem; color: var(--text-mid); background: none; border: none; cursor: pointer;">✕</button>
                </div>

                <div id="modal-body-content" style="font-size: 0.9rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 1.5rem;">
                    <!-- Injected dynamically -->
                </div>

                <div style="display: flex; justify-content: flex-end; gap: 0.65rem; flex-wrap: wrap;">
                    <button class="btn btn-grey" onclick="closeEmailConfirmModal()" style="width: auto; padding: 0.55rem 1rem; font-size: 0.85rem;">
                        ❌ Mégse
                    </button>
                    <button class="btn btn-grey" id="btn-modal-test" onclick="executeEmailSend('send_test')" style="width: auto; padding: 0.55rem 1.1rem; font-size: 0.85rem; border: 1px solid #38bdf8; color: #38bdf8;">
                        🧪 Küldés tesztben (admexgm@gmail.com)
                    </button>
                    <button class="btn btn-primary" id="btn-modal-live" onclick="executeEmailSend('send_live')" style="width: auto; padding: 0.55rem 1.25rem; font-size: 0.85rem; font-weight: 800; background: #ef4444; color: #fff;">
                        🚀 Küldés élesben (${pendingToSendCount} új főnek)
                    </button>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;

    // Load iframe preview
    setTimeout(() => {
        const iframe = document.getElementById('email-preview-iframe');
        if (iframe && previewHtml) {
            const doc = iframe.contentDocument || iframe.contentWindow.document;
            doc.open();
            doc.write(previewHtml);
            doc.close();
        }
    }, 50);
}

function triggerEmailConfirmation(mode) {
    const modal = document.getElementById('email-confirm-modal');
    const modalBody = document.getElementById('modal-body-content');
    const btnTest = document.getElementById('btn-modal-test');
    const btnLive = document.getElementById('btn-modal-live');
    const stats = emailData?.stats || { targetActive: 0 };
    const sentMap = emailData?.sentEmailsMap || {};
    const templates = emailData?.templates || [];
    const activeTemplate = templates.find(t => t.id === selectedTemplateId) || {};

    const alreadySentList = sentMap[selectedTemplateId] || [];
    const alreadySentCount = alreadySentList.length;
    const targetAudienceSize = activeTemplate.targetOnlySentOf
        ? (sentMap[activeTemplate.targetOnlySentOf] || []).length
        : stats.targetActive;
    const pendingToSendCount = Math.max(0, targetAudienceSize - alreadySentCount);

    if (!modal || !modalBody) return;

    if (mode === 'test') {
        modalBody.innerHTML = `
            <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); padding: 0.85rem 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <strong style="color: #38bdf8;">🧪 Teszt Küldés Mód</strong>
                <div style="font-size: 0.82rem; color: #cbd5e1; margin-top: 0.25rem;">
                    A levél kizárólag a(z) <code style="color: #fff; background: rgba(0,0,0,0.4); padding: 2px 5px; border-radius: 3px;">admexgm@gmail.com</code> címre kerül kiküldésre ellenőrzés céljából.
                </div>
            </div>
            <p><strong>Kiválasztott sablon:</strong> ${activeTemplate.title}</p>
            <p><strong>Tárgymező:</strong> <span style="color: #fff;">[TESZT] ${customSubject}</span></p>
            <p style="margin-top: 0.5rem; font-size: 0.82rem; color: var(--text-mid);">Biztosan elküldöd a teszt e-mailt a megadott tesztfiókra?</p>
        `;
        if (btnTest) btnTest.style.display = 'inline-block';
        if (btnLive) btnLive.style.display = 'none';

    } else if (mode === 'live') {
        modalBody.innerHTML = `
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); padding: 0.85rem 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <strong style="color: #f87171;">⚠️ ÉLES KIKÜLDÉSI FIGYELMEZTETÉS!</strong>
                <div style="font-size: 0.82rem; color: #fca5a5; margin-top: 0.25rem;">
                    Ez a művelet éles e-mailt küld ki <strong style="color: #fff;">${pendingToSendCount} db</strong> új meleg leadnek!
                </div>
            </div>
            <p><strong>Kiválasztott sablon:</strong> ${activeTemplate.title}</p>
            <p><strong>Tárgymező:</strong> <span style="color: #fff;">${customSubject}</span></p>
            <p><strong>Új címzettek száma:</strong> <span style="color: #4ade80; font-weight: 800;">${pendingToSendCount} fő</span></p>
            ${alreadySentCount > 0 ? `<p style="font-size: 0.8rem; color: #94a3b8;">🔒 Korábban már elküldve ennek a sablonnak: <strong>${alreadySentCount} fő</strong> (kizárva, nem kapják meg újra).</p>` : ''}
            <p style="margin-top: 0.75rem; font-size: 0.82rem; color: #fca5a5;">
                Biztosan elindítod az éles kiküldést? A folyamat elindulása után nem visszavonható.
            </p>
        `;
        if (btnTest) btnTest.style.display = 'inline-block';
        if (btnLive) btnLive.style.display = 'inline-block';
    }

    modal.style.display = 'flex';
}

function closeEmailConfirmModal() {
    const modal = document.getElementById('email-confirm-modal');
    if (modal) modal.style.display = 'none';
}

async function executeEmailSend(action) {
    closeEmailConfirmModal();

    const statusBox = document.getElementById('broadcast-status-box');
    if (!statusBox) return;

    statusBox.style.display = 'block';
    statusBox.innerHTML = `
        <div class="card" style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.35); padding: 1.25rem; display: flex; align-items: center; gap: 1rem;">
            <span class="loading-spinner"></span>
            <div>
                <div style="font-weight: 800; color: #38bdf8;">${action === 'send_test' ? 'Teszt e-mail küldése folyamatban...' : 'Éles hírlevél kiküldése folyamatban...'}</div>
                <div style="font-size: 0.8rem; color: var(--text-mid); margin-top: 0.2rem;">Kérlek várj, a levelek küldése folyamatban van a szerveren...</div>
            </div>
        </div>
    `;

    try {
        const res = await fetch('/api/admin-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                admin_secret: adminSecret,
                action: 'leads_email',
                sub_action: action,
                template_id: selectedTemplateId,
                custom_subject: customSubject
            })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || 'Hiba történt a küldés során.');
        }

        if (action === 'send_test') {
            statusBox.innerHTML = `
                <div class="card" style="background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.4); padding: 1.25rem;">
                    <div style="font-weight: 800; color: #4ade80; font-size: 1rem;">✅ Teszt E-mail Sikeresen Elküldve!</div>
                    <div style="font-size: 0.85rem; color: #f1f5f9; margin-top: 0.35rem;">
                        A teszt levél sikeresen megérkezett a(z) <strong>${data.recipient || 'admexgm@gmail.com'}</strong> e-mail címre.
                    </div>
                </div>
            `;
        } else {
            statusBox.innerHTML = `
                <div class="card" style="background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.4); padding: 1.25rem;">
                    <div style="font-weight: 900; color: #4ade80; font-size: 1.1rem;">🎉 Éles Kiküldés Sikeresen Befejeződött!</div>
                    <div style="font-size: 0.9rem; color: #f1f5f9; margin-top: 0.4rem;">
                        Összesen <strong>${data.count} db</strong> e-mail sikeresen elküldve a célközönségnek${data.failed > 0 ? `, <strong>${data.failed} db</strong> sikertelen` : ''}.
                    </div>
                </div>
            `;
        }

        // Frissítjük a statisztikákat
        setTimeout(() => {
            loadEmails();
        }, 3000);

    } catch (err) {
        console.error('Send error:', err);
        statusBox.innerHTML = `
            <div class="card" style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.4); padding: 1.25rem;">
                <div style="font-weight: 800; color: #f87171;">❌ Hiba a küldés során:</div>
                <div style="font-size: 0.85rem; color: #fca5a5; margin-top: 0.25rem;">${err.message}</div>
            </div>
        `;
    }
}
