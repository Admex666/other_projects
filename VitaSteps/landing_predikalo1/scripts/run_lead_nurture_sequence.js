/**
 * run_lead_nurture_sequence.js
 *
 * VitaSteps Lead Nurturing Engine V1 (Biztonsági Teszt Mód)
 *
 * BIZTONSÁGI GARANCIA:
 *   - JELENLEG TESZT ÜZEMMÓD: Valódi leadeknek SOHA nem küld emailt!
 *   - Minden kimenő email KIZÁRÓLAG az admexgm@gmail.com címre érkezik!
 *
 * Automatikus email sequence a Kalandfüzetet letöltött érdeklődőknek:
 *   Day 0: Azonnali lead magnet (GPX + Kalandfüzet)
 *   Day 1: Hasznos túratippek (nem sales)
 *   Day 3: Helytörténeti inspiráció és legendák
 *   Day 5: Célkitűzés és a teljesítmény öröme
 *   Day 7: Emlék & VitaSteps érem ajánlat
 *   Day 10: Utolsó ajánlat (100 db-os limitált széria)
 *
 * Használat:
 *   node scripts/run_lead_nurture_sequence.js             <-- Dry Run (csak ellenőrzés)
 *   node scripts/run_lead_nurture_sequence.js --send      <-- Küldés (admexgm@gmail.com-ra átirányítva!)
 *   node scripts/run_lead_nurture_sequence.js --test-step=1 <-- Day 1 teszt küldése admexgm@gmail.com-ra
 *   node scripts/run_lead_nurture_sequence.js --test-step=all <-- Összes sablon (Day 0, 1, 3, 5, 7, 10) tesztelése
 */

const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');

// ── BIZTONSÁGI TESZT CÍMZETT ─────────────────────────────────────────────────
const SAFE_TEST_EMAIL = 'admexgm@gmail.com';

// ── PARSE ARGUMENTS ──────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const IS_SEND = args.includes('--send') || args.some(a => a.startsWith('--test-step'));
const IS_DRY_RUN = !IS_SEND || args.includes('--dry-run');
const FORCE_TIME = args.includes('--force-time') || args.some(a => a.startsWith('--test-step'));

let TEST_STEP_ARG = null;
const testStepArg = args.find(a => a.startsWith('--test-step='));
if (testStepArg) {
    TEST_STEP_ARG = testStepArg.split('=')[1].trim().toLowerCase();
}

let TARGET_LEAD_ID = null;
const leadIdArg = args.find(a => a.startsWith('--lead-id='));
if (leadIdArg) {
    TARGET_LEAD_ID = leadIdArg.split('=')[1].trim();
}

// ── SUPABASE CLIENT ──────────────────────────────────────────────────────────
const supabaseUrl = process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co';
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;

if (!supabaseKey) {
    console.warn('⚠️ Figyelem: SUPABASE_SERVICE_ROLE_KEY nincs beállítva a környezeti változókban!');
}

const supabase = createClient(supabaseUrl, supabaseKey || 'placeholder-key');

// ── NODEMAILER TRANSPORTER (SSL Port 465) ────────────────────────────────────
const smtpPassword = process.env.SMTP_PASSWORD;
if (!smtpPassword) {
    console.warn('⚠️ Figyelem: SMTP_PASSWORD nincs beállítva a környezeti változókban!');
}

const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 465,
    secure: true,
    auth: {
        user: 'vitasteps.team@gmail.com',
        pass: smtpPassword,
    },
});

// ── SEQUENCE DEFINITION (V1) ─────────────────────────────────────────────────
const SEQUENCE_NAME = 'lead_nurture_v1';
const BASE_URL = 'https://vitastepsss.vercel.app';

