const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
require('dotenv').config({ path: '.env.local' });

async function updateTimi() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    const User = mongoose.models.User || mongoose.model('User', new mongoose.Schema({ 
      email: String, 
      username: String, 
      displayName: String,
      password: String
    }));

    const hashedPassword = await bcrypt.hash('Timi2026', 10);
    const res = await User.updateOne(
      { email: 'partner@partner.com' }, 
      { $set: { 
          username: 'timi', 
          displayName: 'Timi',
          password: hashedPassword 
        } 
      }
    );

    console.log('Siker! Timi fiókja frissítve.');
    process.exit(0);
  } catch (err) {
    console.error('Hiba Timi fiókjának frissítésekor:', err);
    process.exit(1);
  }
}

updateTimi();
