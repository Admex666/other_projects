/**
 * Optivoya — Client-Side Telemetry & Analytics Tracker v2.0
 * Lightweight telemetry module tracking search lifecycle, duration, and user interactions.
 */
(function () {
    const Analytics = {
        getSessionId() {
            let sess = sessionStorage.getItem('optivoya_session_id');
            if (!sess) {
                sess = 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 5);
                sessionStorage.setItem('optivoya_session_id', sess);
            }
            return sess;
        },

        getCurrentUser() {
            // Read from localStorage or default cookie session
            return localStorage.getItem('optivoya_username') || 'anonymous_advisor';
        },

        async trackEvent(eventType, module, params = {}, durationMs = null, resultsCount = null, success = true, error = null) {
            try {
                const payload = {
                    session_id: this.getSessionId(),
                    user_id: this.getCurrentUser(),
                    event_type: eventType,
                    module: module,
                    search_params: params,
                    duration_ms: durationMs,
                    results_count: resultsCount,
                    success: success,
                    error_message: error
                };

                fetch('/api/analytics/event', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                }).catch(() => {});
            } catch (e) {
                console.debug("[Analytics] Silent tracker error:", e);
            }
        },

        trackSearchStarted(module, params) {
            return this.trackEvent('search_started', module, params);
        },

        trackSearchCompleted(module, params, durationMs, resultsCount, success = true, error = null) {
            return this.trackEvent('search_completed', module, params, durationMs, resultsCount, success, error);
        },

        trackProposalExported(tripSummary) {
            return this.trackEvent('proposal_exported', 'proposal', tripSummary, null, 1, true);
        }
    };

    window.OptivoyaAnalytics = Analytics;
})();
