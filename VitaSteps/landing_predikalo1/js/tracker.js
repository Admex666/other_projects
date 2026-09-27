/**
 * VitaSteps Analytics & Attribution Tracker (tracker.js)
 * Lightweight, zero-dependency, granular session & funnel tracking.
 */
(function () {
    'use strict';

    if (window.__VitaTrackerInitialized) return;
    window.__VitaTrackerInitialized = true;

    // --- Helper Utilities ---
    function uuidv4() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    function setCookie(name, value, days) {
        let expires = '';
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = '; expires=' + date.toUTCString();
        }
        document.cookie = name + '=' + (value || '') + expires + '; path=/; SameSite=Lax';
    }

    function getCookie(name) {
        const nameEQ = name + '=';
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    // --- Visitor & Session Identity ---
    function getVisitorId() {
        let vid = null;
        try {
            vid = localStorage.getItem('vt_vid') || getCookie('vt_vid');
        } catch (e) {}

        if (!vid) {
            vid = 'v_' + uuidv4().replace(/-/g, '').slice(0, 16);
            try {
                localStorage.setItem('vt_vid', vid);
            } catch (e) {}
            setCookie('vt_vid', vid, 365);
        }
        return vid;
    }

    function getSessionId() {
        let sid = null;
        try {
            sid = sessionStorage.getItem('vt_sid');
        } catch (e) {}

        if (!sid) {
            sid = 's_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
            try {
                sessionStorage.setItem('vt_sid', sid);
            } catch (e) {}
        }
        return sid;
    }

    // --- URL Parameters & Meta Tag extraction ---
    function extractUrlParams() {
        const urlParams = new URLSearchParams(window.location.search);
        const params = {};

        // Meta IDs (Primary)
        const adId = urlParams.get('ad_id') || urlParams.get('meta_ad_id');
        const adsetId = urlParams.get('adset_id') || urlParams.get('meta_adset_id');
        const campaignId = urlParams.get('campaign_id') || urlParams.get('meta_campaign_id');

        if (adId) params.meta_ad_id = adId;
        if (adsetId) params.meta_adset_id = adsetId;
        if (campaignId) params.meta_campaign_id = campaignId;

        // Meta Names (Metadata)
        const adName = urlParams.get('ad_name') || urlParams.get('meta_ad_name');
        const adsetName = urlParams.get('adset_name') || urlParams.get('meta_adset_name');
        const campaignName = urlParams.get('campaign_name') || urlParams.get('meta_campaign_name');

        if (adName) params.meta_ad_name = adName;
        if (adsetName) params.meta_adset_name = adsetName;
        if (campaignName) params.meta_campaign_name = campaignName;

        // UTMs
        ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'fbclid', 'ref'].forEach(key => {
            const val = urlParams.get(key);
            if (val) params[key] = val;
        });

        // Cache in sessionStorage so sub-page navigations in same session retain attribution
        try {
            if (Object.keys(params).length > 0) {
                sessionStorage.setItem('vt_attribution', JSON.stringify(params));
            } else {
                const cached = sessionStorage.getItem('vt_attribution');
                if (cached) Object.assign(params, JSON.parse(cached));
            }
        } catch (e) {}

        return params;
    }

    const visitorId = getVisitorId();
    const sessionId = getSessionId();
    const attributionParams = extractUrlParams();

    // --- State Variables ---
    let timeOnPageSeconds = 0;
    let maxScrollDepth = 0;
    let isOfferViewed = false;
    let isCtaClicked = false;
    let isCheckoutStarted = window.location.pathname.includes('checkout');
    let activeTimer = null;
    let isTabVisible = !document.hidden;

    // --- Device Info ---
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const deviceType = isMobile ? 'mobile' : 'desktop';

    // --- Dispatch Event API ---
    function sendEvent(eventName, eventData = {}, isBeacon = false) {
        const payload = {
            visitor_id: visitorId,
            session_id: sessionId,
            event_name: eventName,
            event_data: eventData,
            url_params: attributionParams,
            metrics: {
                time_on_page: timeOnPageSeconds,
                max_scroll_depth: maxScrollDepth,
                offer_viewed: isOfferViewed,
                cta_clicked: isCtaClicked,
                checkout_started: isCheckoutStarted
            },
            landing_page: window.location.pathname + window.location.search,
            referrer: document.referrer || '',
            device_type: deviceType,
            browser: navigator.userAgent,
            timestamp: new Date().toISOString()
        };

        const endpoint = '/api/track';

        if (isBeacon && navigator.sendBeacon) {
            const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
            navigator.sendBeacon(endpoint, blob);
        } else {
            fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                keepalive: true
            }).catch(() => {
                // Silently handle offline/fetch errors
            });
        }
    }

    // --- 1. Initial Landing Event ---
    sendEvent('landing_session', {
        title: document.title,
        path: window.location.pathname
    });

    // --- 2. Active Time On Page Tracker ---
    document.addEventListener('visibilitychange', function () {
        isTabVisible = !document.hidden;
    });

    activeTimer = setInterval(function () {
        if (isTabVisible) {
            timeOnPageSeconds += 1;
            // Trigger raw engaged check at 15s or 30s
            if (timeOnPageSeconds === 15) {
                sendEvent('engaged_15s', { time: 15 });
            }
            if (timeOnPageSeconds === 60) {
                sendEvent('engaged_60s', { time: 60 });
            }
        }
    }, 1000);

    // --- 3. Scroll Depth Measurement (Debounced) ---
    let scrollTimeout = null;
    function calculateScroll() {
        const h = document.documentElement,
              b = document.body,
              st = 'scrollTop',
              sh = 'scrollHeight';
        const percent = Math.round(((h[st] || b[st]) / ((h[sh] || b[sh]) - h.clientHeight)) * 100) || 0;
        const current = Math.min(100, Math.max(0, percent));

        if (current > maxScrollDepth) {
            maxScrollDepth = current;
            if (maxScrollDepth >= 50 && maxScrollDepth < 75) {
                sendEvent('scroll_50', { depth: 50 });
            } else if (maxScrollDepth >= 75 && maxScrollDepth < 90) {
                sendEvent('scroll_75', { depth: 75 });
            } else if (maxScrollDepth >= 90) {
                sendEvent('scroll_90', { depth: 90 });
            }
        }
    }

    window.addEventListener('scroll', function () {
        if (!scrollTimeout) {
            scrollTimeout = setTimeout(function () {
                calculateScroll();
                scrollTimeout = null;
            }, 250);
        }
    }, { passive: true });

    // --- 4. Offer / Pricing View Observer ---
    function setupOfferObserver() {
        const offerSelectors = [
            '#arak',
            '#csomagok',
            '.pricing-box',
            '.pricing-section',
            '.checkout-section',
            '.order-box',
            '#packages'
        ];

        const targetEl = document.querySelector(offerSelectors.join(', '));
        if (targetEl && window.IntersectionObserver) {
            const observer = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting && !isOfferViewed) {
                        isOfferViewed = true;
                        sendEvent('offer_view', {
                            selector: entry.target.id || entry.target.className
                        });
                        observer.disconnect();
                    }
                });
            }, { threshold: 0.3 });

            observer.observe(targetEl);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupOfferObserver);
    } else {
        setupOfferObserver();
    }

    // --- 5. CTA Click Interceptor ---
    document.addEventListener('click', function (e) {
        const target = e.target.closest('a, button, [data-cta]');
        if (!target) return;

        const href = target.getAttribute('href') || '';
        const isCta = target.classList.contains('btn') ||
                      target.hasAttribute('data-cta') ||
                      href.includes('checkout') ||
                      href.includes('#arak') ||
                      target.tagName === 'BUTTON';

        if (isCta) {
            isCtaClicked = true;
            const btnText = (target.innerText || target.textContent || '').trim().slice(0, 60);
            sendEvent('cta_click', {
                button_text: btnText,
                button_href: href,
                button_id: target.id || ''
            });

            if (href.includes('checkout')) {
                isCheckoutStarted = true;
                sendEvent('checkout_start', {
                    button_text: btnText,
                    destination: href
                });
            }
        }
    }, { passive: true });

    // --- 6. Page Unload / Final Sync ---
    window.addEventListener('pagehide', function () {
        sendEvent('session_ping', { final: true }, true);
    });

    // --- Public API ---
    window.VitaTracker = {
        track: function (name, data) {
            sendEvent(name, data);
        },
        getVisitorId: function () {
            return visitorId;
        },
        getSessionId: function () {
            return sessionId;
        },
        getAttribution: function () {
            return Object.assign({}, attributionParams, {
                visitor_id: visitorId,
                session_id: sessionId
            });
        }
    };

})();
