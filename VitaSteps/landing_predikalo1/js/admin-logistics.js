// ===== ADMIN LOGISTICS & FOXPOST MODULE =====

let logisticsSubFilter = 'pending'; // 'pending', 'shipped', 'all'
let logisticsSearch = '';
let logisticsHideTest = true;

function getGroupedRunIds(run) {
    if (!run) return [];
    const runner = run.runners || {};
    const email = (runner.email || '').toLowerCase().trim();
    const orderId = run.order_id;
    const shipTogether = (run.ship_together_with || '').toLowerCase().trim();
    const shipment = getShipment(run);
    const dest = shipment.parcel_id || shipment.home_address || '';
    const trackingCode = shipment.tracking_code || '';
    const isShipped = !!shipment.shipped;

    const matched = allRuns.filter(r => {
        if (r.id === run.id) return true;
        const rRunner = r.runners || {};
        const rEmail = (rRunner.email || '').toLowerCase().trim();
        const rShipment = getShipment(r);
        const rDest = rShipment.parcel_id || rShipment.home_address || '';
        const rTracking = rShipment.tracking_code || '';
        const rShipped = !!rShipment.shipped;

        // Never group a shipped parcel with an unshipped parcel
        if (isShipped !== rShipped) return false;

        // If both already shipped, only group if they share the exact same tracking code
        if (isShipped && rShipped) {
            return trackingCode && rTracking && trackingCode === rTracking;
        }

        // Neither is shipped yet: check destination match
        if (dest && rDest && dest !== rDest) return false;
        if (orderId && r.order_id && orderId === r.order_id) return true;
        if (email && rEmail && email === rEmail) return true;

        const rShipTogether = (r.ship_together_with || '').toLowerCase().trim();
        if (shipTogether && (shipTogether === rEmail || shipTogether === rShipTogether)) return true;
        if (rShipTogether && (rShipTogether === email)) return true;

        return false;
    });

    return matched.map(r => r.id);
}

function setLogisticsSubFilter(sub) {
    logisticsSubFilter = sub;
    renderList();
}

function handleLogisticsSearch(e) {
    logisticsSearch = e.target.value.toLowerCase();
    renderList();
}