const ALL_SEQUENCE_STEPS = [
    {
        step: 0,
        day: 0,
        minDelayHours: 0,
        emailId: 'lead_v1_day0',
        templateFile: 'v1_day0.html',
        subject: '🗺️ Nagy-Kevély Túraútvonalak és Kalandfüzet – VitaSteps',
        getTargetUrl: (leadId) => `${BASE_URL}/nagykevely/index.html?lead=${leadId}&source=email&email_id=lead_v1_day0&sequence=${SEQUENCE_NAME}#kalandkonyv`
    },
    {
        step: 1,
        day: 1,
        minDelayHours: 24, // >= 1 nap
        emailId: 'lead_v1_day1',
        templateFile: 'v1_day1.html',
        subject: '🌲 4 praktikus tipp, hogy a legtöbbet hozd ki a hétvégi túrádból – VitaSteps',
        getTargetUrl: (leadId) => `${BASE_URL}/nagykevely/index.html?lead=${leadId}&source=email&email_id=lead_v1_day1&sequence=${SEQUENCE_NAME}#kalandkonyv`
    },
    {
        step: 3,
        day: 3,
        minDelayHours: 72, // >= 3 nap
        emailId: 'lead_v1_day3',
        templateFile: 'v1_day3.html',
        subject: '🏰 Teve-szikla, Egri vár és Mackó-barlang: A Kevély elrejtett titkai',
        getTargetUrl: (leadId) => `${BASE_URL}/nagykevely/index.html?lead=${leadId}&source=email&email_id=lead_v1_day3&sequence=${SEQUENCE_NAME}#kalandkonyv`
    },
    {
        step: 5,
        day: 5,
        minDelayHours: 120, // >= 5 nap
        emailId: 'lead_v1_day5',
        templateFile: 'v1_day5.html',
        subject: '🎯 Miért jó célt kitűzni a túrákon? A teljesítmény igazi öröme',
        getTargetUrl: (leadId) => `${BASE_URL}/nagykevely/index.html?lead=${leadId}&source=email&email_id=lead_v1_day5&sequence=${SEQUENCE_NAME}#kihivas`
    },
    {
        step: 7,
        day: 7,
        minDelayHours: 168, // >= 7 nap
        emailId: 'lead_v1_day7',
        templateFile: 'v1_day7.html',
        subject: '🏅 Legyen kézzelfogható emléked a túráról! (A Nagy-Kevély kihívás)',
        getTargetUrl: (leadId) => `${BASE_URL}/nagykevely/index.html?lead=${leadId}&source=email&email_id=lead_v1_day7&sequence=${SEQUENCE_NAME}#erem`
    },
    {
        step: 10,
        day: 10,
        minDelayHours: 240, // >= 10 nap
        emailId: 'lead_v1_day10',
        templateFile: 'v1_day10.html',
        subject: '🌟 Megcsináltad a túrát? 100 darabos limitált érem – Nagy-Kevély',
        getTargetUrl: (leadId) => `${BASE_URL}/checkout.html?lead=${leadId}&c=pilis&source=email&email_id=lead_v1_day10&sequence=${SEQUENCE_NAME}`
    }
];

// Az automata sequence a Day 1-től indul (a Day 0-t a capture-lead.js küldi regisztrációkor)
const SEQUENCE_STEPS = ALL_SEQUENCE_STEPS.filter(s => s.step > 0);

// ── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

function extractFirstName(fullName) {
    if (!fullName || typeof fullName !== 'string') return 'Túrázó';
    let clean = fullName.trim();
    if (!clean || clean.includes('@')) return 'Túrázó';
    clean = clean.replace(/^(dr\.|dr|ifj\.|ifj|id\.|id)\s+/i, '').trim();
    const parts = clean.split(/\s+/);
    if (parts.length === 1) {
        return parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
    }
    const firstName = parts[parts.length - 1];
    return firstName.charAt(0).toUpperCase() + firstName.slice(1);
}

function isBudapestDaytime() {
    try {
        const formatter = new Intl.DateTimeFormat('en-US', {
            timeZone: 'Europe/Budapest',
            hour: 'numeric',
            hour12: false
        });
        const currentHour = parseInt(formatter.format(new Date()), 10);
        return currentHour >= 8 && currentHour < 19;
    } catch (e) {
        console.warn('Időzóna formázási figyelmeztetés:', e.message);
        return true;
    }
}

