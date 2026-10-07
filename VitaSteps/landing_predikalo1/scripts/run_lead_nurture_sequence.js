/**
 * run_lead_nurture_sequence.js
 *
 * VitaSteps Lead Nurturing Engine V1
 *
 * Automatikus email sequence a Kalandfüzetet letöltött érdeklődőknek:
 *   Day 0: Azonnali lead magnet (capture-lead.js küldi)
 *   Day 1: Hasznos túratippek (nem sales)
 *   Day 3: Helytörténeti inspiráció és legendák
 *   Day 5: Célkitűzés és a teljesítmény öröme
 *   Day 7: Emlék & VitaSteps érem ajánlat
 *   Day 10: Utolsó ajánlat (100 db-os limitált széria)
 *
 * Biztonsági garanciák:
 *   - Idempotens: egy lead egy lépést legfeljebb egyszer kaphat meg.
 *   - 2026-10-01 előtti régi leadek SOHA nem kapnak új nurture levelet.
 *   - Vásárlás (converted=true vagy létező run/order) esetén a nurture AZONNAL megáll.
 *   - Leiratkozás (unsubscribed=true) esetén azonnali leállás.
 *   - Időablak ellenőrzés: csak nappal (08:00 - 19:00 Budapest idő) küld, éjjel nem zavarja a felhasználót.
 *   - Minden levélben lead-alapú URL tracking van (nyers email cím nélkül).
 *   - Az elküldött levelekről 'lead_email_sent' esemény kerül az analytics_events táblába.
 *
 * Használat:
 *   node scripts/run_lead_nurture_sequence.js             <-- Dry Run (csak listázza az esedékes leadeket)
 *   node scripts/run_lead_nurture_sequence.js --send      <-- Éles küldés
 *   node scripts/run_lead_nurture_sequence.js --force-time <-- Időablak felülbírálása (tesztekhez)
 *   node scripts/run_lead_nurture_sequence.js --lead-id=<UUID> <-- Csak egy adott lead tesztelése
 */

const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');

// ── PARSE ARGUMENTS ──────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const IS_SEND = args.includes('--send');
const IS_DRY_RUN = !IS_SEND || args.includes('--dry-run');
const FORCE_TIME = args.includes('--force-time');

let TARGET_LEAD_ID = null;
const leadIdArg = args.find(a => a.startsWith('--lead-id='));
if (leadIdArg) {
    TARGET_LEAD_ID = leadIdArg.split('=')[1].trim();
}

// ── SUPABASE CLIENT ──────────────────────────────────────────────────────────
const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

// ── NODEMAILER TRANSPORTER ───────────────────────────────────────────────────
const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: {
        user: 'vitasteps.team@gmail.com',
        pass: process.env.SMTP_PASSWORD,
    },
});

// ── SEQUENCE DEFINITION (V1) ─────────────────────────────────────────────────
const SEQUENCE_NAME = 'lead_nurture_v1';
const BASE_URL = 'https://vitastepsss.vercel.app';

