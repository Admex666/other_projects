/**
 * ClosetMind Landing Page Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    initWaitlistCounter();
    initSmoothScrolling();
});

/**
 * Calculates and updates a dynamic waitlist counter
 * Starts at 141 on April 1, 2026.
 * Increases by 10-20 per day.
 */
function initWaitlistCounter() {
    const counterElement = document.getElementById('waitlist-counter');
    if (!counterElement) return;

    const baseCount = 141;
    const startDate = new Date('2026-04-01T00:00:00');
    const today = new Date();
    
    // Calculate full days passed
    const diffTime = Math.abs(today - startDate);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    // Generate a pseudo-random but consistent daily increase (10-20)
    // We use a simple hash of the day to keep it consistent for the same day
    let totalIncrease = 0;
    for (let i = 0; i < diffDays; i++) {
        const daySeed = i + startDate.getDate();
        // Deterministic "random" between 10 and 20
        const dailyGrowth = 10 + (Math.sin(daySeed) * 5 + 5); 
        totalIncrease += Math.floor(dailyGrowth);
    }

    const finalCount = baseCount + totalIncrease;
    
    // Update the text
    counterElement.innerHTML = `⚡️ <strong>${finalCount.toLocaleString()}</strong> people joined the waitlist`;
    
    // Add subtle entrance animation
    counterElement.style.opacity = '0';
    counterElement.style.transition = 'opacity 1s ease-in';
    setTimeout(() => {
        counterElement.style.opacity = '1';
    }, 100);
}

/**
 * Basic smooth scroll for anchor links
 */
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}
