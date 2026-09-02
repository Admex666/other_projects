const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

function getCreativeCsvData() {
    const candidates = [
        path.join(__dirname, '..', 'meta_kreativ_napi_riport.csv'),
        path.join(__dirname, 'meta_kreativ_napi_riport.csv'),
        path.join(process.cwd(), 'landing_predikalo1', 'meta_kreativ_napi_riport.csv'),
        path.join(process.cwd(), 'meta_kreativ_napi_riport.csv'),
    ];
    for (const p of candidates) {
        if (fs.existsSync(p)) {
            try {
                const content = fs.readFileSync(p, 'utf8');
                const lines = content.trim().split('\n');
                if (lines.length < 2) continue;
                const headers = lines[0].trim().split(';').map(h => h.trim());
                const rows = [];
                for (let i = 1; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (!line) continue;
                    const parts = line.split(';');
                    if (parts.length < headers.length) continue;
                    const r = {};
                    headers.forEach((h, idx) => { r[h] = (parts[idx] || '').trim(); });
                    rows.push({
                        date: r['Datum'],
                        campaign_name: r['Kampany'],
                        adset_name: r['Hirdetes_Sorozat'],
                        ad_name: r['Kreativ_Nev'],
                        ad_id: r['Hirdetes_ID'],
                        spend: Number(r['Koltes_HUF'] || 0),
                        impressions: Number(r['Megjelenes'] || 0),
                        reach: Number(r['Eleres'] || 0),
                        frequency: Number(r['Gyakorisag'] || 0),
                        clicks: Number(r['Osszes_Kattintas'] || 0),
                        link_clicks: Number(r['Link_Kattintas'] || 0),
                        ctr: Number(r['CTR_Szazalek'] || 0),
                        cpc: Number(r['CPC_HUF'] || 0),
                        cpm: Number(r['CPM_HUF'] || 0),
                        purchases: Number(r['Vasarlas_DB'] || 0),
                        revenue: Number(r['Bevetel_HUF'] || 0),
                        cpa: Number(r['CPA_HUF'] || 0),
                        roas: Number(r['ROAS'] || 0),
                    });
                }
                return rows;
            } catch (e) {
                console.error('Error parsing creative CSV:', e);
            }
        }
    }
    return [];
}

function parseRevolutDate(str) {
    if (!str) return 0;
    const parts = str.trim().split(' ');
    if (parts.length === 2) {
        const [y, m, d] = parts[0].split('-').map(Number);
        const [hh, mm, ss] = parts[1].split(':').map(Number);
        return new Date(y, m - 1, d, hh || 0, mm || 0, ss || 0).getTime();
    }
    const t = new Date(str).getTime();
    return isNaN(t) ? 0 : t;
}

