const mongoose = require('mongoose');
require('dotenv').config({ path: '.env.local' });

const dbConnect = async () => {
  await mongoose.connect(process.env.MONGODB_URI);
  
  const User = mongoose.model('User', new mongoose.Schema({ username: String }));
  const Category = mongoose.model('Category', new mongoose.Schema({ 
    userId: mongoose.Schema.Types.ObjectId, 
    name: String, 
    icon: String, 
    type: String 
  }));
  
  const user = await User.findOne({ username: 'adam' });
  if (!user) {
    console.log('User not found!');
    process.exit(1);
  }

  const cats = await Category.find({ userId: user._id }).sort({ name: 1 });
  
  console.log('Ádám kategóriái (' + cats.length + ' db):');
  cats.forEach(c => {
    console.log(`- ${c.icon || '📁'} ${c.name} (${c.type})`);
  });
  
  process.exit(0);
};

dbConnect();
