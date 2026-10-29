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

    // 1. Fetch Page Info
    let pageInfo = { id: pageId, name: name || 'VitaSteps' };
    try {
        const pageRes = await fetch(`https://graph.facebook.com/v21.0/${pageId}?fields=id,name,link,followers_count,fan_count&access_token=${encodeURIComponent(pageToken)}`);
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

    // 3. Check / Attempt Engagement metrics per post
    // Note: 'reactions' and 'comments' require 'pages_read_user_content' permission.
    // If not granted, we gracefully fallback and flag permission status.
    let permissionNotice = null;
    const processedPosts = [];

    for (const post of rawPosts) {
        const item = {
            id: post.id,
            message: post.message || '',
            created_time: post.created_time,
            permalink_url: post.permalink_url,
            shares_count: post.shares?.count || 0,
            status_type: post.status_type || null,
            image_url: post.attachments?.data?.[0]?.media?.image?.src || null,
            attachment_url: post.attachments?.data?.[0]?.url || null,
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
                        permissionNotice = 'Hiányzó Facebook jogosultság (pages_read_user_content). A reakciók és kommentek automatikus beolvasása ehhez a Meta engedélyhez kötött. A posztok és megosztások megjelenítése aktív.';
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

    const result = {
        success: true,
        page: pageInfo,
        total_posts: processedPosts.length,
        permission_notice: permissionNotice,
        has_full_engagement_access: permissionNotice === null,
        last_synced_at: new Date().toISOString(),
        posts: processedPosts
    };

    // Save to Cache JSON file
    try {
        const configDir = path.dirname(CACHE_FILE_PATH);
        if (!fs.existsSync(configDir)) {
            fs.mkdirSync(configDir, { recursive: true });
        }
        fs.writeFileSync(CACHE_FILE_PATH, JSON.stringify(result, null, 2), 'utf8');
        console.log(`[FB Organic] Successfully cached ${processedPosts.length} posts to ${CACHE_FILE_PATH}`);
    } catch (writeErr) {
        console.error('[FB Organic] Failed to write cache file:', writeErr.message);
    }

    return result;
}

// CLI Execution support
if (require.main === module) {
    (async () => {
        try {
            console.log('🔄 Facebook Organikus posztok lekérdezése folyamatban...');
            const data = await fetchFacebookOrganicPosts({ forceRefresh: true });
            console.log(`✅ Sikeres lekérés! Oldal: ${data.page?.name} (${data.page?.id})`);
            console.log(`📊 Posztok száma: ${data.total_posts}`);
            if (data.permission_notice) {
                console.log(`⚠️ Figyelmeztetés: ${data.permission_notice}`);
            }
            console.log('\n--- Legutóbbi posztok ---');
            data.posts.slice(0, 3).forEach((p, i) => {
                console.log(`\n[#${i+1}] ${p.created_time} | ID: ${p.id}`);
                console.log(`    Szöveg: ${(p.message || '').slice(0, 80).replace(/\n/g, ' ')}...`);
                console.log(`    Link: ${p.permalink_url}`);
                console.log(`    Kép: ${p.image_url ? 'Igen' : 'Nincs'}`);
            });
        } catch (err) {
            console.error('❌ Hiba a futtatás során:', err);
            process.exit(1);
        }
    })();
}

module.exports = {
    fetchFacebookOrganicPosts,
    resolvePageToken,
    CACHE_FILE_PATH
};
