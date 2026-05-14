const mongoose = require('mongoose');
require('dotenv').config({ path: '.env.local' });

async function setInitialBalances() {
  await mongoose.connect(process.env.MONGODB_URI);
  
  const Account = mongoose.model('Account', new mongoose.Schema({ 
    name: String, 
    initialBalance: Number 
  }));

  const updates = [
    { name: 'Készpénz', bal: 869500 },
    { name: 'OTP számla', bal: 325521.18 },
    { name: 'PayPal', bal: 8737 },
    { name: 'Valuták (EUR)', bal: 14.81 },
    { name: 'Valuták (BGN)', bal: 4.30 },
    { name: 'Nexo', bal: -251.49 },
    { name: 'Államkincstár', bal: 1350000 },
    { name: 'Wise', bal: -10.86 },
    { name: 'Dapper wallet', bal: 521.22 }
  ];

  console.log('Starting initial balance updates...');

  for (let up of updates) {
    const res = await Account.updateOne(
      { name: up.name }, 
      { $set: { initialBalance: up.bal } }
    );
    console.log(`${up.name.padEnd(20)}: ${res.modifiedCount > 0 ? '✅ SUCCESS' : '⚠️ NO CHANGE / NOT FOUND'}`);
  }

  await mongoose.disconnect();
}

setInitialBalances();
