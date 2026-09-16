/**
 * Optivoya — B2B Value & ROI Calculator (v2.2 with Advisor Role Presets)
 * Computes monthly manual time burden vs. Optivoya conservative saving scenario and monetary value.
 */

(function () {
    const ValueCalculator = {
        init() {
            this.clientInput = document.getElementById('calcClients');
            this.clientVal = document.getElementById('calcClientsVal');
            
            this.hoursInput = document.getElementById('calcHours');
            this.hoursVal = document.getElementById('calcHoursVal');
            
            this.rateInput = document.getElementById('calcRate');
            this.rateVal = document.getElementById('calcRateVal');
            
            // Output elements
            this.outHoursSaved = document.getElementById('outHoursSaved');
            this.outMoneySaved = document.getElementById('outMoneySaved');
            this.outManualHours = document.getElementById('outManualHours');
            this.outAnnualSaved = document.getElementById('outAnnualSaved');
            this.outCapacityGain = document.getElementById('outCapacityGain');
            
            if (!this.clientInput || !this.hoursInput || !this.rateInput) {
                return;
            }
            
            this.bindEvents();
            this.bindPresets();
            this.calculate();
        },
        
        bindEvents() {
            const inputs = [this.clientInput, this.hoursInput, this.rateInput];
            inputs.forEach(inp => {
                inp.addEventListener('input', () => {
                    this.clearActivePreset();
                    this.calculate();
                });
                inp.addEventListener('change', () => this.trackTelemetry());
            });
        },
        
        bindPresets() {
            const presets = document.querySelectorAll('.btn-preset');
            presets.forEach(btn => {
                btn.addEventListener('click', () => {
                    presets.forEach(p => p.classList.remove('active'));
                    btn.classList.add('active');
                    
                    const clients = btn.dataset.clients;
                    const hours = btn.dataset.hours;
                    const rate = btn.dataset.rate;
                    
                    if (clients) this.clientInput.value = clients;
                    if (hours) this.hoursInput.value = hours;
                    if (rate) this.rateInput.value = rate;
                    
                    this.calculate();
                    this.trackTelemetry();
                });
            });
        },
        
        clearActivePreset() {
            document.querySelectorAll('.btn-preset').forEach(p => p.classList.remove('active'));
        },
        
        calculate() {
            const clients = parseInt(this.clientInput.value, 10) || 15;
            const hoursPerClient = parseFloat(this.hoursInput.value) || 4;
            const hourlyRate = parseInt(this.rateInput.value, 10) || 12000;
            
            // Update input label displays
            if (this.clientVal) this.clientVal.innerText = `${clients} ügyfél / hó`;
            if (this.hoursVal) this.hoursVal.innerText = `${hoursPerClient} óra / ügyfél`;
            if (this.rateVal) this.rateVal.innerText = `${hourlyRate.toLocaleString()} Ft / óra`;
            
            // Calculations
            const manualTotalHours = Math.round(clients * hoursPerClient);
            // Optivoya conservative time reduction: 75%
            const hoursSaved = Math.round(manualTotalHours * 0.75);
            const optivoyaTimeSpent = manualTotalHours - hoursSaved;
            
            const monthlyMoneySaved = Math.round(hoursSaved * hourlyRate);
            const annualMoneySaved = Math.round(monthlyMoneySaved * 12);
            const extraCapacityClients = Math.round(clients * 2.5);
            
            // Render outputs
            if (this.outHoursSaved) this.outHoursSaved.innerText = `${hoursSaved} óra / hó`;
            if (this.outMoneySaved) this.outMoneySaved.innerText = `+${monthlyMoneySaved.toLocaleString()} Ft / hó`;
            if (this.outManualHours) this.outManualHours.innerText = `${manualTotalHours} óra / hó (Optivoyával: ~${optivoyaTimeSpent} óra)`;
            if (this.outAnnualSaved) this.outAnnualSaved.innerText = `~${annualMoneySaved.toLocaleString()} Ft / év`;
            if (this.outCapacityGain) this.outCapacityGain.innerText = `+${extraCapacityClients} extra ügyfél kiszolgálása`;
            
            // Store state in window for lead form pre-fill
            window.OptivoyaCalculatedROI = {
                clients,
                hoursPerClient,
                hourlyRate,
                hoursSaved,
                monthlyMoneySaved
            };
        },
        
        trackTelemetry() {
            if (window.OptivoyaLead && window.OptivoyaLead.trackEvent) {
                window.OptivoyaLead.trackEvent('b2b_calculator_adjusted', {
                    clients: this.clientInput.value,
                    hours: this.hoursInput.value,
                    rate: this.rateInput.value,
                    estimated_saving: window.OptivoyaCalculatedROI?.monthlyMoneySaved
                });
            }
        }
    };
    
    document.addEventListener('DOMContentLoaded', () => {
        ValueCalculator.init();
    });
    
    window.ValueCalculator = ValueCalculator;
})();
