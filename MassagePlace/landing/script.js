// Egyedi munkamenet azonosító generálása
const sessionId = 'sess_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now().toString(36);

// Állapot (state) tárolása
const bookingData = {
    session_id: sessionId,
    treatment: null,
    treatment_price: 0,
    upsell: null,
    upsell_price: 0,
    frequency: null,
    total_aov: 0,
    email: null,
    name: null,
    timestamp: null
};

// Az aktuális lépés indexe
let currentStep = 1;
const totalSteps = 5;

const SUPABASE_URL = "https://vggmrmgctzanoutabvvl.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZnZ21ybWdjdHphbm91dGFidnZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkzODIzMzgsImV4cCI6MjA5NDk1ODMzOH0.xg7g-o0l9V5kskL_ebVRJtYiFfGrDFeHMa9ng-WYWnU";

/**
 * Valós idejű mentés a Supabase adatbázisba (REST API).
 */
function saveDataToBackend(eventName, data) {
    console.log(`[Adatmentés - ${eventName}] Lemorzsolódás követése:`, JSON.parse(JSON.stringify(data)));
    
    // Supabase-hez igazított adatszerkezet (a létrehozott tábla alapján)
    const payload = {
        session_id: data.session_id,
        event_name: eventName,
        treatment: data.treatment,
        treatment_price: data.treatment_price || 0,
        upsell: data.upsell,
        upsell_price: data.upsell_price || 0,
        frequency: data.frequency,
        total_aov: data.total_aov || 0,
        name: data.name,
        email: data.email
    };

    fetch(`${SUPABASE_URL}/rest/v1/fake_door_leads`, {
        method: 'POST',
        headers: {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        },
        body: JSON.stringify(payload)
    }).catch(err => console.error("Supabase mentési hiba:", err));
}

/**
 * Kezeli a gombnyomásokat a kérdőív lépéseiben
 */
function selectOption(category, value, price) {
    // Adatok frissítése
    bookingData[category] = value;
    bookingData[`${category}_price`] = price;
    bookingData.total_aov = bookingData.treatment_price + bookingData.upsell_price;
    bookingData.timestamp = new Date().toISOString();

    // Azonnali mentés, hogy ha most bezárja az ablakot, akkor is meglegyen az adat (Partial Submission / Drop-off)
    saveDataToBackend(`selected_${category}`, bookingData);

    // Lépés a következő kérdésre
    goToNextStep();
}

/**
 * Fake door "waitlist" űrlap beküldése
 */
function submitWaitlist(event) {
    event.preventDefault(); // Ne töltse újra az oldalt
    
    // Adatok kinyerése
    const nameInput = document.getElementById('name').value;
    const emailInput = document.getElementById('email').value;

    bookingData.name = nameInput;
    bookingData.email = emailInput;
    bookingData.timestamp = new Date().toISOString();

    // Végleges mentés
    saveDataToBackend('waitlist_submitted', bookingData);

    // Utolsó, "Sikeres" képernyő mutatása
    goToNextStep();
}

/**
 * UI léptető logika
 */
function goToNextStep() {
    if (currentStep >= totalSteps) return;

    // Jelenlegi lépés elrejtése
    const currentEl = document.getElementById(`step-${currentStep}`);
    if (currentEl) {
        currentEl.classList.remove('active');
    }

    // Következő lépés mutatása
    currentStep++;
    const nextEl = document.getElementById(`step-${currentStep}`);
    if (nextEl) {
        nextEl.classList.add('active');
    }
}
