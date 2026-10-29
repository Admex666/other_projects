const fs = require('fs');
const path = require('path');

// Try loading env from root or landing_predikalo1
const rootEnvPath = path.resolve(__dirname, '../../.env');
const localEnvPath = path.resolve(__dirname, '../.env');

if (fs.existsSync(rootEnvPath)) {
    require('dotenv').config({ path: rootEnvPath });
}
if (fs.existsSync(localEnvPath)) {
    require('dotenv').config({ path: localEnvPath });
}

const DEFAULT_PAGE_ID = '1014443515092673'; // VitaSteps canonical Page ID
const CACHE_FILE_PATH = path.resolve(__dirname, '../config/facebook_organic_posts.json');

/**
 * Resolves the VitaSteps Page Access Token.
 * If user token is provided (or FB_PAGE_ACCESS_TOKEN is a user token), calls /me/accounts
 * to get the dedicated page access token. If already a page token or user token gives page accounts,
 * returns the best token and page ID.
 */
async function resolvePageToken(providedToken, pageId = DEFAULT_PAGE_ID) {
    const inputToken = providedToken || process.env.FB_PAGE_ACCESS_TOKEN || process.env.META_ACCESS_TOKEN;
    if (!inputToken) {
        throw new Error('Nincs Facebook token konfigurálva (FB_PAGE_ACCESS_TOKEN vagy META_ACCESS_TOKEN)!');
    }

    // Step 1: Check token identity via /me
    try {
        const meRes = await fetch(`https://graph.facebook.com/v21.0/me?fields=id,name&access_token=${encodeURIComponent(inputToken)}`);
        const meData = await meRes.json();

        // If this token represents the Page itself
        if (meData && meData.id === pageId) {
            return {
                pageToken: inputToken,
                pageId: pageId,
                name: meData.name,
                tokenType: 'page'
            };
        }

        // If it's a user token or other account, query /me/accounts to find VitaSteps
        const accountsRes = await fetch(`https://graph.facebook.com/v21.0/me/accounts?access_token=${encodeURIComponent(inputToken)}`);
        const accountsData = await accountsRes.json();

        if (accountsData && Array.isArray(accountsData.data)) {
            const pageAccount = accountsData.data.find(a => a.id === pageId) || accountsData.data.find(a => (a.name || '').toLowerCase().includes('vitasteps'));
            if (pageAccount && pageAccount.access_token) {
                return {
                    pageToken: pageAccount.access_token,
                    pageId: pageAccount.id,
                    name: pageAccount.name,
                    tokenType: 'page_from_accounts'
                };
            }
        }
    } catch (err) {
        console.warn('[FB Organic] Token resolution check failed, falling back to input token:', err.message);
    }

    // Fallback: direct use
    return {
        pageToken: inputToken,
        pageId: pageId,
        tokenType: 'direct'
    };
}

/**
 * Helper to get ISO 8601 week number
 */
