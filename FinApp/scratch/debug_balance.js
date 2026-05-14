const mongoose = require('mongoose');
require('dotenv').config({ path: '.env.local' });

async function debug() {
  await mongoose.connect(process.env.MONGODB_URI);
  console.log('Connected to MongoDB');

  const Transaction = mongoose.model('Transaction', new mongoose.Schema({
    amount: Number,
    type: String,
    currency: String,
    isBusinessTransaction: Boolean
  }));

  const Account = mongoose.model('Account', new mongoose.Schema({
    name: String,
    initialBalance: Number
  }));

  const count = await Transaction.countDocuments();
  console.log('Total Transactions:', count);

  const stats = await Transaction.aggregate([
    { $group: { _id: '$type', count: { $sum: 1 }, total: { $sum: '$amount' } } }
  ]);
  console.log('Stats by type:', JSON.stringify(stats, null, 2));

  const topTrans = await Transaction.find().sort({ amount: -1 }).limit(5);
  console.log('Top 5 highest amounts:', JSON.stringify(topTrans, null, 2));

  const accounts = await Account.find();
  console.log('Accounts initial balances:', JSON.stringify(accounts.map(a => ({ name: a.name, init: a.initialBalance })), null, 2));

  await mongoose.disconnect();
}

debug();
