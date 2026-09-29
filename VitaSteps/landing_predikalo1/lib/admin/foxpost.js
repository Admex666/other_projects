const { createClient } = require('@supabase/supabase-js');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../../.env') });
require('dotenv').config();

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

function formatPhone(phone, fallbackText = '') {
    let raw = phone ? String(phone).trim() : '';

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

    if (cleaned.length < 10 || cleaned.length > 12) {
        return null;
    }

    return `+${cleaned}`;
}

function parseHungarianAddress(rawAddress) {
    if (!rawAddress || typeof rawAddress !== 'string') return null;
    const str = rawAddress.trim();
    if (!str) return null;

    // 1. Extract 4-digit Hungarian postal code
    const zipMatch = str.match(/\b(\d{4})\b/);
    if (!zipMatch) return null;
    const zip = zipMatch[1];

    // Remove zip from address string
    let rest = str.replace(zip, '').replace(/^[, -]+|[, -]+$/g, '').trim();

    // 2. Extract city and street address
    let city = '';
    let address = '';

    if (rest.includes(',')) {
        const parts = rest.split(',').map(p => p.trim()).filter(Boolean);
        const streetKeywords = /\b(utca|út|tér|körút|krt|fasor|köz|sor|sétány|dűlő|major|tanya|ltp|lakótelep|telep|u\.|krt\.|rkp|rakpart|sgt|sugárút)\b/i;
        if (parts.length >= 2) {
            if (!streetKeywords.test(parts[0])) {
                city = parts[0];
                address = parts.slice(1).join(', ');
            } else if (!streetKeywords.test(parts[parts.length - 1])) {
                city = parts[parts.length - 1];
                address = parts.slice(0, -1).join(', ');
            } else {
                city = parts[0];
                address = parts.slice(1).join(', ');
            }
        } else {
            address = parts[0] || '';
        }
    } else {
        const tokens = rest.split(/\s+/).filter(Boolean);
        if (tokens.length >= 2) {
            city = tokens[0];
            address = tokens.slice(1).join(' ');
        } else {
            address = rest;
        }
    }

    city = city.replace(/^[, -]+|[, -]+$/g, '').trim();
    address = address.replace(/^[, -]+|[, -]+$/g, '').trim();

    if (!city || !address) return null;

    if (city.length > 25) city = city.substring(0, 25);
    if (address.length > 150) address = address.substring(0, 150);

    return { zip, city, address };
}

