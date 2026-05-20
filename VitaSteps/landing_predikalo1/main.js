// ===== COUNTDOWN =====
const EARLYBIRD_END = new Date('2026-05-19T12:15:00');

function updateCountdown() {
    const now = new Date();
    const diff = EARLYBIRD_END - now;
    if (diff <= 0) {
        const countdownEl = document.getElementById('countdown');
        if (countdownEl) {
            countdownEl.innerHTML = '<span style="color:var(--text-mid); font-weight: 600;">Az Early Bird időszak véget ért. A nevezés normál áron folytatódik.</span>';
        }

        // Dynamic price switch to 8.990 Ft (Normal Price)
        const heroCta = document.getElementById('hero-cta');
        if (heroCta && !heroCta.textContent.includes('8.990')) {
            heroCta.innerHTML = 'Nevezek – 8.990 Ft 🏔️';
            // Update the subtext under hero cta if needed
        }

        const paymentBtn = document.getElementById('payment-btn');
        if (paymentBtn && !paymentBtn.textContent.includes('8.990')) {
            paymentBtn.innerHTML = 'Nevezek – 8.990 Ft 🏔️';
        }

        const badge = document.getElementById('badge-earlybird');
        if (badge) {
            badge.innerHTML = '🏔️ Normál nevezés';
            badge.style.background = 'rgba(255,255,255,0.08)';
            badge.style.color = 'var(--text-high)';
        }

        // Additional price adjustments
        const priceStep1 = document.getElementById('price-step1-display');
        if (priceStep1) {
            priceStep1.textContent = '8.990 Ft';
        }

        const priceCurrent = document.getElementById('price-current-display');
        if (priceCurrent) {
            priceCurrent.textContent = '8.990 Ft';
        }

        const priceTag = document.getElementById('price-tag-display');
        if (priceTag) {
            priceTag.textContent = 'Normál ár';
        }

        // Update active timeline state
        const tlEarly = document.getElementById('tl-item-early');
        const tlNormal = document.getElementById('tl-item-normal');
        if (tlEarly && tlNormal) {
            tlEarly.classList.remove('active');
            tlNormal.classList.add('active');
        }
        return;
    }
    const d = Math.floor(diff / (1000 * 60 * 60 * 24));
    const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const s = Math.floor((diff % (1000 * 60)) / 1000);
    document.getElementById('cd-days').textContent = String(d).padStart(2, '0');
    document.getElementById('cd-hours').textContent = String(h).padStart(2, '0');
    document.getElementById('cd-mins').textContent = String(m).padStart(2, '0');
    document.getElementById('cd-secs').textContent = String(s).padStart(2, '0');
}
updateCountdown();
setInterval(updateCountdown, 1000);

// ===== META PIXEL EVENTS =====
document.getElementById('payment-btn')?.addEventListener('click', () => {
    if (typeof fbq !== 'undefined') {
        const isNormalPrice = new Date() > EARLYBIRD_END;
        fbq('track', 'InitiateCheckout', { value: isNormalPrice ? 8990 : 7990, currency: 'HUF' });
    }
});

document.getElementById('hero-cta')?.addEventListener('click', () => {
    if (typeof fbq !== 'undefined') {
        fbq('track', 'ViewContent', { content_name: 'Prédikálószék Kihívás' });
    }
});

document.getElementById('nav-cta')?.addEventListener('click', () => {
    if (typeof fbq !== 'undefined') {
        fbq('track', 'ViewContent', { content_name: 'Prédikálószék Kihívás - Nav CTA' });
    }
});
