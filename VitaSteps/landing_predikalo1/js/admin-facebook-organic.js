// ===== ADMIN FACEBOOK ORGANIC CONTENT & PERFORMANCE MODULE =====

let fbOrganicData = null;
let fbOrganicFilter = 'all'; // 'all', 'with_image', 'text_only', or category_key
let fbOrganicSearch = '';
let fbOrganicSort = 'date_desc'; // 'date_desc', 'date_asc', 'length_desc', 'shares_desc'

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
 * Sort change handler
 */
function setFbOrganicSort(sortVal) {
    fbOrganicSort = sortVal;
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
 * Calculates days ago with friendly relative formatting
 */
function formatDaysAgo(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    const now = new Date();
    const diffMs = now - d;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffHours < 24) {
        if (diffHours <= 1) return 'nemrég';
        return `${diffHours} órája`;
    }
    if (diffDays === 1) return 'tegnap';
    if (diffDays < 7) return `${diffDays} napja`;
    const weeks = Math.floor(diffDays / 7);
    return `${weeks} hete (${diffDays} napja)`;
}

/**
 * Formats day of week
 */
function getFbDayName(isoStr) {
    if (!isoStr) return '';
    const dayNames = ['Vasárnap', 'Hétfő', 'Kedd', 'Szerda', 'Csütörtök', 'Péntek', 'Szombat'];
    const d = new Date(isoStr);
    return isNaN(d.getTime()) ? '' : dayNames[d.getDay()];
}

/**
 * Renders the full Facebook Organic dashboard
 */
