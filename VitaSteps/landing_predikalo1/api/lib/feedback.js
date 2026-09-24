const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
const nodemailer = require('nodemailer');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function handleFeedbackSubmission(req, res) {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
        return res.status(401).json({ error: 'No authorization header provided.' });
    }

    const token = authHeader.split(' ')[1];
    let user;
    try {
        const { data, error: authError } = await supabase.auth.getUser(token);
        if (authError || !data.user) {
            return res.status(401).json({ error: 'Unauthorized user token.' });
        }
        user = data.user;
    } catch (err) {
        return res.status(401).json({ error: 'Token validation failed.' });
    }

    const email = user.email.toLowerCase();

    try {
        const {
            run_id,
            erem_minoseg,
            szallitas_elegedett,
            reszvetel_ujra,
            nps_score,
            kovetkezo_tajegyseg,
            tetszett_legjobban,
            jobba_tenne,
            photo_url
        } = req.body;

        if (!run_id) {
            return res.status(400).json({ error: 'Missing run_id.' });
        }

        const { data: existingFeedback, error: checkError } = await supabase
            .from('feedbacks')
            .select('id')
            .eq('run_id', run_id)
            .maybeSingle();

        if (checkError) throw checkError;

        if (existingFeedback) {
            return res.status(200).json({ success: true, message: 'Feedback already submitted.' });
        }

        // 1. Save feedback to Supabase Database
        const { error: dbError } = await supabase
            .from('feedbacks')
            .insert({
                runner_email: email,
                run_id: run_id,
                erem_minoseg: parseInt(erem_minoseg),
                szallitas_elegedett: parseInt(szallitas_elegedett),
                reszvetel_ujra: reszvetel_ujra,
                nps_score: parseInt(nps_score),
                kovetkezo_tajegyseg: kovetkezo_tajegyseg,
                tetszett_legjobban: tetszett_legjobban || null,
                jobba_tenne: jobba_tenne || null,
                photo_url: photo_url || null
            });

        if (dbError) throw dbError;

        // Fetch run details
        const { data: runData } = await supabase
            .from('runs')
            .select('*, runners(*)')
            .eq('id', run_id)
            .maybeSingle();

        const runnerName = runData?.name || runData?.runners?.name || 'Futó Partner';
        const parts = runnerName.trim().split(/\s+/);
        const firstName = parts.pop() || runnerName;
        const campaign = runData?.campaign || 'predikaloszek';

        // 2. Trigger Referral Email if NPS is 9 or 10
        const npsVal = parseInt(nps_score);
        const smtpPassword = process.env.SMTP_PASSWORD;

        if (npsVal >= 9 && smtpPassword && campaign !== 'pilis') {
            const isPilis = campaign === 'pilis';
            const portalLink = `https://vitastepsss.vercel.app/portal.html?email=${encodeURIComponent(email)}`;
            const refLink = isPilis
                ? `https://vitastepsss.vercel.app/nagykevely/checkout-widget.html?ref=${encodeURIComponent(email)}`
                : `https://vitastepsss.vercel.app/checkout-widget.html?ref=${encodeURIComponent(email)}`;

            let templatePath = path.join(__dirname, '../email_templates/referral_promoter.html');
            if (!fs.existsSync(templatePath)) {
                templatePath = path.join(process.cwd(), 'email_templates/referral_promoter.html');
            }
            if (fs.existsSync(templatePath)) {
                let html = fs.readFileSync(templatePath, 'utf8');
                html = html.replace(/{{FIRST_NAME}}/g, firstName);
                html = html.replace(/{{REFERRAL_LINK}}/g, refLink);
                html = html.replace(/{{PORTAL_LINK}}/g, portalLink);

                const transporter = nodemailer.createTransport({
                    host: 'smtp.gmail.com',
                    port: 587,
                    secure: false,
                    auth: { user: 'vitasteps.team@gmail.com', pass: smtpPassword }
                });

                await transporter.sendMail({
                    from: 'VitaSteps <vitasteps.team@gmail.com>',
                    to: email,
                    subject: '🎁 10% kedvezmény a barátaidnak, ingyenes nevezés Neked!',
                    html: html
                });
            }
        }

        return res.status(200).json({ success: true, message: 'Feedback successfully submitted.' });
    } catch (err) {
        console.error('Submit feedback error:', err);
        return res.status(500).json({ error: err.message });
    }
}

module.exports = {
    handleFeedbackSubmission
};
