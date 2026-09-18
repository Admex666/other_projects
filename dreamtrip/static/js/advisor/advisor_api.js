/**
 * Optivoya Advisor Workspace — Typed REST API Client
 * Centralized API calls with error handling, latency telemetry and response parsing.
 */

(function () {
    'use strict';

    class AdvisorAPIClient {
        constructor(baseUrl = '/api/advisor') {
            this.baseUrl = baseUrl;
        }

        async request(endpoint, options = {}) {
            const url = `${this.baseUrl}${endpoint}`;
            const headers = {
                'Content-Type': 'application/json',
                'X-Requested-With': 'Optivoya-Advisor-Workspace',
                ...(options.headers || {})
            };

            const startTime = performance.now();
            try {
                const response = await fetch(url, { ...options, headers });
                const duration = Math.round(performance.now() - startTime);

                if (!response.ok) {
                    const errData = await response.json().catch(() => ({}));
                    const errMsg = errData.detail || `API error (${response.status})`;
                    throw new Error(errMsg);
                }

                const data = await response.json();
                data._meta = { durationMs: duration, status: response.status };
                return data;
            } catch (err) {
                console.error(`[Advisor API Error] ${options.method || 'GET'} ${url}:`, err);
                throw err;
            }
        }

        // Profile & KPIs
        async getMe() {
            return this.request('/me');
        }

        async getDashboardKPIs() {
            return this.request('/dashboard/kpis');
        }

        // Clients
        async getClients(search = '') {
            const query = search ? `?search=${encodeURIComponent(search)}` : '';
            return this.request(`/clients${query}`);
        }

        async getClientDetails(clientId) {
            return this.request(`/clients/${clientId}`);
        }

        async createClient(clientData) {
            return this.request('/clients', {
                method: 'POST',
                body: JSON.stringify(clientData)
            });
        }

        // Cases
        async getCases(status = '') {
            const query = status ? `?status=${encodeURIComponent(status)}` : '';
            return this.request(`/cases${query}`);
        }

        async getCaseDetails(caseId) {
            return this.request(`/cases/${caseId}`);
        }

        async createCase(caseData) {
            return this.request('/cases', {
                method: 'POST',
                body: JSON.stringify(caseData)
            });
        }

        async updateCaseStatus(caseId, status) {
            return this.request(`/cases/${caseId}/status`, {
                method: 'PATCH',
                body: JSON.stringify({ status })
            });
        }
    }

    window.AdvisorAPI = new AdvisorAPIClient();
})();
