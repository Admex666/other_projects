const Stripe = require('stripe');
const { google } = require('googleapis');

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

        const origin = req.headers.origin || 'https://vitasteps.vercel.app';
        const useTestKey = isTest || (req.headers.host && req.headers.host.includes('localhost'));
        const stripeKey = useTestKey
            ? (process.env.STRIPE_TEST_KEY || process.env.STRIPE_SECRET_KEY)
            : process.env.STRIPE_SECRET_KEY;
        const stripe = Stripe(stripeKey);

        // ── LIMIT CHECK ──────────────────────────────────────────────────────
        const serviceAccountJson = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON);
        const auth = new google.auth.GoogleAuth({
            credentials: {
                client_email: serviceAccountJson.client_email,
                private_key: serviceAccountJson.private_key
            },
            scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly']
        });
        const sheets = google.sheets({ version: 'v4', auth });
        const sheetId = process.env.GOOGLE_SHEET_ID;

        const sheetResponse = await sheets.spreadsheets.values.get({
            spreadsheetId: sheetId,
            range: `Nevezések!A2:AJ500`,
        });

        const rows = sheetResponse.data.values || [];
        let paidCount = 0;
        const isPilis = campaign === 'pilis';

        for (const row of rows) {
            if (row.length > 9) {
                const rowCampaign = (row[2] || '').toString().trim().toLowerCase();
                const rowPaid = (row[9] || '').toString().trim();
                if (rowPaid !== '') {
                    if (isPilis && rowCampaign.includes('pilis')) {
                        paidCount++;
                    } else if (!isPilis && !rowCampaign.includes('pilis')) {
                        paidCount++;
                    }
                }
            }
        }

        const maxLimit = isPilis ? 100 : 99;
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
        const productName = isPilis ? 'A Nagy-Kevély csillagjai Kihívás Érem' : 'Prédikálószék Kihívás Érem';
        const unitAmountCents = 799000; // HUF (Stripe no-decimal) for both campaigns
        const shippingAmountCents = 120000; // 1200 Ft
        const isHomeDelivery = deliveryMethod === 'home';

        const successUrl = isPilis ? `${origin}/nagykevely/siker.html` : `${origin}/sikeres-nevezes.html`;
        const cancelUrl = isPilis ? `${origin}/nagykevely/index.html` : `${origin}/`;

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
            Kampany: isPilis ? 'pilis' : 'predikaloszek',
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

        if (referredBy) {
            sessionOptions.discounts = [{ coupon: 'VSBARAT10' }];
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
