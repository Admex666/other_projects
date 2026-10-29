const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

const TEMPLATES = [
    {
        id: 'email_1_3_days_before_correction',
        title: '⚠️ 1. HELYESBÍTÉS – Javított linkkel (Kizárólag a korábbi 7 címzettnek)',
        path: 'leads_0927/email_1_3_days_before_correction.html',
        defaultSubject: '⚠️ [Helyesbítés] {{NAME}}, az előző levélben a gomb nem működött jól – itt a jó link!',
        description: 'Helyesbítő levél elnézéskéréssel és javított linkkel kizárólag azoknak, akiknek korábban kiment a hibás linkes levél.',
        targetOnlySentOf: 'email_1_3_days_before'
    },
    {
        id: 'email_1_3_days_before',
        title: '📧 1. Sablon – 3 nappal előtte (Szept. 24.)',
        path: 'leads_0927/email_1_3_days_before.html',
        defaultSubject: '⛰️ {{NAME}}, megvan már mikor mész a Nagy-Kevélyre? (3 nap a jelentkezési zárásig)',
        description: 'Emlékeztető a letöltött útvonalakra, visszamenőleges teljesítés és ajánlói/többérmes kedvezmények.'
    },
    {
        id: 'email_2_1_day_before',
        title: '⏳ 2. Sablon – 1 nappal előtte (Szept. 26. - 24 órás sürgetés)',
        path: 'leads_0927/email_2_1_day_before.html',
        defaultSubject: '⏳ Holnap lejár a jelentkezés a Nagy-Kevély kihívásra!',
        description: 'Sürgető levél 24 órás figyelmeztetéssel, tisztázva hogy a túra később is teljesíthető.'
    },
    {
        id: 'email_3_last_day',
        title: '🚨 3. Sablon – Utolsó nap (Szept. 27. - Ma éjféli zárás)',
        path: 'leads_0927/email_3_last_day.html',
        defaultSubject: '🚨 Ma éjfélkor lezárul a jelentkezés a Nagy-Kevély kihívásra!',
        description: 'Utolsó órák, piros sürgősségi kiemelés, ma éjféli határidő és kedvezmények.'
    },
    {
        id: 'lead_conversion_reminder',
        title: '🌲 4. Általános Lead Konverziós Sablon',
        path: 'lead_conversion_reminder.html',
        defaultSubject: '🏅 {{NAME}}, az érmed megszerzésére már csak kevés időd van! – VitaSteps',
        description: 'Általános motivációs levél a Kalandfüzetet letöltött meleg leadeknek.'
    }
];

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

    if (/né$/i.test(lastLower)) {
        if (COMMON_HUNGARIAN_GIVEN_NAMES.has(firstLower) && !AMBIGUOUS_SURNAME_GIVEN_NAMES.has(firstLower)) {
            return toTitleCaseWord(firstPart);
        }
        return parts.map(toTitleCaseWord).join(' ');
    }

    if (COMMON_HUNGARIAN_GIVEN_NAMES.has(lastLower)) {
        return toTitleCaseWord(lastPart);
    }

    if (COMMON_HUNGARIAN_GIVEN_NAMES.has(firstLower)) {
        return toTitleCaseWord(firstPart);
    }

    return toTitleCaseWord(lastPart);
}

function getDaysRemaining() {
    const target = new Date('2026-10-31T23:59:59+01:00');
    const now = new Date();
    const diffTime = target - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays <= 0) return 'utolsó órák';
    return `${diffDays} napod`;
}

async function getSentEmailsMap() {
    try {
        const { data, error } = await supabase.storage
            .from('medals')
            .download('campaigns/sent_leads_emails.json');
        if (data && !error) {
            const text = await data.text();
            if (text && text.trim().length > 0) {
                return JSON.parse(text);
            }
        }
    } catch (e) {
        console.warn('Could not load sent emails from storage:', e.message);
    }

    try {
        const localPath = path.resolve(__dirname, '../../config/sent_leads_emails.json');
        if (fs.existsSync(localPath)) {
            return JSON.parse(fs.readFileSync(localPath, 'utf8'));
        }
    } catch (e) {
        console.warn('Could not load local sent emails fallback:', e.message);
    }

    return {};
}

