/**
 * OPTIVOTA THEME TOGGLE ENGINE
 * Manages Light / Dark mode switching with localStorage persistence and OS preference detection
 */

(function () {
    const STORAGE_KEY = 'optivoya_theme';
    const HTML_ELEMENT = document.documentElement;

    // Detect initial theme: stored value > system preference > default 'light'
    function getPreferredTheme() {
        const storedTheme = localStorage.getItem(STORAGE_KEY);
        if (storedTheme) {
            return storedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    // Apply theme to DOM
    function applyTheme(theme) {
        HTML_ELEMENT.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);
        updateToggleButton(theme);
    }

    // Update toggle button icon and accessibility attributes
    function updateToggleButton(theme) {
        const buttons = document.querySelectorAll('.theme-toggle-btn');
        buttons.forEach(btn => {
            if (theme === 'dark') {
                btn.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="5"></circle>
                        <line x1="12" y1="1" x2="12" y2="3"></line>
                        <line x1="12" y1="21" x2="12" y2="23"></line>
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                        <line x1="1" y1="12" x2="3" y2="12"></line>
                        <line x1="21" y1="12" x2="23" y2="12"></line>
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                    </svg>
                `;
                btn.setAttribute('aria-label', 'Váltás világos módra');
                btn.setAttribute('title', 'Világos mód bekapcsolása');
            } else {
                btn.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                    </svg>
                `;
                btn.setAttribute('aria-label', 'Váltás sötét módra');
                btn.setAttribute('title', 'Sötét mód bekapcsolása');
            }
        });
    }

    // Toggle between light and dark
    window.toggleTheme = function () {
        const currentTheme = HTML_ELEMENT.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    };

    // Apply immediately to avoid flicker
    const initialTheme = getPreferredTheme();
    HTML_ELEMENT.setAttribute('data-theme', initialTheme);

    // Bind DOMContentLoaded listener for buttons
    document.addEventListener('DOMContentLoaded', () => {
        updateToggleButton(HTML_ELEMENT.getAttribute('data-theme') || 'light');
    });

    // Listen for OS preference changes if not manually overridden
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem(STORAGE_KEY)) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });
})();