const SEQUENCE_STEPS = [
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
        // Küldési ablak: reggel 8:00-tól este 19:00-ig Budapest idő szerint
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

// ── MAIN RUNNER ──────────────────────────────────────────────────────────────

async function run() {
    console.log(`\n============================================================`);
    console.log(` VitaSteps Lead Nurturing Engine (V1 Sequence Runner)`);
    console.log(` Mód: ${IS_DRY_RUN ? '🔍 DRY RUN (nem küld emaileket, csak ellenőriz)' : '🚀 ÉLES KÜLDÉS'}`);
    console.log(` Időpont: ${new Date().toISOString()}`);
    console.log(`============================================================\n`);

    // 1. Időablak ellenőrzése
    const isDaytime = isBudapestDaytime();
    if (!isDaytime && !FORCE_TIME) {
        console.log(`⏰ Jelenlegi idő Budapesten nem esik a nappali küldési ablakba (08:00–19:00).`);
        console.log(`   Az automatikus email küldés szünetel az éjszakai órákban a jó felhasználói élményért.`);
        console.log(`   (A futtatás felülbírálható a --force-time kapcsolóval.)`);
        return;
    }

    // 2. Összes lead lekérése
    let query = supabase.from('leads').select('*').order('created_at', { ascending: true });
    if (TARGET_LEAD_ID) {
        query = query.eq('id', TARGET_LEAD_ID);
        console.log(`🎯 Célzott futtatás adott leadre: ${TARGET_LEAD_ID}`);
    }

    const { data: leads, error: leadErr } = await query;
    if (leadErr) {
        console.error('Hiba a leadek lekérésekor:', leadErr);
        return;
    }

    console.log(`Összes lead az adatbázisban: ${leads ? leads.length : 0} db`);

    // 3. Konvertált vásárlók lekérése a duplikált vásárlás-ellenőrzéshez
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

    for (const lead of leads) {
        processedCount++;
        const email = (lead.email || '').toLowerCase().trim();
        const createdAt = new Date(lead.created_at);

        // A) Szigorú Legacy szabály: 2026. október 1. előtt keletkezett leadek NEM kaphatnak új levelet!
        if (createdAt < CUTOFF_DATE) {
            skippedLegacyCount++;
            // Ha még nincs lezárva a lépésszámláló, zárjuk le az adatbázisban
            if ((lead.last_sequence_step === undefined || lead.last_sequence_step === null || lead.last_sequence_step < 10) && IS_SEND) {
                try {
                    await supabase.from('leads').update({
                        sequence: SEQUENCE_NAME,
                        last_sequence_step: 10,
                        sequence_started_at: lead.sequence_started_at || lead.created_at,
                        last_sequence_sent_at: lead.last_sequence_sent_at || lead.created_at
                    }).eq('id', lead.id);
                } catch (e) {}
            }
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
            if (!isConvertedInDb && isConvertedInRuns && IS_SEND) {
                // Szinkronizáljuk a leads táblával
                try {
                    await supabase.from('leads').update({
                        converted: true,
                        converted_at: new Date().toISOString()
                    }).eq('id', lead.id);
                } catch (e) {}
            }
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

        // Ne küldjünk egymás után 20 órán belül két sequence levelet ugyanannak a személynek
        if (lead.last_sequence_sent_at) {
            const hoursSinceLastSent = (now - new Date(lead.last_sequence_sent_at)) / (1000 * 60 * 60);
            if (hoursSinceLastSent < 20) {
                skippedTooSoonCount++;
                continue;
            }
        }

        // E) Keressük meg a legkisebb esedékes lépést, amit még nem kapott meg
        const dueStep = SEQUENCE_STEPS.find(s => s.step > lastStep && elapsedHours >= s.minDelayHours);

        if (!dueStep) {
            // Még nem telt el elég idő a következő lépéshez
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
        console.log(`  └─ CTA URL: ${targetUrl}`);

        if (IS_DRY_RUN) {
            console.log(`  └─ [DRY RUN]: Nem történt email küldés.`);
            continue;
        }

        // F) Éles küldés
        try {
            console.log(`  └─ Küldés folyamatban (${email})...`);
            const rawTemplate = loadTemplate(dueStep.templateFile);
            const personalizedHtml = rawTemplate
                .replace(/\{\{NAME\}\}/g, firstName)
                .replace(/\{\{CTA_URL\}\}/g, targetUrl)
                .replace(/\{\{UNLOCK_URL\}\}/g, targetUrl)
                .replace(/\{\{KALANDKONYV_URL\}\}/g, kalandkonyvUrl)
                .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl);

            await transporter.sendMail({
                from: '"VitaSteps" <vitasteps.team@gmail.com>',
                to: email,
                subject: dueStep.subject,
                html: personalizedHtml
            });

            console.log(`  └─ SIKERES KÜLDÉS!`);

            // G) Adatbázis állapot frissítése
            try {
                await supabase.from('leads').update({
                    sequence: SEQUENCE_NAME,
                    last_sequence_step: dueStep.step,
                    last_sequence_sent_at: new Date().toISOString()
                }).eq('id', lead.id);
            } catch (dbErr) {
                console.warn(`  └─ Figyelmeztetés: lead állapot frissítés hiba:`, dbErr.message);
            }

            // H) Analytics esemény rögzítése: lead_email_sent
            try {
                await supabase.from('analytics_events').insert({
                    session_id: 'nurture_' + Date.now(),
                    visitor_id: 'v_lead_' + lead.id,
                    event_name: 'lead_email_sent',
                    event_data: {
                        lead_id: lead.id,
                        sequence: SEQUENCE_NAME,
                        step: dueStep.step,
                        email_id: dueStep.emailId,
                        subject: dueStep.subject,
                        source: 'email'
                    },
                    created_at: new Date().toISOString()
                });
            } catch (anErr) {
                console.warn(`  └─ Figyelmeztetés: analytics_events rögzítés hiba:`, anErr.message);
            }

            // 1.2 mp várakozás SMTP rate limit védelemre
            await new Promise(r => setTimeout(r, 1200));

        } catch (sendErr) {
            console.error(`  └─ HIBA küldés közben (${email}):`, sendErr.message);
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

run().catch(console.error);
