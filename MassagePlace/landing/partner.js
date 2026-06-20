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
    is_personalized: false,
    lang: 'hu'
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
    if (partnerState.lang === 'en') {
        return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(amount) + " HUF";
    }
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
    priceVal.innerText = new Intl.NumberFormat(partnerState.lang === 'en' ? 'en-US' : 'hu-HU').format(price);
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

function translatePageToEnglish() {
    // Page Title
    document.title = "ZenSlot Partners - Fill Your Empty Hours";

    // H1
    const mainTitle = document.getElementById('main-title');
    if (mainTitle) mainTitle.innerHTML = "Fill your empty hours<br>with last-minute guests";

    // Subtitle
    const mainSubtitle = document.getElementById('main-subtitle');
    if (mainSubtitle) mainSubtitle.innerText = "ZenSlot automatically matches last-minute empty slots at wellness and massage salons with local, paying guests. Specifically designed for premium downtown providers.";

    // Features
    const f1 = document.getElementById('feature-1');
    if (f1) f1.innerHTML = "<strong>Performance-based model:</strong> No signup fees, no monthly subscriptions. You only pay for successfully matched guests.";
    const f2 = document.getElementById('feature-2');
    if (f2) f2.innerHTML = "<strong>Fill last-minute slots:</strong> Automatically match empty slots in the next 24 hours with local office workers in the area.";
    const f3 = document.getElementById('feature-3');
    if (f3) f3.innerHTML = "<strong>Zero fixed costs and risk:</strong> Completely risk-free pilot. You decide which time slots and services you offer on the platform.";

    // Example Box
    const exampleBox = document.getElementById('example-box');
    if (exampleBox) exampleBox.innerHTML = "💡 <strong>Practical example:</strong><br>A massage valued at 20,000 HUF that remains unsold 24 hours before startup sells for between 12,000 and 14,000 HUF to a nearby office worker with ZenSlot.";

    // Calculator Section
    const calcTitle = document.getElementById('calc-title');
    if (calcTitle) calcTitle.innerText = "Calculate your lost revenue!";
    
    const lblEmptyHours = document.getElementById('lbl-empty-hours');
    if (lblEmptyHours) lblEmptyHours.innerText = "Number of empty hours per week:";
    
    const unitHours = document.getElementById('unit-hours');
    if (unitHours) unitHours.innerText = "hours";

    const lblAvgPrice = document.getElementById('lbl-avg-price');
    if (lblAvgPrice) lblAvgPrice.innerText = "Average service price:";
    
    const unitPrice = document.getElementById('unit-price');
    if (unitPrice) unitPrice.innerText = "HUF";

    const lblAnnualLoss = document.getElementById('lbl-annual-loss');
    if (lblAnnualLoss) lblAnnualLoss.innerText = "Estimated annual lost revenue:";

    const recoveredLabel = document.getElementById('recovered-label');
    if (recoveredLabel) {
        if (partnerState.salon_name) {
            recoveredLabel.innerText = "Estimated annual revenue saved for " + partnerState.salon_name + " with ZenSlot:";
        } else {
            recoveredLabel.innerText = "Net revenue saved with ZenSlot:";
        }
    }

    const btnInterest = document.getElementById('btn-interest');
    if (btnInterest) btnInterest.innerText = "Interested in the pilot program";

    const btnReject = document.getElementById('btn-reject');
    if (btnReject) btnReject.innerText = "Not interested";

    // Form Section (Step 2)
    const formTitle = document.getElementById('form-title');
    if (formTitle) formTitle.innerText = "Join the Pilot Program";

    const formSubtitle = document.getElementById('form-subtitle');
    if (formSubtitle) formSubtitle.innerText = "Please provide your contact details, and we will get in touch with you shortly with the pilot details and a detailed calculation.";

    const salonInput = document.getElementById('salon_name');
    if (salonInput) salonInput.placeholder = "Salon name";

    const contactInput = document.getElementById('contact_name');
    if (contactInput) contactInput.placeholder = "Contact name";

    const emailInput = document.getElementById('partner_email');
    if (emailInput) emailInput.placeholder = "Email address";

    const btnSubmitLead = document.getElementById('btn-submit-lead');
    if (btnSubmitLead) btnSubmitLead.innerText = "Submit Application";

    const btnBackCalc1 = document.getElementById('btn-back-calc-1');
    if (btnBackCalc1) btnBackCalc1.innerText = "Back to calculator";

    // Reject Section (Step 3)
    const rejectTitle = document.getElementById('reject-title');
    if (rejectTitle) rejectTitle.innerText = "Thank you for your honesty!";

    const rejectSubtitle = document.getElementById('reject-subtitle');
    if (rejectSubtitle) rejectSubtitle.innerText = "Your feedback means a lot to our development team. Could you share with us in one click the main reason you are not interested?";

    const rBtn1 = document.getElementById('reject-btn-1');
    if (rBtn1) rBtn1.innerText = "We have no empty slots / Fully booked";
    const rBtn2 = document.getElementById('reject-btn-2');
    if (rBtn2) rBtn2.innerText = "We do not want to give discounts";
    const rBtn3 = document.getElementById('reject-btn-3');
    if (rBtn3) rBtn3.innerText = "We already use another booking solution";
    const rBtn4 = document.getElementById('reject-btn-4');
    if (rBtn4) rBtn4.innerText = "We do not trust booking mediators";
    const rBtn5 = document.getElementById('reject-btn-5');
    if (rBtn5) rBtn5.innerText = "Other reason";

    const btnBackCalc2 = document.getElementById('btn-back-calc-2');
    if (btnBackCalc2) btnBackCalc2.innerText = "Back to calculator";

    // Success Section (Step 4)
    const successTitle = document.getElementById('success-title');
    if (successTitle) successTitle.innerText = "Application Successful!";
    
    const successSubtitle = document.getElementById('success-subtitle');
    if (successSubtitle) successSubtitle.innerText = "Thank you for your trust! We will send you detailed information to your email address shortly.";

    // Success Reject Section (Step 5)
    const successRejectTitle = document.getElementById('success-reject-title');
    if (successRejectTitle) successRejectTitle.innerText = "Thank you for your feedback!";
    
    const successRejectSubtitle = document.getElementById('success-reject-subtitle');
    if (successRejectSubtitle) successRejectSubtitle.innerText = "You helped us build a better service for the future.";
}

