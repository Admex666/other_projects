// ===== ADMIN FACEBOOK ORGANIC CONTENT & PERFORMANCE MODULE =====

let fbOrganicData = null;
let fbOrganicFilter = 'all'; // 'all', 'with_image', 'text_only'
let fbOrganicSearch = '';

/**
 * Loads Facebook Organic data from /api/admin-data
 */
async function loadFacebookOrganic(forceRefresh = false) {
    const cardsEl = document.getElementById('fb-organic-cards');
    if (!cardsEl) return;

    if (forceRefresh || !fbOrganicData) {
        cardsEl.innerHTML = `
            <div class="empty-state">
                <span class="loading-spinner"></span>
                <div style="margin-top:0.6rem; font-weight:600;">
                    ${forceRefresh ? 'Meta Graph API élő szinkronizáció folyamatban...' : 'Organikus posztok betöltése...'}
                </div>
            </div>
        `;
    }

    try {
        const url = `/api/admin-data?type=facebook_organic&secret=${encodeURIComponent(adminSecret)}${forceRefresh ? '&force_refresh=true' : ''}`;
        const res = await fetch(url);
        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.error || 'Nem sikerült betölteni a Facebook posztokat.');
        }

        fbOrganicData = data;
        renderFacebookOrganic();

    } catch (err) {
        console.error('FB Organic Load error:', err);
        cardsEl.innerHTML = `
            <div class="empty-state" style="border: 1px dashed var(--red);">
                <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">⚠️</div>
                <div style="color: var(--red); font-weight: 700; margin-bottom: 0.5rem;">Hiba a Facebook adatok betöltésekor</div>
                <div style="font-size: 0.85rem; color: var(--text-mid); max-width: 500px; margin: 0 auto 1rem auto;">${err.message}</div>
                <button class="btn btn-grey" style="width: auto; margin: 0 auto;" onclick="loadFacebookOrganic(true)">🔄 Újrapróbálás</button>
            </div>
        `;
    }
}

/**
 * Filter change handler
 */
function setFbOrganicFilter(filter) {
    fbOrganicFilter = filter;
    renderFacebookOrganic();
}

/**
 * Search input handler
 */
function handleFbOrganicSearch(val) {
    fbOrganicSearch = (val || '').toLowerCase().trim();
    renderFacebookOrganic();
}

/**
 * Helper to format ISO date to readable Hungarian format
 */
