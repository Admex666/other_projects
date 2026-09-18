/**
 * Optivoya — Decision DNA Destination Steps Module
 * Step 0: Destination Pairwise Matrix
 * Step 1: Destination Scenarios (Cost, Temperature, Safety A/B + statements)
 */

(function () {
    const DNADestStep = {
        renderDestAHP(wizard, container) {
            const pairs = [
                { id: 'total_cost_vs_weather', c1: 'total_cost', c2: 'weather', name1: 'Teljes Költség', name2: 'Klíma / Időjárás', desc: 'Olcsóbb utazás vagy garantáltan kellemes időjárás?' },
                { id: 'total_cost_vs_safety', c1: 'total_cost', c2: 'safety', name1: 'Teljes Költség', name2: 'Közbiztonság', desc: 'Alacsonyabb összköltség vagy kiemelkedő biztonsági index?' },
                { id: 'total_cost_vs_experience', c1: 'total_cost', c2: 'experience', name1: 'Teljes Költség', name2: 'Élmények & Látnivalók', desc: 'Alacsonyabb költség vagy gazdag látnivaló- és élménykínálat?' },
                { id: 'weather_vs_safety', c1: 'weather', c2: 'safety', name1: 'Klíma / Időjárás', name2: 'Közbiztonság', desc: 'Ideális időjárás vagy a maximális biztonság a fontosabb?' },
                { id: 'weather_vs_experience', c1: 'weather', c2: 'experience', name1: 'Klíma / Időjárás', name2: 'Élmények & Látnivalók', desc: 'Tökéletes klíma és napsütés vagy világhírű látnivalók és programok?' },
                { id: 'safety_vs_experience', c1: 'safety', c2: 'experience', name1: 'Közbiztonság', name2: 'Élmények & Látnivalók', desc: 'Maximális nyugalom/biztonság vagy nyüzsgő, élményekkel teli nagyváros?' }
            ];
            const criteriaList = [
                { key: 'total_cost', label: '💰 Költség / Büdzsé' },
                { key: 'weather', label: '☀️ Klíma / Időjárás' },
                { key: 'safety', label: '🛡️ Közbiztonság' },
                { key: 'experience', label: '🏛️ Élmények & Látnivalók' }
            ];
            wizard.renderPairwiseMatrix(container, '1. Lépés: Célállomás Súlyozás (Páros Összehasonlítás)', 'Válaszd ki a releváns szempontokat, majd finomhangold a relatív fontosságukat:', pairs, 'dest_ahp', 'dest', criteriaList);
        },

        renderDestScenarios(wizard, container) {
            const state = wizard.state;
            const cCost = state.dest_promethee.cost;
            const cTemp = state.dest_promethee.temp;
            const cSafe = state.dest_promethee.safety;

            const active = state.active_criteria?.dest || ['total_cost', 'weather', 'safety', 'experience'];
            const isCostActive = active.includes('total_cost');
            const isTempActive = active.includes('weather');
            const isSafeActive = active.includes('safety');
            const isExpActive = active.includes('experience');

            const isCostChosen = state.chosen_cards.dest_cost !== null;
            const isTempUnlocked = state.unlocked.dest_temp || (!isCostActive || isCostChosen);
            const isTempChosen = state.chosen_cards.dest_temp !== null;
            const isSafeUnlocked = state.unlocked.dest_safety || (isTempUnlocked && (!isTempActive || isTempChosen));
            const isSafeChosen = state.chosen_cards.dest_safety !== null;
            const isExpUnlocked = state.unlocked.dest_exp || (isSafeUnlocked && (!isSafeActive || isSafeChosen));
            const isExpChosen = state.chosen_cards.dest_exp !== null;

            container.innerHTML = `
                <div style="margin-bottom: 18px;">
                    <h4 style="margin: 0 0 4px 0; font-size: 16.5px; font-weight: 800; color: var(--text-main);">2. Lépés: Célállomás Döntési Helyzetek</h4>
                    <p style="margin: 0; font-size: 12.5px; color: var(--text-muted);">A kiválasztott releváns kritériumoknál válaszd ki a döntési stílusodat (A vagy B):</p>
                </div>

                <!-- 1. KÖLTSÉG SZITUÁCIÓ -->
                ${isCostActive ? `
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px;">
                    <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 10px;">
                        1. Hogyan gondolkodsz az úti cél összköltségéről?
                    </div>
                    
                    <div class="dna-scenario-grid" style="margin-bottom: ${isCostChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_cost', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_cost === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_cost === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">A) Kisebb különbség még nem számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy kisebb eltérés még nem döntő, de egy bizonyos összeg felett már biztosan az olcsóbb úti célt választom.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_cost', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_cost === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_cost === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">B) Minden forint azonnal számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Már a legelső forint különbség is azonnal előnyt jelent az olcsóbb célállomásnak.</div>
                        </div>
                    </div>

                    ${isCostChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.2; animation: fadeInScale 0.2s ease;">
                            ${cCost.type === 5 ? `
                                „Legfeljebb 
                                ${wizard.renderNumericControl({ objName: 'dest_promethee', key: 'cost', param: 'q', value: cCost.q, unit: 'Ft', min: 0, max: 100000, step: 1000, inputWidth: '80px' })}
                                összköltség különbség még <strong>nem számít</strong> nekem két város között, de 
                                ${wizard.renderNumericControl({ objName: 'dest_promethee', key: 'cost', param: 'p', value: cCost.p, unit: 'Ft', min: 5000, max: 250000, step: 5000, inputWidth: '85px' })}
                                felett már <strong>egyértelműen az olcsóbb úti cél</strong> a nyerő.”
                            ` : `
                                „Már a legkisebb költségkülönbség is számít, és 
                                ${wizard.renderNumericControl({ objName: 'dest_promethee', key: 'cost', param: 'p', value: cCost.p, unit: 'Ft', min: 5000, max: 250000, step: 5000, inputWidth: '85px' })}
                                különbségnél már <strong>100%-ban az olcsóbb desztináció</strong> felé billen a mérleg.”
                            `}
                        </div>
                    ` : ''}
                </div>
                ` : ''}

                <!-- 2. HŐMÉRSÉKLET SZITUÁCIÓ -->
                ${isTempActive ? `
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px; opacity: ${isTempUnlocked ? '1.0' : '0.45'}; pointer-events: ${isTempUnlocked ? 'auto' : 'none'}; filter: ${isTempUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">2. Mennyire vagy szigorú az időjárással?</div>
                        ${!isTempUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">Válaszd ki az előző pontot a feloldáshoz</span>' : ''}
                    </div>
                    
                    <div class="dna-scenario-grid" style="margin-bottom: ${isTempChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_temp', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_temp === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_temp === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">A) Pár fok ide vagy oda még jó</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy kisebb eltérés még kellemes idő, csak a szélsőséges hideget vagy hőséget kerülöm.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_temp', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_temp === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_temp === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">B) Pontosan az ideális hőfokot keresem</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Minden egyes fok eltérés azonnal ront a helyszín vonzerején.</div>
                        </div>
                    </div>

                    ${isTempChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.2; animation: fadeInScale 0.2s ease;">
                            ${cTemp.type === 5 ? `
                                „Legfeljebb 
                                ${wizard.renderNumericControl({ objName: 'dest_promethee', key: 'temp', param: 'q', value: cTemp.q, unit: '°C', min: 0, max: 10, step: 0.5, inputWidth: '60px' })}
                                eltérés a kívánt hőfoktól még <strong>ugyanolyan jó nekem</strong>, de 
                                ${wizard.renderNumericControl({ objName: 'dest_promethee', key: 'temp', param: 'p', value: cTemp.p, unit: '°C', min: 1, max: 20, step: 0.5, inputWidth: '60px' })}
                                eltérés felett már <strong>kifejezetten gyengébbnek</strong> tekintem.”
                            ` : `
                                „Minden egyes fok eltérés azonnal számít, és 
                                ${wizard.renderNumericControl({ objName: 'dest_promethee', key: 'temp', param: 'p', value: cTemp.p, unit: '°C', min: 1, max: 20, step: 0.5, inputWidth: '60px' })}
                                eltérésnél már <strong>100%-ban a pontosabb célpont</strong> a preferált.”
                            `}
                        </div>
                    ` : ''}
                </div>
                ` : ''}

                <!-- 3. BIZTONSÁG SZITUÁCIÓ -->
                ${isSafeActive ? `
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px; opacity: ${isSafeUnlocked ? '1.0' : '0.45'}; pointer-events: ${isSafeUnlocked ? 'auto' : 'none'}; filter: ${isSafeUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">3. Hogyan tekintesz a közbiztonságra?</div>
                        ${!isSafeUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">Válaszd ki az előző pontot a feloldáshoz</span>' : ''}
                    </div>

                    <div class="dna-scenario-grid" style="margin-bottom: ${isSafeChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_safety', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_safety === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_safety === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">A) Kisebb különbség még belefér</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Pár pont eltérés még nem döntő, de jelentős biztonsági különbségnél a biztonságosabb kell.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('dest_safety', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.dest_safety === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.dest_safety === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">B) Minden biztonsági pont számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Minden egyes pont biztonsági előny azonnal a biztonságosabb város felé billenti a mérleget.</div>
                        </div>
                    </div>
                    
                    ${isSafeChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.2; animation: fadeInScale 0.2s ease;">
                            ${cSafe.type === 5 ? `
                                „Legfeljebb 
                                ${wizard.renderNumericControl({ objName: 'dest_promethee', key: 'safety', param: 'q', value: cSafe.q, unit: 'pont', min: 0, max: 20, step: 1, inputWidth: '55px' })}
                                pont biztonsági eltérés még <strong>nem számít</strong> két úti cél között, de 
                                ${wizard.renderNumericControl({ objName: 'dest_promethee', key: 'safety', param: 'p', value: cSafe.p, unit: 'pont', min: 2, max: 40, step: 1, inputWidth: '55px' })}
                                pont felett már <strong>kifejezetten a biztonságosabb úti cél</strong> a preferált.”
                            ` : `
                                „Minden egyes pont biztonsági előny számít, és 
                                ${wizard.renderNumericControl({ objName: 'dest_promethee', key: 'safety', param: 'p', value: cSafe.p, unit: 'pont', min: 2, max: 40, step: 1, inputWidth: '55px' })}
                                pont különbségnél már <strong>100%-ban a biztonságosabb város</strong> a nyerő.”
                            `}
                        </div>
                    ` : ''}
                </div>
                ` : ''}
            `;
        }
    };

    window.DNADestStep = DNADestStep;
})();