// URL paraméterek olvasása és inicializálás
window.addEventListener('DOMContentLoaded', () => {
    // 1. URL paraméterek kinyerése
    const urlParams = new URLSearchParams(window.location.search);
    const salonParam = urlParams.get('s');
    const emailParam = urlParams.get('email');
    const langParam = urlParams.get('lang');

    if (langParam && langParam.toLowerCase() === 'en') {
        partnerState.lang = 'en';
    }

    if (salonParam) {
        partnerState.salon_name = decodeURIComponent(salonParam);
        partnerState.is_personalized = true;

        // Személyre szabott szöveg a kalkulátorban a banner helyett (nyelvtani névelő-igazítással)
        const labelEl = document.getElementById('recovered-label');
        if (labelEl) {
            if (partnerState.lang === 'en') {
                labelEl.innerText = "Estimated annual revenue saved for " + partnerState.salon_name + " with ZenSlot:";
            } else {
                const article = getHungarianArticle(partnerState.salon_name);
                labelEl.innerText = "A ZenSlot segítségével " + article + " " + partnerState.salon_name + "-nek megmentett éves bevétel:";
            }
        }
    }

    if (emailParam) {
        partnerState.email = decodeURIComponent(emailParam);
    }

    // Ha angol a nyelv, lefordítjuk az elemeket a kalkulátor frissítése előtt
    if (partnerState.lang === 'en') {
        translatePageToEnglish();
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