function formatFbDate(isoStr) {
    if (!isoStr) return '–';
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return isoStr;
    return d.toLocaleString('hu-HU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Calculates days ago
 */
function formatDaysAgo(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    const now = new Date();
    const diffDays = Math.floor((now - d) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'ma';
    if (diffDays === 1) return 'tegnap';
    return `${diffDays} napja`;
}

/**
 * Renders the full Facebook Organic dashboard
 */
function renderFacebookOrganic() {
    const cardsEl = document.getElementById('fb-organic-cards');
    if (!cardsEl || !fbOrganicData) return;

    const page = fbOrganicData.page || {};
    const posts = fbOrganicData.posts || [];
    const notice = fbOrganicData.permission_notice;
    const lastSync = fbOrganicData.last_synced_at;
    const fromCache = fbOrganicData.from_cache;

    // Filter posts
    let filteredPosts = posts.filter(p => {
        if (fbOrganicFilter === 'with_image' && !p.image_url) return false;
        if (fbOrganicFilter === 'text_only' && p.image_url) return false;
        if (fbOrganicSearch) {
            const msg = (p.message || '').toLowerCase();
            if (!msg.includes(fbOrganicSearch)) return false;
        }
        return true;
    });

    // Summary calculations
    const totalPosts = posts.length;
    const postsWithImages = posts.filter(p => p.image_url).length;
    const totalShares = posts.reduce((sum, p) => sum + (p.shares_count || 0), 0);
    const followers = page.followers_count || page.fan_count || 79;

    let html = `
        <!-- SUMMARY KPI CARDS -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
            
            <div class="fin-card" style="border-left: 4px solid #3b82f6;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #60a5fa; text-transform: uppercase; letter-spacing: 0.05em;">
                    📘 Facebook Oldal
                </div>
                <div style="font-size: 1.35rem; font-weight: 900; color: #fff; margin-top: 0.15rem;">
                    ${page.name || 'VitaSteps'}
                </div>
                <div style="font-size: 0.78rem; color: var(--text-mid); display: flex; align-items: center; justify-content: space-between;">
                    <span>ID: <code>${page.id || '–'}</code></span>
                    <a href="${page.link || 'https://www.facebook.com/' + page.id}" target="_blank" style="color: #60a5fa; text-decoration: none; font-weight: 600;">Oldal megnyitása ↗</a>
                </div>
            </div>

            <div class="fin-card" style="border-left: 4px solid #22c55e;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #4ade80; text-transform: uppercase; letter-spacing: 0.05em;">
                    👥 Követők & Kedvelők
                </div>
                <div style="font-size: 1.35rem; font-weight: 900; color: #fff; margin-top: 0.15rem;">
                    ${followers} fő
                </div>
                <div style="font-size: 0.78rem; color: var(--text-mid);">
                    Organikus bázis a 4 hetes teszt alatt
                </div>
            </div>

            <div class="fin-card" style="border-left: 4px solid #f97316;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #fb923c; text-transform: uppercase; letter-spacing: 0.05em;">
                    📝 Közzétett Posztok
                </div>
                <div style="font-size: 1.35rem; font-weight: 900; color: #fff; margin-top: 0.15rem;">
                    ${totalPosts} db
                </div>
                <div style="font-size: 0.78rem; color: var(--text-mid);">
                    ${postsWithImages} képes • ${totalPosts - postsWithImages} tisztán szöveges
                </div>
            </div>

            <div class="fin-card" style="border-left: 4px solid #a855f7;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #c084fc; text-transform: uppercase; letter-spacing: 0.05em;">
                    🔄 Megosztások (Összes)
                </div>
                <div style="font-size: 1.35rem; font-weight: 900; color: #fff; margin-top: 0.15rem;">
                    ${totalShares} megosztás
                </div>
                <div style="font-size: 0.78rem; color: var(--text-mid);">
                    Átlagosan ${(totalPosts > 0 ? (totalShares / totalPosts).toFixed(2) : '0')} megosztás/poszt
                </div>
            </div>

        </div>
    `;

    // Permission Notice Banner if pages_read_user_content is missing
    if (notice) {
        html += `
            <div style="background: rgba(234, 179, 8, 0.08); border: 1px solid rgba(234, 179, 8, 0.35); border-radius: var(--radius-md); padding: 0.85rem 1.15rem; margin-bottom: 1.25rem; display: flex; align-items: flex-start; gap: 0.75rem;">
                <div style="font-size: 1.3rem; line-height: 1;">💡</div>
                <div style="flex: 1; font-size: 0.8rem; color: #fef08a; line-height: 1.45;">
                    <strong style="color: #facc15;">Meta Graph API Jogosultsági Státusz:</strong>
                    ${notice}
                    <div style="margin-top: 0.25rem; color: #cbd5e1; font-size: 0.75rem;">
                        A bejegyzések szövege, dátuma, közvetlen permalinkje, csatolt képe és megosztásai automatikusan szinkronizálódnak. A poszt közvetlen Facebook linkjére kattintva a valós idejű hozzászólások és lájkok azonnal ellenőrizhetőek.
                    </div>
                </div>
            </div>
        `;
    }

    // Controls & Filter Bar
    html += `
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 0.85rem 1rem; margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem;">
            <div style="display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap;">
                <span style="font-size: 0.78rem; color: var(--text-mid); font-weight: 700; margin-right: 0.3rem;">Szűrés:</span>
                <button class="logistics-sub-tab ${fbOrganicFilter === 'all' ? 'active' : ''}" onclick="setFbOrganicFilter('all')">Összes (${totalPosts})</button>
                <button class="logistics-sub-tab ${fbOrganicFilter === 'with_image' ? 'active' : ''}" onclick="setFbOrganicFilter('with_image')">🖼️ Képes posztok (${postsWithImages})</button>
                <button class="logistics-sub-tab ${fbOrganicFilter === 'text_only' ? 'active' : ''}" onclick="setFbOrganicFilter('text_only')">📄 Csak szöveges (${totalPosts - postsWithImages})</button>
            </div>

            <div style="display: flex; gap: 0.75rem; align-items: center;">
                <input type="text" class="input-text" placeholder="Keresés poszt szövegében..." value="${fbOrganicSearch}" oninput="handleFbOrganicSearch(this.value)" style="margin-bottom: 0; width: 220px; padding: 0.4rem 0.75rem; font-size: 0.8rem;">
                <div style="font-size: 0.72rem; color: var(--text-mid); white-space: nowrap;">
                    ${fromCache ? '📦 Gyorsítótárból' : '🌐 Élő API'} • Frissítve: ${formatFbDate(lastSync)}
                </div>
            </div>
        </div>
    `;

    // Posts Grid / Table
    if (filteredPosts.length === 0) {
        html += `
            <div class="empty-state">
                <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">🔍</div>
                <div>Nincs a megadott szűrésnek megfelelő Facebook bejegyzés.</div>
            </div>
        `;
    } else {
        html += `<div style="display: flex; flex-direction: column; gap: 1rem;">`;

        filteredPosts.forEach((p, idx) => {
            const hasMsg = p.message && p.message.trim().length > 0;
            const msgLines = hasMsg ? p.message.split('\n') : [];
            const titleLine = msgLines[0] || 'Tartalom nélküli státuszfrissítés / kép';
            const restOfMsg = msgLines.slice(1).join('\n').trim();

            html += `
                <div class="card" style="margin-bottom: 0; border: 1px solid var(--border); transition: border-color 0.2s;" onmouseenter="this.style.borderColor='rgba(59,130,246,0.4)'" onmouseleave="this.style.borderColor='var(--border)'">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap;">
                        
                        <div style="flex: 1; min-width: 280px;">
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem;">
                                <span class="badge" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); font-size: 0.72rem;">
                                    #${totalPosts - idx}
                                </span>
                                <span style="font-size: 0.78rem; color: var(--text-mid); font-weight: 600;">
                                    📅 ${formatFbDate(p.created_time)} <span style="color: #94a3b8; font-size: 0.72rem;">(${formatDaysAgo(p.created_time)})</span>
                                </span>
                                ${p.status_type ? `
                                    <span style="font-size: 0.7rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 0.15rem 0.4rem; border-radius: 4px;">
                                        ${p.status_type}
                                    </span>
                                ` : ''}
                            </div>

                            <div style="font-size: 0.95rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; line-height: 1.4;">
                                ${titleLine}
                            </div>

                            ${restOfMsg ? `
                                <div style="font-size: 0.82rem; color: #cbd5e1; white-space: pre-line; line-height: 1.5; margin-bottom: 0.85rem; max-height: 180px; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 0.6rem 0.85rem; border-radius: 6px; border: 1px solid rgba(255,255,255,0.04);">
                                    ${restOfMsg}
                                </div>
                            ` : ''}

                            <div style="display: flex; align-items: center; gap: 0.9rem; font-size: 0.78rem; color: var(--text-mid); flex-wrap: wrap; margin-top: 0.4rem;">
                                <span style="display: inline-flex; align-items: center; gap: 0.3rem;">
                                    <span>🔄</span> <strong>${p.shares_count}</strong> megosztás
                                </span>
                                ${p.reactions_count !== null ? `
                                    <span style="display: inline-flex; align-items: center; gap: 0.3rem; color: #38bdf8;">
                                        <span>👍</span> <strong>${p.reactions_count}</strong> reakció
                                    </span>
                                ` : ''}
                                ${p.comments_count !== null ? `
                                    <span style="display: inline-flex; align-items: center; gap: 0.3rem; color: #ec4899;">
                                        <span>💬</span> <strong>${p.comments_count}</strong> komment
                                    </span>
                                ` : ''}
                                <span>ID: <code style="font-size: 0.72rem;">${p.id}</code></span>
                            </div>
                        </div>

                        <!-- KÉP ÉS KÜLSŐ HIVATKOZÁS -->
                        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.75rem; min-width: 140px;">
                            ${p.image_url ? `
                                <div style="position: relative; width: 140px; height: 95px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); cursor: pointer;" onclick="showImageModal('${p.image_url}')">
                                    <img src="${p.image_url}" alt="Poszt képe" style="width: 100%; height: 100%; object-fit: cover;">
                                    <div style="position: absolute; bottom: 4px; right: 4px; background: rgba(0,0,0,0.7); font-size: 0.65rem; color: #fff; padding: 0.1rem 0.35rem; border-radius: 4px;">🔍 Kép</div>
                                </div>
                            ` : `
                                <div style="width: 140px; height: 70px; border-radius: 8px; border: 1px dashed rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-size: 0.75rem; color: var(--text-mid);">
                                    Szöveges poszt
                                </div>
                            `}

                            ${p.permalink_url ? `
                                <a href="${p.permalink_url}" target="_blank" class="btn btn-grey" style="width: auto; padding: 0.4rem 0.85rem; font-size: 0.78rem; text-decoration: none; display: inline-flex; align-items: center; gap: 0.35rem; color: #60a5fa; border-color: rgba(59, 130, 246, 0.4);">
                                    <span>Megnyitás FB-on</span> <span>↗</span>
                                </a>
                            ` : ''}
                        </div>

                    </div>
                </div>
            `;
        });

        html += `</div>`;
    }

    cardsEl.innerHTML = html;
}