function parseRevolutCsv(content) {
    if (!content) return [];
    const cleanContent = content.replace(/\r/g, '');
    const lines = cleanContent.trim().split('\n');
    if (lines.length < 2) return [];
    const rows = [];
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        const parts = line.split(',');
        if (parts.length < 6) continue;

        const type = (parts[0] || '').trim();
        const product = (parts[1] || '').trim();
        const startedDate = (parts[2] || '').trim();
        const completedDate = (parts[3] || '').trim();
        const description = (parts[4] || '').trim();
        const amount = parseFloat(parts[5]) || 0;
        const fee = parseFloat(parts[6]) || 0;
        const currency = (parts[7] || 'HUF').trim();
        const state = (parts[8] || 'ELVÉGEZVE').trim();
        const balance = parseFloat(parts[9]) || 0;

        // Smart categorization
        const descLower = description.toLowerCase();
        let category = 'other';
        let categoryLabel = '📦 Egyéb működés';
        let categoryColor = '#94a3b8';

        if (descLower.includes('facebook') || descLower.includes('meta')) {
            category = 'marketing';
            categoryLabel = '📢 Marketing (Meta)';
            categoryColor = '#f87171';
        } else if (descLower.includes('stripe') || descLower.includes('technology europe')) {
            category = 'stripe_payout';
            categoryLabel = '💰 Stripe Kifizetés';
            categoryColor = '#22c55e';
        } else if (descLower.includes('foxpost')) {
            category = 'shipping';
            categoryLabel = '🦊 Foxpost Szállítás';
            categoryColor = '#f97316';
        } else if (descLower.includes('simplep') || descLower.includes('boríték') || descLower.includes('csomagol')) {
            category = 'packaging';
            categoryLabel = '📦 Csomagolás';
            categoryColor = '#fb923c';
        } else if (descLower.includes('péter lászló') || descLower.includes('konyvel') || descLower.includes('könyvel')) {
            category = 'accounting';
            categoryLabel = '💼 Könyvelés (Opex)';
            categoryColor = '#c084fc';
        } else if (descLower.includes('kboss') || descLower.includes('számlázz') || descLower.includes('szamlazz')) {
            category = 'software';
            categoryLabel = '🧾 Számlázz.hu Szoftver';
            categoryColor = '#a855f7';
        } else if (descLower.includes('alibaba') || descLower.includes('devizaváltás') || descLower.includes('usd') || descLower.includes('érem') || descLower.includes('erem')) {
            category = 'capex';
            categoryLabel = '🏅 Éremgyártás (Capex)';
            categoryColor = '#38bdf8';
        } else if (descLower.includes('google pay') || descLower.includes('feltöltés') || descLower.includes('topup')) {
            category = 'deposit';
            categoryLabel = '🏦 Kezdőtőke / Betét';
            categoryColor = '#a3e635';
        } else if (descLower.includes('nav') || descLower.includes('adó') || descLower.includes('ado')) {
            category = 'tax';
            categoryLabel = '🏛️ NAV ÁFA / Adó';
            categoryColor = '#eab308';
        } else if (descLower.includes('cashback') || descLower.includes('pénzvisszatérítés')) {
            category = 'cashback';
            categoryLabel = '✨ Pro Cashback';
            categoryColor = '#4ade80';
        } else if (descLower.includes('merchant payment') || type === 'MERCHANT_PAYMENT') {
            category = 'direct_sale';
            categoryLabel = '💳 Közvetlen Eladás';
            categoryColor = '#22c55e';
        }

        rows.push({
            type,
            product,
            startedDate,
            completedDate,
            description,
            amount,
            fee,
            currency,
            state,
            balance,
            category,
            categoryLabel,
            categoryColor
        });
    }

    // Sort descending so the most recent transaction is always first
    rows.sort((a, b) => {
        const dateA = parseRevolutDate(a.completedDate || a.startedDate);
        const dateB = parseRevolutDate(b.completedDate || b.startedDate);
        return dateB - dateA;
    });

    return rows;
}

