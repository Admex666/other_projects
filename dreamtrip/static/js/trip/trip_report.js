/**
 * Optivoya — Trip Report & Proposal Export Module
 * Clean HTML & Print/PDF report generation for clients and travel advisors.
 */

(function () {
    const TripReport = {
        exportProposal(trip, breakdown) {
            if (!trip) trip = window.TripStore ? window.TripStore.getTrip() : null;
            if (!breakdown) breakdown = window.TripCalculator ? window.TripCalculator.calculateBreakdown(trip) : null;
            if (!trip || !breakdown) return;

            const d = trip.destination;
            const f = trip.flight?.selected_flight;
            const s = trip.accommodation?.selected_accommodation;

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
                    <title>Optivoya Utazási Ajánlat — ${d ? d.name : 'Tervezet'}</title>
                    <style>
                        body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; margin: 40px; color: #1e293b; background: #fff; line-height: 1.5; }
                        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 30px; }
                        .logo { font-size: 24px; font-weight: 900; color: #0284c7; letter-spacing: -0.5px; }
                        .card { border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; background: #f8fafc; }
                        .card-title { font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
                        .card-val { font-size: 20px; font-weight: 800; color: #0284c7; }
                        .total-box { margin-top: 30px; padding: 24px; background: #0f172a; color: #fff; border-radius: 16px; display: flex; justify-content: space-between; align-items: center; }
                        .total-label { font-size: 14px; text-transform: uppercase; font-weight: 700; color: #94a3b8; }
                        .total-num { font-size: 32px; font-weight: 900; color: #38bdf8; }
                        .per-person-text { font-size: 15px; color: #cbd5e1; font-weight: 600; text-align: right; }
                        .calc-table { width: 100%; border-collapse: collapse; margin-top: 16px; background: #fff; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }
                        .calc-table th, .calc-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #f1f5f9; font-size: 13.5px; }
                        .calc-table th { background: #f8fafc; font-weight: 700; color: #475569; }
                        .formula-text { font-family: monospace; font-size: 12px; color: #0284c7; background: #f0f9ff; padding: 3px 8px; border-radius: 6px; }
                        @media print { .no-print { display: none; } body { margin: 20px; } }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div>
                            <div class="logo">✦ OPTIVOYA TRAVEL INTELLIGENCE</div>
                            <div style="color: #64748b; font-size: 13px; margin-top: 4px;">Hivatalos Utazási Ajánlat & Költségvetés</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: 700; font-size: 14px;">Azonosító: ${trip.trip_id}</div>
                            <div style="color: #64748b; font-size: 12px;">Dátum: ${new Date().toLocaleDateString('hu-HU')}</div>
                            <button class="no-print" onclick="window.print()" style="margin-top: 8px; padding: 6px 14px; background: #0284c7; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Nyomtatás / PDF mentés</button>
                        </div>
                    </div>

                    ${d ? `
                    <div class="card">
                        <div class="card-title">📍 Célállomás</div>
                        <div class="card-val">${d.name}, ${d.country}</div>
                        <div>Indulás: ${trip.input.origin} • ${breakdown.days} napos időszak (${breakdown.totalPersons} fő)</div>
                        ${d.explanation ? `<div style="margin-top: 6px; font-size: 12px; color: #64748b;">${d.explanation}</div>` : ''}
                    </div>` : ''}

                    ${f ? `
                    <div class="card">
                        <div class="card-title">✈️ Repülőjegy & Menetrend</div>
                        <div class="card-val">${f.airline} Retúr Járat</div>
                        <div>${f.out_date ? `Odaút: ${f.out_date}` : ''} ${f.in_date ? `• Visszaút: ${f.in_date}` : ''} (${f.adults} főre)</div>
                        <div style="margin-top: 8px; font-weight: 700; color: #0284c7;">${Math.round(f.price_total_huf || f.price_huf).toLocaleString()} Ft</div>
                    </div>` : ''}

                    ${s ? `
                    <div class="card">
                        <div class="card-title">🏨 Szállás</div>
                        <div class="card-val">${s.name} ${s.stars ? '⭐'.repeat(s.stars) : ''}</div>
                        <div>${s.nights} éjszaka ${s.rating ? `• Értékelés: ${s.rating}/10` : ''}</div>
                        <div style="margin-top: 8px; font-weight: 700; color: #0284c7;">${Math.round(s.price_total_huf || s.price_huf).toLocaleString()} Ft</div>
                    </div>` : ''}

                    <!-- DETAILED BREAKDOWN TABLE -->
                    <h3 style="margin-top: 28px; margin-bottom: 8px; font-size: 16px; color: #0f172a;">📊 Részletes Matematikai Költségkalkuláció (Numbeo + Valós Árak)</h3>
                    <table class="calc-table">
                        <thead>
                            <tr>
                                <th>Költségtétel</th>
                                <th>Számítási Képlet</th>
                                <th style="text-align: right;">Összeg</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${breakdown.items.map(it => `
                                <tr>
                                    <td><strong>${it.icon} ${it.name}</strong><br><small style="color: #64748b;">${it.desc}</small></td>
                                    <td><span class="formula-text">${it.formula}</span></td>
                                    <td style="text-align: right; font-weight: 800; font-family: monospace;">${it.amount.toLocaleString()} Ft</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>

                    <div class="total-box">
                        <div class="total-label">Becsült teljes utazási költség:</div>
                        <div>
                            <div class="total-num">${breakdown.totalHuf.toLocaleString()} Ft</div>
                            ${breakdown.totalPersons > 1 ? `<div class="per-person-text">~${breakdown.perPersonTotal.toLocaleString()} Ft / fő</div>` : ''}
                        </div>
                    </div>
                </body>
                </html>
            `);
            win.document.close();
        }
    };

    window.TripReport = TripReport;
})();
