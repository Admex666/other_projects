/**
 * Optivoya — Trip Report & Proposal Export Module
 * Minimalist, plain black-and-white HTML & Print/PDF report generation.
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
                    <title>Utazási Tervezet — ${d ? d.name : 'Optivoya'}</title>
                    <style>
                        * { box-sizing: border-box; }
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                            margin: 36px auto;
                            max-width: 820px;
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
                            font-size: 20px;
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
                            letter-spacing: 0.5px;
                            border-bottom: 1px solid #111827;
                            padding-bottom: 4px;
                            margin: 24px 0 12px 0;
                        }
                        .grid-summary {
                            display: grid;
                            grid-template-columns: repeat(3, 1fr);
                            gap: 16px;
                            margin-bottom: 20px;
                        }
                        .summary-box {
                            border: 1px solid #d1d5db;
                            padding: 12px 14px;
                        }
                        .box-label {
                            font-size: 11px;
                            font-weight: 700;
                            text-transform: uppercase;
                            color: #4b5563;
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
                        }
                        .calc-table {
                            width: 100%;
                            border-collapse: collapse;
                            margin-top: 10px;
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
                        }
                        .formula-text {
                            font-family: 'Courier New', Courier, monospace;
                            font-size: 11.5px;
                            color: #4b5563;
                            display: block;
                            margin-top: 2px;
                        }
                        .total-summary {
                            margin-top: 28px;
                            border-top: 2px solid #111827;
                            border-bottom: 2px solid #111827;
                            padding: 16px 10px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
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
                            padding-top: 12px;
                        }
                        .no-print-bar {
                            margin-bottom: 20px;
                            padding: 10px 14px;
                            background: #f3f4f6;
                            border: 1px solid #d1d5db;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        }
                        .btn-print {
                            background: #111827;
                            color: #ffffff;
                            border: none;
                            padding: 8px 18px;
                            font-size: 13px;
                            font-weight: 700;
                            cursor: pointer;
                        }
                        @media print {
                            body { margin: 0; padding: 0; max-width: 100%; }
                            .no-print { display: none !important; }
                            @page { margin: 15mm; size: A4 portrait; }
                        }
                    </style>
                </head>
                <body>
                    <div class="no-print no-print-bar">
                        <span style="font-size: 13px; font-weight: 600;">Nyomtatási és PDF előnézet (fekete-fehér)</span>
                        <button class="btn-print" onclick="window.print()">Nyomtatás / Mentés PDF-ként</button>
                    </div>

                    <div class="header">
                        <div>
                            <div class="logo">OPTIVOYA</div>
                            <div style="font-size: 12px; font-weight: 600; margin-top: 2px;">Utazási és Költségtervezet</div>
                        </div>
                        <div class="doc-meta">
                            <div><strong>Azonosító:</strong> ${trip.trip_id || 'TRIP-' + Math.random().toString(36).substring(2, 8).toUpperCase()}</div>
                            <div><strong>Készült:</strong> ${new Date().toLocaleDateString('hu-HU')}</div>
                        </div>
                    </div>

                    <!-- 1. FŐBB ADATOK -->
                    <div class="grid-summary">
                        <div class="summary-box">
                            <div class="box-label">1. Célállomás</div>
                            <div class="box-value">${d ? d.name + (d.country ? ', ' + d.country : '') : 'Nincs megadva'}</div>
                            <div class="box-desc">Indulás: ${trip.input?.origin || 'Budapest'} • ${breakdown.days} nap (${breakdown.totalPersons} fő)</div>
                        </div>
                        <div class="summary-box">
                            <div class="box-label">2. Repülőjegy</div>
                            <div class="box-value">${f ? f.airline + ' Retúr' : 'Irányár'}</div>
                            <div class="box-desc">${f && f.out_date ? `${f.out_date.split('T')[0]} – ${f.in_date.split('T')[0]}` : 'Menetrend szerint'}</div>
                        </div>
                        <div class="summary-box">
                            <div class="box-label">3. Szállás</div>
                            <div class="box-value">${s ? s.name : 'Irányár'}</div>
                            <div class="box-desc">${s ? `${s.nights} éjszaka ${s.stars ? `(${s.stars} csillag)` : ''}` : `${breakdown.days} éjszaka`}</div>
                        </div>
                    </div>

                    <!-- 2. TÉTELES KÖLTSÉGKALKULÁCIÓ -->
                    <div class="section-title">Tételes Költségvetés</div>
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

                    <!-- 3. ÖSSZESÍTŐ -->
                    <div class="total-summary">
                        <div>
                            <div class="total-title">Becsült Teljes Utazási Költség</div>
                            <div style="font-size: 12px; color: #4b5563;">Tartalmazza az utazás, szállás, étkezés és helyi közlekedés tételeit</div>
                        </div>
                        <div style="text-align: right;">
                            <div class="total-value">${breakdown.totalHuf.toLocaleString()} Ft</div>
                            ${breakdown.totalPersons > 1 ? `<div class="per-person-val">~${breakdown.perPersonTotal.toLocaleString()} Ft / fő (${breakdown.totalPersons} utazóra)</div>` : ''}
                        </div>
                    </div>

                    <div class="footer-note">
                        Ez a dokumentum az Optivoya döntéstámogató rendszerével készült. Az árak az adatforrások aktuális adatai alapján becsült tájékoztató összegek.
                    </div>
                </body>
                </html>
            `);
            win.document.close();
        }
    };

    window.TripReport = TripReport;
})();
