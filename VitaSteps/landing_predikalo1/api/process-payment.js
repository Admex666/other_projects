const Stripe = require('stripe');
const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');
const campaigns = require('../config/campaigns.json');

module.exports = async (req, res) => {
    // Allow GET (from success page redirect) and POST
    if (req.method !== 'GET' && req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    const sessionId = (req.query.session_id || req.body?.session_id || '').trim();
    if (!sessionId) {
        return res.status(400).json({ error: 'Hiányzó session_id paraméter.' });
    }

    // Idempotency: check Supabase if session was already processed
    const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
    const { data: existing } = await supabase
        .from('orders')
        .select('id')
        .eq('stripe_session_id', sessionId)
        .limit(1);

    if (existing && existing.length > 0) {
        console.log(`Session ${sessionId} already processed, skipping.`);
        return res.status(200).json({ received: true, skipped: true });
    }

    // Detect test vs live from session_id prefix
    const isTestTx = sessionId.startsWith('cs_test_');
    const stripeKey = isTestTx
        ? (process.env.STRIPE_TEST_KEY || process.env.STRIPE_SECRET_KEY)
        : process.env.STRIPE_SECRET_KEY;
    const stripe = Stripe(stripeKey);

    // Retrieve and verify the session from Stripe
    let session;
    try {
        session = await stripe.checkout.sessions.retrieve(sessionId);
    } catch (err) {
        console.error('Stripe session retrieve error:', err.message);
        return res.status(400).json({ error: 'Érvénytelen session_id.' });
    }

    if (session.payment_status !== 'paid') {
        console.warn(`Session ${sessionId} not paid yet (status: ${session.payment_status})`);
        return res.status(402).json({ error: 'A fizetés még nem teljesült.' });
    }

    const metadata = session.metadata || {};
    console.log('Processing session metadata:', metadata);

    // ── PARSE METADATA ────────────────────────────────────────────────────
    const email = (metadata.Email || '').trim().toLowerCase();
    const phone = metadata.Telefon || '';
    const billingAddress = metadata.Szamlazasi_cim || '';
    const deliveryMethod = metadata.Szallitas || 'foxpost';
    const parcelName = metadata.Csomagpont_neve || '';
    const parcelAddress = metadata.Csomagpont_cim || '';
    const parcelId = metadata.Csomagpont_id || '';
    const homeAddress = metadata.Hazhoz_cim || '';
    const referredBy = (metadata.Ajanlо_Email || metadata['Ajánló_Email'] || '').trim().toLowerCase();
    const utmCampaign = metadata.Utm_Campaign || metadata.utm_campaign || null;
    const utmContent = metadata.Utm_Content || metadata.utm_content || null;
    const referralsRedeemed = parseInt(metadata.Referrals_Redeemed || metadata.referrals_redeemed || '0', 10);
    // Find campaign robustly matching any variation of 'kampany' or 'campaign' (case-insensitive, handles cyrillic typos)
    let campaign = 'predikaloszek';
    for (const key of Object.keys(metadata)) {
        const lowerKey = key.toLowerCase();
        if (lowerKey.includes('kampany') || lowerKey.includes('campaign') || lowerKey.includes('kampány')) {
            campaign = metadata[key];
            break;
        }
    }

    let medals = [];
    try {
        medals = JSON.parse(metadata.Medaliok || '[]');
    } catch {
        medals = [];
    }

    if (medals.length === 0) {
        const legacyName = metadata.Név || '';
        const legacyDist = metadata.Táv || '';
        if (legacyName) medals = [{ name: legacyName, distance: legacyDist }];
    }

    if (!email || medals.length === 0) {
        console.error('Missing email or medals in session metadata.');
        return res.status(200).json({ received: true, error: 'Missing metadata' });
    }

    const campaignKey = (campaign === 'predikaloszek' || campaign === 'predikalo') ? 'predikaloszek' : 'pilis';
    const config = campaigns[campaignKey];
    const campaignName = config.name;
    const medalPrice = config.price;
    const totalPaid = session.amount_total
        ? Math.round(session.amount_total / 100)
        : medalPrice * medals.length + (deliveryMethod === 'home' ? 1200 : 0);

    const primaryName = medals[0].name;
    const firstName = primaryName.trim().split(/\s+/).pop() || primaryName;
    const shippingDisplay = deliveryMethod === 'home'
        ? `Házhozszállítás: ${homeAddress || billingAddress}`
        : `FOXPOST: ${parcelName} – ${parcelAddress}`;

    const submittedAt = new Date().toLocaleString('hu-HU', { timeZone: 'Europe/Budapest' });

    try {
        // ── 1. SUPABASE DATABASE TRANSACTION ─────────────────────────────
        console.log('Syncing payment data to Supabase...');

        // 1a. Upsert runner details
        const { data: runnerData, error: runnerErr } = await supabase
            .from('runners')
            .upsert({
                email: email.toLowerCase(),
                name: primaryName,
                phone: phone || null,
                billing_address: billingAddress || null,
                billing_name: primaryName
            }, { onConflict: 'email' })
            .select()
            .single();

        if (runnerErr) {
            console.error('Supabase runner upsert error:', runnerErr);
            throw runnerErr;
        }

        // 1b. Create the order
        const { data: orderData, error: orderErr } = await supabase
            .from('orders')
            .insert({
                runner_id: runnerData.id,
                stripe_session_id: sessionId,
                stripe_payment_status: session.payment_status || 'paid',
                amount_total: totalPaid,
                currency: session.currency || 'HUF',
                campaign: campaign || null,
                utm_campaign: utmCampaign || null,
                utm_content: utmContent || null,
                referrals_redeemed: referralsRedeemed,
                is_test: isTestTx,
                billing_name: primaryName,
                billing_email: email,
                billing_address: billingAddress || null
            })
            .select()
            .single();

        if (orderErr) {
            console.error('Supabase orders insert error:', orderErr);
            throw orderErr;
        }

        // 1b-2. Mark lead as converted if this customer previously signed up as a lead
        try {
            await supabase
                .from('leads')
                .update({
                    converted: true,
                    converted_at: new Date().toISOString()
                })
                .eq('email', email.toLowerCase());
            console.log(`Lead status marked as converted for ${email}`);
        } catch (leadUpdateErr) {
            console.warn('Optional lead conversion update skipped/warning:', leadUpdateErr.message);
        }

        // 1c. Create runs and shipments for each medal
        const suffix = config.prefix + (isTestTx ? '-TEST' : '');
        const limit = config.limit;

        const { data: existingRuns, error: fetchErr } = await supabase
            .from('runs')
            .select('serial_number')
            .eq('is_test', isTestTx)
            .ilike('serial_number', `%${suffix}`);

        if (fetchErr) console.error('Supabase fetch error:', fetchErr);

        const existingSerials = (existingRuns || []).map(r => {
            const match = (r.serial_number || '').match(/#(\d+)\//);
            return match ? parseInt(match[1]) : 0;
        });
        let nextSerial = existingSerials.length > 0 ? Math.max(...existingSerials) + 1 : 1;

        for (const medal of medals) {
            const paddedRank = nextSerial.toString().padStart(3, '0');
            const serialNumber = `#${paddedRank}/${limit}${suffix}`;

            const runObj = {
                runner_id: runnerData.id,
                order_id: orderData.id,
                name: medal.name,
                completed: false,
                completion_date: null,
                shipped: false,
                received_date: null,
                serial_number: serialNumber,
                distance_km: parseFloat(medal.distance) || null,
                campaign: campaign || null,
                is_test: isTestTx,
                // Keep legacy columns for backward compatibility before database migration
                stripe_session_id: sessionId,
                referred_by: referredBy || null
            };

            const { data: runData, error: dbErr } = await supabase
                .from('runs')
                .upsert(runObj, { onConflict: 'serial_number' })
                .select()
                .single();

            if (dbErr) {
                console.error(`Supabase runs upsert error for medal ${nextSerial}:`, dbErr);
                nextSerial++;
                continue;
            } else {
                console.log(`Runner synced: ${serialNumber} – ${medal.name}`);
            }

            // 1d. Create shipment entry for this run
            const shipmentObj = {
                run_id: runData.id,
                method: deliveryMethod || null,
                phone: phone || null,
                parcel_id: parcelId || null,
                parcel_name: parcelName || null,
                parcel_address: parcelAddress || null,
                home_address: homeAddress || null,
                shipped: false,
                received: false
            };

            const { error: shipErr } = await supabase
                .from('shipments')
                .upsert(shipmentObj, { onConflict: 'run_id' });

            if (shipErr) {
                console.error(`Supabase shipments upsert error for run ${runData.id}:`, shipErr);
            }

            nextSerial++;
        }

        // ── 3. SZÁMLÁZZ.HU INVOICE ────────────────────────────────────────
        console.log('Generating Számlázz.hu invoice...');
        const rawSzamlaKey = isTestTx
            ? process.env.SZAMLAZZ_TEST_KEY
            : (process.env.SZAMLAZZ_PROD_KEY || process.env.SZAMLAZZ_AGENT_KEY);
        const szamlaKey = rawSzamlaKey ? rawSzamlaKey.toString().trim() : '';

        if (szamlaKey) {
            let zip = '1000', city = 'Budapest', street = billingAddress || 'Külföld';
            const addrMatch = (billingAddress || '').match(/^(\d{4})[,\s]+([A-Za-záéíóöőúüűÁÉÍÓÖŐÚÜŰ\s\-]+?)[,\s]+(.*)$/);
            if (addrMatch) {
                zip = addrMatch[1];
                city = addrMatch[2].trim ? addrMatch[2].trim() : addrMatch[2];
                street = addrMatch[3];
            }

            const today = new Date().toISOString().split('T')[0];
            const invoiceItems = medals.map(medal =>
                `    <tetel>
      <megnevezes>${campaignName} érem</megnevezes>
      <mennyiseg>1.0</mennyiseg>
      <mennyisegiEgyseg>db</mennyisegiEgyseg>
      <nettoEgysegar>${medalPrice}</nettoEgysegar>
      <afakulcs>AAM</afakulcs>
      <nettoErtek>${medalPrice}</nettoErtek>
      <afaErtek>0</afaErtek>
      <bruttoErtek>${medalPrice}</bruttoErtek>
    </tetel>`
            ).join('\n');

            const shippingItem = deliveryMethod === 'home' ? `
    <tetel>
      <megnevezes>Házhozszállítás</megnevezes>
      <mennyiseg>1.0</mennyiseg>
      <mennyisegiEgyseg>db</mennyisegiEgyseg>
      <nettoEgysegar>1200</nettoEgysegar>
      <afakulcs>AAM</afakulcs>
      <nettoErtek>1200</nettoErtek>
      <afaErtek>0</afaErtek>
      <bruttoErtek>1200</bruttoErtek>
    </tetel>` : '';

            const xml = `<?xml version="1.0" encoding="UTF-8"?>
<xmlszamla xmlns="http://www.szamlazz.hu/xmlszamla" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.szamlazz.hu/xmlszamla https://www.szamlazz.hu/szamla/docs/xmlszamla.xsd">
  <beallitasok>
    <szamlaagentkulcs>${szamlaKey}</szamlaagentkulcs>
    <eszamla>false</eszamla>
    <szamlaLetoltes>false</szamlaLetoltes>
    <valaszVerzio>2</valaszVerzio>
  </beallitasok>
  <fejlec>
    <keltDatum>${today}</keltDatum>
    <teljesitesDatum>${today}</teljesitesDatum>
    <fizetesiHataridoDatum>${today}</fizetesiHataridoDatum>
    <fizmod>Bankkártya</fizmod>
    <penznem>HUF</penznem>
    <szamlaNyelve>hu</szamlaNyelve>
    <arfolyamBank>MNB</arfolyamBank>
    <arfolyam>1.0</arfolyam>
    <fizetve>true</fizetve>
  </fejlec>
  <elado>
    <bank>Revolut</bank>
    <bankszamlaszam>30200014-19613410-97640164</bankszamlaszam>
  </elado>
  <vevo>
    <nev>${primaryName}</nev>
    <irsz>${zip}</irsz>
    <telepules>${city}</telepules>
    <cim>${street}</cim>
    <email>${email}</email>
    <sendEmail>true</sendEmail>
  </vevo>
  <tetelek>
${invoiceItems}${shippingItem}
  </tetelek>
</xmlszamla>`;

            const endpoint = 'https://www.szamlazz.hu/szamla/';
            const boundary = '----WebKitFormBoundary' + Math.random().toString(36).substring(2);
            const bodyParts = [
                `--${boundary}`,
                'Content-Disposition: form-data; name="action-xmlagentxmlfile"; filename="invoice.xml"',
                'Content-Type: text/xml',
                '',
                xml,
                `--${boundary}--`,
                ''
            ];

            const szResponse = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': `multipart/form-data; boundary=${boundary}` },
                body: bodyParts.join('\r\n')
            });

            const resText = await szResponse.text();
            console.log('Számlázz.hu response status:', szResponse.status);
            if (resText.includes('<sikeres>true</sikeres>')) {
                console.log('Számlázz.hu invoice generated successfully.');
            } else {
                console.error('Számlázz.hu error:', resText);
            }
        } else {
            console.warn('Számlázz.hu credentials not set, skipping invoice.');
        }

        // ── 4. WELCOME EMAIL ──────────────────────────────────────────────
        console.log('Sending welcome email...');
        const smtpPassword = process.env.SMTP_PASSWORD;
        if (smtpPassword) {
            const transporter = nodemailer.createTransport({
                host: 'smtp.gmail.com',
                port: 587,
                secure: false,
                auth: { user: 'vitasteps.team@gmail.com', pass: smtpPassword }
            });

            const portalLink = `https://vitastepsss.vercel.app/portal.html?email=${encodeURIComponent(email)}`;
            const isPilisK = (campaignKey === 'pilis');
            const locationName = isPilisK ? 'Nagy-Kevély' : 'Prédikálószék';
            const challengePeriod = isPilisK ? '2026. augusztus 1. és szeptember 18.' : '2026. május 28. és június 30.';

            const participantNames = medals.map(m => m.name).filter(Boolean);
            let greetingNames = firstName;
            if (participantNames.length > 0) {
                if (participantNames.length === 1) {
                    greetingNames = participantNames[0];
                } else {
                    greetingNames = participantNames.slice(0, -1).join(', ') + ' és ' + participantNames[participantNames.length - 1];
                }
            }

            const isPlural = participantNames.length > 1;
            const introText = isPlural
                ? `Üdvözlünk a VitaSteps <strong>${campaignName}</strong> kihívásán! Ezzel megtettétek az első lépést afelé, hogy a teljesítményeteket és élményeiteket egyedi emlékekké alakítsátok! 💚`
                : `Üdvözlünk a VitaSteps <strong>${campaignName}</strong> kihívásán! Ezzel megtetted az első lépést afelé, hogy a teljesítményedet és élményeidet egyedi emlékekké alakítsd! 💚`;

            const challengePeriodText = isPlural
                ? `A kihívást <strong>${challengePeriod}</strong> között tudjátok teljesíteni.`
                : `A kihívást <strong>${challengePeriod}</strong> között tudod teljesíteni.`;

            const proofMethodText = isPlural
                ? `A teljesítést igazolni GPS-es rögzítéssel (pl. Strava, Garmin GPX nyomvonal feltöltésével) és/vagy csúcsfotóval (szelfivel) tudjátok a személyes portálotokon.`
                : `A teljesítést igazolni GPS-es rögzítéssel (pl. Strava, Garmin GPX nyomvonal feltöltésével) és/vagy csúcsfotóval (szelfivel) tudod a személyes portálodon.`;

            const deliveryText = `Az érmek postázása a teljesítés igazolását követő 3-5 munkanapon belül történik a választott átvételi pontra.`;

            const medalsHtml = medals.length === 1
                ? `<p style="margin: 5px 0; color: #ffffff;"><strong>Nevező:</strong> ${medals[0].name} &nbsp;|&nbsp; <strong>Táv:</strong> ${medals[0].distance}</p>`
                : `<ul style="padding-left:18px; margin:10px 0; color: #ffffff;">${medals.map((m, i) =>
                    `<li>${i + 1}. érem – <strong>${m.name}</strong> (${m.distance})</li>`
                ).join('')}</ul>`;

            const shippingHtml = deliveryMethod === 'home'
                ? `<p style="margin: 5px 0; color: #ffffff;"><strong>Szállítás:</strong> Házhozszállítás – ${homeAddress || billingAddress}</p>`
                : `<p style="margin: 5px 0; color: #ffffff;"><strong>Szállítás:</strong> Foxpost automata – ${parcelName || 'választva'}</p>`;

            let welcomeHtml = '';
            try {
                const templatePath = path.join(__dirname, '../email_welcome_template.html');
                const rawTemplate = fs.readFileSync(templatePath, 'utf8');
                welcomeHtml = rawTemplate
                    .replace('{{GREETING_NAMES}}', greetingNames)
                    .replace('{{INTRO_TEXT}}', introText)
                    .replace('{{MEDALS_HTML}}', medalsHtml)
                    .replace('{{SHIPPING_HTML}}', shippingHtml)
                    .replace('{{LOCATION_NAME}}', locationName)
                    .replace('{{CHALLENGE_PERIOD_TEXT}}', challengePeriodText)
                    .replace('{{PROOF_METHOD_TEXT}}', proofMethodText)
                    .replace('{{DELIVERY_TEXT}}', deliveryText)
                    .replace('{{PORTAL_LINK}}', portalLink);
            } catch (err) {
                console.error('Error reading email_welcome_template.html:', err);
                // Fallback basic text if template loading fails
                welcomeHtml = `<p>Kedves ${greetingNames}! Sikeresen regisztráltál a ${campaignName} kihívásra. Jelentkezz be itt: ${portalLink}</p>`;
            }

            await transporter.sendMail({
                from: '"VitaSteps" <vitasteps.team@gmail.com>',
                to: email,
                subject: `🏔️ Sikeres Nevezés – ${campaignName}`,
                html: welcomeHtml
            });
            console.log('Welcome email sent.');
        } else {
            console.warn('SMTP_PASSWORD not set, skipping welcome email.');
        }

        return res.status(200).json({ received: true, processed: true });

    } catch (err) {
        console.error('process-payment error:', err);
        return res.status(500).json({ error: err.message });
    }
};
