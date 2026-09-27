const { processAnalyticsEvent } = require('../lib/analytics');

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        let payload = req.body;
        // In case payload was sent via sendBeacon as text/plain or string
        if (typeof payload === 'string') {
            try {
                payload = JSON.parse(payload);
            } catch (e) {
                // invalid json
            }
        }

        if (!payload || typeof payload !== 'object') {
            return res.status(400).json({ error: 'Invalid payload' });
        }

        const result = await processAnalyticsEvent(payload);
        return res.status(200).json(result);

    } catch (err) {
        console.error('Track API error:', err);
        return res.status(500).json({ error: err.message });
    }
};
