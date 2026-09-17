const fs = require('fs');
const path = require('path');
const envPath = path.join(__dirname, '../.env');
let envStr = fs.readFileSync(envPath, 'utf8');
const env = {};
envStr.split('\n').forEach(line => {
  const idx = line.indexOf('=');
  if (idx > 0 && !line.trim().startsWith('#')) {
    env[line.substring(0, idx).trim()] = line.substring(idx + 1).trim();
  }
});
const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);

async function checkLeadsDetail() {
  const { data: leads, error } = await supabase
    .from('leads')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Error fetching leads:', error);
    return;
  }

  console.log('=== LEADS STATISZTIKA ===');
  console.log('Összes feliratkozás (lead bejegyzés):', leads.length);

  const uniqueEmails = [...new Set(leads.map(l => (l.email || '').toLowerCase().trim()))];
  console.log('Egyedi e-mail címek száma:', uniqueEmails.length);

  const campaigns = {};
  const sources = {};
  leads.forEach(l => {
    const c = l.campaign || 'n/a';
    const s = l.source || 'n/a';
    campaigns[c] = (campaigns[c] || 0) + 1;
    sources[s] = (sources[s] || 0) + 1;
  });
  console.log('Kampányok szerint:', JSON.stringify(campaigns, null, 2));
  console.log('Források szerint:', JSON.stringify(sources, null, 2));

  // Runners & Runs mapping
  const { data: allRunners } = await supabase
    .from('runners')
    .select('id, email, name, runs(id, serial_number, campaign, created_at)');
  
  const runnerMap = new Map();
  if (allRunners) {
    allRunners.forEach(r => {
      if (r.email) runnerMap.set(r.email.toLowerCase().trim(), r);
    });
  }

  const convertedLeads = [];
  const unconvertedLeads = [];

  leads.forEach(l => {
    const emailKey = (l.email || '').toLowerCase().trim();
    const r = runnerMap.get(emailKey);
    const hasRuns = r && r.runs && r.runs.length > 0;
    if (hasRuns) {
      convertedLeads.push({ lead: l, runs: r.runs });
    } else {
      unconvertedLeads.push(l);
    }
  });

  console.log('\n=== KONVERZIÓS STATISZTIKA ===');
  console.log('Ebből már nevezett/vásárolt (konvertált):', convertedLeads.length);
  console.log('Még nem vásárolt érdeklődők (warm leads):', unconvertedLeads.length);

  console.log('\n--- Konvertált érdeklődők (vásárlók) ---');
  convertedLeads.forEach(({ lead, runs }) => {
    const serials = runs.map(r => `${r.campaign}:${r.serial_number}`).join(', ');
    console.log(`- ${lead.name} (${lead.email}) | Nevezések: ${serials} | Lead időpont: ${lead.created_at}`);
  });

  console.log('\n--- Még nem vásárolt érdeklődők (Warm Leads - remarketing célcsoport) ---');
  unconvertedLeads.forEach(l => {
    console.log(`- ${l.name} (${l.email}) | Kampány: ${l.campaign} | Dátum: ${l.created_at}`);
  });
}
checkLeadsDetail();
