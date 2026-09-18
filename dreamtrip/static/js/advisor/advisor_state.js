/**
 * Optivoya Advisor Workspace — Reactive State Manager
 * Holds currentAdvisor, cases, clients, kpis, activeCase, and notifies subscribers.
 */

(function () {
    'use strict';

    class AdvisorStateManager {
        constructor() {
            this.state = {
                advisor: null,
                agency: null,
                kpis: {
                    active_cases: 0,
                    research_jobs_completed: 0,
                    proposals_created: 0,
                    estimated_hours_saved: 0.0,
                    avg_composite_tripscore: 0.0
                },
                cases: [],
                clients: [],
                currentCase: null,
                currentClient: null,
                currentView: 'dashboard',
                searchQuery: '',
                isLoading: false,
                lastError: null
            };

            this.listeners = [];
        }

        subscribe(callback) {
            this.listeners.push(callback);
            return () => {
                this.listeners = this.listeners.filter(cb => cb !== callback);
            };
        }

        notify() {
            this.listeners.forEach(cb => {
                try {
                    cb(this.state);
                } catch (e) {
                    console.error('[Advisor State Notify Error]', e);
                }
            });
        }

        async init() {
            this.state.isLoading = true;
            this.notify();

            try {
                const [meRes, kpisRes, casesRes, clientsRes] = await Promise.all([
                    window.AdvisorAPI.getMe().catch(() => ({})),
                    window.AdvisorAPI.getDashboardKPIs().catch(() => ({})),
                    window.AdvisorAPI.getCases().catch(() => ({ cases: [] })),
                    window.AdvisorAPI.getClients().catch(() => ({ clients: [] }))
                ]);

                if (meRes.advisor) this.state.advisor = meRes.advisor;
                if (meRes.agency) this.state.agency = meRes.agency;
                if (kpisRes.active_cases !== undefined) this.state.kpis = kpisRes;
                if (casesRes.cases) this.state.cases = casesRes.cases;
                if (clientsRes.clients) this.state.clients = clientsRes.clients;

                this.updateSidebarBadges();
            } catch (err) {
                this.state.lastError = err.message;
            } finally {
                this.state.isLoading = false;
                this.notify();
            }
        }

        updateSidebarBadges() {
            const casesBadge = document.getElementById('navActiveCasesCount');
            if (casesBadge) {
                const activeCount = this.state.cases.filter(c => c.status !== 'closed' && c.status !== 'rejected').length;
                casesBadge.innerText = activeCount;
            }

            const clientsBadge = document.getElementById('navClientsCount');
            if (clientsBadge) {
                clientsBadge.innerText = this.state.clients.length;
            }

            const advName = document.getElementById('advisorProfileName');
            if (advName && this.state.advisor) {
                advName.innerText = this.state.advisor.name;
            }

            const agencyName = document.getElementById('advisorAgencyName');
            if (agencyName && this.state.agency) {
                agencyName.innerText = this.state.agency.name;
            }
        }

        async refreshCases() {
            const res = await window.AdvisorAPI.getCases();
            if (res.cases) {
                this.state.cases = res.cases;
                this.updateSidebarBadges();
                this.notify();
            }
        }

        async refreshClients() {
            const res = await window.AdvisorAPI.getClients();
            if (res.clients) {
                this.state.clients = res.clients;
                this.updateSidebarBadges();
                this.notify();
            }
        }

        async refreshKPIs() {
            const kpis = await window.AdvisorAPI.getDashboardKPIs();
            if (kpis.active_cases !== undefined) {
                this.state.kpis = kpis;
                this.notify();
            }
        }
    }

    window.AdvisorState = new AdvisorStateManager();
})();
