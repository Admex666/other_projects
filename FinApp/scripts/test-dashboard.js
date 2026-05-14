const mongoose = require('mongoose');
require('dotenv').config({ path: '.env.local' });

const TIMI_ID = '6a05be56b0610b91df873031';

async function test() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    
    const ExchangeRate = mongoose.model('ExchangeRate', new mongoose.Schema({ date: String, rates: Object }));
    const Account = mongoose.model('Account', new mongoose.Schema({ userId: mongoose.Schema.Types.ObjectId, name: String, currency: String }));
    const Transaction = mongoose.model('Transaction', new mongoose.Schema({ userId: mongoose.Schema.Types.ObjectId, accountId: mongoose.Schema.Types.ObjectId, amount: Number, currency: String, type: String }));

    const rateDoc = await ExchangeRate.findOne().sort({ date: -1 });
    const rates = rateDoc.rates;
    console.log('Használt HUF árfolyam:', rates['HUF']);

    const accounts = await Account.find({ userId: new mongoose.Types.ObjectId(TIMI_ID) });
    let totalHuf = 0;

    for (const acc of accounts) {
      const txs = await Transaction.find({ accountId: acc._id });
      let bal = 0;
      for (const tx of txs) {
        if (tx.type === 'income') bal += tx.amount;
        else if (tx.type === 'expense') bal -= tx.amount;
      }

      // Manuális konverzió a lib helyett
      let inBase = bal;
      if (acc.currency !== 'HUF') {
        const fromRate = rates[acc.currency] || (acc.currency === 'EUR' ? 1.0 : null);
        const toRate = rates['HUF'];
        const inEur = acc.currency === 'EUR' ? bal : bal / fromRate;
        inBase = inEur * toRate;
      }

      console.log(`${acc.name}: ${bal} ${acc.currency} -> ${Math.round(inBase)} HUF`);
      totalHuf += inBase;
    }

    console.log('---');
    console.log('Kiszámolt főösszeg:', Math.round(totalHuf), 'HUF');
    process.exit(0);
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
}

test();
