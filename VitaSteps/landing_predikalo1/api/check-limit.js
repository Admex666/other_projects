const { google } = require('googleapis');

// Initialize Google Sheets auth
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

module.exports = async (req, res) => {
    // Only allow GET requests
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        // Cache the response at edge for 30 seconds to prevent hitting Google API rate limits
        res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate');

        // Fetch just the 'fizetett' column (Column J)
        const response = await sheets.spreadsheets.values.get({
            spreadsheetId: sheetId,
            range: `${sheetName}!J2:J500`,
        });

        const rows = response.data.values || [];
        
        // Count non-empty values
        let paidCount = 0;
        for (const row of rows) {
            if (row && row.length > 0 && row[0] && row[0].trim() !== '') {
                paidCount++;
            }
        }

        const limit = 99;
        const closed = paidCount >= limit;

        return res.status(200).json({
            success: true,
            count: paidCount,
            limit: limit,
            closed: closed
        });
    } catch (err) {
        console.error('Error checking checkout limit:', err);
        return res.status(500).json({ error: err.message });
    }
};
