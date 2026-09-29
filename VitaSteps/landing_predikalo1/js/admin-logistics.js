// ===== ADMIN LOGISTICS & FOXPOST MODULE =====

let logisticsSubFilter = 'pending'; // 'pending' (Feladandó), 'shipped' (Már feladva), 'received' (Megérkezett), 'all'
let logisticsSearch = '';
let logisticsHideTest = true;

function isRunShipped(run) {
    if (!run) return false;
    const s = getShipment(run);
    return !!(s.shipped || s.shipped_at || run.shipped);
}

function isRunReceived(run) {
    if (!run) return false;
    const s = getShipment(run);
    return !!(s.received || s.received_at || run.received_date);
}

function isValidTrackingCode(code) {
    if (!code) return false;
    const clean = String(code).trim();
    return clean.length >= 5 && clean !== '-' && clean !== '–' && clean.toUpperCase() !== 'N/A';
}

function getGroupedRunIds(run) {
    if (!run) return [];
    const runner = run.runners || {};
    const email = (runner.email || '').toLowerCase().trim();
    const orderId = run.order_id;
    const shipTogether = (run.ship_together_with || '').toLowerCase().trim();
    const shipment = getShipment(run);
    const dest = shipment.parcel_id || shipment.home_address || '';
    const trackingCode = shipment.tracking_code || '';
    const isShipped = isRunShipped(run);

    const matched = allRuns.filter(r => {
        if (r.id === run.id) return true;
        const rRunner = r.runners || {};
        const rEmail = (rRunner.email || '').toLowerCase().trim();
        const rShipment = getShipment(r);
        const rDest = rShipment.parcel_id || rShipment.home_address || '';
        const rTracking = rShipment.tracking_code || '';
        const rShipped = isRunShipped(r);

        // Never group a shipped parcel with an unshipped parcel
        if (isShipped !== rShipped) return false;

        // If both already shipped:
        if (isShipped && rShipped) {
            // Only group by tracking code if BOTH have a REAL, valid tracking code
            if (isValidTrackingCode(trackingCode) && isValidTrackingCode(rTracking)) {
                return trackingCode === rTracking;
            }
            // If tracking code is missing or placeholder '-', do NOT group by tracking code!
            // Fall back to companion / order / email rules:
            if (orderId && r.order_id && orderId === r.order_id) return true;
            if (email && rEmail && email === rEmail) return true;
            const rShipTogether = (r.ship_together_with || '').toLowerCase().trim();
            if (shipTogether && (shipTogether === rEmail || shipTogether === rShipTogether)) return true;
            if (rShipTogether && (rShipTogether === email)) return true;
            return false;
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
        const isShipped = isRunShipped(run);
        const isReceived = isRunReceived(run);
        if (logisticsSubFilter === 'pending' || logisticsSubFilter === 'to_ship') return !isShipped;
        if (logisticsSubFilter === 'shipped') return isShipped && !isReceived;
        if (logisticsSubFilter === 'received') return isReceived;
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
            const parcel = (shipment.parcel_name || '').toLowerCase();
            return name.includes(logisticsSearch) || email.includes(logisticsSearch) || serial.includes(logisticsSearch) || tracking.includes(logisticsSearch) || parcel.includes(logisticsSearch);
        });
    }

    const totalToShip = completedRuns.filter(r => !isRunShipped(r)).length;
    const totalShipped = completedRuns.filter(r => isRunShipped(r) && !isRunReceived(r)).length;
    const totalReceived = completedRuns.filter(r => isRunReceived(r)).length;

    // 1. Compute Consolidated Packing List
    const unshippedCompleted = completedRuns.filter(r => !isRunShipped(r));
    const packingGroups = [];
    const processedRunIds = new Set();

    unshippedCompleted.forEach(run => {
        if (processedRunIds.has(run.id)) return;
        const groupRunIds = getGroupedRunIds(run);
        const groupRuns = groupRunIds.map(id => allRuns.find(r => r.id === id)).filter(Boolean).filter(r => r.completed && !isRunShipped(r));
        groupRunIds.forEach(id => processedRunIds.add(id));
        if (groupRuns.length > 0) {
            groupRuns.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
            packingGroups.push(groupRuns);
        }
    });

    let packingRowsHtml = packingGroups.map(group => {
        const primary = group[0];
        const primaryRunner = primary.runners || {};
        const primaryName = primary.name || primaryRunner.billing_name || primaryRunner.name || 'Ismeretlen';
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

        const isShipped = isRunShipped(run);
        const isReceived = isRunReceived(run);

        let details = '–';
        if (method === 'foxpost') {
            const trackingBadge = shipment.tracking_code ? '<br>📦 Csomagszám: <b>' + shipment.tracking_code + '</b>' : '';
            const statusIndicator = isReceived 
                ? ' <span style="color:#38bdf8; font-size:0.75rem; font-weight:700;">(Átvéve)</span>' 
                : (isShipped ? ' <span style="color:#22c55e; font-size:0.75rem; font-weight:700;">(Úton)</span>' : '');
            details = `🦊 ${shipment.parcel_name || 'Foxpost automata'} (${shipment.parcel_id || '<span style="color:#ef4444;font-weight:bold;">NINCS AUTOMATA ID</span>'})${trackingBadge}${statusIndicator}`;
        } else if (method === 'home') {
            const statusIndicator = isReceived 
                ? ' <span style="color:#38bdf8; font-size:0.75rem; font-weight:700;">(Átvéve)</span>' 
                : (isShipped ? ' <span style="color:#22c55e; font-size:0.75rem; font-weight:700;">(Úton)</span>' : '');
            details = `🏠 Házhoz: ${shipment.home_address || 'Cím nélkül'}${statusIndicator}`;
        }

        // Calculate total medals in this specific package
        const groupRunIds = getGroupedRunIds(run);
        const packageRuns = groupRunIds.map(id => allRuns.find(r => r.id === id)).filter(Boolean);
        const packageMedalsCount = packageRuns.length;
        const packageSerialsText = packageRuns.map(r => r.serial_number).filter(Boolean).join(', ');

        const packageBadge = packageMedalsCount > 1
            ? `<span style="background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.4); color: #d8b4fe; padding: 0.2rem 0.5rem; border-radius: 6px; font-weight: 700; font-size: 0.72rem; display: inline-flex; align-items: center; gap: 0.3rem;" title="Egy csomagban küldött érmek: ${packageSerialsText}">📦 <b>${packageMedalsCount} db érem</b> (${packageSerialsText})</span>`
            : `<span style="background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: var(--text-mid); padding: 0.2rem 0.45rem; border-radius: 6px; font-size: 0.72rem;">📦 1 db érem</span>`;

        let statusText = '';
        if (isReceived) {
            const rDate = shipment.received_at || run.received_date;
            statusText = `<span class="shipped-badge badge-received">📬 Megérkezett${rDate ? ' (' + formatDate(rDate) + ')' : ''}</span>`;
        } else if (isShipped) {
            const sDate = shipment.shipped_at;
            const countSuffix = packageMedalsCount > 1 ? ` (${packageMedalsCount} db)` : '';
            statusText = `<span class="shipped-badge badge-shipped">🚚 Már feladva${sDate ? ' (' + formatDate(sDate) + ')' : ''}${countSuffix}</span>`;
        } else {
            const countSuffix = packageMedalsCount > 1 ? ` (${packageMedalsCount} db érem)` : '';
            statusText = `<span class="shipped-badge badge-waiting">⏳ Feladandó${countSuffix}</span>`;
        }

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
                <button class="logistics-sub-tab ${logisticsSubFilter === 'pending' || logisticsSubFilter === 'to_ship' ? 'active' : ''}" onclick="setLogisticsSubFilter('pending')">
                    ⏳ Feladandó (${totalToShip})
                </button>
                <button class="logistics-sub-tab ${logisticsSubFilter === 'shipped' ? 'active' : ''}" onclick="setLogisticsSubFilter('shipped')">
                    🚚 Már feladva (${totalShipped})
                </button>
                <button class="logistics-sub-tab ${logisticsSubFilter === 'received' ? 'active' : ''}" onclick="setLogisticsSubFilter('received')">
                    📬 Megérkezett (${totalReceived})
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
        btnSubmit.disabled = checkedCount === 0 || logisticsSubFilter === 'shipped' || logisticsSubFilter === 'received';
    }
    if (btnShip) {
        btnShip.disabled = checkedCount === 0 || logisticsSubFilter === 'shipped' || logisticsSubFilter === 'received';
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

let activeFoxpostEligibleRunIds = [];
let activeFoxpostDispatchBtn = null;

function parseHungarianAddressClient(rawAddress) {
    if (!rawAddress || typeof rawAddress !== 'string') return null;
    const str = rawAddress.trim();
    if (!str) return null;

    // 1. Extract 4-digit Hungarian postal code
    const zipMatch = str.match(/\b(\d{4})\b/);
    if (!zipMatch) return null;
    const zip = zipMatch[1];

    // Remove zip from address string
    let rest = str.replace(zip, '').replace(/^[, -]+|[, -]+$/g, '').trim();

    // 2. Extract city and street address
    let city = '';
    let address = '';

    if (rest.includes(',')) {
        const parts = rest.split(',').map(p => p.trim()).filter(Boolean);
        const streetKeywords = /\b(utca|út|tér|körút|krt|fasor|köz|sor|sétány|dűlő|major|tanya|ltp|lakótelep|telep|u\.|krt\.|rkp|rakpart|sgt|sugárút)\b/i;
        if (parts.length >= 2) {
            if (!streetKeywords.test(parts[0])) {
                city = parts[0];
                address = parts.slice(1).join(', ');
            } else if (!streetKeywords.test(parts[parts.length - 1])) {
                city = parts[parts.length - 1];
                address = parts.slice(0, -1).join(', ');
            } else {
                city = parts[0];
                address = parts.slice(1).join(', ');
            }
        } else {
            address = parts[0] || '';
        }
    } else {
        const tokens = rest.split(/\s+/).filter(Boolean);
        if (tokens.length >= 2) {
            city = tokens[0];
            address = tokens.slice(1).join(' ');
        } else {
            address = rest;
        }
    }

    city = city.replace(/^[, -]+|[, -]+$/g, '').trim();
    address = address.replace(/^[, -]+|[, -]+$/g, '').trim();

    if (!city || !address) return null;

    if (city.length > 25) city = city.substring(0, 25);
    if (address.length > 150) address = address.substring(0, 150);

    return { zip, city, address };
}

function escapeHtmlText(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function openFoxpostHdModal(allEligible, homeGroups, lockerCount, btn) {
    activeFoxpostEligibleRunIds = allEligible.map(r => r.id);
    activeFoxpostDispatchBtn = btn;

    const modal = document.getElementById('foxpost-hd-modal');
    const listEl = document.getElementById('foxpost-hd-modal-list');
    const infoEl = document.getElementById('foxpost-hd-modal-info');
    if (!modal || !listEl) return;

    listEl.innerHTML = homeGroups.map(group => {
        const primary = group[0];
        const primaryRunner = primary.runners || {};
        const primaryShipment = getShipment(primary);
        const recipientName = primary.name || primaryRunner.name || 'Ismeretlen';
        const serials = group.map(r => r.serial_number).filter(Boolean);
        const email = primaryRunner.email || '';
        const phone = primaryShipment.phone || primary.phone || primaryRunner.phone || '';

        // Find raw address
        let rawAddress = primaryShipment.home_address || primaryShipment.target_address || primaryRunner.billing_address || primary.home_address || '';
        if (!rawAddress) {
            for (const r of group) {
                const rRunner = r.runners || {};
                const rShip = getShipment(r);
                rawAddress = rShip.home_address || rShip.target_address || rRunner.billing_address || r.home_address || '';
                if (rawAddress) break;
            }
        }

        const parsed = parseHungarianAddressClient(rawAddress) || { zip: '', city: '', address: '' };
        const isComplete = parsed.zip && parsed.city && parsed.address;
        const groupRunIds = group.map(r => r.id).join(',');

        return `
            <div class="hd-card" data-run-ids="${groupRunIds}" style="background: rgba(255,255,255,0.03); border: 1px solid ${isComplete ? 'rgba(255,255,255,0.12)' : '#ef4444'}; border-radius: 12px; padding: 1.1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.25);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.65rem; gap: 0.5rem; flex-wrap: wrap;">
                    <div>
                        <strong style="color: #fff; font-size: 0.95rem;">${escapeHtmlText(recipientName)}</strong>
                        <span style="color: #c084fc; font-family: monospace; font-size: 0.82rem; margin-left: 0.45rem; font-weight: bold;">(${serials.join(', ')})</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #94a3b8;">
                        <span>📞 ${escapeHtmlText(phone || 'Nincs tel.')}</span> • <span>✉️ ${escapeHtmlText(email || 'Nincs email')}</span>
                    </div>
                </div>

                <div style="background: rgba(0,0,0,0.4); border: 1px dashed ${rawAddress ? 'rgba(255,255,255,0.15)' : '#ef4444'}; border-radius: 6px; padding: 0.5rem 0.75rem; font-size: 0.82rem; color: #e2e8f0; margin-bottom: 0.85rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem;">
                        <span style="color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Eredeti (nyers) cím a megrendelésből:</span>
                        ${!isComplete ? '<span style="color: #ef4444; font-size: 0.72rem; font-weight: bold;">⚠️ Kérjük töltsd ki a hiányzó mezőket!</span>' : '<span style="color: #4ade80; font-size: 0.72rem; font-weight: bold;">✓ Felbontva</span>'}
                    </div>
                    <div style="font-family: monospace; word-break: break-word;">${escapeHtmlText(rawAddress || '⚠️ Nem található cím!')}</div>
                </div>

                <div style="display: grid; grid-template-columns: 110px 160px 1fr; gap: 0.65rem;">
                    <div>
                        <label style="display: block; font-size: 0.72rem; color: #94a3b8; margin-bottom: 0.25rem; font-weight: 600;">Irányítószám *</label>
                        <input type="text" class="form-input hd-field-zip" maxlength="4" value="${escapeHtmlText(parsed.zip)}" placeholder="pl. 1139" style="width: 100%; padding: 0.45rem 0.6rem; font-size: 0.85rem; background: #1e293b; border: 1px solid ${parsed.zip ? 'rgba(255,255,255,0.2)' : '#ef4444'}; color: #fff; border-radius: 6px; font-weight: 600;">
                    </div>
                    <div>
                        <label style="display: block; font-size: 0.72rem; color: #94a3b8; margin-bottom: 0.25rem; font-weight: 600;">Település *</label>
                        <input type="text" class="form-input hd-field-city" maxlength="25" value="${escapeHtmlText(parsed.city)}" placeholder="pl. Budapest" style="width: 100%; padding: 0.45rem 0.6rem; font-size: 0.85rem; background: #1e293b; border: 1px solid ${parsed.city ? 'rgba(255,255,255,0.2)' : '#ef4444'}; color: #fff; border-radius: 6px; font-weight: 600;">
                    </div>
                    <div>
                        <label style="display: block; font-size: 0.72rem; color: #94a3b8; margin-bottom: 0.25rem; font-weight: 600;">Utca, házszám, em/ajtó *</label>
                        <input type="text" class="form-input hd-field-address" maxlength="150" value="${escapeHtmlText(parsed.address)}" placeholder="pl. Csizma utca 3." style="width: 100%; padding: 0.45rem 0.6rem; font-size: 0.85rem; background: #1e293b; border: 1px solid ${parsed.address ? 'rgba(255,255,255,0.2)' : '#ef4444'}; color: #fff; border-radius: 6px;">
                    </div>
                </div>
            </div>
        `;
    }).join('');

    if (lockerCount > 0) {
        infoEl.style.display = 'block';
        infoEl.innerHTML = `ℹ️ A fentieken kívül <strong>${lockerCount} db Foxpost csomagautomatás</strong> érem is egyidejűleg feladásra kerül.`;
    } else {
        infoEl.style.display = 'none';
    }

    modal.style.display = 'flex';
}

function closeFoxpostHdModal() {
    const modal = document.getElementById('foxpost-hd-modal');
    if (modal) modal.style.display = 'none';
}

async function submitFoxpostHdWithOverrides() {
    const cards = document.querySelectorAll('#foxpost-hd-modal-list .hd-card');
    const addressOverrides = {};
    let hasValidationError = false;

    cards.forEach(card => {
        const runIdsStr = card.getAttribute('data-run-ids') || '';
        const runIds = runIdsStr.split(',').map(s => s.trim()).filter(Boolean);

        const zipInput = card.querySelector('.hd-field-zip');
        const cityInput = card.querySelector('.hd-field-city');
        const addressInput = card.querySelector('.hd-field-address');

        const zip = (zipInput ? zipInput.value : '').trim();
        const city = (cityInput ? cityInput.value : '').trim();
        const address = (addressInput ? addressInput.value : '').trim();

        // Validation
        let cardError = false;
        if (!/^\d{4}$/.test(zip)) {
            if (zipInput) zipInput.style.borderColor = '#ef4444';
            cardError = true;
        } else if (zipInput) {
            zipInput.style.borderColor = 'rgba(255,255,255,0.2)';
        }

        if (!city || city.length < 2) {
            if (cityInput) cityInput.style.borderColor = '#ef4444';
            cardError = true;
        } else if (cityInput) {
            cityInput.style.borderColor = 'rgba(255,255,255,0.2)';
        }

        if (!address || address.length < 3) {
            if (addressInput) addressInput.style.borderColor = '#ef4444';
            cardError = true;
        } else if (addressInput) {
            addressInput.style.borderColor = 'rgba(255,255,255,0.2)';
        }

        if (cardError) {
            hasValidationError = true;
            card.style.borderColor = '#ef4444';
        } else {
            card.style.borderColor = 'rgba(255,255,255,0.12)';
            runIds.forEach(id => {
                addressOverrides[id] = { zip, city, address };
            });
        }
    });

    if (hasValidationError) {
        alert('Kérjük javítsd a pirossal jelölt hiányzó vagy érvénytelen címadatokat a jóváhagyás előtt! (4 jegyű irányítószám, település és pontos utca házszám kötelező)');
        return;
    }

    closeFoxpostHdModal();
    await sendFoxpostApiRequest(activeFoxpostEligibleRunIds, addressOverrides, activeFoxpostDispatchBtn);
}

async function sendFoxpostApiRequest(runIds, addressOverrides, btn) {
    const originalText = btn ? btn.innerHTML : 'Foxpost API feladás...';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span> Foxpost API feladás...';
    }

    try {
        const res = await fetch('/api/admin-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'foxpost_create',
                run_ids: runIds,
                address_overrides: addressOverrides,
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
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
        updateLogisticsButtonsState();
    }
}

async function triggerSubmitFoxpost(btn) {
    const selected = getSelectedRuns();
    if (selected.length === 0) return;

    const eligible = selected.filter(r => !isRunShipped(r));

    if (eligible.length === 0) {
        alert('A kiválasztott tételek között nincs feladásra váró érem.');
        return;
    }

    // Group eligible runs into packages
    const groups = [];
    const processedRunIds = new Set();

    eligible.forEach(run => {
        if (processedRunIds.has(run.id)) return;
        const groupRunIds = getGroupedRunIds(run);
        const groupRuns = groupRunIds.map(id => eligible.find(r => r.id === id)).filter(Boolean);
        groupRunIds.forEach(id => processedRunIds.add(id));
        if (groupRuns.length > 0) {
            groupRuns.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
            groups.push(groupRuns);
        }
    });

    const homeGroups = groups.filter(g => getShipment(g[0]).method === 'home');
    const lockerRuns = eligible.filter(r => (getShipment(r).method || 'foxpost') === 'foxpost');

    if (homeGroups.length > 0) {
        // Open the Safety Verification Modal for Home Deliveries
        openFoxpostHdModal(eligible, homeGroups, lockerRuns.length, btn);
    } else {
        // Direct confirmation for Locker-only batches
        if (!confirm(`Biztosan feladod a kijelölt ${eligible.length} db Foxpost csomagautomatás érmet a WebAPI-n keresztül?`)) {
            return;
        }
        await sendFoxpostApiRequest(eligible.map(r => r.id), {}, btn);
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
        const res = await fetch('/api/admin-data', {
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
