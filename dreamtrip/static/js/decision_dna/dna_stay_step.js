/**
 * Optivoya — Decision DNA Stay Steps Module
 * Step 4: Stay Pairwise Matrix (Price, Rating, Location, Amenities)
 * Step 5: Stay Scenarios (Price, Rating, Location A/B, Stars & Rating filters)
 */

(function () {
    const DNAStayStep = {
        renderStayAHP(wizard, container) {
            const pairs = [
                { id: 'price_vs_rating', name1: '💳 Ár / Éjszaka', name2: '⭐ Vendégértékelés (Minőség)', desc: 'Kedvezőbb ár vagy magasabb vendégértékelés?' },
                { id: 'price_vs_location', name1: '💳 Ár / Éjszaka', name2: '📍 Központi Elhelyezkedés', desc: 'Olcsóbb külvárosibb szállás vagy sétálóutcás belváros?' },
                { id: 'price_vs_amenities', name1: '💳 Ár / Éjszaka', name2: '☕ Reggeli & Wellness', desc: 'Alacsonyabb szobaár vagy gazdag reggeli és wellness szolgáltatások?' },
                { id: 'rating_vs_location', name1: '⭐ Vendégértékelés', name2: '📍 Központi Elhelyezkedés', desc: 'Kiváló 9.0+ értékelés vagy köpésnyire lévő belváros?' },
                { id: 'rating_vs_amenities', name1: '⭐ Vendégértékelés', name2: '☕ Reggeli & Wellness', desc: 'Magas minőségi pontszám vagy extra ellátási csomag?' },
                { id: 'location_vs_amenities', name1: '📍 Központi Elhelyezkedés', name2: '☕ Reggeli & Wellness', desc: 'Központi lokáció vagy kényelmi felszereltség a fontosabb?' }
            ];
            wizard.renderPairwiseMatrix(container, '🏨 5. Lépés: Szállás Súlyozás (Páros Döntés)', 'Melyik szempont mennyire fontosabb számodra a szállások rangsorolásakor?', pairs, 'stay_ahp');
        },

        renderStayScenarios(wizard, container) {
            const state = wizard.state;
            const sPrice = state.stay_promethee.price;
            const sRating = state.stay_promethee.rating;
            const filters = state.stay_filters;

            const isPriceChosen = state.chosen_cards.stay_price !== null;
            const isRatingUnlocked = state.unlocked.stay_rating || isPriceChosen;
            const isRatingChosen = state.chosen_cards.stay_rating !== null;
            const isLocUnlocked = state.unlocked.stay_filters || isRatingChosen;

            container.innerHTML = `
                <div style="margin-bottom: 18px;">
                    <h4 style="margin: 0 0 4px 0; font-size: 16.5px; font-weight: 800; color: var(--text-main);">🏨 6. Lépés: Szállás Döntési Helyzetek & Kategóriák</h4>
                    <p style="margin: 0; font-size: 12.5px; color: var(--text-muted);">Válaszd ki a szállás döntési szabályait (Ár, Értékelés, Elhelyezkedés):</p>
                </div>

                <!-- 1. SZÁLLÁS ÁR SZITUÁCIÓ -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px;">
                    <div style="font-size: 13px; font-weight: 800; color: var(--text-main); margin-bottom: 10px;">
                        💳 1. Hogyan viszonyulsz az éjszakánkénti szobaárhoz?
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: ${isPriceChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_price', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.stay_price === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.stay_price === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Pár ezer Ft még nem számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Pár ezer forint éjszakánként még nem oszt, nem szoroz, de nagyobb összegnél már az olcsóbb nyer.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_price', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.stay_price === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.stay_price === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Minden forint árelőny számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Már a legkisebb éjszakánkénti árelőny is azonnal előnyt jelent.</div>
                        </div>
                    </div>

                    ${isPriceChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${sPrice.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sPrice.q.toLocaleString()} Ft / éj</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                különbség még <strong>nem számít</strong> két szálloda között, de 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sPrice.p.toLocaleString()} Ft / éj</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                felett már <strong>kifejezetten az olcsóbb opció</strong> a nyerő.”
                            ` : `
                                „Minden forint árelőny azonnal számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sPrice.p.toLocaleString()} Ft / éj</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'price', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                árkülönbségnél már <strong>100%-ban az olcsóbb szállás</strong> a preferált.”
                            `}
                        </div>
                    ` : ''}
                </div>

                <!-- 2. VENDÉGÉRTÉKELÉS SZITUÁCIÓ -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; margin-bottom: 16px; opacity: ${isRatingUnlocked ? '1.0' : '0.45'}; pointer-events: ${isRatingUnlocked ? 'auto' : 'none'}; filter: ${isRatingUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">⭐ 2. Hogyan viszonyulsz a vendégértékeléshez?</div>
                        ${!isRatingUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">🔒 Válaszd ki az 1. pontot a feloldáshoz</span>' : ''}
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: ${isRatingChosen ? '12px' : '0'};">
                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_rating', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.stay_rating === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.stay_rating === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Kisebb tizedes különbség még belefér</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Egy minimális pontkülönbség még nem számít, de nagyobb minőségi ugrásnál a magasabb értékelésű nyer.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_rating', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.stay_rating === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.stay_rating === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Minden tized pont azonnal számít</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Minden tized pont előny azonnal a magasabbra értékelt hotel felé billenti a mérleget.</div>
                        </div>
                    </div>
                    
                    ${isRatingChosen ? `
                        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 14px 18px; border-radius: 14px; font-size: 13.5px; line-height: 2.1; animation: fadeInScale 0.2s ease;">
                            ${sRating.type === 5 ? `
                                „Legfeljebb 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'q', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sRating.q} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'q', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                értékelésbeli különbség még <strong>elhanyagolható</strong>, de 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sRating.p} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                előny már <strong>egyértelmű minőségi fölényt</strong> jelent.”
                            ` : `
                                „Minden tized pont előny számít, és 
                                <span style="display: inline-flex; align-items: center; gap: 3px; background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; border-radius: 6px; padding: 1px 6px;">
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'p', -1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">−</button>
                                    <strong style="color:#38bdf8; font-family:var(--font-mono);">${sRating.p} pont</strong>
                                    <button type="button" onclick="window.DecisionDNAInstance.stepValue(window.DecisionDNAInstance.state.stay_promethee, 'rating', 'p', 1)" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:900;">+</button>
                                </span>
                                pontelőnynél már <strong>100%-ban a magasabbra értékelt opció</strong> a preferált.”
                            `}
                        </div>
                    ` : ''}
                </div>

                <!-- 3. ELHELYEZKEDÉS & SZŰRŐK SZITUÁCIÓ -->
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 18px; padding: 18px; opacity: ${isLocUnlocked ? '1.0' : '0.45'}; pointer-events: ${isLocUnlocked ? 'auto' : 'none'}; filter: ${isLocUnlocked ? 'none' : 'grayscale(30%)'}; transition: all 0.3s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-size: 13px; font-weight: 800; color: var(--text-main);">📍 3. Elhelyezkedési és kategória preferenciák</div>
                        ${!isLocUnlocked ? '<span style="font-size: 11px; font-weight: 700; color: var(--text-muted);">🔒 Válaszd ki a 2. pontot a feloldáshoz</span>' : ''}
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px;">
                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_loc', 'A', 5)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.stay_loc === 'A' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.stay_loc === 'A' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🟢 A) Rugalmas lokáció</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Nem feltétel a közvetlen belváros, ha jó a közlekedés vagy kedvezőbb az ár.</div>
                        </div>

                        <div onclick="window.DecisionDNAInstance.selectScenario('stay_loc', 'B', 3)" style="cursor: pointer; padding: 12px; border-radius: 12px; border: 2px solid ${state.chosen_cards.stay_loc === 'B' ? 'var(--primary)' : 'var(--border-subtle)'}; background: ${state.chosen_cards.stay_loc === 'B' ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-card)'};">
                            <div style="font-weight: 800; font-size: 12px; color: var(--primary); margin-bottom: 4px;">🔵 B) Szigorúan központi lokáció</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Kifejezetten sétálótávolságra lévő, frekventált vagy belvárosi szállást keresek.</div>
                        </div>
                    </div>

                    <!-- Minőségi Kategória & Slider -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div style="background: var(--bg-card); padding: 12px; border-radius: 12px; border: 1px solid var(--border-subtle);">
                            <label class="form-label" style="font-weight: 700; margin-bottom: 6px; display: block; font-size: 11.5px;">Minimális Csillag:</label>
                            <select onchange="window.DecisionDNAInstance.state.stay_filters.hotel_min_stars = parseInt(this.value, 10)" class="form-control" style="width: 100%; padding: 8px; border-radius: 8px; background: var(--bg-surface); font-weight: 700;">
                                <option value="0" ${filters.hotel_min_stars === 0 ? 'selected' : ''}>Bármilyen kategória</option>
                                <option value="3" ${filters.hotel_min_stars === 3 ? 'selected' : ''}>3★ vagy jobb</option>
                                <option value="4" ${filters.hotel_min_stars === 4 ? 'selected' : ''}>4★ vagy jobb</option>
                                <option value="5" ${filters.hotel_min_stars === 5 ? 'selected' : ''}>5★ (Luxus)</option>
                            </select>
                        </div>

                        <div style="background: var(--bg-card); padding: 12px; border-radius: 12px; border: 1px solid var(--border-subtle);">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                                <label class="form-label" style="font-weight: 700; margin: 0; font-size: 11.5px;">Min. Vendégértékelés:</label>
                                <strong id="dnaRatingDisp" style="color: var(--primary); font-family: var(--font-mono); font-size: 12.5px;">${filters.hotel_min_rating}+</strong>
                            </div>
                            <input type="range" min="0" max="9.5" step="0.5" value="${filters.hotel_min_rating}" style="width: 100%;" oninput="window.DecisionDNAInstance.state.stay_filters.hotel_min_rating = parseFloat(this.value); document.getElementById('dnaRatingDisp').innerText = this.value + '+';">
                        </div>
                    </div>
                </div>
            `;
        }
    };

    window.DNAStayStep = DNAStayStep;
})();