function renderFacebookOrganic() {
    const cardsEl = document.getElementById('fb-organic-cards');
    if (!cardsEl || !fbOrganicData) return;

    const page = fbOrganicData.page || {};
    const posts = fbOrganicData.posts || [];
    const trends = fbOrganicData.trends || {};
    const notice = fbOrganicData.permission_notice;
    const lastSync = fbOrganicData.last_synced_at;
    const fromCache = fbOrganicData.from_cache;

    // Filter posts
    let filteredPosts = posts.filter(p => {
        if (fbOrganicFilter === 'with_image' && !p.image_url) return false;
        if (fbOrganicFilter === 'text_only' && p.image_url) return false;
        if (fbOrganicFilter.startsWith('cat_')) {
            const targetCat = fbOrganicFilter.replace('cat_', '');
            if (p.content_analysis?.category_key !== targetCat) return false;
        }
        if (fbOrganicSearch) {
            const msg = (p.message || '').toLowerCase();
            const cat = (p.content_analysis?.category_label || '').toLowerCase();
            if (!msg.includes(fbOrganicSearch) && !cat.includes(fbOrganicSearch)) return false;
        }
        return true;
    });

    // Sort posts
    filteredPosts.sort((a, b) => {
        if (fbOrganicSort === 'date_asc') {
            return new Date(a.created_time) - new Date(b.created_time);
        } else if (fbOrganicSort === 'length_desc') {
            return (b.content_analysis?.char_count || 0) - (a.content_analysis?.char_count || 0);
        } else if (fbOrganicSort === 'shares_desc') {
            return (b.shares_count || 0) - (a.shares_count || 0);
        }
        // default date_desc
        return new Date(b.created_time) - new Date(a.created_time);
    });

    // Summary calculations
    const totalPosts = posts.length;
    const postsWithImages = trends.format_distribution?.with_image ?? posts.filter(p => p.image_url).length;
    const textOnlyPosts = trends.format_distribution?.text_only ?? (totalPosts - postsWithImages);
    const totalShares = posts.reduce((sum, p) => sum + (p.shares_count || 0), 0);
    const followers = page.followers_count || page.fan_count || 79;
    const talkingAbout = page.talking_about_count || 0;
    const avgPostsPerWeek = trends.avg_posts_per_active_week || (totalPosts > 0 ? (totalPosts / 4).toFixed(1) : 0);
    const avgChars = trends.avg_char_length || 0;
    const topCat = trends.top_category || { label: 'Közösségi kérdés', count: 4, icon: '❓' };
    const imageRatio = totalPosts > 0 ? Math.round((postsWithImages / totalPosts) * 100) : 0;

    let html = `
        <!-- 1. TOP STATS & KPI HERO GRID -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin-bottom: 1.25rem;">
            
            <div class="fin-card" style="border-left: 4px solid #3b82f6;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #60a5fa; text-transform: uppercase; letter-spacing: 0.05em; display: flex; justify-content: space-between;">
                    <span>📘 Meta Oldal</span>
                    <span style="font-size: 0.68rem; background: rgba(59,130,246,0.15); padding: 0.1rem 0.35rem; border-radius: 4px; color: #93c5fd;">4 hetes teszt</span>
                </div>
                <div style="font-size: 1.35rem; font-weight: 900; color: #fff; margin-top: 0.2rem;">
                    ${page.name || 'VitaSteps'}
                </div>
                <div style="font-size: 0.76rem; color: var(--text-mid); display: flex; align-items: center; justify-content: space-between; margin-top: 0.2rem;">
                    <span>ID: <code>${page.id || '–'}</code></span>
                    <a href="${page.link || 'https://www.facebook.com/' + page.id}" target="_blank" style="color: #60a5fa; text-decoration: none; font-weight: 600;">Megnyitás ↗</a>
                </div>
            </div>

            <div class="fin-card" style="border-left: 4px solid #22c55e;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #4ade80; text-transform: uppercase; letter-spacing: 0.05em;">
                    👥 Követők & Aktív Beszélők
                </div>
                <div style="font-size: 1.35rem; font-weight: 900; color: #fff; margin-top: 0.2rem; display: flex; align-items: baseline; gap: 0.4rem;">
                    <span>${followers}</span> <span style="font-size: 0.82rem; font-weight: 600; color: #86efac;">követő</span>
                    <span style="font-size: 0.75rem; color: var(--text-mid); margin-left: auto;">🔥 ${talkingAbout} aktív beszélő</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.2rem;">
                    Organikus bázisépítés az indulás óta
                </div>
            </div>

            <div class="fin-card" style="border-left: 4px solid #f97316;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #fb923c; text-transform: uppercase; letter-spacing: 0.05em;">
                    📝 Közzétett Posztok & Gyakoriság
                </div>
                <div style="font-size: 1.35rem; font-weight: 900; color: #fff; margin-top: 0.2rem; display: flex; align-items: baseline; gap: 0.4rem;">
                    <span>${totalPosts} db</span>
                    <span style="font-size: 0.8rem; font-weight: 700; color: #fdba74;">(~${avgPostsPerWeek} poszt / hét)</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.2rem;">
                    🖼️ ${imageRatio}% képes (${postsWithImages}) • ✍️ ${100 - imageRatio}% szöveges (${textOnlyPosts})
                </div>
            </div>

            <div class="fin-card" style="border-left: 4px solid #a855f7;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #c084fc; text-transform: uppercase; letter-spacing: 0.05em;">
                    🎯 Vezető Témapillér
                </div>
                <div style="font-size: 1.15rem; font-weight: 900; color: #fff; margin-top: 0.2rem; display: flex; align-items: center; gap: 0.4rem;">
                    <span>${topCat.icon || '❓'}</span> <span>${topCat.label}</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.2rem;">
                    ${topCat.count} bejegyzés • Átlagos szöveghossz: <strong style="color: #e2e8f0;">${avgChars} kar.</strong>
                </div>
            </div>

            <div class="fin-card" style="border-left: 4px solid #eab308;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #fde047; text-transform: uppercase; letter-spacing: 0.05em;">
                    🔄 Megosztások & Viralitás
                </div>
                <div style="font-size: 1.35rem; font-weight: 900; color: #fff; margin-top: 0.2rem;">
                    ${totalShares} megosztás
                </div>
                <div style="font-size: 0.75rem; color: var(--text-mid); margin-top: 0.2rem;">
                    Átlagosan ${(totalPosts > 0 ? (totalShares / totalPosts).toFixed(2) : '0')} megosztás / poszt
                </div>
            </div>

        </div>
    `;

    // 2. TRENDS & DISTRIBUTION PANEL
    const weeklyTrend = trends.weekly_trend || [];
    const dayDist = trends.day_distribution || {};
    const catDist = trends.category_distribution || [];

    html += `
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.15rem 1.25rem; margin-bottom: 1.25rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
                <div style="font-size: 0.92rem; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 0.45rem;">
                    <span>📈</span> <span>Tartalom-Stratégiai Trendek & Megoszlás (4 hetes periódus)</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-mid);">
                    Összesen ${trends.active_weeks_count || 0} aktív hét adatai
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.25rem;">
                
                <!-- Heti Bontás Trend Grafikon / Sávok -->
                <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 0.85rem 1rem;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 0.75rem; display: flex; justify-content: space-between;">
                        <span>📅 Heti posztgyakoriság</span>
                        <span>Darabszám</span>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 0.55rem;">
    `;

    const maxWeekly = Math.max(...weeklyTrend.map(w => w.count), 1);
    weeklyTrend.forEach(w => {
        const pct = Math.round((w.count / maxWeekly) * 100);
        html += `
            <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 0.2rem;">
                    <span style="font-weight: 600; color: #e2e8f0;">${w.week_key} (${w.week_number}. hét)</span>
                    <span style="font-weight: 800; color: #38bdf8;">${w.count} poszt</span>
                </div>
                <div style="width: 100%; height: 7px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden;">
                    <div style="width: ${pct}%; height: 100%; background: linear-gradient(90deg, #38bdf8, #818cf8); border-radius: 4px;"></div>
                </div>
            </div>
        `;
    });

    html += `
                    </div>
                </div>

                <!-- Napok Szerinti Aktivitás -->
                <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 0.85rem 1rem;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 0.75rem;">
                        🗓️ Legaktívabb napok
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 0.35rem; text-align: center;">
    `;

    const dayShorts = { 'Hétfő': 'H', 'Kedd': 'K', 'Szerda': 'Sze', 'Csütörtök': 'Cs', 'Péntek': 'P', 'Szombat': 'Szo', 'Vasárnap': 'V' };
    const maxDayCount = Math.max(...Object.values(dayDist), 1);

    Object.keys(dayShorts).forEach(dName => {
        const cnt = dayDist[dName] || 0;
        const isTop = cnt === maxDayCount && cnt > 0;
        html += `
            <div style="background: ${isTop ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255,255,255,0.03)'}; border: 1px solid ${isTop ? 'rgba(34, 197, 94, 0.4)' : 'rgba(255,255,255,0.06)'}; border-radius: 6px; padding: 0.5rem 0.2rem;">
                <div style="font-size: 0.7rem; color: ${isTop ? '#86efac' : '#94a3b8'}; font-weight: 700;">${dayShorts[dName]}</div>
                <div style="font-size: 1.05rem; font-weight: 900; color: ${isTop ? '#4ade80' : '#fff'}; margin-top: 0.15rem;">${cnt}</div>
            </div>
        `;
    });

    html += `
                    </div>
                    <div style="font-size: 0.72rem; color: var(--text-mid); margin-top: 0.75rem; text-align: center;">
                        Leggyakoribb közzétételi nap: <strong style="color: #4ade80;">Szombat & Kedd</strong>
                    </div>
                </div>

                <!-- Témapillér Megoszlás -->
                <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 0.85rem 1rem;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 0.75rem; display: flex; justify-content: space-between;">
                        <span>🏷️ Témapillérek aránya</span>
                        <span>Részesedés</span>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 0.45rem;">
    `;

    catDist.forEach(c => {
        const cPct = totalPosts > 0 ? Math.round((c.count / totalPosts) * 100) : 0;
        html += `
            <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem;">
                <span style="color: #cbd5e1; display: inline-flex; align-items: center; gap: 0.35rem;">
                    <span>${c.icon}</span> <strong>${c.label}</strong>
                </span>
                <span style="color: #94a3b8; font-weight: 700;">${c.count} db (${cPct}%)</span>
            </div>
        `;
    });

    html += `
                    </div>
                </div>

            </div>
        </div>
    `;

    // 3. Permission Notice Banner if pages_read_user_content is missing
    if (notice) {
        html += `
            <div style="background: rgba(234, 179, 8, 0.08); border: 1px solid rgba(234, 179, 8, 0.35); border-radius: var(--radius-md); padding: 0.85rem 1.15rem; margin-bottom: 1.25rem; display: flex; align-items: flex-start; gap: 0.75rem;">
                <div style="font-size: 1.3rem; line-height: 1;">💡</div>
                <div style="flex: 1; font-size: 0.8rem; color: #fef08a; line-height: 1.45;">
                    <strong style="color: #facc15;">Meta Graph API Jogosultsági Státusz:</strong>
                    ${notice}
                    <div style="margin-top: 0.25rem; color: #cbd5e1; font-size: 0.75rem;">
                        A bejegyzések szövege, dátuma, közvetlen linkje, csatolt képe, szöveghosszúsága, témakategóriája és megosztásai automatikusan szinkronizálódnak.
                    </div>
                </div>
            </div>
        `;
    }

    // 4. Controls, Sorting & Filter Bar
    html += `
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 0.85rem 1rem; margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem;">
            
            <div style="display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap;">
                <span style="font-size: 0.78rem; color: var(--text-mid); font-weight: 700; margin-right: 0.3rem;">Szűrés:</span>
                <button class="logistics-sub-tab ${fbOrganicFilter === 'all' ? 'active' : ''}" onclick="setFbOrganicFilter('all')">Összes (${totalPosts})</button>
                <button class="logistics-sub-tab ${fbOrganicFilter === 'with_image' ? 'active' : ''}" onclick="setFbOrganicFilter('with_image')">🖼️ Képes (${postsWithImages})</button>
                <button class="logistics-sub-tab ${fbOrganicFilter === 'text_only' ? 'active' : ''}" onclick="setFbOrganicFilter('text_only')">✍️ Szöveges (${textOnlyPosts})</button>
                <button class="logistics-sub-tab ${fbOrganicFilter === 'cat_community_question' ? 'active' : ''}" onclick="setFbOrganicFilter('cat_community_question')">❓ Kérdések</button>
                <button class="logistics-sub-tab ${fbOrganicFilter === 'cat_educational_tips' ? 'active' : ''}" onclick="setFbOrganicFilter('cat_educational_tips')">💡 Tippek</button>
            </div>

            <div style="display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap;">
                <select class="input-select" onchange="setFbOrganicSort(this.value)" style="margin-bottom: 0; padding: 0.4rem 0.65rem; font-size: 0.78rem; background: var(--surface); color: var(--text-light); border: 1px solid var(--border); border-radius: 6px;">
                    <option value="date_desc" ${fbOrganicSort === 'date_desc' ? 'selected' : ''}>📅 Időrend: Legújabb elöl</option>
                    <option value="date_asc" ${fbOrganicSort === 'date_asc' ? 'selected' : ''}>📅 Időrend: Legrégebbi elöl</option>
                    <option value="length_desc" ${fbOrganicSort === 'length_desc' ? 'selected' : ''}>🔤 Szöveghosszúság szerint</option>
                    <option value="shares_desc" ${fbOrganicSort === 'shares_desc' ? 'selected' : ''}>🔄 Megosztások száma szerint</option>
                </select>

                <input type="text" class="input-text" placeholder="Keresés poszt szövegében..." value="${fbOrganicSearch}" oninput="handleFbOrganicSearch(this.value)" style="margin-bottom: 0; width: 200px; padding: 0.4rem 0.75rem; font-size: 0.8rem;">
                
                <div style="font-size: 0.72rem; color: var(--text-mid); white-space: nowrap;">
                    ${fromCache ? '📦 Gyorsítótárból' : '🌐 Élő API'} • ${formatFbDate(lastSync)}
                </div>
            </div>
        </div>
    `;

    // 5. Posts Feed Grid
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
            const titleLine = msgLines[0] || 'Vizuális bejegyzés / Fotófrissítés';
            const restOfMsg = msgLines.slice(1).join('\n').trim();
            const analysis = p.content_analysis || {};
            const dayName = getFbDayName(p.created_time);

            html += `
                <div class="card" style="margin-bottom: 0; border: 1px solid var(--border); transition: border-color 0.2s; position: relative;" onmouseenter="this.style.borderColor='rgba(59,130,246,0.4)'" onmouseleave="this.style.borderColor='var(--border)'">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap;">
                        
                        <div style="flex: 1; min-width: 280px;">
                            
                            <!-- Jelvények sáv: kategória, sorszám, időpont, relatív idő -->
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.6rem; flex-wrap: wrap;">
                                <span class="badge" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); font-size: 0.72rem; font-weight: 800;">
                                    #${totalPosts - idx}
                                </span>

                                <span style="font-size: 0.75rem; color: #94a3b8; font-weight: 700; background: rgba(255,255,255,0.04); padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid rgba(255,255,255,0.06);">
                                    📅 ${dayName}, ${formatFbDate(p.created_time)} <span style="color: #38bdf8;">(${formatDaysAgo(p.created_time)})</span>
                                </span>

                                <span style="font-size: 0.72rem; color: #cbd5e1; background: rgba(147, 51, 234, 0.15); border: 1px solid rgba(147, 51, 234, 0.3); padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 700;">
                                    ${analysis.category_icon || '📌'} ${analysis.category_label || 'Bejegyzés'}
                                </span>

                                <span style="font-size: 0.72rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 0.2rem 0.5rem; border-radius: 4px;">
                                    ${analysis.format_label || (p.image_url ? '🖼️ Képes' : '✍️ Szöveges')}
                                </span>

                                ${p.performance_badge ? `
                                    <span style="font-size: 0.72rem; font-weight: 800; color: #facc15; background: rgba(234, 179, 8, 0.15); border: 1px solid rgba(234, 179, 8, 0.3); padding: 0.2rem 0.5rem; border-radius: 4px;">
                                        ${p.performance_badge.label}
                                    </span>
                                ` : ''}
                            </div>

                            <!-- Címsor / Első sor -->
                            <div style="font-size: 0.98rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; line-height: 1.45;">
                                ${titleLine}
                            </div>

                            <!-- Teljes szövegtörzs ha van -->
                            ${restOfMsg ? `
                                <div style="font-size: 0.82rem; color: #cbd5e1; white-space: pre-line; line-height: 1.55; margin-bottom: 0.85rem; max-height: 200px; overflow-y: auto; background: rgba(0,0,0,0.25); padding: 0.65rem 0.9rem; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                                    ${restOfMsg}
                                </div>
                            ` : ''}

                            <!-- Poszt részletes statisztikai mutatói (megosztás, szöveghossz, szószám, reakciók) -->
                            <div style="display: flex; align-items: center; gap: 0.9rem; font-size: 0.75rem; color: var(--text-mid); flex-wrap: wrap; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.05);">
                                <span style="display: inline-flex; align-items: center; gap: 0.3rem; background: rgba(168, 85, 247, 0.12); padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid rgba(168, 85, 247, 0.25); color: #c084fc;">
                                    <span>🔄</span> <strong>${p.shares_count || 0}</strong> megosztás
                                </span>

                                <span style="display: inline-flex; align-items: center; gap: 0.3rem; background: rgba(56, 189, 248, 0.1); padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid rgba(56, 189, 248, 0.2); color: #38bdf8;">
                                    <span>🔤</span> <strong>${analysis.char_count || 0}</strong> karakter <span style="color: #94a3b8;">(${analysis.word_count || 0} szó)</span>
                                </span>

                                ${analysis.hashtags && analysis.hashtags.length > 0 ? `
                                    <span style="display: inline-flex; align-items: center; gap: 0.3rem; color: #a78bfa;">
                                        <span>🏷️</span> ${analysis.hashtags.join(' ')}
                                    </span>
                                ` : `
                                    <span style="color: #64748b; font-size: 0.7rem;">(Nincs hashtag)</span>
                                `}

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

                                <span style="margin-left: auto; color: #64748b; font-size: 0.7rem;">
                                    ID: <code>${p.id}</code>
                                </span>
                            </div>

                        </div>

                        <!-- KÉP ELŐNÉZET ÉS KÜLSŐ HIVATKOZÁS -->
                        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.75rem; min-width: 150px;">
                            ${p.image_url ? `
                                <div style="position: relative; width: 150px; height: 100px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); cursor: pointer;" onclick="showImageModal('${p.image_url}')">
                                    <img src="${p.image_url}" alt="Poszt képe" style="width: 100%; height: 100%; object-fit: cover;">
                                    <div style="position: absolute; bottom: 4px; right: 4px; background: rgba(0,0,0,0.75); font-size: 0.65rem; color: #fff; padding: 0.15rem 0.4rem; border-radius: 4px;">🔍 Kép nagyítása</div>
                                </div>
                            ` : `
                                <div style="width: 150px; height: 80px; border-radius: 8px; border: 1px dashed rgba(255,255,255,0.12); display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 0.75rem; color: var(--text-mid); background: rgba(255,255,255,0.01);">
                                    <span style="font-size: 1.2rem; margin-bottom: 0.2rem;">✍️</span>
                                    <span>Tisztán szöveges</span>
                                </div>
                            `}

                            ${p.permalink_url ? `
                                <a href="${p.permalink_url}" target="_blank" class="btn btn-grey" style="width: auto; padding: 0.45rem 0.85rem; font-size: 0.78rem; text-decoration: none; display: inline-flex; align-items: center; gap: 0.35rem; color: #60a5fa; border-color: rgba(59, 130, 246, 0.4); font-weight: 600;">
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
