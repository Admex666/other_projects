const mongoose = require('mongoose');
require('dotenv').config({ path: '.env.local' });

async function checkFinal() {
  await mongoose.connect(process.env.MONGODB_URI);
  
  const Transaction = mongoose.model('Transaction', new mongoose.Schema({
    amount: Number,
    type: String,
    accountId: mongoose.Schema.Types.ObjectId,
    toAccountId: mongoose.Schema.Types.ObjectId
  }));
  
  const Account = mongoose.model('Account', new mongoose.Schema({
    name: String,
    currency: String,
    initialBalance: Number
  }));

  const accounts = await Account.find();
  let totalHUF = 0;

  console.log('--- Account Balances ---');
  for (let acc of accounts) {
    const bal = await Transaction.aggregate([
      { $match: { accountId: acc._id, type: { $in: ['income', 'expense'] } } },
      { $group: { _id: null, total: { $sum: { $cond: [{ $eq: ['$type', 'income'] }, '$amount', { $subtract: [0, '$amount'] }] } } } }
    ]);

    const out = await Transaction.aggregate([
      { $match: { accountId: acc._id, type: 'transfer' } },
      { $group: { _id: null, total: { $sum: '$amount' } } }
    ]);

    const inc = await Transaction.aggregate([
      { $match: { toAccountId: acc._id, type: 'transfer' } },
      { $group: { _id: null, total: { $sum: '$amount' } } }
    ]);

    const balance = (acc.initialBalance || 0) + (bal[0]?.total || 0) - (out[0]?.total || 0) + (inc[0]?.total || 0);
    console.log(`${acc.name.padEnd(20)}: ${balance.toLocaleString().padStart(12)} ${acc.currency}`);
    
    if (acc.currency === 'HUF') totalHUF += balance;
  }
  
  console.log('------------------------');
  console.log(`Total HUF (approx):    ${totalHUF.toLocaleString().padStart(12)} HUF`);

  await mongoose.disconnect();
}

checkFinal();
