const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

function formatPhone(phone, fallbackText = '') {
    let raw = phone ? String(phone).trim() : '';

    // If phone is not a valid sequence of digits, attempt to extract from fallbackText
    if (!raw || !raw.match(/\d/)) {
        if (fallbackText) {
            const m = String(fallbackText).match(/(?:(?:\+|00)?36|06)[\s\-]?[1-9]\d[\s\-]?\d{3}[\s\-]?\d{3,4}/);
            if (m) raw = m[0];
        }
    }

    if (!raw) return null;

    let cleaned = raw.replace(/\D/g, '');
    if (cleaned.startsWith('0036')) {
        cleaned = cleaned.substring(2);
    }
    if (cleaned.startsWith('06')) {
        cleaned = '36' + cleaned.substring(2);
    }
    if (!cleaned.startsWith('36') && (cleaned.length === 8 || cleaned.length === 9)) {
        cleaned = '36' + cleaned;
    }

    // Hungarian mobile numbers standard format: +36 (20|30|70|...) XXXXXXX -> length 11 with country code
    if (cleaned.length < 10 || cleaned.length > 12) {
        return null;
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
        // 1. Fetch runs, runners, and shipments from Supabase
        const { data: runs, error: fetchErr } = await supabase
            .from('runs')
            .select('*, runners(name, email, phone, billing_address), shipments(*)')
            .in('id', run_ids);

        if (fetchErr) throw fetchErr;
        if (!runs || runs.length === 0) {
            return res.status(404).json({ error: 'No matching runs found' });
        }

        // 2. Group runs into consolidated packages (multi-medal / ship_together)
        const groups = [];
        for (const run of runs) {
            const runner = run.runners || {};
            const shipment = Array.isArray(run.shipments) ? (run.shipments[0] || {}) : (run.shipments || {});

            // Skip if already shipped
            if (shipment.shipped) {
                console.log(`Skipping already shipped run: ${run.serial_number}`);
                continue;
            }

            const method = shipment.method || run.shipping_method || 'foxpost';
            if (method !== 'foxpost') {
                console.log(`Skipping home delivery run ${run.serial_number} from direct Foxpost locker API`);
                continue;
            }

            const destination = shipment.parcel_id || run.parcel_id || '';
            const email = (runner.email || '').toLowerCase().trim();
            const shipTogether = (run.ship_together_with || '').toLowerCase().trim();

            let foundGroup = null;
            for (const g of groups) {
                const match = g.some(other => {
                    const otherRunner = other.runners || {};
                    const otherShipment = Array.isArray(other.shipments) ? (other.shipments[0] || {}) : (other.shipments || {});
                    const otherDest = otherShipment.parcel_id || other.parcel_id || '';

                    if (destination && otherDest && destination !== otherDest) return false;

                    const otherEmail = (otherRunner.email || '').toLowerCase().trim();
                    const otherShipTogether = (other.ship_together_with || '').toLowerCase().trim();

                    return (
                        (email && otherEmail && email === otherEmail) ||
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

        // 3. Build & Pre-validate parcel creation payloads
        const validParcelsPayload = [];
        const failedParcels = [];
        const runMap = new Map();

        for (const group of groups) {
            const primaryRun = group[0];
            const primaryRunner = primaryRun.runners || {};
            const primaryShipment = Array.isArray(primaryRun.shipments) ? (primaryRun.shipments[0] || {}) : (primaryRun.shipments || {});
            const refCode = group.map(r => r.serial_number).join(', ');

            let recipientName = primaryRun.name || primaryRunner.name || 'Ismeretlen';
            if (recipientName.length > 50) {
                recipientName = recipientName.substring(0, 47) + '...';
            }

            const email = primaryRunner.email || '';

            // Find valid phone across the group (checking shipment, runner phone, and billing_address fallback)
            let phone = null;
            for (const r of group) {
                const rRunner = r.runners || {};
                const rShipment = Array.isArray(r.shipments) ? (r.shipments[0] || {}) : (r.shipments || {});
                phone = formatPhone(rShipment.phone, rRunner.billing_address) ||
                        formatPhone(r.phone, rRunner.billing_address) ||
                        formatPhone(rRunner.phone, rRunner.billing_address);
                if (phone) break;
            }

            const destination = primaryShipment.parcel_id || primaryRun.parcel_id || '';

            // Validation checks before sending to Foxpost API
            const validationErrors = [];
            if (!phone) {
                validationErrors.push({ field: 'phone', message: 'Hiányzó vagy érvénytelen telefonszám (pl. +36301234567 szükséges)' });
            }
            if (!destination) {
                validationErrors.push({ field: 'destination', message: 'Hiányzó Foxpost csomagautomata azonosító' });
            }
            if (!email) {
                validationErrors.push({ field: 'email', message: 'Hiányzó email cím' });
            }

            if (validationErrors.length > 0) {
                failedParcels.push({
                    serial_number: refCode,
                    recipient: recipientName,
                    errors: validationErrors
                });
                continue;
            }

            validParcelsPayload.push({
                recipientName: recipientName,
                recipientEmail: email,
                recipientPhone: phone,
                destination: destination,
                size: "XS",
                cod: 0,
                refCode: refCode,
                comment: ""
            });

            group.forEach(r => {
                runMap.set(r.serial_number, r);
            });
        }

        if (validParcelsPayload.length === 0) {
            return res.status(200).json({
                success: false,
                message: 'Egyetlen csomag sem felelt meg az előzetes ellenőrzésnek (pl. hiányzó telefonszám vagy automata).',
                created_count: 0,
                failed: failedParcels
            });
        }

        // 4. Send valid parcels to Foxpost API
        console.log(`Sending ${validParcelsPayload.length} valid parcels to Foxpost API...`);
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
            body: JSON.stringify(validParcelsPayload)
        });

        if (!fResponse.ok) {
            const errText = await fResponse.text();
            console.error('Foxpost API HTTP error:', errText);
            return res.status(502).json({ error: `Foxpost API error: ${errText}`, failed: failedParcels });
        }

        const resData = await fResponse.json();
        console.log('Foxpost response data:', JSON.stringify(resData, null, 2));
        const returnedParcels = resData.parcels || [];

        // 5. Update Supabase with generated barcodes
        const updatedRunIds = [];

        for (const p of returnedParcels) {
            const barcode = p.clFoxId || p.barcode || p.uniqueBarcode;
            const refCode = p.refCode;

            if (!barcode || (p.errors && p.errors.length > 0)) {
                failedParcels.push({
                    serial_number: refCode,
                    recipient: p.recipientName,
                    errors: p.errors || [{ message: 'A Foxpost nem adott vissza érvényes csomagszámot' }]
                });
                continue;
            }

            const matchedRunSerials = refCode.split(',').map(s => s.trim());
            const matchedRuns = matchedRunSerials.map(s => runMap.get(s)).filter(Boolean);

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

                if (shipErr) console.error(`Error updating shipments for serials [${refCode}]:`, shipErr);

                // Update runs records
                const { error: runErr } = await supabase
                    .from('runs')
                    .update({ shipped: true })
                    .in('id', runIdsToUpdate);

                if (runErr) console.error(`Error updating runs for serials [${refCode}]:`, runErr);

                updatedRunIds.push(...runIdsToUpdate);
            }
        }

        return res.status(200).json({
            success: updatedRunIds.length > 0,
            message: `${updatedRunIds.length} db csomag sikeresen feladva és szinkronizálva a Foxpostból.`,
            created_count: updatedRunIds.length,
            run_ids: updatedRunIds,
            failed: failedParcels
        });

    } catch (err) {
        console.error('Foxpost parcel creation error:', err);
        return res.status(500).json({ error: err.message });
    }
};
