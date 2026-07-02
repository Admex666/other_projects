const Stripe = require('stripe');
const { google } = require('googleapis');

const stripe = Stripe(process.env.STRIPE_SECRET_KEY);

module.exports = async (req, res) => {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        console.log('Received payload:', req.body);
        const { name, billingAddress, address, distance, email, parcelCarrier, parcelName, parcelAddress, parcelId, phone, referredBy } = req.body;
        const origin = req.headers.origin || 'https://vitasteps.vercel.app'; // fallback

        // Check checkout limit (max 99 paid purchases) before proceeding
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
        const sheetName = 'Nevezések';

        const sheetResponse = await sheets.spreadsheets.values.get({
            spreadsheetId: sheetId,
            range: `${sheetName}!J2:J500`,
        });

        const rows = sheetResponse.data.values || [];
        let paidCount = 0;
        for (const row of rows) {
            if (row && row.length > 0 && row[0] && row[0].trim() !== '') {
                paidCount++;
            }
        }

        if (paidCount >= 99) {
            return res.status(400).json({ error: 'Sajnos minden érem elfogyott, a nevezés lezárult!' });
        }

        const sessionOptions = {
            payment_method_types: ['card'],
            billing_address_collection: 'auto',
            line_items: [
                {
                    price_data: {
                        currency: 'huf',
                        product_data: {
                            name: 'Prédikálószék Kihívás Érem',
                            description: `Választott táv: ${distance}`,
                        },
                        unit_amount: 799000, // Stripe treats HUF as a 2-decimal currency (fillér), so we need to add 00
                    },
                    quantity: 1,
                },
            ],
            mode: 'payment',
            success_url: `${origin}/sikeres-nevezes.html`,
            cancel_url: `${origin}/`,
            payment_intent_data: {
                metadata: {
                    Név: name,
                    Email: email || '',
                    Telefon: phone || '',
                    Táv: distance,
                    Futár: parcelCarrier || '',
                    Csomagpont_neve: parcelName || address || '',
                    Csomagpont_cím: parcelAddress || '',
                    Csomagpont_id: parcelId || '',
                    Számlázási_cím: billingAddress || '',
                    Ajánló_Email: referredBy || ''
                }
            },
            metadata: {
                Név: name,
                Email: email || '',
                Telefon: phone || '',
                Táv: distance,
                Futár: parcelCarrier || '',
                Csomagpont_neve: parcelName || address || '',
                Csomagpont_cím: parcelAddress || '',
                Csomagpont_id: parcelId || '',
                Számlázási_cím: billingAddress || '',
                Ajánló_Email: referredBy || ''
            }
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
