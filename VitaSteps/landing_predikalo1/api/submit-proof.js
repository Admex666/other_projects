const path = require('path');
const fs = require('fs');

// Attempt to load .env from multiple potential locations
const envCandidates = [
    path.resolve(__dirname, '../.env'),
    path.resolve(__dirname, '../../landing_predikalo1/.env'),
    path.resolve(process.cwd(), 'landing_predikalo1/.env'),
    path.resolve(process.cwd(), '.env')
];
for (const envPath of envCandidates) {
    if (fs.existsSync(envPath)) {
        require('dotenv').config({ path: envPath });
        break;
    }
}
require('dotenv').config();

const { createClient } = require('@supabase/supabase-js');

// Pushbullet Access Token with fallback
const DEFAULT_PUSHBULLET_TOKEN = 'o.AL09U6r5T6x65MzyOS2fSVrL4pUVzuOR';
const PUSHBULLET_TOKEN = process.env.PUSHBULLET_ACCESS_TOKEN || DEFAULT_PUSHBULLET_TOKEN;

// Initialize Supabase Client with Service Role
const supabaseUrl = process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co';
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

function sendPushbulletSafe(title, body) {
    const token = PUSHBULLET_TOKEN;
    if (!token) {
        console.log('[Pushbullet] No token configured, skipping.');
        return Promise.resolve(false);
    }

    return new Promise((resolve) => {
        try {
            const https = require('https');
            const payload = JSON.stringify({
                type: 'note',
                title: String(title || 'VitaSteps Értesítés').slice(0, 250),
                body: String(body || '').slice(0, 1500)
            });

            const req = https.request({
                hostname: 'api.pushbullet.com',
                path: '/v2/pushes',
                method: 'POST',
                timeout: 5000,
                headers: {
                    'Access-Token': token,
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(payload)
                }
            }, (res) => {
                let resData = '';
                res.on('data', chunk => resData += chunk);
                res.on('end', () => {
                    if (res.statusCode >= 200 && res.statusCode < 300) {
                        console.log('[Pushbullet] Notification sent successfully (HTTP ' + res.statusCode + ').');
                        resolve(true);
                    } else {
                        console.warn('[Pushbullet] Service returned HTTP ' + res.statusCode + ': ' + resData);
                        resolve(false);
                    }
                });
            });

            req.on('timeout', () => {
                console.warn('[Pushbullet] Request timed out after 5000ms. Aborting.');
                req.destroy();
                resolve(false);
            });

            req.on('error', (err) => {
                console.warn('[Pushbullet] Network error while sending push:', err.message);
                resolve(false);
            });

            req.write(payload);
            req.end();
        } catch (err) {
            console.warn('[Pushbullet] Unexpected exception in sendPushbulletSafe:', err.message);
            resolve(false);
        }
    });
}

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    // Authenticate user via authorization header if present
    const authHeader = req.headers.authorization;
    let userEmail = null;

    if (authHeader && authHeader.startsWith('Bearer ')) {
        const token = authHeader.split(' ')[1];
        try {
            const { data, error: authError } = await supabase.auth.getUser(token);
            if (!authError && data?.user) {
                userEmail = data.user.email?.toLowerCase();
            }
        } catch (err) {
            console.warn('Token verification warning:', err.message);
        }
    }

    try {
        const { run_id, run_ids, proof_urls, ship_together_with } = req.body;

        if (!run_id && (!run_ids || run_ids.length === 0)) {
            return res.status(400).json({ error: 'run_id vagy run_ids megadása kötelező.' });
        }

        const targetIds = Array.from(new Set([
            ...(run_id ? [run_id] : []),
            ...(Array.isArray(run_ids) ? run_ids : [])
        ]));

        if (!proof_urls || !Array.isArray(proof_urls) || proof_urls.length === 0) {
            return res.status(400).json({ error: 'Legalább egy igazolás URL szükséges.' });
        }

        console.log(`[submit-proof] Submitting proof for runs: ${targetIds.join(', ')} by user ${userEmail || 'unknown'}`);

        // Update runs using service role client
        const updatePayload = {
            proof_submitted: true,
            proof_urls: proof_urls,
            proof_submitted_at: new Date().toISOString(),
            ship_together_with: (ship_together_with && typeof ship_together_with === 'string') 
                ? ship_together_with.trim().toLowerCase() 
                : null
        };

        const { data, error: dbError } = await supabase
            .from('runs')
            .update(updatePayload)
            .in('id', targetIds)
            .select('id, serial_number, name, campaign, runners(name, email)');

        if (dbError) {
            console.error('[submit-proof] DB error:', dbError);
            throw new Error('Adatbázis hiba az igazolás rögzítésekor: ' + dbError.message);
        }

        console.log(`[submit-proof] Successfully updated ${data?.length || 0} run(s).`);

        // Send Pushbullet notification to admin (resilient, non-blocking)
        let pushSent = false;
        try {
            const firstRun = data && data[0] ? data[0] : {};
            const runnerName = firstRun.name || firstRun.runners?.name || 'Résztvevő';
            const email = firstRun.runners?.email || userEmail || '–';
            const serials = (data || []).map(r => r.serial_number).filter(Boolean).join(', ') || 'sorszám nélkül';
            const isPilis = firstRun.campaign === 'pilis' || (firstRun.serial_number || '').includes('-PK');
            const campaignName = isPilis ? 'A Nagy-Kevély csillagai' : 'Prédikálószék Vertical';
            const filesCount = proof_urls.length;

            const pbTitle = `📥 Új igazolás: ${runnerName} (${serials})`;
            const pbBody = `Futó: ${runnerName}\nKihívás: ${campaignName}\nSorszám: ${serials}\nCsatolt igazolások: ${filesCount} db fájl\nEmail: ${email}\n\nNyisd meg az admin felületet az ellenőrzéshez:\nhttps://vitastepsss.vercel.app/admin.html`;

            pushSent = await sendPushbulletSafe(pbTitle, pbBody);
        } catch (pushErr) {
            console.warn('[submit-proof] Pushbullet notification failed gracefully:', pushErr);
        }

        return res.status(200).json({
            success: true,
            message: 'Igazolás sikeresen elmentve!',
            pushbullet_sent: pushSent,
            updated_runs: data
        });

    } catch (err) {
        console.error('[submit-proof] Exception:', err);
        return res.status(500).json({ error: err.message || 'Belső szerverhiba' });
    }
};