async function saveSentEmailsMap(sentMap) {
    const jsonStr = JSON.stringify(sentMap, null, 2);
    try {
        await supabase.storage
            .from('medals')
            .upload('campaigns/sent_leads_emails.json', Buffer.from(jsonStr, 'utf8'), {
                upsert: true,
                contentType: 'application/json'
            });
    } catch (e) {
        console.warn('Failed to upload sent emails to storage:', e.message);
    }

    try {
        const localPath = path.resolve(__dirname, '../../config/sent_leads_emails.json');
        fs.writeFileSync(localPath, jsonStr, 'utf8');
    } catch (e) {
        // Safe ignore on read-only serverless
    }
}

async function getConvertedEmailsAndUnsubscribed() {
    const convertedEmailSet = new Set();
    const unsubscribedEmailSet = new Set();

    try {
        const { data: runners } = await supabase
            .from('runners')
            .select('email, runs(id)');
        if (runners) {
            runners.forEach(r => {
                if (r.email && r.runs && r.runs.length > 0) {
                    convertedEmailSet.add(r.email.toLowerCase().trim());
                }
            });
        }
    } catch (e) {
        console.warn('Runners check warning:', e.message);
    }

    try {
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
    } catch (e) {
        console.warn('Orders check warning:', e.message);
    }

    try {
        const { data: unsubEvents } = await supabase
            .from('analytics_events')
            .select('event_data')
            .eq('event_name', 'lead_unsubscribed');
        if (unsubEvents) {
            unsubEvents.forEach(ev => {
                const em = ev.event_data && ev.event_data.email ? String(ev.event_data.email).toLowerCase().trim() : '';
                if (em) unsubscribedEmailSet.add(em);
            });
        }
    } catch (e) {
        // Ignore
    }

    return { convertedEmailSet, unsubscribedEmailSet };
}

function aggregateUniqueLeads(allLeads, convertedEmailSet, extraUnsubscribedSet = new Set()) {
    const unsubscribedEmailSet = new Set(extraUnsubscribedSet);
    const leadConvertedEmailSet = new Set();
    const leadsByEmail = new Map();

    (allLeads || []).forEach(l => {
        const cleanEmail = (l.email || '').toLowerCase().trim();
        if (!cleanEmail || !cleanEmail.includes('@')) return;

        const isUnsub = l.unsubscribed === true || l.source === 'unsubscribed' || (l.campaign && l.campaign.toLowerCase() === 'unsubscribed');
        const isConv = l.converted === true || convertedEmailSet.has(cleanEmail);

        if (isUnsub) {
            unsubscribedEmailSet.add(cleanEmail);
        }
        if (isConv) {
            leadConvertedEmailSet.add(cleanEmail);
        }

        if (!leadsByEmail.has(cleanEmail)) {
            leadsByEmail.set(cleanEmail, []);
        }
        leadsByEmail.get(cleanEmail).push(l);
    });

    const uniqueEmails = Array.from(leadsByEmail.keys());
    let unsubscribedCount = 0;
    let convertedCount = 0;
    const targetLeads = [];

    uniqueEmails.forEach(email => {
        if (unsubscribedEmailSet.has(email)) {
            unsubscribedCount++;
            return;
        }
        if (leadConvertedEmailSet.has(email) || convertedEmailSet.has(email)) {
            convertedCount++;
            return;
        }

        const records = leadsByEmail.get(email);
        let bestRawName = '';
        for (const rec of records) {
            const n = (rec.name || '').trim();
            if (n && !n.includes('@') && !/\d/.test(n)) {
                bestRawName = n;
                break;
            }
        }
        if (!bestRawName && records.length > 0) {
            bestRawName = (records[0].name || '').trim();
        }

        const firstName = extractFirstName(bestRawName);

        targetLeads.push({
            id: records[0].id,
            email: email,
            fullName: bestRawName || 'Túrázó',
            name: firstName,
            campaign: records[0].campaign || 'pilis',
            created_at: records[0].created_at
        });
    });

    return {
        totalUnique: uniqueEmails.length,
        totalRecords: (allLeads || []).length,
        unsubscribedCount,
        convertedCount,
        targetLeads
    };
}

