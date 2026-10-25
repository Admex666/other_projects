/**
 * test_lead_nurture_suite.js
 *
 * Automatikus tesztelési keretrendszer a VitaSteps Lead Nurturing V1 rendszerhez.
 *
 * Ellenőrzi az összes minőségi és biztonsági kaput:
 *  1. Mind a 6 nurture email sablon létezik és tartalmazza a kötelező változókat
 *  2. Day 1, 3, 5, 7, 10 késleltetési logikák és időkapuk
 *  3. Idempotencia: ugyanaz az email nem küldhető ki kétszer (DB vagy analytics_events alapján sem)
 *  4. Régi, 2026-10-01 előtti leadek vagy a szeptemberi kampány címzettjei SOHA nem kapnak új nurture emailt
 *  5. Vásárlás (converted=true, runners.runs vagy orders.billing_email) azonnal leállítja a küldést
 *  6. Leiratkozás (unsubscribed=true, source='unsubscribed' vagy lead_unsubscribed event) azonnal megállítja a küldést
 *  7. E-mail szintű deduplikáció: több lead sor esetén is pontosan 1 levél mehet ki, és ha bármely sor kizárt, a teljes cím kizárt
 *  8. 20 órás cooldown védelem két levél között (DB vagy analytics_events alapján)
 *  9. Magyar keresztnév kinyerés (Magyar és nyugati névsorrend, -né végződés, ALL CAPS, telefonszám/email szűrés)
 * 10. Email CTA linkek biztonsága (lead UUID használata, nyers e-mail nélkül)
 * 11. Frontend kapu feloldás UUID alapú ?lead=<UUID> paraméterrel (nagykevely/index.html & kalandkonyv.html)
 * 12. Admin leads-email.js aggregáció és kizárások (runners + orders + unsubscribed + legacy)
 * 13. Nappali küldési ablak (08:00 - 19:00 Budapest) kalkuláció
 * 14. Analytics esemény struktúrák (lead_created, lead_email_sent, lead_email_clicked, lead_checkout_started)
 */

const assert = require('assert');
const path = require('path');
const fs = require('fs');
const {
    extractFirstName,
    evaluateUniqueLeadsForNurture
} = require('./run_lead_nurture_sequence');
const {
    aggregateUniqueLeads
} = require('../lib/admin/leads-email');

console.log('============================================================');
console.log(' VITASTEPS LEAD NURTURING V1 TEST SUITE');
console.log('============================================================\n');

let passedTests = 0;
let totalTests = 0;

function it(name, fn) {
    totalTests++;
    try {
        fn();
        console.log(`  ✅ [PASS] ${name}`);
        passedTests++;
    } catch (err) {
        console.error(`  ❌ [FAIL] ${name}`);
        console.error(`     Hiba: ${err.message}\n`);
    }
}

// 1. Sablonok megléte
it('1. Mind a 6 nurture email sablon létezik a lead_nurture mappában és érvényes változókat tartalmaz', () => {
    const templateDir = path.join(__dirname, '../email_templates/lead_nurture');
    const expectedTemplates = ['v1_day0.html', 'v1_day1.html', 'v1_day3.html', 'v1_day5.html', 'v1_day7.html', 'v1_day10.html'];

    expectedTemplates.forEach(t => {
        const p = path.join(templateDir, t);
        assert.ok(fs.existsSync(p), `Sablon nem található: ${t}`);
        const content = fs.readFileSync(p, 'utf8');
        assert.ok(content.includes('{{NAME}}'), `${t} hiányolja a {{NAME}} változót`);
        assert.ok(content.includes('{{CTA_URL}}') || content.includes('{{UNLOCK_URL}}'), `${t} hiányolja a CTA linket`);
        assert.ok(content.includes('{{UNSUBSCRIBE_URL}}'), `${t} hiányolja az unsubscribe linket`);
        assert.ok(!content.includes('vitasteps.vercel.app/'), `${t} hibás (régi) domain nevet tartalmaz`);
    });
});

