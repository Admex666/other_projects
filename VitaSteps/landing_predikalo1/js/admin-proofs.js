// ===== ADMIN PROOFS & RUNNERS MODULE =====

let pendingSubFilter = 'all'; // 'all', 'submitted', 'unsubmitted'
let pendingCampaignFilter = 'all'; // 'all', 'predikalo', 'pilis'
let pendingSearchQuery = '';
let pendingHideTest = true;

function updateStats() {
    const validRuns = allRuns.filter(r => !pendingHideTest || !isTestRun(r));
    const proofPending = validRuns.filter(r => r.proof_submitted && !r.completed).length;
    const notSubmitted = validRuns.filter(r => !r.proof_submitted && !r.completed).length;
    const approved = validRuns.filter(r => r.completed).length;
    const total = validRuns.length;

    const statsEl = document.getElementById('stats-bar');
    if (statsEl) {
        statsEl.innerHTML = `
            <div class="stat-chip">📥 Igazolásra vár: <strong>${proofPending}</strong></div>
            <div class="stat-chip">🏃 Még nem igazolt: <strong>${notSubmitted}</strong></div>
            <div class="stat-chip">✅ Jóváhagyott: <strong>${approved}</strong></div>
            <div class="stat-chip">📋 Összes nevezés: <strong>${total}</strong></div>
        `;
    }

    // Éremkészlet és kampány statisztikák
    const pilisRuns = validRuns.filter(r => isPilisRun(r));
    const predikaloRuns = validRuns.filter(r => !isPilisRun(r));

    const pilisLimit = CAMPAIGNS_CONFIG.pilis?.limit || 100;
    const predikaloLimit = CAMPAIGNS_CONFIG.predikaloszek?.limit || 100;

    const pilisSold = pilisRuns.length;
    const pilisRemaining = Math.max(0, pilisLimit - pilisSold);
    const pilisPct = ((pilisSold / pilisLimit) * 100).toFixed(0);

    const predikaloSold = predikaloRuns.length;
    const predikaloRemaining = Math.max(0, predikaloLimit - predikaloSold);
    const predikaloPct = ((predikaloSold / predikaloLimit) * 100).toFixed(0);

    const totalLimit = pilisLimit + predikaloLimit;
    const totalSold = pilisSold + predikaloSold;
    const totalRemaining = pilisRemaining + predikaloRemaining;
    const totalPct = ((totalSold / totalLimit) * 100).toFixed(0);

    const invEl = document.getElementById('inventory-bar');
    if (invEl) {
        invEl.innerHTML = `
            <div class="inventory-grid">
                <!-- Nagy-Kevély Készlet Kártya -->
                <div class="inventory-card" style="border-left: 4px solid #c4ff00; background: linear-gradient(145deg, rgba(196, 255, 0, 0.04) 0%, rgba(12, 15, 21, 0.95) 100%);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.35rem;">
                        <div>
                            <span style="font-size: 0.78rem; font-weight: 800; color: #c4ff00; text-transform: uppercase; letter-spacing: 0.06em;">
                                🌌 A Nagy-Kevély csillagai
                            </span>
                            <div style="font-size: 1.5rem; font-weight: 900; font-family: 'Outfit', sans-serif; color: #fff; margin-top: 0.2rem;">
                                ${pilisRemaining} db <span style="font-size: 0.85rem; font-weight: 600; color: #a1a1aa;">szabad érem maradt</span>
                            </div>
                        </div>
                        <span class="badge" style="background: rgba(196, 255, 0, 0.12); color: #c4ff00; border: 1px solid rgba(196, 255, 0, 0.35); font-weight: 800;">
                            ${pilisSold} / ${pilisLimit} eladva (${pilisPct}%)
                        </span>
                    </div>
                    <div class="inventory-progress-bg">
                        <div class="inventory-progress-fill" style="width: ${pilisPct}%; background: #c4ff00;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-mid); margin-top: 0.4rem;">
                        <span>✅ Teljesítve: <strong style="color:#fff;">${pilisRuns.filter(r => r.completed).length} db</strong></span>
                        <span>📦 Postázva: <strong style="color:#fff;">${pilisRuns.filter(r => r.completed && getShipment(r).shipped).length} db</strong></span>
                        <span>⏳ Igazolatlan: <strong style="color:#f59e0b;">${pilisRuns.filter(r => !r.completed).length} db</strong></span>
                    </div>
                </div>

                <!-- Prédikálószék Készlet Kártya -->
                <div class="inventory-card" style="border-left: 4px solid #38bdf8; background: linear-gradient(145deg, rgba(56, 189, 248, 0.04) 0%, rgba(12, 15, 21, 0.95) 100%);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.35rem;">
                        <div>
                            <span style="font-size: 0.78rem; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.06em;">
                                🏔️ Prédikálószék Vertical
                            </span>
                            <div style="font-size: 1.5rem; font-weight: 900; font-family: 'Outfit', sans-serif; color: #fff; margin-top: 0.2rem;">
                                ${predikaloRemaining} db <span style="font-size: 0.85rem; font-weight: 600; color: #a1a1aa;">szabad érem maradt</span>
                            </div>
                        </div>
                        <span class="badge" style="background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); font-weight: 800;">
                            ${predikaloSold} / ${predikaloLimit} eladva (${predikaloPct}%)
                        </span>
                    </div>
                    <div class="inventory-progress-bg">
                        <div class="inventory-progress-fill" style="width: ${predikaloPct}%; background: #38bdf8;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-mid); margin-top: 0.4rem;">
                        <span>✅ Teljesítve: <strong style="color:#fff;">${predikaloRuns.filter(r => r.completed).length} db</strong></span>
                        <span>📦 Postázva: <strong style="color:#fff;">${predikaloRuns.filter(r => r.completed && getShipment(r).shipped).length} db</strong></span>
                        <span>⏳ Igazolatlan: <strong style="color:#f59e0b;">${predikaloRuns.filter(r => !r.completed).length} db</strong></span>
                    </div>
                </div>

                <!-- Összesített Készlet Kártya -->
                <div class="inventory-card" style="border-left: 4px solid #a855f7; background: linear-gradient(145deg, rgba(168, 85, 247, 0.04) 0%, rgba(12, 15, 21, 0.95) 100%);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.35rem;">
                        <div>
                            <span style="font-size: 0.78rem; font-weight: 800; color: #c084fc; text-transform: uppercase; letter-spacing: 0.06em;">
                                🏅 Összesített Éremkészlet
                            </span>
                            <div style="font-size: 1.5rem; font-weight: 900; font-family: 'Outfit', sans-serif; color: #fff; margin-top: 0.2rem;">
                                ${totalRemaining} db <span style="font-size: 0.85rem; font-weight: 600; color: #a1a1aa;">szabad / ${totalLimit} limit</span>
                            </div>
                        </div>
                        <span class="badge" style="background: rgba(168, 85, 247, 0.12); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.35); font-weight: 800;">
                            ${totalSold} db eladva (${totalPct}%)
                        </span>
                    </div>
                    <div class="inventory-progress-bg">
                        <div class="inventory-progress-fill" style="width: ${totalPct}%; background: #a855f7;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-mid); margin-top: 0.4rem;">
                        <span>✅ Összes jóváhagyva: <strong style="color:#fff;">${approved} db</strong></span>
                        <span>📦 Összes feladva: <strong style="color:#fff;">${validRuns.filter(r => r.completed && getShipment(r).shipped).length} db</strong></span>
                    </div>
                </div>
            </div>
        `;
    }
}

