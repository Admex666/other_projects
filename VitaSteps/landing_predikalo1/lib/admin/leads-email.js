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
        description: 'Általános motivációs levél a Kalandkönyvet letöltött meleg leadeknek.'
    }
];

function extractFirstName(fullName) {
    if (!fullName || typeof fullName !== 'string') return 'Túrázó';
    let clean = fullName.trim();
    if (!clean || clean.includes('@')) return 'Túrázó';

    // Remove titles like Dr., Ifj., Id.
    clean = clean.replace(/^(dr\.|dr|ifj\.|ifj|id\.|id)\s+/i, '').trim();

    const parts = clean.split(/\s+/);
    if (parts.length === 1) {
        return parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
    }
    // In Hungarian format: "Vezetéknév Keresztnév" -> the last word is the first name (e.g. "Szabó Viktória" -> "Viktória")
    const firstName = parts[parts.length - 1];
    return firstName.charAt(0).toUpperCase() + firstName.slice(1);
}

function getDaysRemaining() {
    const target = new Date('2026-09-27T23:59:59+02:00');
    const now = new Date();
    const diffTime = target - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays <= 0) return 'utolsó órák';
    return `${diffDays} napod`;
}

function aggregateUniqueLeads(allLeads, convertedEmailSet) {
    const unsubscribedEmailSet = new Set();
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
            if (n && !n.includes('@')) {
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

        // 2. Vásárlók (konvertáltak) lekérése kizáráshoz
        const { data: runners, error: runErr } = await supabase
            .from('runners')
            .select('email, runs(id)');

        if (runErr) throw runErr;

        const convertedEmailSet = new Set();
        if (runners) {
            runners.forEach(r => {
                if (r.email && r.runs && r.runs.length > 0) {
                    convertedEmailSet.add(r.email.toLowerCase().trim());
                }
            });
        }

        const {
            totalUnique,
            totalRecords,
            unsubscribedCount,
            convertedCount,
            targetLeads
        } = aggregateUniqueLeads(leads, convertedEmailSet);

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

        return res.status(200).json({
            stats: {
                total: totalUnique,
                totalRecords: totalRecords,
                targetActive: targetLeads.length,
                converted: convertedCount,
                unsubscribed: unsubscribedCount
            },
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
    const DEADLINE_STR = '2026. szeptember 27.';
    const CHECKOUT_URL = 'https://vitasteps.vercel.app/checkout.html?c=pilis';
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
        const unsubUrl = `https://vitasteps.vercel.app/api/unsubscribe?email=${encodeURIComponent(testEmail)}`;

        const personalizedHtml = rawTemplateHtml
            .replace(/\{\{NAME\}\}/g, testName)
            .replace(/\{\{FIRST_NAME\}\}/g, testName)
            .replace(/\{\{DAYS_LEFT\}\}/g, daysLeft)
            .replace(/\{\{DEADLINE\}\}/g, DEADLINE_STR)
            .replace(/\{\{CHECKOUT_URL\}\}/g, CHECKOUT_URL)
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

            const { data: runners } = await supabase
                .from('runners')
                .select('email, runs(id)');

            const convertedEmailSet = new Set();
            if (runners) {
                runners.forEach(r => {
                    if (r.email && r.runs && r.runs.length > 0) {
                        convertedEmailSet.add(r.email.toLowerCase().trim());
                    }
                });
            }

            const { targetLeads: targetList } = aggregateUniqueLeads(leads, convertedEmailSet);

            if (targetList.length === 0) {
                return res.status(200).json({
                    success: true,
                    mode: 'live',
                    count: 0,
                    message: 'Nincs kiküldendő aktív lead az adatbázisban.'
                });
            }

            let sentCount = 0;
            let failedCount = 0;
            const errors = [];
            const processedEmailSet = new Set();

            for (let i = 0; i < targetList.length; i++) {
                const r = targetList[i];
                const cleanEmail = (r.email || '').toLowerCase().trim();

                // Double guard: skip if already processed in this batch
                if (!cleanEmail || processedEmailSet.has(cleanEmail)) {
                    continue;
                }
                processedEmailSet.add(cleanEmail);

                const firstName = r.name || 'Túrázó';
                const unsubUrl = `https://vitasteps.vercel.app/api/unsubscribe?email=${encodeURIComponent(cleanEmail)}`;
                const personalizedHtml = rawTemplateHtml
                    .replace(/\{\{NAME\}\}/g, firstName)
                    .replace(/\{\{FIRST_NAME\}\}/g, firstName)
                    .replace(/\{\{DAYS_LEFT\}\}/g, daysLeft)
                    .replace(/\{\{DEADLINE\}\}/g, DEADLINE_STR)
                    .replace(/\{\{CHECKOUT_URL\}\}/g, CHECKOUT_URL)
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
                errors: errors.slice(0, 5),
                message: `Éles küldés befejezve! Sikeresen elküldve: ${sentCount} db címzettnek${failedCount > 0 ? `, sikertelen: ${failedCount} db` : ''}.`
            });

        } catch (err) {
            console.error('Live broadcast error:', err);
            return res.status(500).json({ error: 'Hiba az éles küldés során: ' + err.message });
        }
    }
}

module.exports = {
    handleGetLeadsData,
    handleSendLeadsEmail
};
