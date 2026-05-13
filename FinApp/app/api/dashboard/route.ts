import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';
import dbConnect from '@/lib/mongodb';
import { Transaction } from '@/models/Transaction';
import { Account } from '@/models/Account';
import { VirtualPocket } from '@/models/VirtualPocket';
import { Category } from '@/models/Category';
import mongoose from 'mongoose';
import { getLatestRates, convertCurrency } from '@/lib/exchange-rates';

export async function GET() {
  const session = await getServerSession(authOptions);

  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  await dbConnect();
  
  // Ensure models are registered (especially for population)
  if (!mongoose.models.Category) mongoose.model('Category', Category.schema);
  if (!mongoose.models.Account) mongoose.model('Account', Account.schema);

  const userId = new mongoose.Types.ObjectId((session.user as any).id);

  // 1. Get all accounts
  const accounts = await Account.find({ userId });
  
  // 2. Get pockets
  const pockets = await VirtualPocket.find({ owners: userId }).populate('linkedAccountId', 'name');
  
  // 3. Get balances
  const balances = await Transaction.aggregate([
    { $match: { userId } },
    { $group: { _id: '$accountId', balance: { $sum: { $cond: [{ $eq: ['$type', 'income'] }, '$amount', { $subtract: [0, '$amount'] }] } } } }
  ]);

  const outgoingTransfers = await Transaction.aggregate([
    { $match: { userId, type: 'transfer' } },
    { $group: { _id: '$fromAccountId', total: { $sum: '$amount' } } }
  ]);

  const incomingTransfers = await Transaction.aggregate([
    { $match: { userId, type: 'transfer' } },
    { $group: { _id: '$toAccountId', total: { $sum: '$amount' } } }
  ]);

  const rates = await getLatestRates();

  const accountMap = await Promise.all(accounts.map(async (acc) => {
    const baseBalance = balances.find(b => b._id && b._id.toString() === acc._id.toString())?.balance || 0;
    const out = outgoingTransfers.find(t => t._id && t._id.toString() === acc._id.toString())?.total || 0;
    const inc = incomingTransfers.find(t => t._id && t._id.toString() === acc._id.toString())?.total || 0;
    
    const balance = baseBalance - out + inc;
    const balanceInBase = await convertCurrency(balance, acc.currency, 'HUF', rates);
    
    return {
      ...acc.toObject(),
      balance,
      balanceInBase
    };
  }));

  // 4. Recent transactions
  const recentTransactions = await Transaction.find({ userId })
    .sort({ date: -1 })
    .limit(10)
    .populate('accountId', 'name color icon')
    .populate('categoryId', 'name icon');

  // 5. Monthly data
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const monthlyData = await Transaction.aggregate([
    { $match: { userId, date: { $gte: startOfMonth }, type: { $ne: 'transfer' } } },
    { $group: { _id: '$type', total: { $sum: '$amount' } } }
  ]);

  const income = monthlyData.find(d => d._id === 'income')?.total || 0;
  const expense = monthlyData.find(d => d._id === 'expense')?.total || 0;

  // 6. Trend data
  const sixMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 5, 1);
  const trendData = await Transaction.aggregate([
    { $match: { userId, date: { $gte: sixMonthsAgo } } },
    {
      $group: {
        _id: {
          year: { $year: '$date' },
          month: { $month: '$date' },
          type: '$type'
        },
        total: { $sum: '$amount' }
      }
    },
    { $sort: { '_id.year': 1, '_id.month': 1 } }
  ]);

  return NextResponse.json({
    accounts: accountMap,
    recentTransactions,
    monthly: {
      income,
      expense,
      profit: income - expense
    },
    trend: trendData,
    pockets
  });
}
