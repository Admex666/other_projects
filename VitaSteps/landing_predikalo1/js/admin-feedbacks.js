// ===== ADMIN FEEDBACKS & REVIEWS MODULE =====

let allFeedbacks = [];
let fbSelectedCampaign = 'all'; // 'all', 'pilis', 'predikalo'
let fbRatingFilter = 'all'; // 'all', '5star', 'with_text', 'with_photo'
let fbSearchQuery = '';

function setFbCampaign(camp) {
    fbSelectedCampaign = camp;
    document.querySelectorAll('#fb-campaign-tabs .mkt-tab').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById(`fb-camp-${camp}`);
    if (btn) btn.classList.add('active');
    renderFeedbackView();
}

function setFbRatingFilter(filter) {
    fbRatingFilter = filter;
    document.querySelectorAll('#fb-filter-tabs .mkt-tab').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById(`fb-filter-${filter}`);
    if (btn) btn.classList.add('active');
    renderFeedbackView();
}

function handleFbSearch(e) {
    fbSearchQuery = e.target.value.toLowerCase().trim();
    renderFeedbackView();
}

async function loadFeedbacks() {
    const container = document.getElementById('section-feedbacks');
    if (!container) return;

    const listEl = document.getElementById('fb-content-container');
    if (listEl) {
        listEl.innerHTML = '<div class="empty-state"><span class="loading-spinner"></span><div style="margin-top:0.5rem">Visszajelzések betöltése...</div></div>';
    }

    try {
        const res = await fetch(`/api/admin-data?type=feedbacks&secret=${encodeURIComponent(adminSecret)}`);
        if (!res.ok) throw new Error('Nem sikerült betölteni a visszajelzéseket');

        const data = await res.json();
        allFeedbacks = data.feedbacks || [];
        renderFeedbackView();

    } catch (err) {
        console.error('Feedbacks load error:', err);
        if (listEl) {
            listEl.innerHTML = `<div class="empty-state" style="color: var(--red);">Hiba történt a visszajelzések betöltésekor: ${err.message}</div>`;
        }
    }
}

