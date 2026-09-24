/**
 * send_lead_conversion_email.js
 *
 * Küldi a konverziós emlékeztető e-mailt a Kalandkönyvet letöltött,
 * de még nem vásárolt (warm lead) érdeklődőknek.
 *
 * Használat:
 *   node scripts/send_lead_conversion_email.js          <-- Dry Run (listázza a címzetteket és a behelyettesített szöveget)
 *   node scripts/send_lead_conversion_email.js --send   <-- Éles küldés
 */

const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');

const DRY_RUN = !process.argv.includes('--send');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

// Beállítások
const DEADLINE_STR = '2026. szeptember 27.';
const TARGET_DATE = new Date('2026-09-27T23:59:59+02:00');
const CHECKOUT_URL = 'https://vitasteps.vercel.app/checkout.html?c=pilis';

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
    console.log(`Mód: ${DRY_RUN ? '🔍 DRY RUN (nem küld e-maileket, csak listáz)' : '🚀 ÉLES KÜLDÉS'}`);
    console.log(`Határidő: ${DEADLINE_STR} (Hátralévő idő: ${getDaysRemaining()})\n`);

    // 1. Összes lead lekérése
    const { data: leads, error: leadErr } = await supabase
        .from('leads')
        .select('*')
        .order('created_at', { ascending: false });

    if (leadErr) {
        console.error('Hiba a leadek lekérésekor:', leadErr);
        return;
    }

    // 2. Már vásárolt (konvertált) felhasználók lekérése kizáráshoz
    const { data: runners, error: runErr } = await supabase
        .from('runners')
        .select('email, runs(id)');

    if (runErr) {
        console.error('Hiba a vásárlók lekérésekor:', runErr);
        return;
    }

    const convertedEmailSet = new Set();
    if (runners) {
        runners.forEach(r => {
            if (r.email && r.runs && r.runs.length > 0) {
                convertedEmailSet.add(r.email.toLowerCase().trim());
            }
        });
    }

    // 3. Egyedi, még nem vásárolt és nem leiratkozott címzettek szűrése
    const recipientsMap = new Map();

    leads.forEach(lead => {
        const cleanEmail = (lead.email || '').toLowerCase().trim();
        if (!cleanEmail || !cleanEmail.includes('@')) return;

        // Kizárjuk a leiratkozottakat
        if (lead.unsubscribed === true || lead.source === 'unsubscribed' || (lead.campaign && lead.campaign.toLowerCase() === 'unsubscribed')) {
            return;
        }

        // Kizárjuk a már vásároltakat
        if (convertedEmailSet.has(cleanEmail)) return;

        if (!recipientsMap.has(cleanEmail)) {
            recipientsMap.set(cleanEmail, {
                email: cleanEmail,
                name: (lead.name && lead.name.trim().length > 0) ? lead.name.trim() : 'Túrázó',
                createdAt: lead.created_at
            });
        }
    });

    const targetRecipients = Array.from(recipientsMap.values());
    console.log(`Megcélzott meleg érdeklődők száma: ${targetRecipients.length} fő\n`);

    const daysLeft = getDaysRemaining();

    for (let i = 0; i < targetRecipients.length; i++) {
        const recipient = targetRecipients[i];
        const unsubUrl = `https://vitasteps.vercel.app/api/unsubscribe?email=${encodeURIComponent(recipient.email)}`;
        const personalizedHtml = templateHtml
            .replace(/\{\{NAME\}\}/g, recipient.name)
            .replace(/\{\{DAYS_LEFT\}\}/g, daysLeft)
            .replace(/\{\{DEADLINE\}\}/g, DEADLINE_STR)
            .replace(/\{\{CHECKOUT_URL\}\}/g, CHECKOUT_URL)
            .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl);

        const subject = `🏅 ${recipient.name}, az érmed megszerzésére még ${daysLeft} van! – VitaSteps`;

        if (DRY_RUN) {
            console.log(`[DRY RUN ${i + 1}/${targetRecipients.length}] Címzett: ${recipient.name} <${recipient.email}> | Tárgy: ${subject}`);
        } else {
            try {
                console.log(`Küldés folyamatban (${i + 1}/${targetRecipients.length}): ${recipient.name} <${recipient.email}>...`);
                await transporter.sendMail({
                    from: '"VitaSteps" <vitasteps.team@gmail.com>',
                    to: recipient.email,
                    subject: subject,
                    html: personalizedHtml,
                });
                console.log(` -> SIKERESEN ELKÜLDVE.`);
                // 1 mp szünet rate limit elkerülésére
                await new Promise(r => setTimeout(r, 1000));
            } catch (err) {
                console.error(` -> HIBA a küldés során (${recipient.email}):`, err.message);
            }
        }
    }

    console.log(`\nKész! Összesen ${targetRecipients.length} érdeklődő feldolgozva.`);
}

main().catch(console.error);
