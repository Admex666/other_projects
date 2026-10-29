const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../../.env') });
require('dotenv').config({ path: path.resolve(__dirname, '../../../.env.local') });
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });
require('dotenv').config();

const { createClient } = require('@supabase/supabase-js');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const { ImapFlow } = require('imapflow');
const { simpleParser } = require('mailparser');
const { getCreativeCsvData } = require('./finance');

const supabase = createClient(
    process.env.SUPABASE_URL || 'https://ncsathcqpvlrygkphced.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

const ALLOWED_TABLES = [
    'runners',
    'runs',
    'orders',
    'shipments',
    'feedbacks',
    'leads',
    'meta_daily_metrics',
    'analytics_sessions',
    'analytics_visitors',
    'analytics_events',
    'marketing_targets'
];

// ─────────────────────────────────────────────────────────────────────────────
// SYSTEM PROMPT (Magyar nyelven, teljes VitaSteps kontextussal)
// ─────────────────────────────────────────────────────────────────────────────
const SYSTEM_INSTRUCTION = `Te vagy a **VitaSteps Admin AI Asszisztens**, a VitaSteps teljes körű üzleti, pénzügyi, marketing, operatív és ügyfélszolgálati elemző intelligenciája.
Minden válaszodat **magyar nyelven**, strukturáltan, pontos adatokkal (forint összegek, darabszámok, nevek, dátumok) és átlátható Markdown formázással (táblázatok, félkövér kiemelések, felsorolások) add meg!

### 🏔️ A VitaSteps Ökoszisztéma és Üzleti Modell
A VitaSteps fizikai érmes túrakihívásokat, virtuális kihívásokat és városi audiosétákat szervező márka (*„MOZOGJ. FEDEZZ FEL. TELJESÍTS.”*).
Jelenlegi fő kihívások (kampányok):
1. **🏔️ Prédikálószék Vertical (\`predikaloszek\` / \`-PS\`):**
   - Limitált 100 db (99 értékesíthető) egyedi fém érem.
   - Nevezési díj: **7 990 Ft / érem**.
   - Távok: Klasszikus (10 km), Félmaraton (15 km), Hosszú (20 km), Ultra (25 km).
2. **🌌 A Nagy-Kevély csillagai (\`pilis\` / \`-PK\`):**
   - Limitált 100 db sötétben foszforeszkáló csillagászati érem a Pilisben.
   - Nevezési díj: **7 990 Ft / érem**.
   - Távok: Családi (5 km), Klasszikus (10 km), Extra (13 km), Félmaraton (21 km).

### 📊 Unit Economics és Pénzügyi Alapelvek
- **Bruttó eladási ár:** 7 990 Ft / érem (többérmes vásárlásnál vagy kuponnál kedvezményes lehet, házhozszállításnál felár).
- **Változó költségek (1 db éremnél):**
  - Foxpost csomagautomata szállítás: ~1 140 – 1 250 Ft (házhozszállítás ~2 400 Ft). Többérmes vagy összevont szállításnál csak egyszer merül fel!
  - Stripe tranzakciós jutalék: ~1.5% + 50–85 Ft (~170–205 Ft).
  - Számlázz.hu e-számla díj: ~35–40 Ft.
  - Csomagolás (buborékos boríték + kísérőkártya): ~120–150 Ft.
  - Meta Ads hirdetési költség (CAC / CPA): kampánytól függően, + 27% import ÁFA terheli.
- **Fix költségek (Capex & Opex):**
  - Éremgyártási Capex (Alibaba): ~163 000 Ft / 100 db-os széria (~1 630 Ft / db bekerülési érték).
  - Könyvelés (Péter László): 15 000 Ft / hó.
- **Pénzügyi Mérleg:**
  - Likvid tőke = Revolut Pro egyenleg + Stripe elérhető egyenleg (+ Stripe pending jóváírás alatt).
  - Raktárkészlet értéke = Szabad érmek darabszáma × bekerülési egységár.

### 🗄️ Adatbázis Séma (Supabase)
- \`runners\`: Futók profiljai (\`id, name, email, phone, billing_name, billing_address, referral_code, referred_by, is_test, created_at\`).
- \`runs\`: Nevezések és teljesítések (\`id, runner_id, order_id, name, campaign, distance, serial_number, serial_rank, proof_submitted, proof_submitted_at, proof_urls, strava_url, completed, completion_date, diploma_url, ship_together_with, is_test, created_at\`).
  - Megjegyzés: egy \`run\` akkor tartozik a Nagy-Kevély (\`pilis\`) kampányhoz, ha \`campaign === 'pilis'\` vagy a \`serial_number\` tartalmazza a \`-PK\`-t. Különben Prédikálószék (\`predikaloszek\`).
  - A teszt futásokat (\`is_test === true\` vagy \`serial_number\`-ben \`999\` / \`TEST\`, vagy \`admex\` / \`teszt\` név/email) az üzleti statisztikákból érdemes kiszűrni, hacsak nem kérdezik kifejezetten.
- \`orders\`: Stripe rendelések (\`id, runner_id, stripe_session_id, stripe_payment_status, amount_total, quantity, campaign, billing_name, billing_address, invoice_number, created_at\`). Csak a \`stripe_payment_status = 'paid'\` számít fizetett rendelésnek!
- \`shipments\`: Csomagküldési adatok (\`id, run_id, method, parcel_id, parcel_name, home_address, phone, shipped, shipped_at, tracking_code, foxpost_status, received_at\`).
- \`feedbacks\`: Teljesítői visszajelzések (\`id, run_id, erem_minoseg, szallitas_elegedett, nps_score, legjobban_tetszett, mit_tenne_jobba, kovetkezo_tajegyseg, reszvetel_ujra, photo_url, created_at\`).
- \`leads\`: Kalandfüzetet / GPX-et letöltött érdeklődők (\`id, email, name, campaign, source, converted, unsubscribed, created_at\`).
- \`meta_daily_metrics\`: Napi szintű Meta hirdetési adatok.
- \`analytics_sessions\`, \`analytics_visitors\`, \`analytics_events\`: Weboldal látogatói tölcsér és viselkedési analitika.

### 🛠️ Szabályok a Toolok (Függvényhívások) használatához:
- **MINDIG** kérdezd le a valós adatokat a rendelkezésedre álló toolokkal, mielőtt válaszolnál! Soha ne találj ki számokat vagy neveket fejből!
- Ha általános helyzetképet, készletet vagy futó statisztikát kérdeznek, használd a \`get_database_overview\` vagy \`query_supabase_table\` toolt.
- Ha pénzügyről, Revolutról, Stripe-ról, P&L-ről, likvid tőkéről vagy mérlegről kérdeznek, használd a \`get_financial_and_cashflow_data\` toolt.
- Ha hirdetésekről, kreatívokról, ROAS-ról, CPA-ról vagy Meta költésről kérdeznek, használd a \`get_marketing_and_creatives_data\` toolt.
- Ha emailekről, ügyféllevelekről, beérkezett üzenetekről, Foxpost/Számlázz.hu/Stripe értesítésekről kérdeznek, használd a \`search_and_read_emails\` toolt!
- Ha stratégiai döntésekről (ADR), folyamatokról vagy a tudásbázisról kérdeznek, használd a \`read_knowledge_graph\` toolt!`;

// ─────────────────────────────────────────────────────────────────────────────
// GEMINI FUNCTION DECLARATIONS (TOOLS)
// ─────────────────────────────────────────────────────────────────────────────
const GEMINI_TOOLS = [
    {
        functionDeclarations: [
            {
                name: 'get_database_overview',
                description: 'Átfogó, valós idejű statisztikai összefoglalót ad a teljes VitaSteps Supabase adatbázisról: éremkészlet és eladások kampányonként (Nagy-Kevély vs Prédikálószék), várakozó igazolások, még nem igazolt futók, jóváhagyott teljesítők, csomagolásra/feladásra váró Foxpost csomagok, visszajelzések (NPS, csillagok), leadek és legutóbbi aktivitások.',
                parameters: {
                    type: 'OBJECT',
                    properties: {
                        include_recent_items: {
                            type: 'BOOLEAN',
                            description: 'Ha true (alapértelmezett), visszaadja a legutóbbi 10 nevezést, a jóváhagyásra váró beküldött igazolásokat és a feladásra váró csomagokat is.'
                        }
                    }
                }
            },
            {
                name: 'query_supabase_table',
                description: 'Rugalmas, csak-olvasható lekérdezés bármelyik VitaSteps Supabase táblán (runners, runs, orders, shipments, feedbacks, leads, meta_daily_metrics, analytics_sessions, analytics_visitors, analytics_events). Támogatja a relációk lekérését (pl. runs táblánál "*, runners(name, email, phone), shipments(*)"), szűrést, rendezést és limitet.',
                parameters: {
                    type: 'OBJECT',
                    properties: {
                        table: {
                            type: 'STRING',
                            description: 'A lekérdezendő tábla neve: runners | runs | orders | shipments | feedbacks | leads | meta_daily_metrics | analytics_sessions | analytics_visitors | analytics_events'
                        },
                        select: {
                            type: 'STRING',
                            description: 'Supabase select kifejezés. Például: "*" vagy runs esetén "*, runners(name, email, phone), shipments(*)".'
                        },
                        filters: {
                            type: 'ARRAY',
                            description: 'Opcionális szűrőfeltételek listája.',
                            items: {
                                type: 'OBJECT',
                                properties: {
                                    column: { type: 'STRING', description: 'Mező neve, pl. completed, campaign, email, proof_submitted' },
                                    operator: { type: 'STRING', description: 'Operátor: eq | neq | gt | gte | lt | lte | ilike | is | in' },
                                    value: { type: 'STRING', description: 'Érték szövegként (boolean esetén "true"/"false", null esetén "null").' }
                                },
                                required: ['column', 'operator', 'value']
                            }
                        },
                        order_by: {
                            type: 'STRING',
                            description: 'Rendezési mező neve (alapértelmezett: created_at).'
                        },
                        ascending: {
                            type: 'BOOLEAN',
                            description: 'Növekvő rendezés (true) vagy csökkenő (false, alapértelmezett).'
                        },
                        limit: {
                            type: 'INTEGER',
                            description: 'Maximális visszaadott sorok száma (alapértelmezett 50, max 250).'
                        }
                    },
                    required: ['table']
                }
            },
            {
                name: 'get_financial_and_cashflow_data',
                description: 'Lekéri a teljes pénzügyi, banki és cashflow adatokat: élő Stripe egyenleg (elérhető és pending), Stripe kifizetések (payouts) és tranzakciók, Revolut Pro bankszámla egyenleg és kategorizált tranzakciók (Marketing, Foxpost, Éremgyártás Capex, Könyvelés, Stripe kifizetés), fizetett rendelések összesítése és kampány szintű P&L / készletértékelés.',
                parameters: {
                    type: 'OBJECT',
                    properties: {
                        include_transactions_limit: {
                            type: 'INTEGER',
                            description: 'Hány darab legutóbbi egyedi Revolut és Stripe tranzakciót listázzon tételesen (alapértelmezett: 40).'
                        }
                    }
                }
            },
            {
                name: 'get_marketing_and_creatives_data',
                description: 'Lekéri a Meta Ads hirdetési és kreatív teljesítmény adatokat (meta_kreativ_napi_riport.csv és meta_daily_metrics): összköltés, megjelenés, elérés, link kattintás, CTR, CPC, vásárlások száma, CPA, ROAS kampányonként és kreatívonként (hirdetésenként) összesítve, valamint napi bontásban.',
                parameters: {
                    type: 'OBJECT',
                    properties: {
                        campaign_filter: {
                            type: 'STRING',
                            description: 'Opcionális szűrés: "all" (alapértelmezett), "pilis" (Nagy-Kevély), vagy "predikalo" (Prédikálószék).'
                        },
                        days: {
                            type: 'INTEGER',
                            description: 'Opcionális időablak napokban (pl. 7 az elmúlt 7 naphoz, vagy 0 / üres a teljes időszakhoz).'
                        }
                    }
                }
            },
            {
                name: 'read_knowledge_graph',
                description: 'Olvassa a VitaSteps projekt Knowledge Graph (knowledge/) dokumentációját és a config/campaigns.json fájlt. Képes kilistázni az összes tudáscsomópontot (entities, concepts, processes, systems, metrics, decisions/ADR, learnings, operations), vagy beolvasni konkrét markdown fájlok teljes tartalmát.',
                parameters: {
                    type: 'OBJECT',
                    properties: {
                        file_path: {
                            type: 'STRING',
                            description: 'A beolvasandó fájl relatív elérési útja a knowledge/ mappán belül (pl. "INDEX.md", "systems/admin-panel.md", "metrics/unit-economics.md", "decisions/ADR-009-strategic-ecosystem-pivot.md", vagy "campaigns.json"). Ha üres vagy "list", kilistázza az összes elérhető fájlt és az INDEX.md-t.'
                        },
                        search_term: {
                            type: 'STRING',
                            description: 'Opcionális keresőkifejezés, amire rákeres az összes knowledge/ markdown fájlban.'
                        }
                    }
                }
            },
            {
                name: 'search_and_read_emails',
                description: 'Keresés és e-mailek olvasása a VitaSteps Gmail fiókjából (vitasteps.team@gmail.com, vagy másodlagos fiókból) IMAP / Gmail API kapcsolaton keresztül. Képes listázni a legutóbbi beérkezett (INBOX) vagy elküldött leveleket, szűrni feladóra, tárgyra, szövegre, olvasatlan státuszra, és visszaadja a levelek tárgyát, feladóját, dátumát és szöveges tartalmát.',
                parameters: {
                    type: 'OBJECT',
                    properties: {
                        query: {
                            type: 'STRING',
                            description: 'Opcionális keresőszó (keres a tárgyban, feladóban és szövegben is, pl. "Foxpost", "igazolás", "Stripe", vagy egy futó neve/email címe).'
                        },
                        from: {
                            type: 'STRING',
                            description: 'Opcionális szűrés a feladó nevére vagy email címére.'
                        },
                        subject: {
                            type: 'STRING',
                            description: 'Opcionális szűrés az email tárgyára.'
                        },
                        unread_only: {
                            type: 'BOOLEAN',
                            description: 'Ha true, csak az olvasatlan leveleket keresi.'
                        },
                        folder: {
                            type: 'STRING',
                            description: 'Postafiók mappa: "INBOX" (alapértelmezett, beérkezett levelek) vagy "[Gmail]/Sent Mail" / "SENT" (elküldött levelek).'
                        },
                        limit: {
                            type: 'INTEGER',
                            description: 'Visszaadott levelek maximális száma (alapértelmezett: 10, max: 25).'
                        },
                        account: {
                            type: 'STRING',
                            description: 'Melyik postafiókot olvassa: "primary" (vitasteps.team@gmail.com, alapértelmezett) vagy "secondary" (ha van beállítva GMAIL_SECOND_USER).'
                        }
                    }
                }
            }
        ]
    }
];

// ─────────────────────────────────────────────────────────────────────────────
// IN-MEMORY SMART CACHE (60s TTL for instant subsequent / pre-warmed queries)
// ─────────────────────────────────────────────────────────────────────────────
const AI_TOOL_CACHE = new Map();

async function getCachedOrFetch(key, ttlMs, fetchFn) {
    const now = Date.now();
    const cached = AI_TOOL_CACHE.get(key);
    if (cached && (now - cached.ts) < ttlMs && cached.data !== null) {
        return cached.data;
    }
    if (cached && cached.inflight) {
        return cached.inflight;
    }
    const promise = Promise.resolve()
        .then(() => fetchFn())
        .then(data => {
            AI_TOOL_CACHE.set(key, { ts: Date.now(), data, inflight: null });
            return data;
        })
        .catch(err => {
            if (cached) cached.inflight = null;
            throw err;
        });

    AI_TOOL_CACHE.set(key, { ts: cached ? cached.ts : 0, data: cached ? cached.data : null, inflight: promise });
    return promise;
}

function warmUpAiCache() {
    getCachedOrFetch('db_overview:compact', 120000, () => toolGetDatabaseOverview({ include_recent_items: false })).catch(() => {});
    getCachedOrFetch('finance:10', 120000, () => toolGetFinancialAndCashflowData({ include_transactions_limit: 10 })).catch(() => {});
    getCachedOrFetch('marketing:all:0', 120000, () => toolGetMarketingAndCreativesData({ campaign_filter: 'all', days: 0 })).catch(() => {});
}

async function buildLiveSnapshotContext() {
    try {
        const [dbOverview, finData, mktData] = await Promise.all([
            getCachedOrFetch('db_overview:compact', 120000, () => toolGetDatabaseOverview({ include_recent_items: false })),
            getCachedOrFetch('finance:10', 120000, () => toolGetFinancialAndCashflowData({ include_transactions_limit: 10 })),
            getCachedOrFetch('marketing:all:0', 120000, () => toolGetMarketingAndCreativesData({ campaign_filter: 'all', days: 0 }))
        ]);

        const compactSnapshot = {
            campaigns: dbOverview.campaigns,
            orders: dbOverview.orders_summary,
            feedbacks: {
                count: dbOverview.feedbacks_summary?.total_feedbacks,
                avg_medal: dbOverview.feedbacks_summary?.avg_medal_rating_out_of_5,
                avg_nps: dbOverview.feedbacks_summary?.avg_nps_out_of_10
            },
            leads: dbOverview.leads_summary,
            balance_sheet: finData.balance_sheet,
            pnl: finData.campaign_pnl_summary,
            marketing: mktData.summary
        };

        return '\n\n### ⚡ ÉLŐ ELŐTÖLTÖTT KPI PILLANATKÉP:\n' +
            'Ha a kérdés megválaszolható az alábbi élő adatokból, NE hívj toolt, hanem válaszolj AZONNAL! Toolt csak emailekhez, részletes táblakereséshez, vagy Knowledge Graphhoz hívj:\n' +
            JSON.stringify(compactSnapshot);
    } catch (e) {
        return '';
    }
}

// Helper: Call Gemini API with automatic retry and fallback cascade on 503/429 High Demand
let cachedAvailableModels = null;
async function getFallbackCandidates(primaryModel, apiKey) {
    const defaults = [
        primaryModel,
        'gemini-3.1-flash-lite',
        'gemini-3.5-flash',
        'gemini-3.1-pro-preview'
    ];
    return [...new Set(defaults.filter(Boolean))];
}

async function callGeminiWithResilience(selectedModel, apiKey, payload, timeoutMs = 15000) {
    const candidates = await getFallbackCandidates(selectedModel, apiKey);
    let lastRes = null;
    let lastData = null;
    let usedModel = selectedModel;

    // Try primary model first, then fallback to other fast models
    const attemptPlan = [
        { model: selectedModel, delayMs: 0 },
        ...candidates.filter(m => m !== selectedModel).slice(0, 2).map(m => ({ model: m, delayMs: 250 }))
    ];

    for (const step of attemptPlan) {
        if (step.delayMs > 0) {
            await new Promise(r => setTimeout(r, step.delayMs));
        }
        usedModel = step.model;
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${usedModel}:generateContent?key=${encodeURIComponent(apiKey)}`;

        // Clone payload and configure thinkingConfig
        const bodyObj = JSON.parse(JSON.stringify(payload));
        if (usedModel.includes('lite') && bodyObj.generationConfig?.thinkingConfig) {
            delete bodyObj.generationConfig.thinkingConfig;
        }

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);

        let res;
        let data;
        try {
            res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bodyObj),
                signal: controller.signal
            });
            clearTimeout(timer);
            data = await res.json();
        } catch (fetchErr) {
            clearTimeout(timer);
            console.warn(`Gemini call to ${usedModel} failed/timed out:`, fetchErr.message);
            lastRes = { ok: false, status: 504 };
            lastData = { error: { message: `Időtúllépés vagy hálózati hiba a(z) ${usedModel} modellnél (${fetchErr.message}).` } };
            continue;
        }

        // Retry without thinkingConfig if model complains about thinkingConfig
        if (!res.ok && bodyObj.generationConfig?.thinkingConfig && (data?.error?.message || '').toLowerCase().includes('thinking')) {
            delete bodyObj.generationConfig.thinkingConfig;
            const c2 = new AbortController();
            const t2 = setTimeout(() => c2.abort(), timeoutMs);
            try {
                res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bodyObj),
                    signal: c2.signal
                });
                clearTimeout(t2);
                data = await res.json();
            } catch (err2) {
                clearTimeout(t2);
            }
        }

        if (res.ok) {
            return { res, data, usedModel };
        }

        lastRes = res;
        lastData = data;
        const errMsg = (data?.error?.message || '').toLowerCase();
        const isTransientOrModelError =
            res.status === 503 ||
            res.status === 429 ||
            res.status === 404 ||
            res.status === 504 ||
            errMsg.includes('high demand') ||
            errMsg.includes('overloaded') ||
            errMsg.includes('try again') ||
            errMsg.includes('resource exhausted') ||
            errMsg.includes('no longer available') ||
            errMsg.includes('not found') ||
            errMsg.includes('not supported') ||
            errMsg.includes('quota');

        if (!isTransientOrModelError) {
            break; // Invalid API key or malformed request -> stop immediately
        }
    }

    return { res: lastRes, data: lastData, usedModel };
}

// ─────────────────────────────────────────────────────────────────────────────
// HELPER FUNCTIONS FOR TOOLS
// ─────────────────────────────────────────────────────────────────────────────

function isTestRunRecord(r) {
    if (!r) return false;
    if (r.is_test) return true;
    const s = (r.serial_number || '').toUpperCase();
    const e = (r.runners?.email || '').toLowerCase();
    const n = (r.name || r.runners?.name || '').toLowerCase();
    return s.includes('TEST') || s.includes('999') || e.includes('test') || e.includes('admex') || n.includes('próba') || n.includes('teszt') || n.includes('minta');
}

function isPilisRunRecord(r) {
    if (!r) return false;
    const c = (r.campaign || '').toLowerCase();
    const s = (r.serial_number || '').toLowerCase();
    return c.includes('pilis') || c.includes('kevely') || s.includes('-pk') || s.includes('999');
}

// 1. TOOL: get_database_overview
async function toolGetDatabaseOverview(args = {}) {
    const includeRecent = args.include_recent_items !== false;

    const [runsRes, ordersRes, feedbacksRes, leadsRes] = await Promise.all([
        supabase.from('runs').select('*, runners(name, email, phone), shipments(*)').order('created_at', { ascending: false }),
        supabase.from('orders').select('*').order('created_at', { ascending: false }),
        supabase.from('feedbacks').select('*, runs(name, campaign, serial_number)').order('created_at', { ascending: false }),
        supabase.from('leads').select('*').order('created_at', { ascending: false })
    ]);

    const allRuns = runsRes.data || [];
    const realRuns = allRuns.filter(r => !isTestRunRecord(r));
    const testRunsCount = allRuns.length - realRuns.length;

    const pilisRuns = realRuns.filter(r => isPilisRunRecord(r));
    const predikaloRuns = realRuns.filter(r => !isPilisRunRecord(r));

    const getShipObj = (r) => Array.isArray(r.shipments) ? (r.shipments[0] || {}) : (r.shipments || {});

    const summarizeCampaignRuns = (list, limit) => {
        const sold = list.length;
        const completed = list.filter(r => r.completed).length;
        const proofPendingApproval = list.filter(r => !r.completed && r.proof_submitted).length;
        const notSubmittedYet = list.filter(r => !r.completed && !r.proof_submitted).length;
        const shipped = list.filter(r => r.completed && getShipObj(r).shipped).length;
        const waitingToShip = list.filter(r => r.completed && !getShipObj(r).shipped).length;
        const received = list.filter(r => getShipObj(r).received_at).length;

        return {
            limit,
            sold,
            remaining_stock: Math.max(0, limit - sold),
            sold_percentage: ((sold / limit) * 100).toFixed(1) + '%',
            completed_approved: completed,
            proof_submitted_waiting_approval: proofPendingApproval,
            not_submitted_yet: notSubmittedYet,
            shipped_count: shipped,
            waiting_to_pack_and_ship: waitingToShip,
            delivered_received_count: received
        };
    };

    const allOrders = ordersRes.data || [];
    const paidOrders = allOrders.filter(o => o.stripe_payment_status === 'paid');
    const totalPaidOrderRevenue = paidOrders.reduce((s, o) => s + (Number(o.amount_total) || 0), 0);

    const feedbacks = feedbacksRes.data || [];
    const avgMedal = feedbacks.length ? (feedbacks.reduce((s, f) => s + (Number(f.erem_minoseg) || 0), 0) / feedbacks.length).toFixed(2) : 0;
    const avgNps = feedbacks.length ? (feedbacks.reduce((s, f) => s + (Number(f.nps_score) || 0), 0) / feedbacks.length).toFixed(2) : 0;

    const leads = leadsRes.data || [];
    const uniqueLeadEmails = new Set(leads.map(l => (l.email || '').toLowerCase().trim()).filter(Boolean));
    const runnerEmails = new Set(realRuns.map(r => (r.runners?.email || '').toLowerCase().trim()).filter(Boolean));
    let convertedLeads = 0;
    let unsubscribedLeads = 0;
    uniqueLeadEmails.forEach(email => {
        const recs = leads.filter(l => (l.email || '').toLowerCase().trim() === email);
        if (recs.some(l => l.unsubscribed || l.source === 'unsubscribed')) unsubscribedLeads++;
        else if (recs.some(l => l.converted) || runnerEmails.has(email)) convertedLeads++;
    });

    const result = {
        timestamp: new Date().toISOString(),
        campaigns: {
            nagy_kevely_pilis: summarizeCampaignRuns(pilisRuns, 100),
            predikaloszek: summarizeCampaignRuns(predikaloRuns, 99),
            combined_total: summarizeCampaignRuns(realRuns, 199)
        },
        test_runs_excluded: testRunsCount,
        orders_summary: {
            total_orders_in_db: allOrders.length,
            paid_orders_count: paidOrders.length,
            total_paid_revenue_huf: totalPaidOrderRevenue
        },
        feedbacks_summary: {
            total_reviews: feedbacks.length,
            avg_medal_rating_out_of_5: Number(avgMedal),
            avg_nps_score_out_of_10: Number(avgNps)
        },
        leads_summary: {
            total_lead_records: leads.length,
            unique_leads: uniqueLeadEmails.size,
            converted_to_buyers: convertedLeads,
            unsubscribed: unsubscribedLeads,
            active_warm_leads_remaining: Math.max(0, uniqueLeadEmails.size - convertedLeads - unsubscribedLeads)
        }
    };

    if (includeRecent) {
        result.pending_approval_proofs = realRuns
            .filter(r => !r.completed && r.proof_submitted)
            .map(r => ({
                run_id: r.id,
                name: r.name || r.runners?.name,
                email: r.runners?.email,
                campaign: isPilisRunRecord(r) ? 'Nagy-Kevély' : 'Prédikálószék',
                serial_number: r.serial_number,
                proof_submitted_at: r.proof_submitted_at,
                proof_urls: r.proof_urls,
                strava_url: r.strava_url
            }));

        result.waiting_to_ship_runs = realRuns
            .filter(r => r.completed && !getShipObj(r).shipped)
            .map(r => {
                const sh = getShipObj(r);
                return {
                    run_id: r.id,
                    name: r.name || r.runners?.name,
                    email: r.runners?.email,
                    campaign: isPilisRunRecord(r) ? 'Nagy-Kevély' : 'Prédikálószék',
                    serial_number: r.serial_number,
                    completion_date: r.completion_date,
                    shipping_method: sh.method,
                    parcel_name: sh.parcel_name || sh.home_address
                };
            });

        result.recent_registrations = realRuns.slice(0, 12).map(r => ({
            run_id: r.id,
            name: r.name || r.runners?.name,
            email: r.runners?.email,
            campaign: isPilisRunRecord(r) ? 'Nagy-Kevély' : 'Prédikálószék',
            serial_number: r.serial_number,
            completed: r.completed,
            proof_submitted: r.proof_submitted,
            created_at: r.created_at
        }));
    }

    return result;
}

// 2. TOOL: query_supabase_table
async function toolQuerySupabaseTable(args = {}) {
    const table = (args.table || '').trim();
    if (!ALLOWED_TABLES.includes(table)) {
        return { error: `Nem engedélyezett vagy ismeretlen tábla: "${table}". Engedélyezett táblák: ${ALLOWED_TABLES.join(', ')}` };
    }

    const selectStr = args.select || '*';
    const limit = Math.min(Math.max(Number(args.limit) || 50, 1), 250);
    const orderBy = args.order_by || (table === 'meta_daily_metrics' ? 'date' : 'created_at');
    const ascending = Boolean(args.ascending);

    let query = supabase.from(table).select(selectStr);

    if (Array.isArray(args.filters)) {
        for (const f of args.filters) {
            if (!f || !f.column || !f.operator) continue;
            let val = f.value;
            if (val === 'true') val = true;
            else if (val === 'false') val = false;
            else if (val === 'null') val = null;
            else if (!isNaN(val) && val !== '' && typeof val === 'string' && !['ilike', 'in'].includes(f.operator)) {
                // Keep string if serial_number or phone, otherwise number works in PostgREST too
            }

            switch (f.operator) {
                case 'eq': query = query.eq(f.column, val); break;
                case 'neq': query = query.neq(f.column, val); break;
                case 'gt': query = query.gt(f.column, val); break;
                case 'gte': query = query.gte(f.column, val); break;
                case 'lt': query = query.lt(f.column, val); break;
                case 'lte': query = query.lte(f.column, val); break;
                case 'ilike': query = query.ilike(f.column, val); break;
                case 'is': query = query.is(f.column, val); break;
                case 'in': {
                    const arr = String(val).split(',').map(s => s.trim());
                    query = query.in(f.column, arr);
                    break;
                }
            }
        }
    }

    query = query.order(orderBy, { ascending }).limit(limit);

    const { data, error } = await query;
    if (error) {
        return { error: error.message, table };
    }

    return {
        table,
        count: (data || []).length,
        rows: data || []
    };
}

// 3. TOOL: get_financial_and_cashflow_data
async function toolGetFinancialAndCashflowData(args = {}) {
    const txLimit = Math.min(Math.max(Number(args.include_transactions_limit) || 40, 5), 150);

    // Fetch ALL Stripe, Supabase Storage, and Supabase DB queries in PARALLEL
    let stripeAvailableHuf = 0;
    let stripePendingHuf = 0;
    let stripeTransactions = [];
    let stripePayouts = [];
    let revolutCsvText = '';

    const [balRes, txRes, payoutRes, storageRes, runsRes, ordersRes] = await Promise.all([
        stripe.balance.retrieve().catch(e => { console.warn('Stripe balance warning:', e.message); return null; }),
        stripe.balanceTransactions.list({ limit: 100 }).catch(e => { console.warn('Stripe tx warning:', e.message); return null; }),
        stripe.payouts.list({ limit: 50 }).catch(e => { console.warn('Stripe payout warning:', e.message); return null; }),
        supabase.storage.from('medals').download('finance/revolut_statement.csv').catch(() => ({ data: null })),
        supabase.from('runs').select('id, campaign, serial_number, completed, is_test, name, runners(email)'),
        supabase.from('orders').select('*').eq('stripe_payment_status', 'paid')
    ]);

    if (balRes) {
        stripeAvailableHuf = (balRes.available || []).reduce((s, b) => b.currency.toLowerCase() === 'huf' ? s + (b.amount / 100) : s, 0);
        stripePendingHuf = (balRes.pending || []).reduce((s, b) => b.currency.toLowerCase() === 'huf' ? s + (b.amount / 100) : s, 0);
    }
    if (txRes && txRes.data) {
        stripeTransactions = txRes.data.map(t => ({
            id: t.id,
            date: new Date(t.created * 1000).toISOString().slice(0, 10),
            type: t.type,
            amount_huf: t.amount / 100,
            fee_huf: t.fee / 100,
            net_huf: t.net / 100,
            status: t.status,
            description: t.description
        }));
    }
    if (payoutRes && payoutRes.data) {
        stripePayouts = payoutRes.data.map(p => ({
            id: p.id,
            created_date: new Date(p.created * 1000).toISOString().slice(0, 10),
            arrival_date: new Date(p.arrival_date * 1000).toISOString().slice(0, 10),
            amount_huf: p.amount / 100,
            status: p.status
        }));
    }
    if (storageRes && storageRes.data && !storageRes.error) {
        try { revolutCsvText = await storageRes.data.text(); } catch (e) {}
    }

    if (!revolutCsvText || revolutCsvText.length < 20) {
        const candidates = [
            path.join(__dirname, '../../revolut_statement.csv'),
            path.join(process.cwd(), 'landing_predikalo1', 'revolut_statement.csv'),
            path.join(process.cwd(), 'revolut_statement.csv')
        ];
        for (const p of candidates) {
            if (fs.existsSync(p)) {
                revolutCsvText = fs.readFileSync(p, 'utf8');
                break;
            }
        }
    }

    const revolutRows = [];
    const categoryTotals = {};
    if (revolutCsvText) {
        const lines = revolutCsvText.replace(/\r/g, '').trim().split('\n');
        for (let i = 1; i < lines.length; i++) {
            const parts = lines[i].trim().split(',');
            if (parts.length < 6) continue;
            const type = (parts[0] || '').trim();
            const startedDate = (parts[2] || '').trim();
            const completedDate = (parts[3] || '').trim();
            const description = (parts[4] || '').trim();
            const amount = parseFloat(parts[5]) || 0;
            const fee = parseFloat(parts[6]) || 0;
            const currency = (parts[7] || 'HUF').trim();
            const state = (parts[8] || '').trim();
            const balance = parseFloat(parts[9]) || 0;

            const descLower = description.toLowerCase();
            let category = 'other';
            if (descLower.includes('facebook') || descLower.includes('meta')) category = 'marketing_meta';
            else if (descLower.includes('stripe') || descLower.includes('technology europe')) category = 'stripe_payout';
            else if (descLower.includes('foxpost')) category = 'shipping_foxpost';
            else if (descLower.includes('simplep') || descLower.includes('boríték') || descLower.includes('csomagol')) category = 'packaging';
            else if (descLower.includes('péter lászló') || descLower.includes('konyvel') || descLower.includes('könyvel')) category = 'accounting_opex';
            else if (descLower.includes('kboss') || descLower.includes('számlázz') || descLower.includes('szamlazz')) category = 'software_szamlazz';
            else if (descLower.includes('alibaba') || descLower.includes('devizaváltás') || descLower.includes('usd') || descLower.includes('érem')) category = 'medal_capex';
            else if (descLower.includes('google pay') || descLower.includes('feltöltés') || descLower.includes('topup')) category = 'capital_deposit';
            else if (descLower.includes('nav') || descLower.includes('adó')) category = 'tax_nav';
            else if (descLower.includes('cashback') || descLower.includes('pénzvisszatérítés')) category = 'cashback';

            if (!categoryTotals[category]) categoryTotals[category] = { count: 0, total_amount_huf: 0 };
            categoryTotals[category].count++;
            categoryTotals[category].total_amount_huf += (amount - fee);

            revolutRows.push({
                date: completedDate || startedDate,
                type,
                description,
                amount_huf: amount,
                fee_huf: fee,
                currency,
                state,
                balance_huf: balance,
                category
            });
        }
    }

    revolutRows.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
    const revolutBalanceHuf = revolutRows.length > 0 ? (revolutRows[0].balance_huf || 0) : 0;

    // runsRes & ordersRes already fetched in parallel above

    const realRuns = (runsRes.data || []).filter(r => !isTestRunRecord(r));
    const pilisSold = realRuns.filter(r => isPilisRunRecord(r)).length;
    const predikaloSold = realRuns.filter(r => !isPilisRunRecord(r)).length;
    const pilisRemaining = Math.max(0, 100 - pilisSold);
    const predikaloRemaining = Math.max(0, 99 - predikaloSold);

    // Unit capex ~1630 HUF per medal
    const unitCostHuf = 1630;
    const inventoryValueHuf = (pilisRemaining + predikaloRemaining) * unitCostHuf;
    const totalLiquidHuf = revolutBalanceHuf + stripeAvailableHuf;

    const paidOrders = ordersRes.data || [];
    const pilisOrders = paidOrders.filter(o => (o.campaign || '').toLowerCase().includes('pilis') || (o.campaign || '').toLowerCase().includes('kevely'));
    const predikaloOrders = paidOrders.filter(o => !((o.campaign || '').toLowerCase().includes('pilis') || (o.campaign || '').toLowerCase().includes('kevely')));

    const metaRows = getCreativeCsvData();
    const pilisMetaSpend = metaRows.filter(m => (m.campaign_name || '').toLowerCase().includes('pilis') || (m.campaign_name || '').toLowerCase().includes('kevély') || (m.campaign_name || '').toLowerCase().includes('kevely')).reduce((s, m) => s + (m.spend || 0), 0);
    const predikaloMetaSpend = metaRows.filter(m => !((m.campaign_name || '').toLowerCase().includes('pilis') || (m.campaign_name || '').toLowerCase().includes('kevély') || (m.campaign_name || '').toLowerCase().includes('kevely'))).reduce((s, m) => s + (m.spend || 0), 0);

    return {
        balance_sheet: {
            revolut_pro_balance_huf: Math.round(revolutBalanceHuf),
            stripe_available_balance_huf: Math.round(stripeAvailableHuf),
            stripe_pending_balance_huf: Math.round(stripePendingHuf),
            total_liquid_cash_huf: Math.round(totalLiquidHuf),
            total_liquid_including_pending_huf: Math.round(totalLiquidHuf + stripePendingHuf),
            inventory: {
                nagy_kevely_remaining_medals: pilisRemaining,
                predikaloszek_remaining_medals: predikaloRemaining,
                total_remaining_medals: pilisRemaining + predikaloRemaining,
                estimated_inventory_cost_value_huf: Math.round(inventoryValueHuf),
                potential_gross_revenue_of_remaining_stock_huf: (pilisRemaining + predikaloRemaining) * 7990
            },
            total_balance_sheet_equity_huf: Math.round(totalLiquidHuf + stripePendingHuf + inventoryValueHuf)
        },
        campaign_pnl_summary: {
            nagy_kevely: {
                medals_sold: pilisSold,
                paid_orders_count: pilisOrders.length,
                gross_order_revenue_huf: pilisOrders.reduce((s, o) => s + (Number(o.amount_total) || 0), 0),
                meta_ad_spend_net_huf: Math.round(pilisMetaSpend),
                meta_ad_spend_with_27pct_vat_huf: Math.round(pilisMetaSpend * 1.27),
                medal_capex_100_units_huf: 163000
            },
            predikaloszek: {
                medals_sold: predikaloSold,
                paid_orders_count: predikaloOrders.length,
                gross_order_revenue_huf: predikaloOrders.reduce((s, o) => s + (Number(o.amount_total) || 0), 0),
                meta_ad_spend_net_huf: Math.round(predikaloMetaSpend),
                meta_ad_spend_with_27pct_vat_huf: Math.round(predikaloMetaSpend * 1.27),
                medal_capex_100_units_huf: 163000
            }
        },
        revolut_category_totals: categoryTotals,
        recent_revolut_transactions: revolutRows.slice(0, txLimit),
        recent_stripe_payouts: stripePayouts.slice(0, 15),
        recent_stripe_transactions: stripeTransactions.slice(0, txLimit)
    };
}

// 4. TOOL: get_marketing_and_creatives_data
async function toolGetMarketingAndCreativesData(args = {}) {
    const campFilter = (args.campaign_filter || 'all').toLowerCase();
    const days = Number(args.days) || 0;

    let rows = getCreativeCsvData();
    if (!rows || rows.length === 0) {
        const { data } = await supabase.from('meta_daily_metrics').select('*').order('date', { ascending: false });
        rows = data || [];
    }

    if (campFilter === 'pilis' || campFilter === 'nagykevely') {
        rows = rows.filter(r => {
            const c = ((r.campaign_name || '') + ' ' + (r.adset_name || '') + ' ' + (r.ad_name || '')).toLowerCase();
            return c.includes('pilis') || c.includes('kevély') || c.includes('kevely');
        });
    } else if (campFilter === 'predikalo' || campFilter === 'predikaloszek') {
        rows = rows.filter(r => {
            const c = ((r.campaign_name || '') + ' ' + (r.adset_name || '') + ' ' + (r.ad_name || '')).toLowerCase();
            return !(c.includes('pilis') || c.includes('kevély') || c.includes('kevely'));
        });
    }

    if (days > 0) {
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - days);
        const cutoffStr = cutoff.toISOString().slice(0, 10);
        rows = rows.filter(r => (r.date || '') >= cutoffStr);
    }

    // Aggregate by Creative (ad_name)
    const byCreative = {};
    const byDate = {};
    let totalSpend = 0;
    let totalImpressions = 0;
    let totalLinkClicks = 0;
    let totalPurchases = 0;
    let totalRevenue = 0;

    for (const r of rows) {
        const adName = r.ad_name || 'Ismeretlen kreatív';
        if (!byCreative[adName]) {
            byCreative[adName] = {
                ad_name: adName,
                campaign_name: r.campaign_name,
                adset_name: r.adset_name,
                spend_huf: 0,
                impressions: 0,
                link_clicks: 0,
                purchases: 0,
                revenue_huf: 0
            };
        }
        const c = byCreative[adName];
        c.spend_huf += Number(r.spend || 0);
        c.impressions += Number(r.impressions || 0);
        c.link_clicks += Number(r.link_clicks || 0);
        c.purchases += Number(r.purchases || 0);
        c.revenue_huf += Number(r.revenue || 0);

        const d = r.date || 'unknown';
        if (!byDate[d]) {
            byDate[d] = { date: d, spend_huf: 0, impressions: 0, link_clicks: 0, purchases: 0, revenue_huf: 0 };
        }
        byDate[d].spend_huf += Number(r.spend || 0);
        byDate[d].impressions += Number(r.impressions || 0);
        byDate[d].link_clicks += Number(r.link_clicks || 0);
        byDate[d].purchases += Number(r.purchases || 0);
        byDate[d].revenue_huf += Number(r.revenue || 0);

        totalSpend += Number(r.spend || 0);
        totalImpressions += Number(r.impressions || 0);
        totalLinkClicks += Number(r.link_clicks || 0);
        totalPurchases += Number(r.purchases || 0);
        totalRevenue += Number(r.revenue || 0);
    }

    const creativesList = Object.values(byCreative).map(c => ({
        ...c,
        spend_huf: Math.round(c.spend_huf),
        revenue_huf: Math.round(c.revenue_huf),
        ctr_pct: c.impressions > 0 ? Number(((c.link_clicks / c.impressions) * 100).toFixed(2)) : 0,
        cpc_huf: c.link_clicks > 0 ? Math.round(c.spend_huf / c.link_clicks) : 0,
        cpa_huf: c.purchases > 0 ? Math.round(c.spend_huf / c.purchases) : null,
        roas: c.spend_huf > 0 ? Number((c.revenue_huf / c.spend_huf).toFixed(2)) : 0
    })).sort((a, b) => b.spend_huf - a.spend_huf);

    const dailyList = Object.values(byDate).sort((a, b) => b.date.localeCompare(a.date)).slice(0, 30);

    return {
        filter_applied: { campaign_filter: campFilter, days: days || 'all' },
        totals: {
            total_spend_net_huf: Math.round(totalSpend),
            total_spend_gross_with_27vat_huf: Math.round(totalSpend * 1.27),
            total_impressions: totalImpressions,
            total_link_clicks: totalLinkClicks,
            avg_ctr_pct: totalImpressions > 0 ? Number(((totalLinkClicks / totalImpressions) * 100).toFixed(2)) : 0,
            avg_cpc_huf: totalLinkClicks > 0 ? Math.round(totalSpend / totalLinkClicks) : 0,
            meta_reported_purchases: totalPurchases,
            meta_reported_revenue_huf: Math.round(totalRevenue),
            avg_cpa_huf: totalPurchases > 0 ? Math.round(totalSpend / totalPurchases) : null,
            blended_roas: totalSpend > 0 ? Number((totalRevenue / totalSpend).toFixed(2)) : 0
        },
        creatives_breakdown: creativesList,
        daily_breakdown_last_30_days: dailyList
    };
}

// 5. TOOL: read_knowledge_graph
async function toolReadKnowledgeGraph(args = {}) {
    const knowledgeRootCandidates = [
        path.resolve(__dirname, '../../../knowledge'),
        path.resolve(process.cwd(), '../knowledge'),
        path.resolve(process.cwd(), 'knowledge')
    ];
    let knowledgeDir = null;
    for (const cand of knowledgeRootCandidates) {
        if (fs.existsSync(cand)) {
            knowledgeDir = cand;
            break;
        }
    }

    if (!knowledgeDir) {
        return { error: 'A knowledge/ mappa nem található a szerveren.' };
    }

    // Helper to list all markdown files recursively
    function listMdFiles(dir, base = '') {
        let results = [];
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
            const rel = base ? `${base}/${entry.name}` : entry.name;
            if (entry.isDirectory()) {
                results = results.concat(listMdFiles(path.join(dir, entry.name), rel));
            } else if (entry.name.endsWith('.md')) {
                results.push(rel);
            }
        }
        return results;
    }

    const allFiles = listMdFiles(knowledgeDir);

    if (args.search_term) {
        const term = args.search_term.toLowerCase();
        const matches = [];
        for (const f of allFiles) {
            const content = fs.readFileSync(path.join(knowledgeDir, f), 'utf8');
            if (content.toLowerCase().includes(term)) {
                matches.push({
                    file: f,
                    excerpt: content.slice(0, 600)
                });
            }
        }
        return { search_term: args.search_term, matches_count: matches.length, matches };
    }

    const reqFile = (args.file_path || '').trim();
    if (!reqFile || reqFile === 'list' || reqFile === 'INDEX.md') {
        const indexPath = path.join(knowledgeDir, 'INDEX.md');
        const indexContent = fs.existsSync(indexPath) ? fs.readFileSync(indexPath, 'utf8') : '';
        return {
            available_files: allFiles,
            index_md_content: indexContent
        };
    }

    if (reqFile === 'campaigns.json' || reqFile.endsWith('campaigns.json')) {
        const campPath = path.resolve(__dirname, '../../config/campaigns.json');
        if (fs.existsSync(campPath)) {
            return { file: 'config/campaigns.json', content: JSON.parse(fs.readFileSync(campPath, 'utf8')) };
        }
    }

    const normalized = reqFile.replace(/^knowledge\//, '').replace(/\.\./g, '');
    const targetPath = path.join(knowledgeDir, normalized);
    if (fs.existsSync(targetPath) && fs.statSync(targetPath).isFile()) {
        return {
            file: normalized,
            content: fs.readFileSync(targetPath, 'utf8')
        };
    }

    // Fuzzy match filename
    const found = allFiles.find(f => f.toLowerCase().includes(normalized.toLowerCase()));
    if (found) {
        return {
            file: found,
            content: fs.readFileSync(path.join(knowledgeDir, found), 'utf8')
        };
    }

    return {
        error: `A kért fájl nem található: "${reqFile}"`,
        available_files: allFiles
    };
}

// 6. TOOL: search_and_read_emails (IMAP / Gmail integration)
async function toolSearchAndReadEmails(args = {}) {
    const accountType = args.account === 'secondary' ? 'secondary' : 'primary';
    const user = accountType === 'secondary'
        ? (process.env.GMAIL_SECOND_USER || process.env.GMAIL_USER || 'vitasteps.team@gmail.com')
        : (process.env.GMAIL_USER || 'vitasteps.team@gmail.com');
    const pass = accountType === 'secondary'
        ? (process.env.GMAIL_SECOND_APP_PASSWORD || process.env.GMAIL_APP_PASSWORD || process.env.SMTP_PASSWORD)
        : (process.env.GMAIL_APP_PASSWORD || process.env.SMTP_PASSWORD);

    if (!pass) {
        return {
            error: 'Nincs beállítva email jelszó (SMTP_PASSWORD vagy GMAIL_APP_PASSWORD) a környezeti változókban.'
        };
    }

    const limit = Math.min(Math.max(Number(args.limit) || 10, 1), 25);
    const folderInput = (args.folder || 'INBOX').trim();
    const queryStr = (args.query || '').trim();
    const fromFilter = (args.from || '').trim();
    const subjectFilter = (args.subject || '').trim();
    const unreadOnly = Boolean(args.unread_only);

    const client = new ImapFlow({
        host: 'imap.gmail.com',
        port: 993,
        secure: true,
        auth: { user, pass },
        logger: false
    });

    try {
        await client.connect();

        // Resolve folder name if SENT requested
        let targetMailbox = folderInput;
        if (folderInput.toUpperCase() === 'SENT') {
            const list = await client.list();
            const sentBox = list.find(b => b.specialUse === '\\Sent' || b.path.toLowerCase().includes('sent') || b.path.toLowerCase().includes('elküldött'));
            if (sentBox) targetMailbox = sentBox.path;
        }

        const lock = await client.getMailboxLock(targetMailbox);
        const emails = [];
        try {
            const totalExists = client.mailbox.exists || 0;
            if (totalExists === 0) {
                return { account: user, folder: targetMailbox, total_in_folder: 0, emails: [] };
            }

            // Build IMAP search criteria or fetch recent messages and filter
            let searchCriteria = {};
            if (unreadOnly) searchCriteria.seen = false;
            if (fromFilter) searchCriteria.from = fromFilter;
            if (subjectFilter) searchCriteria.subject = subjectFilter;

            let uids = [];
            const hasSpecificCriteria = unreadOnly || fromFilter || subjectFilter || queryStr;

            if (hasSpecificCriteria) {
                try {
                    if (queryStr && !fromFilter && !subjectFilter) {
                        // Use Gmail X-GM-RAW or OR search, fallback to fetching last 60 messages and filtering in JS for full UTF-8 / Hungarian support
                        const startSeq = Math.max(1, totalExists - 60 + 1);
                        const messages = [];
                        for await (const msg of client.fetch(`${startSeq}:*`, { uid: true, envelope: true, flags: true, source: true })) {
                            messages.push(msg);
                        }
                        messages.reverse();
                        const qLower = queryStr.toLowerCase();
                        for (const msg of messages) {
                            if (emails.length >= limit) break;
                            const parsed = await simpleParser(msg.source);
                            const subj = (parsed.subject || '').toLowerCase();
                            const fromText = (parsed.from?.text || '').toLowerCase();
                            const toText = (parsed.to?.text || '').toLowerCase();
                            const bodyText = (parsed.text || '').toLowerCase();
                            if (subj.includes(qLower) || fromText.includes(qLower) || toText.includes(qLower) || bodyText.includes(qLower)) {
                                emails.push({
                                    uid: msg.uid,
                                    date: parsed.date ? parsed.date.toISOString() : msg.envelope?.date,
                                    from: parsed.from?.text || '',
                                    to: parsed.to?.text || '',
                                    subject: parsed.subject || '(Nincs tárgy)',
                                    unread: !msg.flags?.has('\\Seen'),
                                    snippet: (parsed.text || '').replace(/\s+/g, ' ').trim().slice(0, 1200)
                                });
                            }
                        }
                        return {
                            account: user,
                            folder: targetMailbox,
                            total_in_folder: totalExists,
                            query: queryStr,
                            returned_count: emails.length,
                            emails
                        };
                    } else {
                        uids = await client.search(searchCriteria, { uid: true });
                    }
                } catch (searchErr) {
                    uids = [];
                }
            }

            if (uids && uids.length > 0) {
                const targetUids = uids.slice(-limit).reverse();
                for await (const msg of client.fetch(targetUids, { uid: true, envelope: true, flags: true, source: true }, { uid: true })) {
                    const parsed = await simpleParser(msg.source);
                    emails.push({
                        uid: msg.uid,
                        date: parsed.date ? parsed.date.toISOString() : msg.envelope?.date,
                        from: parsed.from?.text || '',
                        to: parsed.to?.text || '',
                        subject: parsed.subject || '(Nincs tárgy)',
                        unread: !msg.flags?.has('\\Seen'),
                        snippet: (parsed.text || '').replace(/\s+/g, ' ').trim().slice(0, 1200)
                    });
                }
                emails.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
            } else if (!hasSpecificCriteria) {
                const startSeq = Math.max(1, totalExists - limit + 1);
                for await (const msg of client.fetch(`${startSeq}:*`, { uid: true, envelope: true, flags: true, source: true })) {
                    const parsed = await simpleParser(msg.source);
                    emails.push({
                        uid: msg.uid,
                        date: parsed.date ? parsed.date.toISOString() : msg.envelope?.date,
                        from: parsed.from?.text || '',
                        to: parsed.to?.text || '',
                        subject: parsed.subject || '(Nincs tárgy)',
                        unread: !msg.flags?.has('\\Seen'),
                        snippet: (parsed.text || '').replace(/\s+/g, ' ').trim().slice(0, 1200)
                    });
                }
                emails.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
            }

            return {
                account: user,
                folder: targetMailbox,
                total_in_folder: totalExists,
                returned_count: emails.length,
                emails
            };
        } finally {
            lock.release();
        }
    } catch (err) {
        return {
            error: `IMAP csatlakozási vagy olvasási hiba (${user}): ${err.message}`
        };
    } finally {
        try { await client.logout(); } catch (e) {}
    }
}

// Dispatcher for Gemini Tool Calls
async function executeToolCall(name, args) {
    try {
        switch (name) {
            case 'get_database_overview': {
                const inc = args?.include_recent_items !== false;
                return await getCachedOrFetch(`db_overview:${inc}`, 60000, () => toolGetDatabaseOverview(args));
            }
            case 'query_supabase_table': {
                const key = `query_table:${JSON.stringify(args || {})}`;
                return await getCachedOrFetch(key, 45000, () => toolQuerySupabaseTable(args));
            }
            case 'get_financial_and_cashflow_data': {
                const lim = Math.min(Math.max(Number(args?.include_transactions_limit) || 40, 5), 150);
                return await getCachedOrFetch(`finance:${lim}`, 60000, () => toolGetFinancialAndCashflowData(args));
            }
            case 'get_marketing_and_creatives_data': {
                const cf = (args?.campaign_filter || 'all').toLowerCase();
                const d = Number(args?.days) || 0;
                return await getCachedOrFetch(`marketing:${cf}:${d}`, 60000, () => toolGetMarketingAndCreativesData(args));
            }
            case 'read_knowledge_graph': {
                const key = `kg:${JSON.stringify(args || {})}`;
                return await getCachedOrFetch(key, 300000, () => toolReadKnowledgeGraph(args));
            }
            case 'search_and_read_emails': {
                const key = `emails:${JSON.stringify(args || {})}`;
                return await getCachedOrFetch(key, 45000, () => toolSearchAndReadEmails(args));
            }
            default:
                return { error: `Ismeretlen tool: ${name}` };
        }
    } catch (err) {
        console.error(`Tool execution error [${name}]:`, err);
        return { error: `Hiba a(z) ${name} futtatása közben: ${err.message}` };
    }
}

const TOOL_LABELS = {
    get_database_overview: '🗄️ Supabase Összefoglaló',
    query_supabase_table: '🔍 Supabase Tábla Lekérdezés',
    get_financial_and_cashflow_data: '💳 Pénzügy, Revolut & Stripe',
    get_marketing_and_creatives_data: '📊 Meta Ads & Kreatív Riport',
    read_knowledge_graph: '🧠 Knowledge Graph Tudásbázis',
    search_and_read_emails: '📧 Gmail Postafiók'
};

// ─────────────────────────────────────────────────────────────────────────────
// MAIN HTTP HANDLER: handleAiAssistant(req, res)
// ─────────────────────────────────────────────────────────────────────────────
async function handleAiAssistant(req, res) {
    const type = req.body?.type || req.query?.type;
    const action = req.body?.action || req.query?.action;

    // 1. Status Check Endpoint (GET or type=ai_status)
    if (req.method === 'GET' || type === 'ai_status' || action === 'ai_status') {
        warmUpAiCache();
        const hasServerGeminiKey = Boolean(process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY);
        const hasPrimaryGmail = Boolean(process.env.SMTP_PASSWORD || process.env.GMAIL_APP_PASSWORD);
        const hasSecondaryGmail = Boolean(process.env.GMAIL_SECOND_USER && process.env.GMAIL_SECOND_APP_PASSWORD);

        return res.status(200).json({
            success: true,
            status: {
                gemini_configured: hasServerGeminiKey,
                supabase_configured: Boolean(process.env.SUPABASE_SERVICE_ROLE_KEY),
                stripe_configured: Boolean(process.env.STRIPE_SECRET_KEY),
                meta_csv_available: getCreativeCsvData().length > 0,
                gmail_primary: hasPrimaryGmail ? (process.env.GMAIL_USER || 'vitasteps.team@gmail.com') : null,
                gmail_secondary: hasSecondaryGmail ? process.env.GMAIL_SECOND_USER : null
            },
            models: [
                { id: 'gemini-3.1-flash-lite', label: '⚡ Gemini 3.1 Flash-Lite (Leggyorsabb, 1-2 mp válaszidő)' },
                { id: 'gemini-3.5-flash', label: '🚀 Gemini 3.5 Flash (Részletes elemzés)' },
                { id: 'gemini-3.1-pro-preview', label: '🧠 Gemini 3.1 Pro (Mély stratégiai & P&L)' }
            ]
        });
    }

    // 2. Chat Message Execution (POST)
    const {
        message,
        history = [],
        model = 'gemini-3.1-flash-lite',
        api_key_override = ''
    } = req.body || {};

    if (!message || typeof message !== 'string') {
        return res.status(400).json({ error: 'Hiányzó üzenet (message).' });
    }

    const apiKey = (api_key_override || process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || '').trim();
    if (!apiKey) {
        return res.status(400).json({
            error: 'GEMINI_API_KEY_MISSING',
            message: 'Hiányzik a Google AI Studio (Gemini) API kulcs! Add hozzá a .env fájlhoz (GEMINI_API_KEY=...) vagy add meg közvetlenül a felületen.'
        });
    }

    // Map legacy / overloaded model names automatically
    const MODEL_MAP = {
        'gemini-2.5-flash': 'gemini-3.1-flash-lite',
        'gemini-2.0-flash': 'gemini-3.1-flash-lite',
        'gemini-3.8-flash': 'gemini-3.1-flash-lite',
        'gemini-3.8-flash-lite': 'gemini-3.1-flash-lite',
        'gemini-2.5-pro': 'gemini-3.1-pro-preview',
        'gemini-3.8-pro': 'gemini-3.1-pro-preview'
    };
    const normalizedModel = MODEL_MAP[model] || model;
    let selectedModel = ['gemini-3.1-flash-lite', 'gemini-3.5-flash', 'gemini-3.1-pro-preview'].includes(normalizedModel)
        ? normalizedModel
        : 'gemini-3.1-flash-lite';

    // Build conversation contents for Gemini API
    const contents = [];
    if (Array.isArray(history)) {
        const recentHistory = history.slice(-12);
        for (const h of recentHistory) {
            if (!h || !h.text) continue;
            contents.push({
                role: h.role === 'model' || h.role === 'assistant' ? 'model' : 'user',
                parts: [{ text: String(h.text) }]
            });
        }
    }
    contents.push({
        role: 'user',
        parts: [{ text: message }]
    });

    const toolsUsed = [];
    const MAX_TURNS = 6;

    try {
        const liveSnapshotAppendix = await buildLiveSnapshotContext();
        const fullSystemPrompt = SYSTEM_INSTRUCTION + liveSnapshotAppendix;
        let useThinkingConfig = true;

        for (let turn = 0; turn < MAX_TURNS; turn++) {
            const genConfig = {
                temperature: 0.2,
                maxOutputTokens: 2048
            };
            if (useThinkingConfig && !selectedModel.includes('lite')) {
                genConfig.thinkingConfig = {
                    thinkingBudget: selectedModel.includes('flash') ? 128 : 512
                };
            }

            const payload = {
                systemInstruction: {
                    parts: [{ text: fullSystemPrompt }]
                },
                contents,
                tools: GEMINI_TOOLS,
                generationConfig: genConfig
            };

            const { res: geminiRes, data: geminiData, usedModel } = await callGeminiWithResilience(selectedModel, apiKey, payload);
            selectedModel = usedModel;

            if (!geminiRes.ok) {
                const errMsg = geminiData?.error?.message || `Gemini API hiba (${geminiRes.status})`;
                return res.status(geminiRes.status === 400 || geminiRes.status === 403 ? 400 : 500).json({
                    error: errMsg,
                    details: geminiData?.error
                });
            }

            const candidate = geminiData?.candidates?.[0];
            const modelContent = candidate?.content;
            if (!modelContent || !Array.isArray(modelContent.parts)) {
                return res.status(200).json({
                    success: true,
                    reply: 'Nem érkezett válasz a modelltől.',
                    model: selectedModel,
                    tools_used: toolsUsed
                });
            }

            // Append the model's turn to contents
            contents.push(modelContent);

            // Check if the model requested any functionCalls
            const functionCalls = modelContent.parts.filter(p => p.functionCall);
            if (functionCalls.length === 0) {
                // Final text response reached
                const finalText = modelContent.parts
                    .filter(p => typeof p.text === 'string')
                    .map(p => p.text)
                    .join('\n')
                    .trim();

                if (toolsUsed.length === 0 && liveSnapshotAppendix) {
                    toolsUsed.push({
                        name: 'live_snapshot',
                        label: '⚡ Élő Gyorsítótár (DB • Pénzügy • Meta)'
                    });
                }
                return res.status(200).json({
                    success: true,
                    reply: finalText || 'Kész.',
                    model: selectedModel,
                    tools_used: toolsUsed
                });
            }

            // Execute all requested function calls truly in PARALLEL via Promise.all
            const responseParts = await Promise.all(functionCalls.map(async (part) => {
                const fc = part.functionCall;
                const toolName = fc.name;
                const toolArgs = fc.args || {};

                let detailSuffix = '';
                if (toolName === 'query_supabase_table' && toolArgs.table) {
                    detailSuffix = ` (${toolArgs.table})`;
                } else if (toolName === 'read_knowledge_graph' && toolArgs.file_path) {
                    detailSuffix = ` (${toolArgs.file_path})`;
                } else if (toolName === 'search_and_read_emails' && toolArgs.query) {
                    detailSuffix = ` ("${toolArgs.query}")`;
                }

                toolsUsed.push({
                    name: toolName,
                    label: (TOOL_LABELS[toolName] || toolName) + detailSuffix,
                    args: toolArgs
                });

                const toolResult = await executeToolCall(toolName, toolArgs);
                return {
                    functionResponse: {
                        name: toolName,
                        response: { result: toolResult }
                    }
                };
            }));

            // Append function responses as a 'user' (or 'function') turn
            contents.push({
                role: 'user',
                parts: responseParts
            });
        }

        // If loop exhausted MAX_TURNS, return whatever text we have
        return res.status(200).json({
            success: true,
            reply: 'Az elemzés elérte a maximális lépésszámot. Kérlek pontosítsd a kérdést!',
            model: selectedModel,
            tools_used: toolsUsed
        });

    } catch (err) {
        console.error('AI Assistant error:', err);
        return res.status(500).json({
            error: 'Hiba történt az AI Asszisztens futtatása közben: ' + err.message
        });
    }
}

module.exports = {
    handleAiAssistant,
    executeToolCall
};
