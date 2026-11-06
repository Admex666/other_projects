const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();

    // GET /api/kitero?action=verify-cid&cid=xyz
    if (req.method === 'GET') {
        const { action, cid } = req.query || {};
        if (action === 'verify-cid') {
            if (!cid || typeof cid !== 'string') {
                return res.status(400).json({ valid: false, error: 'Hiányzó kampányazonosító.' });
            }

            try {
                // Find matching recipient session or lead metadata
                const { data: eventMatch } = await supabase
                    .from('analytics_events')
                    .select('visitor_id, session_id, event_data, created_at')
                    .eq('event_name', 'email_click')
                    .filter('event_data->>cid', 'eq', cid)
                    .order('created_at', { ascending: false })
                    .limit(1);

                return res.status(200).json({
                    valid: true,
                    cid: cid,
                    found: !!(eventMatch && eventMatch.length > 0)
                });
            } catch (err) {
                return res.status(200).json({ valid: true, cid: cid });
            }
        }
        return res.status(400).json({ error: 'Érvénytelen GET művelet.' });
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    // POST /api/kitero: Handle Early Access / Waitlist Lead Submission
    try {
        const {
            name,
            email,
            cid,
            price_variant,
            hero_variant,
            cta_variant,
            visitor_id,
            session_id,
            feedback
        } = req.body || {};

        if (!email || typeof email !== 'string' || !email.includes('@')) {
            return res.status(400).json({ error: 'Kérjük adj meg egy érvényes e-mail címet!' });
        }

        const cleanEmail = email.trim().toLowerCase();
        const rawName = (name && typeof name === 'string' && name.trim().length > 0) ? name.trim() : 'Érdeklődő';
        const cleanName = (rawName.includes('@') || /^\+?\d[\d\s\-]{5,}$/.test(rawName)) ? 'Érdeklődő' : rawName;

        // 1. Check if user already converted in core VitaSteps
        let isConverted = false;
        try {
            const { data: existingRunner } = await supabase
                .from('runners')
                .select('id, runs(id)')
                .ilike('email', cleanEmail)
                .maybeSingle();

            if (existingRunner && existingRunner.runs && existingRunner.runs.length > 0) {
                isConverted = true;
            }
        } catch (e) {}

        // 2. Upsert runner for identity stitching
        await supabase
            .from('runners')
            .upsert(
                { email: cleanEmail, name: cleanName },
                { onConflict: 'email', ignoreDuplicates: false }
            );

        // 3. Insert or update lead in 'leads' table
        const leadPayload = {
            email: cleanEmail,
            name: cleanName,
            campaign: 'kitero_val_1',
            source: cid ? `email_cid_${cid}` : 'kitero_landing',
            converted: isConverted,
            converted_at: isConverted ? new Date().toISOString() : null,
            created_at: new Date().toISOString()
        };

        const { data: insertedLead } = await supabase
            .from('leads')
            .insert(leadPayload)
            .select('id')
            .maybeSingle();

        // 4. Log conversion event to analytics_events
        if (session_id && visitor_id) {
            await supabase
                .from('analytics_events')
                .insert({
                    session_id,
                    visitor_id,
                    event_name: 'lead_submit',
                    event_data: {
                        cid: cid || null,
                        price_variant: price_variant || '3490',
                        hero_variant: hero_variant || 'A',
                        cta_variant: cta_variant || 'A',
                        feedback: feedback || null
                    },
                    created_at: new Date().toISOString()
                });

            // Update session flags
            await supabase
                .from('analytics_sessions')
                .update({
                    cta_clicked: true,
                    checkout_started: true,
                    lead_email: cleanEmail
                })
                .eq('session_id', session_id);
        }

        return res.status(200).json({
            success: true,
            message: 'Köszönjük! Sikeresen rögzítettük az érdeklődésedet a VitaSteps Kitérőre.'
        });

    } catch (err) {
        console.error('Kitérő API error:', err);
        return res.status(500).json({ error: 'Szerverhiba az adatok mentésekor. Kérjük próbáld újra!' });
    }
};
