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
    const templates = emailData.templates || [];
    const activeTemplate = templates.find(t => t.id === selectedTemplateId) || templates[0] || {};
    
    if (!customSubject && activeTemplate.defaultSubject) {
        customSubject = activeTemplate.defaultSubject;
    }

    let previewHtml = activeTemplate.previewHtml || '';
    if (previewHtml) {
        const testName = 'Kovács Péter (Minta)';
        const unsubUrl = `https://vitasteps.vercel.app/api/unsubscribe?email=pelda@domain.com`;
        const checkoutUrl = 'https://vitasteps.vercel.app/nagykevely/index.html#arak';
        const deadlineStr = '2026. szeptember 27.';
        const daysLeft = emailData.daysRemaining || '3 napod';

        previewHtml = previewHtml
            .replace(/\{\{NAME\}\}/g, testName)
            .replace(/\{\{FIRST_NAME\}\}/g, testName)
            .replace(/\{\{DAYS_LEFT\}\}/g, daysLeft)
            .replace(/\{\{DEADLINE\}\}/g, deadlineStr)
            .replace(/\{\{CHECKOUT_URL\}\}/g, checkoutUrl)
            .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl);
    }

    let html = `
        <!-- 1. KPI Summary Cards -->
        <div class="metrics-grid" style="grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
            <!-- Célközönség -->
            <div class="card" style="background: linear-gradient(145deg, rgba(34, 197, 94, 0.12) 0%, rgba(12, 16, 26, 0.95) 100%); border: 1px solid rgba(34, 197, 94, 0.4);">
                <div class="metric-title" style="color: #4ade80; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">
                    🎯 Célközönség (Kiküldendő)
                </div>
                <div class="metric-value" style="color: #4ade80; font-size: 1.75rem; font-family: 'Outfit', monospace; margin-top: 0.35rem;">
                    ${stats.targetActive} <span style="font-size: 0.9rem; color: #86efac; font-weight: 600;">fő</span>
                </div>
                <div style="font-size: 0.75rem; color: #86efac; margin-top: 0.25rem;">
                    unsubscribed=FALSE & converted=FALSE
                </div>
            </div>

            <!-- Összes regisztrált lead -->
            <div class="card" style="background: var(--surface); border: 1px solid var(--border);">
                <div class="metric-title" style="color: var(--text-mid); font-size: 0.75rem; font-weight: 700;">
                    📥 Összes Letöltő (Leads)
                </div>
                <div class="metric-value" style="color: #fff; font-size: 1.5rem; margin-top: 0.35rem;">
                    ${stats.total} <span style="font-size: 0.85rem; color: var(--text-mid);">fő</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.25rem;">
                    Útvonalat & Kalandkönyvet letöltők
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
                    return `
                    <div onclick="selectEmailTemplate('${t.id}')" style="cursor: pointer; padding: 0.85rem 1rem; border-radius: 8px; border: 2px solid ${isSelected ? '#c4ff00' : 'var(--border)'}; background: ${isSelected ? 'rgba(196, 255, 0, 0.08)' : 'rgba(255, 255, 255, 0.02)'}; transition: all 0.2s;">
                        <div style="font-weight: 800; font-size: 0.88rem; color: ${isSelected ? '#c4ff00' : '#fff'}; margin-bottom: 0.25rem;">
                            ${t.title}
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-mid); line-height: 1.4;">
                            ${t.description}
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
                    Kiválasztott sablon: <strong style="color: #c4ff00;">${activeTemplate.title}</strong> | Célközönség: <strong style="color: #38bdf8;">${stats.targetActive} fő aktív lead</strong>
                </div>
            </div>

            <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
                <button class="btn btn-grey" onclick="triggerEmailConfirmation('test')" style="width: auto; padding: 0.65rem 1.25rem; font-size: 0.88rem; font-weight: 700; border: 1px solid rgba(255,255,255,0.2);">
                    🧪 Teszt Küldés (admexgm@gmail.com)
                </button>
                <button class="btn btn-primary" onclick="triggerEmailConfirmation('live')" style="width: auto; padding: 0.65rem 1.5rem; font-size: 0.88rem; font-weight: 900; background: #c4ff00; color: #000; box-shadow: 0 4px 20px rgba(196, 255, 0, 0.35);">
                    🚀 Éles Kiküldés (${stats.targetActive} fő)
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
                        🚀 Küldés élesben (${stats.targetActive} fő)
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
    const templates = emailData?.templates || [];
    const activeTemplate = templates.find(t => t.id === selectedTemplateId) || {};

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
                    Ez a művelet éles e-mailt küld ki <strong style="color: #fff;">${stats.targetActive} db</strong> meleg leadnek, akiknél <code style="background: rgba(0,0,0,0.4); padding: 2px 4px; border-radius: 3px; color: #fff;">unsubscribed=FALSE</code> és <code style="background: rgba(0,0,0,0.4); padding: 2px 4px; border-radius: 3px; color: #fff;">converted=FALSE</code>!
                </div>
            </div>
            <p><strong>Kiválasztott sablon:</strong> ${activeTemplate.title}</p>
            <p><strong>Tárgymező:</strong> <span style="color: #fff;">${customSubject}</span></p>
            <p><strong>Címzettek száma:</strong> <span style="color: #4ade80; font-weight: 800;">${stats.targetActive} fő</span></p>
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