function renderLogistics(container) {
    let completedRuns = allRuns.filter(r => r.completed);
    if (logisticsHideTest) completedRuns = completedRuns.filter(r => !isTestRun(r));

    // Filter by sub-filter
    let filtered = completedRuns.filter(run => {
        const shipment = getShipment(run);
        const isShipped = !!shipment.shipped;
        if (logisticsSubFilter === 'pending') return !isShipped;
        if (logisticsSubFilter === 'shipped') return isShipped;
        return true;
    });

    // Filter by search query
    if (logisticsSearch) {
        filtered = filtered.filter(run => {
            const runner = run.runners || {};
            const name = (run.name || runner.name || '').toLowerCase();
            const email = (runner.email || '').toLowerCase();
            const serial = (run.serial_number || '').toLowerCase();
            const shipment = getShipment(run);
            const tracking = (shipment.tracking_code || '').toLowerCase();
            return name.includes(logisticsSearch) || email.includes(logisticsSearch) || serial.includes(logisticsSearch) || tracking.includes(logisticsSearch);
        });
    }

    const totalWaiting = completedRuns.filter(r => !getShipment(r).shipped).length;
    const totalShipped = completedRuns.filter(r => getShipment(r).shipped).length;

    // 1. Compute Consolidated Packing List
    const unshippedCompleted = completedRuns.filter(r => !getShipment(r).shipped);
    const packingGroups = [];
    const processedRunIds = new Set();

    unshippedCompleted.forEach(run => {
        if (processedRunIds.has(run.id)) return;
        const groupRunIds = getGroupedRunIds(run);
        const groupRuns = groupRunIds.map(id => allRuns.find(r => r.id === id)).filter(Boolean).filter(r => r.completed && !getShipment(r).shipped);
        groupRunIds.forEach(id => processedRunIds.add(id));
        if (groupRuns.length > 0) packingGroups.push(groupRuns);
    });

    let packingRowsHtml = packingGroups.map(group => {
        const primary = group[0];
        const primaryName = primary.name || primary.runners?.name || 'Ismeretlen';
        const others = group.slice(1).map(r => r.name || r.runners?.name || '').filter(Boolean);
        const othersText = others.length > 0 ? ` (+ ${others.join(', ')})` : '';
        const shipment = getShipment(primary);
        const method = shipment.method || 'foxpost';
        let destText = method === 'foxpost'
            ? `🦊 Foxpost automata: <strong>${shipment.parcel_name || 'Locker'}</strong> (${shipment.parcel_id || 'ID nélkül'})`
            : `🏠 Házhozszállítás: <strong>${shipment.home_address || 'Cím nélkül'}</strong>`;

        // Group medals by campaign in this package
        const campMap = {};
        group.forEach(r => {
            const info = getCampaignInfo(r);
            if (!campMap[info.name]) {
                campMap[info.name] = { count: 0, info: info, serials: [] };
            }
            campMap[info.name].count++;
            if (r.serial_number) {
                campMap[info.name].serials.push(r.serial_number);
            }
        });

        const breakdownBadges = Object.values(campMap).map(c => {
            return `<span style="background: rgba(255,255,255,0.06); border: 1px solid ${c.info.color}40; color: #fff; padding: 0.2rem 0.55rem; border-radius: 6px; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 0.35rem;">
                <span>${c.info.icon}</span>
                <strong style="color: ${c.info.color}; font-size: 0.82rem;">${c.count}x ${c.info.name}</strong>
                <span style="opacity: 0.9; font-size: 0.75rem; font-family: monospace;">(${c.serials.join(', ')})</span>
            </span>`;
        }).join(' <span style="color:var(--text-mid); font-weight:bold; font-size:0.8rem; margin: 0 0.15rem;">+</span> ');

        // Check if this group has pending companion runs that haven't finished yet
        const pendingCompanions = allRuns.filter(r => {
            if (r.completed) return false;
            const rRunner = r.runners || {};
            const rEmail = (rRunner.email || '').toLowerCase().trim();
            const rOrderId = r.order_id;
            return (primary.order_id && rOrderId === primary.order_id) || (primary.runners?.email && rEmail === (primary.runners.email || '').toLowerCase().trim());
        });

        const pendingCompanionBadge = pendingCompanions.length > 0
            ? `<div style="font-size: 0.75rem; color: #f59e0b; margin-top: 0.35rem; background: rgba(245, 158, 11, 0.1); border: 1px dashed rgba(245, 158, 11, 0.3); padding: 0.2rem 0.5rem; border-radius: 4px; display: inline-flex; align-items: center; gap: 0.3rem;">
                <span>⚠️</span>
                <span>Együtt rendelve, de még nem teljesített érem: <strong>${pendingCompanions.map(r => `${r.name || 'Résztvevő'} (${r.serial_number})`).join(', ')}</strong></span>
            </div>`
            : '';

        return `
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; border-bottom: 1px solid rgba(255,255,255,0.06); padding: 0.65rem 0.25rem; flex-wrap: wrap; gap: 0.6rem;">
                <div>
                    <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                        <strong style="color: #fff; font-size: 0.95rem;">${primaryName}</strong>${othersText}
                        <span style="font-size: 0.75rem; color: var(--text-mid);">📧 ${(primary.runners?.email || '')}</span>
                    </div>
                    <div style="font-size: 0.78rem; color: var(--text-mid); margin-top: 0.2rem;">${destText}</div>
                    <div style="margin-top: 0.4rem; display: flex; flex-wrap: wrap; gap: 0.35rem; align-items: center;">
                        ${breakdownBadges}
                    </div>
                    ${pendingCompanionBadge}
                </div>
                <div style="background: rgba(168, 85, 247, 0.18); color: #d8b4fe; font-weight: 800; border-radius: 8px; padding: 0.4rem 0.85rem; font-size: 0.85rem; border: 1px solid rgba(168, 85, 247, 0.4); text-align: center; white-space: nowrap;">
                    📦 Összesen a csomagba: <strong>${group.length} db érem</strong>
                </div>
            </div>
        `;
    }).join('');

    if (packingGroups.length === 0) {
        packingRowsHtml = '<div style="color: var(--text-mid); font-size: 0.85rem; padding: 0.5rem 0;">Nincsenek postázásra váró érmek.</div>';
    }

    // 2. Compute Table Rows with Package Medal Counts
    let tableRowsHtml = filtered.map(run => {
        const runner = run.runners || {};
        const name = run.name || runner.name || 'Ismeretlen';
        const email = runner.email || '–';
        const shipment = getShipment(run);
        const rawPhone = shipment.phone || runner.phone || '';
        const phone = rawPhone || '–';
        const serial = run.serial_number || '–';
        const method = shipment.method || 'foxpost';
        const campInfo = getCampaignInfo(run);
        const campBadge = `<span style="font-size:0.7rem; color:${campInfo.color}; border:1px solid ${campInfo.color}40; background:${campInfo.color}15; padding:0.12rem 0.4rem; border-radius:4px; margin-right:0.35rem; display:inline-flex; align-items:center; gap:0.2rem;">${campInfo.icon} ${campInfo.name}</span>`;
        
        const isPhoneValid = rawPhone && rawPhone.replace(/\D/g, '').length >= 9;
        const isLockerValid = method !== 'foxpost' || (shipment.parcel_id && String(shipment.parcel_id).trim() !== '');

        let details = '–';
        if (method === 'foxpost') {
            details = `🦊 ${shipment.parcel_name || 'Foxpost automata'} (${shipment.parcel_id || '<span style="color:#ef4444;font-weight:bold;">NINCS AUTOMATA ID</span>'})${shipment.tracking_code ? '<br>📦 Csomagszám: <b>' + shipment.tracking_code + '</b>' : ''}`;
        } else if (method === 'home') {
            details = `🏠 Házhoz: ${shipment.home_address || 'Cím nélkül'}`;
        }

        // Calculate total medals in this specific package
        const groupRunIds = getGroupedRunIds(run);
        const packageRuns = groupRunIds.map(id => allRuns.find(r => r.id === id)).filter(Boolean);
        const packageMedalsCount = packageRuns.length;
        const packageSerialsText = packageRuns.map(r => r.serial_number).filter(Boolean).join(', ');

        const packageBadge = packageMedalsCount > 1
            ? `<span style="background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.4); color: #d8b4fe; padding: 0.2rem 0.5rem; border-radius: 6px; font-weight: 700; font-size: 0.72rem; display: inline-flex; align-items: center; gap: 0.3rem;" title="Egy csomagban küldött érmek: ${packageSerialsText}">📦 <b>${packageMedalsCount} db érem</b> (${packageSerialsText})</span>`
            : `<span style="background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: var(--text-mid); padding: 0.2rem 0.45rem; border-radius: 6px; font-size: 0.72rem;">📦 1 db érem</span>`;

        const statusText = shipment.shipped
            ? `<span class="shipped-badge badge-shipped">✅ Feladva (${packageMedalsCount} db érem a csomagban)</span>`
            : `<span class="shipped-badge badge-waiting">⏳ Szállításra vár (${packageMedalsCount} db érem)</span>`;

        const phoneDisplay = isPhoneValid
            ? `<span>${phone}</span>`
            : `<span style="color:#ef4444; font-weight:bold;" title="Érvénytelen vagy hiányzó telefonszám">⚠️ ${phone}</span>`;

        const editBtn = `
            <button onclick="promptEditShipment('${run.id}', '${(rawPhone || '').replace(/'/g, "\\'")}', '${(shipment.parcel_id || '').replace(/'/g, "\\'")}', '${(shipment.parcel_name || '').replace(/'/g, "\\'")}')" 
                style="background:rgba(255,255,255,0.06); border:1px solid var(--border); color:var(--text-mid); border-radius:4px; padding:0.15rem 0.4rem; font-size:0.7rem; cursor:pointer; margin-left:0.3rem;" title="Telefonszám és automata módosítása">
                ✏️
            </button>
        `;

        return `
            <tr>
                <td>
                    <input type="checkbox" class="checkbox-custom logistics-checkbox" data-run-id="${run.id}" onchange="onLogisticsCheckboxChange(this, '${run.id}')">
                </td>
                <td style="font-weight: 600;">
                    <div>${name}</div>
                    <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.15rem;">${email}</div>
                </td>
                <td>${campBadge}<strong>${serial}</strong></td>
                <td>${packageBadge}</td>
                <td><div style="display:flex; align-items:center;">${phoneDisplay}${editBtn}</div></td>
                <td style="font-size: 0.8rem; max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${shipment.parcel_name || ''}">${details}</td>
                <td>${statusText}</td>
            </tr>
        `;
    }).join('');

    if (filtered.length === 0) {
        tableRowsHtml = `<tr><td colspan="7" class="empty-state" style="padding: 2rem;">Nincs a szűrésnek megfelelő szállítási tétel.</td></tr>`;
    }

    container.innerHTML = `
        <!-- Packing Guide Section -->
        <div class="card" style="border-left: 4px solid var(--accent); margin-bottom: 1.5rem; background: linear-gradient(180deg, rgba(249, 115, 22, 0.04) 0%, rgba(12, 15, 21, 1) 100%);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
                <h3 style="font-size: 1.05rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem;">
                    <span>📦</span> Csomagolási és Kiszállítási Segédlet
                </h3>
                <span style="font-size: 0.8rem; color: var(--text-mid);">Automatikus csoportosítás azonos cím & rendelések alapján</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                ${packingRowsHtml}
            </div>
        </div>

        <!-- Logistics Table Toolbar -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
                <button class="logistics-sub-tab ${logisticsSubFilter === 'pending' ? 'active' : ''}" onclick="setLogisticsSubFilter('pending')">
                    ⏳ Szállításra vár (${totalWaiting})
                </button>
                <button class="logistics-sub-tab ${logisticsSubFilter === 'shipped' ? 'active' : ''}" onclick="setLogisticsSubFilter('shipped')">
                    ✅ Már feladva (${totalShipped})
                </button>
                <button class="logistics-sub-tab ${logisticsSubFilter === 'all' ? 'active' : ''}" onclick="setLogisticsSubFilter('all')">
                    Összes (${completedRuns.length})
                </button>
            </div>
            <div style="display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap;">
                <input type="text" placeholder="Keresés név, automata, kód..." class="input-text" style="width: 220px; margin-bottom: 0; padding: 0.45rem 0.8rem; font-size: 0.82rem;" value="${logisticsSearch}" oninput="handleLogisticsSearch(event)">
                
                <button id="btn-submit-foxpost" class="btn btn-purple" style="margin: 0; padding: 0.45rem 1rem; font-size: 0.82rem;" onclick="triggerSubmitFoxpost(this)" disabled>
                    🦊 Foxpost API Feladás (<span id="selected-foxpost-count">0</span>)
                </button>
                <button id="btn-mark-shipped" class="btn btn-orange" style="margin: 0; padding: 0.45rem 1rem; font-size: 0.82rem;" onclick="triggerMarkShipped(this)" disabled>
                    📦 Feladottnak jelölés (<span id="selected-ship-count">0</span>)
                </button>
            </div>
        </div>

        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 40px;">
                            <input type="checkbox" class="checkbox-custom" id="master-logistics-checkbox" onchange="toggleAllLogistics(this)">
                        </th>
                        <th>Résztvevő</th>
                        <th>Sorszám</th>
                        <th>Csomag Tartalma</th>
                        <th>Telefonszám</th>
                        <th>Átvételi Pont / Cím</th>
                        <th>Státusz</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRowsHtml}
                </tbody>
            </table>
        </div>
    `;

    updateLogisticsButtonsState();
}

