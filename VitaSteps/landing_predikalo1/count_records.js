const fs = require('fs');
const path = require('path');

const envContent = fs.readFileSync(path.join(__dirname, '.env'), 'utf8');
envContent.split('\n').forEach(line => {
    const parts = line.split('=');
    if (parts.length >= 2) {
        const key = parts[0].trim();
        const val = parts.slice(1).join('=').trim().replace(/^"|"$/g, '').replace(/^'|'$/g, '');
        process.env[key] = val;
    }
});

const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

async function inspectNullCampaignRuns() {
    try {
        console.log('--- Inspecting Remaining Null-Campaign runs ---');
        
        const { data: runs, error: ruErr } = await supabase
            .from('runs')
            .select('id, serial_number, name, completed, is_test, campaign')
            .is('campaign', null);

        if (ruErr) {
            console.error('Error fetching runs:', ruErr);
            return;
        }

        console.log(`Found ${runs.length} runs with null campaign:`);
        console.log(JSON.stringify(runs, null, 2));

    } catch (err) {
        console.error('Inspect error:', err);
    }
}
inspectNullCampaignRuns();
