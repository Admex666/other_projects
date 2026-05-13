const bcrypt = require('bcryptjs');
const mongoose = require('mongoose');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config({ path: path.join(__dirname, '..', '.env.local') });

const UserSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  displayName: { type: String, required: true },
  baseCurrency: { type: String, default: 'HUF' },
  sharedWith: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
  createdAt: { type: Date, default: Date.now },
});

const User = mongoose.models.User || mongoose.model('User', UserSchema);

async function createAdmin() {
  const uri = process.env.MONGODB_URI;
  if (!uri || uri.includes('REPLACE_WITH_YOUR_PASSWORD')) {
    console.error('Error: MONGODB_URI not set or password not replaced in .env.local');
    process.exit(1);
  }

  await mongoose.connect(uri);
  console.log('Connected to MongoDB');

  const email = 'admin@admin.com'; // You can change this
  const password = 'password123'; // You can change this
  const displayName = 'Ádám';

  const existing = await User.findOne({ email });
  if (existing) {
    console.log('User already exists');
    process.exit(0);
  }

  const hashedPassword = await bcrypt.hash(password, 10);
  const user = new User({
    email,
    password: hashedPassword,
    displayName,
  });

  await user.save();
  console.log('Admin user created successfully!');
  console.log('Email:', email);
  console.log('Password:', password);
  process.exit(0);
}

createAdmin().catch(err => {
  console.error(err);
  process.exit(1);
});
