const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Read .env manually
const envPath = path.join(__dirname, '..', '.env');
const envVars = {};
if (fs.existsSync(envPath)) {
    const lines = fs.readFileSync(envPath, 'utf8').split('\n');
    for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
            const [key, val] = trimmed.split('=', 2);
            envVars[key.trim()] = val.trim().replace(/^["']|["']$/g, '');
        }
    }
}

const supabase = createClient(envVars.SUPABASE_URL, envVars.SUPABASE_SERVICE_ROLE_KEY);

async function check() {
    // Fetch schema details of the 'runs' table via rpc or SQL
    // Since PostgREST doesn't expose direct SQL, we can fetch a single row to see all returned properties!
    const { data: runs, error } = await supabase
        .from('runs')
        .select('*')
        .limit(1);

    if (error) {
        console.error('Error fetching runs:', error);
    } else {
        console.log('Columns in runs table row:', Object.keys(runs[0] || {}));
    }
}
check();