function loadTemplate(templateFile) {
    const templatePath = path.join(__dirname, '../email_templates/lead_nurture', templateFile);
    if (!fs.existsSync(templatePath)) {
        throw new Error(`Nem található az email sablon fájl: ${templatePath}`);
    }
    return fs.readFileSync(templatePath, 'utf8');
}

// ── DIRECT TEST SENDER TO ADMEXGM@GMAIL.COM ──────────────────────────────────

async function runDirectTest(stepFilter) {
    console.log(`\n============================================================`);
    console.log(` 📧 DIRECT TEST KÜLDÉS AZ ADMEXGM@GMAIL.COM CÍMRE`);
    console.log(` Kért lépés(ek): ${stepFilter}`);
    console.log(` Címzett: ${SAFE_TEST_EMAIL}`);
    console.log(`============================================================\n`);

    if (!smtpPassword) {
        console.error('HIBA: SMTP_PASSWORD környezeti változó hiányzik!');
        process.exit(1);
    }

    let stepsToSend = [];
    if (stepFilter === 'all') {
        stepsToSend = ALL_SEQUENCE_STEPS;
    } else {
        const stepNum = parseInt(stepFilter, 10);
        const match = ALL_SEQUENCE_STEPS.find(s => s.step === stepNum || s.day === stepNum);
        if (!match) {
            console.error(`Ismeretlen teszt lépés: ${stepFilter}. Választható: 0, 1, 3, 5, 7, 10 vagy all`);
            process.exit(1);
        }
        stepsToSend = [match];
    }

    const testLeadId = 'test-lead-uuid-admex';
    const testName = 'Ádám';

    for (const step of stepsToSend) {
        console.log(`\n▶️ Teszt küldés előkészítése: Day ${step.day} (${step.templateFile})`);
        const targetUrl = step.getTargetUrl(testLeadId);
        const unsubUrl = `${BASE_URL}/api/unsubscribe?lead=${encodeURIComponent(testLeadId)}`;
        const kalandkonyvUrl = `${BASE_URL}/nagykevely/kalandkonyv.html?lead=${encodeURIComponent(testLeadId)}&source=email&email_id=${step.emailId}&sequence=${SEQUENCE_NAME}`;

        const rawTemplate = loadTemplate(step.templateFile);
        const personalizedHtml = rawTemplate
            .replace(/\{\{NAME\}\}/g, testName)
            .replace(/\{\{CTA_URL\}\}/g, targetUrl)
            .replace(/\{\{UNLOCK_URL\}\}/g, targetUrl)
            .replace(/\{\{KALANDKONYV_URL\}\}/g, kalandkonyvUrl)
            .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl);

        const testSubject = `[TESZT Day ${step.day}] ${step.subject}`;

        try {
            const info = await transporter.sendMail({
                from: '"VitaSteps Teszt" <vitasteps.team@gmail.com>',
                to: SAFE_TEST_EMAIL,
                subject: testSubject,
                html: personalizedHtml
            });
            console.log(`  ✅ SIKERES KÜLDÉS! Message ID: ${info.messageId}`);
        } catch (err) {
            console.error(`  ❌ Hiba küldés közben:`, err.message);
        }

        // Rate limit védelem több levél küldésekor
        if (stepsToSend.length > 1) {
            await new Promise(r => setTimeout(r, 1500));
        }
    }

    console.log(`\n============================================================`);
    console.log(` ✅ Teszt küldés befejeződött. Kérlek ellenőrizd az admexgm@gmail.com postaládádat!`);
    console.log(`============================================================\n`);
}

// ── MAIN RUNNER ──────────────────────────────────────────────────────────────

