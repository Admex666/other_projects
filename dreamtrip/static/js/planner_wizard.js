/**
 * Optivoya — Master Travel Planner Wizard Engine v2.0 (Facade Controller)
 * Orchestrates PlannerState, PlannerIntake, PlannerDestinations, PlannerFlights, PlannerStays, and PlannerSummary.
 * 100% backward-compatible API for window.Wizard.
 */

(function () {
    const WizardFacade = {
        // Step Navigation
        goToStep(stepNum) { return window.PlannerState.setStep(stepNum); },
        startPlanning() { return window.PlannerDestinations.startPlanning(); },

        // Intake & Preferences
        setOrigin(city) { return window.PlannerIntake.setOrigin(city); },
        switchDateMode(mode) { return window.PlannerIntake.switchDateMode(mode); },
        onDurationSliderChange(val) { return window.PlannerIntake.onDurationSliderChange(val); },
        onYearChange(year) { return window.PlannerIntake.onYearChange(year); },
        onMonthChange(month) { return window.PlannerIntake.onMonthChange(month); },
        applyExactPreset(days, duration, btn) { return window.PlannerIntake.applyExactPreset(days, duration, btn); },
        toggleDeparturePref(checked) { return window.PlannerIntake.toggleDeparturePref(checked); },
        onDepHourChange(val) { return window.PlannerIntake.onDepHourChange(val); },
        setMaxDuration(hours) { return window.PlannerIntake.setMaxDuration(hours); },
        onRatingChange(val) { return window.PlannerIntake.onRatingChange(val); },
        openDecisionDNA() { return window.PlannerIntake.openDecisionDNA(); },
        openAHPModal() { return window.PlannerIntake.openDecisionDNA(); },
        openStayPrioritiesModal() { return window.PlannerIntake.openDecisionDNA(); },
        openPrometheeModal() { return window.PlannerIntake.openDecisionDNA(); },
        closeAHPModal() {
            const backdrop = document.getElementById('ahpModalBackdrop');
            if (backdrop) backdrop.style.display = 'none';
        },

        // Destinations Step
        selectDestination(index) { return window.PlannerDestinations.selectDestination(index); },
        recalculateDestinations() { return window.PlannerDestinations.recalculateDestinations(); },

        // Flights Step
        selectFlight(index) { return window.PlannerFlights.selectFlight(index); },
        recalculateFlights() { return window.PlannerFlights.recalculateFlights(); },

        // Stays Step
        selectStay(index) { return window.PlannerStays.selectStay(index); },
        recalculateStays() { return window.PlannerStays.recalculateStays(); },

        // Summary & Export
        exportProposal() { return window.PlannerSummary.exportProposal(); },
        resumeSessionFromCart() { return window.PlannerSummary.resumeSessionFromCart(); }
    };

    window.Wizard = WizardFacade;

    // Global DOM initialization
    document.addEventListener('DOMContentLoaded', () => {
        const state = window.PlannerState;
        if (!state) return;

        // 1. Central Location Autocomplete
        if (window.initLocationAutocomplete) {
            window.initLocationAutocomplete({
                inputId: 'origin',
                dropdownId: 'origin-dropdown',
                mode: 'origin'
            });
        }

        // 2. Central Date Range Picker Flatpickr wrapper
        if (window.initAdvisorDatePicker) {
            state.exact_fp = window.initAdvisorDatePicker({
                triggerElementId: 'exact_date_picker_trigger',
                datePrimaryLabelId: 'exact_date_primary',
                dateSubLabelId: 'exact_date_sub',
                hiddenStartInputId: 'exact_out_date',
                hiddenEndInputId: 'exact_in_date',
                defaultStartDays: 14,
                defaultDurationDays: 7
            });

            // Interval Mode: Outbound Departure Window Range Picker
            state.interval_out_fp = window.initAdvisorDatePicker({
                triggerElementId: 'interval_out_picker_trigger',
                datePrimaryLabelId: 'interval_out_primary',
                dateSubLabelId: 'interval_out_sub',
                hiddenStartInputId: 'interval_out_from',
                hiddenEndInputId: 'interval_out_to',
                defaultStartDays: 7,
                defaultDurationDays: 14,
                onDateChange: function (startIso, endIso) {
                    if (startIso && state.interval_in_fp) {
                        state.interval_in_fp.set('minDate', startIso);

                        const inFromInput = document.getElementById('interval_in_from');
                        const currentInFrom = inFromInput ? inFromInput.value : null;

                        if (currentInFrom && currentInFrom < startIso) {
                            const startD = new Date(startIso);
                            const newInFrom = new Date(startD.getTime() + 7 * 24 * 60 * 60 * 1000);
                            const newInTo = new Date(startD.getTime() + 21 * 24 * 60 * 60 * 1000);
                            state.interval_in_fp.setDate([newInFrom, newInTo], true);
                            if (typeof state.interval_in_fp.updateDisplay === 'function') {
                                state.interval_in_fp.updateDisplay(newInFrom, newInTo);
                            }
                        }
                    }
                }
            });

            // Interval Mode: Inbound Return Window Range Picker (minDate = earliest outbound)
            const initialOutFrom = document.getElementById('interval_out_from')?.value || "today";
            state.interval_in_fp = window.initAdvisorDatePicker({
                triggerElementId: 'interval_in_picker_trigger',
                datePrimaryLabelId: 'interval_in_primary',
                dateSubLabelId: 'interval_in_sub',
                hiddenStartInputId: 'interval_in_from',
                hiddenEndInputId: 'interval_in_to',
                minDate: initialOutFrom,
                defaultStartDays: 14,
                defaultDurationDays: 22
            });
        }

        // 3. Adults & Children Steppers
        ['adults_count', 'children_count'].forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                const sync = () => {
                    const displayId = id.replace('_count', '_display');
                    const disp = document.getElementById(displayId);
                    if (disp) disp.innerText = input.value;
                };
                input.addEventListener('input', sync);
                input.addEventListener('change', sync);
            }
        });

        // 4. Max Flight Duration Stepper
        const durInput = document.getElementById('intake_max_flight_duration');
        if (durInput) {
            const syncDur = () => {
                const val = parseInt(durInput.value, 10) || 0;
                window.PlannerIntake.setMaxDuration(val);
            };
            durInput.addEventListener('input', syncDur);
            durInput.addEventListener('change', syncDur);
        }

        // 5. Month & Stay Duration Steppers
        const monthDurInput = document.getElementById('month_duration_input');
        if (monthDurInput) {
            const syncMonth = () => {
                const val = parseInt(monthDurInput.value, 10) || 7;
                window.PlannerIntake.onDurationSliderChange(val);
            };
            monthDurInput.addEventListener('input', syncMonth);
            monthDurInput.addEventListener('change', syncMonth);
        }

        const intMinInput = document.getElementById('interval_min_stay_input');
        if (intMinInput) {
            const syncMin = () => {
                const disp = document.getElementById('interval_min_stay_display');
                if (disp) disp.innerText = `${intMinInput.value} nap`;
            };
            intMinInput.addEventListener('input', syncMin);
            intMinInput.addEventListener('change', syncMin);
        }

        const intMaxInput = document.getElementById('interval_max_stay_input');
        if (intMaxInput) {
            const syncMax = () => {
                const disp = document.getElementById('interval_max_stay_display');
                if (disp) disp.innerText = `${intMaxInput.value} nap`;
            };
            intMaxInput.addEventListener('input', syncMax);
            intMaxInput.addEventListener('change', syncMax);
        }

        // 6. Chip select buttons
        document.querySelectorAll('.chip-select-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const cb = btn.querySelector('input[type="checkbox"]');
                if (cb) {
                    cb.checked = !cb.checked;
                    btn.classList.toggle('active', cb.checked);
                }
            });
        });

        // 7. Initialize Year and Month pickers
        if (window.PlannerIntake) {
            window.PlannerIntake.initYearAndMonthPickers();
        }

        // 8. Auto-resume from TripCart
        setTimeout(() => {
            if (window.PlannerSummary) {
                window.PlannerSummary.resumeSessionFromCart();
            }
        }, 150);
    });
})();