function setFilter(filter) {
    currentFilter = filter;
    document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
    const tabBtn = document.getElementById(`tab-${filter}`);
    if (tabBtn) tabBtn.classList.add('active');

    const isMkt = filter === 'marketing';
    const isFin = filter === 'finance';
    const proofListEl = document.getElementById('proof-list');
    const mktEl = document.getElementById('section-marketing');
    const finEl = document.getElementById('section-finance');

    if (proofListEl) proofListEl.style.display = (isMkt || isFin) ? 'none' : '';
    if (mktEl) mktEl.style.display = isMkt ? 'block' : 'none';
    if (finEl) finEl.style.display = isFin ? 'block' : 'none';

    if (isFin) {
        loadFinance();
    } else if (isMkt) {
        loadMarketing();
    } else {
        renderList();
    }
}

function setPendingSubFilter(sub) {
    pendingSubFilter = sub;
    renderList();
}

function setPendingCampaignFilter(camp) {
    pendingCampaignFilter = camp;
    renderList();
}

function handlePendingSearch(e) {
    pendingSearchQuery = e.target.value;
    renderList();
}

function togglePendingHideTest(el) {
    pendingHideTest = el.checked;
    logisticsHideTest = el.checked;
    updateStats();
    renderList();
}

function renderList() {
    const container = document.getElementById('proof-list');
    if (!container) return;

    if (currentFilter === 'logistics') {
        renderLogistics(container);
        return;
    }

    let runs = [];
    if (currentFilter === 'pending') {
        runs = allRuns.filter(r => !r.completed);
        if (pendingSubFilter === 'submitted') runs = runs.filter(r => r.proof_submitted);
        if (pendingSubFilter === 'unsubmitted') runs = runs.filter(r => !r.proof_submitted);
    } else if (currentFilter === 'approved') {
        runs = allRuns.filter(r => r.completed);
    } else {
        runs = [...allRuns];
    }

    if (pendingHideTest) runs = runs.filter(r => !isTestRun(r));

    if (pendingCampaignFilter !== 'all') {
        runs = runs.filter(r => {
            const isPilis = r.campaign === 'pilis' || (r.serial_number || '').includes('-PK') || (r.serial_number || '').includes('999');
            return pendingCampaignFilter === 'pilis' ? isPilis : !isPilis;
        });
    }

    if (pendingSearchQuery) {
        const q = pendingSearchQuery.toLowerCase();
        runs = runs.filter(r => {
            const name = (r.name || r.runners?.name || '').toLowerCase();
            const email = (r.runners?.email || '').toLowerCase();
            const serial = (r.serial_number || '').toLowerCase();
            return name.includes(q) || email.includes(q) || serial.includes(q);
        });
    }

    if (currentFilter === 'pending') {
        renderPendingProofs(runs, container);
    } else {
        renderRunsTable(runs, container);
    }
}

