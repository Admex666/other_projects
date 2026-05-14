const mongoose = require('mongoose');
require('dotenv').config({ path: '.env.local' });

async function migrate() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    const User = mongoose.models.User || mongoose.model('User', new mongoose.Schema({ 
      email: String, 
      username: String, 
      displayName: String 
    }));

    const res = await User.updateOne(
      { email: 'admin@admin.com' }, 
      { $set: { 
          email: 'adam.jakus99@gmail.com', 
          username: 'adam', 
          displayName: 'Adam' 
        } 
      }
    );

    console.log('Siker! Módosított dokumentumok száma:', res.modifiedCount);
    process.exit(0);
  } catch (err) {
    console.error('Hiba a migráció során:', err);
    process.exit(1);
  }
}

migrate();
