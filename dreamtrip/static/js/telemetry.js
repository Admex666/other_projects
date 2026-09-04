/**
 * Optivoya — Universal Telemetry & Microsoft Clarity Bridge
 * Tracks all user interactions, button clicks, dwell times, and user journeys.
 * Guarantees persistent session tracking across page views and API requests.
 */

(function () {
    // 1. Session ID Management
    function getOrInitSessionId() {
        let sid = sessionStorage.getItem('optivoya_session_id');
        if (!sid) {
            // Check cookie
            const match = document.cookie.match(new RegExp('(^| )optivoya_session_id=([^;]+)'));
            if (match && match[2]) {
                sid = match[2];
            } else {
                sid = 'sess_' + Math.random().toString(16).substring(2, 10) + Date.now().toString(16).slice(-4);
            }
            sessionStorage.setItem('optivoya_session_id', sid);
        }
        // Always refresh cookie for backend visibility
        document.cookie = `optivoya_session_id=${sid}; path=/; max-age=86400; SameSite=Lax`;
        return sid;
    }

    const sessionId = getOrInitSessionId();
    let lastActionTime = Date.now();

    const OptivoyaTelemetry = {
        sessionId: sessionId,
        userId: window.optivoya_user || 'guest',

        init() {
            this.syncWithClarity();
            this.bindGlobalButtonTracking();
            this.bindPageLifecycle();
        },

        // Microsoft Clarity Deep Identification
        syncWithClarity() {
            if (window.clarity) {
                try {
                    const user = this.userId;
                    window.clarity("identify", user, this.sessionId, window.location.pathname);
                    window.clarity("set", "session_id", this.sessionId);
                    window.clarity("set", "user_id", user);
                    window.clarity("set", "url", window.location.pathname);
                } catch (e) {
                    console.debug("[CLARITY SYNC ERROR]", e);
                }
            } else {
                // Retry if clarity loads slightly later
                setTimeout(() => {
                    if (window.clarity) {
                        try {
                            window.clarity("identify", this.userId, this.sessionId, window.location.pathname);
                            window.clarity("set", "session_id", this.sessionId);
                            window.clarity("set", "user_id", this.userId);
                        } catch (e) {}
                    }
                }, 1000);
            }
        },

        trackEvent(eventType, module = 'master_planner', metaData = {}, searchParams = {}) {
            const now = Date.now();
            const dwellMs = Math.max(0, now - lastActionTime);
            const dwellSec = Math.round(dwellMs / 1000);
            lastActionTime = now;

            const payload = {
                session_id: this.sessionId,
                user_id: this.userId,
                event_type: eventType,
                module: module,
                duration_ms: dwellMs,
                meta_data: {
                    ...metaData,
                    dwell_ms: dwellMs,
                    dwell_sec: dwellSec,
                    url: window.location.pathname,
                    timestamp_client: new Date().toISOString()
                },
                search_params: searchParams
            };

            // Also tag Clarity if relevant
            if (window.clarity && (metaData.button_text || metaData.destination)) {
                try {
                    if (metaData.destination) window.clarity("set", "destination", String(metaData.destination));
                    if (metaData.action) window.clarity("set", "last_action", String(metaData.action));
                } catch (err) {}
            }

            try {
                const jsonStr = JSON.stringify(payload);
                if (navigator.sendBeacon) {
                    const blob = new Blob([jsonStr], { type: 'application/json' });
                    navigator.sendBeacon('/api/telemetry/event', blob);
                } else {
                    fetch('/api/telemetry/event', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: jsonStr,
                        keepalive: true
                    }).catch(() => {});
                }
            } catch (e) {
                console.debug("[TELEMETRY SEND ERROR]", e);
            }
        },

        // Universal Button & Interaction Listener ("MINDEN GOMB LEGYEN TRACKELVE")
        bindGlobalButtonTracking() {
            document.addEventListener('click', (e) => {
                // Broad selector for ANY clickable interactive element or button
                const target = e.target.closest(
                    'button, a.btn, a[role="button"], .btn, [class*="btn-"], .step-node, ' +
                    'input[type="button"], input[type="submit"], input[type="reset"], [role="button"], ' +
                    '.modal-close-btn, .modal-close, [data-action], [data-toggle], .tab-btn, .filter-pill, ' +
                    '.user-item, .param-chip, input[type="checkbox"], input[type="radio"], [onclick]'
                );
                if (!target) return;

                const btnId = target.id || '';
                let rawText = target.innerText || target.value || target.getAttribute('aria-label') || target.getAttribute('title') || '';
                // Clean up whitespace & material icon names
                let btnText = rawText.replace(/\b(material-symbols-outlined|material-icons)\b/g, '')
                                     .replace(/\s+/g, ' ')
                                     .trim()
                                     .slice(0, 80);
                if (!btnText && target.title) btnText = target.title;
                if (!btnText && target.id) btnText = `#${target.id}`;
                if (!btnText && target.name) btnText = `[name=${target.name}]`;

                const btnClass = (target.className || '').toString().slice(0, 120);
                const currentStep = (window.PlannerState && typeof window.PlannerState.step === 'number') ? window.PlannerState.step : null;

                // Identify nearest contextual card/container
                const card = target.closest('[data-destination], .destination-card, .flight-card, .stay-card, .kpi-card, .modal-box, .panel-card');
                let contextInfo = {};
                if (card) {
                    if (card.dataset && card.dataset.destination) contextInfo.target_destination = card.dataset.destination;
                    if (card.dataset && card.dataset.id) contextInfo.card_id = card.dataset.id;
                    const cardTitle = card.querySelector('h3, h4, .destination-name, .city-name, .airline-name, .hotel-name, .panel-title');
                    if (cardTitle) {
                        contextInfo.card_title = cardTitle.innerText.trim().slice(0, 60);
                    }
                }

                // Determine semantic action name
                let actionName = 'button_clicked';
                const lowerText = btnText.toLowerCase();
                if (target.classList.contains('step-node') || target.classList.contains('tab-btn')) {
                    actionName = 'stepper_or_tab_clicked';
                } else if (lowerText.includes('járatok keresése') || lowerText.includes('célállomás kiválasztása')) {
                    actionName = 'destination_selected';
                } else if (lowerText.includes('járat kiválasztása') || lowerText.includes('járatot választok')) {
                    actionName = 'flight_selected';
                } else if (lowerText.includes('szállás kiválasztása') || lowerText.includes('szállást választok')) {
                    actionName = 'stay_selected';
                } else if (lowerText.includes('ajánlat') || lowerText.includes('pdf') || lowerText.includes('export')) {
                    actionName = 'proposal_export_clicked';
                } else if (btnId === 'dummyModeToggle') {
                    actionName = 'dummy_mode_toggled';
                } else if (target.type === 'checkbox') {
                    actionName = target.checked ? 'checkbox_checked' : 'checkbox_unchecked';
                }

                this.trackEvent('button_click', 'ui_interaction', {
                    action: actionName,
                    button_id: btnId,
                    button_text: btnText || '(Névtelen gomb)',
                    button_class: btnClass,
                    planner_step: currentStep,
                    tag_name: target.tagName.toLowerCase(),
                    ...contextInfo
                });
            }, true);
        },

        bindPageLifecycle() {
            // Track initial page view with session
            this.trackEvent('page_view', 'navigation', {
                title: document.title,
                url: window.location.pathname
            });
        }
    };

    window.OptivoyaTelemetry = OptivoyaTelemetry;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => OptivoyaTelemetry.init());
    } else {
        OptivoyaTelemetry.init();
    }
})();
