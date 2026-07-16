const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    const { action, run_id, admin_secret } = req.body;

    // Validate admin secret
    if (!admin_secret || admin_secret !== process.env.ADMIN_SECRET) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    if (!run_id) return res.status(400).json({ error: 'run_id is required' });

    try {
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
            const nodemailer = require('nodemailer');
            const smtpPassword = process.env.SMTP_PASSWORD;
            const runnerEmail = runData.runners?.email;

            if (smtpPassword && runnerEmail) {
                const runnerName = runData.name || runData.runners?.name || 'Futó Partner';
                const isPilisK = runData.serial_number && (runData.serial_number.includes('PK') || runData.serial_number.includes('999'));
                const campaignName = isPilisK ? 'A Nagy-Kevély csillagjai érem' : 'Prédikálószék Vertical';

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
                    tav: runData.distance_km ? `${runData.distance_km} km` : '',
                    datum: today,
                    campaign: isPilisK ? 'A Nagy-Kevély csillagjai' : 'Prédikálószék Vertical'
                });
                const oklevelLink = `https://vitastepsss.vercel.app/predikalo/oklevel.html?${params.toString()}`;

                const congratsHtml = `
                <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #0b0f19; color: #ffffff; border-radius: 8px;">
                  <h1 style="color: #c4ff00; text-align: center;">🏆 Szuper teljesítés!</h1>
                  <p>Szia <strong>${runnerName}</strong>,</p>
                  <p>Gratulálunk! Az adminisztrátorunk ellenőrizte és <strong>jóváhagyta</strong> a beküldött igazolásodat a <strong>${campaignName}</strong> kihíváson! 🎉</p>
                  <p>Hatalmas gratuláció a sikeres teljesítésedhez! Az érmed hamarosan útnak indul a megadott szállítási módnak megfelelően.</p>
                  
                  <div style="background: #121824; border: 1px solid #1a2235; padding: 15px; border-radius: 6px; margin: 20px 0; text-align: center;">
                    <p style="margin-top: 0; color: #ffffff;">Töltsd le a személyre szabott okleveledet, vagy oszd meg a visszajelzésedet a portálon:</p>
                    <a href="${portalLink}" style="background: #c4ff00; color: #000000; padding: 10px 20px; border-radius: 4px; text-decoration: none; font-weight: bold; display: inline-block; margin-bottom: 10px;">Belépés a Portálra</a>
                    <br>
                    <a href="${oklevelLink}" target="_blank" style="color: #c4ff00; text-decoration: underline; font-size: 0.9rem;">Közvetlen oklevél link</a>
                  </div>
                  
                  <p style="font-size: 0.90rem; color: #8a99b3;">További szép napot és jó futást kívánunk!<br>A VitaSteps csapata</p>
                </div>
                `;

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

        } else {
            return res.status(400).json({ error: 'Invalid action. Use "approve" or "reject".' });
        }
    } catch (err) {
        console.error('Admin action error:', err);
        return res.status(500).json({ error: err.message });
    }
};