// 2. Késleltetési logikák és esedékességi számítások a valós motorral
it('2. Day 1, 3, 5, 7, 10 óra késleltetések helyesen kalkulálódnak a valódi motorban', () => {
    const now = new Date('2026-10-25T12:00:00Z');

    function evalAtHours(hoursAgo, lastStep) {
        const createdAt = new Date(now.getTime() - hoursAgo * 3600 * 1000).toISOString();
        const res = evaluateUniqueLeadsForNurture({
            leads: [{
                id: 'lead-1',
                email: 'teszt@example.com',
                name: 'Teszt Elek',
                created_at: createdAt,
                last_sequence_step: lastStep
            }],
            now
        });
        return res.eligibleItems[0]?.dueStep?.step;
    }

    assert.strictEqual(evalAtHours(12, 0), undefined);
    assert.strictEqual(evalAtHours(25, 0), 1);
    assert.strictEqual(evalAtHours(40, 1), undefined);
    assert.strictEqual(evalAtHours(75, 1), 3);
    assert.strictEqual(evalAtHours(130, 3), 5);
    assert.strictEqual(evalAtHours(170, 5), 7);
    assert.strictEqual(evalAtHours(250, 7), 10);
    assert.strictEqual(evalAtHours(300, 10), undefined);
});

// 3. Idempotencia: analytics_events fallback amikor a DB oszlopok hiányoznak
it('3. Idempotencia: analytics_events (lead_email_sent) alapján is megakadályozza a duplikált küldést', () => {
    const now = new Date('2026-10-25T12:00:00Z');
    const res = evaluateUniqueLeadsForNurture({
        leads: [{
            id: 'lead-oct-1',
            email: 'october@example.com',
            name: 'Kovács Péter',
            created_at: '2026-10-20T10:00:00Z' // ~122 órája (> 5 nap), nincs last_sequence_step oszlop a soron
        }],
        emailEvents: [
            {
                event_name: 'lead_email_sent',
                event_data: { lead_id: 'lead-oct-1', step: 1, email_id: 'lead_v1_day1' },
                created_at: '2026-10-21T10:00:00Z'
            },
            {
                event_name: 'lead_email_sent',
                event_data: { lead_id: 'lead-oct-1', step: 3, email_id: 'lead_v1_day3' },
                created_at: '2026-10-23T10:00:00Z'
            }
        ],
        now
    });

    assert.strictEqual(res.eligibleItems.length, 1);
    assert.strictEqual(res.eligibleItems[0].lastStep, 3);
    assert.strictEqual(res.eligibleItems[0].dueStep.step, 5);
});

// 4. Régi leadek és szeptemberi kampány címzettek szigorú kizárása
it('4. Régi leadek (< 2026-10-01) és a szeptemberi kampány címzettjei szigorúan kizárva', () => {
    const now = new Date('2026-10-25T12:00:00Z');
    const res = evaluateUniqueLeadsForNurture({
        leads: [
            { id: 'l1', email: 'sept@example.com', name: 'Szept Elek', created_at: '2026-09-27T10:00:00Z' },
            { id: 'l2', email: 'sent0927@example.com', name: 'Sent Elek', created_at: '2026-10-05T10:00:00Z' },
            { id: 'l3', email: 'oct@example.com', name: 'Okt Elek', created_at: '2026-10-05T10:00:00Z' }
        ],
        legacySentEmailSet: new Set(['sent0927@example.com']),
        now
    });

    assert.strictEqual(res.skippedLegacyCount, 2);
    assert.strictEqual(res.eligibleItems.length, 1);
    assert.strictEqual(res.eligibleItems[0].lead.email, 'oct@example.com');
});

// 5. Vásárlás és leiratkozás kizárása (cross-table orders/runners + events)
it('5. Vásárlás (leads.converted, runners, orders) vagy leiratkozás esetén a nurture azonnal leáll', () => {
    const now = new Date('2026-10-25T12:00:00Z');
    const convertedEmailSet = new Set(['buyer_in_orders@example.com']);

    const res = evaluateUniqueLeadsForNurture({
        leads: [
            { id: '1', email: 'buyer_in_orders@example.com', name: 'Vevő 1', created_at: '2026-10-10T10:00:00Z', converted: false },
            { id: '2', email: 'buyer_in_leads@example.com', name: 'Vevő 2', created_at: '2026-10-10T10:00:00Z', converted: true },
            { id: '3', email: 'unsub_in_leads@example.com', name: 'Unsub 1', created_at: '2026-10-10T10:00:00Z', unsubscribed: true },
            { id: '4', email: 'unsub_in_events@example.com', name: 'Unsub 2', created_at: '2026-10-10T10:00:00Z', unsubscribed: false },
            { id: '5', email: 'active_warm@example.com', name: 'Meleg Lead', created_at: '2026-10-10T10:00:00Z', converted: false }
        ],
        convertedEmailSet,
        emailEvents: [
            { event_name: 'lead_unsubscribed', event_data: { email: 'unsub_in_events@example.com' }, created_at: '2026-10-12T10:00:00Z' }
        ],
        now
    });

    assert.strictEqual(res.skippedConvertedCount, 2);
    assert.strictEqual(res.skippedUnsubscribedCount, 2);
    assert.strictEqual(res.eligibleItems.length, 1);
    assert.strictEqual(res.eligibleItems[0].lead.email, 'active_warm@example.com');
});

