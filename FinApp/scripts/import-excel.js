const xlsx = require('xlsx');
const mongoose = require('mongoose');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config({ path: path.join(__dirname, '..', '.env.local') });

const UserSchema = new mongoose.Schema({ email: String });
const AccountSchema = new mongoose.Schema({
  userId: mongoose.Schema.Types.ObjectId,
  name: String,
  currency: String,
  isBusinessAccount: Boolean
});
const CategorySchema = new mongoose.Schema({
  userId: mongoose.Schema.Types.ObjectId,
  name: String,
  type: String
});
const TransactionSchema = new mongoose.Schema({
  userId: mongoose.Schema.Types.ObjectId,
  type: String,
  date: Date,
  amount: Number,
  currency: String,
  accountId: mongoose.Schema.Types.ObjectId,
  toAccountId: mongoose.Schema.Types.ObjectId,
  categoryId: mongoose.Schema.Types.ObjectId,
  note: String,
  isBusinessTransaction: Boolean,
  importedFrom: String
});

const User = mongoose.models.User || mongoose.model('User', UserSchema);
const Account = mongoose.models.Account || mongoose.model('Account', AccountSchema);
const Category = mongoose.models.Category || mongoose.model('Category', CategorySchema);
const Transaction = mongoose.models.Transaction || mongoose.model('Transaction', TransactionSchema);

async function importExcel() {
  const uri = process.env.MONGODB_URI;
  await mongoose.connect(uri);
  console.log('Connected to MongoDB');

  const admin = await User.findOne({ email: 'admin@admin.com' });
  if (!admin) {
    console.error('Admin user not found! Run create-admin.js first.');
    process.exit(1);
  }

  const filePath = 'C:\\Users\\Adam\\Downloads\\2026_05_11_16_44_30_225888.xlsx';
  const workbook = xlsx.readFile(filePath);

  const getOrCreateAccount = async (name, currency = 'HUF') => {
    let acc = await Account.findOne({ userId: admin._id, name });
    if (!acc) {
      acc = await Account.create({
        userId: admin._id,
        name,
        currency,
        isBusinessAccount: name === 'Revolut Pro'
      });
      console.log(`Created account: ${name}`);
    }
    return acc;
  };

  const getOrCreateCategory = async (name, type) => {
    let cat = await Category.findOne({ userId: admin._id, name, type });
    if (!cat) {
      cat = await Category.create({ userId: admin._id, name, type });
      console.log(`Created category: ${name} (${type})`);
    }
    return cat;
  };

  // 1. Kiadások
  const kiadasSheet = workbook.Sheets['Kiad\u00E1sok'];
  const kiadasData = xlsx.utils.sheet_to_json(kiadasSheet, { range: 1 });
  console.log(`Importing ${kiadasData.length} expenses...`);

  for (const row of kiadasData) {
    const accountName = row['Sz\u00E1mla'];
    const categoryName = row['Kateg\u00F3ria'];
    const amount = row['\u00D6sszeg a sz\u00E1mla p\u00E9nznem\u00E9ben'];
    const currency = row['Sz\u00E1mla p\u00E9nzneme'];
    const dateStr = row['D\u00E1tum \u00E9s id\u0151'];
    const note = row['Megjegyz\u00E9s'];

    if (!amount || !accountName) continue;

    const account = await getOrCreateAccount(accountName, currency);
    const category = await getOrCreateCategory(categoryName, 'expense');

    await Transaction.create({
      userId: admin._id,
      type: 'expense',
      date: new Date(dateStr),
      amount: Math.abs(amount),
      currency: currency || 'HUF',
      accountId: account._id,
      categoryId: category._id,
      note: note || '',
      isBusinessTransaction: account.isBusinessAccount || categoryName === 'VitaSteps',
      importedFrom: 'xlsx'
    });
  }

  // 2. Bevételek
  const bevetelSheet = workbook.Sheets['Bev\u00E9tel'];
  const bevetelData = xlsx.utils.sheet_to_json(bevetelSheet, { range: 1 });
  console.log(`Importing ${bevetelData.length} incomes...`);

  for (const row of bevetelData) {
    const accountName = row['Sz\u00E1mla'];
    const categoryName = row['Kateg\u00F3ria'];
    const amount = row['\u00D6sszeg a sz\u00E1mla p\u00E9nznem\u00E9ben'];
    const currency = row['Sz\u00E1mla p\u00E9nzneme'];
    const dateStr = row['D\u00E1tum \u00E9s id\u0151'];
    const note = row['Megjegyz\u00E9s'];

    if (!amount || !accountName) continue;

    const account = await getOrCreateAccount(accountName, currency);
    const category = await getOrCreateCategory(categoryName, 'income');

    await Transaction.create({
      userId: admin._id,
      type: 'income',
      date: new Date(dateStr),
      amount: Math.abs(amount),
      currency: currency || 'HUF',
      accountId: account._id,
      categoryId: category._id,
      note: note || '',
      isBusinessTransaction: account.isBusinessAccount,
      importedFrom: 'xlsx'
    });
  }

  // 3. Átutalások
  const atutalasSheet = workbook.Sheets['\u00C1tutal\u00E1s'];
  const atutalasData = xlsx.utils.sheet_to_json(atutalasSheet, { range: 1 });
  console.log(`Importing ${atutalasData.length} transfers...`);

  for (const row of atutalasData) {
    const fromName = row['Kimen\u0151'];
    const toName = row['Be\u00E9rkez\u0151'];
    const amountFrom = row['\u00D6sszeg kimen\u0151 p\u00E9nznemben'];
    const currencyFrom = row['Kimen\u0151 p\u00E9nznem'];
    const dateStr = row['D\u00E1tum \u00E9s id\u0151'];
    const note = row['Megjegyz\u00E9s'];

    if (!amountFrom || !fromName || !toName) continue;

    const fromAccount = await getOrCreateAccount(fromName, currencyFrom);
    const toAccount = await getOrCreateAccount(toName); // currency might vary

    await Transaction.create({
      userId: admin._id,
      type: 'transfer',
      date: new Date(dateStr),
      amount: Math.abs(amountFrom),
      currency: currencyFrom || 'HUF',
      accountId: fromAccount._id,
      toAccountId: toAccount._id,
      note: note || '',
      isBusinessTransaction: fromAccount.isBusinessAccount || toAccount.isBusinessAccount,
      importedFrom: 'xlsx'
    });
  }

  console.log('Import finished successfully!');
  process.exit(0);
}

importExcel().catch(err => {
  console.error(err);
  process.exit(1);
});