function onLogisticsCheckboxChange(checkbox, runId) {
    const isChecked = checkbox.checked;
    const run = allRuns.find(r => r.id === runId);
    if (run) {
        const groupRunIds = getGroupedRunIds(run);
        groupRunIds.forEach(id => {
            const cb = document.querySelector(`.logistics-checkbox[data-run-id="${id}"]`);
            if (cb) cb.checked = isChecked;
        });
    }
    updateLogisticsButtonsState();
}

function toggleAllLogistics(masterCheckbox) {
    const checkboxes = document.querySelectorAll('.logistics-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = masterCheckbox.checked;
    });
    updateLogisticsButtonsState();
}

function updateLogisticsButtonsState() {
    const checkedCount = document.querySelectorAll('.logistics-checkbox:checked').length;
    const btnSubmit = document.getElementById('btn-submit-foxpost');
    const btnShip = document.getElementById('btn-mark-shipped');
    const countFox = document.getElementById('selected-foxpost-count');
    const countShip = document.getElementById('selected-ship-count');

    if (countFox) countFox.textContent = checkedCount;
    if (countShip) countShip.textContent = checkedCount;

    if (btnSubmit) {
        btnSubmit.disabled = checkedCount === 0 || logisticsSubFilter === 'shipped';
    }
    if (btnShip) {
        btnShip.disabled = checkedCount === 0 || logisticsSubFilter === 'shipped';
    }
}