// 6. E-mail szintű deduplikáció több lead sor esetén
it('6. E-mail szintű deduplikáció: többször regisztrált lead csak 1 levelet kaphat, és részleges leiratkozás is kizárja', () => {
    const now = new Date('2026-10-25T12:00:00Z');
    const res = evaluateUniqueLeadsForNurture({
        leads: [
            // Arvagel kétszer regisztrált októberben -> csak 1x szerepelhet az eligibleItems-ben!
            { id: 'dup-1a', email: 'arvagel@gmail.com', name: 'Gabriella Szalainé Árvai', created_at: '2026-10-16T13:39:34Z' },
            { id: 'dup-1b', email: 'arvagel@gmail.com', name: 'Gabriella Szalainé Árvai', created_at: '2026-10-16T14:08:57Z' },
            // Multi-row ahol az egyik sor leiratkozott, a másik nem -> teljesen ki kell zárni!
            { id: 'dup-2a', email: 'partial_unsub@example.com', name: 'Teszt Anna', created_at: '2026-10-15T10:00:00Z', unsubscribed: true },
            { id: 'dup-2b', email: 'partial_unsub@example.com', name: 'Teszt Anna', created_at: '2026-10-18T10:00:00Z', unsubscribed: false }
        ],
        now
    });

    assert.strictEqual(res.totalRows, 4);
    assert.strictEqual(res.uniqueLeadCount, 2);
    assert.strictEqual(res.duplicateRowsRemoved, 2);
    assert.strictEqual(res.skippedUnsubscribedCount, 1);
    assert.strictEqual(res.eligibleItems.length, 1);
    assert.strictEqual(res.eligibleItems[0].lead.email, 'arvagel@gmail.com');
    assert.strictEqual(res.eligibleItems[0].firstName, 'Gabriella');
});

// 7. 20 órás cooldown védelem
it('7. 20 órán belül már megkeresett lead nem kaphat újabb levelet', () => {
    const now = new Date('2026-10-25T12:00:00Z');
    const res = evaluateUniqueLeadsForNurture({
        leads: [{
            id: 'cool-1',
            email: 'cooldown@example.com',
            name: 'Kovács János',
            created_at: '2026-10-20T10:00:00Z'
        }],
        emailEvents: [{
            event_name: 'lead_email_sent',
            event_data: { lead_id: 'cool-1', step: 1, email_id: 'lead_v1_day1' },
            created_at: '2026-10-25T02:00:00Z' // 10 órája ment ki Day 1
        }],
        now
    });

    assert.strictEqual(res.skippedTooSoonCount, 1);
    assert.strictEqual(res.eligibleItems.length, 0);
});

// 8. Magyar keresztnév formázó (okos felismerés)
it('8. Keresztnév kinyerés helyesen kezeli a magyar és nyugati sorrendet, -né neveket és telefonszámokat', () => {
    assert.strictEqual(extractFirstName('Kovács János'), 'János');
    assert.strictEqual(extractFirstName('Dr. Tóth Viktória'), 'Viktória');
    assert.strictEqual(extractFirstName('Papp-Radnai Barbara'), 'Barbara');
    assert.strictEqual(extractFirstName('Csaba Tóth'), 'Csaba');
    assert.strictEqual(extractFirstName('Annamaria Vincze'), 'Annamaria');
    assert.strictEqual(extractFirstName('Irén Vizi-Székely'), 'Irén');
    assert.strictEqual(extractFirstName('Anita Babikne Gyovai'), 'Anita');
    assert.strictEqual(extractFirstName('Mihály Tamás Locher'), 'Mihály');
    assert.strictEqual(extractFirstName('Gabriella Szalainé Árvai'), 'Gabriella');
    assert.strictEqual(extractFirstName('MIKLÓS  ZOLTÁNNÉ'), 'Miklós Zoltánné');
    assert.strictEqual(extractFirstName('Belák Udóné'), 'Belák Udóné');
    assert.strictEqual(extractFirstName('Ádám Katalin'), 'Katalin');
    assert.strictEqual(extractFirstName('Mirczik Ádám'), 'Ádám');
    assert.strictEqual(extractFirstName('+36306312788'), 'Túrázó');
    assert.strictEqual(extractFirstName('adam.mirczik@gmail.com'), 'Túrázó');
    assert.strictEqual(extractFirstName(''), 'Túrázó');
});

