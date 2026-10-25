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

if (!supabaseKey && require.main === module) {
    console.warn('⚠️ Figyelem: SUPABASE_SERVICE_ROLE_KEY nincs beállítva a környezeti változókban!');
}

const supabase = createClient(supabaseUrl, supabaseKey || 'placeholder-key');

// ── NODEMAILER TRANSPORTER (SSL Port 465) ────────────────────────────────────
const smtpPassword = process.env.SMTP_PASSWORD;
if (!smtpPassword && require.main === module) {
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
const CUTOFF_DATE = new Date('2026-10-01T00:00:00Z');

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

// ── MAGYAR KERESZTNÉV FELISMERŐ SZÓTÁR ────────────────────────────────────────
const COMMON_HUNGARIAN_GIVEN_NAMES = new Set([
    'abigél', 'adél', 'adrián', 'adrienn', 'ágnes', 'ágoston', 'ákos', 'alajos', 'albert', 'alex', 'alexandra', 'alíz',
    'amália', 'ambrus', 'anastasia', 'anasztázia', 'andor', 'andrás', 'andrea', 'anett', 'angela', 'angyalka', 'anikó',
    'aniko', 'anita', 'anna', 'annamária', 'annamaria', 'antal', 'antónia', 'áron', 'árpád', 'attila', 'aurél',
    'balázs', 'balazs', 'bálint', 'balint', 'barbara', 'barbi', 'barna', 'barnabás', 'barnabas', 'béla', 'bela',
    'bence', 'benedek', 'benjámin', 'benjamin', 'bernadett', 'berni', 'bertalan', 'bettina', 'bianka', 'biborka',
    'bíborka', 'blanka', 'boglárka', 'boglarka', 'bogi', 'boldizsár', 'borbála', 'borbala', 'boróka', 'botond', 'brigitta',
    'csaba', 'csilla', 'csongor',
    'dalma', 'dániel', 'daniel', 'dani', 'dávid', 'david', 'debóra', 'dénes', 'denes', 'dezső', 'dezso', 'diána', 'diana',
    'dominik', 'dominika', 'donát', 'donat', 'dóra', 'dora', 'dorina', 'dorottya', 'dorka',
    'edina', 'edit', 'eduárd', 'edvárd', 'elek', 'elemér', 'eleonóra', 'eleonora', 'eliza', 'emese', 'emil', 'emília',
    'emilia', 'emma', 'emőke', 'emoke', 'endre', 'enikő', 'eniko', 'erik', 'erika', 'ernő', 'erno', 'erzsébet', 'erzsebet',
    'eszter', 'etelka', 'éva', 'eva', 'evelin',
    'fanni', 'ferenc', 'flóra', 'flora', 'flórián', 'franciska', 'fruzsina',
    'gábor', 'gabor', 'gabriella', 'gabi', 'gaspar', 'gáspár', 'gellért', 'gergely', 'gergő', 'gergo', 'géza', 'geza',
    'gizella', 'gréta', 'greta', 'gyöngyi', 'gyongyi', 'györgy', 'gyorgy', 'györgyi', 'győző', 'gyozo', 'gyula',
    'hajnalka', 'hajni', 'hanna', 'hedvig', 'helga', 'henrietta', 'henrik', 'hilda', 'hubert', 'hunor',
    'ibolya', 'ildikó', 'ildiko', 'ilona', 'imre', 'irén', 'iren', 'istván', 'istvan', 'iván', 'ivan', 'izabella',
    'jakab', 'jános', 'janos', 'jázmin', 'jazmin', 'jenő', 'jeno', 'jolán', 'jolan', 'jónás', 'józsef', 'jozsef',
    'judit', 'júlia', 'julia', 'julianna', 'jusztina',
    'kálmán', 'kalman', 'kamilla', 'karola', 'karolina', 'károly', 'karoly', 'kata', 'katalin', 'kati', 'kitti',
    'klára', 'klara', 'klaudia', 'klementina', 'kolos', 'konrád', 'kornél', 'kornel', 'kornélia', 'kornelia',
    'kristóf', 'kristof', 'krisztián', 'krisztian', 'krisztina', 'kriszta', 'ksénia',
    'lajos', 'lászló', 'laszlo', 'laura', 'leila', 'levente', 'lia', 'lídia', 'lidia', 'lili', 'liliána', 'liliana',
    'lilla', 'lívia', 'livia', 'lőrinc', 'lorinc', 'luca', 'lujza', 'lukács',
    'magdolna', 'magdi', 'maja', 'marcell', 'margit', 'margó', 'mária', 'maria', 'mariann', 'marianna', 'marika',
    'márió', 'márk', 'mark', 'márta', 'marta', 'márti', 'márton', 'marton', 'máté', 'mate', 'mátyás', 'matyas',
    'melinda', 'melissza', 'mihály', 'mihaly', 'miklós', 'miklos', 'milán', 'milan', 'mira', 'mirjam', 'mónika', 'monika',
    'nándor', 'nandor', 'natália', 'natalia', 'natasa', 'nelli', 'nikolett', 'nikoletta', 'niki', 'noémi', 'noemi',
    'nóra', 'nora', 'norbert', 'norbi',
    'olga', 'olivér', 'oliver', 'orsolya', 'orsi', 'oszkár', 'oszkar', 'ottó', 'otto',
    'pál', 'pal', 'péter', 'peter', 'peti', 'petra', 'piroska',
    'ráhel', 'ramóna', 'ramona', 'rebeka', 'réka', 'reka', 'renáta', 'renata', 'renátó', 'richárd', 'richard',
    'rita', 'róbert', 'robert', 'roland', 'róza', 'roza', 'rozália', 'rozalia', 'rudolf',
    'sándor', 'sandor', 'sára', 'sara', 'sári', 'sarolta', 'sebestyén', 'simon', 'szabolcs', 'szandra', 'szilárd',
    'szilard', 'szilveszter', 'szilvia', 'szimonetta', 'szonja', 'szófia',
    'tamás', 'tamas', 'tímea', 'timea', 'timi', 'tibor', 'tivadar', 'tünde', 'tunde',
    'ulrik',
    'valéria', 'valeria', 'vanda', 'vanessza', 'veronika', 'vera', 'viktor', 'viktória', 'viktoria', 'viki',
    'vilmos', 'vince', 'virág', 'virag', 'vivien',
    'zalán', 'zalan', 'zita', 'zoé', 'zoe', 'zoltán', 'zoltan', 'zoli', 'zsolt', 'zsolti', 'zsófia', 'zsofia',
    'zsófi', 'zsofi', 'zsombor', 'zsuzsanna', 'zsuzsa', 'zsuzsi'
]);

const AMBIGUOUS_SURNAME_GIVEN_NAMES = new Set([
    'ádám', 'adam', 'bálint', 'balint', 'barna', 'benedek', 'csonka', 'deák', 'fábián', 'fabian', 'faragó',
    'fazekas', 'fehér', 'fekete', 'fodor', 'forró', 'fülöp', 'fulop', 'gál', 'gal', 'gáspár', 'gaspar',
    'gombos', 'győri', 'hajdú', 'hajdu', 'halász', 'hegedűs', 'horváth', 'horvath', 'illés', 'illes',
    'jakab', 'juhász', 'juhasz', 'kádár', 'kelemen', 'király', 'kiss', 'kovács', 'kovacs',
    'kozma', 'lengyel', 'lukács', 'lukacs', 'magyar', 'máté', 'mate', 'mester', 'mezei', 'miklós', 'miklos',
    'molnár', 'molnar', 'major', 'nagy', 'német', 'németh', 'nemeth', 'nyári', 'oláh', 'olah', 'orbán', 'orban',
    'orosz', 'örs', 'pál', 'pal', 'pap', 'papp', 'pataki', 'péter', 'peter', 'pintér', 'pinter', 'puskás', 'puskas',
    'rácz', 'racz', 'simon', 'sipos', 'somogyi', 'soós', 'soos', 'szabó', 'szabo', 'szalai', 'székely',
    'szekely', 'szilágyi', 'szilagyi', 'szűcs', 'szucs', 'takács', 'takacs', 'tamás', 'tamas', 'tóth', 'toth',
    'török', 'torok', 'urbán', 'urban', 'varga', 'vargha', 'vass', 'végh', 'vegh', 'veres', 'veress',
    'virág', 'virag', 'vörös', 'voros'
]);

function toTitleCaseWord(word) {
    if (!word) return '';
    return word
        .split('-')
        .map(part => part ? part.charAt(0).toUpperCase() + part.slice(1).toLowerCase() : '')
        .join('-');
}

// ── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

function extractFirstName(fullName) {
    if (!fullName || typeof fullName !== 'string') return 'Túrázó';
    let clean = fullName.trim();
    if (!clean || clean.includes('@') || /\d/.test(clean)) return 'Túrázó';

    clean = clean.replace(/^(dr\.|dr|ifj\.|ifj|id\.|id|prof\.|prof|özv\.|ozv)\s+/i, '').trim();
    if (!clean) return 'Túrázó';

    const parts = clean.split(/\s+/).filter(Boolean);
    if (parts.length === 1) {
        return toTitleCaseWord(parts[0]);
    }

    const lastPart = parts[parts.length - 1];
    const firstPart = parts[0];
    const lastLower = lastPart.toLowerCase();
    const firstLower = firstPart.toLowerCase();

    // 1. Ha az utolsó szó "-né"-re végződik (pl. "MIKLÓS ZOLTÁNNÉ", "Belák Udóné")
    if (/né$/i.test(lastLower)) {
        if (COMMON_HUNGARIAN_GIVEN_NAMES.has(firstLower) && !AMBIGUOUS_SURNAME_GIVEN_NAMES.has(firstLower)) {
            return toTitleCaseWord(firstPart);
        }
        return parts.map(toTitleCaseWord).join(' ');
    }

    // 2. Magyar sorrend: az utolsó szó ismert keresztnév (pl. "Szabó Viktória", "Mirczik Ádám", "Ádám Katalin")
    if (COMMON_HUNGARIAN_GIVEN_NAMES.has(lastLower)) {
        return toTitleCaseWord(lastPart);
    }

    // 3. Nyugati sorrend: az első szó ismert keresztnév (pl. "Csaba Tóth", "Annamaria Vincze", "Irén Vizi-Székely", "Anita Babikne Gyovai")
    if (COMMON_HUNGARIAN_GIVEN_NAMES.has(firstLower)) {
        return toTitleCaseWord(firstPart);
    }

    // Alapértelmezett magyar sorrend
    return toTitleCaseWord(lastPart);
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

function loadLegacySentEmailsSet() {
    const set = new Set();
    try {
        const localPath = path.join(__dirname, '../config/sent_leads_emails.json');
        if (fs.existsSync(localPath)) {
            const data = JSON.parse(fs.readFileSync(localPath, 'utf8'));
            Object.values(data || {}).forEach(arr => {
                if (Array.isArray(arr)) {
                    arr.forEach(e => {
                        if (e) set.add(String(e).toLowerCase().trim());
                    });
                }
            });
        }
    } catch (e) {
        // Ignore
    }
    return set;
}

/**
 * Deduplikálja és kiértékeli az összes lead sort e-mail cím szerint.
 * Garantálja:
 *  - Egy e-mail cím SOHA nem kaphat duplikált levelet több lead sor miatt.
 *  - Ha egy e-mail bármely sora leiratkozott vagy vásárolt, az egész e-mail kizárásra kerül.
 *  - Ha egy e-mail legelső regisztrációja 2026-10-01 előtti (vagy szerepel a legacy sent listán), kizárásra kerül.
 *  - Ha a `leads.last_sequence_step` oszlop hiányzik a DB-ből, az `analytics_events` (`lead_email_sent`) alapján is rekonstruálja az állapotot.
 */
function evaluateUniqueLeadsForNurture({
    leads = [],
    convertedEmailSet = new Set(),
    legacySentEmailSet = new Set(),
    emailEvents = [],
    now = new Date()
}) {
    // 1. Események indexelése lead_id és email alapján
    const maxStepByLeadId = new Map();
    const maxStepByEmail = new Map();
    const lastSentAtByLeadId = new Map();
    const lastSentAtByEmail = new Map();
    const unsubscribedByLeadId = new Set();
    const unsubscribedByEmail = new Set();

    (emailEvents || []).forEach(ev => {
        const evName = ev.event_name;
        const data = ev.event_data || {};
        const lid = data.lead_id ? String(data.lead_id).trim() : null;
        const em = data.email ? String(data.email).toLowerCase().trim() : null;
        const ts = ev.created_at ? new Date(ev.created_at) : null;

        if (evName === 'lead_unsubscribed') {
            if (lid) unsubscribedByLeadId.add(lid);
            if (em) unsubscribedByEmail.add(em);
        } else if (evName === 'lead_email_sent') {
            let step = typeof data.step === 'number' ? data.step : parseInt(data.step, 10);
            if (isNaN(step) && data.email_id) {
                const m = String(data.email_id).match(/day(\d+)/i);
                if (m) step = parseInt(m[1], 10);
            }
            if (!isNaN(step)) {
                if (lid) {
                    const prev = maxStepByLeadId.has(lid) ? maxStepByLeadId.get(lid) : -1;
                    if (step > prev) maxStepByLeadId.set(lid, step);
                }
                if (em) {
                    const prev = maxStepByEmail.has(em) ? maxStepByEmail.get(em) : -1;
                    if (step > prev) maxStepByEmail.set(em, step);
                }
            }
            if (ts && !isNaN(ts.getTime())) {
                if (lid) {
                    const prevTs = lastSentAtByLeadId.get(lid);
                    if (!prevTs || ts > prevTs) lastSentAtByLeadId.set(lid, ts);
                }
                if (em) {
                    const prevTs = lastSentAtByEmail.get(em);
                    if (!prevTs || ts > prevTs) lastSentAtByEmail.set(em, ts);
                }
            }
        }
    });

    // 2. Csoportosítás egyedi e-mail cím szerint
    const byEmail = new Map();
    let totalRows = 0;

    (leads || []).forEach(lead => {
        totalRows++;
        const email = (lead.email || '').toLowerCase().trim();
        if (!email || !email.includes('@')) return;
        if (!byEmail.has(email)) {
            byEmail.set(email, []);
        }
        byEmail.get(email).push(lead);
    });

    let skippedLegacyCount = 0;
    let skippedConvertedCount = 0;
    let skippedUnsubscribedCount = 0;
    let skippedCompletedCount = 0;
    let skippedTooSoonCount = 0;
    let skippedNotYetDueCount = 0;
    const eligibleItems = [];

    for (const [email, rows] of byEmail.entries()) {
        // Időrendbe rendezés (legkorábbi elöl)
        rows.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
        const earliestRow = rows[0];
        const latestRow = rows[rows.length - 1];

        // Legjobb név kiválasztása a sorok közül
        let bestRawName = '';
        for (const r of rows) {
            const n = (r.name || '').trim();
            if (n && !n.includes('@') && !/\d/.test(n)) {
                bestRawName = n;
                break;
            }
        }
        if (!bestRawName) {
            bestRawName = (earliestRow.name || '').trim();
        }

        // B) Kizárás: Leiratkozottak (ha BÁRMELYIK sor vagy event leiratkozott) — legmagasabb prioritás
        const isUnsubscribed = rows.some(r =>
            r.unsubscribed === true ||
            r.source === 'unsubscribed' ||
            (r.campaign && r.campaign.toLowerCase() === 'unsubscribed') ||
            unsubscribedByLeadId.has(String(r.id))
        ) || unsubscribedByEmail.has(email);

        if (isUnsubscribed) {
            skippedUnsubscribedCount++;
            continue;
        }

        // C) Kizárás: Vásárolt (konvertált) leadek (ha BÁRMELYIK sor konvertált, vagy szerepel a runners/orders táblában)
        const isConverted = rows.some(r => r.converted === true) || convertedEmailSet.has(email);
        if (isConverted) {
            skippedConvertedCount++;
            continue;
        }

        // A) Szigorú Legacy szabály: 2026. október 1. előtt keletkezett leadek vagy a szeptemberi kampány címzettjei NEM kaphatnak új levelet!
        const earliestCreatedAt = new Date(earliestRow.created_at);
        const isLegacy = earliestCreatedAt < CUTOFF_DATE || legacySentEmailSet.has(email);
        if (isLegacy) {
            skippedLegacyCount++;
            continue;
        }

        // D) Sequence állapot meghatározása (DB oszlopok ÉS analytics_events uniója)
        const sequenceStartedAt = new Date(earliestRow.sequence_started_at || earliestRow.created_at);

        let lastStep = 0;
        for (const r of rows) {
            if (r.last_sequence_step !== undefined && r.last_sequence_step !== null) {
                const s = parseInt(r.last_sequence_step, 10);
                if (!isNaN(s) && s > lastStep) lastStep = s;
            }
            if (maxStepByLeadId.has(String(r.id))) {
                const s = maxStepByLeadId.get(String(r.id));
                if (s > lastStep) lastStep = s;
            }
        }
        if (maxStepByEmail.has(email) && maxStepByEmail.get(email) > lastStep) {
            lastStep = maxStepByEmail.get(email);
        }

        if (lastStep >= 10) {
            skippedCompletedCount++;
            continue;
        }

        // Utolsó kiküldött levél ideje (DB vagy analytics_events)
        let lastSentAt = null;
        for (const r of rows) {
            if (r.last_sequence_sent_at) {
                const t = new Date(r.last_sequence_sent_at);
                if (!isNaN(t.getTime()) && (!lastSentAt || t > lastSentAt)) {
                    lastSentAt = t;
                }
            }
            if (lastSentAtByLeadId.has(String(r.id))) {
                const t = lastSentAtByLeadId.get(String(r.id));
                if (!lastSentAt || t > lastSentAt) {
                    lastSentAt = t;
                }
            }
        }
        if (lastSentAtByEmail.has(email)) {
            const t = lastSentAtByEmail.get(email);
            if (!lastSentAt || t > lastSentAt) {
                lastSentAt = t;
            }
        }

        const elapsedMs = now - sequenceStartedAt;
        const elapsedHours = elapsedMs / (1000 * 60 * 60);

        if (lastSentAt) {
            const hoursSinceLastSent = (now - lastSentAt) / (1000 * 60 * 60);
            if (hoursSinceLastSent < 20) {
                skippedTooSoonCount++;
                continue;
            }
        }

        // E) Keressük meg a legkisebb esedékes lépést
        const dueStep = SEQUENCE_STEPS.find(s => s.step > lastStep && elapsedHours >= s.minDelayHours);
        if (!dueStep) {
            skippedNotYetDueCount++;
            continue;
        }

        const primaryLead = latestRow; // A legfrissebb UUID-t használjuk a linkekhez
        const firstName = extractFirstName(bestRawName);

        eligibleItems.push({
            lead: {
                ...primaryLead,
                email,
                name: bestRawName || primaryLead.name
            },
            allRowIds: rows.map(r => r.id),
            rowCount: rows.length,
            firstName,
            dueStep,
            lastStep,
            elapsedHours,
            sequenceStartedAt,
            lastSentAt
        });
    }

    return {
        totalRows,
        uniqueLeadCount: byEmail.size,
        duplicateRowsRemoved: totalRows - byEmail.size,
        skippedLegacyCount,
        skippedConvertedCount,
        skippedUnsubscribedCount,
        skippedCompletedCount,
        skippedTooSoonCount,
        skippedNotYetDueCount,
        eligibleItems
    };
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

    console.log(`Összes lead rekord az adatbázisban: ${leads ? leads.length : 0} db`);

    // 3. Konvertált vásárlók lekérése (runners + orders)
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

    // 3b. Korábbi szeptemberi kampány címzettek betöltése (extra védelem)
    const legacySentEmailSet = loadLegacySentEmailsSet();
    try {
        const { data: sData, error: sErr } = await supabase.storage
            .from('medals')
            .download('campaigns/sent_leads_emails.json');
        if (sData && !sErr) {
            const parsed = JSON.parse(await sData.text());
            Object.values(parsed || {}).forEach(arr => {
                if (Array.isArray(arr)) {
                    arr.forEach(e => {
                        if (e) legacySentEmailSet.add(String(e).toLowerCase().trim());
                    });
                }
            });
        }
    } catch (e) {
        // Fallback to local config already loaded
    }

    // 3c. Analytics email események lekérése (állapot-rekonstrukcióhoz és leiratkozás ellenőrzéshez)
    let emailEvents = [];
    try {
        const { data: aeData } = await supabase
            .from('analytics_events')
            .select('event_name, event_data, created_at')
            .in('event_name', ['lead_email_sent', 'lead_unsubscribed']);
        if (aeData) emailEvents = aeData;
    } catch (aeErr) {
        console.warn('Analytics events lekérdezési figyelmeztetés:', aeErr.message);
    }

    // 4. Egyedi leadek deduplikált kiértékelése
    const evaluation = evaluateUniqueLeadsForNurture({
        leads: leads || [],
        convertedEmailSet,
        legacySentEmailSet,
        emailEvents,
        now: new Date()
    });

    for (const item of evaluation.eligibleItems) {
        const { lead, firstName, dueStep, elapsedHours, rowCount } = item;
        const email = lead.email;
        const targetUrl = dueStep.getTargetUrl(lead.id);
        const unsubUrl = `${BASE_URL}/api/unsubscribe?lead=${encodeURIComponent(lead.id)}`;
        const kalandkonyvUrl = `${BASE_URL}/nagykevely/kalandkonyv.html?lead=${encodeURIComponent(lead.id)}&source=email&email_id=${dueStep.emailId}&sequence=${SEQUENCE_NAME}`;

        console.log(`[ESEDÉKES] Lead: ${firstName} <${email}>${rowCount > 1 ? ` (deduplikálva ${rowCount} sorból)` : ''}`);
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
    console.log(`   Összes lead rekord a táblában: ${evaluation.totalRows}`);
    console.log(`   Egyedi (deduplikált) e-mail címek: ${evaluation.uniqueLeadCount} (duplikált sorok kiszűrve: ${evaluation.duplicateRowsRemoved})`);
    console.log(`   Régi (2026-10-01 előtti / szept. kampány) kihagyva: ${evaluation.skippedLegacyCount}`);
    console.log(`   Már vásárolt (konvertált) leadek kihagyva: ${evaluation.skippedConvertedCount}`);
    console.log(`   Leiratkozott leadek kihagyva: ${evaluation.skippedUnsubscribedCount}`);
    console.log(`   Már lezárult sequence (Day 10+) kihagyva: ${evaluation.skippedCompletedCount}`);
    console.log(`   20 órán belül már levelet kapott: ${evaluation.skippedTooSoonCount}`);
    console.log(`   Most esedékes egyedi leadek: ${evaluation.eligibleItems.length}`);
    console.log(`============================================================\n`);
}

if (require.main === module) {
    run().catch(err => {
        console.error('Kritikus hiba a futtatás során:', err);
        process.exit(1);
    });
}

module.exports = {
    ALL_SEQUENCE_STEPS,
    SEQUENCE_STEPS,
    CUTOFF_DATE,
    extractFirstName,
    evaluateUniqueLeadsForNurture,
    loadTemplate
};
