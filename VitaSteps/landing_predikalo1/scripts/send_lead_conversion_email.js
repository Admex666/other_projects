/**
 * send_lead_conversion_email.js
 *
 * Küldi a konverziós emlékeztető e-mailt a Kalandfüzetet letöltött,
 * de még nem vásárolt (warm lead) érdeklődőknek.
 *
 * Használat:
 *   node scripts/send_lead_conversion_email.js          <-- Dry Run (listázza a címzetteket és a behelyettesített szöveget)
 *   node scripts/send_lead_conversion_email.js --send   <-- Küldés (alapértelmezetten teszt módban admexgm@gmail.com-ra)
 */

const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');
const { extractFirstName } = require('./run_lead_nurture_sequence');

const DRY_RUN = !process.argv.includes('--send');
const SAFE_TEST_EMAIL = 'admexgm@gmail.com';
const CUTOFF_DATE = new Date('2026-10-01T00:00:00Z');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

// Beállítások (Októberi kihívás zárása)
const DEADLINE_STR = '2026. október 31.';
const TARGET_DATE = new Date('2026-10-31T23:59:59+01:00');
const CHECKOUT_URL = 'https://vitastepsss.vercel.app/nagykevely/index.html#kihivas';

// Sablon betöltése
const templatePath = path.join(__dirname, '../email_templates/lead_conversion_reminder.html');
const templateHtml = fs.readFileSync(templatePath, 'utf8');

function getDaysRemaining() {
    const now = new Date();
    const diffTime = TARGET_DATE - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays <= 0) return 'utolsó órák';
    return `${diffDays} napod`;
}

// Nodemailer transport
const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 465,
    secure: true,
    auth: {
        user: 'vitasteps.team@gmail.com',
        pass: process.env.SMTP_PASSWORD,
    },
});

