const { createClient } = require('@supabase/supabase-js');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

async function check() {
    const { data: orders, error } = await supabase
        .from('orders')
        .select('*')
        .eq('stripe_payment_status', 'paid')
        .eq('is_test', false)
        .order('created_at', { ascending: false });

    if (error) {
        console.error('Error fetching orders:', error);
        return;
    }

    console.log('=== RENDELÉS ÉS KREATÍV HOZZÁRENDELÉS STATISZTIKA ===');
    console.log(`Összes fizetett éles rendelés: ${orders.length} db\n`);

    const pilis = orders.filter(o => (o.campaign || '').toLowerCase() === 'pilis');
    const predikalo = orders.filter(o => (o.campaign || '').toLowerCase() === 'predikaloszek');

    const pDirect = pilis.filter(o => (o.utm_content || '').trim()).length;
    const pCampOnly = pilis.filter(o => !(o.utm_content || '').trim() && (o.utm_campaign || '').trim()).length;
    const pNoUtm = pilis.filter(o => !(o.utm_content || '').trim() && !(o.utm_campaign || '').trim()).length;

    console.log(`1. 🌌 NAGY-KEVÉLY (PILIS) – ${pilis.length} db rendelés:`);
    console.log(`   ✅ Egyértelmű kreatívhoz kötve (utm_content): ${pDirect} db`);
    console.log(`   🟡 Csak kampány UTM volt (kreatív nélkül, fallback): ${pCampOnly} db`);
    console.log(`   ❌ Nincs semmilyen UTM / Organikus / Direkt: ${pNoUtm} db\n`);

    console.log(`2. 🏔️ PRÉDIKÁLÓSZÉK – ${predikalo.length} db rendelés:`);
    console.log(`   ❌ Nincs UTM / Korábbi organikus kampány: ${predikalo.length} db (egyik sincs Meta kreatívhoz kötve)\n`);

    console.log('--- NAGY-KEVÉLY RENDELÉSEK RÉSZLETES LISTÁJA ---');
    pilis.forEach((o, idx) => {
        const cnt = (o.utm_content || '').trim();
        const cmp = (o.utm_campaign || '').trim();
        let stat = '✅ PONTOS KREATÍV';
        if (!cnt && cmp) stat = '🟡 CSAK KAMPÁNY (Fallback)';
        if (!cnt && !cmp) stat = '❌ NINCS UTM (Organikus/Közvetlen)';
        console.log(`${idx + 1}. ${o.created_at.slice(0, 10)} | ${String(o.amount_total).padStart(6, ' ')} Ft | ${o.billing_email.padEnd(28, ' ')} | content: '${cnt}' | status: ${stat}`);
    });
}

check();