function getIsoWeek(dateObj) {
    const d = new Date(Date.UTC(dateObj.getFullYear(), dateObj.getMonth(), dateObj.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}

/**
 * Categorizes a post into a pillar/type and returns category info
 */
function analyzePostContent(message = '', statusType = '', hasImage = false) {
    const text = (message || '').trim();
    const lower = text.toLowerCase();

    // 1. Text statistics
    const charCount = text.length;
    const words = text ? text.split(/\s+/).filter(w => w.length > 0) : [];
    const wordCount = words.length;

    // 2. Hashtags extraction
    const hashtags = (text.match(/#[a-zA-Z0-9_\u00C0-\u024F]+/g) || []).map(h => h.trim());

    // 3. Post Category / Pillar classification
    let categoryKey = 'other';
    let categoryLabel = 'Általános bejegyzés';
    let categoryIcon = '📌';

    const isQuestion = text.includes('?') ||
        lower.includes('melyik vagy') ||
        lower.includes('nálad mi') ||
        lower.includes('mit gondolsz') ||
        lower.includes('hova mennél') ||
        lower.includes('melyik helyre') ||
        lower.includes('neked volt');

    const isEducational = lower.includes('3 dolog') ||
        lower.includes('tanács') ||
        lower.includes('tipp') ||
        lower.includes('túra előtt') ||
        lower.includes('szintemelkedés') ||
        lower.includes('felszerelés');

    const isInspirationalStory = lower.includes('emlék') ||
        lower.includes('visszagondolsz') ||
        lower.includes('élmény') ||
        lower.includes('történet') ||
        lower.includes('miért érdemes') ||
        lower.includes('legjobb élményt');

    if (isEducational) {
        categoryKey = 'educational_tips';
        categoryLabel = 'Edukáció & Túratippek';
        categoryIcon = '💡';
    } else if (isQuestion && (lower.includes('a)') || lower.includes('b)'))) {
        categoryKey = 'interactive_poll';
        categoryLabel = 'Kérdés & Szavazás (A/B)';
        categoryIcon = '📊';
    } else if (isQuestion) {
        categoryKey = 'community_question';
        categoryLabel = 'Közösségi kérdés';
        categoryIcon = '❓';
    } else if (isInspirationalStory) {
        categoryKey = 'inspiration_story';
        categoryLabel = 'Inspiráció & Élmény';
        categoryIcon = '🌄';
    } else if (hasImage && !text) {
        categoryKey = 'visual_update';
        categoryLabel = 'Vizuális frissítés (kép)';
        categoryIcon = '🖼️';
    } else if (hasImage) {
        categoryKey = 'photo_story';
        categoryLabel = 'Fotós bejegyzés';
        categoryIcon = '📸';
    }

    // 4. Format type badge
    let formatType = 'text_only';
    let formatLabel = '✍️ Szöveges poszt';
    if (hasImage) {
        formatType = 'with_image';
        formatLabel = '🖼️ Képes poszt';
    }

    return {
        char_count: charCount,
        word_count: wordCount,
        hashtags: hashtags,
        category_key: categoryKey,
        category_label: categoryLabel,
        category_icon: categoryIcon,
        format_type: formatType,
        format_label: formatLabel
    };
}

/**
 * Calculates aggregated trends and KPIs over posts
 */
function calculateAggregateTrends(posts = []) {
    if (!posts || posts.length === 0) {
        return {
            weekly_distribution: {},
            day_distribution: {},
            time_slot_distribution: {},
            category_distribution: {},
            format_distribution: { with_image: 0, text_only: 0 },
            active_weeks_count: 0,
            avg_posts_per_active_week: 0,
            avg_char_length: 0,
            top_performing_category: null
        };
    }

    const dayNames = ['Vasárnap', 'Hétfő', 'Kedd', 'Szerda', 'Csütörtök', 'Péntek', 'Szombat'];
    const weeklyMap = {};
    const dayMap = { 'Hétfő': 0, 'Kedd': 0, 'Szerda': 0, 'Csütörtök': 0, 'Péntek': 0, 'Szombat': 0, 'Vasárnap': 0 };
    const timeSlots = { 'Reggel (06-11)': 0, 'Napközben (11-16)': 0, 'Késő délután / Este (16-21)': 0, 'Éjjel (21-06)': 0 };
    const categoryMap = {};
    const formatMap = { with_image: 0, text_only: 0 };

    let totalChars = 0;
    let postsWithTextCount = 0;

    posts.forEach(p => {
        const d = new Date(p.created_time);
        const year = d.getFullYear();
        const isoWeek = getIsoWeek(d);
        const weekKey = `${year}-W${isoWeek < 10 ? '0' + isoWeek : isoWeek}`;

        // Weekly
        if (!weeklyMap[weekKey]) {
            weeklyMap[weekKey] = {
                week_key: weekKey,
                year: year,
                week_number: isoWeek,
                count: 0,
                shares: 0,
                posts: []
            };
        }
        weeklyMap[weekKey].count += 1;
        weeklyMap[weekKey].shares += (p.shares_count || 0);
        weeklyMap[weekKey].posts.push(p.id);

        // Day of week
        const dayName = dayNames[d.getDay()];
        if (dayMap[dayName] !== undefined) dayMap[dayName] += 1;

        // Time slot
        const hour = d.getHours();
        if (hour >= 6 && hour < 11) timeSlots['Reggel (06-11)'] += 1;
        else if (hour >= 11 && hour < 16) timeSlots['Napközben (11-16)'] += 1;
        else if (hour >= 16 && hour < 21) timeSlots['Késő délután / Este (16-21)'] += 1;
        else timeSlots['Éjjel (21-06)'] += 1;

        // Category
        const catKey = p.content_analysis?.category_key || 'other';
        const catLabel = p.content_analysis?.category_label || 'Egyéb';
        if (!categoryMap[catKey]) {
            categoryMap[catKey] = { key: catKey, label: catLabel, icon: p.content_analysis?.category_icon || '📌', count: 0, shares: 0 };
        }
        categoryMap[catKey].count += 1;
        categoryMap[catKey].shares += (p.shares_count || 0);

        // Format
        if (p.image_url) formatMap.with_image += 1;
        else formatMap.text_only += 1;

        // Text len
        if (p.content_analysis?.char_count > 0) {
            totalChars += p.content_analysis.char_count;
            postsWithTextCount += 1;
        }
    });

    const activeWeeks = Object.keys(weeklyMap).length;
    const avgPostsPerWeek = activeWeeks > 0 ? (posts.length / activeWeeks).toFixed(1) : 0;
    const avgChars = postsWithTextCount > 0 ? Math.round(totalChars / postsWithTextCount) : 0;

    // Find best category by count/shares
    const sortedCategories = Object.values(categoryMap).sort((a, b) => (b.shares * 10 + b.count) - (a.shares * 10 + a.count));
    const topCategory = sortedCategories.length > 0 ? sortedCategories[0] : null;

    // Sort weeks chronological
    const sortedWeeks = Object.values(weeklyMap).sort((a, b) => a.week_key.localeCompare(b.week_key));

    return {
        weekly_trend: sortedWeeks,
        day_distribution: dayMap,
        time_slot_distribution: timeSlots,
        category_distribution: Object.values(categoryMap),
        format_distribution: formatMap,
        active_weeks_count: activeWeeks,
        avg_posts_per_active_week: parseFloat(avgPostsPerWeek),
        avg_char_length: avgChars,
        top_category: topCategory
    };
}

/**
 * Fetches published posts and attempts to query engagement and insights metrics.
 */
async function fetchFacebookOrganicPosts(options = {}) {
    const forceRefresh = options.forceRefresh || false;
    const targetPageId = options.pageId || process.env.FB_PAGE_ID || DEFAULT_PAGE_ID;

    // Check cache if not forcing refresh
    if (!forceRefresh && fs.existsSync(CACHE_FILE_PATH)) {
        try {
            const cached = JSON.parse(fs.readFileSync(CACHE_FILE_PATH, 'utf8'));
            const cacheAgeMs = Date.now() - new Date(cached.last_synced_at || 0).getTime();
            // Cache valid for 30 minutes if within memory
            if (cacheAgeMs < 30 * 60 * 1000 && Array.isArray(cached.posts)) {
                return {
                    ...cached,
                    from_cache: true
                };
            }
        } catch (e) {
            console.warn('[FB Organic] Cache read error, refreshing:', e.message);
        }
    }

    const { pageToken, pageId, name } = await resolvePageToken(options.token, targetPageId);

    // 1. Fetch Page Info & Extended Stats
    let pageInfo = { id: pageId, name: name || 'VitaSteps' };
    try {
        const pageRes = await fetch(`https://graph.facebook.com/v21.0/${pageId}?fields=id,name,link,fan_count,followers_count,talking_about_count,verification_status,category,website&access_token=${encodeURIComponent(pageToken)}`);
        const pageJson = await pageRes.json();
        if (!pageJson.error) {
            pageInfo = pageJson;
        }
    } catch (e) {
        console.warn('[FB Organic] Could not fetch page info:', e.message);
    }

    // 2. Fetch Published Posts
    const postFields = [
        'id',
        'message',
        'created_time',
        'permalink_url',
        'shares',
        'status_type',
        'attachments{media,title,url,type}'
    ].join(',');

    const postsUrl = `https://graph.facebook.com/v21.0/${pageId}/published_posts?fields=${postFields}&limit=50&access_token=${encodeURIComponent(pageToken)}`;
    const postsRes = await fetch(postsUrl);
    const postsData = await postsRes.json();

    if (postsData.error) {
        throw new Error(`Facebook API Error: ${postsData.error.message} (Code: ${postsData.error.code})`);
    }

    const rawPosts = postsData.data || [];

    // 3. Process & Analyze Posts
    let permissionNotice = null;
    const processedPosts = [];

    for (const post of rawPosts) {
        const hasImage = !!(post.attachments?.data?.[0]?.media?.image?.src);
        const analysis = analyzePostContent(post.message, post.status_type, hasImage);

        const item = {
            id: post.id,
            message: post.message || '',
            created_time: post.created_time,
            permalink_url: post.permalink_url,
            shares_count: post.shares?.count || 0,
            status_type: post.status_type || null,
            image_url: post.attachments?.data?.[0]?.media?.image?.src || null,
            attachment_url: post.attachments?.data?.[0]?.url || null,
            content_analysis: analysis,
            reactions_count: null,
            comments_count: null,
            engagement_available: false,
            insights: null
        };

        // Try getting reactions summary if not yet failed with permission issue
        if (permissionNotice === null) {
            try {
                const rxRes = await fetch(`https://graph.facebook.com/v21.0/${post.id}/reactions?summary=total_count&limit=0&access_token=${encodeURIComponent(pageToken)}`);
                const rxData = await rxRes.json();
                if (rxData.error) {
                    if (rxData.error.code === 10 || (rxData.error.message && rxData.error.message.includes('pages_read_user_content'))) {
                        permissionNotice = 'Hiányzó Facebook jogosultság (pages_read_user_content). A reakciók és kommentek automatikus beolvasása ehhez a Meta engedélyhez kötött. A posztok, megosztások, szövegstatisztikák és trendek teljes körűen aktívak.';
                    }
                } else if (rxData.summary) {
                    item.reactions_count = rxData.summary.total_count || 0;
                    item.engagement_available = true;
                }
            } catch (err) {
                // Ignore network glitch on detail
            }
        }

        // Try comments if reactions succeeded
        if (item.engagement_available) {
            try {
                const cmRes = await fetch(`https://graph.facebook.com/v21.0/${post.id}/comments?summary=total_count&limit=0&access_token=${encodeURIComponent(pageToken)}`);
                const cmData = await cmRes.json();
                if (cmData.summary) {
                    item.comments_count = cmData.summary.total_count || 0;
                }
            } catch (err) {}
        }

        processedPosts.push(item);
    }

    // 4. Compute Engagement Score & Ranks
    // Calculate synthetic engagement index: shares*5 + (reactions||0)*2 + (comments||0)*3 + length bonus
    processedPosts.forEach(p => {
        let score = (p.shares_count || 0) * 5;
        if (p.reactions_count !== null) score += (p.reactions_count * 2);
        if (p.comments_count !== null) score += (p.comments_count * 3);
        if (p.content_analysis?.char_count > 100) score += 2; // substantial content
        if (p.image_url) score += 1;
        p.engagement_score = score;
    });

    // Sort by engagement score descending to assign badges
    const sortedByEngagement = [...processedPosts].sort((a, b) => (b.engagement_score || 0) - (a.engagement_score || 0));
    const maxScore = sortedByEngagement.length > 0 ? sortedByEngagement[0].engagement_score : 0;

    processedPosts.forEach(p => {
        if (maxScore > 0 && p.engagement_score === maxScore && (p.shares_count > 0 || (p.reactions_count || 0) > 0)) {
            p.performance_badge = { label: '🏆 Legjobban teljesítő', class: 'badge-top' };
        } else if (p.content_analysis?.category_key === 'interactive_poll') {
            p.performance_badge = { label: '🔥 Kiemelt interakció', class: 'badge-hot' };
        } else if (p.content_analysis?.category_key === 'educational_tips') {
            p.performance_badge = { label: '⭐ Értékes tartalom', class: 'badge-star' };
        } else {
            p.performance_badge = null;
        }
    });

    // 5. Aggregate Trends
    const trends = calculateAggregateTrends(processedPosts);

    const result = {
        success: true,
        page: pageInfo,
        total_posts: processedPosts.length,
        permission_notice: permissionNotice,
        has_full_engagement_access: permissionNotice === null,
        last_synced_at: new Date().toISOString(),
        trends: trends,
        posts: processedPosts
    };

    // Save to Cache JSON file
    try {
        const configDir = path.dirname(CACHE_FILE_PATH);
        if (!fs.existsSync(configDir)) {
            fs.mkdirSync(configDir, { recursive: true });
        }
        fs.writeFileSync(CACHE_FILE_PATH, JSON.stringify(result, null, 2), 'utf8');
        console.log(`[FB Organic] Successfully cached ${processedPosts.length} posts and calculated trends to ${CACHE_FILE_PATH}`);
    } catch (writeErr) {
        console.error('[FB Organic] Failed to write cache file:', writeErr.message);
    }

    return result;
}

// CLI Execution support
if (require.main === module) {
    (async () => {
        try {
            console.log('🔄 Facebook Organikus posztok lekérdezése és trendek elemzése folyamatban...');
            const data = await fetchFacebookOrganicPosts({ forceRefresh: true });
            console.log(`✅ Sikeres lekérés! Oldal: ${data.page?.name} (${data.page?.id})`);
            console.log(`📊 Posztok száma: ${data.total_posts}`);
            console.log(`📈 Heti bontás: ${data.trends?.weekly_trend?.map(w => w.week_key + ': ' + w.count + ' db').join(', ')}`);
            console.log(`🎯 Legjobb témapillér: ${data.trends?.top_category?.label} (${data.trends?.top_category?.count} db)`);
            console.log(`🔤 Átlagos szöveghossz: ${data.trends?.avg_char_length} karakter`);
            if (data.permission_notice) {
                console.log(`⚠️ Figyelmeztetés: ${data.permission_notice}`);
            }
        } catch (err) {
            console.error('❌ Hiba a futtatás során:', err);
            process.exit(1);
        }
    })();
}

module.exports = {
    fetchFacebookOrganicPosts,
    resolvePageToken,
    analyzePostContent,
    calculateAggregateTrends,
    CACHE_FILE_PATH
};
