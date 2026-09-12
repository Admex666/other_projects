/**
 * Optivoya — Trip Report & Proposal Export Module v3.0
 * High-end, print- and PDF-ready B2B Client Proposal & Trip Itinerary export.
 * Seamlessly integrates Unified TripScore, Effective Vacation Time, Experience Fit,
 * scheduled multi-day itinerary with transit guidance, and Numbeo cost breakdown.
 */

(function () {
    const TripReport = {
        exportProposal(trip, breakdown) {
            if (!trip) trip = window.TripStore ? window.TripStore.getTrip() : null;
            if (!breakdown) breakdown = window.TripCalculator ? window.TripCalculator.calculateBreakdown(trip) : null;
            if (!trip || !breakdown) return;

            const state = window.PlannerState;
            const d = trip.destination || state?.selectedDest;
            const f = trip.flight?.selected_flight || trip.flight || state?.selectedFlight;
            const s = trip.accommodation?.selected_accommodation || trip.accommodation || state?.selectedStay;

            // Harvest activities, itinerary and preferences
            const acts = trip.activities?.selected_activities?.length 
                ? trip.activities.selected_activities 
                : (state?.selectedActivities || []);
            const itinerary = trip.activities?.itinerary?.days?.length 
                ? trip.activities.itinerary 
                : (state?.currentItinerary?.days?.length ? state.currentItinerary : null);
            const expPrefs = trip.experience_preferences || state?.intake?.experience_preferences || {};
            const logPrefs = trip.logistics_preferences || state?.intake?.logistics_preferences || {};

            // Harvest or compute TripScore
            const scoreObj = trip.trip_score || {};
            const destScore = Math.round(scoreObj.dest_score || d?.score || 75);
            const flightScore = Math.round(scoreObj.flight_score || f?.relevance_pct || 78);
            const stayScore = Math.round(scoreObj.stay_score || Math.min(99, (s?.rating || 8.8) * 10));
            const actsCount = acts.length;
            const expScore = Math.round(scoreObj.exp_score || Math.min(98, 65 + (actsCount * 4)));
            const effHours = Math.round(scoreObj.effective_vacation_hours || f?.effective_vacation_hours || 16);
            
            const rawScore = (destScore * 0.25) + (flightScore * 0.25) + (stayScore * 0.25) + (expScore * 0.25);
            const tripScore = scoreObj.score || Math.round(Math.max(50, Math.min(99, rawScore)));

            let tripScoreTitle = scoreObj.title || "Kiváló Összhang & Kiegyensúlyozott Csomag";
            if (tripScore >= 88) tripScoreTitle = "Kiemelkedő Összhang & Prémium Illeszkedés";
            else if (tripScore < 78) tripScoreTitle = "Jó Ár-Érték Arányú Utazási Terv";

            // Category tag translation & display
            const categoryNames = {
                'food_gastronomy': '🍷 Gasztronómia & Bor',
                'culture_history': '🏛️ Kultúra & Művészet',
                'authenticity_vibes': '🏺 Autentikus Életérzés',
                'nature_outdoors': '🌿 Természet & Kilátás',
                'beach_coastal': '🌊 Tengerpart & Strand',
                'active_adventure': '⚡ Aktív Élmény'
            };

            const activeExpTags = Object.entries(expPrefs)
                .filter(([_, val]) => typeof val === 'number' && val >= 0.4)
                .map(([key, _]) => categoryNames[key] || key);

            const win = window.open('', '_blank');
            if (!win) {
                alert("Kérjük engedélyezd a felugró ablakokat az ajánlat megnyitásához!");
                return;
            }

            win.document.write(`
                <!DOCTYPE html>
                <html lang="hu">
                <head>
                    <meta charset="UTF-8">
                    <title>Utazási Tervezet & Ajánlat — ${d ? d.name : 'Optivoya'}</title>
                    <style>
                        * { box-sizing: border-box; }
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                            margin: 32px auto;
                            max-width: 860px;
                            color: #111827;
                            background: #ffffff;
                            line-height: 1.5;
                            padding: 0 20px;
                        }
                        .header {
                            border-bottom: 2px solid #111827;
                            padding-bottom: 16px;
                            margin-bottom: 24px;
                            display: flex;
                            justify-content: space-between;
                            align-items: flex-end;
                        }
                        .logo {
                            font-size: 22px;
                            font-weight: 900;
                            letter-spacing: 0.5px;
                            text-transform: uppercase;
                        }
                        .doc-meta {
                            font-size: 12px;
                            color: #4b5563;
                            text-align: right;
                        }
                        .section-title {
                            font-size: 13px;
                            font-weight: 800;
                            text-transform: uppercase;
                            letter-spacing: 0.6px;
                            border-bottom: 1.5px solid #111827;
                            padding-bottom: 5px;
                            margin: 28px 0 14px 0;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        }

                        /* 1. TripScore Banner */
                        .score-banner {
                            background: #0f172a;
                            color: #ffffff;
                            border-radius: 6px;
                            padding: 20px 24px;
                            margin-bottom: 24px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            gap: 20px;
                        }
                        .score-badge-wrap {
                            display: flex;
                            align-items: center;
                            gap: 16px;
                        }
                        .score-number {
                            font-size: 42px;
                            font-weight: 900;
                            line-height: 1;
                            color: #38bdf8;
                            font-family: 'Courier New', Courier, monospace;
                        }
                        .score-title {
                            font-size: 16px;
                            font-weight: 800;
                            color: #f8fafc;
                        }
                        .score-vacation-time {
                            display: inline-block;
                            margin-top: 4px;
                            font-size: 12.5px;
                            font-weight: 700;
                            color: #10b981;
                            background: rgba(16, 185, 129, 0.15);
                            padding: 2px 8px;
                            border-radius: 4px;
                        }
                        .score-pillars {
                            display: grid;
                            grid-template-columns: repeat(2, 1fr);
                            gap: 8px 16px;
                            font-size: 12px;
                            color: #cbd5e1;
                        }
                        .pillar-item strong {
                            color: #ffffff;
                        }

                        /* 2. Style & Logistics Bar */
                        .style-bar {
                            background: #f8fafc;
                            border: 1px solid #e2e8f0;
                            border-radius: 6px;
                            padding: 12px 16px;
                            margin-bottom: 22px;
                            font-size: 12px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            flex-wrap: wrap;
                            gap: 10px;
                        }
                        .tag-pill {
                            display: inline-block;
                            background: #e2e8f0;
                            color: #1e293b;
                            font-weight: 700;
                            font-size: 11px;
                            padding: 3px 8px;
                            border-radius: 4px;
                            margin-right: 4px;
                        }

                        /* 3. Summary Grid */
                        .grid-summary {
                            display: grid;
                            grid-template-columns: repeat(3, 1fr);
                            gap: 16px;
                            margin-bottom: 24px;
                        }
                        .summary-box {
                            border: 1px solid #d1d5db;
                            border-radius: 4px;
                            padding: 14px;
                            background: #ffffff;
                        }
                        .box-label {
                            font-size: 11px;
                            font-weight: 800;
                            text-transform: uppercase;
                            color: #6b7280;
                            margin-bottom: 4px;
                        }
                        .box-value {
                            font-size: 15px;
                            font-weight: 800;
                            color: #111827;
                            margin-bottom: 4px;
                        }
                        .box-desc {
                            font-size: 12px;
                            color: #4b5563;
                            line-height: 1.4;
                        }

                        /* 4. Multi-day Itinerary */
                        .itinerary-day {
                            border: 1px solid #e5e7eb;
                            border-radius: 6px;
                            margin-bottom: 16px;
                            background: #fafafa;
                            overflow: hidden;
                            page-break-inside: avoid;
                        }
                        .itinerary-day-header {
                            background: #f3f4f6;
                            padding: 10px 14px;
                            font-weight: 800;
                            font-size: 13px;
                            display: flex;
                            justify-content: space-between;
                            border-bottom: 1px solid #e5e7eb;
                        }
                        .itinerary-slot {
                            padding: 10px 14px;
                            border-bottom: 1px solid #f0f0f0;
                            display: flex;
                            gap: 16px;
                            font-size: 12.5px;
                            background: #ffffff;
                        }
                        .itinerary-slot:last-child {
                            border-bottom: none;
                        }
                        .slot-time {
                            width: 85px;
                            flex-shrink: 0;
                            font-weight: 700;
                            font-family: 'Courier New', Courier, monospace;
                            color: #4b5563;
                        }
                        .slot-content {
                            flex: 1;
                        }
                        .slot-title {
                            font-weight: 800;
                            color: #111827;
                        }
                        .slot-desc {
                            font-size: 11.5px;
                            color: #6b7280;
                            margin-top: 2px;
                        }
                        .transit-alert {
                            margin-top: 6px;
                            padding: 6px 10px;
                            background: #fffbeb;
                            border-left: 3px solid #f59e0b;
                            font-size: 11.5px;
                            color: #92400e;
                            border-radius: 0 4px 4px 0;
                        }

                        /* 5. Activities Table */
                        .act-table {
                            width: 100%;
                            border-collapse: collapse;
                            margin-bottom: 24px;
                            font-size: 12.5px;
                        }
                        .act-table th {
                            background: #f9fafb;
                            border-bottom: 1.5px solid #111827;
                            padding: 8px 10px;
                            text-align: left;
                            font-size: 11px;
                            font-weight: 800;
                            text-transform: uppercase;
                        }
                        .act-table td {
                            padding: 9px 10px;
                            border-bottom: 1px solid #e5e7eb;
                            vertical-align: top;
                        }

                        /* 6. Calc Table & Totals */
                        .calc-table {
                            width: 100%;
                            border-collapse: collapse;
                            margin-top: 10px;
                            page-break-inside: avoid;
                        }
                        .calc-table th {
                            font-size: 11px;
                            font-weight: 800;
                            text-transform: uppercase;
                            text-align: left;
                            border-bottom: 1.5px solid #111827;
                            padding: 8px 10px;
                            color: #111827;
                        }
                        .calc-table td {
                            padding: 10px;
                            border-bottom: 1px solid #e5e7eb;
                            font-size: 13px;
                            vertical-align: top;
                        }
                        .calc-table .num-col {
                            text-align: right;
                            font-variant-numeric: tabular-nums;
                            font-weight: 700;
                            white-space: nowrap;
                            font-family: 'Courier New', Courier, monospace;
                        }
                        .formula-text {
                            font-family: 'Courier New', Courier, monospace;
                            font-size: 11px;
                            color: #6b7280;
                            display: block;
                            margin-top: 2px;
                        }
                        .total-summary {
                            margin-top: 24px;
                            border-top: 2px solid #111827;
                            border-bottom: 2px solid #111827;
                            padding: 16px 10px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            page-break-inside: avoid;
                        }
                        .total-title {
                            font-size: 14px;
                            font-weight: 800;
                            text-transform: uppercase;
                            letter-spacing: 0.5px;
                        }
                        .total-value {
                            font-size: 24px;
                            font-weight: 900;
                            font-variant-numeric: tabular-nums;
                            font-family: 'Courier New', Courier, monospace;
                        }
                        .per-person-val {
                            font-size: 13px;
                            font-weight: 600;
                            color: #4b5563;
                            text-align: right;
                        }
                        .footer-note {
                            margin-top: 36px;
                            font-size: 11px;
                            color: #6b7280;
                            text-align: center;
                            border-top: 1px solid #e5e7eb;
                            padding-top: 14px;
                        }
                        .no-print-bar {
                            margin-bottom: 20px;
                            padding: 10px 14px;
                            background: #f3f4f6;
                            border: 1px solid #d1d5db;
                            border-radius: 4px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        }
                        .btn-print {
                            background: #111827;
                            color: #ffffff;
                            border: none;
                            border-radius: 4px;
                            padding: 8px 18px;
                            font-size: 13px;
                            font-weight: 700;
                            cursor: pointer;
                        }
                        @media print {
                            body { margin: 0; padding: 0; max-width: 100%; }
                            .no-print { display: none !important; }
                            @page { margin: 12mm; size: A4 portrait; }
                        }
                    </style>
                </head>
                <body>
                    <div class="no-print no-print-bar">
                        <span style="font-size: 13px; font-weight: 600;">Optivoya B2B Ajánlati és Utazási Tervezet (Nyomtatási & PDF előnézet)</span>
                        <button class="btn-print" onclick="window.print()">Nyomtatás / Mentés PDF-ként</button>
                    </div>

                    <div class="header">
                        <div>
                            <div class="logo">OPTIVOYA</div>
                            <div style="font-size: 12px; font-weight: 700; color: #4b5563; margin-top: 2px;">Prémium Utazási & Élmény Tervezet • Döntéstámogató Rendszer</div>
                        </div>
                        <div class="doc-meta">
                            <div><strong>Azonosító:</strong> ${trip.trip_id || 'TRIP-' + Math.random().toString(36).substring(2, 8).toUpperCase()}</div>
                            <div><strong>Készült:</strong> ${new Date().toLocaleDateString('hu-HU')}</div>
                            <div><strong>Utazók:</strong> ${breakdown.totalPersons} fő (${breakdown.days} nap / ${Math.max(1, breakdown.days - 1)} éjszaka)</div>
                        </div>
                    </div>

                    <!-- 1. UNIFIED TRIPSCORE & VALUE PROPOSITION BANNER -->
                    <div class="score-banner">
                        <div class="score-badge-wrap">
                            <div class="score-number">${tripScore}<span style="font-size: 20px; color: #94a3b8;">/100</span></div>
                            <div>
                                <div class="score-title">${tripScoreTitle}</div>
                                <div class="score-vacation-time">⚡ +${effHours} óra hasznos idő a helyszínen</div>
                            </div>
                        </div>
                        <div class="score-pillars">
                            <div class="pillar-item">📍 Desztináció: <strong>${destScore}p</strong></div>
                            <div class="pillar-item">✈️ Repülés & Idő: <strong>${flightScore}p</strong></div>
                            <div class="pillar-item">🏨 Szállás Érték: <strong>${stayScore}p</strong></div>
                            <div class="pillar-item">🎭 Élménydiverzitás: <strong>${expScore}p</strong></div>
                        </div>
                    </div>

                    <!-- 2. STÍLUS & LOGISZTIKAI PROFIL -->
                    ${(activeExpTags.length > 0 || logPrefs.day_start) ? `
                        <div class="style-bar">
                            <div>
                                <strong style="font-size: 11px; text-transform: uppercase; color: #64748b; margin-right: 8px;">Élményfókusz:</strong>
                                ${activeExpTags.length > 0 ? activeExpTags.map(t => `<span class="tag-pill">${t}</span>`).join('') : '<span style="color:#64748b;">Kiegyensúlyozott felfedezés</span>'}
                            </div>
                            <div style="color: #475569;">
                                ⏱️ <strong>Időkeret:</strong> ${logPrefs.day_start || '09:00'} – ${logPrefs.day_end || '22:00'} • <strong>Séta limit:</strong> max. ${logPrefs.max_walking_minutes || 20} perc
                            </div>
                        </div>
                    ` : ''}

                    <!-- 3. FŐBB UTAS- & SZOLGÁLTATÁSI ADATOK -->
                    <div class="grid-summary">
                        <div class="summary-box">
                            <div class="box-label">1. Célállomás</div>
                            <div class="box-value">${d ? d.name + (d.country ? ', ' + d.country : '') : 'Nincs megadva'}</div>
                            <div class="box-desc">
                                Indulás: ${trip.input?.origin || 'Budapest'} • ${breakdown.days} nap (${breakdown.totalPersons} fő)<br>
                                Nappali hőm.: ~${d?.temp_avg || d?.metrics?.temp_avg || 24}°C • Biztonság: ${Math.round(d?.safety_score || d?.numbeo?.safety_index || 60)}/100
                            </div>
                        </div>
                        <div class="summary-box">
                            <div class="box-label">2. Repülőjárat</div>
                            <div class="box-value">${f ? (f.airline || f.out_airline || 'Járat') + ' Retúr' : 'Irányár'}</div>
                            <div class="box-desc">
                                ${f && (f.out_date || f.out_dep_time) ? `${(f.out_date || f.out_dep_time).split('T')[0]} – ${(f.in_date || f.in_dep_time).split('T')[0]}` : 'Menetrend szerint'}<br>
                                ${f?.out_stops === 0 ? 'Közvetlen járat' : (f?.out_stops ? `${f.out_stops} átszállás` : 'Optimális útvonal')} • Hasznos idő: +${effHours} óra
                            </div>
                        </div>
                        <div class="summary-box">
                            <div class="box-label">3. Szálláshely</div>
                            <div class="box-value">${s ? s.name : 'Irányár'}</div>
                            <div class="box-desc">
                                ${s ? `${s.nights || breakdown.days} éjszaka ${s.stars ? `(${s.stars} csillag)` : ''} • Értékelés: ${s.rating || 8.8}/10` : `${breakdown.days} éjszaka`}<br>
                                ${s?.address ? s.address : (d?.name ? `${d.name} központja` : 'Központi elhelyezkedés')}
                            </div>
                        </div>
                    </div>

                    <!-- 4. NAPI ÉLMÉNY ÚTITERV & SÉTAÚTVONALAK -->
                    ${itinerary && itinerary.days && itinerary.days.length > 0 ? `
                        <div class="section-title">
                            <span>Napi Élmény Útiterv & Menetrend</span>
                            <span style="font-size: 11px; font-weight: 600; color: #6b7280; text-transform: none;">Logisztikai kerethez és nyitvatartásokhoz igazítva</span>
                        </div>
                        ${itinerary.days.map((day, dIdx) => `
                            <div class="itinerary-day">
                                <div class="itinerary-day-header">
                                    <span>${dIdx + 1}. NAP ${day.date ? `(${day.date})` : ''}</span>
                                    <span style="color: #6b7280; font-weight: 600;">${day.slots ? day.slots.length : 0} tervezett élmény</span>
                                </div>
                                ${(day.slots || []).map(slot => {
                                    const slotLabels = {
                                        'morning': 'Délelőtt',
                                        'lunch': 'Ebédszünet',
                                        'afternoon': 'Délután',
                                        'sunset': 'Naplemente',
                                        'dinner_evening': 'Esti program'
                                    };
                                    const slotName = slotLabels[slot.slot] || slot.slot || 'Program';
                                    return `
                                        <div class="itinerary-slot">
                                            <div class="slot-time">
                                                <div>${slot.time_window || ''}</div>
                                                <div style="font-size: 11px; font-weight: normal; color: #6b7280;">${slotName}</div>
                                            </div>
                                            <div class="slot-content">
                                                <div class="slot-title">${slot.name} ${slot.duration_min ? `<span style="font-weight: normal; color: #6b7280; font-size: 11px;">(~${slot.duration_min} perc)</span>` : ''}</div>
                                                ${slot.description ? `<div class="slot-desc">${slot.description}</div>` : ''}
                                                ${slot.distance_from_prev_m ? `<div style="font-size: 11px; color: #6b7280; margin-top: 2px;">🚶 Séta az előző ponttól: ~${Math.round(slot.distance_from_prev_m)} méter (~${Math.round(slot.walk_time_from_prev_min || slot.distance_from_prev_m / 80)} perc)</div>` : ''}
                                                ${slot.transit_recommendation ? `
                                                    <div class="transit-alert">
                                                        🚗 <strong>Tranzit javaslat:</strong> ${slot.transit_recommendation}
                                                    </div>
                                                ` : ''}
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        `).join('')}
                    ` : ''}

                    <!-- 5. KIVÁLASZTOTT FŐBB ÉLMÉNYEK PORTFÓLIÓJA -->
                    ${acts && acts.length > 0 ? `
                        <div class="section-title">
                            <span>Kiválasztott Élmények & Személyes Ajánlások</span>
                            <span style="font-size: 11px; font-weight: 600; color: #6b7280; text-transform: none;">${acts.length} kiválasztott tétel</span>
                        </div>
                        <table class="act-table">
                            <thead>
                                <tr>
                                    <th style="width: 35%;">Élmény Neve</th>
                                    <th style="width: 25%;">Kategória</th>
                                    <th style="width: 40%;">Személyes Illeszkedés / Indoklás</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${acts.map(a => `
                                    <tr>
                                        <td>
                                            <strong>${a.name}</strong>
                                            ${a.duration_min ? `<div style="font-size: 11px; color: #6b7280;">~${a.duration_min} perc</div>` : ''}
                                        </td>
                                        <td>
                                            <span class="tag-pill">${a.category ? a.category.replace(/_/g, ' ') : 'látnivaló'}</span>
                                        </td>
                                        <td>
                                            ${a.fit_score ? `<strong style="color: #0284c7;">${Math.round(a.fit_score * 100)}% illeszkedés</strong> — ` : ''}
                                            ${a.recommendation_reason || a.description || 'Kiemelt helyi élmény'}
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    ` : ''}

                    <!-- 6. TÉTELES KÖLTSÉGKALKULÁCIÓ -->
                    <div class="section-title">Tételes Matematikai Költségvetés</div>
                    <table class="calc-table">
                        <thead>
                            <tr>
                                <th style="width: 35%;">Költségtétel</th>
                                <th style="width: 45%;">Számítási Alap</th>
                                <th style="width: 20%;" class="num-col">Összeg</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${breakdown.items.map(it => `
                                <tr>
                                    <td>
                                        <strong>${it.name}</strong>
                                        ${it.desc ? `<div style="font-size: 11.5px; color: #4b5563; margin-top: 2px;">${it.desc}</div>` : ''}
                                    </td>
                                    <td>
                                        <span class="formula-text">${it.formula}</span>
                                    </td>
                                    <td class="num-col">${it.amount.toLocaleString()} Ft</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>

                    <!-- 7. ÖSSZESÍTŐ -->
                    <div class="total-summary">
                        <div>
                            <div class="total-title">Becsült Teljes Utazási Költség</div>
                            <div style="font-size: 12px; color: #4b5563;">Tartalmazza a repülőjegy, szállás, étkezési profil és helyi közlekedés tételeit</div>
                        </div>
                        <div style="text-align: right;">
                            <div class="total-value">${breakdown.totalHuf.toLocaleString()} Ft</div>
                            ${breakdown.totalPersons > 1 ? `<div class="per-person-val">~${breakdown.perPersonTotal.toLocaleString()} Ft / fő (${breakdown.totalPersons} utazóra összesen)</div>` : ''}
                        </div>
                    </div>

                    <div class="footer-note">
                        Ez a hivatalos ügyfélajánlat az Optivoya döntéstámogató motorjával készült. Az árak az adatforrások (Kiwi.com GraphQL, Cozycozy, Numbeo) aktuális adatai alapján becsült összegek. A dokumentum PDF formátumban menthető vagy közvetlenül nyomtatható.
                    </div>
                </body>
                </html>
            `);
            win.document.close();
        }
    };

    window.TripReport = TripReport;
})();

