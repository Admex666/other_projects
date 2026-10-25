// ===== ADMIN AI ASSISTANT (GEMINI 3.8) MODULE =====

let aiChatHistory = [];
let aiIsLoading = false;
let aiLoadingStatusText = "";
let rawSavedAiModel = localStorage.getItem('vs_ai_model') || 'gemini-3.8-flash';
if (rawSavedAiModel.includes('2.5') || rawSavedAiModel.includes('2.0')) {
    rawSavedAiModel = rawSavedAiModel.includes('pro') ? 'gemini-3.8-pro' : 'gemini-3.8-flash';
    localStorage.setItem('vs_ai_model', rawSavedAiModel);
}
let aiModel = rawSavedAiModel;
let aiCustomApiKey = localStorage.getItem('vs_gemini_api_key') || '';
let aiStatusData = null;
let aiDrawerOpen = false;

const AI_QUICK_PROMPTS = [
    {
        icon: '📊',
        label: 'P&L, Készlet & Likvid tőke',
        prompt: 'Kérlek készíts egy teljes pénzügyi és készlet összefoglalót! Hogy áll a Nagy-Kevély és a Prédikálószék éremkészlet, mennyi a jelenlegi likvid tőkénk (Revolut + Stripe), és hogyan alakul a két kampány P&L-je?'
    },
    {
        icon: '📬',
        label: 'Legutóbbi Gmail emailek',
        prompt: 'Nézd meg a vitasteps.team@gmail.com postafiókot! Mik a legutóbbi beérkezett emailek, van-e olvasatlan ügyféllevél vagy fontos értesítés, amire válaszolnunk kell?'
    },
    {
        icon: '⏳',
        label: 'Jóváhagyásra & Feladásra várók',
        prompt: 'Kik azok a futók, akik már beküldték az igazolást és jóváhagyásra várnak, illetve kiknek kell most csomagolni és Foxposttal feladni az érmét?'
    },
    {
        icon: '📈',
        label: 'Meta Ads & Kreatív ROAS elemzés',
        prompt: 'Elemezd a Meta Ads hirdetési kampányokat és kreatívokat! Melyik kreatív hozza a legjobb CPA-t és ROAS-t, és melyiket érdemes lekapcsolni vagy skálázni?'
    },
    {
        icon: '🏃',
        label: 'Még nem igazolt túrázók',
        prompt: 'Hányan neveztek már be a Nagy-Kevély és a Prédikálószék kihívásokra úgy, hogy még nem töltöttek fel teljesítési igazolást? Kik a legrégebb óta várakozók?'
    },
    {
        icon: '💬',
        label: 'Visszajelzések & Következő tájegység',
        prompt: 'Összegezd a teljesítői visszajelzéseket (feedbacks)! Mi az átlagos NPS és érem értékelés, mit dicsérnek legjobban, és melyik következő tájegységre szavaztak a legtöbben?'
    },
    {
        icon: '🎯',
        label: 'Meleg Leadek & Konverzió',
        prompt: 'Hány egyedi leadünk van az adatbázisban, hányan konvertáltak már vásárlóvá, és hány aktív meleg leadnek tudunk még e-mailt küldeni?'
    },
    {
        icon: '🧠',
        label: 'Knowledge Graph & Stratégia',
        prompt: 'Olvasd el a Knowledge Graph INDEX.md-t és foglald össze a VitaSteps 5-pilléres ökoszisztéma stratégiáját és a legfontosabb üzleti döntéseket (ADR-eket)!'
    }
];

