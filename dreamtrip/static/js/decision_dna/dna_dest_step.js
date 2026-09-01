/**
 * Optivoya — Decision DNA Destination Steps Module
 * Step 0: Destination Pairwise Matrix
 * Step 1: Destination Scenarios (Cost, Temperature, Safety A/B + statements)
 */

(function () {
    const DNADestStep = {
        renderDestAHP(wizard, container) {
            const pairs = [
                { id: 'total_cost_vs_weather', name1: '💰 Teljes Költség', name2: '☀️ Klíma / Időjárás', desc: 'Olcsóbb utazás vagy garantáltan kellemes időjárás?' },
                { id: 'total_cost_vs_safety', name1: '💰 Teljes Költség', name2: '🛡️ Közbiztonság', desc: 'Alacsonyabb összköltség vagy kiemelkedő biztonsági index?' },
                { id: 'weather_vs_safety', name1: '☀️ Klíma / Időjárás', name2: '🛡️ Közbiztonság', desc: 'Ideális időjárás vagy a maximális biztonság a fontosabb?' }
            ];
            wizard.renderPairwiseMatrix(container, '🌍 1. Lépés: Célállomás Súlyozás (Páros Döntés)', 'Melyik szempont mennyire fontosabb számodra a desztináció kiválasztásakor?', pairs, 'dest_ahp');
        },

        renderDestScenarios(wizard, container) {
            const state = wizard.state;
            const cCost = state.dest_promethee.cost;
            const cTemp = state.dest_promethee.temp;
            const cSafe = state.dest_promethee.safety;

            const isCostChosen = state.chosen_cards.dest_cost !== null;
            const isTempUnlocked = state.unlocked.dest_temp || isCostChosen;
            const isTempChosen = state.chosen_cards.dest_temp !== null;
            const isSafeUnlocked = state.unlocked.dest_safety || isTempChosen;
            const isSafeChosen = state.chosen_cards.dest_safety !== null;

            container.innerHTML = `
                <div style="margin-bottom: 18px;">
                    <h4 style="margin: 0 0 4px 0; font-size: 16.5px; font-weight: 800; color: var(--text-main);">🌍 2. Lépés: Célállomás Döntési Helyzetek</h4>
                    <p style="margin: 0; font-size: 12.5px; color: var(--text-muted);">Minden kritériumnál válaszd ki a döntési stílusodat (A vagy B), majd finomhangold a mondatot:</p>
                </div>

                <!-- 1. KÖLTSÉG SZITUÁCIÓ -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px;">
                    <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 10px;">
                        💰 1. Hogyan gondolkodsz az úti cél összköltségéről?
                    </div>
                    
                    <div class="dna-scenario-grid" style="margin-bottom: ${isCostChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_cost', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_cost === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_cost === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Kisebb különbség még nem számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy kisebb eltérés még nem döntő, de egy bizonyos összeg felett már biztosan az olcsóbb úti célt választom.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_cost', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_cost === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_cost === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Minden forint azonnal számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Már a legelső forint különbség is azonnal előnyt jelent az olcsóbb célállomásnak.</div>
                        </div>
                    </div>

                    ${isCostChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${cCost.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cCost.q.toLocaleString()} Ft</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                összköltség különbség még <strong>nem számít</strong> nekem két város között, de 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cCost.p.toLocaleString()} Ft</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                felett már <strong>egyértelműen az olcsóbb úti cél</strong> a nyerő.”
                            ` : `
                                „Már a legkisebb költségkülönbség is számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cCost.p.toLocaleString()} Ft</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'cost', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                különbségnél már <strong>100%-ban az olcsóbb desztináció</strong> felé billen a mérleg.”
                            `}
                        </div>
                    ` : ''}
                </div>

                <!-- 2. HŐMÉRSÉKLET SZITUÁCIÓ -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px; opacity: ${isTempUnlocked ? '1.0' : '0.45'}; pointer-events: ${isTempUnlocked ? 'auto' : 'none'}; filter: ${isTempUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">☀️ 2. Mennyire vagy szigorú az időjárással?</div>
                        ${!isTempUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">🔒 Válaszd ki az 1. pontot a feloldáshoz</span>' : ''}
                    </div>
                    
                    <div class="dna-scenario-grid" style="margin-bottom: ${isTempChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_temp', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_temp === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_temp === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Pár fok ide vagy oda még jó</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy kisebb eltérés még kellemes idő, csak a szélsőséges hideget vagy hőséget kerülöm.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_temp', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_temp === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_temp === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Pontosan az ideális hőfokot keresem</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Minden egyes fok eltérés azonnal ront a helyszín vonzerején.</div>
                        </div>
                    </div>

                    ${isTempChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${cTemp.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">±${cTemp.q} °C</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                eltérés a kívánt hőfoktól még <strong>ugyanolyan jó nekem</strong>, de 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">±${cTemp.p} °C</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                eltérés felett már <strong>kifejezetten gyengébbnek</strong> tekintem.”
                            ` : `
                                „Minden egyes fok eltérés azonnal számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">±${cTemp.p} °C</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'temp', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                eltérésnél már <strong>100%-ban a pontosabb célpont</strong> a preferált.”
                            `}
                        </div>
                    ` : ''}
                </div>

                <!-- 3. BIZTONSÁG SZITUÁCIÓ -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; opacity: ${isSafeUnlocked ? '1.0' : '0.45'}; pointer-events: ${isSafeUnlocked ? 'auto' : 'none'}; filter: ${isSafeUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">🛡️ 3. Hogyan tekintesz a közbiztonságra?</div>
                        ${!isSafeUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">🔒 Válaszd ki a 2. pontot a feloldáshoz</span>' : ''}
                    </div>

                    <div class="dna-scenario-grid" style="margin-bottom: ${isSafeChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_safety', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_safety === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_safety === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Kisebb különbség még belefér</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Pár pont eltérés még nem döntő, de jelentős biztonsági különbségnél a biztonságosabb kell.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_safety', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_safety === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_safety === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Minden biztonsági pont számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Minden egyes pont biztonsági előny azonnal a biztonságosabb város felé billenti a mérleget.</div>
                        </div>
                    </div>
                    
                    ${isSafeChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${cSafe.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cSafe.q} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                biztonsági pontszám különbség még <strong>elhanyagolható</strong>, de 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cSafe.p} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                különbség felett már <strong>kizárólag a biztonságosabb város</strong> a preferált.”
                            ` : `
                                „Minden egyes pont biztonsági előny számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${cSafe.p} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.dest_promethee, 'safety', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                pontkülönbségnél már <strong>100%-ban a biztonságosabb úti cél</strong> felé billen a mérleg.”
                            `}
                        </div>
                    ` : ''}
                </div>
            `;
        }
    };

    window.DNADestStep = DNADestStep;
})();
