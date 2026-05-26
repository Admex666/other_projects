const Stripe = require('stripe');

const stripe = Stripe(process.env.STRIPE_SECRET_KEY);

module.exports = async (req, res) => {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        const { name, address, distance } = req.body;
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
                        unit_amount: 7990, // HUF is zero-decimal currency in Stripe
                    },
                    quantity: 1,
                },
            ],
            mode: 'payment',
            success_url: `${origin}/sikeres-nevezes.html`,
            cancel_url: `${origin}/`,
            metadata: {
                Név: name,
                Cím: address,
                Táv: distance
            }
        });

        res.status(200).json({ url: session.url });
    } catch (err) {
        console.error('Stripe API error:', err);
        res.status(500).json({ error: err.message });
    }
};
