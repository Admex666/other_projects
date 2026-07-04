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
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate');

        const campaign = req.query.campaign || 'predikaloszek';
        const isPilis = campaign === 'pilis';

        const response = await sheets.spreadsheets.values.get({
            spreadsheetId: sheetId,
            range: `${sheetName}!A2:AJ500`,
        });

        const rows = response.data.values || [];
        
        let paidCount = 0;
        for (const row of rows) {
            if (row.length > 9) {
                const rowCampaign = (row[2] || '').toString().trim().toLowerCase();
                const rowPaid = (row[9] || '').toString().trim();
                
                if (rowPaid !== '') {
                    if (isPilis && rowCampaign.includes('pilis')) {
                        paidCount++;
                    } else if (!isPilis && !rowCampaign.includes('pilis')) {
                        paidCount++;
                    }
                }
            }
        }

        const limit = isPilis ? 100 : 99;
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
