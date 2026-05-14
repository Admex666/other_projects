const mongoose = require('mongoose');
const xlsx = require('xlsx');
require('dotenv').config({ path: '.env.local' });

const TIMI_ID = '6a05be56b0610b91df873031';

// Schemas
const AccountSchema = new mongoose.Schema({
  userId: mongoose.Schema.Types.ObjectId,
  name: String,
  currency: String,
  balance: Number,
  color: String,
  isBusinessAccount: Boolean
});

const CategorySchema = new mongoose.Schema({
  userId: mongoose.Schema.Types.ObjectId,
  name: String,
  type: String,
  icon: String,
  color: String
});

const TransactionSchema = new mongoose.Schema({
  userId: mongoose.Schema.Types.ObjectId,
  accountId: mongoose.Schema.Types.ObjectId,
  categoryId: mongoose.Schema.Types.ObjectId,
  amount: Number,
  currency: String,
  type: String,
  date: Date,
  note: String,
  isBusinessTransaction: Boolean,
  toAccountId: mongoose.Schema.Types.ObjectId // For transfers
});

const Account = mongoose.models.Account || mongoose.model('Account', AccountSchema);
const Category = mongoose.models.Category || mongoose.model('Category', CategorySchema);
const Transaction = mongoose.models.Transaction || mongoose.model('Transaction', TransactionSchema);

async function importData() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('Adatbázis csatlakozva.');

    const workbook = xlsx.readFile('2026_05_14_18_27_51_514537.xlsx');
    
    const accountsCache = {};
    const categoriesCache = {};

    async function getOrCreateAccount(name, currency = 'HUF') {
      const key = `${name}-${currency}`;
      if (accountsCache[key]) return accountsCache[key];

      let acc = await Account.findOne({ userId: TIMI_ID, name, currency });
      if (!acc) {
        acc = await Account.create({
          userId: TIMI_ID,
          name,
          currency,
          balance: 0,
          color: '#' + Math.floor(Math.random()*16777215).toString(16),
          isBusinessAccount: false
        });
        console.log(`Új számla létrehozva: ${name}`);
      }
      accountsCache[key] = acc._id;
      return acc._id;
    }

    async function getOrCreateCategory(name, type) {
      const key = `${name}-${type}`;
      if (categoriesCache[key]) return categoriesCache[key];

      let cat = await Category.findOne({ userId: TIMI_ID, name, type });
      if (!cat) {
        cat = await Category.create({
          userId: TIMI_ID,
          name,
          type,
          icon: type === 'expense' ? '💸' : '💰',
          color: type === 'expense' ? '#FF4D4D' : '#4DFF4D'
        });
        console.log(`Új kategória létrehozva: ${name} (${type})`);
      }
      categoriesCache[key] = cat._id;
      return cat._id;
    }

    function excelDateToJS(excelDate) {
      if (!excelDate || isNaN(excelDate)) return new Date();
      return new Date(Math.round((excelDate - 25569) * 86400 * 1000));
    }

    // 1. Kiadások
    console.log('Kiadások feldolgozása...');
    const expenseData = xlsx.utils.sheet_to_json(workbook.Sheets['Kiadások'], { header: 1 });
    const expenses = [];
    for (let i = 1; i < expenseData.length; i++) {
      const row = expenseData[i];
      if (!row[0]) continue;

      const date = excelDateToJS(row[0]);
      const categoryName = row[1] || 'Egyéb';
      const accountName = row[2] || 'Készpénz';
      const amount = parseFloat(row[3]) || 0;
      const currency = row[4] || 'HUF';
      const note = row[10] || '';

      const accountId = await getOrCreateAccount(accountName, currency);
      const categoryId = await getOrCreateCategory(categoryName, 'expense');

      expenses.push({
        userId: TIMI_ID,
        accountId,
        categoryId,
        amount,
        currency,
        type: 'expense',
        date,
        note,
        isBusinessTransaction: false
      });
    }
    if (expenses.length > 0) await Transaction.insertMany(expenses);
    console.log(`${expenses.length} kiadás importálva.`);

    // 2. Bevételek
    console.log('Bevételek feldolgozása...');
    const incomeData = xlsx.utils.sheet_to_json(workbook.Sheets['Bevétel'], { header: 1 });
    const incomes = [];
    for (let i = 1; i < incomeData.length; i++) {
      const row = incomeData[i];
      if (!row[0]) continue;

      const date = excelDateToJS(row[0]);
      const categoryName = row[1] || 'Fizetés';
      const accountName = row[2] || 'Bank';
      const amount = parseFloat(row[3]) || 0;
      const currency = row[4] || 'HUF';
      const note = row[10] || '';

      const accountId = await getOrCreateAccount(accountName, currency);
      const categoryId = await getOrCreateCategory(categoryName, 'income');

      incomes.push({
        userId: TIMI_ID,
        accountId,
        categoryId,
        amount,
        currency,
        type: 'income',
        date,
        note,
        isBusinessTransaction: false
      });
    }
    if (incomes.length > 0) await Transaction.insertMany(incomes);
    console.log(`${incomes.length} bevétel importálva.`);

    // 3. Átutalások
    console.log('Átutalások feldolgozása...');
    const transferData = xlsx.utils.sheet_to_json(workbook.Sheets['Átutalás'], { header: 1 });
    const transfers = [];
    for (let i = 1; i < transferData.length; i++) {
      const row = transferData[i];
      if (!row[0]) continue;

      const date = excelDateToJS(row[0]);
      const fromAccountName = row[1];
      const toAccountName = row[3];
      const amount = parseFloat(row[4]) || 0;
      const currency = row[5] || 'HUF';
      const note = row[8] || '';

      const accountId = await getOrCreateAccount(fromAccountName, currency);
      const toAccountId = await getOrCreateAccount(toAccountName, currency);

      transfers.push({
        userId: TIMI_ID,
        accountId,
        toAccountId,
        amount,
        currency,
        type: 'transfer',
        date,
        note,
        isBusinessTransaction: false
      });
    }
    if (transfers.length > 0) await Transaction.insertMany(transfers);
    console.log(`${transfers.length} átutalás importálva.`);

    console.log('ADATOK SIKERESEN IMPORTÁLVA!');
    process.exit(0);
  } catch (err) {
    console.error('Hiba az importálás során:', err);
    process.exit(1);
  }
}

importData();
