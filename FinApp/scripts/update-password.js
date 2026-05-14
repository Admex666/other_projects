const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
require('dotenv').config({ path: '.env.local' });

async function updatePassword() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    const User = mongoose.models.User || mongoose.model('User', new mongoose.Schema({ 
      username: String, 
      password: String 
    }));

    const hashedPassword = await bcrypt.hash('Eztt0rdfel', 10);
    const res = await User.updateOne(
      { username: 'adam' }, 
      { $set: { password: hashedPassword } }
    );

    console.log('Siker! Jelszó frissítve az "adam" felhasználóhoz.');
    process.exit(0);
  } catch (err) {
    console.error('Hiba a jelszófrissítés során:', err);
    process.exit(1);
  }
}

updatePassword();
