const { google } = require('googleapis');
const { createClient } = require('@supabase/supabase-js');

// Initialize Supabase Client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

module.exports = async (req, res) => {
    // We allow GET (triggered manually or by cron) or POST
    if (req.method !== 'GET' && req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        console.log('Starting synchronization: Google Sheets -> Supabase...');

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
        const response = await sheets.spreadsheets.values.get({
            spreadsheetId: sheetId,
            range: `${sheetName}!A1:AH500`,
        });

        const rows = response.data.values;
        if (!rows || rows.length < 2) {
            return res.status(200).json({ success: true, message: 'No rows found in sheet.' });
        }

        const headers = rows[0];
        const findCol = (name, defaultIdx) => {
            const idx = headers.findIndex(h => h.trim().toLowerCase() === name.toLowerCase().trim());
            return idx !== -1 ? idx : defaultIdx;
        };

        const colSerial = findCol("#", 0);
        const colEmail = findCol("email", 3);
        const colName = findCol("név", 4);
        const colTeljesitve = findCol("teljesítve dátum", 12);
        const colDistance = findCol("tény táv?", 13);
        const colShipped = findCol("érem kiküldve?", 24);
        const colReceived = findCol("érem átvéve", 26); // Will match the dynamically created column index
        const colReferredBy = findCol("ajánló email", -1);

        const dataRows = rows.slice(1);
        const runnersToUpsert = [];

        for (const row of dataRows) {
            // Safe helper to read row cell
            const colVal = (idx) => (idx < row.length ? (row[idx] || '').toString().trim() : '');

            const email = colVal(colEmail);
            const name = colVal(colName);
            if (!email || !name) continue;

            const serial = colVal(colSerial);
            const completedDate = colVal(colTeljesitve);
            const distanceRaw = colVal(colDistance);
            const shippedVal = colVal(colShipped);
            const receivedDate = colVal(colReceived);
            const referredBy = colReferredBy !== -1 ? colVal(colReferredBy) : '';

            const completed = !!completedDate;
            const shipped = !!shippedVal && !["", "#n/a", "#name?", "#value!", "nem", "no", "false", "0"].includes(shippedVal.toLowerCase());
            
            // Try to parse distance to number
            let distanceKm = parseFloat(distanceRaw.replace(',', '.'));
            if (isNaN(distanceKm)) {
                distanceKm = null;
            }

            runnersToUpsert.push({
                email: email.toLowerCase(),
                name: name,
                completed: completed,
                completion_date: completedDate || null,
                shipped: shipped,
                received_date: receivedDate || null,
                raw_serial: serial,
                serial_number: null,
                distance_km: distanceKm,
                referred_by: referredBy.toLowerCase().trim() || null
            });
        }

        // Separate completed and non-completed runners
        const completedRunners = [];
        const nonCompletedRunners = [];

        for (const runner of runnersToUpsert) {
            if (runner.completed) {
                completedRunners.push(runner);
            } else {
                nonCompletedRunners.push(runner);
            }
        }

        // Sort completed runners based on completion date ascending, then '#' ascending
        const normalizeDate = (d) => {
            if (!d) return '';
            return d.replace(/\s+/g, '').replace(/\.$/, '');
        };

        completedRunners.sort((a, b) => {
            const dateA = normalizeDate(a.completion_date);
            const dateB = normalizeDate(b.completion_date);
            if (dateA !== dateB) {
                return dateA.localeCompare(dateB);
            }
            const serialA = parseInt(a.raw_serial) || 0;
            const serialB = parseInt(b.raw_serial) || 0;
            return serialA - serialB;
        });

        // Assign rank-based serial numbers (always out of 100)
        completedRunners.forEach((runner, idx) => {
            const rank = idx + 1;
            const paddedRank = rank.toString().padStart(3, '0');
            runner.serial_number = `#${paddedRank}/100`;
        });

        // Recombine and clean raw_serial
        const finalRunnersToUpsert = [
            ...completedRunners,
            ...nonCompletedRunners
        ];

        finalRunnersToUpsert.forEach(r => {
            delete r.raw_serial;
        });

        // Append hardcoded dev user to ensure they can always log in and test
        finalRunnersToUpsert.push({
            email: 'admexgm@gmail.com',
            name: 'Admex Dev',
            completed: true,
            completion_date: '2026.06.30',
            shipped: true,
            received_date: '2026.06.30',
            serial_number: '#999/100',
            distance_km: 15,
            referred_by: null
        });

        // Deduplicate runners by email to avoid ON CONFLICT DO UPDATE constraint violations
        const runnersMap = new Map();
        for (const runner of finalRunnersToUpsert) {
            const emailKey = runner.email.toLowerCase();
            if (runnersMap.has(emailKey)) {
                const existing = runnersMap.get(emailKey);
                if (!existing.completed && runner.completed) {
                    runnersMap.set(emailKey, runner);
                } else if (existing.completed && runner.completed) {
                    if (!existing.serial_number && runner.serial_number) {
                        runnersMap.set(emailKey, runner);
                    }
                }
            } else {
                runnersMap.set(emailKey, runner);
            }
        }
        const deduplicatedRunners = Array.from(runnersMap.values());

        console.log(`Parsed and ranked ${deduplicatedRunners.length} unique runners from Sheet. Syncing with Supabase...`);

        // Batch upsert to Supabase
        const { data, error } = await supabase
            .from('runners')
            .upsert(deduplicatedRunners, { onConflict: 'email' });

        if (error) {
            throw error;
        }

        res.status(200).json({
            success: true,
            message: `Successfully synchronized ${runnersToUpsert.length} runners to Supabase.`
        });
    } catch (err) {
        console.error('Sync error:', err);
        res.status(500).json({ error: err.message });
    }
};
