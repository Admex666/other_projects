/**
 * Optivoya Advisor Workspace — Navigation & Keyboard Shortcuts
 * Manages view transitions and global productivity hotkeys:
 * - N: Open New Case Modal
 * - C: Open New Client Modal
 * - /: Focus Global Search
 * - Escape: Close Modals / Return to Dashboard
 */

(function () {
    'use strict';

    class AdvisorNavigationManager {
        constructor() {
            this.currentView = 'dashboard';
        }

        init() {
            this.bindKeyboardShortcuts();
            this.populateClientSelectDropdown();
        }

        navigate(viewName) {
            this.currentView = viewName;
            window.AdvisorState.state.currentView = viewName;

            // Update sidebar nav UI
            document.querySelectorAll('.sidebar-nav .nav-item').forEach(el => {
                el.classList.toggle('active', el.getAttribute('data-view') === viewName);
            });

            // Re-render view
            if (window.AdvisorDashboard) {
                window.AdvisorDashboard.render();
            }
        }

        openNewCaseModal() {
            this.populateClientSelectDropdown();
            const modal = document.getElementById('newCaseModal');
            if (modal) {
                modal.style.display = 'flex';
                const titleInput = document.getElementById('caseTitleInput');
                if (titleInput) setTimeout(() => titleInput.focus(), 50);
            }
        }

        openNewClientModal() {
            const modal = document.getElementById('newClientModal');
            if (modal) {
                modal.style.display = 'flex';
                const nameInput = document.getElementById('clientNameInput');
                if (nameInput) setTimeout(() => nameInput.focus(), 50);
            }
        }

        closeModals() {
            const modals = document.querySelectorAll('.modal-overlay');
            modals.forEach(m => m.style.display = 'none');
        }

        populateClientSelectDropdown() {
            const select = document.getElementById('caseClientSelect');
            if (!select) return;

            const clients = window.AdvisorState.state.clients || [];
            select.innerHTML = clients.map(c => `
                <option value="${c.id}">${c.name} (${c.email || 'Nincs email'})</option>
            `).join('');

            if (clients.length === 0) {
                select.innerHTML = '<option value="">Előbb hozz létre egy ügyfelet!</option>';
            }
        }

        bindKeyboardShortcuts() {
            document.addEventListener('keydown', (e) => {
                // Ignore if focus is in an input or textarea
                const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
                const isInputActive = ['input', 'textarea', 'select'].includes(activeTag);

                if (e.key === 'Escape') {
                    this.closeModals();
                    return;
                }

                if (isInputActive) return;

                if (e.key === 'n' || e.key === 'N') {
                    e.preventDefault();
                    this.openNewCaseModal();
                } else if (e.key === 'c' || e.key === 'C') {
                    e.preventDefault();
                    this.openNewClientModal();
                } else if (e.key === '/') {
                    e.preventDefault();
                    const searchInput = document.getElementById('globalAdvisorSearch');
                    if (searchInput) searchInput.focus();
                } else if (e.key === 'd' || e.key === 'D') {
                    e.preventDefault();
                    this.navigate('dashboard');
                }
            });
        }
    }

    window.AdvisorNavigation = new AdvisorNavigationManager();
})();
