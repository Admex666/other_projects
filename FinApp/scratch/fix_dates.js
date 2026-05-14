const mongoose = require('mongoose');
require('dotenv').config({ path: '.env.local' });

async function fixDates() {
  await mongoose.connect(process.env.MONGODB_URI);
  const Transaction = mongoose.model('Transaction', new mongoose.Schema({ date: Date }));
  
  const trans = await Transaction.find({ 
    date: { $lt: new Date('1971-01-01') } 
  });
  
  console.log(`Found ${trans.length} transactions with 1970 dates.`);
  
  let fixedCount = 0;
  for (let t of trans) {
    const excelSerial = t.date.getTime();
    // Check if it looks like an Excel serial (usually between 40000 and 60000)
    if (excelSerial > 30000 && excelSerial < 70000) {
      const realDate = new Date((excelSerial - 25569) * 86400 * 1000);
      await Transaction.updateOne({ _id: t._id }, { $set: { date: realDate } });
      fixedCount++;
    }
  }
  
  console.log(`Successfully fixed ${fixedCount} dates.`);
  await mongoose.disconnect();
}

fixDates();
