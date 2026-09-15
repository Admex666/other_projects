const fs = require('fs');
const path = require('path');

let envStr = '';
const envPath = path.join(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
  envStr = fs.readFileSync(envPath, 'utf8');
} else {
  envStr = fs.readFileSync(path.join(__dirname, '..', '..', '.env'), 'utf8');
}

const env = {};
envStr.split('\n').forEach(line => {
  const idx = line.indexOf('=');
  if (idx > 0 && !line.trim().startsWith('#')) {
    env[line.substring(0, idx).trim()] = line.substring(idx + 1).trim();
  }
});

const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);

async function syncCompanionShipments() {
  const pairs = [
    { companion: '#055/100', primary: '#056/100' }, // Rudolf Alexandra <- Jakab Miklós
    { companion: '#049/100', primary: '#048/100' }, // Szabó-Mráz Anita <- Szabó Richárd
    { companion: '#034/100', primary: '#033/100' }, // Szabó Éva <- Mikó Balázs
    { companion: '#041/100', primary: '#042/100' }, // Palotai Bálint <- Palotai Tímea
    { companion: '#047/100', primary: '#046/100' }, // Menyhért Emese Angéla <- Hajdinák István
    { companion: '#029/100', primary: '#028/100' }, // Erős Rezső <- Mester Anita
    { companion: '#010/100', primary: '#014/100' }, // Zsíros Norbert <- Vitai Zita
    { companion: '#024/100', primary: '#022/100' }, // Hendre Kármen <- Berényi Zoltán
    { companion: '#025/100', primary: '#022/100' }, // Berényi Botond <- Berényi Zoltán
    { companion: '#027/100', primary: '#026/100' }, // Berényiné Tóth Gabriella <- Berényi Mihály
    { companion: '#051/100', primary: '#011/100' }, // Bodor Anikó <- Balaton Edit
    { companion: '#053/100', primary: '#054/100' }, // Korpos-Kakas Vivien <- Korpos Levente
    { companion: '#058/100', primary: '#057/100' }, // Kuli Erika <- Mike Gyula
    { companion: '#059/100', primary: '#057/100' }, // Mike Botond <- Mike Gyula
    { companion: '#061/100', primary: '#057/100' }  // Mike Petra <- Mike Gyula
  ];

  for (const item of pairs) {
    const { companion, primary } = item;
    const { data: pRun } = await supabase.from('runs').select('id, serial_number, received_date, shipments(*)').eq('serial_number', primary).single();
    const { data: cRun } = await supabase.from('runs').select('id, serial_number, shipments(*)').eq('serial_number', companion).single();

    if (!pRun || !cRun) {
      console.log('Skipping missing run:', companion, primary);
      continue;
    }

    const pShip = pRun.shipments;
    const cShip = cRun.shipments;

    if (!pShip || !cShip) {
      console.log('Skipping missing shipment:', companion, primary);
      continue;
    }

    const shipUpdate = {
      tracking_code: pShip.tracking_code,
      shipped: true,
      shipped_at: pShip.shipped_at || cShip.shipped_at,
      received: pShip.received,
      received_at: pShip.received_at || cShip.received_at,
      parcel_id: pShip.parcel_id || cShip.parcel_id,
      parcel_name: pShip.parcel_name || cShip.parcel_name,
      parcel_address: pShip.parcel_address || cShip.parcel_address
    };

    const { error: sErr } = await supabase.from('shipments').update(shipUpdate).eq('id', cShip.id);
    if (sErr) console.error('Error updating shipment for', companion, sErr);

    if (pRun.received_date) {
      const { error: rErr } = await supabase.from('runs').update({ received_date: pRun.received_date }).eq('id', cRun.id);
      if (rErr) console.error('Error updating run for', companion, rErr);
    }

    console.log('Synced ' + companion + ' <- ' + primary + ': tracking=' + pShip.tracking_code + ', received=' + pShip.received);
  }
  console.log('Successfully completed companion shipments sync.');
}

syncCompanionShipments().catch(console.error);
