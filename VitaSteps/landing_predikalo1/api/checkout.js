const Stripe = require('stripe');
const { createClient } = require('@supabase/supabase-js');
const campaigns = require('../config/campaigns.json');

module.exports = async (req, res) => {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        console.log('Received payload:', JSON.stringify(req.body));
        const {
            medals,           // array: [{ name, distance }]
            email,
            phone,
            billingAddress,
            deliveryMethod,   // 'foxpost' | 'home'
            homeAddress,
            parcelCarrier,
            parcelName,
            parcelAddress,
            parcelId,
            referredBy,
            isTest,
            campaign
        } = req.body;

        // Validate medals array
        if (!medals || !Array.isArray(medals) || medals.length === 0) {
            return res.status(400).json({ error: 'Legalább egy nevező adatait meg kell adni!' });
        }

        // Default to pilis if not specified or invalid
        const campaignKey = (campaign === 'predikaloszek' || campaign === 'predikalo') ? 'predikaloszek' : 'pilis';
        const config = campaigns[campaignKey];

        const origin = req.headers.origin || 'https://vitasteps.vercel.app';
        const useTestKey = isTest || (req.headers.host && req.headers.host.includes('localhost'));
        
        // Block live registrations for Pilis campaign
        if (campaignKey === 'pilis' && !useTestKey) {
            return res.status(403).json({
                error: 'A Nagy-Kevély csillagai kihívás éles nevezése még nem indult el! Kérjük látogass vissza később.'
            });
        }

        if (useTestKey && !process.env.STRIPE_TEST_KEY) {
            return res.status(500).json({ error: 'A STRIPE_TEST_KEY nincs beállítva a szerveren. Kérjük jelezd a fejlesztőknek!' });
        }
        const stripeKey = useTestKey
            ? process.env.STRIPE_TEST_KEY
            : process.env.STRIPE_SECRET_KEY;
        const stripe = Stripe(stripeKey);

        const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

        // ── REFERRAL COUNT CHECK ─────────────────────────────────────────────
        let referralCount = 0;
        if (email) {
            const cleanEmail = email.trim().toLowerCase();
            const { count, error: countErr } = await supabase
                .from('runners')
                .select('*', { count: 'exact', head: true })
                .eq('referred_by', cleanEmail);
            
            if (countErr) {
                console.error('Error fetching referral count from Supabase:', countErr);
            } else {
                referralCount = count || 0;
                console.log(`Referral count for ${cleanEmail}: ${referralCount}`);
            }
        }

        // ── LIMIT CHECK ──────────────────────────────────────────────────────
        const { count: paidCount, error: fetchErr } = await supabase
            .from('runs')
            .select('id', { count: 'exact', head: true })
            .eq('is_test', useTestKey)
            .eq('campaign', campaignKey);

        if (fetchErr) {
            console.error('Supabase count error in limit check:', fetchErr);
            throw fetchErr;
        }

        const maxLimit = config.limit;
        if (paidCount + medals.length > maxLimit) {
            const remaining = maxLimit - paidCount;
            if (remaining <= 0) {
                return res.status(400).json({ error: 'Sajnos minden érem elfogyott, a nevezés lezárult!' });
            }
            return res.status(400).json({
                error: `Csak ${remaining} db érem maradt! Kérjük csökkentsd a mennyiséget.`
            });
        }

        // ── PRICING ──────────────────────────────────────────────────────────
        const productName = config.productName;
        const unitAmountCents = config.price * 100; // HUF (Stripe no-decimal)
        const shippingAmountCents = 120000; // 1200 Ft
        const isHomeDelivery = deliveryMethod === 'home';

        const successUrl = `${origin}/siker.html?c=${campaignKey}&session_id={CHECKOUT_SESSION_ID}`;
        const cancelUrl = campaignKey === 'predikaloszek'
            ? `${origin}/predikalo/index.html`
            : `${origin}/nagykevely/index.html`;

        // ── METADATA ─────────────────────────────────────────────────────────
        // Stripe metadata values must be strings, max 500 chars each
        const meta = {
            Email: email || '',
            Telefon: phone || '',
            Szamlazasi_cim: billingAddress || '',
            Szallitas: deliveryMethod || 'foxpost',
            Csomagpont_neve: parcelName || '',
            Csomagpont_cim: parcelAddress || '',
            Csomagpont_id: parcelId || '',
            Hazhoz_cim: homeAddress || '',
            Ajanlо_Email: referredBy || '',
            Kampany: campaignKey,
            IsTest: useTestKey ? 'true' : 'false',
            Medaliok: JSON.stringify(medals).substring(0, 490) // serialize array, max 490 chars
        };

        // ── STRIPE LINE ITEMS ─────────────────────────────────────────────────
        const lineItems = [
            {
                price_data: {
                    currency: 'huf',
                    product_data: {
                        name: productName,
                        description: medals.length === 1
                            ? `Nevező: ${medals[0].name} | Táv: ${medals[0].distance}`
                            : `${medals.length} db érem | Nevezők: ${medals.map(m => m.name).join(', ')}`,
                    },
                    unit_amount: unitAmountCents,
                },
                quantity: medals.length,
            }
        ];

        if (isHomeDelivery) {
            lineItems.push({
                price_data: {
                    currency: 'huf',
                    product_data: {
                        name: 'Házhozszállítás (Magyar Posta)',
                        description: `Szállítási cím: ${homeAddress || billingAddress}`,
                    },
                    unit_amount: shippingAmountCents,
                },
                quantity: 1,
            });
        }

        // ── SESSION ──────────────────────────────────────────────────────────
        const sessionOptions = {
            payment_method_types: ['card'],
            billing_address_collection: 'auto',
            line_items: lineItems,
            mode: 'payment',
            success_url: successUrl,
            cancel_url: cancelUrl,
            payment_intent_data: { metadata: meta },
            metadata: meta
        };

        // Determine correct discount coupon:
        // - Own referrals give tiered coupon: VS_AJANLO_10, VS_AJANLO_20, etc.
        // - Friend referral gives fallback: VSBARAT10 (10%)
        let appliedCoupon = null;
        if (referralCount > 0) {
            const discountPercent = Math.min(50, referralCount * 10);
            appliedCoupon = `VS_AJANLO_${discountPercent}`;
            
            // Ensure this coupon exists in Stripe programmatically
            try {
                await stripe.coupons.retrieve(appliedCoupon);
                console.log(`Stripe coupon verified: ${appliedCoupon}`);
            } catch (err) {
                if (err.statusCode === 404) {
                    console.log(`Creating missing Stripe coupon: ${appliedCoupon}`);
                    await stripe.coupons.create({
                        id: appliedCoupon,
                        percent_off: discountPercent,
                        duration: 'forever',
                        name: `${discountPercent}% Ajánlói Kedvezmény (VitaSteps)`,
                    });
                } else {
                    console.error('Error retrieving/creating Stripe coupon:', err);
                }
            }
        } else if (referredBy) {
            appliedCoupon = 'VSBARAT10';
            
            // Ensure fallback friend coupon exists in Stripe
            try {
                await stripe.coupons.retrieve(appliedCoupon);
            } catch (err) {
                if (err.statusCode === 404) {
                    console.log(`Creating missing fallback Stripe coupon: ${appliedCoupon}`);
                    await stripe.coupons.create({
                        id: appliedCoupon,
                        percent_off: 10,
                        duration: 'forever',
                        name: '10% Ajánlói Barát Kedvezmény (VitaSteps)',
                    });
                }
            }
        }

        if (appliedCoupon) {
            sessionOptions.discounts = [{ coupon: appliedCoupon }];
            console.log(`Checkout Session will apply coupon: ${appliedCoupon}`);
        } else {
            sessionOptions.allow_promotion_codes = true;
        }

        const session = await stripe.checkout.sessions.create(sessionOptions);
        res.status(200).json({ url: session.url });

    } catch (err) {
        console.error('Stripe API error:', err);
        res.status(500).json({ error: err.message });
    }
};
