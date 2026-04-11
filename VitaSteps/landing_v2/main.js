document.addEventListener('DOMContentLoaded', () => {
    const modal = document.querySelector('.modal-overlay');
    const buyTriggers = document.querySelectorAll('.buy-trigger');

    // Track Intent to Buy
    buyTriggers.forEach(trigger => {
        trigger.addEventListener('click', () => {
            console.log('PAYMENT_INTENT: User clicked the buy button');
            modal.style.display = 'flex';
            
            // Meta Pixel Lead tracking can be added here
            if (window.fbq) {
                fbq('track', 'AddToCart', { value: 7900, currency: 'HUF' });
            }
        });
    });

    // Close modal on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});
