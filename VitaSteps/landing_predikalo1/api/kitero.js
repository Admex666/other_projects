const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

// 1x1 transparent GIF (43 bytes standard tracking pixel)
const TRANSPARENT_GIF = Buffer.from(
    'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',
    'base64'
);

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();

    // GET requests: verify-cid or track-open
    if (req.method === 'GET') {
        let action = req.query?.action;
        let cid = req.query?.cid;

        if (!action && req.url) {
            try {
                const parsedUrl = new URL(req.url, 'http://localhost');
                action = parsedUrl.searchParams.get('action');
                cid = parsedUrl.searchParams.get('cid');
            } catch (e) {}
        }

        // GET /api/kitero?action=track-open&cid=xyz
        if (action === 'track-open') {
            const cleanCid = (cid && typeof cid === 'string') ? cid.trim() : null;

            if (cleanCid) {
                try {
                    await supabase
                        .from('analytics_events')
                        .insert({
                            session_id: `email_open_${cleanCid}_${Date.now()}`,
                            visitor_id: `cid_${cleanCid}`,
                            event_name: 'email_open',
                            event_data: {
                                cid: cleanCid,
                                user_agent: req.headers['user-agent'] || null,
                                ip: req.headers['x-forwarded-for'] || req.socket?.remoteAddress || null
                            },
                            created_at: new Date().toISOString()
                        });
                } catch (err) {
                    console.error('Kitérő open tracking error:', err);
                }
            }

            res.setHeader('Content-Type', 'image/gif');
            res.setHeader('Content-Length', TRANSPARENT_GIF.length);
            res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0');
            res.setHeader('Pragma', 'no-cache');
            res.setHeader('Expires', '0');
            return res.status(200).end(TRANSPARENT_GIF);
        }

        // GET /api/kitero?action=verify-cid&cid=xyz
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

        // GET /api/kitero?action=funnel-data
        if (action === 'funnel-data' || action === 'funnel-stats') {
            const { getKiteroFunnelData } = require('../lib/admin/kitero-funnel');
            const funnelData = await getKiteroFunnelData();
            return res.status(200).json(funnelData);
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
        const cleanCid = (cid && typeof cid === 'string') ? cid.trim() : null;

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
            source: cleanCid ? `email_cid_${cleanCid}` : 'kitero_landing',
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
        const effectiveVisitorId = visitor_id || (cleanCid ? `cid_${cleanCid}` : `v_${Date.now()}`);
        const effectiveSessionId = session_id || `s_kitero_${Date.now()}`;

        await supabase
            .from('analytics_events')
            .insert({
                session_id: effectiveSessionId,
                visitor_id: effectiveVisitorId,
                event_name: 'lead_submit',
                event_data: {
                    cid: cleanCid,
                    price_variant: price_variant || '3490',
                    hero_variant: hero_variant || 'A',
                    cta_variant: cta_variant || 'A',
                    feedback: feedback || null
                },
                created_at: new Date().toISOString()
            });

        // Update session flags if session_id was provided
        if (session_id) {
            await supabase
                .from('analytics_sessions')
                .update({
                    cta_clicked: true,
                    checkout_started: true,
                    lead_email: cleanEmail
                })
                .eq('session_id', session_id);
        }

        // 5. Send automated confirmation email
        try {
            const firstName = cleanName.split(/\s+/)[0] || 'Túrázó';
            await sendLeadConfirmationEmail(cleanEmail, firstName);
        } catch (mailErr) {
            console.error('Kitérő confirmation email error:', mailErr);
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

async function sendLeadConfirmationEmail(toEmail, firstName) {
    if (!process.env.SMTP_PASSWORD) {
        console.warn('SMTP_PASSWORD missing, skipping confirmation email');
        return;
    }

    const tplHtmlPath = path.resolve(__dirname, '../kitero/email_templates/lead_confirmation.html');
    const tplTxtPath = path.resolve(__dirname, '../kitero/email_templates/lead_confirmation.txt');

    let htmlBody = fs.existsSync(tplHtmlPath) ? fs.readFileSync(tplHtmlPath, 'utf8') : '';
    let txtBody = fs.existsSync(tplTxtPath) ? fs.readFileSync(tplTxtPath, 'utf8') : '';

    htmlBody = htmlBody.replace(/\{\{first_name\}\}/g, firstName);
    txtBody = txtBody.replace(/\{\{first_name\}\}/g, firstName);

    const transporter = nodemailer.createTransport({
        host: 'smtp.gmail.com',
        port: 465,
        secure: true,
        auth: {
            user: 'vitasteps.team@gmail.com',
            pass: process.env.SMTP_PASSWORD
        }
    });

    await transporter.sendMail({
        from: '"VitaSteps" <vitasteps.team@gmail.com>',
        to: toEmail,
        subject: 'Köszönjük az érdeklődésedet! – VitaSteps Kitérő',
        text: txtBody,
        html: htmlBody
    });
    console.log(`Confirmation email sent to ${toEmail}`);
}
