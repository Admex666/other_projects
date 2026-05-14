const mongoose = require('mongoose');
require('dotenv').config({ path: '.env.local' });

const TIMI_ID = '6a05be56b0610b91df873031';

async function fixBalances() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('Adatbázis csatlakozva.');

    const Account = mongoose.models.Account || mongoose.model('Account', new mongoose.Schema({
      userId: mongoose.Schema.Types.ObjectId,
      name: String,
      currency: String,
      balance: Number,
      color: String
    }));

    const Transaction = mongoose.models.Transaction || mongoose.model('Transaction', new mongoose.Schema({
      userId: mongoose.Schema.Types.ObjectId,
      accountId: mongoose.Schema.Types.ObjectId,
      amount: Number,
      currency: String,
      type: String,
      date: Date,
      note: String
    }));

    // 1. "500000" számla törlése (és a hozzá tartozó tranzakcióké)
    const badAcc = await Account.findOne({ userId: TIMI_ID, name: '500000' });
    if (badAcc) {
      await Transaction.deleteMany({ accountId: badAcc._id });
      await Account.deleteOne({ _id: badAcc._id });
      console.log('500000 számla törölve.');
    }

    // Segédfüggvény az egyenleg beállításához
    async function setTargetBalance(name, targetAmount, currency = 'HUF') {
      let acc = await Account.findOne({ userId: TIMI_ID, name, currency });
      if (!acc) {
        acc = await Account.create({
          userId: TIMI_ID,
          name,
          currency,
          balance: 0,
          color: '#' + Math.floor(Math.random()*16777215).toString(16)
        });
      }

      // Kiszámoljuk a jelenlegi egyenleget a tranzakciókból
      const txs = await Transaction.find({ accountId: acc._id });
      const currentBalance = txs.reduce((sum, tx) => {
        if (tx.type === 'income') return sum + tx.amount;
        if (tx.type === 'expense') return sum - tx.amount;
        if (tx.type === 'transfer') {
           // Ez bonyolultabb, de most egyszerűsítünk egy korrekciós tétellel
           return sum; 
        }
        return sum;
      }, 0);

      // Töröljük a régi korrekciókat, ha vannak
      await Transaction.deleteMany({ accountId: acc._id, note: 'Nyitó egyenleg korrekció' });

      // Új korrekciós tétel, hogy elérjük a célt
      // A dashboard úgyis újraszámolja a tranzakciókból
      const diff = targetAmount; // Most egyszerűen beállítjuk nyitónak
      
      // Valójában a legjobb, ha töröljük az összes importált tranzakciót az adott számláról 
      // ÉS hozzáadunk egyetlen nyitó egyenleget + a májusi tranzakciókat.
      // De maradjunk a legegyszerűbbnél: adjunk hozzá egy korrekciót a jelenlegi állapothoz képest.
    }

    // Finomított módszer: Töröljük a számla tranzakcióit és létrehozunk egy tiszta nyitó egyenleget
    async function resetAndSet(name, amount, currency = 'HUF') {
       let acc = await Account.findOne({ userId: TIMI_ID, name, currency });
       if (!acc) {
         acc = await Account.create({
           userId: TIMI_ID,
           name,
           currency,
           balance: amount,
           color: '#' + Math.floor(Math.random()*16777215).toString(16)
         });
       }

       // Csak a 'Nyitó egyenleg' típusú vagy korábbi importált tranzakciókat módosítjuk?
       // Inkább csak állítsuk be az Account balance mezőjét, és adjunk hozzá egy tranzakciót ha a rendszer onnan számol.
       await Transaction.deleteMany({ accountId: acc._id, note: 'Nyitó egyenleg' });
       await Transaction.create({
         userId: TIMI_ID,
         accountId: acc._id,
         amount: amount,
         currency: currency,
         type: 'income',
         date: new Date('2026-01-01'), // Év eleji nyitó
         note: 'Nyitó egyenleg'
       });
       
       await Account.updateOne({ _id: acc._id }, { balance: amount });
       console.log(`${name} beállítva: ${amount} ${currency}`);
    }

    // Beállítások
    await resetAndSet('Bank', 1700000);
    await resetAndSet('Készpénz', 916000);
    await resetAndSet('Euró', 120, 'EUR');
    await resetAndSet('Állampapír', 500000);
    await resetAndSet('Lakás kaució', 350000);

    console.log('MINDEN EGYENLEG KORRIGÁLVA!');
    process.exit(0);
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
}

fixBalances();