async function handleGetLeadsData(req, res) {
    try {
        // 1. Leads lekérése
        const { data: leads, error: leadErr } = await supabase
            .from('leads')
            .select('*')
            .order('created_at', { ascending: false });

        if (leadErr) throw leadErr;

        // 2. Vásárlók (runners + orders) és leiratkozottak lekérése kizáráshoz
        const { convertedEmailSet, unsubscribedEmailSet } = await getConvertedEmailsAndUnsubscribed();

        const {
            totalUnique,
            totalRecords,
            unsubscribedCount,
            convertedCount,
            targetLeads
        } = aggregateUniqueLeads(leads, convertedEmailSet, unsubscribedEmailSet);

        // 3. Analytics események lekérése a lead tölcsérhez (clicks, checkouts, nurture lépések)
        let emailClicksCount = 0;
        let checkoutStartsCount = 0;
        const nurtureSteps = { day0: 0, day1: 0, day3: 0, day5: 0, day7: 0, day10: 0 };

        try {
            const { data: leadEvents, error: evErr } = await supabase
                .from('analytics_events')
                .select('event_name, event_data, created_at')
                .in('event_name', ['lead_email_sent', 'lead_email_clicked', 'lead_checkout_started']);

            if (!evErr && leadEvents) {
                leadEvents.forEach(ev => {
                    if (ev.event_name === 'lead_email_clicked') {
                        emailClicksCount++;
                    } else if (ev.event_name === 'lead_checkout_started') {
                        checkoutStartsCount++;
                    } else if (ev.event_name === 'lead_email_sent') {
                        const step = String(ev.event_data?.step);
                        if (step === '0') nurtureSteps.day0++;
                        else if (step === '1') nurtureSteps.day1++;
                        else if (step === '3') nurtureSteps.day3++;
                        else if (step === '5') nurtureSteps.day5++;
                        else if (step === '7') nurtureSteps.day7++;
                        else if (step === '10') nurtureSteps.day10++;
                    }
                });
            }
        } catch (evError) {
            console.warn('Analytics lead events fetch error:', evError.message);
        }

        // Aktív októberi meleg leadek (2026. okt 1. utániak, akik még nem vásároltak és nem iratkoztak le)
        const octLeadsMap = new Map();
        (leads || []).filter(l => new Date(l.created_at) >= new Date('2026-10-01T00:00:00Z')).forEach(l => {
            const em = (l.email || '').toLowerCase().trim();
            if (em && !octLeadsMap.has(em)) octLeadsMap.set(em, l);
        });

        let activeWarmOctoberCount = 0;
        octLeadsMap.forEach((l, em) => {
            if (!convertedEmailSet.has(em) && !unsubscribedEmailSet.has(em) && !l.converted) {
                activeWarmOctoberCount++;
            }
        });

        const convRate = totalUnique > 0 ? parseFloat(((convertedCount / totalUnique) * 100).toFixed(1)) : 0;
        const unsubRate = totalUnique > 0 ? parseFloat(((unsubscribedCount / totalUnique) * 100).toFixed(1)) : 0;
        const clickRate = totalUnique > 0 ? parseFloat(((emailClicksCount / totalUnique) * 100).toFixed(1)) : 0;
        const checkoutRate = emailClicksCount > 0 ? parseFloat(((checkoutStartsCount / emailClicksCount) * 100).toFixed(1)) : 0;

        const funnel = {
            totalSubscribers: totalRecords,
            totalUniqueLeads: totalUnique,
            emailClicks: emailClicksCount,
            checkoutStarts: checkoutStartsCount,
            convertedCount: convertedCount,
            convRate: convRate,
            unsubscribedCount: unsubscribedCount,
            unsubRate: unsubRate,
            clickRate: clickRate,
            checkoutRate: checkoutRate,
            nurture: {
                steps: nurtureSteps,
                activeWarmOctoberCount: activeWarmOctoberCount,
                totalOctoberLeads: octLeadsMap.size
            }
        };

        // Sablonok betöltése előnézethez
        const templatesWithContent = TEMPLATES.map(t => {
            const fullPath = path.resolve(__dirname, '../../email_templates', t.path);
            let content = '';
            if (fs.existsSync(fullPath)) {
                content = fs.readFileSync(fullPath, 'utf8');
            }
            return {
                ...t,
                previewHtml: content
            };
        });

        const sentEmailsMap = await getSentEmailsMap();

        return res.status(200).json({
            stats: {
                total: totalUnique,
                totalRecords: totalRecords,
                targetActive: targetLeads.length,
                converted: convertedCount,
                unsubscribed: unsubscribedCount
            },
            funnel: funnel,
            sentEmailsMap: sentEmailsMap,
            targetLeads: targetLeads.slice(0, 100),
            templates: templatesWithContent,
            daysRemaining: getDaysRemaining(),
            testEmail: 'admexgm@gmail.com'
        });

    } catch (err) {
        console.error('Admin leads get error:', err);
        return res.status(500).json({ error: err.message });
    }
}