function escapeHtmlAi(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Lightweight, clean Markdown to HTML renderer (tables, code blocks, lists, bold, headers)
function renderMarkdownAi(mdText) {
    if (!mdText) return '';
    let text = String(mdText).replace(/\r\n/g, '\n');

    // Extract code blocks first
    const codeBlocks = [];
    text = text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (_, lang, code) => {
        const idx = codeBlocks.length;
        codeBlocks.push(`<pre class="ai-code-block"><code>${escapeHtmlAi(code.trim())}</code></pre>`);
        return `@@CODEBLOCK_${idx}@@`;
    });

    const lines = text.split('\n');
    let html = '';
    let inTable = false;
    let inUl = false;
    let inOl = false;

    const closeListsAndTables = () => {
        if (inTable) { html += '</tbody></table></div>'; inTable = false; }
        if (inUl) { html += '</ul>'; inUl = false; }
        if (inOl) { html += '</ol>'; inOl = false; }
    };

    const formatInline = (s) => {
        let out = escapeHtmlAi(s);
        out = out.replace(/`([^`]+)`/g, '<code class="ai-inline-code">$1</code>');
        out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        out = out.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        return out;
    };

    for (let i = 0; i < lines.length; i++) {
        const rawLine = lines[i];
        const trimmed = rawLine.trim();

        // Check code block placeholder
        if (/^@@CODEBLOCK_\d+@@$/.test(trimmed)) {
            closeListsAndTables();
            const idx = Number(trimmed.replace(/\D/g, ''));
            html += codeBlocks[idx] || '';
            continue;
        }

        // Table detection
        if (trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.split('|').length > 2) {
            const cells = trimmed.slice(1, -1).split('|').map(c => c.trim());
            // Check if separator line like |---|---|
            if (cells.every(c => /^[:\-]+$/.test(c))) {
                continue;
            }
            if (!inTable) {
                closeListsAndTables();
                inTable = true;
                html += '<div class="ai-table-wrap"><table class="ai-md-table"><thead><tr>';
                cells.forEach(c => { html += `<th>${formatInline(c)}</th>`; });
                html += '</tr></thead><tbody>';
            } else {
                html += '<tr>';
                cells.forEach(c => { html += `<td>${formatInline(c)}</td>`; });
                html += '</tr>';
            }
            continue;
        } else if (inTable) {
            html += '</tbody></table></div>';
            inTable = false;
        }

        // Headings
        if (trimmed.startsWith('#### ')) {
            closeListsAndTables();
            html += `<h5 class="ai-h4">${formatInline(trimmed.slice(5))}</h5>`;
            continue;
        }
        if (trimmed.startsWith('### ')) {
            closeListsAndTables();
            html += `<h4 class="ai-h3">${formatInline(trimmed.slice(4))}</h4>`;
            continue;
        }
        if (trimmed.startsWith('## ')) {
            closeListsAndTables();
            html += `<h3 class="ai-h2">${formatInline(trimmed.slice(3))}</h3>`;
            continue;
        }
        if (trimmed.startsWith('# ')) {
            closeListsAndTables();
            html += `<h2 class="ai-h1">${formatInline(trimmed.slice(2))}</h2>`;
            continue;
        }

        // Horizontal rule
        if (/^---+$/.test(trimmed)) {
            closeListsAndTables();
            html += '<hr class="ai-hr">';
            continue;
        }

        // Unordered list
        if (/^[-*•]\s+/.test(trimmed)) {
            if (inOl) { html += '</ol>'; inOl = false; }
            if (!inUl) { html += '<ul class="ai-ul">'; inUl = true; }
            html += `<li>${formatInline(trimmed.replace(/^[-*•]\s+/, ''))}</li>`;
            continue;
        }

        // Ordered list
        if (/^\d+\.\s+/.test(trimmed)) {
            if (inUl) { html += '</ul>'; inUl = false; }
            if (!inOl) { html += '<ol class="ai-ol">'; inOl = true; }
            html += `<li>${formatInline(trimmed.replace(/^\d+\.\s+/, ''))}</li>`;
            continue;
        }

        // Empty line
        if (!trimmed) {
            closeListsAndTables();
            continue;
        }

        // Standard paragraph
        closeListsAndTables();
        html += `<p class="ai-p">${formatInline(trimmed)}</p>`;
    }

    closeListsAndTables();
    return html;
}

async function loadAiAssistantStatus() {
    if (!adminSecret) return;
    try {
        const res = await fetch(`/api/admin-data?type=ai_status&secret=${encodeURIComponent(adminSecret)}`);
        if (res.ok) {
            aiStatusData = await res.json();
            renderAiStatusBar();
        }
    } catch (e) {
        console.warn('AI status check failed:', e);
    }
}

function setAiModel(newModel) {
    aiModel = newModel;
    localStorage.setItem('vs_ai_model', newModel);
    const mainSelect = document.getElementById('ai-model-select-main');
    const drawerSelect = document.getElementById('ai-model-select-drawer');
    if (mainSelect && mainSelect.value !== newModel) mainSelect.value = newModel;
    if (drawerSelect && drawerSelect.value !== newModel) drawerSelect.value = newModel;
}

function saveAiCustomApiKey() {
    const inp = document.getElementById('ai-custom-api-key-input');
    if (!inp) return;
    const val = inp.value.trim();
    aiCustomApiKey = val;
    if (val) {
        localStorage.setItem('vs_gemini_api_key', val);
    } else {
        localStorage.removeItem('vs_gemini_api_key');
    }
    renderAiStatusBar();
    renderAiMessages();
}

function clearAiConversation() {
    aiChatHistory = [];
    renderAiMessages();
}

function renderAiStatusBar() {
    const s = aiStatusData?.status || {};
    const hasKey = Boolean(s.gemini_configured || aiCustomApiKey);
    const gmailLabel = s.gmail_primary || 'vitasteps.team@gmail.com';
    const hasGmail = Boolean(s.gmail_primary);

    const badgesHtml = `
        <span class="ai-conn-badge ${hasKey ? 'ok' : 'warn'}" title="${hasKey ? 'Gemini API csatlakoztatva' : 'Gemini API kulcs szükséges'}">
            🤖 Gemini API ${hasKey ? '✓' : '⚠️'}
        </span>
        <span class="ai-conn-badge ok" title="Supabase PostgreSQL élő kapcsolat">
            🗄️ Supabase DB ✓
        </span>
        <span class="ai-conn-badge ok" title="Stripe & Revolut Pro pénzügyi modul">
            💳 Stripe & Revolut ✓
        </span>
        <span class="ai-conn-badge ok" title="Meta Ads kreatív riportok">
            📊 Meta Ads ✓
        </span>
        <span class="ai-conn-badge ok" title="VitaSteps Knowledge Graph dokumentáció">
            🧠 Knowledge Graph ✓
        </span>
        <span class="ai-conn-badge ${hasGmail ? 'ok' : 'warn'}" title="Gmail IMAP: ${escapeHtmlAi(gmailLabel)}">
            📧 Gmail (${escapeHtmlAi(gmailLabel)}) ${hasGmail ? '✓' : '⚠️'}
        </span>
    `;

    const barEl = document.getElementById('ai-status-badges-bar');
    if (barEl) barEl.innerHTML = badgesHtml;

    const keyBannerEl = document.getElementById('ai-api-key-banner');
    if (keyBannerEl) {
        if (!s.gemini_configured) {
            keyBannerEl.style.display = 'flex';
            const keyInp = document.getElementById('ai-custom-api-key-input');
            if (keyInp && !keyInp.value && aiCustomApiKey) {
                keyInp.value = aiCustomApiKey;
            }
        } else {
            keyBannerEl.style.display = 'none';
        }
    }
}

function renderAiQuickChips(containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = AI_QUICK_PROMPTS.map((q, idx) => `
        <button class="ai-quick-chip" onclick="sendQuickAiPrompt(${idx})" ${aiIsLoading ? 'disabled' : ''}>
            <span>${q.icon}</span>
            <span>${escapeHtmlAi(q.label)}</span>
        </button>
    `).join('');
}

function sendQuickAiPrompt(idx) {
    const item = AI_QUICK_PROMPTS[idx];
    if (!item || aiIsLoading) return;
    sendAiChatMessage(item.prompt);
}

function renderAiMessages() {
    const containers = [
        document.getElementById('ai-chat-messages-main'),
        document.getElementById('ai-chat-messages-drawer')
    ].filter(Boolean);

    const welcomeHtml = `
        <div class="ai-welcome-box">
            <div class="ai-welcome-icon">🤖</div>
            <div class="ai-welcome-title">Szia Ádám! Én vagyok a VitaSteps Admin AI Asszisztens.</div>
            <div class="ai-welcome-sub">
                Közvetlen, valós idejű olvasási hozzáférésem van a <strong>Supabase adatbázishoz</strong> (futók, nevezések, igazolások, Foxpost csomagok, visszajelzések, leadek), a <strong>Revolut & Stripe pénzügyekhez</strong>, a <strong>Meta Ads kreatív riportokhoz</strong>, a <strong>Knowledge Graph</strong> tudásbázishoz és a <strong>vitasteps.team@gmail.com</strong> postafiókhoz.
            </div>
            <div class="ai-welcome-hint">Válassz egy gyors kérdést fent, vagy írj be bármilyen egyedi elemzési kérést!</div>
        </div>
    `;

    let messagesHtml = '';
    if (aiChatHistory.length === 0 && !aiIsLoading) {
        messagesHtml = welcomeHtml;
    } else {
        messagesHtml = aiChatHistory.map(m => {
            if (m.role === 'user') {
                return `
                    <div class="ai-msg-row user">
                        <div class="ai-msg-bubble user">
                            <div class="ai-msg-text">${escapeHtmlAi(m.text)}</div>
                        </div>
                    </div>
                `;
            } else {
                const toolsHtml = Array.isArray(m.tools_used) && m.tools_used.length > 0
                    ? `<div class="ai-tools-used-bar">
                        ${m.tools_used.map(t => `<span class="ai-tool-pill">${escapeHtmlAi(t.label || t.name)}</span>`).join('')}
                       </div>`
                    : '';
                return `
                    <div class="ai-msg-row model">
                        <div class="ai-msg-avatar">🤖</div>
                        <div class="ai-msg-bubble model ${m.isError ? 'error' : ''}">
                            ${toolsHtml}
                            <div class="ai-md-content">${m.isError ? escapeHtmlAi(m.text) : renderMarkdownAi(m.text)}</div>
                            ${m.model ? `<div class="ai-msg-footer">⚡ Modell: ${escapeHtmlAi(m.model)}</div>` : ''}
                        </div>
                    </div>
                `;
            }
        }).join('');

        if (aiIsLoading) {
            messagesHtml += `
                <div class="ai-msg-row model">
                    <div class="ai-msg-avatar">🤖</div>
                    <div class="ai-msg-bubble model loading">
                        <div style="display: flex; align-items: center; gap: 0.65rem;">
                            <span class="loading-spinner"></span>
                            <span>${escapeHtmlAi(aiLoadingStatusText || "Adatbázisok, pénzügyek és postafiók elemzése folyamatban...")}</span>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    containers.forEach(c => {
        c.innerHTML = messagesHtml;
        c.scrollTop = c.scrollHeight;
    });
}

