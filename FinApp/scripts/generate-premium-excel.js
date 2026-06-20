const ExcelJS = require('exceljs');

async function createPremiumExcel() {
  const workbook = new ExcelJS.Workbook();
  workbook.creator = 'FinSpace';
  workbook.lastModifiedBy = 'FinSpace';
  workbook.created = new Date();
  workbook.modified = new Date();

  // Color Palette
  const colors = {
    headerBg: 'FF1E293B', // Slate 800
    headerText: 'FFFFFFFF', // White
    autoCellBg: 'FFF1F5F9', // Slate 100 (automated cells)
    highlightBg: 'FF10B981', // Emerald 500
    highlightText: 'FFFFFFFF', // White
  };

  const numberFormat = '#,##0 "Ft"';

  // 1. SETTINGS SHEET
  const wsSettings = workbook.addWorksheet('Beállítások');
  wsSettings.columns = [
    { header: 'Kategóriák', key: 'categories', width: 20 },
    { header: 'Számlák', key: 'accounts', width: 20 },
    { header: 'Zsebek', key: 'pockets', width: 20 },
    { header: 'Típusok', key: 'types', width: 15 },
    { header: 'Igen/Nem', key: 'bools', width: 15 }
  ];

  // Apply header style
  wsSettings.getRow(1).font = { bold: true, color: { argb: colors.headerText } };
  wsSettings.getRow(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: colors.headerBg } };

  const settingsData = {
    categories: ['Fizetés', 'Ajándék', 'Étel-ital', 'Közlekedés', 'Egészség', 'Szórakozás', 'Utazás', 'Lakhatás', 'Egyéb', 'Befektetés'],
    accounts: ['OTP Készpénz', 'Revolut HUF', 'Revolut EUR', 'CIB Bank', 'Készpénz'],
    pockets: ['Utazás', 'Autó fenntartás', 'Vésztartalék', 'Technika', 'Ruházkodás', 'Befektetések'],
    types: ['Bevétel', 'Kiadás', 'Átvezetés'],
    bools: ['Igen', 'Nem']
  };

  const maxRows = Math.max(
    settingsData.categories.length,
    settingsData.accounts.length,
    settingsData.pockets.length,
    settingsData.types.length,
    settingsData.bools.length
  );

  for (let i = 0; i < maxRows; i++) {
    wsSettings.addRow({
      categories: settingsData.categories[i] || '',
      accounts: settingsData.accounts[i] || '',
      pockets: settingsData.pockets[i] || '',
      types: settingsData.types[i] || '',
      bools: settingsData.bools[i] || ''
    });
  }

  // Define named ranges for data validation
  // ExcelJS doesn't support named ranges directly across sheets for data validation in the exact way Google Sheets does,
  // but we will use the formula references like '"Beállítások"!$A$2:$A$20'

  // 2. TRANSACTIONS SHEET
  const wsTx = workbook.addWorksheet('Tranzakciók', { views: [{ state: 'frozen', ySplit: 1 }] });
  wsTx.columns = [
    { header: 'Dátum', key: 'date', width: 15 },
    { header: 'Típus', key: 'type', width: 15 },
    { header: 'Összeg', key: 'amount', width: 15 },
    { header: 'Kategória', key: 'category', width: 20 },
    { header: 'Számla', key: 'account', width: 20 },
    { header: 'Zseb', key: 'pocket', width: 20 },
    { header: 'Megjegyzés', key: 'note', width: 40 },
    { header: 'VitaSteps?', key: 'vitasteps', width: 15 }
  ];

  // Header style
  wsTx.getRow(1).font = { bold: true, color: { argb: colors.headerText } };
  wsTx.getRow(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: colors.headerBg } };
  wsTx.getRow(1).alignment = { horizontal: 'center' };

  // Add sample data
  wsTx.addRow(['2026-06-01', 'Bevétel', 500000, 'Fizetés', 'OTP Készpénz', '', 'Júniusi bér', 'Nem']);
  wsTx.addRow(['2026-06-02', 'Átvezetés', 50000, '', '', 'Vésztartalék', 'Pénz félretétele', 'Nem']);
  wsTx.addRow(['2026-06-05', 'Kiadás', 15000, 'Étel-ital', 'Revolut HUF', '', 'Heti bevásárlás', 'Nem']);
  wsTx.addRow(['2026-06-10', 'Bevétel', 120000, 'Egyéb', 'CIB Bank', '', 'Projekt díj', 'Igen']);
  wsTx.addRow(['2026-06-12', 'Kiadás', 20000, 'Utazás', 'Revolut HUF', 'Utazás', 'Repjegy', 'Nem']);

  // Format amount column
  wsTx.getColumn('amount').numFmt = numberFormat;

  // Add Data Validations for 1000 rows
  for (let i = 2; i <= 1000; i++) {
    wsTx.getCell(`B${i}`).dataValidation = {
      type: 'list', allowBlank: true, formulae: ['Beállítások!$D$2:$D$5']
    };
    wsTx.getCell(`D${i}`).dataValidation = {
      type: 'list', allowBlank: true, formulae: ['Beállítások!$A$2:$A$20']
    };
    wsTx.getCell(`E${i}`).dataValidation = {
      type: 'list', allowBlank: true, formulae: ['Beállítások!$B$2:$B$20']
    };
    wsTx.getCell(`F${i}`).dataValidation = {
      type: 'list', allowBlank: true, formulae: ['Beállítások!$C$2:$C$20']
    };
    wsTx.getCell(`H${i}`).dataValidation = {
      type: 'list', allowBlank: true, formulae: ['Beállítások!$E$2:$E$3']
    };

    // Alternating row colors (Zebra)
    if (i % 2 === 0) {
      wsTx.getRow(i).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF8FAFC' } }; // Slate 50
    }
  }


  // 3. DASHBOARD SHEET
  const wsDash = workbook.addWorksheet('Dashboard');
  wsDash.columns = [
    { width: 5 }, // padding
    { width: 30 }, // Mutató neve
    { width: 25 }, // Érték
  ];

  // Helper function to style sections
  function addSectionHeader(rowNum, title) {
    const row = wsDash.getRow(rowNum);
    row.getCell(2).value = title;
    row.getCell(2).font = { bold: true, size: 14, color: { argb: colors.headerText } };
    row.getCell(2).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: colors.headerBg } };
    row.getCell(3).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: colors.headerBg } };
  }

  function addDataRow(rowNum, title, formula, isHighlight = false) {
    const row = wsDash.getRow(rowNum);
    row.getCell(2).value = title;
    row.getCell(2).font = { bold: isHighlight, size: 12 };
    
    const valCell = row.getCell(3);
    valCell.value = { formula: formula };
    valCell.numFmt = numberFormat;
    
    // Auto cell marker style
    if (isHighlight) {
      valCell.font = { bold: true, color: { argb: colors.highlightText }, size: 12 };
      valCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: colors.highlightBg } };
    } else {
      valCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: colors.autoCellBg } };
    }

    // Border
    valCell.border = {
      top: { style: 'thin', color: { argb: 'FFE2E8F0' } },
      bottom: { style: 'thin', color: { argb: 'FFE2E8F0' } },
      left: { style: 'thin', color: { argb: 'FFE2E8F0' } },
      right: { style: 'thin', color: { argb: 'FFE2E8F0' } },
    };
  }

  // Build Dashboard
  addSectionHeader(2, '💰 FŐ MUTATÓK (🔒 Auto)');
  addDataRow(3, 'Összes Bevétel:', 'SUMIF(Tranzakciók!B:B, "Bevétel", Tranzakciók!C:C)');
  addDataRow(4, 'Összes Kiadás:', 'SUMIF(Tranzakciók!B:B, "Kiadás", Tranzakciók!C:C)');
  addDataRow(5, 'Teljes Vagyon:', 'C3 - C4', true);

  addSectionHeader(7, '🎯 VIRTUÁLIS ZSEBEK (🔒 Auto)');
  let currRow = 8;
  settingsData.pockets.forEach(pocket => {
    addDataRow(currRow, pocket + ':', `SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Átvezetés", Tranzakciók!F:F, "${pocket}") - SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Kiadás", Tranzakciók!F:F, "${pocket}")`);
    currRow++;
  });
  
  addDataRow(currRow, 'Zsebek Összesen:', `SUM(C8:C${currRow - 1})`);
  addDataRow(currRow + 1, 'Szabad Egyenleg:', `C5 - C${currRow}`, true);

  currRow += 3;
  addSectionHeader(currRow, '💼 VITASTEPS (🔒 Auto)');
  addDataRow(currRow + 1, 'Üzleti Bevétel:', 'SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Bevétel", Tranzakciók!H:H, "Igen")');
  addDataRow(currRow + 2, 'Üzleti Kiadás:', 'SUMIFS(Tranzakciók!C:C, Tranzakciók!B:B, "Kiadás", Tranzakciók!H:H, "Igen")');
  addDataRow(currRow + 3, 'Üzleti Profit:', `C${currRow + 1} - C${currRow + 2}`, true);

  // Save the workbook
  await workbook.xlsx.writeFile('Szemelyes_FinSpace_Premium.xlsx');
  console.log('Szemelyes_FinSpace_Premium.xlsx successfully generated!');
}

createPremiumExcel().catch(console.error);