async function handleSendLeadsEmail(req, res) {
    const { action, sub_action, template_id, custom_subject } = req.body || {};
    const sendMode = sub_action || action; // 'send_test' or 'send_live'

    if (!['send_test', 'send_live'].includes(sendMode)) {
        return res.status(400).json({ error: 'Érvénytelen művelet. Lehetséges opciók: send_test, send_live' });
    }

    const templateConfig = TEMPLATES.find(t => t.id === template_id) || TEMPLATES[0];
    const templatePath = path.resolve(__dirname, '../../email_templates', templateConfig.path);

    if (!fs.existsSync(templatePath)) {
        return res.status(404).json({ error: `Sablonfájl nem található: ${templateConfig.path}` });
    }

    const rawTemplateHtml = fs.readFileSync(templatePath, 'utf8');
    const DEADLINE_STR = '2026. október 31.';
    const LANDING_URL = 'https://vitastepsss.vercel.app/nagykevely/index.html';
    const daysLeft = getDaysRemaining();

    const smtpPassword = process.env.SMTP_PASSWORD;
    if (!smtpPassword) {
        return res.status(500).json({ error: 'SMTP_PASSWORD hiányzik a környezeti változókból.' });
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

    if (sendMode === 'send_test') {
        const testEmail = 'admexgm@gmail.com';
        const testName = 'Ádám (Teszt)';
        const unsubUrl = `https://vitastepsss.vercel.app/api/unsubscribe?email=${encodeURIComponent(testEmail)}`;

        const personalizedHtml = rawTemplateHtml
            .replace(/\{\{NAME\}\}/g, testName)
            .replace(/\{\{FIRST_NAME\}\}/g, testName)
            .replace(/\{\{DAYS_LEFT\}\}/g, daysLeft)
            .replace(/\{\{DEADLINE\}\}/g, DEADLINE_STR)
            .replace(/\{\{CHECKOUT_URL\}\}/g, LANDING_URL)
            .replace(/\{\{LANDING_URL\}\}/g, LANDING_URL)
            .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl);

        const subject = custom_subject ?
            `[TESZT] ${custom_subject.replace(/\{\{NAME\}\}/g, testName)}` :
            `[TESZT] ${templateConfig.defaultSubject.replace(/\{\{NAME\}\}/g, testName)}`;

        try {
            await transporter.sendMail({
                from: '"VitaSteps" <vitasteps.team@gmail.com>',
                to: testEmail,
                subject: subject,
                html: personalizedHtml,
            });

            return res.status(200).json({
                success: true,
                mode: 'test',
                count: 1,
                recipient: testEmail,
                subject: subject,
                message: `Teszt e-mail sikeresen elküldve a(z) ${testEmail} címre!`
            });
        } catch (mailErr) {
            console.error('Test email send error:', mailErr);
            return res.status(500).json({ error: 'Hiba a teszt levél kiküldésekor: ' + mailErr.message });
        }
    }

    if (sendMode === 'send_live') {
        try {
            const { data: leads, error: leadErr } = await supabase
                .from('leads')
                .select('*')
                .order('created_at', { ascending: false });

            if (leadErr) throw leadErr;

            const { convertedEmailSet, unsubscribedEmailSet } = await getConvertedEmailsAndUnsubscribed();
            const { targetLeads: fullTargetList } = aggregateUniqueLeads(leads, convertedEmailSet, unsubscribedEmailSet);

            // Load persistent sent list for this template
            const sentEmailsMap = await getSentEmailsMap();
            if (!sentEmailsMap[templateConfig.id]) {
                sentEmailsMap[templateConfig.id] = [];
            }
            const alreadySentSet = new Set((sentEmailsMap[templateConfig.id] || []).map(e => (e || '').toLowerCase().trim()));

            // Also build a set of all legacy recipients across all 0927 templates
            const allPreviouslyContactedLegacySet = new Set();
            Object.values(sentEmailsMap).forEach(arr => {
                if (Array.isArray(arr)) {
                    arr.forEach(e => {
                        if (e) allPreviouslyContactedLegacySet.add(String(e).toLowerCase().trim());
                    });
                }
            });

            // Restrict audience to parent template recipients if targetOnlySentOf is defined
            let baseList = fullTargetList;
            if (templateConfig.targetOnlySentOf) {
                const parentSentSet = new Set((sentEmailsMap[templateConfig.targetOnlySentOf] || []).map(e => (e || '').toLowerCase().trim()));
                baseList = fullTargetList.filter(r => {
                    const cleanEmail = (r.email || '').toLowerCase().trim();
                    return cleanEmail && parentSentSet.has(cleanEmail);
                });
            }

            // Filter out already sent recipients AND legacy pre-October recipients who already got the 4 September closing emails
            const targetList = baseList.filter(r => {
                const cleanEmail = (r.email || '').toLowerCase().trim();
                if (!cleanEmail || alreadySentSet.has(cleanEmail)) return false;
                if (!templateConfig.targetOnlySentOf && allPreviouslyContactedLegacySet.has(cleanEmail)) return false;
                return true;
            });

            if (targetList.length === 0) {
                return res.status(200).json({
                    success: true,
                    mode: 'live',
                    count: 0,
                    alreadySentCount: alreadySentSet.size,
                    message: `Minden jogosult lead (${alreadySentSet.size} fő) már korábban megkapta ezt a sablont.`
                });
            }

            let sentCount = 0;
            let failedCount = 0;
            const errors = [];
            const processedEmailSet = new Set();

            for (let i = 0; i < targetList.length; i++) {
                const r = targetList[i];
                const cleanEmail = (r.email || '').toLowerCase().trim();

                // Double guard: skip if already processed in this batch or already sent
                if (!cleanEmail || processedEmailSet.has(cleanEmail) || alreadySentSet.has(cleanEmail)) {
                    continue;
                }
                processedEmailSet.add(cleanEmail);

                const firstName = r.name || 'Túrázó';
                const unsubUrl = `https://vitastepsss.vercel.app/api/unsubscribe?email=${encodeURIComponent(cleanEmail)}`;
                const personalizedHtml = rawTemplateHtml
                    .replace(/\{\{NAME\}\}/g, firstName)
                    .replace(/\{\{FIRST_NAME\}\}/g, firstName)
                    .replace(/\{\{DAYS_LEFT\}\}/g, daysLeft)
                    .replace(/\{\{DEADLINE\}\}/g, DEADLINE_STR)
                    .replace(/\{\{CHECKOUT_URL\}\}/g, LANDING_URL)
                    .replace(/\{\{LANDING_URL\}\}/g, LANDING_URL)
                    .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl);

                const subject = custom_subject ?
                    custom_subject.replace(/\{\{NAME\}\}/g, firstName) :
                    templateConfig.defaultSubject.replace(/\{\{NAME\}\}/g, firstName);

                try {
                    await transporter.sendMail({
                        from: '"VitaSteps" <vitasteps.team@gmail.com>',
                        to: cleanEmail,
                        subject: subject,
                        html: personalizedHtml,
                    });
                    sentCount++;

                    // Mark as sent in persistent log
                    alreadySentSet.add(cleanEmail);
                    if (!sentEmailsMap[templateConfig.id].includes(cleanEmail)) {
                        sentEmailsMap[templateConfig.id].push(cleanEmail);
                        await saveSentEmailsMap(sentEmailsMap);
                    }

                    await new Promise(resolve => setTimeout(resolve, 800));
                } catch (err) {
                    failedCount++;
                    errors.push({ email: cleanEmail, error: err.message });
                    console.error(`Failed to send to ${cleanEmail}:`, err.message);
                }
            }

            return res.status(200).json({
                success: true,
                mode: 'live',
                count: sentCount,
                failed: failedCount,
                totalTargeted: targetList.length,
                alreadySentPreviously: alreadySentSet.size - sentCount,
                errors: errors.slice(0, 5),
                message: `Éles küldés befejezve! Sikeresen elküldve: ${sentCount} db új címzettnek${failedCount > 0 ? `, sikertelen: ${failedCount} db` : ''}.`
            });

        } catch (err) {
            console.error('Live broadcast error:', err);
            return res.status(500).json({ error: 'Hiba az éles küldés során: ' + err.message });
        }
    }
}

module.exports = {
    handleGetLeadsData,
    handleSendLeadsEmail,
    extractFirstName,
    aggregateUniqueLeads
};
