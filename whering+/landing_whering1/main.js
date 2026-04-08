import { inject } from '@vercel/analytics';

// Initialize Vercel Analytics
inject();

// Tally Modal Logic
window.openTally = function() {
    const modal = document.getElementById('tallyModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Stop scrolling
    }
}

window.closeTally = function() {
    const modal = document.getElementById('tallyModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Enable scrolling
    }
}

// Close modal when clicking outside of it
window.onclick = function (event) {
    const modal = document.getElementById('tallyModal');
    if (event.target == modal) {
        window.closeTally();
    }
}
