const Stripe = require('stripe');
const { google } = require('googleapis');
const { createClient } = require('@supabase/supabase-js');
const nodemailer = require('nodemailer');
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

        const isTest = rawBody.includes('IsTest":"true') || rawBody.includes('test_');
        const stripeKey = isTest
            ? (process.env.STRIPE_TEST_KEY || process.env.STRIPE_SECRET_KEY)
            : process.env.STRIPE_SECRET_KEY;
        const stripe = Stripe(stripeKey);

        const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
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
        const campaign = metadata.Kampany || 'predikaloszek';
        const isTestTx = metadata.IsTest === 'true';

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
            // ── GOOGLE SHEETS ─────────────────────────────────────────────
            console.log('Writing to Google Sheets...');
            const serviceAccountJson = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON);
            const auth = new google.auth.GoogleAuth({
                credentials: {
                    client_email: serviceAccountJson.client_email,
                    private_key: serviceAccountJson.private_key
                },
                scopes: ['https://www.googleapis.com/auth/spreadsheets']
            });
            const sheets = google.sheets({ version: 'v4', auth });
            const sheetId = process.env.GOOGLE_SHEET_ID;

            // ── 1a. tally_raw – one row per order (legacy compatibility) ──
            const campaignDisplay = campaign === 'pilis' ? 'A Nagy-Kevély csillagjai' : 'Prédikálószék';
            const tallyRawRow = Array(22).fill('');
            tallyRawRow[0] = sessionId;
            tallyRawRow[1] = sessionId;
            tallyRawRow[2] = submittedAt;
            tallyRawRow[5] = primaryName;
            tallyRawRow[6] = String(totalPaid);
            tallyRawRow[7] = 'HUF';
            tallyRawRow[8] = primaryName;
            tallyRawRow[9] = email;
            tallyRawRow[11] = billingAddress;
            tallyRawRow[12] = medals[0].distance;
            tallyRawRow[13] = String(totalPaid);
            tallyRawRow[14] = 'HUF';
            tallyRawRow[15] = primaryName;
            tallyRawRow[16] = email;
            tallyRawRow[19] = 'Igen';
            tallyRawRow[20] = campaignDisplay;
            tallyRawRow[21] = campaign === 'pilis' ? 'jelentkezés 1' : 'előjelentkezés 1';

            await sheets.spreadsheets.values.append({
                spreadsheetId: sheetId,
                range: 'tally_raw!A:V',
                valueInputOption: 'USER_ENTERED',
                insertDataOption: 'INSERT_ROWS',
                requestBody: { values: [tallyRawRow] }
            });
            console.log('tally_raw written.');

            // ── 1b. tally_szallitas ────────────────────────────────────────
            const tallySzallitasRow = Array(10).fill('');
            tallySzallitasRow[0] = sessionId;
            tallySzallitasRow[1] = sessionId;
            tallySzallitasRow[2] = submittedAt;
            tallySzallitasRow[3] = primaryName;
            tallySzallitasRow[4] = email;
            tallySzallitasRow[5] = shippingDisplay;
            tallySzallitasRow[6] = primaryName;
            tallySzallitasRow[7] = email;
            tallySzallitasRow[8] = phone;
            tallySzallitasRow[9] = deliveryMethod === 'home'
                ? (homeAddress || billingAddress)
                : `${parcelName} (${parcelAddress})`;

            await sheets.spreadsheets.values.append({
                spreadsheetId: sheetId,
                range: 'tally_szallitas!A:J',
                valueInputOption: 'USER_ENTERED',
                insertDataOption: 'INSERT_ROWS',
                requestBody: { values: [tallySzallitasRow] }
            });
            console.log('tally_szallitas written.');

            // ── 1c. stripe_raw2 – one row per medal ───────────────────────
            // Columns: A=Timestamp, B=SessionID, C=VásárlóEmail, D=NevezoNev, E=Táv,
            //          F=Kampány, G=Szállítás, H=CsomagpontVagyHázhoz, I=CsomagpontID,
            //          J=SzámlázásiCím, K=Telefon, L=VégösszegFt, M=Test, N=Sorszám(later)
            const stripe_raw2_rows = medals.map((medal, idx) => [
                submittedAt,                              // A: Timestamp
                sessionId,                                // B: Session ID
                email,                                    // C: Vásárló email
                medal.name,                               // D: Nevező neve
                medal.distance,                           // E: Táv
                campaign,                                 // F: Kampány
                deliveryMethod,                           // G: Szállítás módja
                deliveryMethod === 'home'
                    ? (homeAddress || billingAddress)
                    : `${parcelName} – ${parcelAddress}`, // H: Csomagpont / házhozszállítási cím
                parcelId,                                 // I: Csomagpont ID
                billingAddress,                           // J: Számlázási cím
                phone,                                    // K: Telefon
                idx === 0 ? String(totalPaid) : '',       // L: Végösszeg (csak első sorban)
                isTestTx ? 'true' : 'false',              // M: Test?
                ''                                        // N: Sorszám (webhook tölti be alább)
            ]);

            await sheets.spreadsheets.values.append({
                spreadsheetId: sheetId,
                range: 'stripe_raw2!A:N',
                valueInputOption: 'USER_ENTERED',
                insertDataOption: 'INSERT_ROWS',
                requestBody: { values: stripe_raw2_rows }
            });
            console.log(`stripe_raw2 written (${medals.length} medal rows).`);

            // ── 2. SUPABASE – one runner per medal ────────────────────────
            console.log('Syncing to Supabase...');
            const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

            // Get current max serial for this campaign
            const suffix = config.prefix;
            const limit = config.limit;

            const { data: existingRunners, error: fetchErr } = await supabase
                .from('runners')
                .select('serial_number')
                .ilike('serial_number', `%${suffix}`);

            if (fetchErr) {
                console.error('Supabase fetch error:', fetchErr);
            }

            const existingSerials = (existingRunners || [])
                .map(r => {
                    const match = (r.serial_number || '').match(/#(\d+)\//);
                    return match ? parseInt(match[1]) : 0;
                });
            let nextSerial = existingSerials.length > 0 ? Math.max(...existingSerials) + 1 : 1;

            for (const medal of medals) {
                const paddedRank = nextSerial.toString().padStart(3, '0');
                const serialNumber = `#${paddedRank}/${limit}${suffix}`;

                const runnerObj = {
                    email: email,
                    name: medal.name,
                    completed: false,
                    completion_date: null,
                    shipped: false,
                    received_date: null,
                    serial_number: serialNumber,
                    distance_km: parseFloat(medal.distance) || null,
                    referred_by: referredBy || null
                };

                // For multiple medals on same email, append index to email to allow multiple records
                if (medals.length > 1) {
                    runnerObj.email = `${email}+medal${nextSerial}`;
                }

                const { error: dbErr } = await supabase
                    .from('runners')
                    .upsert(runnerObj, { onConflict: 'email' });

                if (dbErr) {
                    console.error(`Supabase upsert error for medal ${nextSerial}:`, dbErr);
                } else {
                    console.log(`Runner synced: ${serialNumber} – ${medal.name}`);
                }

                nextSerial++;
            }

            // ── 3. SZÁMLÁZZ.HU INVOICE ────────────────────────────────────
            console.log('Generating Számlázz.hu invoice...');
            const szamlaKey = (isTestTx
                ? (process.env.SZAMLAZZ_TEST_KEY || process.env.SZAMLAZZ_AGENT_KEY)
                : process.env.SZAMLAZZ_AGENT_KEY
            ).toString().trim().toLowerCase();

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

                // Build medals list for email
                const medalsHtml = medals.length === 1
                    ? `<p><strong>Nevező:</strong> ${medals[0].name} &nbsp;|&nbsp; <strong>Táv:</strong> ${medals[0].distance}</p>`
                    : `<ul style="padding-left:18px; margin:10px 0;">${medals.map((m, i) =>
                        `<li>${i + 1}. érem – <strong>${m.name}</strong> (${m.distance})</li>`
                    ).join('')}</ul>`;

                const shippingHtml = deliveryMethod === 'home'
                    ? `<p><strong>Szállítás:</strong> Házhozszállítás – ${homeAddress || billingAddress}</p>`
                    : `<p><strong>Szállítás:</strong> Foxpost automata – ${parcelName || 'választva'}</p>`;

                const welcomeHtml = `
                <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #0b0f19; color: #ffffff; border-radius: 8px;">
                  <h1 style="color: #c4ff00; text-align: center;">🏔️ Sikeres Nevezés!</h1>
                  <p>Szia <strong>${firstName}</strong>,</p>
                  <p>Sikeresen beneveztél a <strong>${campaignName}</strong> kihívásunkra! Köszönjük a bizalmadat! 💚</p>
                  ${medalsHtml}
                  ${shippingHtml}
                  <p>A számlát a Számlázz.hu hamarosan kiküldi e-mailben.</p>

                  <div style="background: #121824; border: 1px solid #1a2235; padding: 15px; border-radius: 6px; margin: 20px 0; text-align: center;">
                    <p style="margin-top: 0; color: #ffffff;">Lépj be a személyes túrázó portálodra, ahol igazolhatod a teljesítésedet:</p>
                    <a href="${portalLink}" style="background: #c4ff00; color: #000000; padding: 10px 20px; border-radius: 4px; text-decoration: none; font-weight: bold; display: inline-block;">Belépés a Portálra</a>
                  </div>

                  <p style="font-size: 0.90rem; color: #8a99b3;">Sok sikert kívánunk a kihíváshoz!<br>A VitaSteps csapata</p>
                </div>
                `;

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