async function getRevolutData(customCsvText) {
    if (customCsvText) {
        return parseRevolutCsv(customCsvText);
    }

    // 1. Try fetching from Supabase Storage (cloud persistent source)
    try {
        const { data: downData, error } = await supabase.storage
            .from('medals')
            .download('finance/revolut_statement.csv');

        if (downData && !error) {
            const text = await downData.text();
            if (text && text.length > 20) {
                return parseRevolutCsv(text);
            }
        }
    } catch (err) {
        console.warn('Supabase storage download skipped/failed:', err.message);
    }

    // 2. Fallback to local files
    const candidates = [
        path.join(__dirname, '..', 'revolut_statement.csv'),
        path.join(__dirname, 'revolut_statement.csv'),
        path.join(process.cwd(), 'landing_predikalo1', 'revolut_statement.csv'),
        path.join(process.cwd(), 'revolut_statement.csv'),
    ];
    for (const p of candidates) {
        if (fs.existsSync(p)) {
            try {
                const content = fs.readFileSync(p, 'utf8');
                return parseRevolutCsv(content);
            } catch (e) {
                console.error('Error parsing local Revolut CSV:', e);
            }
        }
    }
    return [];
}

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'GET' && req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const admin_secret = req.body?.admin_secret || req.query?.secret || req.query?.admin_secret;
    const type = req.body?.type || req.query?.type;
    const csv_content = req.body?.csv_content;

    // Validate admin secret
    if (!admin_secret || admin_secret !== process.env.ADMIN_SECRET) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    try {
        // Upload / Update Revolut statement CSV
        if (type === 'upload_revolut' && csv_content) {
            // 1. Upload to Supabase Storage (cloud persistent storage safe for Vercel Serverless)
            try {
                const { error: upErr } = await supabase.storage
                    .from('medals')
                    .upload('finance/revolut_statement.csv', Buffer.from(csv_content, 'utf8'), {
                        upsert: true,
                        contentType: 'text/csv'
                    });
                if (upErr) console.warn('Supabase storage upload error:', upErr);
            } catch (storageErr) {
                console.warn('Storage upload error:', storageErr);
            }

            // 2. Safe local file write attempt (ignored on read-only environments like Vercel)
            try {
                const savePath = path.join(__dirname, '..', 'revolut_statement.csv');
                fs.writeFileSync(savePath, csv_content, 'utf8');
            } catch (fsErr) {
                // EROFS is expected on Vercel Lambda, ignore safely
            }

            const revolutRows = parseRevolutCsv(csv_content);
            return res.status(200).json({ success: true, count: revolutRows.length });
        }

        // Finance & Cash Flow Data
        if (type === 'finance') {
            // Live Stripe Balance
            let stripeBalance = { available: [{ amount: 0, currency: 'huf' }], pending: [{ amount: 0, currency: 'huf' }] };
            let stripeTransactions = [];
            let stripePayouts = [];

            try {
                stripeBalance = await stripe.balance.retrieve();
                const txList = await stripe.balanceTransactions.list({ limit: 100 });
                stripeTransactions = txList.data.map(t => ({
                    id: t.id,
                    created: t.created * 1000,
                    type: t.type,
                    amount: t.amount / 100,
                    fee: t.fee / 100,
                    net: t.net / 100,
                    currency: t.currency.toUpperCase(),
                    status: t.status,
                    description: t.description
                }));
                const pList = await stripe.payouts.list({ limit: 50 });
                stripePayouts = pList.data.map(p => ({
                    id: p.id,
                    created: p.created * 1000,
                    arrival_date: p.arrival_date * 1000,
                    amount: p.amount / 100,
                    currency: p.currency.toUpperCase(),
                    status: p.status,
                    method: p.method,
                    description: p.description
                }));
            } catch (sErr) {
                console.error('Stripe API error:', sErr);
            }

            // Revolut Pro Data
            const revolutRows = await getRevolutData();
            const latestBalance = revolutRows.length > 0 ? (revolutRows[0].balance || 0) : 0;

            return res.status(200).json({
                success: true,
                stripe: {
                    balance: stripeBalance,
                    transactions: stripeTransactions,
                    payouts: stripePayouts
                },
                revolut: {
                    currentBalance: latestBalance,
                    transactions: revolutRows
                }
            });
        }

        // Marketing Analytics Data
        if (type === 'marketing') {
            const creativeRows = getCreativeCsvData();
            const { data: dbMetrics, error: mErr } = await supabase
                .from('meta_daily_metrics')
                .select('*')
                .order('date', { ascending: false });

            if (mErr) console.error('Error fetching meta metrics:', mErr);

            const { data: orders, error: oErr } = await supabase
                .from('orders')
                .select('*')
                .eq('stripe_payment_status', 'paid')
                .order('created_at', { ascending: false });

            if (oErr) console.error('Error fetching orders:', oErr);

            const mergedMetrics = creativeRows.length > 0 ? creativeRows : (dbMetrics || []);
            const lastUpdated = mergedMetrics.length > 0 ? mergedMetrics[0].date : null;

            return res.status(200).json({
                success: true,
                metrics: mergedMetrics,
                orders: orders || [],
                lastUpdated
            });
        }

        // Standard Admin Data (Runs + Campaigns)
        const { data: runs, error: rErr } = await supabase
            .from('runs')
            .select('*, runners(name, email, phone, billing_name, billing_address), shipments(*)')
            .order('created_at', { ascending: false });

        if (rErr) throw rErr;

        let campaignsConfig = null;
        try {
            const configPath = path.join(__dirname, '..', 'config', 'campaigns.json');
            if (fs.existsSync(configPath)) {
                campaignsConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            }
        } catch (cErr) {
            console.warn('Could not read campaigns.json:', cErr);
        }

        return res.status(200).json({
            success: true,
            runs: runs || [],
            campaigns: campaignsConfig
        });

    } catch (err) {
        console.error('Admin data fetch error:', err);
        return res.status(500).json({ error: err.message });
    }
};
