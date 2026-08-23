
const fs = require('fs');
let code = fs.readFileSync('static/js/trip_cart.js', 'utf8');

const localStorageMock = {
    store: {},
    getItem(k) { return this.store[k]; },
    setItem(k, v) { this.store[k] = v; }
};

global.localStorage = localStorageMock;
global.window = { addEventListener: () => {}, location: {} };
global.document = { addEventListener: () => {}, getElementById: () => null, createElement: () => ({ style: {}, classList: { add: () => {}, remove: () => {} } }), body: { appendChild: () => {} } };

eval(code);

// 1. Destination Matcher Selection
window.TripCart.setDestination({
    name: 'Róma',
    city: 'Róma',
    country: 'Olaszország',
    duration: 7,
    adults: 2,
    children: 0,
    origin: 'Budapest',
    daily_cost_eur: 43.2,
    flight_price_huf: 48900,
    numbeo: { meal_inexpensive: 16.0, meal_midrange: 32.0, coffee: 1.6, transport_ticket: 1.50 }
});

let cta1 = window.TripCart.getNextStepCTA();
console.log('CTA after Destination:', cta1.badge, '->', cta1.text);

// 2. Flight Selection
window.TripCart.setFlight({
    airline: 'Wizz Air',
    price_huf: 48900,
    total_price_huf: 48900,
    out_date: '2026-09-10',
    in_date: '2026-09-17',
    exact_stay_nights: 7,
    adults: 2
});

let cta2 = window.TripCart.getNextStepCTA();
console.log('CTA after Flight:', cta2.badge, '->', cta2.text);

// 3. Accommodation Selection
window.TripCart.setStay({
    name: 'Hotel Colosseum Rome',
    price_huf: 148000,
    rating: 8.8,
    stars: 4,
    nights: 7
});

let cta3 = window.TripCart.getNextStepCTA();
console.log('CTA after Stay:', cta3.badge, '->', cta3.text);

// 4. Breakdown calculation
let breakdown = window.TripCart.calculateBreakdown();
console.log('\n--- DETAILED ITEMIZED NUMBEO BREAKDOWN ---');
breakdown.items.forEach(it => {
    console.log(it.icon, it.name, '=>', it.formula, '=', it.amount.toLocaleString() + ' Ft');
});
console.log('TOTAL:', breakdown.totalHuf.toLocaleString() + ' Ft');
console.log('PER PERSON:', breakdown.perPersonTotal.toLocaleString() + ' Ft / fő');
