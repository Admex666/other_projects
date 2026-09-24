const fs = require('fs');
const path = require('path');
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

function getDaysRemaining() {
    const target = new Date('2026-09-27T23:59:59+02:00');
    const now = new Date();
    const diffTime = target - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays <= 0) return 'utolsó órák';
    return `${diffDays} napod`;
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

        const allLeads = leads || [];
        let totalCount = allLeads.length;
        let unsubscribedCount = 0;
        let convertedCount = 0;
        let targetLeads = [];
        const uniqueTargetMap = new Map();

        allLeads.forEach(l => {
            const cleanEmail = (l.email || '').toLowerCase().trim();
            const isUnsub = l.unsubscribed === true || l.source === 'unsubscribed' || (l.campaign && l.campaign.toLowerCase() === 'unsubscribed');
            const isConv = l.converted === true || convertedEmailSet.has(cleanEmail);

            if (isUnsub) {
                unsubscribedCount++;
            } else if (isConv) {
                convertedCount++;
            } else if (cleanEmail && cleanEmail.includes('@')) {
                if (!uniqueTargetMap.has(cleanEmail)) {
                    const item = {
                        id: l.id,
                        email: cleanEmail,
                        name: (l.name && l.name.trim().length > 0) ? l.name.trim() : 'Túrázó',
                        campaign: l.campaign || 'pilis',
                        created_at: l.created_at
                    };
                    uniqueTargetMap.set(cleanEmail, item);
                    targetLeads.push(item);
                }
            }
        });

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
                total: totalCount,
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
    const CHECKOUT_URL = 'https://vitasteps.vercel.app/nagykevely/index.html#arak';
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

            const recipientsMap = new Map();
            (leads || []).forEach(l => {
                const cleanEmail = (l.email || '').toLowerCase().trim();
                if (!cleanEmail || !cleanEmail.includes('@')) return;

                if (l.unsubscribed === true || l.source === 'unsubscribed' || (l.campaign && l.campaign.toLowerCase() === 'unsubscribed')) return;
                if (l.converted === true || convertedEmailSet.has(cleanEmail)) return;

                if (!recipientsMap.has(cleanEmail)) {
                    recipientsMap.set(cleanEmail, {
                        email: cleanEmail,
                        name: (l.name && l.name.trim().length > 0) ? l.name.trim() : 'Túrázó'
                    });
                }
            });

            const targetList = Array.from(recipientsMap.values());

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

            for (let i = 0; i < targetList.length; i++) {
                const r = targetList[i];
                const unsubUrl = `https://vitasteps.vercel.app/api/unsubscribe?email=${encodeURIComponent(r.email)}`;
                const personalizedHtml = rawTemplateHtml
                    .replace(/\{\{NAME\}\}/g, r.name)
                    .replace(/\{\{FIRST_NAME\}\}/g, r.name)
                    .replace(/\{\{DAYS_LEFT\}\}/g, daysLeft)
                    .replace(/\{\{DEADLINE\}\}/g, DEADLINE_STR)
                    .replace(/\{\{CHECKOUT_URL\}\}/g, CHECKOUT_URL)
                    .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl);

                const subject = custom_subject ?
                    custom_subject.replace(/\{\{NAME\}\}/g, r.name) :
                    templateConfig.defaultSubject.replace(/\{\{NAME\}\}/g, r.name);

                try {
                    await transporter.sendMail({
                        from: '"VitaSteps" <vitasteps.team@gmail.com>',
                        to: r.email,
                        subject: subject,
                        html: personalizedHtml,
                    });
                    sentCount++;
                    await new Promise(resolve => setTimeout(resolve, 800));
                } catch (err) {
                    failedCount++;
                    errors.push({ email: r.email, error: err.message });
                    console.error(`Failed to send to ${r.email}:`, err.message);
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
