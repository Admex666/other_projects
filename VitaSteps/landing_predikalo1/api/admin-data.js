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
                        roas: Number(r['ROAS'] || 0)
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

function getRevolutData() {
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
                const lines = content.trim().split('\n');
                if (lines.length < 2) continue;
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
                return rows;
            } catch (e) {
                console.error('Error parsing Revolut CSV:', e);
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
            const savePath = path.join(__dirname, '..', 'revolut_statement.csv');
            fs.writeFileSync(savePath, csv_content, 'utf8');
            const revolutRows = getRevolutData();
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
                    destination: p.destination
                }));
            } catch (stripeErr) {
                console.error('Stripe API error in finance fetch:', stripeErr.message);
            }

            // Revolut Statement Data
            const revolutRows = getRevolutData();
            const latestRevolutBalance = revolutRows.length > 0 ? revolutRows[revolutRows.length - 1].balance : 0;

            // Summary by category
            const revolutSummary = {};
            revolutRows.forEach(r => {
                revolutSummary[r.category] = (revolutSummary[r.category] || 0) + r.amount;
            });

            return res.status(200).json({
                stripe: {
                    balance: stripeBalance,
                    transactions: stripeTransactions,
                    payouts: stripePayouts
                },
                revolut: {
                    currentBalance: latestRevolutBalance,
                    transactions: revolutRows,
                    summaryByCategory: revolutSummary,
                    totalCount: revolutRows.length
                }
            });
        }

        if (type === 'marketing') {
            // Fetch targets
            const { data: targets, error: targetsErr } = await supabase
                .from('marketing_targets')
                .select('*');
            if (targetsErr) throw targetsErr;

            // Fetch paid real orders for customer cohort analysis and revenue calculation
            const { data: orders, error: ordersErr } = await supabase
                .from('orders')
                .select('id, runner_id, campaign, amount_total, created_at, stripe_payment_status, is_test')
                .eq('stripe_payment_status', 'paid')
                .eq('is_test', false)
                .order('created_at', { ascending: true });
            if (ordersErr) throw ordersErr;

            // Fetch meta daily metrics from Supabase
            const { data: metrics, error: metricsErr } = await supabase
                .from('meta_daily_metrics')
                .select('*')
                .order('date', { ascending: false })
                .limit(200);
            if (metricsErr) throw metricsErr;

            // Fetch creative level daily report from CSV
            const creativeRows = getCreativeCsvData();

            // Use creative rows if available, augmented with any metrics rows that have ad_name or fallback to metrics
            const combinedMetrics = creativeRows.length > 0 ? creativeRows : (metrics || []);

            return res.status(200).json({
                targets: targets || [],
                orders: orders || [],
                metrics: combinedMetrics,
                dbMetrics: metrics || []
            });
        }

        // Default: fetch all runs with runners and shipments
        const { data: runs, error: runsErr } = await supabase
            .from('runs')
            .select('*, runners(name, email, phone, billing_address), shipments(*)')
            .order('proof_submitted_at', { ascending: false, nullsFirst: false });
        if (runsErr) throw runsErr;

        return res.status(200).json({ runs: runs || [] });
    } catch (err) {
        console.error('Error in admin-data API:', err);
        return res.status(500).json({ error: err.message });
    }
};
