/**
 * Optivoya — Decision DNA Flight Steps Module
 * Step 2: Flight Pairwise Matrix (Price, Duration, Stops)
 * Step 3: Flight Scenarios (Price, Duration, Stops A/B + statements)
 */

(function () {
    const DNAFlightStep = {
        renderFlightAHP(wizard, container) {
            const pairs = [
                { id: 'price_vs_duration', c1: 'price', c2: 'duration', name1: 'Repjegy Ár', name2: 'Menetidő (Időtartam)', desc: 'Olcsóbb repjegy vagy lényegesen rövidebb utazási idő?' },
                { id: 'price_vs_stops', c1: 'price', c2: 'stops', name1: 'Repjegy Ár', name2: 'Közvetlen Járat (0 átszállás)', desc: 'Spórolás egy átszállással vagy ragaszkodás a közvetlen járathoz?' },
                { id: 'duration_vs_stops', c1: 'duration', c2: 'stops', name1: 'Menetidő', name2: 'Átszállások Száma', desc: 'Rövidebb menetidő vagy kényelmes, átszállásmentes út?' }
            ];
            const criteriaList = [
                { key: 'price', label: '💰 Repjegy Ár' },
                { key: 'duration', label: '⏱️ Menetidő' },
                { key: 'stops', label: '🔄 Átszállások Száma' }
            ];
            wizard.renderPairwiseMatrix(container, '3. Lépés: Repülőjárat Súlyozás (Páros Összehasonlítás)', 'Válaszd ki a releváns szempontokat, majd határozd meg az arányokat:', pairs, 'flight_ahp', 'flight', criteriaList);
        },

        renderFlightScenarios(wizard, container) {
            const state = wizard.state;
            const priceCfg = state.flight_promethee.price;
            const durCfg = state.flight_promethee.duration;
            const pPriceQ = priceCfg.q.toLocaleString() + ' Ft';
            const pPriceP = priceCfg.p.toLocaleString() + ' Ft';
            const pDurQ = durCfg.q < 1 ? `${Math.round(durCfg.q * 60)} perc` : `${durCfg.q} óra`;
            const pDurP = `${durCfg.p} óra`;

            const active = state.active_criteria?.flight || ['price', 'duration', 'stops'];
            const isPriceActive = active.includes('price');
            const isDurActive = active.includes('duration');
            const isStopsActive = active.includes('stops');

            const isPriceChosen = state.chosen_cards.flight_price !== null;
            const isDurUnlocked = state.unlocked.flight_dur || (!isPriceActive || isPriceChosen);
            const isDurChosen = state.chosen_cards.flight_dur !== null;
            const isStopsUnlocked = state.unlocked.flight_stops || (isDurUnlocked && (!isDurActive || isDurChosen));
            const isStopsChosen = state.chosen_cards.flight_stops !== null;

            container.innerHTML = `
                <div style="margin-bottom: 18px;">
                    <h4 style="margin: 0 0 4px 0; font-size: 16.5px; font-weight: 800; color: var(--text-main);">4. Lépés: Járat Döntési Helyzetek</h4>
                    <p style="margin: 0; font-size: 12.5px; color: var(--text-muted);">A kiválasztott releváns járat-szempontoknál finomhangold a döntési szabályokat:</p>
                </div>

                <!-- 1. REPJEGY ÁR SZITUÁCIÓ -->
                ${isPriceActive ? `
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px;">
                    <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 10px;">
                        1. Hogyan gondolkodsz a repjegyárakról két járat között?
                    </div>
                    
                    <div class="dna-scenario-grid" style="margin-bottom: ${isPriceChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_price', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.flight_price === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.flight_price === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">A) Pár ezer Ft még nem döntő</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy minimális árkülönbség még nem számít, de nagyobb összegnél már egyértelműen az olcsóbb kell.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_price', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.flight_price === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.flight_price === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">B) A legelső forint árelőny is számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Már a legkisebb árelőny is azonnal az olcsóbb járat felé billenti a mérleget.</div>
                        </div>
                    </div>

                    ${isPriceChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.2; animation: fadeInScale 0.2s ease;">
                            ${priceCfg.type === 5 ? `
                                „Legfeljebb 
                                ${wizard.renderNumericControl({ objName: 'flight_promethee', key: 'price', param: 'q', value: priceCfg.q, unit: 'Ft', min: 0, max: 40000, step: 1000, inputWidth: '75px' })}
                                árkülönbség még <strong>nem számít</strong> nekem két járat között, de utána minden forint számít, egészen 
                                ${wizard.renderNumericControl({ objName: 'flight_promethee', key: 'price', param: 'p', value: priceCfg.p, unit: 'Ft', min: 5000, max: 150000, step: 2500, inputWidth: '85px' })}
                                különbségig, ahonnan már <strong>egyértelműen az olcsóbb járat</strong> a nyerő.”
                            ` : `
                                „Már a legkisebb árelőny is számít, és 
                                ${wizard.renderNumericControl({ objName: 'flight_promethee', key: 'price', param: 'p', value: priceCfg.p, unit: 'Ft', min: 5000, max: 150000, step: 2500, inputWidth: '85px' })}
                                árkülönbségnél már <strong>100%-ban az olcsóbb járat</strong> dominál.”
                            `}
                        </div>
                    ` : ''}
                </div>
                ` : ''}

                <!-- 2. MENETIDŐ SZITUÁCIÓ -->
                ${isDurActive ? `
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px; opacity: ${isDurUnlocked ? '1.0' : '0.45'}; pointer-events: ${isDurUnlocked ? 'auto' : 'none'}; filter: ${isDurUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">2. Hogyan viszonyulsz a plusz utazási időhöz?</div>
                        ${!isDurUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">Válaszd ki az előző pontot a feloldáshoz</span>' : ''}
                    </div>
                    
                    <div class="dna-scenario-grid" style="margin-bottom: ${isDurChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_dur', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.flight_dur === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.flight_dur === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">A) Egy kis plusz idő még belefér</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy fél óra vagy 1 óra többlet még rendben van, de több órával hosszabb utat már nem szívesen vállalok be.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_dur', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.flight_dur === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.flight_dur === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">B) Minden plusz perc számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Minden egyes felesleges utazási perc ront az élményen már a legelsőtől.</div>
                        </div>
                    </div>

                    ${isDurChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.2; animation: fadeInScale 0.2s ease;">
                            ${durCfg.type === 5 ? `
                                „Legfeljebb 
                                ${wizard.renderNumericControl({ objName: 'flight_promethee', key: 'duration', param: 'q', value: durCfg.q, unit: 'óra', min: 0, max: 4, step: 0.25, inputWidth: '60px' })}
                                plusz menetidő még <strong>belefér nekem</strong>, de 
                                ${wizard.renderNumericControl({ objName: 'flight_promethee', key: 'duration', param: 'p', value: durCfg.p, unit: 'óra', min: 0.5, max: 10, step: 0.5, inputWidth: '60px' })}
                                plusz menetidőnél már <strong>100%-ban a gyorsabb járat</strong> a jobb.”
                            ` : `
                                „Minden perc számít, és 
                                ${wizard.renderNumericControl({ objName: 'flight_promethee', key: 'duration', param: 'p', value: durCfg.p, unit: 'óra', min: 0.5, max: 10, step: 0.5, inputWidth: '60px' })}
                                menetidő-többletnél már <strong>100%-ban a gyorsabb járat</strong> a nyerő.”
                            `}
                        </div>
                    ` : ''}
                </div>
                ` : ''}

                <!-- 3. ÁTSZÁLLÁSOK SZITUÁCIÓ -->
                ${isStopsActive ? `
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; opacity: ${isStopsUnlocked ? '1.0' : '0.45'}; pointer-events: ${isStopsUnlocked ? 'auto' : 'none'}; filter: ${isStopsUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">3. Hogyan viszonyulsz az átszálláshoz?</div>
                        ${!isStopsUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">Válaszd ki az előző pontot a feloldáshoz</span>' : ''}
                    </div>

                    <div class="dna-scenario-grid" style="margin-bottom: ${isStopsChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_stops', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.flight_stops === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.flight_stops === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">A) Bevállalok átszállást spórolásért</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Ha jelentősen olcsóbb, szívesen utazom 1 átszállással is.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('flight_stops', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.flight_stops === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.flight_stops === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">B) Ragaszkodom a közvetlen járathoz</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Csak a közvetlen (0 átszállásos) kényelmes járatok jöhetnek szóba.</div>
                        </div>
                    </div>

                    ${isStopsChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.2; animation: fadeInScale 0.2s ease;">
                            ${state.chosen_cards.flight_stops === 'A' ? `
                                „Szívesen bevállalok <strong>1 kényelmes átszállást</strong>, amennyiben legalább 
                                ${wizard.renderNumericControl({ objName: 'flight_promethee', key: 'stops_saving_needed', param: null, value: state.flight_promethee.stops_saving_needed, unit: 'Ft', min: 5000, max: 80000, step: 2500, inputWidth: '85px' })}
                                megtakarítást jelent a közvetlen repjegyhez képest.”
                            ` : `
                                „Kizárólag <strong>közvetlen, átszállásmentes járatokat</strong> keresek; átszállásos opciót csak akkor mutasson a rendszer, ha egyáltalán nincs közvetlen járat.”
                            `}
                        </div>
                    ` : ''}
                </div>
                ` : ''}
            `;
        }
    };

    window.DNAFlightStep = DNAFlightStep;
})();
