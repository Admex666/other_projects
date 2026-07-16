const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Manually parse .env
const envPath = path.join(__dirname, '..', '.env');
const envConfig = fs.readFileSync(envPath, 'utf-8');
const env = {};
envConfig.split('\n').forEach(line => {
    const parts = line.split('=');
    if (parts.length >= 2) {
        const key = parts[0].trim();
        const val = parts.slice(1).join('=').trim();
        env[key] = val;
    }
});

const supabaseUrl = env.SUPABASE_URL;
const supabaseKey = env.SUPABASE_SERVICE_ROLE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

async function markCompleted() {
    const email = 'admexgm@gmail.com';
    
    // First, inspect
    const { data: runners, error: getError } = await supabase
        .from('runners')
        .select('*')
        .eq('email', email);

    if (getError) {
        console.error("Error fetching runner:", getError);
        return;
    }

    if (runners.length === 0) {
        console.log(`No runner found for ${email}, creating a new one...`);
        // Let's create one if not exists
        const today = new Date().toISOString().split('T')[0];
        const { data: inserted, error: insertError } = await supabase
            .from('runners')
            .insert({
                email: email,
                name: 'Próba Jani',
                completed: true,
                completion_date: today,
                shipped: true,
                received_date: today,
                serial_number: '#042/100',
                distance_km: 10,
                is_test: true
            })
            .select();
        if (insertError) {
            console.error("Error creating runner:", insertError);
        } else {
            console.log("Successfully created Prédikálószék runner:", inserted);
        }
        return;
    }

    const runner = runners[0];
    console.log("Found runner:", runner);

    // Update runner to be a completed Prédikálószék runner (no PK in serial_number)
    const today = new Date().toISOString().split('T')[0];
    const { data: updated, error: updateError } = await supabase
        .from('runners')
        .update({
            name: 'Próba Jani',
            completed: true,
            completion_date: today,
            shipped: true,
            received_date: today,
            serial_number: '#042/100', // Prédikálószék format (no 'PK')
            distance_km: 10
        })
        .eq('id', runner.id)
        .select();

    if (updateError) {
        console.error("Error updating runner:", updateError);
    } else {
        console.log("Successfully updated runner to completed Prédikálószék runner:", updated);
    }
}

markCompleted();
