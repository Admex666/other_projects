// ===== COUNTDOWN =====
const CAMPAIGN_END = new Date('2026-05-27T23:59:59');

function updateCountdown() {
    const now = new Date();
    const diff = CAMPAIGN_END - now;
    if (diff <= 0) {
        const countdownEl = document.getElementById('countdown');
        if (countdownEl) {
            countdownEl.innerHTML = '<span style="color:var(--text-mid); font-weight: 600;">A nevezés lezárult. Később új kihívással jelentkezünk!</span>';
        }

        const heroCta = document.getElementById('hero-cta');
        if (heroCta) {
            heroCta.style.pointerEvents = 'none';
            heroCta.style.opacity = '0.5';
            heroCta.innerHTML = 'Nevezés lezárult';
        }

        const paymentBtn = document.getElementById('payment-btn');
        if (paymentBtn) {
            paymentBtn.style.pointerEvents = 'none';
            paymentBtn.style.opacity = '0.5';
            paymentBtn.innerHTML = 'Nevezés lezárult';
        }

        const badge = document.getElementById('badge-earlybird');
        if (badge) {
            badge.innerHTML = 'Kihívás lezárva';
            badge.style.background = 'rgba(255,255,255,0.08)';
            badge.style.color = 'var(--text-high)';
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
        fbq('track', 'InitiateCheckout', { value: 7990, currency: 'HUF' });
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
