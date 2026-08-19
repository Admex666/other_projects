const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    const { admin_secret, type } = req.body;

    // Validate admin secret
    if (!admin_secret || admin_secret !== process.env.ADMIN_SECRET) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    try {
        if (type === 'marketing') {
            // Fetch targets
            const { data: targets, error: targetsErr } = await supabase
                .from('marketing_targets')
                .select('*');
            if (targetsErr) throw targetsErr;

            // Fetch paid real orders for customer cohort analysis
            const { data: orders, error: ordersErr } = await supabase
                .from('orders')
                .select('id, runner_id, campaign, created_at, stripe_payment_status, is_test')
                .eq('stripe_payment_status', 'paid')
                .eq('is_test', false)
                .order('created_at', { ascending: true });
            if (ordersErr) throw ordersErr;

            // Fetch meta daily metrics
            const { data: metrics, error: metricsErr } = await supabase
                .from('meta_daily_metrics')
                .select('*')
                .order('date', { ascending: false })
                .limit(200);
            if (metricsErr) throw metricsErr;

            return res.status(200).json({
                targets: targets || [],
                orders: orders || [],
                metrics: metrics || []
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
