const Stripe = require('stripe');

const stripe = Stripe(process.env.STRIPE_SECRET_KEY);

module.exports = async (req, res) => {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        console.log('Received payload:', req.body);
        const { name, billingAddress, address, distance, email, parcelCarrier, parcelName, parcelAddress, parcelId, phone } = req.body;
        const origin = req.headers.origin || 'https://vitasteps.vercel.app'; // fallback

        const session = await stripe.checkout.sessions.create({
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
                    Számlázási_cím: billingAddress || ''
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
                Számlázási_cím: billingAddress || ''
            }
        });

        res.status(200).json({ url: session.url });
    } catch (err) {
        console.error('Stripe API error:', err);
        res.status(500).json({ error: err.message });
    }
};
