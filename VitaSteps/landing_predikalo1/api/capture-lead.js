const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');

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
    const cleanName = (name && typeof name === 'string' && name.trim().length > 0) ? name.trim() : 'Túrázó';
    const activeCampaign = campaign || 'pilis';

    try {
        // 1. Ellenőrizzük, hogy létezik-e már fizetett nevezése a 'runs' táblában (konvertált-e már)
        let isConverted = false;
        try {
            const { data: existingRunner } = await supabase
                .from('runners')
                .select('id, runs(id)')
                .eq('email', cleanEmail)
                .maybeSingle();

            if (existingRunner && existingRunner.runs && existingRunner.runs.length > 0) {
                isConverted = true;
            }
        } catch (checkErr) {
            console.warn('Conversion status check warning:', checkErr.message);
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

        // 3. Mentés a 'leads' táblába (konverziós státusszal és időbélyeggel)
        try {
            const leadPayload = {
                email: cleanEmail,
                name: cleanName,
                campaign: activeCampaign,
                source: 'landing_gated_routes',
                converted: isConverted,
                converted_at: isConverted ? new Date().toISOString() : null,
                created_at: new Date().toISOString()
            };

            const { error: leadErr } = await supabase
                .from('leads')
                .insert(leadPayload);

            if (leadErr) {
                // Ha a converted oszlop még nincs létrehozva a táblában, próbáljuk meg anélkül
                console.warn('Lead insert with converted status failed, falling back to base columns:', leadErr.message);
                await supabase
                    .from('leads')
                    .insert({
                        email: cleanEmail,
                        name: cleanName,
                        campaign: activeCampaign,
                        source: 'landing_gated_routes',
                        created_at: new Date().toISOString()
                    });
            }
        } catch (leadTableErr) {
            console.warn('Leads table insert warning:', leadTableErr.message);
        }

        // 4. Feloldó URL és Kalandkönyv URL generálása
        const host = req.headers['x-forwarded-host'] || req.headers.host || 'vitastepsss.vercel.app';
        const proto = (req.headers['x-forwarded-proto'] || 'https');
        const baseUrl = `${proto}://${host}`;

        const unlockUrl = `${baseUrl}/nagykevely/index.html?lead=true&email=${encodeURIComponent(cleanEmail)}#kalandkonyv`;
        const kalandkonyvUrl = `${baseUrl}/nagykevely/kalandkonyv.html?lead=true&nev=${encodeURIComponent(cleanName)}`;

        // 5. Automatikus e-mail küldés a szabványos e-mail sablonból
        const smtpPassword = process.env.SMTP_PASSWORD;
        if (smtpPassword) {
            const transporter = nodemailer.createTransport({
                host: 'smtp.gmail.com',
                port: 587,
                secure: false,
                auth: {
                    user: 'vitasteps.team@gmail.com',
                    pass: smtpPassword
                }
            });

            // Sablon betöltése az email_templates mappából
            const templatePath = path.resolve(__dirname, '../email_templates/lead_routes_kalandkonyv.html');
            let emailHtml = '';

            if (fs.existsSync(templatePath)) {
                emailHtml = fs.readFileSync(templatePath, 'utf8')
                    .replace(/\{\{NAME\}\}/g, cleanName)
                    .replace(/\{\{UNLOCK_URL\}\}/g, unlockUrl)
                    .replace(/\{\{KALANDKONYV_URL\}\}/g, kalandkonyvUrl);
            } else {
                console.warn('Template file not found at:', templatePath);
                emailHtml = `<p>Szia ${cleanName}!<br>Itt éred el a Kalandkönyvet és a túraútvonalakat: <a href="${unlockUrl}">Megnyitás</a></p>`;
            }

            await transporter.sendMail({
                from: '"VitaSteps" <vitasteps.team@gmail.com>',
                to: cleanEmail,
                subject: `🗺️ Nagy-Kevély Túraútvonalak és Kalandkönyv – VitaSteps`,
                html: emailHtml
            });

            console.log(`Lead confirmation email sent successfully to ${cleanEmail}`);
        } else {
            console.warn('SMTP_PASSWORD missing, email skipped.');
        }

        return res.status(200).json({
            success: true,
            message: 'Sikeres feliratkozás! Az e-mailt és a hozzáférési linket elküldtük.',
            converted: isConverted,
            unlockUrl,
            kalandkonyvUrl
        });

    } catch (err) {
        console.error('Lead capture error:', err);
        return res.status(500).json({ error: 'Hiba történt a feliratkozás feldolgozásakor: ' + (err.message || 'Ismeretlen hiba') });
    }
};
