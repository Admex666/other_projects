const { createClient } = require('@supabase/supabase-js');

// Initialize Supabase Client with Service Role
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

module.exports = async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    // Authenticate user via authorization header if present
    const authHeader = req.headers.authorization;
    let userEmail = null;

    if (authHeader && authHeader.startsWith('Bearer ')) {
        const token = authHeader.split(' ')[1];
        try {
            const { data, error: authError } = await supabase.auth.getUser(token);
            if (!authError && data?.user) {
                userEmail = data.user.email?.toLowerCase();
            }
        } catch (err) {
            console.warn('Token verification warning:', err.message);
        }
    }

    try {
        const { run_id, run_ids, proof_urls, ship_together_with } = req.body;

        if (!run_id && (!run_ids || run_ids.length === 0)) {
            return res.status(400).json({ error: 'run_id vagy run_ids megadása kötelező.' });
        }

        const targetIds = Array.from(new Set([
            ...(run_id ? [run_id] : []),
            ...(Array.isArray(run_ids) ? run_ids : [])
        ]));

        if (!proof_urls || !Array.isArray(proof_urls) || proof_urls.length === 0) {
            return res.status(400).json({ error: 'Legalább egy igazolás URL szükséges.' });
        }

        console.log(`[submit-proof] Submitting proof for runs: ${targetIds.join(', ')} by user ${userEmail || 'unknown'}`);

        // Update runs using service role client
        const updatePayload = {
            proof_submitted: true,
            proof_urls: proof_urls,
            proof_submitted_at: new Date().toISOString(),
            ship_together_with: ship_together_with ? ship_together_with.trim().toLowerCase() : null
        };

        const { data, error: dbError } = await supabase
            .from('runs')
            .update(updatePayload)
            .in('id', targetIds)
            .select('id, serial_number, name');

        if (dbError) {
            console.error('[submit-proof] DB error:', dbError);
            throw new Error('Adatbázis hiba az igazolás rögzítésekor: ' + dbError.message);
        }

        console.log(`[submit-proof] Successfully updated ${data?.length || 0} run(s).`);

        return res.status(200).json({
            success: true,
            message: 'Igazolás sikeresen elmentve!',
            updated_runs: data
        });

    } catch (err) {
        console.error('[submit-proof] Exception:', err);
        return res.status(500).json({ error: err.message || 'Belső szerverhiba' });
    }
};
