/**
 * Optivoya — Decision DNA Summary Step Module
 * Step 6: Visual Multi-Dimensional Decision DNA Profile Overview
 */

(function () {
    const DNASummaryStep = {
        renderSummary(wizard, container) {
            if (window.DNAMath) window.DNAMath.calculateAllAHP(wizard.state);
            const wDest = wizard.state.calculated_weights.dest;
            const wFlight = wizard.state.calculated_weights.flight;
            const wStay = wizard.state.calculated_weights.stay;

            container.innerHTML = `
                <div style="text-align: center; margin-bottom: 24px;">
                    <div style="font-size: 32px; margin-bottom: 6px;">🧬</div>
                    <h3 style="margin: 0 0 6px 0; font-size: 20px; font-weight: 800; color: var(--text-main);">Az Egyéni Utazási Döntési DNS-ed Készen Áll!</h3>
                    <p style="margin: 0 auto; max-width: 540px; font-size: 13px; color: var(--text-muted);">
                        A páros összehasonlítások és az életszerű döntési helyzetek alapján a rendszer kiszámította a személyre szabott súlyokat és toleranciákat.
                    </p>
                </div>

                <div class="dna-summary-grid" style="margin-bottom: 24px;">
                    <!-- 1. Desztináció Súlyok -->
                    <div style="background: var(--bg-surface); padding: 16px; border-radius: 16px; border: 1px solid var(--border-subtle);">
                        <div style="font-size: 11px; font-weight: 800; color: var(--primary); text-transform: uppercase; margin-bottom: 10px;">🌍 Célállomás Súlyok</div>
                        <div style="display: flex; flex-direction: column; gap: 6px;">
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>💰 Teljes Költség:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wDest.total_cost}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>☀️ Klíma / Időjárás:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wDest.weather}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>🛡️ Közbiztonság:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wDest.safety}%</strong></div>
                        </div>
                    </div>

                    <!-- 2. Járat Súlyok -->
                    <div style="background: var(--bg-surface); padding: 16px; border-radius: 16px; border: 1px solid var(--border-subtle);">
                        <div style="font-size: 11px; font-weight: 800; color: var(--primary); text-transform: uppercase; margin-bottom: 10px;">✈️ Járat Súlyok</div>
                        <div style="display: flex; flex-direction: column; gap: 6px;">
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>💳 Repjegy Ár:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wFlight.price}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>⏱️ Menetidő:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wFlight.duration}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>🔄 Átszállásszám:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wFlight.stops}%</strong></div>
                        </div>
                    </div>

                    <!-- 3. Szállás Súlyok -->
                    <div style="background: var(--bg-surface); padding: 16px; border-radius: 16px; border: 1px solid var(--border-subtle);">
                        <div style="font-size: 11px; font-weight: 800; color: var(--primary); text-transform: uppercase; margin-bottom: 10px;">🏨 Szállás Súlyok</div>
                        <div style="display: flex; flex-direction: column; gap: 6px;">
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>💳 Szobaár / éj:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wStay.price}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>⭐ Vendégértékelés:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wStay.rating}%</strong></div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px;"><span>📍 Lokáció:</span><strong style="font-family:var(--font-mono); color:var(--primary);">${wStay.location}%</strong></div>
                        </div>
                    </div>
                </div>

                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 14px; padding: 14px 18px; text-align: center; color: var(--text-main); font-size: 13px; font-weight: 700;">
                    ✅ A döntési szabályok és küszöbértékek készen állnak az intelligens desztináció-, járat- és szálláselemzésre!
                </div>
            `;
        }
    };

    window.DNASummaryStep = DNASummaryStep;
})();