async function main() {
    console.log(`\n=== VitaSteps – Lead Konverziós Kampány Küldő ===`);
    console.log(`Mód: ${DRY_RUN ? '🔍 DRY RUN (nem küld e-maileket, csak listáz)' : '🔒 BIZTONSÁGI TESZT KÜLDÉS (admexgm@gmail.com)'}`);
    console.log(`Határidő: ${DEADLINE_STR} (Hátralévő idő: ${getDaysRemaining()})\n`);

    // 1. Összes lead lekérése
    const { data: leads, error: leadErr } = await supabase
        .from('leads')
        .select('*')
        .order('created_at', { ascending: true });

    if (leadErr) {
        console.error('Hiba a leadek lekérésekor:', leadErr);
        return;
    }

    // 2. Már vásárolt (konvertált) felhasználók lekérése kizáráshoz (runners + orders)
    const convertedEmailSet = new Set();
    const { data: runners, error: runErr } = await supabase
        .from('runners')
        .select('email, runs(id)');

    if (runErr) {
        console.error('Hiba a vásárlók lekérésekor:', runErr);
        return;
    }

    if (runners) {
        runners.forEach(r => {
            if (r.email && r.runs && r.runs.length > 0) {
                convertedEmailSet.add(r.email.toLowerCase().trim());
            }
        });
    }

    const { data: paidOrders } = await supabase
        .from('orders')
        .select('billing_email')
        .eq('is_test', false);

    if (paidOrders) {
        paidOrders.forEach(o => {
            if (o.billing_email) {
                convertedEmailSet.add(o.billing_email.toLowerCase().trim());
            }
        });
    }

    // 2b. Korábbi szeptemberi kampányban már megkeresett címzettek betöltése
    const legacySentSet = new Set();
    try {
        const localSentPath = path.join(__dirname, '../config/sent_leads_emails.json');
        if (fs.existsSync(localSentPath)) {
            const sentMap = JSON.parse(fs.readFileSync(localSentPath, 'utf8'));
            Object.values(sentMap || {}).forEach(arr => {
                if (Array.isArray(arr)) {
                    arr.forEach(e => {
                        if (e) legacySentSet.add(String(e).toLowerCase().trim());
                    });
                }
            });
        }
    } catch (e) {}

    // 3. Csoportosítás egyedi e-mail címek szerint (duplikáció és részleges leiratkozás kizárása)
    const byEmail = new Map();
    (leads || []).forEach(lead => {
        const cleanEmail = (lead.email || '').toLowerCase().trim();
        if (!cleanEmail || !cleanEmail.includes('@')) return;
        if (!byEmail.has(cleanEmail)) byEmail.set(cleanEmail, []);
        byEmail.get(cleanEmail).push(lead);
    });

    const targetRecipients = [];

    for (const [cleanEmail, rows] of byEmail.entries()) {
        // Kizárjuk, ha BÁRMELYIK sora leiratkozott
        const isUnsub = rows.some(r =>
            r.unsubscribed === true ||
            r.source === 'unsubscribed' ||
            (r.campaign && r.campaign.toLowerCase() === 'unsubscribed')
        );
        if (isUnsub) continue;

        // Kizárjuk, ha BÁRMELYIK sora konvertált vagy szerepel a runners/orders táblákban
        const isConv = rows.some(r => r.converted === true) || convertedEmailSet.has(cleanEmail);
        if (isConv) continue;

        // Kizárjuk a 2026-10-01 előtti vagy korábbi kampányban már megkeresett leadeket
        const earliestCreatedAt = new Date(rows[0].created_at);
        if (earliestCreatedAt < CUTOFF_DATE || legacySentSet.has(cleanEmail)) continue;

        let bestRawName = '';
        for (const r of rows) {
            const n = (r.name || '').trim();
            if (n && !n.includes('@') && !/\d/.test(n)) {
                bestRawName = n;
                break;
            }
        }
        const firstName = extractFirstName(bestRawName || rows[0].name);
        const latestRow = rows[rows.length - 1];

        targetRecipients.push({
            id: latestRow.id,
            email: cleanEmail,
            name: firstName,
            createdAt: rows[0].created_at
        });
    }

    console.log(`Megcélzott aktív meleg érdeklődők száma: ${targetRecipients.length} fő\n`);

    const daysLeft = getDaysRemaining();

    for (let i = 0; i < targetRecipients.length; i++) {
        const recipient = targetRecipients[i];
        const unsubUrl = `https://vitastepsss.vercel.app/api/unsubscribe?lead=${encodeURIComponent(recipient.id)}`;
        const checkoutWithLeadUrl = `https://vitastepsss.vercel.app/nagykevely/index.html?lead=${encodeURIComponent(recipient.id)}&source=email&email_id=lead_conversion_reminder#kihivas`;
        const personalizedHtml = templateHtml
            .replace(/\{\{NAME\}\}/g, recipient.name)
            .replace(/\{\{DAYS_LEFT\}\}/g, daysLeft)
            .replace(/\{\{DEADLINE\}\}/g, DEADLINE_STR)
            .replace(/\{\{CHECKOUT_URL\}\}/g, checkoutWithLeadUrl)
            .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl);

        const subject = `🏅 ${recipient.name}, az érmed megszerzésére még ${daysLeft} van! – VitaSteps`;

        if (DRY_RUN) {
            console.log(`[DRY RUN ${i + 1}/${targetRecipients.length}] Címzett: ${recipient.name} <${recipient.email}> | Tárgy: ${subject}`);
        } else {
            try {
                console.log(`[BIZTONSÁGI TESZT] Küldés (${i + 1}/${targetRecipients.length}): ${recipient.name} <${recipient.email}> -> ${SAFE_TEST_EMAIL}...`);
                await transporter.sendMail({
                    from: '"VitaSteps Teszt" <vitasteps.team@gmail.com>',
                    to: SAFE_TEST_EMAIL,
                    subject: `[TESZT - Eredeti: ${recipient.email}] ${subject}`,
                    html: personalizedHtml,
                });
                console.log(` -> SIKERESEN ELKÜLDVE (${SAFE_TEST_EMAIL}).`);
                await new Promise(r => setTimeout(r, 1000));
            } catch (err) {
                console.error(` -> HIBA a küldés során (${recipient.email}):`, err.message);
            }
        }
    }

    console.log(`\nKész! Összesen ${targetRecipients.length} érdeklődő feldolgozva.`);
}

if (require.main === module) {
    main().catch(console.error);
}
