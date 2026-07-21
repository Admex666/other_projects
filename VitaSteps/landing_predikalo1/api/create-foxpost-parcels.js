const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

function formatPhone(phone) {
    if (!phone) return '';
    let cleaned = phone.replace(/\D/g, '');
    if (cleaned.startsWith('06')) {
        cleaned = '36' + cleaned.substring(2);
    }
    if (!cleaned.startsWith('36') && cleaned.length === 9) {
        cleaned = '36' + cleaned;
    }
    return `+${cleaned}`;
}

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    const { run_ids, admin_secret } = req.body;

    // Validate admin secret
    if (!admin_secret || admin_secret !== process.env.ADMIN_SECRET) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    if (!run_ids || !Array.isArray(run_ids) || run_ids.length === 0) {
        return res.status(400).json({ error: 'run_ids (non-empty array) is required' });
    }

    try {
        // 1. Fetch runs and shipments from Supabase
        const { data: runs, error: fetchErr } = await supabase
            .from('runs')
            .select('*, runners(name, email, phone), shipments(*)')
            .in('id', run_ids);

        if (fetchErr) throw fetchErr;
        if (!runs || runs.length === 0) {
            return res.status(404).json({ error: 'No matching runs found' });
        }

        // 2. Build parcel creation payload for Foxpost API
        const parcelsPayload = [];
        const runMap = new Map(); // to lookup runs by serial number later

        for (const run of runs) {
            const runner = run.runners || {};
            const shipment = Array.isArray(run.shipments) ? (run.shipments[0] || {}) : (run.shipments || {});

            // Skip if already shipped (to prevent duplicate parcel creation on Foxpost)
            if (shipment.shipped) {
                console.log(`Skipping already shipped run: ${run.serial_number}`);
                continue;
            }

            const name = run.name || runner.name || 'Ismeretlen';
            const email = runner.email || '';
            const rawPhone = shipment.phone || run.phone || runner.phone || '';
            const phone = formatPhone(rawPhone);
            const destination = shipment.parcel_id || run.parcel_id || '';
            const method = shipment.method || run.shipping_method || 'foxpost';

            // Foxpost bulk API only supports parcel lockers. Home delivery is handled separately or ignored here.
            if (method !== 'foxpost') {
                console.log(`Skipping home delivery run ${run.serial_number} from direct Foxpost API upload`);
                continue;
            }

            if (!destination) {
                console.warn(`No destination locker ID found for run ${run.serial_number}`);
                continue;
            }

            parcelsPayload.push({
                recipientName: name,
                recipientEmail: email,
                recipientPhone: phone,
                destination: destination,
                size: "XS",
                cod: 0,
                refCode: run.serial_number, // Use unique serial number as the reference code
                comment: "VitaSteps erem"
            });

            runMap.set(run.serial_number, run);
        }

        if (parcelsPayload.length === 0) {
            return res.status(200).json({ 
                success: true, 
                message: 'No eligible Foxpost locker shipments found for creation.',
                created_count: 0
            });
        }

        // 3. Send payload to Foxpost API
        console.log(`Sending ${parcelsPayload.length} parcels to Foxpost API...`);
        const foxpostUrl = "https://webapi.foxpost.hu/api/parcel";
        const authHeader = 'Basic ' + Buffer.from(process.env.FOXPOST_USERNAME + ':' + process.env.FOXPOST_PASSWORD).toString('base64');

        const fResponse = await fetch(foxpostUrl, {
            method: 'POST',
            headers: {
                'Api-key': process.env.FOXPOST_API_KEY,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': authHeader
            },
            body: JSON.stringify(parcelsPayload)
        });

        if (!fResponse.ok) {
            const errText = await fResponse.text();
            console.error('Foxpost API error:', errText);
            return res.status(502).json({ error: `Foxpost API error: ${errText}` });
        }

        const resData = await fResponse.json();
        console.log('Foxpost response data:', JSON.stringify(resData, null, 2));
        const createdParcels = resData.parcels || [];
        console.log(`Foxpost successfully created ${createdParcels.length} parcels.`);

        // 4. Update Supabase with the generated barcodes
        const updatedRunIds = [];
        const failedParcels = [];

        for (const p of createdParcels) {
            const barcode = p.clFoxId;
            const refCode = p.refCode;
            const matchedRun = runMap.get(refCode);
            console.log('Mapping parcel:', { barcode, refCode, matchedRunId: matchedRun ? matchedRun.id : null });

            if (!barcode || (p.errors && p.errors.length > 0)) {
                failedParcels.push({
                    serial_number: refCode,
                    recipient: p.recipientName,
                    errors: p.errors || [{ message: 'Nem sikerült csomagszámot generálni' }]
                });
                continue;
            }

            if (matchedRun) {
                // Update shipments record
                const { error: shipErr } = await supabase
                    .from('shipments')
                    .update({
                        tracking_code: barcode,
                        shipped: true,
                        shipped_at: new Date().toISOString()
                    })
                    .eq('run_id', matchedRun.id);

                if (shipErr) {
                    console.error(`Error updating shipment for run ${matchedRun.serial_number}:`, shipErr);
                }

                // Update runs record
                const { error: runErr } = await supabase
                    .from('runs')
                    .update({ shipped: true })
                    .eq('id', matchedRun.id);

                if (runErr) {
                    console.error(`Error updating run ${matchedRun.serial_number}:`, runErr);
                }

                updatedRunIds.push(matchedRun.id);
            }
        }

        return res.status(200).json({
            success: true,
            message: `Successfully created ${updatedRunIds.length} Foxpost parcels and synced to database.`,
            created_count: updatedRunIds.length,
            run_ids: updatedRunIds,
            failed: failedParcels
        });

    } catch (err) {
        console.error('Foxpost parcel creation error:', err);
        return res.status(500).json({ error: err.message });
    }
};
