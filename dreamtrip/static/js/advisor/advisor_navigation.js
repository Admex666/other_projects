/**
 * Optivoya Advisor Workspace — Hierarchical Navigation & Hash Router
 * Manages 3-tier navigation:
 * 1. Global (Dashboard, Clients CRM, All Cases, Settings)
 * 2. Client Profile & Cases
 * 3. Active Case Workspace (Brief, Research Lab, Options, Compare, Proposals, Timeline)
 * 
 * URL Hash Routing:
 * - #/dashboard
 * - #/clients
 * - #/clients/:clientId
 * - #/cases
 * - #/cases/:caseId
 * - #/cases/:caseId/:subview (brief, research, options, compare, proposals, timeline)
 */

(function () {
    'use strict';

    class AdvisorNavigationManager {
        constructor() {
            this.currentView = 'dashboard';
            this.subView = 'brief';
        }

        init() {
            this.bindKeyboardShortcuts();
            this.bindHashRouter();
            this.populateClientSelectDropdown();
            
            // Initial route parse from window.location.hash
            this.handleHashChange();
        }

        bindHashRouter() {
            window.addEventListener('hashchange', () => {
                this.handleHashChange();
            });
        }

        handleHashChange() {
            const hash = window.location.hash.replace(/^#\/?/, '').trim();
            if (!hash || hash === 'dashboard') {
                this.navigate('dashboard', {}, false);
                return;
            }

            const parts = hash.split('/');
            const root = parts[0];

            if (root === 'clients') {
                if (parts[1]) {
                    window.AdvisorState.setActiveClient(parts[1]);
                    this.navigate('client-detail', { clientId: parts[1] }, false);
                } else {
                    this.navigate('clients', {}, false);
                }
            } else if (root === 'cases') {
                if (parts[1]) {
                    const caseId = parts[1];
                    const subview = parts[2] || 'brief';
                    window.AdvisorState.setActiveCase(caseId);
                    this.navigate(subview, { caseId: caseId }, false);
                } else {
                    this.navigate('cases', {}, false);
                }
            } else if (['research', 'options', 'compare', 'proposals', 'proposal', 'timeline', 'brief', 'settings'].includes(root)) {
                this.navigate(root, {}, false);
            } else {
                this.navigate('dashboard', {}, false);
            }
        }

        navigate(viewName, params = {}, updateHash = true) {
            this.currentView = viewName;
            window.AdvisorState.state.currentView = viewName;

            if (params.caseId) {
                window.AdvisorState.setActiveCase(params.caseId);
            }
            if (params.clientId) {
                window.AdvisorState.setActiveClient(params.clientId);
            }

            const activeCase = window.AdvisorState.getActiveCase();

            // Update URL hash if requested
            if (updateHash) {
                if (viewName === 'dashboard') {
                    window.location.hash = '#/dashboard';
                } else if (viewName === 'clients') {
                    window.location.hash = '#/clients';
                } else if (viewName === 'client-detail' && params.clientId) {
                    window.location.hash = `#/clients/${params.clientId}`;
                } else if (viewName === 'cases') {
                    window.location.hash = '#/cases';
                } else if (['brief', 'research', 'options', 'compare', 'proposals', 'proposal', 'timeline'].includes(viewName) && activeCase) {
                    window.location.hash = `#/cases/${activeCase.id}/${viewName}`;
                } else if (viewName === 'settings') {
                    window.location.hash = '#/settings';
                }
            }

            this.updateSidebarUI();
            this.updateHeaderBreadcrumbs();

            // Re-render dashboard view container
            if (window.AdvisorDashboard) {
                window.AdvisorDashboard.render();
            }
        }

        navigateToCase(caseId, subview = 'brief') {
            window.AdvisorState.setActiveCase(caseId);
            this.navigate(subview, { caseId: caseId }, true);
        }

        navigateToClient(clientId) {
            window.AdvisorState.setActiveClient(clientId);
            this.navigate('client-detail', { clientId: clientId }, true);
        }

        exitActiveCase() {
            window.AdvisorState.setActiveCase(null);
            this.navigate('cases', {}, true);
        }

        updateSidebarUI() {
            const activeCase = window.AdvisorState.getActiveCase();
            const activeCaseSection = document.getElementById('sidebarActiveCaseSection');
            
            // Show/hide active case section in sidebar
            if (activeCaseSection) {
                if (activeCase) {
                    activeCaseSection.style.display = 'block';
                    const titleEl = document.getElementById('sidebarActiveCaseTitle');
                    if (titleEl) titleEl.innerText = activeCase.title || 'Aktív Ügy';
                    const clientEl = document.getElementById('sidebarActiveCaseClient');
                    const client = window.AdvisorState.getActiveClient();
                    if (clientEl) clientEl.innerText = client ? client.name : 'Ügyfél';
                } else {
                    activeCaseSection.style.display = 'none';
                }
            }

            // Update active states on nav items
            document.querySelectorAll('.sidebar-nav .nav-item').forEach(el => {
                const targetView = el.getAttribute('data-view');
                const isMatch = targetView === this.currentView || (targetView === 'proposals' && this.currentView === 'proposal');
                el.classList.toggle('active', isMatch);
            });
        }

        updateHeaderBreadcrumbs() {
            const breadcrumbsContainer = document.getElementById('headerBreadcrumbs');
            if (!breadcrumbsContainer) return;

            const state = window.AdvisorState.state;
            const activeCase = window.AdvisorState.getActiveCase();
            const activeClient = window.AdvisorState.getActiveClient();
            const view = this.currentView;

            let crumbs = [];

            // Root
            crumbs.push(`
                <span class="breadcrumb-item" onclick="window.AdvisorNavigation.navigate('dashboard')">
                    <span class="material-symbols-outlined" style="font-size:16px;">dashboard</span>
                    <span>Workspace</span>
                </span>
            `);

            if (view === 'dashboard') {
                crumbs.push(`<span class="breadcrumb-separator">/</span><span class="breadcrumb-current">Dashboard</span>`);
            } else if (view === 'cases') {
                crumbs.push(`<span class="breadcrumb-separator">/</span><span class="breadcrumb-current">Összes Ügy</span>`);
            } else if (view === 'clients') {
                crumbs.push(`<span class="breadcrumb-separator">/</span><span class="breadcrumb-current">Ügyfelek (CRM)</span>`);
            } else if (view === 'client-detail') {
                crumbs.push(`<span class="breadcrumb-separator">/</span><span class="breadcrumb-item" onclick="window.AdvisorNavigation.navigate('clients')">Ügyfelek</span>`);
                crumbs.push(`<span class="breadcrumb-separator">/</span><span class="breadcrumb-current">${activeClient ? activeClient.name : 'Ügyfél Profil'}</span>`);
            } else if (['brief', 'research', 'options', 'compare', 'proposals', 'proposal', 'timeline'].includes(view)) {
                if (activeClient) {
                    crumbs.push(`<span class="breadcrumb-separator">/</span><span class="breadcrumb-item" onclick="window.AdvisorNavigation.navigateToClient('${activeClient.id}')">${activeClient.name}</span>`);
                }
                if (activeCase) {
                    crumbs.push(`<span class="breadcrumb-separator">/</span><span class="breadcrumb-item" onclick="window.AdvisorNavigation.navigateToCase('${activeCase.id}', 'brief')">${activeCase.title}</span>`);
                }

                const subviewLabels = {
                    'brief': 'Brief & Megkötések',
                    'research': 'Intelligence Lab',
                    'options': '3 Döntési Archetípus',
                    'compare': 'Összehasonlító Mátrix',
                    'proposals': 'Ügyfélajánlat',
                    'proposal': 'Ügyfélajánlat',
                    'timeline': 'Idővonal & Audit'
                };
                crumbs.push(`<span class="breadcrumb-separator">/</span><span class="breadcrumb-current">${subviewLabels[view] || view}</span>`);
            } else if (view === 'settings') {
                crumbs.push(`<span class="breadcrumb-separator">/</span><span class="breadcrumb-current">Beállítások</span>`);
            }

            // Case context summary pill
            let casePill = '';
            if (activeCase) {
                const dest = activeCase.research_scope?.candidate_destinations?.[0] || 'Több célpont';
                const budget = activeCase.total_budget_huf ? (activeCase.total_budget_huf).toLocaleString('hu-HU') + ' Ft' : 'Büdzsé nincs megadva';
                casePill = `
                    <div class="active-case-pill">
                        <span class="material-symbols-outlined" style="font-size:14px; color:var(--secondary-container);">trip_origin</span>
                        <span>${dest} (${activeCase.duration_days_min} nap)</span>
                        <span style="opacity:0.4;">•</span>
                        <span style="font-family:var(--font-mono); color:#a7f540;">${budget}</span>
                        <button type="button" class="btn-exit-case" onclick="window.AdvisorNavigation.exitActiveCase()" title="Kilépés az ügyből">✕</button>
                    </div>
                `;
            }

            breadcrumbsContainer.innerHTML = `
                <div style="display:flex; align-items:center; gap:8px; flex:1; overflow:hidden;">
                    ${crumbs.join('')}
                </div>
                ${casePill}
            `;
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

    window.AdvisorToast = function(message, type = 'info') {
        let toastContainer = document.getElementById('advisorToastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'advisorToastContainer';
            toastContainer.style.position = 'fixed';
            toastContainer.style.bottom = '24px';
            toastContainer.style.right = '24px';
            toastContainer.style.zIndex = '9999';
            toastContainer.style.display = 'flex';
            toastContainer.style.flexDirection = 'column';
            toastContainer.style.gap = '10px';
            toastContainer.style.pointerEvents = 'none';
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        toast.className = `advisor-toast advisor-toast-${type}`;
        toast.style.background = type === 'error' ? '#3d0a0a' : (type === 'success' ? '#1c4e24' : '#16201a');
        toast.style.color = '#ffffff';
        toast.style.border = type === 'error' ? '1px solid #ff4444' : (type === 'success' ? '1px solid #a7f540' : '1px solid rgba(255,255,255,0.12)');
        toast.style.borderRadius = '8px';
        toast.style.padding = '12px 18px';
        toast.style.fontSize = '13px';
        toast.style.fontWeight = '500';
        toast.style.boxShadow = '0 8px 24px rgba(0,0,0,0.5)';
        toast.style.display = 'flex';
        toast.style.alignItems = 'center';
        toast.style.gap = '10px';
        toast.style.pointerEvents = 'auto';
        toast.innerHTML = `<span>${message}</span>`;

        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    };
})();
