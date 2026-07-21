const { createClient } = require('@supabase/supabase-js');

module.exports = async (req, res) => {
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate');

        const campaign = req.query.campaign || 'predikaloszek';
        const campaignKey = (campaign === 'predikaloszek' || campaign === 'predikalo') ? 'predikaloszek' : 'pilis';
        const isPilis = campaignKey === 'pilis';

        const useTestKey = req.query.is_test === 'true' || (req.headers.host && req.headers.host.includes('localhost'));

        const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
        
        // Count runs for this campaign from Supabase
        const { count: paidCount, error: fetchErr } = await supabase
            .from('runs')
            .select('id', { count: 'exact', head: true })
            .eq('is_test', useTestKey)
            .eq('campaign', campaignKey);

        if (fetchErr) {
            console.error('Supabase count error in check-limit:', fetchErr);
            throw fetchErr;
        }

        const limit = isPilis ? 100 : 99;
        const closed = (paidCount || 0) >= limit;

        return res.status(200).json({
            success: true,
            count: paidCount || 0,
            limit: limit,
            closed: closed
        });
    } catch (err) {
        console.error('Error checking checkout limit:', err);
        return res.status(500).json({ error: err.message });
    }
};
