/**
 * send_promo_referral.js
 *
 * Sends the Nagy-Kevély referral promo email to all Prédikálószék runners
 * whose medal has already been received (shipments.received = TRUE).
 *
 * Usage:
 *   node scripts/send_promo_referral.js           ← dry run (just lists recipients)
 *   node scripts/send_promo_referral.js --send    ← actually sends emails
 */

require('dotenv').config({ path: require('path').join(__dirname, '../.env') });

const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');

const DRY_RUN = !process.argv.includes('--send');

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

const PORTAL_BASE = 'https://vitasteps.vercel.app/portal.html';
const MARKETING_BASE = 'https://vitasteps.vercel.app/nagykevely/index.html';

// ── Load email template ───────────────────────────────────────────────────────
const templatePath = path.join(__dirname, '../email_promo_referral_template.html');
const templateHtml = fs.readFileSync(templatePath, 'utf8');

// ── Nodemailer transport ──────────────────────────────────────────────────────
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
    console.log(`\n=== VitaSteps – Promo Referral Email Script ===`);
    console.log(`Mode: ${DRY_RUN ? '🔍 DRY RUN (no emails sent)' : '🚀 LIVE SEND'}\n`);

    // ── 1. Query: received Prédikálószék runners ──────────────────────────────
    const { data: shipments, error } = await supabase
        .from('shipments')
        .select(`
            received,
            runs!inner (
                id,
                campaign,
                name,
                runners!inner (
                    email,
                    name
                )
            )
        `)
        .eq('received', true)
        .eq('runs.campaign', 'predikaloszek');

    if (error) {
        console.error('❌ Supabase query error:', error.message);
        process.exit(1);
    }

    if (!shipments || shipments.length === 0) {
        console.log('Nincs egyetlen átvett Prédikálószék csomag sem az adatbázisban.');
        return;
    }

    // Deduplicate by email (one email per runner, regardless of how many runs)
    const seen = new Set();
    const recipients = [];
    for (const s of shipments) {
        const runner = s.runs?.runners;
        const runName = s.runs?.name;
        if (!runner?.email || seen.has(runner.email)) continue;
        seen.add(runner.email);
        recipients.push({
            email: runner.email.trim().toLowerCase(),
            name: runName || runner.name || 'Kalandor',
        });
    }

    console.log(`📦 Átvett Prédikálószék csomagok összesen (shipments sorok): ${shipments.length}`);
    console.log(`👤 Egyedi emailcímek (deduplikált): ${recipients.length}\n`);

    console.log('--- Első 5 címzett (preview) ---');
    recipients.slice(0, 5).forEach((r, i) => {
        console.log(`  ${i + 1}. ${r.name} <${r.email}>`);
    });
    console.log('--------------------------------\n');

    if (DRY_RUN) {
        console.log('ℹ️  DRY RUN – emailek NEM lettek elküldve.');
        console.log('    Futtatsd --send flaggel az éles küldéshez:\n');
        console.log('    node scripts/send_promo_referral.js --send\n');
        return;
    }

    // ── 2. Send emails ────────────────────────────────────────────────────────
    console.log(`📧 Küldés indul (${recipients.length} email)...\n`);
    let sent = 0;
    let failed = 0;

    for (const r of recipients) {
        const referralLink = `${MARKETING_BASE}?ref=${encodeURIComponent(r.email)}`;
        const portalLink = PORTAL_BASE;

        const html = templateHtml
            .replace(/\{\{NAME\}\}/g, r.name)
            .replace(/\{\{REFERRAL_LINK\}\}/g, referralLink)
            .replace(/\{\{PORTAL_LINK\}\}/g, portalLink);

        try {
            await transporter.sendMail({
                from: '"VitaSteps" <vitasteps.team@gmail.com>',
                to: r.email,
                subject: '⛰️ Indul a Nagy-Kevély csillagai – a te ajánlói linked már vár!',
                html,
            });
            console.log(`  ✅ Elküldve: ${r.name} <${r.email}>`);
            sent++;
            // Small delay to avoid SMTP rate limits
            await new Promise(res => setTimeout(res, 300));
        } catch (err) {
            console.error(`  ❌ Hiba: ${r.email} – ${err.message}`);
            failed++;
        }
    }

    console.log(`\n=== Kész ===`);
    console.log(`✅ Sikeresen elküldve: ${sent}`);
    if (failed > 0) console.log(`❌ Sikertelen: ${failed}`);
}

main().catch(err => {
    console.error('Unexpected error:', err);
    process.exit(1);
});
