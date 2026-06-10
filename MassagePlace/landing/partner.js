// Generálunk egy egyedi session ID-t a partner látogatásához
const sessionId = 'part_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now().toString(36);

// Supabase konfiguráció
const SUPABASE_URL = "https://vggmrmgctzanoutabvvl.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZnZ21ybWdjdHphbm91dGFidnZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkzODIzMzgsImV4cCI6MjA5NDk1ODMzOH0.xg7g-o0l9V5kskL_ebVRJtYiFfGrDFeHMa9ng-WYWnU";

// Globális állapot
const partnerState = {
    session_id: sessionId,
    salon_name: null,
    email: null,
    contact_name: null,
    weekly_empty_hours: 5,
    average_price: 15000,
    estimated_annual_loss: 3900000,
    estimated_recovered: 1326000,
    rejection_reason: null,
    ip_address: null,
    is_personalized: false
};

// UI Elemek
const hoursSlider = document.getElementById('hours-slider');
const priceSlider = document.getElementById('price-slider');
const hoursVal = document.getElementById('hours-val');
const priceVal = document.getElementById('price-val');
const lostRevenueEl = document.getElementById('lost-revenue');
const recoveredRevenueEl = document.getElementById('recovered-revenue');

// Számok formázása ezres elválasztóval
function formatCurrency(amount) {
    return new Intl.NumberFormat('hu-HU', { style: 'currency', currency: 'HUF', maximumFractionDigits: 0 }).format(amount);
}

// Kalkulátor frissítése
function updateCalculator() {
    const hours = parseInt(hoursSlider.value);
    const price = parseInt(priceSlider.value);

    // Éves kieső bevétel = órák száma hetente * átlagos ár * 52 hét
    const annualLoss = hours * price * 52;

    // ZenSlot-tal visszaszerezhető nettó bevétel:
    // Feltételezve, hogy a helyek 50%-át töltjük be 20% last-minute kedvezménnyel és 15% közvetítési díjjal.
    // Így a szalon nettó bevétele a listaár 68%-a (100% - 20% kedv. - 15% közvetítési díj az eladott árból, azaz 80% * 0.85 = 68%).
    const recovered = Math.round(hours * 0.5 * 52 * (price * 0.68));

    // Állapot mentése
    partnerState.weekly_empty_hours = hours;
    partnerState.average_price = price;
    partnerState.estimated_annual_loss = annualLoss;
    partnerState.estimated_recovered = recovered;

    // UI Frissítés
    hoursVal.innerText = hours;
    priceVal.innerText = new Intl.NumberFormat('hu-HU').format(price);
    lostRevenueEl.innerText = formatCurrency(annualLoss);
    recoveredRevenueEl.innerText = formatCurrency(recovered);
}

// Slider események
if (hoursSlider && priceSlider) {
    hoursSlider.addEventListener('input', updateCalculator);
    priceSlider.addEventListener('input', updateCalculator);
}

// UI Léptetés
function changeStep(fromStep, toStep) {
    const fromEl = document.getElementById(`step-${fromStep}`);
    const toEl = document.getElementById(`step-${toStep}`);
    if (fromEl) fromEl.classList.remove('active');
    if (toEl) toEl.classList.add('active');
}

function showForm() {
    changeStep(1, 2);
    // Ha az URL-ből már megvan a szalon neve, töltsük be az űrlapba
    if (partnerState.salon_name) {
        document.getElementById('salon_name').value = partnerState.salon_name;
    }
    if (partnerState.email) {
        document.getElementById('partner_email').value = partnerState.email;
    }
    saveDataToSupabase('partner_clicked_interest');
}

function showFeedback() {
    changeStep(1, 3);
    saveDataToSupabase('partner_clicked_reject');
}

function goBackToStep(stepNum) {
    // Visszatér a megadott lépésre (általában a kalkulátorhoz az 1-esre)
    const activeStepEl = document.querySelector('.step.active');
    if (activeStepEl) activeStepEl.classList.remove('active');
    document.getElementById(`step-${stepNum}`).classList.add('active');
}

// Mentés Supabase-be
function saveDataToSupabase(eventName) {
    const payload = {
        session_id: partnerState.session_id,
        event_name: eventName,
        salon_name: partnerState.salon_name,
        email: partnerState.email,
        contact_name: partnerState.contact_name,
        weekly_empty_hours: partnerState.weekly_empty_hours,
        average_price: partnerState.average_price,
        estimated_annual_loss: partnerState.estimated_annual_loss,
        estimated_recovered: partnerState.estimated_recovered,
        rejection_reason: partnerState.rejection_reason,
        ip_address: partnerState.ip_address,
        is_personalized: partnerState.is_personalized
    };

    console.log(`[Supabase Mentés - ${eventName}]:`, payload);

    fetch(`${SUPABASE_URL}/rest/v1/fake_partner_leads`, {
        method: 'POST',
        headers: {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        },
        body: JSON.stringify(payload)
    }).catch(err => console.error("Partner Supabase mentési hiba:", err));
}

// Opt-In Jelentkezési Űrlap beküldése
function submitPartnerLead(event) {
    event.preventDefault();

    partnerState.salon_name = document.getElementById('salon_name').value;
    partnerState.contact_name = document.getElementById('contact_name').value;
    partnerState.email = document.getElementById('partner_email').value;

    saveDataToSupabase('partner_lead_submitted');
    changeStep(2, 4);
}

// Visszautasítás és visszajelzés beküldése
function submitRejection(reason) {
    partnerState.rejection_reason = reason;
    saveDataToSupabase('partner_rejected_feedback');
    changeStep(3, 5);
}

function getHungarianArticle(name) {
    if (!name) return "a";
    const firstChar = name.trim().charAt(0).toLowerCase();
    const vowels = ['a', 'á', 'e', 'é', 'i', 'í', 'o', 'ó', 'ö', 'ő', 'u', 'ú', 'ü', 'ű'];
    return vowels.includes(firstChar) ? "az" : "a";
}

// URL paraméterek olvasása és inicializálás
window.addEventListener('DOMContentLoaded', () => {
    // 1. URL paraméterek kinyerése
    const urlParams = new URLSearchParams(window.location.search);
    const salonParam = urlParams.get('s');
    const emailParam = urlParams.get('email');

    if (salonParam) {
        partnerState.salon_name = decodeURIComponent(salonParam);
        partnerState.is_personalized = true;

        // Személyre szabott szöveg a kalkulátorban a banner helyett (nyelvtani névelő-igazítással)
        const labelEl = document.getElementById('recovered-label');
        if (labelEl) {
            const article = getHungarianArticle(partnerState.salon_name);
            labelEl.innerText = "A ZenSlot segítségével " + article + " " + partnerState.salon_name + "-nek megmentett éves bevétel:";
        }
    }

    if (emailParam) {
        partnerState.email = decodeURIComponent(emailParam);
    }

    // Kalkulátor inicializálása alapértékekkel
    updateCalculator();

    // 2. IP cím lekérése és oldalmegtekintés mentése (Silent tracking)
    fetch('https://api.ipify.org?format=json')
        .then(res => res.json())
        .then(data => {
            partnerState.ip_address = data.ip;
            saveDataToSupabase('partner_page_view');
        })
        .catch(err => {
            console.warn("Nem sikerült az IP lekérdezés:", err);
            // Ha hiba van, akkor is mentünk
            saveDataToSupabase('partner_page_view');
        });
});