async function handleFoxpostCreation(req, res) {
    const { run_ids, address_overrides } = req.body;

    if (!run_ids || !Array.isArray(run_ids) || run_ids.length === 0) {
        return res.status(400).json({ error: 'run_ids (non-empty array) is required' });
    }

    // Build lookup map for user-confirmed/edited address overrides
    const overridesMap = new Map();
    if (address_overrides && typeof address_overrides === 'object') {
        if (Array.isArray(address_overrides)) {
            address_overrides.forEach(ov => {
                if (ov.run_id) overridesMap.set(String(ov.run_id), ov);
                if (ov.serial_number) overridesMap.set(String(ov.serial_number), ov);
                if (ov.run_ids && Array.isArray(ov.run_ids)) {
                    ov.run_ids.forEach(id => overridesMap.set(String(id), ov));
                }
            });
        } else {
            Object.entries(address_overrides).forEach(([key, val]) => {
                overridesMap.set(String(key), val);
            });
        }
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
            const isHome = method === 'home';
            const destination = isHome
                ? (shipment.home_address || shipment.target_address || runner.billing_address || '')
                : (shipment.parcel_id || run.parcel_id || '');

            const email = (runner.email || '').toLowerCase().trim();
            const shipTogether = (run.ship_together_with || '').toLowerCase().trim();

            let foundGroup = null;
            for (const g of groups) {
                const match = g.some(other => {
                    const otherRunner = other.runners || {};
                    const otherShipment = Array.isArray(other.shipments) ? (other.shipments[0] || {}) : (other.shipments || {});
                    const otherMethod = otherShipment.method || other.shipping_method || 'foxpost';

                    // Locker and Home Delivery cannot be merged into the same parcel
                    if (method !== otherMethod) return false;

                    const otherIsHome = otherMethod === 'home';
                    const otherDest = otherIsHome
                        ? (otherShipment.home_address || otherShipment.target_address || otherRunner.billing_address || '')
                        : (otherShipment.parcel_id || other.parcel_id || '');

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
        const groupMap = new Map();

        for (const group of groups) {
            group.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
            const primaryRun = group[0];
            const primaryRunner = primaryRun.runners || {};
            const primaryShipment = Array.isArray(primaryRun.shipments) ? (primaryRun.shipments[0] || {}) : (primaryRun.shipments || {});
            const method = primaryShipment.method || primaryRun.shipping_method || 'foxpost';
            const isHome = method === 'home';

            // Foxpost WebAPI strictly enforces maxLength: 30 on refCode
            let refCode = group.map(r => r.serial_number).join(',');
            if (refCode.length > 30) {
                if (group.length > 1) {
                    refCode = `${primaryRun.serial_number}+${group.length - 1}`;
                }
                if (refCode.length > 30) {
                    refCode = refCode.substring(0, 30);
                }
            }

            let recipientName = primaryRun.name || primaryRunner.billing_name || primaryRunner.name || 'Ismeretlen';
            if (recipientName.length > 50) {
                recipientName = recipientName.substring(0, 47) + '...';
            }

            const email = primaryRunner.email || '';

            let phone = null;
            for (const r of group) {
                const rRunner = r.runners || {};
                const rShipment = Array.isArray(r.shipments) ? (r.shipments[0] || {}) : (r.shipments || {});
                phone = formatPhone(rShipment.phone, rRunner.billing_address) ||
                        formatPhone(r.phone, rRunner.billing_address) ||
                        formatPhone(rRunner.phone, rRunner.billing_address);
                if (phone) break;
            }

            const validationErrors = [];
            if (!phone) {
                validationErrors.push({ field: 'phone', message: 'Hiányzó vagy érvénytelen telefonszám (pl. +36301234567 szükséges)' });
            }
            if (!email) {
                validationErrors.push({ field: 'email', message: 'Hiányzó email cím' });
            }

            let parcelItem = null;

            if (isHome) {
                // Check if user provided an override for any run in this group
                let override = null;
                for (const r of group) {
                    if (overridesMap.has(String(r.id))) { override = overridesMap.get(String(r.id)); break; }
                    if (overridesMap.has(String(r.serial_number))) { override = overridesMap.get(String(r.serial_number)); break; }
                }
                if (!override && overridesMap.has(refCode)) {
                    override = overridesMap.get(refCode);
                }

                let zip = '';
                let city = '';
                let address = '';

                if (override && override.zip && override.city && override.address) {
                    zip = String(override.zip).trim();
                    city = String(override.city).trim().substring(0, 25);
                    address = String(override.address).trim().substring(0, 150);
                } else {
                    let rawAddress = primaryShipment.home_address || primaryShipment.target_address || primaryRunner.billing_address || primaryRun.home_address || '';
                    if (!rawAddress) {
                        for (const r of group) {
                            const rRunner = r.runners || {};
                            const rShipment = Array.isArray(r.shipments) ? (r.shipments[0] || {}) : (r.shipments || {});
                            rawAddress = rShipment.home_address || rShipment.target_address || rRunner.billing_address || r.home_address || '';
                            if (rawAddress) break;
                        }
                    }

                    const parsedAddr = parseHungarianAddress(rawAddress);
                    if (parsedAddr) {
                        zip = parsedAddr.zip;
                        city = parsedAddr.city;
                        address = parsedAddr.address;
                    }
                }

                if (!zip || !city || !address) {
                    validationErrors.push({
                        field: 'recipientAddress',
                        message: `Hiányzó vagy érvénytelen házhozszállítási cím (Irányítószám, Város, Utca házszám szükséges)`
                    });
                } else {
                    parcelItem = {
                        recipientName: recipientName,
                        recipientEmail: email,
                        recipientPhone: phone,
                        recipientZip: zip,
                        recipientCity: city,
                        recipientAddress: address,
                        recipientCountry: 'HU',
                        size: 'XS',
                        cod: 0,
                        refCode: refCode,
                        comment: ''
                    };
                }
            } else {
                const destination = primaryShipment.parcel_id || primaryRun.parcel_id || '';
                if (!destination) {
                    validationErrors.push({ field: 'destination', message: 'Hiányzó Foxpost csomagautomata azonosító' });
                } else {
                    parcelItem = {
                        recipientName: recipientName,
                        recipientEmail: email,
                        recipientPhone: phone,
                        destination: destination,
                        size: 'XS',
                        cod: 0,
                        refCode: refCode,
                        comment: ''
                    };
                }
            }

            if (validationErrors.length > 0 || !parcelItem) {
                failedParcels.push({
                    serial_number: refCode,
                    recipient: recipientName,
                    errors: validationErrors
                });
                continue;
            }

            validParcelsPayload.push(parcelItem);

            const enrichedGroup = group.map(r => ({
                ...r,
                _parsedAddress: isHome ? { zip: parcelItem.recipientZip, city: parcelItem.recipientCity, address: parcelItem.recipientAddress } : null
            }));

            groupMap.set(refCode, enrichedGroup);
        }

        if (validParcelsPayload.length === 0) {
            return res.status(200).json({
                success: false,
                message: 'Egyetlen csomag sem felelt meg az előzetes ellenőrzésnek (pl. hiányzó telefonszám, automata azonosító vagy lakcím).',
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
        console.log('Foxpost API response body:', JSON.stringify(resData, null, 2));
        const returnedParcels = resData.parcels || [];

        // 5. Update Supabase with generated barcodes
        const updatedRunIds = [];

        for (const p of returnedParcels) {
            const barcode = p.clFoxId || p.barcode || p.uniqueBarcode;
            const refCode = p.refCode;

            if (!barcode || (p.errors && p.errors.length > 0)) {
                const formattedErrors = (p.errors || []).map(e => (typeof e === 'object' && e.message) ? `${e.field || ''}: ${e.message}`.trim() : String(e));
                failedParcels.push({
                    serial_number: refCode,
                    recipient: p.recipientName || 'Ismeretlen',
                    errors: formattedErrors.length > 0 ? formattedErrors : [{ message: 'A Foxpost nem adott vissza érvényes csomagszámot' }]
                });
                continue;
            }

            const matchedRuns = groupMap.get(refCode) || [];

            if (matchedRuns.length > 0) {
                const runIdsToUpdate = matchedRuns.map(r => r.id);

                const shipmentUpdatePayload = {
                    tracking_code: barcode,
                    shipped: true,
                    shipped_at: new Date().toISOString()
                };

                const firstMatched = matchedRuns[0];
                if (firstMatched && firstMatched._parsedAddress) {
                    const pAddr = firstMatched._parsedAddress;
                    shipmentUpdatePayload.home_address = `${pAddr.zip} ${pAddr.city}, ${pAddr.address}`;
                }

                // Update shipments records
                const { error: shipErr } = await supabase
                    .from('shipments')
                    .update(shipmentUpdatePayload)
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
}

module.exports = {
    handleFoxpostCreation
};
