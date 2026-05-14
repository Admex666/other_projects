const mongoose = require('mongoose');
require('dotenv').config({ path: '.env.local' });

async function fixRate() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    const ExchangeRate = mongoose.models.ExchangeRate || mongoose.model('ExchangeRate', new mongoose.Schema({ 
      date: String, 
      rates: Object 
    }));

    const today = new Date().toISOString().split('T')[0];
    
    // Frissítjük a mai árfolyamot, hogy a HUF 357.43 legyen
    await ExchangeRate.findOneAndUpdate(
      { date: today }, 
      { $set: { 'rates.HUF': 357.43 } },
      { upsert: true }
    );

    console.log('Siker! A HUF árfolyamot 357.43-ra állítottam.');
    process.exit(0);
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
}

fixRate();