function renderPendingProofs(runs, container) {
    let toolbarHtml = `
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1.5rem; display: flex; gap: 1rem; align-items: center; justify-content: space-between; flex-wrap: wrap;">
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <button class="logistics-sub-tab ${pendingSubFilter === 'all' ? 'active' : ''}" onclick="setPendingSubFilter('all')">Összes nem jóváhagyott</button>
                <button class="logistics-sub-tab ${pendingSubFilter === 'submitted' ? 'active' : ''}" onclick="setPendingSubFilter('submitted')">📥 Csak beküldött igazolások</button>
                <button class="logistics-sub-tab ${pendingSubFilter === 'unsubmitted' ? 'active' : ''}" onclick="setPendingSubFilter('unsubmitted')">🏃 Még nem igazolt</button>
            </div>
            <div style="display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap;">
                <select class="input-text" style="width: auto; margin-bottom: 0; padding: 0.4rem 0.8rem; font-size: 0.82rem;" onchange="setPendingCampaignFilter(this.value)">
                    <option value="all" ${pendingCampaignFilter === 'all' ? 'selected' : ''}>Minden kampány</option>
                    <option value="predikalo" ${pendingCampaignFilter === 'predikalo' ? 'selected' : ''}>🏔️ Prédikálószék</option>
                    <option value="pilis" ${pendingCampaignFilter === 'pilis' ? 'selected' : ''}>⭐ Nagy-Kevély</option>
                </select>
                <input type="text" placeholder="Keresés név, email, sorszám..." class="input-text" style="width: 220px; margin-bottom: 0; padding: 0.4rem 0.8rem; font-size: 0.82rem;" value="${pendingSearchQuery}" oninput="handlePendingSearch(event)">
                <label style="font-size: 0.8rem; color: var(--text-mid); display: flex; align-items: center; gap: 0.35rem; cursor: pointer;">
                    <input type="checkbox" ${pendingHideTest ? 'checked' : ''} onchange="togglePendingHideTest(this)">
                    Teszt nélkül
                </label>
            </div>
        </div>
    `;

    if (runs.length === 0) {
        container.innerHTML = toolbarHtml + `
            <div class="empty-state">
                <div class="icon">✨</div>
                <div>Nincs megjeleníthető igazolás a megadott szűrésben.</div>
            </div>`;
        return;
    }

    let cardsHtml = runs.map(run => {
        const runner = run.runners || {};
        const name = run.name || runner.name || 'Ismeretlen';
        const email = runner.email || 'Nincs email';
        const serial = run.serial_number || 'Nincs sorszám';
        const urls = run.proof_urls || [];
        const campInfo = getCampaignInfo(run);

        const badgeHtml = run.proof_submitted
            ? `<span class="badge badge-pending">📥 Igazolás beküldve</span>`
            : `<span class="badge badge-not-submitted">🏃 Még nem igazolt</span>`;

        let filesHtml = '';
        if (urls.length > 0) {
            filesHtml = '<div class="proof-files">' + urls.map((url, i) => {
                const isImg = url.match(/\.(jpg|jpeg|png|webp|gif)$/i) || url.includes('/proofs/');
                if (isImg) {
                    return `<img src="${url}" class="proof-thumb" onclick="showImageModal('${url}')" alt="Igazolás ${i+1}" title="Kattints a nagyításhoz">`;
                }
                return `<a href="${url}" target="_blank" class="proof-doc-link">📄 Igazolás fájl megnyitása</a>`;
            }).join('') + '</div>';
        } else {
            filesHtml = '<div style="font-size: 0.82rem; color: var(--text-mid); margin-bottom: 1rem; font-style: italic;">A résztvevő még nem töltött fel igazolást.</div>';
        }

        return `
            <div class="proof-card" id="card-${run.id}">
                <div class="proof-header">
                    <div>
                        <div class="runner-name">${name}</div>
                        <div class="runner-meta">
                            📧 ${email} | 🗓️ Regisztrált: ${formatDate(run.created_at)}
                            ${run.proof_submitted_at ? ` | ⏱️ Igazolva: ${formatDate(run.proof_submitted_at)}` : ''}
                        </div>
                    </div>
                    <div class="badges">
                        <span style="font-size:0.75rem; color:${campInfo.color}; border:1px solid ${campInfo.color}40; background:${campInfo.color}15; padding:0.2rem 0.5rem; border-radius:4px;">${campInfo.icon} ${campInfo.name}</span>
                        <span class="badge badge-serial">${serial}</span>
                        ${badgeHtml}
                    </div>
                </div>
                ${filesHtml}
                <div class="proof-actions">
                    <button class="btn btn-approve" onclick="approveRun('${run.id}')">✅ Jóváhagyás & Éremküldés</button>
                    <button class="btn btn-reject" onclick="rejectRun('${run.id}')">❌ Elutasítás</button>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = toolbarHtml + cardsHtml;
}

function renderRunsTable(runs, container) {
    if (runs.length === 0) {
        container.innerHTML = `<div class="empty-state"><div class="icon">📋</div><div>Nincs megjeleníthető tétel.</div></div>`;
        return;
    }

    let rowsHtml = runs.map(run => {
        const runner = run.runners || {};
        const name = run.name || runner.name || 'Ismeretlen';
        const email = runner.email || '–';
        const serial = run.serial_number || '–';
        const shipment = getShipment(run);
        const campInfo = getCampaignInfo(run);
        const campBadge = `<span style="font-size:0.7rem; color:${campInfo.color}; border:1px solid ${campInfo.color}40; background:${campInfo.color}15; padding:0.12rem 0.4rem; border-radius:4px; margin-right:0.35rem;">${campInfo.icon} ${campInfo.name}</span>`;

        let statusText = '';
        if (run.completed) {
            statusText = shipment.shipped
                ? `<span class="shipped-badge badge-shipped">Feladva (${shipment.tracking_code || 'Foxpost'})</span>`
                : `<span class="shipped-badge badge-waiting">Jóváhagyva (Szállításra vár)</span>`;
        } else if (run.proof_submitted) {
            statusText = `<span class="badge badge-pending">Igazolásra vár</span>`;
        } else {
            statusText = `<span class="badge badge-not-submitted">Folyamatban</span>`;
        }

        return `
            <tr>
                <td style="font-weight: 600;">${name}</td>
                <td>${campBadge}<strong>${serial}</strong></td>
                <td>${email}</td>
                <td>${formatDate(run.created_at)}</td>
                <td>${statusText}</td>
            </tr>
        `;
    }).join('');

    container.innerHTML = `
        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Név</th>
                        <th>Kihívás & Sorszám</th>
                        <th>Email</th>
                        <th>Regisztráció</th>
                        <th>Állapot</th>
                    </tr>
                </thead>
                <tbody>${rowsHtml}</tbody>
            </table>
        </div>
    `;
}

async function approveRun(runId) {
    if (!confirm('Biztosan jóváhagyod a teljesítést? A rendszer gratuláló emailt küld a résztvevőnek.')) return;

    try {
        const res = await fetch('/api/admin-approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'approve', run_id: runId, admin_secret: adminSecret })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Hiba a jóváhagyáskor');

        alert('Teljesítés sikeresen jóváhagyva!');
        loadData();

    } catch (err) {
        alert('Hiba történt: ' + err.message);
    }
}

async function rejectRun(runId) {
    if (!confirm('Biztosan elutasítod a feltöltött igazolást? A státusz visszaáll nem teljesítettre.')) return;

    try {
        const res = await fetch('/api/admin-approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'reject', run_id: runId, admin_secret: adminSecret })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Hiba az elutasításkor');

        alert('Igazolás elutasítva és visszaállítva.');
        loadData();

    } catch (err) {
        alert('Hiba történt: ' + err.message);
    }
}

function showImageModal(url) {
    const modal = document.getElementById('image-modal');
    const img = document.getElementById('modal-img');
    if (modal && img) {
        img.src = url;
        modal.style.display = 'flex';
    }
}

function closeImageModal() {
    const modal = document.getElementById('image-modal');
    if (modal) modal.style.display = 'none';
}
