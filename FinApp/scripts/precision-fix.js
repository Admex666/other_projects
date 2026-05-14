const mongoose = require('mongoose');
require('dotenv').config({ path: '.env.local' });

const TIMI_ID = '6a05be56b0610b91df873031';

async function precisionFix() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    
    const Account = mongoose.models.Account || mongoose.model('Account', new mongoose.Schema({
      userId: mongoose.Schema.Types.ObjectId,
      name: String,
      currency: String,
      balance: Number
    }));

    const Transaction = mongoose.models.Transaction || mongoose.model('Transaction', new mongoose.Schema({
      userId: mongoose.Schema.Types.ObjectId,
      accountId: mongoose.Schema.Types.ObjectId,
      amount: Number,
      currency: String,
      type: String,
      note: String
    }));

    async function adjustToTarget(name, targetAmount, currency = 'HUF') {
      const acc = await Account.findOne({ userId: TIMI_ID, name, currency });
      if (!acc) return;

      // Töröljük a korábbi korrekciókat
      await Transaction.deleteMany({ accountId: acc._id, note: 'Nyitó egyenleg' });

      // Megnézzük mennyi az egyenleg az importált tranzakciókkal
      const txs = await Transaction.find({ accountId: acc._id });
      const currentSum = txs.reduce((sum, tx) => {
        if (tx.type === 'income') return sum + tx.amount;
        if (tx.type === 'expense') return sum - tx.amount;
        return sum;
      }, 0);

      // Akkora nyitót adunk hozzá, hogy a sum + opening = targetAmount legyen
      const openingNeeded = targetAmount - currentSum;

      await Transaction.create({
        userId: TIMI_ID,
        accountId: acc._id,
        amount: openingNeeded,
        currency: currency,
        type: 'income',
        note: 'Nyitó egyenleg'
      });

      console.log(`${name} korrigálva. Szükséges nyitó: ${openingNeeded} ${currency}. Új egyenleg: ${targetAmount}`);
    }

    await adjustToTarget('Bank', 1700000);
    await adjustToTarget('Készpénz', 916000);
    await adjustToTarget('Euró', 120, 'EUR');
    await adjustToTarget('Állampapír', 500000);
    await adjustToTarget('Lakás kaució', 350000);

    process.exit(0);
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
}

precisionFix();