async function sendAiChatMessage(overrideText) {
    if (aiIsLoading) return;

    const mainInput = document.getElementById('ai-chat-input-main');
    const drawerInput = document.getElementById('ai-chat-input-drawer');

    let text = overrideText;
    if (!text) {
        if (aiDrawerOpen && drawerInput && drawerInput.value.trim()) {
            text = drawerInput.value.trim();
        } else if (mainInput && mainInput.value.trim()) {
            text = mainInput.value.trim();
        }
    }

    if (!text) return;

    if (mainInput) mainInput.value = '';
    if (drawerInput) drawerInput.value = '';

    const priorHistory = aiChatHistory
        .filter(h => !h.isError)
        .map(h => ({ role: h.role, text: h.text }));

    aiChatHistory.push({ role: 'user', text });
    aiIsLoading = true;
    aiLoadingStatusText = 'Adatbázisok, pénzügyek és postafiók elemzése folyamatban...';
    renderAiMessages();
    renderAiQuickChips('ai-quick-chips-main');
    renderAiQuickChips('ai-quick-chips-drawer');

    const MAX_CLIENT_RETRIES = 6;
    try {
        for (let attempt = 1; attempt <= MAX_CLIENT_RETRIES; attempt++) {
            const res = await fetch('/api/admin-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    admin_secret: adminSecret,
                    type: 'ai_chat',
                    message: text,
                    history: priorHistory,
                    model: aiModel,
                    api_key_override: aiCustomApiKey || undefined
                })
            });

            const data = await res.json();

            if (!res.ok || data.error) {
                const errText = String(data.message || data.error || '');
                const errLower = errText.toLowerCase();
                const isHighDemand =
                    res.status === 503 ||
                    res.status === 429 ||
                    errLower.includes('high demand') ||
                    errLower.includes('overloaded') ||
                    errLower.includes('try again later') ||
                    errLower.includes('resource exhausted') ||
                    errLower.includes('temporarily unavailable');

                if (isHighDemand && attempt < MAX_CLIENT_RETRIES) {
                    aiLoadingStatusText = `Google AI szerverek terheltek, automatikus újraküldés (${attempt + 1}/${MAX_CLIENT_RETRIES}. kísérlet)...`;
                    renderAiMessages();
                    await new Promise(r => setTimeout(r, 1500 * attempt));
                    continue;
                }

                aiChatHistory.push({
                    role: 'model',
                    text: `❌ ${errText || 'Ismeretlen hiba történt az AI válaszadás során.'}`,
                    isError: true
                });
                if (data.error === 'GEMINI_API_KEY_MISSING') {
                    const keyBannerEl = document.getElementById('ai-api-key-banner');
                    if (keyBannerEl) keyBannerEl.style.display = 'flex';
                }
                break;
            } else {
                aiChatHistory.push({
                    role: 'model',
                    text: data.reply || 'Kész.',
                    model: data.model || aiModel,
                    tools_used: data.tools_used || []
                });
                break;
            }
        }
    } catch (err) {
        aiChatHistory.push({
            role: 'model',
            text: `❌ Hálózati hiba: ${err.message}`,
            isError: true
        });
    } finally {
        aiIsLoading = false;
        aiLoadingStatusText = '';
        renderAiMessages();
        renderAiQuickChips('ai-quick-chips-main');
        renderAiQuickChips('ai-quick-chips-drawer');
    }
}

