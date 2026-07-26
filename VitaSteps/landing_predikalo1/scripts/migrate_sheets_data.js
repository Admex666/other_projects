const fs = require('fs');
const path = require('path');

// 1. Manually parse .env to avoid external dependencies
const envContent = fs.readFileSync(path.join(__dirname, '..', '.env'), 'utf8');
envContent.split('\n').forEach(line => {
    const parts = line.split('=');
    if (parts.length >= 2) {
        const key = parts[0].trim();
        const val = parts.slice(1).join('=').trim().replace(/^"|"$/g, '').replace(/^'|'$/g, '');
        process.env[key] = val;
    }
});

const { google } = require('googleapis');
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

async function runMigration() {
    try {
        console.log('🚀 Starting database migration from Google Sheets to Supabase (Prédikálószék)...');

        const serviceAccountJson = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON);
        const auth = new google.auth.GoogleAuth({
            credentials: {
                client_email: serviceAccountJson.client_email,
                private_key: serviceAccountJson.private_key
            },
            scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly']
        });

        const sheets = google.sheets({ version: 'v4', auth });
        const sheetId = process.env.GOOGLE_SHEET_ID;
        const sheetName = 'Nevezések';

        // Fetch sheet values
        console.log('Reading data from Google Sheet...');
        const response = await sheets.spreadsheets.values.get({
            spreadsheetId: sheetId,
            range: `${sheetName}!A1:AH500`,
        });

        const rows = response.data.values;
        if (!rows || rows.length < 2) {
            console.log('No rows found in sheet.');
            return;
        }

        const headers = rows[0];
        const findCol = (name, defaultIdx) => {
            const idx = headers.findIndex(h => h.trim().toLowerCase() === name.toLowerCase().trim());
            return idx !== -1 ? idx : defaultIdx;
        };

        const colSerial = findCol("#", 0);
        const colEmail = findCol("email", 3);
        const colName = findCol("név", 4);
        const colBillingName = findCol("számlázási név", 6);
        const colBillingAddress = findCol("számlázási cím", 7);
        const colPlanDist = findCol("terv km?", 8);
        const colPaid = findCol("fizetett", 9);
        const colTeljesitve = findCol("teljesítve dátum", 12);
        const colDistance = findCol("tény táv?", 13);
        const colShippingType = findCol("szállítás típus", 20);
        const colShippingAddress = findCol("szállítási cím", 21);
        const colShippingPhone = findCol("szállítási telefonszám", 22);
        const colFoxpostBarcode = findCol("foxpost barcode", 25);
        const colShipped = findCol("érem kiküldve?", 26);
        const colReceived = findCol("érem átvéve", 27);
        const colReferredBy = findCol("ajánló email", -1);

        const dataRows = rows.slice(1);
        console.log(`Processing ${dataRows.length} rows...`);

        let migratedCount = 0;

        for (const row of dataRows) {
            const colVal = (idx) => (idx !== -1 && idx < row.length ? (row[idx] || '').toString().trim() : '');

            const email = colVal(colEmail).toLowerCase().trim();
            const name = colVal(colName).trim();
            if (!email || !name) continue;

            const serial = colVal(colSerial);
            if (!serial) continue;

            // Construct serial number e.g. #014/100
            const paddedRank = serial.toString().padStart(3, '0');
            const serialNumber = `#${paddedRank}/100`;

            const billingName = colVal(colBillingName) || name;
            const billingAddress = colVal(colBillingAddress) || null;
            const phone = colVal(colShippingPhone) || null;

            // 1. Upsert runner details
            const { data: runnerData, error: runnerErr } = await supabase
                .from('runners')
                .upsert({
                    email: email,
                    name: name,
                    phone: phone,
                    billing_name: billingName,
                    billing_address: billingAddress
                }, { onConflict: 'email' })
                .select()
                .single();

            if (runnerErr) {
                console.error(`Error upserting runner ${email}:`, runnerErr.message);
                continue;
            }

            // 2. Deterministic order creation
            const stripeSessionId = `MIGRATED-PS-${serial}`;
            const paidAmount = parseInt(colVal(colPaid)) || 7990;

            const { data: orderData, error: orderErr } = await supabase
                .from('orders')
                .upsert({
                    runner_id: runnerData.id,
                    stripe_session_id: stripeSessionId,
                    stripe_payment_status: 'paid',
                    amount_total: paidAmount,
                    currency: 'HUF',
                    campaign: 'predikaloszek',
                    is_test: false,
                    billing_name: billingName,
                    billing_email: email,
                    billing_address: billingAddress
                }, { onConflict: 'stripe_session_id' })
                .select()
                .single();

            if (orderErr) {
                console.error(`Error upserting order for ${email}:`, orderErr.message);
                continue;
            }

            // 3. Upsert run details
            const completionDate = colVal(colTeljesitve);
            const completed = !!completionDate;

            const distanceRaw = colVal(colDistance) || colVal(colPlanDist) || '15';
            let distanceKm = parseFloat(distanceRaw.replace(',', '.'));
            if (isNaN(distanceKm)) distanceKm = 15;

            const shippedVal = colVal(colShipped);
            const shipped = !!shippedVal && !["", "#n/a", "#name?", "#value!", "nem", "no", "false", "0"].includes(shippedVal.toLowerCase());
            
            const receivedDate = colVal(colReceived);
            const referredBy = colReferredBy !== -1 ? colVal(colReferredBy).toLowerCase().trim() : null;

            const runObj = {
                runner_id: runnerData.id,
                order_id: orderData.id,
                name: name,
                completed: completed,
                completion_date: completionDate || null,
                shipped: shipped,
                received_date: receivedDate || null,
                serial_number: serialNumber,
                distance_km: distanceKm,
                campaign: 'predikaloszek',
                is_test: false,
                stripe_session_id: stripeSessionId,
                referred_by: referredBy || null
            };

            const { data: runData, error: runErr } = await supabase
                .from('runs')
                .upsert(runObj, { onConflict: 'serial_number' })
                .select()
                .single();

            if (runErr) {
                console.error(`Error upserting run for ${serialNumber}:`, runErr.message);
                continue;
            }

            // 4. Upsert shipment details
            const rawShippingType = colVal(colShippingType).toLowerCase();
            const rawShippingAddress = colVal(colShippingAddress);
            const barcode = colVal(colFoxpostBarcode) || null;

            if (rawShippingAddress) {
                let method = 'foxpost';
                if (rawShippingType === 'házhozszállítás' || rawShippingType === 'hazhoz' || rawShippingType.includes('posta')) {
                    method = 'home';
                } else if (rawShippingAddress.toLowerCase().includes('kulcsra') || rawShippingAddress.toLowerCase().includes('z-pont') || rawShippingAddress.toLowerCase().includes('packeta')) {
                    method = 'foxpost';
                }

                let parcelName = '';
                let parcelAddress = '';
                let homeAddress = '';

                if (method === 'foxpost') {
                    // Match pattern: "FOXPOST ... (1234 City, Street 12.)"
                    const match = rawShippingAddress.match(/^(.*?)\s*\((.*?)\)$/);
                    if (match) {
                        parcelName = match[1].trim();
                        parcelAddress = match[2].trim();
                    } else {
                        parcelName = rawShippingAddress;
                        parcelAddress = rawShippingAddress;
                    }
                } else {
                    homeAddress = rawShippingAddress;
                }

                const shipmentObj = {
                    run_id: runData.id,
                    method: method,
                    phone: phone,
                    parcel_id: null,
                    parcel_name: parcelName || null,
                    parcel_address: parcelAddress || null,
                    home_address: homeAddress || null,
                    shipped: shipped,
                    received: !!receivedDate,
                    tracking_code: barcode
                };

                const { error: shipErr } = await supabase
                    .from('shipments')
                    .upsert(shipmentObj, { onConflict: 'run_id' });

                if (shipErr) {
                    console.error(`Error upserting shipment for run ${runData.id}:`, shipErr.message);
                }
            }

            migratedCount++;
        }

        console.log(`\n🎉 Migration finished! Successfully processed and synced ${migratedCount} rows from Google Sheets to Supabase.`);
        
    } catch (err) {
        console.error('Migration failed:', err);
    }
}

runMigration();
