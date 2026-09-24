const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../../.env') });
require('dotenv').config();
const nodemailer = require('nodemailer');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

// Éremkiszállítás dátumai kampányonként (YYYY-MM-DD)
const MEDAL_SHIP_DATES = {
    pilis: '2026-08-25',
    predikaloszek: '2026-01-01',
};

function getMedalShippingText(campaignKey) {
    const raw = MEDAL_SHIP_DATES[campaignKey] || '2026-08-25';
    const shipDate = new Date(raw + 'T12:00:00Z');
    const now = new Date();
    if (now > shipDate) {
        return 'Az érmeket néhány munkanapon belül feladjuk, a megadott szállítási módnak megfelelően. 📦';
    }
    const dateHu = shipDate.toLocaleDateString('hu-HU', { year: 'numeric', month: 'long', day: 'numeric' });
    return `Az érmeket <strong>${dateHu}</strong> után postázzuk ki, a megadott szállítási módnak megfelelően. 📦`;
}

function formatDistanceLabel(dist, isPilis) {
    if (dist == null || dist === '') return '';
    const num = typeof dist === 'number' ? dist : parseFloat(dist);
    if (isNaN(num)) return String(dist);
    if (isPilis) {
        if (num <= 6) return `Családi (${num} km)`;
        if (num >= 9 && num <= 11) return `Klasszikus (${num} km)`;
        if (num >= 12 && num <= 15) return `Extra (${num} km)`;
        if (num >= 20) return `Félmaraton (${num} km)`;
        return `Kevély (${num} km)`;
    } else {
        if (num <= 11) return `Klasszikus (${num} km)`;
        if (num >= 14 && num <= 16) return `Félmaraton (${num} km)`;
        if (num >= 19 && num <= 21) return `Hosszú (${num} km)`;
        if (num >= 24) return `Ultra (${num} km)`;
        return `Prédikáló (${num} km)`;
    }
}

