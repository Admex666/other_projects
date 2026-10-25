const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');
const { extractFirstName } = require('../scripts/run_lead_nurture_sequence');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    const { name, email, campaign } = req.body || {};

    if (!email || typeof email !== 'string' || !email.includes('@')) {
        return res.status(400).json({ error: 'Érvényes e-mail cím megadása kötelező.' });
    }

    const cleanEmail = email.trim().toLowerCase();
    const rawName = (name && typeof name === 'string' && name.trim().length > 0) ? name.trim() : 'Túrázó';
    const cleanName = (rawName.includes('@') || /^\+?\d[\d\s\-]{5,}$/.test(rawName)) ? 'Túrázó' : rawName;
    const greetingName = extractFirstName(cleanName);
    const activeCampaign = campaign || 'pilis';

    try {
        // 1. Ellenőrizzük, hogy létezik-e már fizetett nevezése a 'runs' vagy 'orders' táblában (konvertált-e már)
        let isConverted = false;
        try {
            const { data: existingRunner } = await supabase
                .from('runners')
                .select('id, runs(id)')
                .ilike('email', cleanEmail)
                .maybeSingle();

            if (existingRunner && existingRunner.runs && existingRunner.runs.length > 0) {
                isConverted = true;
            }

            if (!isConverted) {
                const { data: existingOrders } = await supabase
                    .from('orders')
                    .select('id')
                    .ilike('billing_email', cleanEmail)
                    .eq('is_test', false)
                    .limit(1);
                if (existingOrders && existingOrders.length > 0) {
                    isConverted = true;
                }
            }
        } catch (checkErr) {
            console.warn('Conversion status check warning:', checkErr.message);
        }

        // 1b. Ellenőrizzük, hogy szerepel-e már a 'leads' táblában (idempotencia & leiratkozás védelem)
        let existingLeads = [];
        try {
            const { data: foundLeads } = await supabase
                .from('leads')
                .select('*')
                .ilike('email', cleanEmail)
                .order('created_at', { ascending: false });
            if (foundLeads) existingLeads = foundLeads;
        } catch (existErr) {
            console.warn('Existing leads check warning:', existErr.message);
        }

        const isUnsubscribed = existingLeads.some(l =>
            l.unsubscribed === true ||
            l.source === 'unsubscribed' ||
            (l.campaign && l.campaign.toLowerCase() === 'unsubscribed')
        );

        if (existingLeads.some(l => l.converted === true)) {
            isConverted = true;
        }

        // 2. Mentés / frissítés a 'runners' táblába (központi felhasználói profil)
        const { error: runnerErr } = await supabase
            .from('runners')
            .upsert(
                { email: cleanEmail, name: cleanName },
                { onConflict: 'email', ignoreDuplicates: false }
            );

        if (runnerErr) {
            console.warn('Supabase runners upsert warning:', runnerErr.message);
        }

        // 3. Mentés a 'leads' táblába (duplikáció elkerülésével: ha már létezik, nem szúrunk be új sort!)
        let leadId = existingLeads.length > 0 ? existingLeads[0].id : null;
        const isAlreadyRegisteredLead = existingLeads.length > 0;

        if (!isAlreadyRegisteredLead) {
            try {
                const leadPayload = {
                    email: cleanEmail,
                    name: cleanName,
                    campaign: activeCampaign,
                    source: 'landing_gated_routes',
                    converted: isConverted,
                    converted_at: isConverted ? new Date().toISOString() : null,
                    created_at: new Date().toISOString(),
                    sequence: 'lead_nurture_v1',
                    sequence_started_at: new Date().toISOString(),
                    last_sequence_step: 0,
                    last_sequence_sent_at: new Date().toISOString()
                };

                const { data: insertedLead, error: leadErr } = await supabase
                    .from('leads')
                    .insert(leadPayload)
                    .select('id')
                    .maybeSingle();

                if (leadErr) {
                    // Ha a sequence oszlopok még nincsenek létrehozva a sémában, fallback az alap mezőkre
                    console.warn('Lead insert with sequence columns failed, falling back to base columns:', leadErr.message);
                    const { data: fallbackLead } = await supabase
                        .from('leads')
                        .insert({
                            email: cleanEmail,
                            name: cleanName,
                            campaign: activeCampaign,
                            source: 'landing_gated_routes',
                            converted: isConverted,
                            converted_at: isConverted ? new Date().toISOString() : null,
                            created_at: new Date().toISOString()
                        })
                        .select('id')
                        .maybeSingle();
                    if (fallbackLead) leadId = fallbackLead.id;
                } else if (insertedLead) {
                    leadId = insertedLead.id;
                }
            } catch (leadTableErr) {
                console.warn('Leads table insert warning:', leadTableErr.message);
            }
        } else if (isConverted && existingLeads.some(l => !l.converted)) {
            // Ha közben vásárló lett, szinkronizáljuk a meglévő lead sor(oka)t
            try {
                await supabase
                    .from('leads')
                    .update({ converted: true, converted_at: new Date().toISOString() })
                    .ilike('email', cleanEmail);
            } catch (syncErr) {}
        }

        // Ha nem kaptunk ID-t, próbáljuk meg lekérdezni
        if (!leadId) {
            try {
                const { data: fetchedLead } = await supabase
                    .from('leads')
                    .select('id')
                    .ilike('email', cleanEmail)
                    .order('created_at', { ascending: false })
                    .limit(1)
                    .maybeSingle();
                if (fetchedLead) leadId = fetchedLead.id;
            } catch (fetchErr) {}
        }

        // 4. Analytics: lead_created esemény rögzítése (csak új lead esetén)
        if (!isAlreadyRegisteredLead) {
            try {
                await supabase.from('analytics_events').insert({
                    session_id: 'lead_' + Date.now(),
                    visitor_id: leadId ? 'v_lead_' + leadId : 'v_' + cleanEmail,
                    event_name: 'lead_created',
                    event_data: {
                        lead_id: leadId,
                        email: cleanEmail,
                        campaign: activeCampaign,
                        sequence: 'lead_nurture_v1',
                        step: 0,
                        source: 'landing_gated_routes'
                    },
                    created_at: new Date().toISOString()
                });
            } catch (analyticsErr) {
                console.warn('Analytics lead_created insert warning:', analyticsErr.message);
            }
        }

        // 5. Feloldó URL és Kalandfüzet URL generálása (biztonságos tracking paraméterekkel, e-mail cím nélkül az URL-ben!)
        const host = req.headers['x-forwarded-host'] || req.headers.host || 'vitastepsss.vercel.app';
        const proto = (req.headers['x-forwarded-proto'] || 'https');
        const baseUrl = `${proto}://${host}`;

        const leadParam = leadId ? `lead=${encodeURIComponent(leadId)}` : `lead=true`;
        const unlockUrl = `${baseUrl}/nagykevely/index.html?${leadParam}&source=email&email_id=lead_v1_day0&sequence=lead_nurture_v1#kalandkonyv`;
        const kalandkonyvUrl = `${baseUrl}/nagykevely/kalandkonyv.html?${leadParam}&source=email&email_id=lead_v1_day0&sequence=lead_nurture_v1`;
        const unsubUrl = `${baseUrl}/api/unsubscribe?${leadId ? `lead=${encodeURIComponent(leadId)}` : `email=${encodeURIComponent(cleanEmail)}`}`;

        // Ellenőrizzük, kapott-e már Day 0 e-mailt korábban (duplikált Day 0 megelőzése)
        let alreadyReceivedDay0 = isAlreadyRegisteredLead;
        if (!alreadyReceivedDay0 && leadId) {
            try {
                const { data: sentEvents } = await supabase
                    .from('analytics_events')
                    .select('id')
                    .eq('event_name', 'lead_email_sent')
                    .contains('event_data', { lead_id: leadId, step: 0 })
                    .limit(1);
                if (sentEvents && sentEvents.length > 0) alreadyReceivedDay0 = true;
            } catch (e) {}
        }

        // 6. Automatikus Day 0 e-mail küldés a lead magnet átadására
        // KIZÁRÁS: Nem küldünk levelet, ha leiratkozott, vagy ha már korábban regisztrált/kapott Day 0-t!
        const smtpPassword = process.env.SMTP_PASSWORD;
        if (smtpPassword && !isUnsubscribed && !alreadyReceivedDay0) {
            const transporter = nodemailer.createTransport({
                host: 'smtp.gmail.com',
                port: 587,
                secure: false,
                auth: {
                    user: 'vitasteps.team@gmail.com',
                    pass: smtpPassword
                }
            });

            // Sablon betöltése: elsődlegesen a lead_nurture/v1_day0.html sablonból
            let templatePath = path.resolve(__dirname, '../email_templates/lead_nurture/v1_day0.html');
            if (!fs.existsSync(templatePath)) {
                templatePath = path.resolve(__dirname, '../email_templates/lead_routes_kalandkonyv.html');
            }

            let emailHtml = '';

            if (fs.existsSync(templatePath)) {
                emailHtml = fs.readFileSync(templatePath, 'utf8')
                    .replace(/\{\{NAME\}\}/g, greetingName)
                    .replace(/\{\{CTA_URL\}\}/g, unlockUrl)
                    .replace(/\{\{UNLOCK_URL\}\}/g, unlockUrl)
                    .replace(/\{\{KALANDKONYV_URL\}\}/g, kalandkonyvUrl)
                    .replace(/\{\{UNSUBSCRIBE_URL\}\}/g, unsubUrl);
            } else {
                console.warn('Template file not found at:', templatePath);
                emailHtml = `<p>Kedves ${greetingName}!<br>Itt éred el a Kalandfüzetet és a túraútvonalakat: <a href="${unlockUrl}">Megnyitás</a></p>`;
            }

            await transporter.sendMail({
                from: '"VitaSteps" <vitasteps.team@gmail.com>',
                to: cleanEmail,
                subject: `🗺️ Nagy-Kevély Túraútvonalak és Kalandfüzet – VitaSteps`,
                html: emailHtml
            });

            console.log(`Lead confirmation email (Day 0) sent successfully to ${cleanEmail}`);

            // Analytics: lead_email_sent esemény rögzítése
            try {
                await supabase.from('analytics_events').insert({
                    session_id: 'email_' + Date.now(),
                    visitor_id: leadId ? 'v_lead_' + leadId : 'v_' + cleanEmail,
                    event_name: 'lead_email_sent',
                    event_data: {
                        lead_id: leadId,
                        email: cleanEmail,
                        sequence: 'lead_nurture_v1',
                        step: 0,
                        email_id: 'lead_v1_day0',
                        source: 'email'
                    },
                    created_at: new Date().toISOString()
                });
            } catch (analyticsEmailErr) {
                console.warn('Analytics lead_email_sent insert warning:', analyticsEmailErr.message);
            }
        } else if (isUnsubscribed || alreadyReceivedDay0) {
            console.log(`Day 0 email skipped for ${cleanEmail} (unsubscribed=${isUnsubscribed}, alreadyReceivedDay0=${alreadyReceivedDay0})`);
        } else {
            console.warn('SMTP_PASSWORD missing, email skipped.');
        }

        return res.status(200).json({
            success: true,
            message: 'Sikeres feliratkozás! A hozzáférést feloldottuk.',
            converted: isConverted,
            unsubscribed: isUnsubscribed,
            already_registered: isAlreadyRegisteredLead,
            lead_id: leadId,
            unlockUrl,
            kalandkonyvUrl
        });

    } catch (err) {
        console.error('Lead capture error:', err);
        return res.status(500).json({ error: 'Hiba történt a feliratkozás feldolgozásakor: ' + (err.message || 'Ismeretlen hiba') });
    }
};