function handleAiInputKeydown(event, source) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        const inp = document.getElementById(source === 'drawer' ? 'ai-chat-input-drawer' : 'ai-chat-input-main');
        if (inp && inp.value.trim()) {
            sendAiChatMessage(inp.value.trim());
        }
    }
}

function toggleAiDrawer(forceState) {
    const drawer = document.getElementById('ai-floating-drawer');
    const fab = document.getElementById('ai-floating-fab');
    if (!drawer) return;

    aiDrawerOpen = typeof forceState === 'boolean' ? forceState : !aiDrawerOpen;
    drawer.style.display = aiDrawerOpen ? 'flex' : 'none';
    if (fab) {
        fab.classList.toggle('active', aiDrawerOpen);
    }

    if (aiDrawerOpen) {
        if (!aiStatusData) loadAiAssistantStatus();
        renderAiQuickChips('ai-quick-chips-drawer');
        renderAiMessages();
        setTimeout(() => {
            const inp = document.getElementById('ai-chat-input-drawer');
            if (inp) inp.focus();
        }, 80);
    }
}

function loadAiAssistantTab() {
    loadAiAssistantStatus();
    renderAiQuickChips('ai-quick-chips-main');
    renderAiMessages();
    const mainSelect = document.getElementById('ai-model-select-main');
    if (mainSelect) mainSelect.value = aiModel;
    setTimeout(() => {
        const inp = document.getElementById('ai-chat-input-main');
        if (inp) inp.focus();
    }, 80);
}