async function run() {
    // 0. Ha direkt teszt lépést kért a felhasználó
    if (TEST_STEP_ARG) {
        await runDirectTest(TEST_STEP_ARG);
        return;
    }

    console.log(`\n============================================================`);
    console.log(` VitaSteps Lead Nurturing Engine (V1 Sequence Runner)`);
    console.log(` Mód: ${IS_DRY_RUN ? '🔍 DRY RUN (nem küld emailt)' : '🔒 BIZTONSÁGI TESZT MÓD (CSAK admexgm@gmail.com kaphat emailt)'}`);
    console.log(` Időpont: ${new Date().toISOString()}`);
    console.log(`============================================================\n`);

    // 1. Időablak ellenőrzése
    const isDaytime = isBudapestDaytime();
    if (!isDaytime && !FORCE_TIME) {
        console.log(`⏰ Jelenlegi idő Budapesten nem esik a nappali küldési ablakba (08:00–19:00).`);
        console.log(`   Az automatikus email küldés szünetel az éjszakai órákban a jó felhasználói élményért.`);
        return;
    }

    // 2. Leadek lekérése
    let query = supabase.from('leads').select('*').order('created_at', { ascending: true });
    if (TARGET_LEAD_ID) {
        query = query.eq('id', TARGET_LEAD_ID);
        console.log(`🎯 Célzott futtatás adott leadre: ${TARGET_LEAD_ID}`);
    }

    const { data: leads, error: leadErr } = await query;
    if (leadErr) {
        console.error('Hiba a leadek lekérésekor Supabase-ből:', leadErr.message);
        return;
    }

    console.log(`Összes lead az adatbázisban: ${leads ? leads.length : 0} db`);

    // 3. Konvertált vásárlók lekérése
    const { data: runnersWithRuns } = await supabase
        .from('runners')
        .select('email, runs(id)');

    const convertedEmailSet = new Set();
    if (runnersWithRuns) {
        runnersWithRuns.forEach(r => {
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
            if (o.billing_email) convertedEmailSet.add(o.billing_email.toLowerCase().trim());
        });
    }

    console.log(`Aktív vásárlók száma adatbázisban (kizárandó leadek): ${convertedEmailSet.size} fő`);

    // 4. Leadek kiértékelése
    const CUTOFF_DATE = new Date('2026-10-01T00:00:00Z');
    let processedCount = 0;
    let eligibleCount = 0;
    let skippedLegacyCount = 0;
    let skippedConvertedCount = 0;
    let skippedUnsubscribedCount = 0;
    let skippedCompletedCount = 0;
    let skippedTooSoonCount = 0;

    for (const lead of leads || []) {
        processedCount++;
        const email = (lead.email || '').toLowerCase().trim();
        const createdAt = new Date(lead.created_at);

        // A) Szigorú Legacy szabály: 2026. október 1. előtt keletkezett leadek NEM kaphatnak új levelet!
        if (createdAt < CUTOFF_DATE) {
            skippedLegacyCount++;
            continue;
        }

        // B) Kizárás: Leiratkozottak
        if (lead.unsubscribed === true || lead.source === 'unsubscribed' || (lead.campaign && lead.campaign.toLowerCase() === 'unsubscribed')) {
            skippedUnsubscribedCount++;
            continue;
        }

        // C) Kizárás: Vásárolt (konvertált) leadek
        const isConvertedInDb = lead.converted === true;
        const isConvertedInRuns = convertedEmailSet.has(email);

        if (isConvertedInDb || isConvertedInRuns) {
            skippedConvertedCount++;
            continue;
        }

        // D) Sequence állapot meghatározása
        const sequenceStartedAt = new Date(lead.sequence_started_at || lead.created_at);
        const lastStep = lead.last_sequence_step !== undefined && lead.last_sequence_step !== null
            ? parseInt(lead.last_sequence_step, 10)
            : 0;

        if (lastStep >= 10) {
            skippedCompletedCount++;
            continue;
        }

        const now = new Date();
        const elapsedMs = now - sequenceStartedAt;
        const elapsedHours = elapsedMs / (1000 * 60 * 60);

        if (lead.last_sequence_sent_at) {
            const hoursSinceLastSent = (now - new Date(lead.last_sequence_sent_at)) / (1000 * 60 * 60);
            if (hoursSinceLastSent < 20) {
                skippedTooSoonCount++;
                continue;
            }
        }

        // E) Keressük meg a legkisebb esedékes lépést
        const dueStep = SEQUENCE_STEPS.find(s => s.step > lastStep && elapsedHours >= s.minDelayHours);

        if (!dueStep) {
            continue;
        }

        eligibleCount++;
        const firstName = extractFirstName(lead.name);
        const targetUrl = dueStep.getTargetUrl(lead.id);
        const unsubUrl = `${BASE_URL}/api/unsubscribe?lead=${encodeURIComponent(lead.id)}`;
        const kalandkonyvUrl = `${BASE_URL}/nagykevely/kalandkonyv.html?lead=${encodeURIComponent(lead.id)}&source=email&email_id=${dueStep.emailId}&sequence=${SEQUENCE_NAME}`;

        console.log(`[ESEDÉKES] Lead: ${firstName} <${email}>`);
        console.log(`  └─ Lépés: Day ${dueStep.day} (Step ${dueStep.step}) | Eltelt idő: ${elapsedHours.toFixed(1)} óra (min. ${dueStep.minDelayHours}h)`);
        console.log(`  └─ Tárgy: ${dueStep.subject}`);

        if (IS_DRY_RUN) {
            console.log(`  └─ [DRY RUN]: Nem történt email küldés.`);
            continue;
        }

        // F) BIZTONSÁGI KÜLDÉS: CSAK ADMEXGM@GMAIL.COM-RA!
        try {
            console.log(`  🔒 [BIZTONSÁGI MÓD]: Eredeti címzett (${email}) helyett KIZÁRÓLAG ide küldve: ${SAFE_TEST_EMAIL}`);
            const rawTemplate = loadTemplate(dueStep.templateFile);
            const personalizedHtml = rawTemplate
                .replace(/\{\{NAME\}\}/g, firstName)
                .replace(/\{\{CTA_URL\}\}/g, targetUrl)
                .replace(/\{\{UNLOCK_URL\}\}/g, targetUrl)
                .replace(/\{\{KALANDKONYV_URL\}\}/g, kalandkonyvUrl)
                .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl);

            await transporter.sendMail({
                from: '"VitaSteps Teszt" <vitasteps.team@gmail.com>',
                to: SAFE_TEST_EMAIL,
                subject: `[TESZT - Eredeti címzett: ${email}] ${dueStep.subject}`,
                html: personalizedHtml
            });

            console.log(`  ✅ SIKERES TESZT KÜLDÉS -> ${SAFE_TEST_EMAIL}`);

            // Rate limit védelem
            await new Promise(r => setTimeout(r, 1200));

        } catch (sendErr) {
            console.error(`  ❌ Hiba küldés közben:`, sendErr.message);
        }
    }

    console.log(`\n============================================================`);
    console.log(` ÖSSZEGZÉS:`);
    console.log(`   Összes vizsgált lead: ${processedCount}`);
    console.log(`   Régi (2026-10-01 előtti) leadek kihagyva: ${skippedLegacyCount}`);
    console.log(`   Már vásárolt (konvertált) leadek kihagyva: ${skippedConvertedCount}`);
    console.log(`   Leiratkozott leadek kihagyva: ${skippedUnsubscribedCount}`);
    console.log(`   Már lezárult sequence (Day 10+) kihagyva: ${skippedCompletedCount}`);
    console.log(`   20 órán belül már levelet kapott: ${skippedTooSoonCount}`);
    console.log(`   Most esedékes leadek: ${eligibleCount}`);
    console.log(`============================================================\n`);
}

run().catch(err => {
    console.error('Kritikus hiba a futtatás során:', err);
    process.exit(1);
});