async function handleApproveActions(req, res) {
    const { action, run_id, run_ids } = req.body;

    if (action !== 'ping' && action !== 'ship' && !run_id) {
        return res.status(400).json({ error: 'run_id is required' });
    }
    if (action === 'ship' && (!run_ids || !Array.isArray(run_ids))) {
        return res.status(400).json({ error: 'run_ids (array) is required' });
    }

    if (action === 'approve') {
        const today = new Date().toISOString().split('T')[0];

        // Fetch runner details to send congratulatory email
        const { data: runData, error: fetchErr } = await supabase
            .from('runs')
            .select('*, runners(email, name)')
            .eq('id', run_id)
            .single();

        if (fetchErr || !runData) {
            throw new Error('Nem található a regisztráció a megadott ID-val: ' + (fetchErr?.message || 'Ismeretlen hiba'));
        }

        const { error } = await supabase
            .from('runs')
            .update({
                completed: true,
                completion_date: today
            })
            .eq('id', run_id);

        if (error) throw error;

        // Send congratulatory email
        const smtpPassword = process.env.SMTP_PASSWORD;
        const runnerEmail = runData.runners?.email;

        if (smtpPassword && runnerEmail) {
            const runnerName = runData.name || runData.runners?.name || 'Futó Partner';
            const isPilisK = runData.serial_number && (runData.serial_number.includes('PK') || runData.serial_number.includes('999'));
            const campaignName = isPilisK ? 'A Nagy-Kevély csillagai érem' : 'Prédikálószék Vertical';
            const campaignKey = isPilisK ? 'pilis' : 'predikaloszek';
            const shippingText = getMedalShippingText(campaignKey);

            const transporter = nodemailer.createTransport({
                host: 'smtp.gmail.com',
                port: 587,
                secure: false,
                auth: { user: 'vitasteps.team@gmail.com', pass: smtpPassword }
            });

            const portalLink = `https://vitastepsss.vercel.app/portal.html?email=${encodeURIComponent(runnerEmail)}`;

            // Construct parameters for oklevel.html link
            const params = new URLSearchParams({
                nev: runnerName,
                sorszam: runData.serial_number || '',
                tav: formatDistanceLabel(runData.distance_km, isPilisK),
                datum: today,
                campaign: isPilisK ? 'A Nagy-Kevély csillagai' : 'Prédikálószék Vertical'
            });
            const oklevelLink = `https://vitastepsss.vercel.app/predikalo/oklevel.html?${params.toString()}`;

            let congratsHtml = '';
            try {
                let templatePath = path.join(__dirname, '../../email_templates/proof_approved.html');
                if (!fs.existsSync(templatePath)) {
                    templatePath = path.join(process.cwd(), 'email_templates/proof_approved.html');
                }
                const rawTemplate = fs.readFileSync(templatePath, 'utf8');
                congratsHtml = rawTemplate
                    .replace(/\{\{RUNNER_NAME\}\}/g, runnerName)
                    .replace(/\{\{CAMPAIGN_NAME\}\}/g, campaignName)
                    .replace(/\{\{SHIPPING_TEXT\}\}/g, shippingText)
                    .replace(/\{\{PORTAL_LINK\}\}/g, portalLink)
                    .replace(/\{\{OKLEVEL_LINK\}\}/g, oklevelLink);
            } catch (tmplErr) {
                console.error('Error loading proof_approved.html:', tmplErr);
                congratsHtml = `
                <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #0b0f19; color: #ffffff; border-radius: 8px;">
                  <h1 style="color: #c4ff00; text-align: center;">🏆 Szuper teljesítés!</h1>
                  <p>Kedves <strong>${runnerName}</strong>,</p>
                  <p>Gratulálunk! Az igazolásodat jóváhagytuk a <strong>${campaignName}</strong> kihíváson! 🎉</p>
                  <p>${shippingText}</p>
                  <p><a href="${portalLink}" style="color: #c4ff00;">Belépés a Portálra</a> | <a href="${oklevelLink}" style="color: #c4ff00;">Oklevél</a></p>
                </div>`;
            }

            await transporter.sendMail({
                from: '"VitaSteps" <vitasteps.team@gmail.com>',
                to: runnerEmail,
                subject: `🏆 Sikeres teljesítés jóváhagyva: ${campaignName}!`,
                html: congratsHtml
            });
            console.log(`Congrats email sent to ${runnerEmail}`);
        }

        return res.status(200).json({ success: true, message: 'Run approved and email sent.' });

    } else if (action === 'reject') {
        const { error } = await supabase
            .from('runs')
            .update({
                proof_submitted: false,
                proof_urls: [],
                proof_submitted_at: null
            })
            .eq('id', run_id);

        if (error) throw error;
        return res.status(200).json({ success: true, message: 'Run rejected and reset.' });

    } else if (action === 'ship') {
        const { error: shipErr } = await supabase
            .from('shipments')
            .update({
                shipped: true,
                shipped_at: new Date().toISOString()
            })
            .in('run_id', run_ids);

        if (shipErr) throw shipErr;

        const { error: runErr } = await supabase
            .from('runs')
            .update({ shipped: true })
            .in('id', run_ids);

        if (runErr) throw runErr;

        return res.status(200).json({ success: true, message: 'Runs marked as shipped.' });

    } else if (action === 'update_shipment') {
        const { phone, parcel_id, parcel_name, method, home_address } = req.body;

        // 1. Update shipments table
        const updatePayload = {};
        if (phone !== undefined) updatePayload.phone = phone;
        if (parcel_id !== undefined) updatePayload.parcel_id = parcel_id;
        if (parcel_name !== undefined) updatePayload.parcel_name = parcel_name;
        if (method !== undefined) updatePayload.method = method;
        if (home_address !== undefined) updatePayload.home_address = home_address;

        const { error: shipErr } = await supabase
            .from('shipments')
            .update(updatePayload)
            .eq('run_id', run_id);

        if (shipErr) throw shipErr;

        // 2. Also update runner phone if provided
        if (phone) {
            const { data: runData } = await supabase
                .from('runs')
                .select('runner_id')
                .eq('id', run_id)
                .single();

            if (runData && runData.runner_id) {
                await supabase
                    .from('runners')
                    .update({ phone: phone })
                    .eq('id', runData.runner_id);
            }
        }

        return res.status(200).json({ success: true, message: 'Shipment updated.' });

    } else if (action === 'ping') {
        return res.status(200).json({ success: true, message: 'Pong' });
    }

    return res.status(400).json({ error: 'Invalid action.' });
}

module.exports = {
    handleApproveActions
};
