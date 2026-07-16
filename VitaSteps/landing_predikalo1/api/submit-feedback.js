const { google } = require('googleapis');
const { createClient } = require('@supabase/supabase-js');

// Initialize Supabase Client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

module.exports = async (req, res) => {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    // Authenticate user via authorization header
    const authHeader = req.headers.authorization;
    if (!authHeader) {
        return res.status(401).json({ error: 'No authorization header provided.' });
    }

    const token = authHeader.split(' ')[1];
    let user;
    try {
        const { data, error: authError } = await supabase.auth.getUser(token);
        if (authError || !data.user) {
            return res.status(401).json({ error: 'Unauthorized user token.' });
        }
        user = data.user;
    } catch (err) {
        return res.status(401).json({ error: 'Token validation failed.' });
    }

    const email = user.email.toLowerCase();

    try {
        const {
            erem_minoseg,
            szallitas_elegedett,
            reszvetel_ujra,
            nps_score,
            kovetkezo_tajegyseg,
            tetszett_legjobban,
            jobba_tenne,
            photo_url
        } = req.body;

        console.log(`Received feedback submission from ${email}...`);

        const { data: existingFeedback, error: checkError } = await supabase
            .from('feedbacks')
            .select('id')
            .eq('run_id', req.body.run_id)
            .maybeSingle();

        if (checkError) throw checkError;

        if (existingFeedback) {
            console.log(`Feedback for run ${req.body.run_id} already exists. Skipping duplicate write.`);
            return res.status(200).json({ success: true, message: 'Feedback already submitted.' });
        }

        // 1. Save feedback to Supabase Database
        const { error: dbError } = await supabase
            .from('feedbacks')
            .insert({
                runner_email: email,
                run_id: req.body.run_id || null,
                erem_minoseg: parseInt(erem_minoseg),
                szallitas_elegedett: parseInt(szallitas_elegedett),
                reszvetel_ujra: reszvetel_ujra,
                nps_score: parseInt(nps_score),
                kovetkezo_tajegyseg: kovetkezo_tajegyseg,
                tetszett_legjobban: tetszett_legjobban || null,
                jobba_tenne: jobba_tenne || null,
                photo_url: photo_url || null
            });

        if (dbError) {
            throw dbError;
        }

        // 2. Write to Google Sheets
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

        // Fetch user name from 'Nevezések' to populate sheet
        const nezvesekResponse = await sheets.spreadsheets.values.get({
            spreadsheetId: sheetId,
            range: 'Nevezések!A1:Z500',
        });
        const nevesekRows = nezvesekResponse.data.values || [];
        
        let runnerName = '';
        let rowIdxToUpdate = -1;
        let colFollowupIdx = -1;

        if (nevesekRows.length > 0) {
            const headers = nevesekRows[0];
            const colEmail = headers.findIndex(h => h.trim().toLowerCase() === 'email');
            const colName = headers.findIndex(h => h.trim().toLowerCase() === 'név');
            colFollowupIdx = headers.findIndex(h => h.trim().toLowerCase() === 'follow-up email?');

            if (colEmail !== -1) {
                for (let i = 1; i < nevesekRows.length; i++) {
                    const row = nevesekRows[i];
                    if (row[colEmail] && row[colEmail].trim().toLowerCase() === email) {
                        runnerName = colName !== -1 ? (row[colName] || '') : '';
                        rowIdxToUpdate = i + 1; // 1-based index (including header)
                        break;
                    }
                }
            }
        }

        if (email === 'admexgm@gmail.com') {
            runnerName = 'Admex Dev';
        }

        // Write to 'feedback_raw' sheet
        const feedbackSheetName = 'feedback_raw';
        const feedbackResponse = await sheets.spreadsheets.values.get({
            spreadsheetId: sheetId,
            range: `${feedbackSheetName}!A1:Z100`,
        });

        const feedbackRows = feedbackResponse.data.values || [];
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);

        // If sheet is empty, write headers first
        if (feedbackRows.length === 0) {
            const defaultHeaders = [
                'Timestamp', 'Email', 'Név', 'Érem minősége', 'Szállítás zökkenőmentes', 
                'Új részvétel', 'NPS Ajánlás (0-10)', 'Következő tájegység', 
                'Mi tetszett legjobban', 'Mi tenné jobbá', 'Kép URL'
            ];
            await sheets.spreadsheets.values.update({
                spreadsheetId: sheetId,
                range: `${feedbackSheetName}!A1`,
                valueInputOption: 'RAW',
                body: { values: [defaultHeaders] },
            });
        }

        // Append feedback row
        const newFeedbackRow = [
            timestamp, email, runnerName, erem_minoseg, szallitas_elegedett,
            reszvetel_ujra, nps_score, kovetkezo_tajegyseg,
            tetszett_legjobban || '', jobba_tenne || '', photo_url || ''
        ];

        await sheets.spreadsheets.values.append({
            spreadsheetId: sheetId,
            range: `${feedbackSheetName}!A:A`,
            valueInputOption: 'RAW',
            body: { values: [newFeedbackRow] },
        });

        // 3. Mark 'follow-up email?' as 'Igen' in 'Nevezések' to prevent double emailing
        if (rowIdxToUpdate !== -1 && colFollowupIdx !== -1) {
            const colLetter = chrLetter(colFollowupIdx);
            await sheets.spreadsheets.values.update({
                spreadsheetId: sheetId,
                range: `Nevezések!${colLetter}${rowIdxToUpdate}`,
                valueInputOption: 'RAW',
                body: { values: [['Igen']] },
            });
        }

        res.status(200).json({ success: true, message: 'Feedback successfully submitted.' });
    } catch (err) {
        console.error('Submit feedback error:', err);
        res.status(500).json({ error: err.message });
    }
};

// Helper function to convert column index to letters (0-indexed A, B, C...)
function chrLetter(idx) {
    if (idx < 26) {
        return String.fromCharCode(65 + idx);
    } else {
        return String.fromCharCode(64 + Math.floor(idx / 26)) + String.fromCharCode(65 + (idx % 26));
    }
}
