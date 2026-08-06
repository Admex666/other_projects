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

        // 2. Group runs into consolidated packages
        const groups = [];
        for (const run of runs) {
            const runner = run.runners || {};
            const shipment = Array.isArray(run.shipments) ? (run.shipments[0] || {}) : (run.shipments || {});

            // Skip if already shipped (to prevent duplicate parcel creation on Foxpost)
            if (shipment.shipped) {
                console.log(`Skipping already shipped run: ${run.serial_number}`);
                continue;
            }

            const method = shipment.method || run.shipping_method || 'foxpost';
            if (method !== 'foxpost') {
                console.log(`Skipping home delivery run ${run.serial_number} from direct Foxpost API upload`);
                continue; // Foxpost bulk API only supports parcel lockers
            }

            const destination = shipment.parcel_id || run.parcel_id || '';
            if (!destination) {
                console.warn(`No destination locker ID found for run ${run.serial_number}`);
                continue;
            }

            const email = (runner.email || '').toLowerCase().trim();
            const shipTogether = (run.ship_together_with || '').toLowerCase().trim();

            // Try to find an existing group that matches
            let foundGroup = null;
            for (const g of groups) {
                const match = g.some(other => {
                    const otherRunner = other.runners || {};
                    const otherShipment = Array.isArray(other.shipments) ? (other.shipments[0] || {}) : (other.shipments || {});
                    const otherDest = otherShipment.parcel_id || other.parcel_id || '';

                    // Campaign must match
                    const runCampaign = run.campaign || 'predikaloszek';
                    const otherCampaign = other.campaign || 'predikaloszek';
                    if (runCampaign !== otherCampaign) return false;

                    // Destination locker must match
                    if (destination !== otherDest) return false;

                    const otherEmail = (otherRunner.email || '').toLowerCase().trim();
                    const otherShipTogether = (other.ship_together_with || '').toLowerCase().trim();

                    // Same email, or bidirectional ship_together_with link
                    return (
                        email === otherEmail ||
                        (shipTogether && shipTogether === otherEmail) ||
                        (otherShipTogether && otherShipTogether === email) ||
                        (shipTogether && otherShipTogether && shipTogether === otherShipTogether)
                    );
                });

                if (match) {
                    foundGroup = g;
                    break;
                }
            }

            if (foundGroup) {
                foundGroup.push(run);
            } else {
                groups.push([run]);
            }
        }

        // 3. Build parcel creation payload for Foxpost API
        const parcelsPayload = [];
        const runMap = new Map(); // to lookup runs by serial number later

        for (const group of groups) {
            // Representative run (we take the first run as the primary contact)
            const primaryRun = group[0];
            const primaryRunner = primaryRun.runners || {};
            const primaryShipment = Array.isArray(primaryRun.shipments) ? (primaryRun.shipments[0] || {}) : (primaryRun.shipments || {});

            // Recipient name: always the first member only
            let recipientName = primaryRun.name || primaryRunner.name || 'Ismeretlen';
            if (recipientName.length > 50) {
                recipientName = recipientName.substring(0, 47) + '...';
            }

            // Recipient email: first person's email
            const email = primaryRunner.email || '';

            // Recipient phone: find a valid phone in the group
            let rawPhone = '';
            for (const r of group) {
                const rShipment = Array.isArray(r.shipments) ? (r.shipments[0] || {}) : (r.shipments || {});
                rawPhone = rShipment.phone || r.phone || r.runners?.phone || '';
                if (rawPhone) break;
            }
            const phone = formatPhone(rawPhone);

            const destination = primaryShipment.parcel_id || primaryRun.parcel_id || '';

            // RefCode: join serial numbers of all group runs (comma separated)
            const refCode = group.map(r => r.serial_number).join(', ');

            parcelsPayload.push({
                recipientName: recipientName,
                recipientEmail: email,
                recipientPhone: phone,
                destination: destination,
                size: "XS",
                cod: 0,
                refCode: refCode,
                comment: ""
            });

            // Map each run in the group to the runMap so we can resolve them when barcodes are returned
            group.forEach(r => {
                runMap.set(r.serial_number, r);
            });
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

            const matchedRunSerials = refCode.split(',').map(s => s.trim());
            const matchedRuns = matchedRunSerials.map(s => runMap.get(s)).filter(Boolean);
            console.log('Mapping parcel:', { barcode, refCode, matchedCount: matchedRuns.length });

            if (matchedRuns.length > 0) {
                const runIdsToUpdate = matchedRuns.map(r => r.id);

                // Update shipments records
                const { error: shipErr } = await supabase
                    .from('shipments')
                    .update({
                        tracking_code: barcode,
                        shipped: true,
                        shipped_at: new Date().toISOString()
                    })
                    .in('run_id', runIdsToUpdate);

                if (shipErr) {
                    console.error(`Error updating shipments for serials [${refCode}]:`, shipErr);
                }

                // Update runs records
                const { error: runErr } = await supabase
                    .from('runs')
                    .update({ shipped: true })
                    .in('id', runIdsToUpdate);

                if (runErr) {
                    console.error(`Error updating runs for serials [${refCode}]:`, runErr);
                }

                updatedRunIds.push(...runIdsToUpdate);
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