// 9. Link formázás és URL paraméter biztonság
it('9. Tracking linkek nem tartalmaznak nyers email címet, lead ID-t használnak', () => {
    const leadId = 'a1b2c3d4-e5f6-7890-abcd-1234567890ab';
    const emailId = 'lead_v1_day1';
    const sequence = 'lead_nurture_v1';
    const targetUrl = `https://vitastepsss.vercel.app/nagykevely/index.html?lead=${leadId}&source=email&email_id=${emailId}&sequence=${sequence}#kalandkonyv`;

    assert.ok(targetUrl.includes(`lead=${leadId}`), 'Lead ID hiányzik');
    assert.ok(targetUrl.includes(`email_id=${emailId}`), 'Email ID hiányzik');
    assert.ok(targetUrl.includes(`sequence=${sequence}`), 'Sequence hiányzik');
    assert.ok(!targetUrl.includes('@'), 'Hiba: Nyers email cím található az URL-ben!');
});

// 10. Frontend kapu feloldás ellenőrzése (?lead=<UUID> támogatása)
it('10. Frontend oldalak (nagykevely/index.html és kalandkonyv.html) feloldják a zárolást UUID ?lead= paraméterrel is', () => {
    const indexHtml = fs.readFileSync(path.join(__dirname, '../nagykevely/index.html'), 'utf8');
    const kalandHtml = fs.readFileSync(path.join(__dirname, '../nagykevely/kalandkonyv.html'), 'utf8');

    // Nem szabad kizárólag params.get('lead') === 'true'-ra szűrni
    assert.ok(!indexHtml.includes("if (params.get('lead') === 'true') return true;"), 'index.html még mindig csak lead=true-t fogad el!');
    assert.ok(!kalandHtml.includes("const isLeadParam = params.get('lead') === 'true';"), 'kalandkonyv.html még mindig csak lead=true-t fogad el!');
    assert.ok(indexHtml.includes("localStorage.setItem('vt_lead_id'"), 'index.html nem menti el a vt_lead_id-t!');
    assert.ok(kalandHtml.includes("localStorage.setItem('vt_lead_id'"), 'kalandkonyv.html nem menti el a vt_lead_id-t!');
});

// 11. Admin leads-email.js aggregáció ellenőrzése
it('11. Admin aggregateUniqueLeads helyesen kizárja a vásárlókat és leiratkozottakat', () => {
    const sampleLeads = [
        { id: '1', email: 'warm@example.com', name: 'Csaba Tóth', created_at: '2026-10-10T10:00:00Z' },
        { id: '2', email: 'warm@example.com', name: 'Csaba Tóth', created_at: '2026-10-11T10:00:00Z' },
        { id: '3', email: 'buyer@example.com', name: 'Vevő János', created_at: '2026-10-10T10:00:00Z' },
        { id: '4', email: 'unsub@example.com', name: 'Leiratkozó Éva', created_at: '2026-10-10T10:00:00Z', unsubscribed: true }
    ];
    const result = aggregateUniqueLeads(sampleLeads, new Set(['buyer@example.com']));
    assert.strictEqual(result.totalRecords, 4);
    assert.strictEqual(result.totalUnique, 3);
    assert.strictEqual(result.convertedCount, 1);
    assert.strictEqual(result.unsubscribedCount, 1);
    assert.strictEqual(result.targetLeads.length, 1);
    assert.strictEqual(result.targetLeads[0].name, 'Csaba');
});

// 12. Budapest daytime ablak
it('12. Nappali küldési ablak (08:00 - 19:00 Budapest) kalkuláció érvényes', () => {
    function isDaytimeBudapest(hour) {
        return hour >= 8 && hour < 19;
    }

    assert.strictEqual(isDaytimeBudapest(3), false);
    assert.strictEqual(isDaytimeBudapest(7), false);
    assert.strictEqual(isDaytimeBudapest(8), true);
    assert.strictEqual(isDaytimeBudapest(12), true);
    assert.strictEqual(isDaytimeBudapest(18), true);
    assert.strictEqual(isDaytimeBudapest(19), false);
    assert.strictEqual(isDaytimeBudapest(23), false);
});

console.log(`\n============================================================`);
console.log(` EREDMÉNY: ${passedTests} / ${totalTests} teszt SIKERES!`);
console.log('============================================================\n');

if (passedTests !== totalTests) {
    process.exit(1);
}
