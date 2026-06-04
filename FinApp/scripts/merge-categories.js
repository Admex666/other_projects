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
  const Transaction = mongoose.model('Transaction', new mongoose.Schema({
    categoryId: mongoose.Schema.Types.ObjectId
  }, { strict: false }));
  
  const user = await User.findOne({ username: 'adam' });
  if (!user) {
    console.log('User not found!');
    process.exit(1);
  }

  const userId = user._id;

  // 1. Merge "Ajándék" and "Ajándékok"
  const ajandekInc = await Category.findOne({ userId, name: 'Ajándék' });
  const ajandekExp = await Category.findOne({ userId, name: 'Ajándékok' });

  if (ajandekInc && ajandekExp) {
    console.log('Merging Ajándék and Ajándékok...');
    // Keep ajandekInc, update it
    ajandekInc.type = 'both';
    await ajandekInc.save();

    // Update transactions
    const result = await Transaction.updateMany(
      { categoryId: ajandekExp._id },
      { $set: { categoryId: ajandekInc._id } }
    );
    console.log(`Updated ${result.modifiedCount} transactions for Ajándék.`);

    // Delete ajandekExp
    await Category.deleteOne({ _id: ajandekExp._id });
    console.log('Deleted Ajándékok (expense).');
  }

  // 2. Merge "Egyéb"
  const egyebInc = await Category.findOne({ userId, name: 'Egyéb', type: 'income' });
  const egyebExp = await Category.findOne({ userId, name: 'Egyéb', type: 'expense' });

  if (egyebInc && egyebExp) {
    console.log('Merging Egyéb...');
    // Keep egyebExp, update it
    egyebExp.type = 'both';
    await egyebExp.save();

    // Update transactions
    const result = await Transaction.updateMany(
      { categoryId: egyebInc._id },
      { $set: { categoryId: egyebExp._id } }
    );
    console.log(`Updated ${result.modifiedCount} transactions for Egyéb.`);

    // Delete egyebInc
    await Category.deleteOne({ _id: egyebInc._id });
    console.log('Deleted Egyéb (income).');
  }

  console.log('Merge complete!');
  process.exit(0);
};

dbConnect();
