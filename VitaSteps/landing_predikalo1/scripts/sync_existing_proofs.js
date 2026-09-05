const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function syncProofs() {
    console.log('--- Starting Proof Synchronization ---');

    // 1. List all folders in medals/proofs
    const { data: folders, error: listErr } = await supabase.storage
        .from('medals')
        .list('proofs', { limit: 100 });

    if (listErr) {
        console.error('Error listing storage proofs:', listErr);
        return;
    }

    console.log(`Found ${folders.length} folders in proofs/`);

    for (const folder of folders) {
        const runId = folder.name;
        // Check if runId is a valid UUID
        if (!runId.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)) {
            continue;
        }

        // List files in this run's folder
        const { data: files, error: filesErr } = await supabase.storage
            .from('medals')
            .list(`proofs/${runId}`, { limit: 100, sortBy: { column: 'created_at', order: 'asc' } });

        if (filesErr || !files || files.length === 0) {
            console.log(`Folder ${runId} has no files or error.`);
            continue;
        }

        // Generate public URLs for each file
        const publicUrls = files.map(file => {
            const { data } = supabase.storage
                .from('medals')
                .getPublicUrl(`proofs/${runId}/${file.name}`);
            return data.publicUrl;
        });

        const latestFile = files[files.length - 1];
        const submittedAt = latestFile.created_at || new Date().toISOString();

        // Check current run record
        const { data: run, error: fetchErr } = await supabase
            .from('runs')
            .select('id, serial_number, name, completed, proof_submitted, proof_urls, runners(name, email)')
            .eq('id', runId)
            .maybeSingle();

        if (fetchErr || !run) {
            console.log(`No run found for ID: ${runId}`);
            continue;
        }

        const runnerName = run.name || run.runners?.name || 'Ismeretlen';
        const serial = run.serial_number || 'no-sn';

        console.log(`\nProcessing: ${runnerName} (${serial}) [${runId}]`);
        console.log(`  Current state: proof_submitted=${run.proof_submitted}, completed=${run.completed}, current_urls=${(run.proof_urls || []).length}`);
        console.log(`  Found ${publicUrls.length} file(s) in storage.`);

        // Always ensure proof_submitted is true and proof_urls contains all uploaded files
        const updatePayload = {
            proof_submitted: true,
            proof_urls: publicUrls,
            proof_submitted_at: submittedAt
        };

        const { error: updateErr } = await supabase
            .from('runs')
            .update(updatePayload)
            .eq('id', runId);

        if (updateErr) {
            console.error(`  ❌ Error updating run ${runId}:`, updateErr);
        } else {
            console.log(`  ✅ Successfully updated ${runnerName} (${serial}) with ${publicUrls.length} proof URL(s)!`);
        }
    }

    console.log('\n--- Proof Synchronization Finished ---');
}

syncProofs().catch(console.error);
