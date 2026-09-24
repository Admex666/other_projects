const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

function renderUnsubscribePage(email, success = true, errorMsg = '') {
    return `<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Leiratkozás – VitaSteps</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --surface: #121824;
            --border: rgba(255, 255, 255, 0.08);
            --lime: #c4ff00;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            background-color: var(--bg);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            max-width: 520px;
            width: 100%;
            padding: 40px 32px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            position: relative;
            overflow: hidden;
        }
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #38bdf8 0%, #c4ff00 100%);
        }
        .icon-circle {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background: rgba(196, 255, 0, 0.1);
            border: 1px solid rgba(196, 255, 0, 0.25);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            margin: 0 auto 20px;
        }
        h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 24px;
            font-weight: 800;
            margin-bottom: 12px;
            color: #fff;
        }
        p {
            font-size: 15px;
            color: var(--text-muted);
            line-height: 1.6;
            margin-bottom: 20px;
        }
        .email-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            color: #38bdf8;
            font-family: monospace;
            font-size: 14px;
            padding: 6px 14px;
            border-radius: 6px;
            margin-bottom: 24px;
            word-break: break-all;
        }
        .btn {
            display: inline-block;
            background: var(--lime);
            color: #000;
            font-weight: 800;
            text-decoration: none;
            padding: 14px 28px;
            border-radius: 8px;
            font-size: 15px;
            transition: all 0.2s ease;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(196, 255, 0, 0.3);
        }
        .footer-brand {
            margin-top: 30px;
            font-size: 12px;
            color: #64748b;
        }
    </style>
</head>
<body>
    <div class="card">
        ${success ? `
            <div class="icon-circle">✅</div>
            <h1>Sikeres leiratkozás</h1>
            <p>Sikeresen leiratkoztál a VitaSteps hírleveleiről és emlékeztető e-mailjeiről.</p>
            ${email ? `<div class="email-badge">${email}</div>` : ''}
            <p style="font-size: 14px;">A jövőben nem fogsz több promóciós vagy motivációs megkeresést kapni tőlünk erre a címre.</p>
            <div style="margin-top: 24px;">
                <a href="https://vitasteps.vercel.app" class="btn">Vissza a VitaSteps főoldalra</a>
            </div>
        ` : `
            <div class="icon-circle" style="background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.3);">❌</div>
            <h1>Hiba történt</h1>
            <p>${errorMsg || 'Nem sikerült feldolgozni a leiratkozási kérést.'}</p>
            <div style="margin-top: 24px;">
                <a href="https://vitasteps.vercel.app" class="btn">Vissza a főoldalra</a>
            </div>
        `}
        <div class="footer-brand">© 2026 VitaSteps – Természetjáró Kihívások</div>
    </div>
</body>
</html>`;
}

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();

    const email = (req.query.email || (req.body && req.body.email) || '').trim().toLowerCase();

    if (!email || !email.includes('@')) {
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        return res.status(400).send(renderUnsubscribePage('', false, 'Hiányzó vagy érvénytelen e-mail cím.'));
    }

    try {
        // 1. Megpróbáljuk beállítani az 'unsubscribed = true' értéket
        let updateResult = await supabase
            .from('leads')
            .update({ unsubscribed: true, source: 'unsubscribed' })
            .eq('email', email);

        // 2. Ha az 'unsubscribed' oszlop még nem létezne a séma gyorsítótárban, frissítjük a 'source'-t
        if (updateResult.error && updateResult.error.message && updateResult.error.message.includes('column')) {
            console.warn('Fallback to source=unsubscribed for:', email);
            updateResult = await supabase
                .from('leads')
                .update({ source: 'unsubscribed' })
                .eq('email', email);
        }

        if (updateResult.error) {
            console.error('Supabase unsubscribe update error:', updateResult.error);
        }

        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        return res.status(200).send(renderUnsubscribePage(email, true));

    } catch (err) {
        console.error('Unsubscribe handler error:', err);
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        return res.status(500).send(renderUnsubscribePage(email, false, 'Szerverhiba történt a kérés feldolgozása közben.'));
    }
};