function getSelectedRuns() {
    const checkedBoxes = document.querySelectorAll('.logistics-checkbox:checked');
    const ids = Array.from(checkedBoxes).map(cb => cb.dataset.runId);
    return allRuns.filter(r => ids.includes(r.id));
}

async function promptEditShipment(runId, curPhone, curParcelId, curParcelName) {
    const newPhone = prompt('Add meg a résztvevő érvényes telefonszámát (pl. +36301234567):', curPhone || '+36');
    if (newPhone === null) return;

    const newParcelId = prompt('Add meg a Foxpost automata azonosítóját (pl. hu351):', curParcelId || '');
    if (newParcelId === null) return;

    try {
        const res = await fetch('/api/admin-approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'update_shipment',
                run_id: runId,
                phone: newPhone.trim(),
                parcel_id: newParcelId.trim(),
                admin_secret: adminSecret
            })
        });

        const data = await res.json();
        if (res.ok) {
            alert('Szállítási adatok sikeresen frissítve!');
            loadData();
        } else {
            alert('Hiba a mentéskor: ' + (data.error || 'Ismeretlen hiba'));
        }
    } catch (err) {
        alert('Hiba a hálózati kéréskor: ' + err.message);
    }
}

async function triggerSubmitFoxpost(btn) {
    const selected = getSelectedRuns();
    if (selected.length === 0) return;

    const eligible = selected.filter(r => {
        const shipment = getShipment(r);
        return (shipment.method || 'foxpost') === 'foxpost' && !shipment.shipped;
    });

    if (eligible.length === 0) {
        alert('A kiválasztott tételek között nincs feladásra váró Foxpost automatás érem.');
        return;
    }

    if (!confirm(`Biztosan feladod a kijelölt ${eligible.length} db érmet a Foxpost WebAPI-n keresztül?`)) {
        return;
    }

    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner"></span> Foxpost API feladás...';

    try {
        const res = await fetch('/api/create-foxpost-parcels', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                run_ids: eligible.map(r => r.id),
                admin_secret: adminSecret
            })
        });

        const data = await res.json();

        if (res.ok && data.success) {
            let msg = data.message || 'Csomagok sikeresen feladva!';
            if (data.failed && data.failed.length > 0) {
                msg += '\n\n⚠️ Néhány csomagnál hiba történt:\n' + data.failed.map(f => `- ${f.serial_number} (${f.recipient}): ${f.errors.map(e => e.message || e).join(', ')}`).join('\n');
            }
            alert(msg);
            loadData();
        } else {
            let errMsg = data.error || data.message || 'Ismeretlen hiba történt a feladás során.';
            if (data.failed && data.failed.length > 0) {
                errMsg += '\n\n⚠️ Részletek:\n' + data.failed.map(f => `- ${f.serial_number} (${f.recipient}): ${f.errors.map(e => e.message || e).join(', ')}`).join('\n');
            }
            alert('Hiba a Foxpost feladáskor:\n' + errMsg);
        }

    } catch (err) {
        alert('Hálózati hiba történt a Foxpost feladáskor: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        updateLogisticsButtonsState();
    }
}

async function triggerMarkShipped(btn) {
    const selected = getSelectedRuns();
    if (selected.length === 0) return;

    if (!confirm(`Biztosan feladottnak jelölöd a kiválasztott ${selected.length} db érmet?`)) {
        return;
    }

    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner"></span> Frissítés...';

    try {
        const res = await fetch('/api/admin-approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'ship',
                run_ids: selected.map(r => r.id),
                admin_secret: adminSecret
            })
        });

        const data = await res.json();
        if (res.ok) {
            alert('A tételek sikeresen feladottként lettek elmentve!');
            loadData();
        } else {
            alert('Hiba a státusz mentésekor: ' + (data.error || 'Ismeretlen hiba'));
        }
    } catch (err) {
        alert('Hiba a hálózati kéréskor: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        updateLogisticsButtonsState();
    }
}
