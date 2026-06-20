const XLSX = require('xlsx');

// 1. Create a new workbook
const wb = XLSX.utils.book_new();

// 2. Settings Sheet
const settingsData = [
  ['Kategóriák', 'Számlák', 'Zsebek'],
  ['Fizetés', 'OTP Készpénz', 'Utazás'],
  ['Ajándék', 'Revolut HUF', 'Autó fenntartás'],
  ['Étel-ital', 'Revolut EUR', 'Vésztartalék'],
  ['Közlekedés', 'CIB Bank', 'Technika'],
  ['Egészség', 'Készpénz', 'Ruházkodás'],
  ['Szórakozás', '', 'Befektetések'],
  ['Utazás', '', ''],
  ['Lakhatás', '', ''],
  ['Egyéb', '', ''],
];
const wsSettings = XLSX.utils.aoa_to_sheet(settingsData);
XLSX.utils.book_append_sheet(wb, wsSettings, "Beállítások");

// 3. Transactions Sheet
const txData = [
  ['Dátum', 'Típus', 'Összeg', 'Kategória', 'Számla', 'Zseb', 'Megjegyzés', 'VitaSteps?'],
  // Sample data to show how it works
  ['2026-06-01', 'Bevétel', 500000, 'Fizetés', 'OTP Készpénz', '', 'Júniusi bér', 'Nem'],
  ['2026-06-02', 'Átvezetés', 50000, '', '', 'Vésztartalék', 'Pénz félretétele', 'Nem'],
  ['2026-06-05', 'Kiadás', 15000, 'Étel-ital', 'Revolut HUF', '', 'Heti bevásárlás', 'Nem'],
  ['2026-06-10', 'Bevétel', 120000, 'Egyéb', 'CIB Bank', '', 'Projekt díj', 'Igen'],
  ['2026-06-12', 'Kiadás', 20000, 'Utazás', 'Revolut HUF', 'Utazás', 'Repjegy', 'Nem'],
];
const wsTx = XLSX.utils.aoa_to_sheet(txData);
// Adjust column widths for better readability
wsTx['!cols'] = [
  {wch: 12}, // Dátum
  {wch: 12}, // Típus
  {wch: 12}, // Összeg
  {wch: 15}, // Kategória
  {wch: 15}, // Számla
  {wch: 15}, // Zseb
  {wch: 30}, // Megjegyzés
  {wch: 12}, // VitaSteps?
];
XLSX.utils.book_append_sheet(wb, wsTx, "Tranzakciók");

// 4. Dashboard Sheet
// Using formulas pointing to the Transactions sheet
const dashboardData = [
  ['💰 FŐ MUTATÓK', ''],
  ['Összes Bevétel:', { t: 'n', f: 'SUMIF(Tranzakciók!B:B, "Bevétel", Tranzakciók!C:C)' }],
  ['Összes Kiadás:', { t: 'n', f: 'SUMIF(Tranzakciók!B:B, "Kiadás", Tranzakciók!C:C)' }],
  ['Teljes Vagyon:', { t: 'n', f: 'B2 - B3' }],
  ['', ''],
  ['🎯 VIRTUÁLIS ZSEBEK', 'Egyenleg'],
  ['Utazás', { t: 'n', f: 'SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Átvezetés", Tranzakciók!F:F, A7) - SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Kiadás", Tranzakciók!F:F, A7)' }],
  ['Autó fenntartás', { t: 'n', f: 'SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Átvezetés", Tranzakciók!F:F, A8) - SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Kiadás", Tranzakciók!F:F, A8)' }],
  ['Vésztartalék', { t: 'n', f: 'SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Átvezetés", Tranzakciók!F:F, A9) - SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Kiadás", Tranzakciók!F:F, A9)' }],
  ['Technika', { t: 'n', f: 'SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Átvezetés", Tranzakciók!F:F, A10) - SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Kiadás", Tranzakciók!F:F, A10)' }],
  ['Ruházkodás', { t: 'n', f: 'SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Átvezetés", Tranzakciók!F:F, A11) - SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Kiadás", Tranzakciók!F:F, A11)' }],
  ['Befektetések', { t: 'n', f: 'SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Átvezetés", Tranzakciók!F:F, A12) - SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Kiadás", Tranzakciók!F:F, A12)' }],
  ['Zsebek Összesen:', { t: 'n', f: 'SUM(B7:B12)' }],
  ['Szabad Egyenleg:', { t: 'n', f: 'B4 - B13' }], // Teljes vagyon - zsebekben lévő pénz
  ['', ''],
  ['💼 VITASTEPS (ÜZLETI)', ''],
  ['Üzleti Bevétel:', { t: 'n', f: 'SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Bevétel", Tranzakciók!H:H, "Igen")' }],
  ['Üzleti Kiadás:', { t: 'n', f: 'SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Kiadás", Tranzakciók!H:H, "Igen")' }],
  ['Üzleti Profit:', { t: 'n', f: 'B17 - B18' }],
];
const wsDash = XLSX.utils.aoa_to_sheet(dashboardData);
wsDash['!cols'] = [
  {wch: 25}, // Col A
  {wch: 20}, // Col B
];
XLSX.utils.book_append_sheet(wb, wsDash, "Dashboard");

// 5. Save the file
XLSX.writeFile(wb, "Szemelyes_FinSpace.xlsx");

console.log("Szemelyes_FinSpace.xlsx successfully generated!");
