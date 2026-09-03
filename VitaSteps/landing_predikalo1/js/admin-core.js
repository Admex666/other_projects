// ===== ADMIN CORE MODULE: Auth, State, Utilities, Config =====

let CAMPAIGNS_CONFIG = {
    predikaloszek: {
        id: "predikaloszek",
        name: "Prédikálószék",
        icon: "🏔️",
        color: "#f97316",
        prefix: "",
        limit: 100,
        fixedCost: 163000
    },
    pilis: {
        id: "pilis",
        name: "Nagy-Kevély",
        icon: "⭐",
        color: "#a855f7",
        prefix: "-PK",
        limit: 100,
        fixedCost: 163000
    }
};

// Global App State
let adminSecret = '';
let allRuns = [];
let currentFilter = 'pending'; // 'pending', 'approved', 'all', 'logistics', 'marketing', 'finance'

// Helper to check if a run belongs to Pilis / Nagy-Kevély
function isPilisRun(run) {
    if (!run) return false;
    const c = (run.campaign || '').toLowerCase();
    const s = (run.serial_number || '').toLowerCase();
    return c.includes('pilis') || c.includes('kevely') || s.includes('-pk') || s.includes('999');
}

// Helper to determine Campaign Info for a run
function getCampaignInfo(run) {
    if (isPilisRun(run)) {
        return {
            id: 'pilis',
            name: CAMPAIGNS_CONFIG.pilis?.name || 'A Nagy-Kevély csillagai',
            icon: '🌌',
            color: '#c4ff00',
            limit: CAMPAIGNS_CONFIG.pilis?.limit || 100,
            ...(CAMPAIGNS_CONFIG.pilis || {})
        };
    }
    return {
        id: 'predikaloszek',
        name: CAMPAIGNS_CONFIG.predikaloszek?.name || 'Prédikálószék Vertical',
        icon: '🏔️',
        color: '#38bdf8',
        limit: CAMPAIGNS_CONFIG.predikaloszek?.limit || 100,
        ...(CAMPAIGNS_CONFIG.predikaloszek || {})
    };
}

// Helper to extract primary shipment object
function getShipment(run) {
    if (!run || !run.shipments) return {};
    return Array.isArray(run.shipments) ? (run.shipments[0] || {}) : run.shipments;
}

function isTestRun(r) {
    if (r.is_test) return true;
    const s = (r.serial_number || '').toUpperCase();
    const e = (r.runners?.email || '').toLowerCase();
    const n = (r.name || r.runners?.name || '').toLowerCase();
    return s.includes('TEST') || s.includes('999') || e.includes('test') || e.includes('admex') || n.includes('próba') || n.includes('teszt') || n.includes('minta');
}

function formatHUF(val) {
    return Math.round(val).toLocaleString('hu-HU') + ' Ft';
}

function formatDate(isoStr) {
    if (!isoStr) return '–';
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return isoStr;
    return d.toLocaleDateString('hu-HU', { year: 'numeric', month: '2-digit', day: '2-digit' });
}

// Authentication Handlers
async function login() {
    const input = document.getElementById('admin-password');
    const errEl = document.getElementById('login-error');
    const secret = input.value.trim();

    if (!secret) {
        errEl.textContent = 'Kérlek add meg a jelszót!';
        errEl.style.display = 'block';
        return;
    }

    errEl.style.display = 'none';

    try {
        const res = await fetch('/api/admin-approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'ping', admin_secret: secret })
        });

        if (res.status === 401) {
            errEl.textContent = 'Hibás jelszó!';
            errEl.style.display = 'block';
            return;
        }

        if (!res.ok) {
            errEl.textContent = 'Hiba történt a belépéskor.';
            errEl.style.display = 'block';
            return;
        }

        adminSecret = secret;
        sessionStorage.setItem('vs_admin_secret', secret);
        showApp();
        loadData();

    } catch (err) {
        errEl.textContent = 'Hálózati hiba történt.';
        errEl.style.display = 'block';
    }
}

function logout() {
    sessionStorage.removeItem('vs_admin_secret');
    adminSecret = '';
    document.getElementById('screen-dashboard').style.display = 'none';
    document.getElementById('screen-login').style.display = 'block';
    document.getElementById('admin-password').value = '';
}

function showApp() {
    document.getElementById('screen-login').style.display = 'none';
    document.getElementById('screen-dashboard').style.display = 'block';
}

// Data Fetching
async function loadData() {
    try {
        const res = await fetch(`/api/admin-data?secret=${encodeURIComponent(adminSecret)}`);
        if (!res.ok) throw new Error('Nem sikerült betölteni az adatokat');

        const data = await res.json();
        allRuns = data.runs || [];

        if (data.campaigns) {
            CAMPAIGNS_CONFIG = {
                ...CAMPAIGNS_CONFIG,
                ...data.campaigns
            };
            if (CAMPAIGNS_CONFIG.pilis) CAMPAIGNS_CONFIG.pilis.id = 'pilis';
            if (CAMPAIGNS_CONFIG.predikaloszek) CAMPAIGNS_CONFIG.predikaloszek.id = 'predikaloszek';
        }

        updateStats();
        renderList();

    } catch (err) {
        console.error('Data load error:', err);
        alert('Hiba történt az adatok betöltésekor: ' + err.message);
    }
}

// Init on Load
document.addEventListener('DOMContentLoaded', () => {
    const saved = sessionStorage.getItem('vs_admin_secret');
    if (saved) {
        adminSecret = saved;
        showApp();
        loadData();
    }
});