function renderFeedbackView() {
    const contentEl = document.getElementById('fb-content-container');
    if (!contentEl) return;

    // Filter by campaign
    let filtered = allFeedbacks.filter(f => {
        const run = f.runs || {};
        const camp = (run.campaign || '').toLowerCase();
        const serial = (run.serial_number || '').toLowerCase();
        const isPilis = camp.includes('pilis') || camp.includes('kevely') || serial.includes('-pk');

        if (fbSelectedCampaign === 'pilis') return isPilis;
        if (fbSelectedCampaign === 'predikalo') return !isPilis;
        return true;
    });

    // Calculate Campaign Stats before extra sub-filtering
    const totalCount = filtered.length;
    let sumMedal = 0, countMedal = 0;
    let sumShipping = 0, countShipping = 0;
    let sumNps = 0, countNps = 0;
    let promoters = 0;
    let willParticipateCount = 0;
    let withPhotoCount = 0;
    let destinationCounts = {};

    filtered.forEach(f => {
        if (f.erem_minoseg) { sumMedal += Number(f.erem_minoseg); countMedal++; }
        if (f.szallitas_elegedett) { sumShipping += Number(f.szallitas_elegedett); countShipping++; }
        if (f.nps_score !== null && f.nps_score !== undefined) {
            const nps = Number(f.nps_score);
            sumNps += nps;
            countNps++;
            if (nps >= 9) promoters++;
        }
        if ((f.reszvetel_ujra || '').toLowerCase() === 'igen') {
            willParticipateCount++;
        }
        if (f.photo_url) {
            withPhotoCount++;
        }

        // Destinations breakdown
        if (f.kovetkezo_tajegyseg) {
            const parts = f.kovetkezo_tajegyseg.split(',').map(s => s.trim().replace(/^Egyéb:\s*/i, '')).filter(Boolean);
            parts.forEach(p => {
                destinationCounts[p] = (destinationCounts[p] || 0) + 1;
            });
        }
    });

    const avgMedal = countMedal > 0 ? (sumMedal / countMedal).toFixed(1) : '–';
    const avgShipping = countShipping > 0 ? (sumShipping / countShipping).toFixed(1) : '–';
    const avgNps = countNps > 0 ? (sumNps / countNps).toFixed(1) : '–';
    const promoterPct = countNps > 0 ? Math.round((promoters / countNps) * 100) : 0;
    const participatePct = totalCount > 0 ? Math.round((willParticipateCount / totalCount) * 100) : 0;

    // Apply sub-filters
    if (fbRatingFilter === '5star') {
        filtered = filtered.filter(f => Number(f.erem_minoseg) === 5);
    } else if (fbRatingFilter === 'with_text') {
        filtered = filtered.filter(f => (f.tetszett_legjobban && f.tetszett_legjobban.trim().length > 2 && f.tetszett_legjobban !== 'None') || (f.jobba_tenne && f.jobba_tenne.trim().length > 2 && f.jobba_tenne !== 'None'));
    } else if (fbRatingFilter === 'with_photo') {
        filtered = filtered.filter(f => !!f.photo_url);
    }

    // Apply search query
    if (fbSearchQuery) {
        filtered = filtered.filter(f => {
            const run = f.runs || {};
            const runner = run.runners || {};
            const name = (run.name || runner.name || '').toLowerCase();
            const email = (f.runner_email || runner.email || '').toLowerCase();
            const serial = (run.serial_number || '').toLowerCase();
            const liked = (f.tetszett_legjobban || '').toLowerCase();
            const improve = (f.jobba_tenne || '').toLowerCase();
            const dest = (f.kovetkezo_tajegyseg || '').toLowerCase();

            return name.includes(fbSearchQuery) ||
                   email.includes(fbSearchQuery) ||
                   serial.includes(fbSearchQuery) ||
                   liked.includes(fbSearchQuery) ||
                   improve.includes(fbSearchQuery) ||
                   dest.includes(fbSearchQuery);
        });
    }

    // Sorted destination entries
    const topDestinations = Object.entries(destinationCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 7);

    // Build KPI Summary HTML
    let kpiHtml = `
        <div class="fin-summary-grid" style="margin-bottom: 1.5rem;">
            <div class="fin-card highlight" style="border-color: rgba(236, 72, 153, 0.4); background: linear-gradient(145deg, rgba(236, 72, 153, 0.08) 0%, rgba(12, 15, 21, 0.95) 100%);">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="font-size:0.75rem; color:var(--text-mid); font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">Összes visszajelzés</div>
                    <span style="font-size:1.1rem;">💬</span>
                </div>
                <div style="font-size:1.8rem; font-weight:800; font-family:'Outfit',sans-serif; color:#f472b6; margin-top:0.2rem;">
                    ${totalCount} <span style="font-size:0.9rem; font-weight:600; color:var(--text-mid);">db kitöltés</span>
                </div>
                <div style="font-size:0.75rem; color:var(--text-mid); margin-top:0.2rem;">
                    📸 Fotót feltöltött: <strong style="color:#fff;">${withPhotoCount} fő</strong>
                </div>
            </div>

            <div class="fin-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="font-size:0.75rem; color:var(--text-mid); font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">Érem minőség</div>
                    <span style="font-size:1.1rem;">⭐</span>
                </div>
                <div style="font-size:1.8rem; font-weight:800; font-family:'Outfit',sans-serif; color:#eab308; margin-top:0.2rem;">
                    ${avgMedal} <span style="font-size:1rem; font-weight:600; color:var(--text-mid);">/ 5.0</span>
                </div>
                <div style="font-size:0.75rem; color:#4ade80; margin-top:0.2rem;">
                    ⭐⭐⭐⭐⭐ Prémium kivitelezés
                </div>
            </div>

            <div class="fin-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="font-size:0.75rem; color:var(--text-mid); font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">Szállítás & Csomagolás</div>
                    <span style="font-size:1.1rem;">📦</span>
                </div>
                <div style="font-size:1.8rem; font-weight:800; font-family:'Outfit',sans-serif; color:#f97316; margin-top:0.2rem;">
                    ${avgShipping} <span style="font-size:1rem; font-weight:600; color:var(--text-mid);">/ 5.0</span>
                </div>
                <div style="font-size:0.75rem; color:var(--text-mid); margin-top:0.2rem;">
                    Gyors Foxpost és elegáns díszdoboz
                </div>
            </div>

            <div class="fin-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="font-size:0.75rem; color:var(--text-mid); font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">NPS Ajánlási Index</div>
                    <span style="font-size:1.1rem;">🚀</span>
                </div>
                <div style="font-size:1.8rem; font-weight:800; font-family:'Outfit',sans-serif; color:#22c55e; margin-top:0.2rem;">
                    ${avgNps} <span style="font-size:1rem; font-weight:600; color:var(--text-mid);">/ 10</span>
                </div>
                <div style="font-size:0.75rem; color:#86efac; margin-top:0.2rem;">
                    ${promoterPct}% Promóter (9-10 pont)
                </div>
            </div>

            <div class="fin-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="font-size:0.75rem; color:var(--text-mid); font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">Újra részt venne?</div>
                    <span style="font-size:1.1rem;">🔄</span>
                </div>
                <div style="font-size:1.8rem; font-weight:800; font-family:'Outfit',sans-serif; color:#38bdf8; margin-top:0.2rem;">
                    ${participatePct}% <span style="font-size:1rem; font-weight:600; color:var(--text-mid);">Igen</span>
                </div>
                <div style="font-size:0.75rem; color:var(--text-mid); margin-top:0.2rem;">
                    Visszatérő túrázó bázis
                </div>
            </div>
        </div>
    `;

    // Destinations demand tag list
    let destHtml = '';
    if (topDestinations.length > 0) {
        destHtml = `
            <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.1rem 1.25rem; margin-bottom: 1.5rem;">
                <div style="font-size:0.75rem; font-weight:700; color:var(--text-mid); text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.65rem;">
                    🗺️ Leggyakrabban kért következő tájegységek a résztvevőktől:
                </div>
                <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
                    ${topDestinations.map(([name, count]) => `
                        <div style="background: rgba(255,255,255,0.04); border: 1px solid var(--border); border-radius: 6px; padding: 0.3rem 0.65rem; font-size: 0.8rem; display: flex; align-items: center; gap: 0.4rem;">
                            <span style="color:#e4e4e7; font-weight:600;">${name}</span>
                            <span style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 0.1rem 0.35rem; border-radius: 4px; font-size: 0.72rem; font-weight: 700;">${count} db</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Individual Cards List
    let cardsHtml = '';
    if (filtered.length === 0) {
        cardsHtml = `
            <div class="empty-state">
                <div class="icon">💬</div>
                <div>Nincs megjeleníthető visszajelzés a választott szűrési feltételekkel.</div>
            </div>
        `;
    } else {
        cardsHtml = filtered.map((f, idx) => {
            const run = f.runs || {};
            const runner = run.runners || {};
            const name = run.name || runner.name || 'Ismeretlen Résztvevő';
            const email = f.runner_email || runner.email || 'Nincs megadva';
            const serial = run.serial_number || '–';
            const campInfo = getCampaignInfo(run);
            const dateStr = formatDate(f.created_at);

            const nps = Number(f.nps_score || 0);
            let npsBadgeStyle = 'background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4);';
            if (nps < 7) {
                npsBadgeStyle = 'background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4);';
            } else if (nps < 9) {
                npsBadgeStyle = 'background: rgba(234, 179, 8, 0.15); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.4);';
            }

            const hasLikedText = f.tetszett_legjobban && f.tetszett_legjobban.trim() !== 'None' && f.tetszett_legjobban.trim().length > 1;
            const hasImproveText = f.jobba_tenne && f.jobba_tenne.trim() !== 'None' && f.jobba_tenne.trim().length > 1;

            return `
                <div class="proof-card" style="margin-bottom: 1.25rem; border-left: 4px solid ${campInfo.color};">
                    <div class="proof-header" style="align-items: flex-start; margin-bottom: 0.85rem;">
                        <div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: #fff;">
                                ${name}
                            </div>
                            <div style="font-size: 0.78rem; color: var(--text-mid); margin-top: 0.2rem;">
                                📧 ${email} | 🗓️ ${dateStr}
                            </div>
                        </div>
                        <div class="badges" style="display:flex; gap:0.4rem; align-items:center; flex-wrap:wrap;">
                            <span style="font-size:0.75rem; color:${campInfo.color}; border:1px solid ${campInfo.color}40; background:${campInfo.color}15; padding:0.2rem 0.5rem; border-radius:4px; font-weight:700;">
                                ${campInfo.icon} ${campInfo.name}
                            </span>
                            <span class="badge badge-serial">${serial}</span>
                            <span style="padding:0.2rem 0.5rem; border-radius:4px; font-size:0.75rem; font-weight:800; ${npsBadgeStyle}">
                                NPS ${nps}/10
                            </span>
                        </div>
                    </div>

                    <!-- Értékelési csillagok és részletek -->
                    <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; padding: 0.6rem 0.85rem; background: rgba(0,0,0,0.25); border: 1px solid var(--border); border-radius: 8px; font-size: 0.82rem;">
                        <div>
                            <span style="color: var(--text-mid);">Érem minőség:</span>
                            <strong style="color: #eab308; margin-left: 0.25rem;">${'⭐'.repeat(Number(f.erem_minoseg) || 5)} (${f.erem_minoseg}/5)</strong>
                        </div>
                        <div>
                            <span style="color: var(--text-mid);">Csomagolás & szállítás:</span>
                            <strong style="color: #f97316; margin-left: 0.25rem;">${'⭐'.repeat(Number(f.szallitas_elegedett) || 5)} (${f.szallitas_elegedett}/5)</strong>
                        </div>
                        <div>
                            <span style="color: var(--text-mid);">Újra részt venne:</span>
                            <strong style="color: #38bdf8; margin-left: 0.25rem;">${f.reszvetel_ujra || 'Igen'}</strong>
                        </div>
                    </div>

                    <!-- Szöveges visszajelzések -->
                    ${hasLikedText ? `
                        <div style="background: rgba(34, 197, 94, 0.05); border-left: 3px solid #22c55e; border-radius: 0 8px 8px 0; padding: 0.75rem 1rem; margin-bottom: 0.75rem;">
                            <div style="font-size: 0.75rem; font-weight: 700; color: #4ade80; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.25rem;">
                                💚 Mi tetszett legjobban:
                            </div>
                            <div style="font-size: 0.88rem; color: #f0f4ff; line-height: 1.45; font-style: italic;">
                                „${f.tetszett_legjobban}”
                            </div>
                        </div>
                    ` : ''}

                    ${hasImproveText ? `
                        <div style="background: rgba(245, 158, 11, 0.06); border-left: 3px solid #f59e0b; border-radius: 0 8px 8px 0; padding: 0.75rem 1rem; margin-bottom: 0.75rem;">
                            <div style="font-size: 0.75rem; font-weight: 700; color: #facc15; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.25rem;">
                                💡 Mit tenne jobbá / észrevétel:
                            </div>
                            <div style="font-size: 0.88rem; color: #f0f4ff; line-height: 1.45;">
                                „${f.jobba_tenne}”
                            </div>
                        </div>
                    ` : ''}

                    <!-- Fotó és tájegység lábléc -->
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.75rem; margin-top:0.85rem; padding-top:0.65rem; border-top:1px solid rgba(255,255,255,0.05); font-size:0.78rem;">
                        <div>
                            ${f.kovetkezo_tajegyseg ? `
                                <span style="color:var(--text-mid);">Következő célpontok:</span>
                                <span style="color:#cbd5e1; font-weight:600; margin-left:0.25rem;">${f.kovetkezo_tajegyseg}</span>
                            ` : ''}
                        </div>

                        ${f.photo_url ? `
                            <div style="display:flex; align-items:center; gap:0.5rem;">
                                <span style="color:var(--text-mid);">📸 Feltöltött fotó:</span>
                                <img src="${f.photo_url}" style="width:40px; height:40px; border-radius:6px; object-fit:cover; border:1px solid rgba(236, 72, 153, 0.5); cursor:pointer; box-shadow:0 2px 8px rgba(0,0,0,0.4);" onclick="showImageModal('${f.photo_url}')" title="Kattints a nagyításhoz">
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    contentEl.innerHTML = kpiHtml + destHtml + cardsHtml;
}
