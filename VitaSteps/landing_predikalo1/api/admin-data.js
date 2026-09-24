const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');
const { handleApproveActions } = require('../lib/admin/approve');
const { handleFoxpostCreation } = require('../lib/admin/foxpost');
const { handleGetLeadsData, handleSendLeadsEmail } = require('../lib/admin/leads-email');
const { handleFinanceData, handleRevolutUpload, getCreativeCsvData } = require('../lib/admin/finance');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

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
    const action = req.body?.action || req.query?.action;

    // Validate admin secret
    if (!admin_secret || admin_secret !== process.env.ADMIN_SECRET) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    try {
        // ── 1. LEADS EMAIL ACTIONS ───────────────────────────────────────────
        if (type === 'leads_email' || action === 'leads_email') {
            if (req.method === 'GET') {
                return await handleGetLeadsData(req, res);
            }
            if (req.method === 'POST') {
                return await handleSendLeadsEmail(req, res);
            }
        }

        // ── 2. REVOLUT CSV UPLOAD ────────────────────────────────────────────
        if (type === 'upload_revolut' || action === 'upload_revolut') {
            return await handleRevolutUpload(req, res);
        }

        // ── 3. FINANCE DATA ──────────────────────────────────────────────────
        if (type === 'finance') {
            return await handleFinanceData(req, res);
        }

        // ── 4. FEEDBACKS DATA ────────────────────────────────────────────────
        if (type === 'feedbacks') {
            const { data: feedbacks, error: fErr } = await supabase
                .from('feedbacks')
                .select('*, runs(id, name, serial_number, campaign, shipped, created_at, runners(name, email, phone))')
                .order('created_at', { ascending: false });

            if (fErr) throw fErr;

            return res.status(200).json({
                success: true,
                feedbacks: feedbacks || []
            });
        }

        // ── 5. MARKETING DATA ────────────────────────────────────────────────
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

        // ── 6. FOXPOST PARCEL CREATION (POST) ────────────────────────────────
        if (action === 'foxpost_create' || action === 'create_foxpost') {
            return await handleFoxpostCreation(req, res);
        }

        // ── 7. RUN APPROVAL / REJECTION / SHIPPING ACTIONS (POST) ─────────────
        if (action && ['approve', 'reject', 'ship', 'update_shipment', 'ping'].includes(action)) {
            return await handleApproveActions(req, res);
        }

        // ── 8. DEFAULT: RUNS LIST & CAMPAIGNS CONFIG (GET) ───────────────────
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
        console.error('Admin API error:', err);
        return res.status(500).json({ error: err.message });
    }
};
