/**
 * Optivoya — Unified Trip Cart Facade v2.0
 * Lightweight facade orchestrating TripStore, TripCalculator, TripDrawer, and TripReport.
 * 100% backward-compatible API for window.TripCart and window.TripEngine.
 */

(function () {
    const TripFacade = {
        // 1. STORE & STATE MANAGEMENT
        getTrip() { return window.TripStore.getTrip(); },
        saveTrip(trip) { return window.TripStore.saveTrip(trip); },
        syncToServer(trip) { return window.TripStore.syncToServer(trip); },
        getCart() { return window.TripStore.getCart(); },
        setDestination(data) { return window.TripStore.setDestination(data); },
        setFlight(data) { return window.TripStore.setFlight(data); },
        addFlightShortlist(data) { return window.TripStore.addFlightShortlist(data); },
        setStay(data) { return window.TripStore.setStay(data); },
        addAccommodationShortlist(data) { return window.TripStore.addAccommodationShortlist(data); },
        removeDestination() { return window.TripStore.removeDestination(); },
        removeFlight() { return window.TripStore.removeFlight(); },
        removeStay() { return window.TripStore.removeStay(); },
        setDiningProfile(profileKey) { return window.TripStore.setDiningProfile(profileKey); },
        clearCart() { return window.TripStore.clearCart(); },

        // 2. COST CALCULATION ENGINE
        getNumbeoMetrics(cityName) { return window.TripCalculator.getNumbeoMetrics(cityName); },
        calculateBreakdown(trip) { return window.TripCalculator.calculateBreakdown(trip || this.getTrip()); },

        // 3. UI & DRAWER PRESENTATION
        getNextStepCTA(trip) { return window.TripDrawer.getNextStepCTA(trip || this.getTrip()); },
        render() { return window.TripDrawer.render(); },
        hideBar() { return window.TripDrawer.hideBar(); },
        showBar() { return window.TripDrawer.showBar(); },
        showDrawer() { return window.TripDrawer.showDrawer(); },
        hideDrawer() { return window.TripDrawer.hideDrawer(); },
        showToast(message, icon) { return window.TripDrawer.showToast(message, icon); },
        goToPlannerStep(step) { return window.TripDrawer.goToPlannerStep(step); },

        // 4. REPORT & EXPORT GENERATOR
        exportProposal() { return window.TripReport.exportProposal(this.getTrip(), this.calculateBreakdown()); }
    };

    window.TripCart = TripFacade;
    window.TripEngine = TripFacade;

    document.addEventListener('DOMContentLoaded', () => {
        if (window.TripDrawer) {
            window.TripDrawer.render();
        }
    });
})();
