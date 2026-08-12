const { createClient } = require('@supabase/supabase-js');
const campaigns = require('../config/campaigns.json');

module.exports = async (req, res) => {
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        const email = (req.query.email || '').trim().toLowerCase();
        const qty = parseInt(req.query.qty || '1', 10);
        const referredBy = (req.query.referredBy || '').trim().toLowerCase();
        const campaignKey = (req.query.campaign === 'predikaloszek' || req.query.campaign === 'predikalo') ? 'predikaloszek' : 'pilis';
        const config = campaigns[campaignKey] || campaigns['pilis'];
        const price = config.price || 7990;

        let totalReferrals = 0;
        let pastRedeemed = 0;

        if (email) {
            const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
            
            // 1. Total referred friends in runs
            const { count: refCount } = await supabase
                .from('runs')
                .select('*', { count: 'exact', head: true })
                .eq('referred_by', email)
                .eq('is_test', false);
            totalReferrals = refCount || 0;

            // 2. Referrals already redeemed in past paid orders
            const { data: pastOrders } = await supabase
                .from('orders')
                .select('referrals_redeemed')
                .eq('billing_email', email)
                .eq('stripe_payment_status', 'paid')
                .eq('is_test', false);

            if (pastOrders) {
                pastRedeemed = pastOrders.reduce((sum, o) => sum + (o.referrals_redeemed || 0), 0);
            }
        }

        const unusedReferrals = Math.max(0, totalReferrals - pastRedeemed);
        const additionalMedals = Math.max(0, qty - 1);
        const effectiveReferrals = unusedReferrals + additionalMedals;

        let discountPercent = 0;
        let redeemedThisOrder = 0;

        if (effectiveReferrals >= 5) { discountPercent = 100; redeemedThisOrder = Math.min(5, unusedReferrals + additionalMedals); }
        else if (effectiveReferrals === 4) { discountPercent = 70; redeemedThisOrder = Math.min(4, unusedReferrals + additionalMedals); }
        else if (effectiveReferrals === 3) { discountPercent = 45; redeemedThisOrder = Math.min(3, unusedReferrals + additionalMedals); }
        else if (effectiveReferrals === 2) { discountPercent = 25; redeemedThisOrder = Math.min(2, unusedReferrals + additionalMedals); }
        else if (effectiveReferrals === 1) { discountPercent = 10; redeemedThisOrder = Math.min(1, unusedReferrals + additionalMedals); }
        else if (referredBy) { discountPercent = 10; redeemedThisOrder = 0; }

        const firstMedalPrice = Math.round(price * (1 - discountPercent / 100));
        const otherMedalsPrice = additionalMedals * price;
        const totalMedalsPrice = firstMedalPrice + otherMedalsPrice;
        const totalSavings = (qty * price) - totalMedalsPrice;

        return res.status(200).json({
            totalReferrals,
            pastRedeemed,
            unusedReferrals,
            qty,
            additionalMedals,
            effectiveReferrals,
            discountPercent,
            redeemedThisOrder,
            firstMedalPrice,
            otherMedalsPrice,
            totalMedalsPrice,
            totalSavings,
            price
        });
    } catch (err) {
        console.error('Error checking referral discount:', err);
        return res.status(500).json({ error: err.message });
    }
};
