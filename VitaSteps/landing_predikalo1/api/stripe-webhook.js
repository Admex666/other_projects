const Stripe = require('stripe');
const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');
const campaigns = require('../config/campaigns.json');

module.exports = async (req, res) => {
    if (req.method !== 'POST') {
        return res.status(405).send('Method Not Allowed');
    }

    const sig = req.headers['stripe-signature'];
    let event;

    try {
        let rawBody = req.body;
        if (typeof req.body !== 'string' && !Buffer.isBuffer(req.body)) {
            rawBody = JSON.stringify(req.body);
        }

        // Detect test mode by peeking at raw body before signature verification
        // (livemode:false appears in the event JSON for test events)
        const rawBodyStr = Buffer.isBuffer(rawBody) ? rawBody.toString('utf8') : rawBody;
        const isTestEvent = rawBodyStr.includes('"livemode":false') || rawBodyStr.includes('IsTest":"true');

        const stripeKey = isTestEvent
            ? process.env.STRIPE_TEST_KEY || process.env.STRIPE_SECRET_KEY
            : process.env.STRIPE_SECRET_KEY;
        const stripe = Stripe(stripeKey);

        // Select the correct webhook signing secret based on mode
        const webhookSecret = isTestEvent
            ? (process.env.STRIPE_TEST_WEBHOOK_SECRET || process.env.STRIPE_WEBHOOK_SECRET)
            : process.env.STRIPE_WEBHOOK_SECRET;

        if (webhookSecret && sig) {
            event = stripe.webhooks.constructEvent(rawBody, sig, webhookSecret);
        } else {
            event = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
        }
    } catch (err) {
        console.error('Webhook signature verification failed:', err.message);
        return res.status(400).send(`Webhook Error: ${err.message}`);
    }

    console.log('Received Stripe Event Type:', event.type);

    if (event.type === 'checkout.session.completed') {
        const session = event.data.object;
        const metadata = session.metadata || {};
        console.log('Session metadata:', metadata);

        // ── PARSE METADATA (new multi-medal format) ────────────────────────
        const email = (metadata.Email || '').trim().toLowerCase();
        const phone = metadata.Telefon || '';
        const billingAddress = metadata.Szamlazasi_cim || metadata.Számlázási_cím || '';
        const deliveryMethod = metadata.Szallitas || 'foxpost';
        const parcelName = metadata.Csomagpont_neve || '';
        const parcelAddress = metadata.Csomagpont_cim || metadata.Csomagpont_cím || '';
        const parcelId = metadata.Csomagpont_id || '';
        const homeAddress = metadata.Hazhoz_cim || '';
        const referredBy = (metadata.Ajanlо_Email || metadata['Ajánló_Email'] || '').trim().toLowerCase();
        // Find campaign robustly matching any variation of 'kampany' or 'campaign' (case-insensitive, handles cyrillic typos)
        let campaign = 'predikaloszek';
        for (const key of Object.keys(metadata)) {
            const lowerKey = key.toLowerCase();
            if (lowerKey.includes('kampany') || lowerKey.includes('campaign') || lowerKey.includes('kampány')) {
                campaign = metadata[key];
                break;
            }
        }
        const isTestTx = (metadata.IsTest === 'true' || session.livemode === false);

        // Parse medals JSON (new) or fall back to old single-medal format
        let medals = [];
        try {
            medals = JSON.parse(metadata.Medaliok || '[]');
        } catch {
            medals = [];
        }

        // Fallback for old single-medal format
        if (medals.length === 0) {
            const legacyName = metadata.Név || '';
            const legacyDist = metadata.Táv || '';
            if (legacyName) {
                medals = [{ name: legacyName, distance: legacyDist }];
            }
        }

        if (!email || medals.length === 0) {
            console.error('Missing email or medals in checkout metadata.');
            return res.status(200).json({ received: true, error: 'Missing metadata' });
        }

        const campaignKey = (campaign === 'predikaloszek' || campaign === 'predikalo') ? 'predikaloszek' : 'pilis';
        const config = campaigns[campaignKey];
        const campaignName = config.name;
        const medalPrice = config.price;
        const totalPaid = session.amount_total
            ? Math.round(session.amount_total / 100) // Stripe no-decimal for HUF = already in HUF
            : medalPrice * medals.length + (deliveryMethod === 'home' ? 1200 : 0);

        // The first medal's contact info is used for the "buyer"
        const primaryName = medals[0].name;
        const firstName = primaryName.trim().split(/\s+/).pop() || primaryName;
        const shippingDisplay = deliveryMethod === 'home'
            ? `Házhozszállítás: ${homeAddress || billingAddress}`
            : `FOXPOST: ${parcelName} – ${parcelAddress}`;

        const submittedAt = new Date().toLocaleString('hu-HU', { timeZone: 'Europe/Budapest' });
        const sessionId = session.id || `stripe_${Date.now()}`;

        try {
            // ── 1. SUPABASE DATABASE TRANSACTION ─────────────────────────────
            console.log('Syncing payment data to Supabase...');
            const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

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

            // 1c. Create runs and shipments for each medal
            const suffix = config.prefix + (isTestTx ? '-TEST' : '');
            const limit = config.limit;

            const { data: existingRuns, error: fetchErr } = await supabase
                .from('runs')
                .select('serial_number')
                .eq('is_test', isTestTx)
                .ilike('serial_number', `%${suffix}`);

            if (fetchErr) {
                console.error('Supabase fetch error:', fetchErr);
            }

            const existingSerials = (existingRuns || [])
                .map(r => {
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

            // ── 3. SZÁMLÁZZ.HU INVOICE ────────────────────────────────────
            console.log('Generating Számlázz.hu invoice...');
            const rawSzamlaKey = isTestTx
                ? process.env.SZAMLAZZ_TEST_KEY
                : (process.env.SZAMLAZZ_PROD_KEY || process.env.SZAMLAZZ_AGENT_KEY);
            const szamlaKey = rawSzamlaKey ? rawSzamlaKey.toString().trim() : '';

            if (szamlaKey) {
                let zip = '1000';
                let city = 'Budapest';
                let street = billingAddress || 'Külföld';

                const addrMatch = (billingAddress || '').match(/^(\d{4})[,\s]+([A-Za-záéíóöőúüűÁÉÍÓÖŐÚÜŰ\s\-]+?)[,\s]+(.*)$/);
                if (addrMatch) {
                    zip = addrMatch[1];
                    city = addrMatch[2].trim ? addrMatch[2].trim() : addrMatch[2];
                    street = addrMatch[3];
                }

                const today = new Date().toISOString().split('T')[0];

                // Build line items for invoice – one per medal + shipping if applicable
                const invoiceItems = medals.map(medal =>
                    `    <tetel>
      <megnevezes>${campaignName} Nevezési díj (${medal.distance}) – ${medal.name}</megnevezes>
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
      <megnevezes>Házhozszállítás (Magyar Posta)</megnevezes>
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
    <eszamla>true</eszamla>
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
    <megjegyzes>Biztonságos Stripe kártyás fizetés.</megjegyzes>
    <arfolyamBank>MNB</arfolyamBank>
    <arfolyam>1.0</arfolyam>
    <fizetve>true</fizetve>
  </fejlec>
  <elado>
    <bank>OTP Bank</bank>
    <bankszamlaszam>11773004-00000000-00000000</bankszamlaszam>
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
            // ── 4. WELCOME EMAIL ──────────────────────────────────────────
            console.log('Sending welcome email...');
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

        } catch (err) {
            console.error('Webhook processing error:', err);
            return res.status(500).send(`Internal Webhook Error: ${err.message}`);
        }
    }

    res.status(200).json({ received: true });
};
