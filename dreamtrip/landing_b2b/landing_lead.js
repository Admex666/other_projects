/**
 * Optivoya — B2B Lead Capture, Access Gate & Telemetry Module (v2.3)
 * Intercepts all platform entry points, displays the closed B2B gate modal,
 * and rigorously tracks every button click & telemetry event.
 */

(function () {
    const OptivoyaLead = {
        sessionId: 'sess_' + Math.random().toString(36).substring(2, 12) + '_' + Date.now(),
        attribution: {},
        currentTriggerCTA: 'general_beta_modal',
        
        init() {
            this.extractAttribution();
            this.bindAccessGateAndModalEvents();
            this.bindButtonTracking();
            this.bindForm();
            this.bindTabs();
            this.bindFAQ();
            this.bindSmoothScroll();
            this.trackEvent('b2b_landing_view', { 
                attribution: this.attribution,
                screen_width: window.innerWidth,
                screen_height: window.innerHeight
            });
        },
        
        extractAttribution() {
            const params = new URLSearchParams(window.location.search);
            this.attribution = {
                utm_source: params.get('utm_source') || 'direct',
                utm_medium: params.get('utm_medium') || '',
                utm_campaign: params.get('utm_campaign') || '',
                utm_term: params.get('utm_term') || '',
                utm_content: params.get('utm_content') || '',
                ref: params.get('ref') || '',
                referrer: document.referrer || 'direct'
            };
        },
        
        bindAccessGateAndModalEvents() {
            const modal = document.getElementById('b2bBetaModal');
            const closeBtn = document.getElementById('b2bModalClose');
            
            // 1. Beta Modal Triggers
            document.querySelectorAll('.trigger-beta-modal').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const ctaName = btn.getAttribute('data-cta-name') || 'beta_modal_btn';
                    const btnText = btn.innerText.trim();
                    this.trackButtonClick(ctaName, 'beta_modal', btnText);
                    this.openModal('beta', ctaName);
                });
            });
            
            // 2. Access Gate Triggers (Blocked Platform Actions)
            document.querySelectorAll('.trigger-access-gate').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const ctaName = btn.getAttribute('data-cta-name') || 'locked_feature_btn';
                    const btnText = btn.innerText.trim();
                    this.trackButtonClick(ctaName, 'access_gate', btnText);
                    this.openModal('gate', ctaName);
                });
            });
            
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.closeModal());
            }
            
            if (modal) {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) this.closeModal();
                });
            }
            
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && modal && modal.classList.contains('active')) {
                    this.closeModal();
                }
            });
        },

        bindButtonTracking() {
            // Track all other CTA buttons and links with data-cta-name
            document.querySelectorAll('[data-cta-name]').forEach(el => {
                // Avoid double binding if already a modal trigger
                if (!el.classList.contains('trigger-beta-modal') && !el.classList.contains('trigger-access-gate')) {
                    el.addEventListener('click', () => {
                        const ctaName = el.getAttribute('data-cta-name');
                        const text = el.innerText.trim();
                        this.trackButtonClick(ctaName, 'general_cta', text);
                    });
                }
            });
        },
        
        trackButtonClick(ctaName, triggerType, buttonText) {
            console.log(`[Optivoya Telemetry] Button Clicked: ${ctaName} (${triggerType}) -> "${buttonText}"`);
            this.trackEvent('b2b_button_click', {
                cta_name: ctaName,
                trigger_type: triggerType,
                button_text: buttonText,
                page_location: window.location.pathname
            });
        },
        
        openModal(mode = 'beta', ctaSource = 'unknown') {
            const modal = document.getElementById('b2bBetaModal');
            if (!modal) return;
            
            this.currentTriggerCTA = ctaSource;
            const ctaHiddenInput = document.getElementById('leadCtaSource');
            if (ctaHiddenInput) ctaHiddenInput.value = ctaSource;
            
            const badgeEl = document.getElementById('b2bModalBadge');
            const titleEl = document.getElementById('b2bModalTitle');
            const descEl = document.getElementById('b2bModalDesc');
            const submitBtn = document.getElementById('leadSubmitBtn');
            
            if (mode === 'gate') {
                if (badgeEl) {
                    badgeEl.innerHTML = '<span class="material-symbols-outlined" style="font-size:12px; vertical-align:middle; margin-right:3px;">lock</span> ZÁRT B2B FUNKCIÓ';
                    badgeEl.style.borderColor = 'rgba(245, 158, 11, 0.4)';
                    badgeEl.style.color = '#fbbf24';
                    badgeEl.style.background = 'rgba(245, 158, 11, 0.12)';
                }
                if (titleEl) {
                    titleEl.innerText = 'Kérj Hozzáférést a Döntési Motorhoz';
                }
                if (descEl) {
                    descEl.innerHTML = 'A Master Planner és az élő ajánlatkészítő rendszer jelenleg <strong>zártkörű béta</strong> programban érhető el. Add meg az adataidat a próbaverzió aktiválásához!';
                }
                if (submitBtn) {
                    submitBtn.innerHTML = '<span>Hozzáférési Link Kérése</span> <span class="material-symbols-outlined" style="font-size: 17px;">arrow_forward</span>';
                }
            } else {
                if (badgeEl) {
                    badgeEl.innerHTML = 'B2B BÉTA PROGRAM';
                    badgeEl.style.borderColor = '';
                    badgeEl.style.color = '';
                    badgeEl.style.background = '';
                }
                if (titleEl) {
                    titleEl.innerText = 'Jelentkezés az Optivoya Béta Hozzáféréshez';
                }
                if (descEl) {
                    descEl.innerText = 'Add meg az adataidat, és a jóváhagyást követően megküldjük a személyre szabott hozzáférést.';
                }
                if (submitBtn) {
                    submitBtn.innerHTML = '<span>Jelentkezés Beküldése</span> <span class="material-symbols-outlined" style="font-size: 17px;">arrow_forward</span>';
                }
            }
            
            // Pre-fill calculated savings if available
            const calc = window.OptivoyaCalculatedROI;
            if (calc) {
                const clientsInp = document.getElementById('leadClients');
                if (clientsInp && !clientsInp.value) clientsInp.value = calc.clients;
                
                const rateInp = document.getElementById('leadHourlyRate');
                if (rateInp && !rateInp.value) rateInp.value = calc.hourlyRate;
            }
            
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            this.trackEvent('b2b_beta_modal_opened', { mode, cta_source: ctaSource });
        },
        
        closeModal() {
            const modal = document.getElementById('b2bBetaModal');
            if (!modal) return;
            modal.classList.remove('active');
            document.body.style.overflow = '';
        },
        
        bindForm() {
            const form = document.getElementById('b2bBetaForm');
            if (!form) return;
            
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const submitBtn = form.querySelector('button[type="submit"]');
                const originalContent = submitBtn ? submitBtn.innerHTML : 'Jelentkezés beküldése';
                
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerText = 'Küldés folyamatban...';
                }
                
                const calc = window.OptivoyaCalculatedROI || {};
                
                const payload = {
                    name: document.getElementById('leadName')?.value?.trim(),
                    email: document.getElementById('leadEmail')?.value?.trim(),
                    agency_name: document.getElementById('leadAgency')?.value?.trim() || '',
                    agency_type: document.getElementById('leadAgencyType')?.value || 'independent_advisor',
                    clients_per_month: parseInt(document.getElementById('leadClients')?.value, 10) || calc.clients || 10,
                    research_hours_per_client: calc.hoursPerClient || 4.0,
                    hourly_rate_huf: parseInt(document.getElementById('leadHourlyRate')?.value, 10) || calc.hourlyRate || 12000,
                    estimated_monthly_saving_huf: calc.monthlyMoneySaved || 0,
                    current_tools: document.getElementById('leadCurrentTools')?.value?.trim() || '',
                    message: document.getElementById('leadMessage')?.value?.trim() || '',
                    cta_source: this.currentTriggerCTA,
                    utm_source: this.attribution.utm_source,
                    utm_medium: this.attribution.utm_medium,
                    utm_campaign: this.attribution.utm_campaign,
                    utm_term: this.attribution.utm_term,
                    utm_content: this.attribution.utm_content,
                    referrer: this.attribution.referrer,
                    client_session_id: this.sessionId,
                    submitted_at: new Date().toISOString()
                };
                
                // Always save locally in localStorage as a bulletproof fallback
                try {
                    const existingLeads = JSON.parse(localStorage.getItem('optivoya_b2b_leads') || '[]');
                    existingLeads.push(payload);
                    localStorage.setItem('optivoya_b2b_leads', JSON.stringify(existingLeads));
                } catch (err) {}

                // Send lead conversion telemetry event
                this.trackEvent('b2b_lead_submitted', {
                    cta_source: this.currentTriggerCTA,
                    agency_type: payload.agency_type,
                    estimated_monthly_saving_huf: payload.estimated_monthly_saving_huf
                });
                
                try {
                    const res = await fetch('/api/b2b/lead', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    
                    const data = await res.json().catch(() => ({ status: 'ok' }));
                    this.renderSuccessScreen(payload);
                } catch (err) {
                    // Fallback graceful success even on static Vercel host without backend
                    console.log('[Optivoya Lead] Handled offline/standalone lead submission:', payload);
                    this.renderSuccessScreen(payload);
                }
            });
        },

        renderSuccessScreen(payload) {
            const modalBody = document.querySelector('.b2b-modal-card');
            if (modalBody) {
                modalBody.innerHTML = `
                    <div style="text-align: center; padding: 24px 0;">
                        <span class="material-symbols-outlined" style="font-size: 56px; color: #10b981; margin-bottom: 12px;">task_alt</span>
                        <h3 style="font-size: 24px; font-weight: 800; margin-bottom: 10px; color: #ffffff;">Sikeres Béta Regisztráció!</h3>
                        <p style="font-size: 14.5px; color: var(--b2b-text-secondary); line-height: 1.6; margin-bottom: 24px;">
                            Köszönjük a jelentkezést, <strong>${payload.name || ''}</strong>!<br>
                            Az Optivoya B2B Advisor hozzáférési linkjét és a személyre szabott bevezető útmutatót hamarosan elküldjük a(z) <strong>${payload.email}</strong> címre.
                        </p>
                        <button class="btn-b2b-primary" style="width: 100%;" onclick="window.OptivoyaLead.closeModal()">Visszatérés az oldalra</button>
                    </div>
                `;
            }
        },
        
        bindTabs() {
            const tabBtns = document.querySelectorAll('.b2b-tab-btn');
            const tabPanels = document.querySelectorAll('.b2b-tab-content-panel');
            
            tabBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const targetId = btn.dataset.tab;
                    tabBtns.forEach(b => b.classList.remove('active'));
                    tabPanels.forEach(p => p.classList.remove('active'));
                    
                    btn.classList.add('active');
                    const targetPanel = document.getElementById(targetId);
                    if (targetPanel) targetPanel.classList.add('active');
                    
                    this.trackEvent('b2b_tour_tab_switched', { tab: targetId });
                });
            });
        },
        
        bindFAQ() {
            const faqItems = document.querySelectorAll('.b2b-faq-item');
            faqItems.forEach(item => {
                const question = item.querySelector('.b2b-faq-question');
                if (question) {
                    question.addEventListener('click', () => {
                        const isOpen = item.classList.contains('active');
                        faqItems.forEach(i => i.classList.remove('active'));
                        if (!isOpen) {
                            item.classList.add('active');
                            this.trackEvent('b2b_faq_opened', { question: question.innerText.trim() });
                        }
                    });
                }
            });
        },
        
        bindSmoothScroll() {
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    const targetId = this.getAttribute('href');
                    if (targetId && targetId !== '#') {
                        const targetEl = document.querySelector(targetId);
                        if (targetEl) {
                            e.preventDefault();
                            targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }
                });
            });
        },
        
        trackEvent(eventType, metaData = {}) {
            try {
                fetch('/api/analytics/event', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        event_type: eventType,
                        session_id: this.sessionId,
                        module: 'b2b_landing',
                        meta_data: {
                            ...metaData,
                            ...this.attribution,
                            url: window.location.href,
                            timestamp: new Date().toISOString()
                        }
                    })
                }).catch(() => {});
            } catch (e) {}
        }
    };
    
    document.addEventListener('DOMContentLoaded', () => {
        OptivoyaLead.init();
    });
    
    window.OptivoyaLead = OptivoyaLead;
})();
