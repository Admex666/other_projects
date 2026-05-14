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
  
  if (!mongoose.models.Category) mongoose.model('Category', Category.schema);
  if (!mongoose.models.Account) mongoose.model('Account', Account.schema);

  const userId = new mongoose.Types.ObjectId((session.user as any).id);

  const accounts = await Account.find({ userId });
  const pockets = await VirtualPocket.find({ owners: userId }).populate('linkedAccountId', 'name');
  
  const rates = await getLatestRates();

  // 1. Calculate Account Balances (Only real transactions)
  const accountMap = await Promise.all(accounts.map(async (acc) => {
    const txs = await Transaction.find({
      userId: userId.toString(),
      isInternalAllocation: { $ne: true },
      $or: [
        { accountId: acc._id },
        { toAccountId: acc._id }
      ]
    });

    // Fallback: if no txs found with string ID, try with ObjectId
    if (txs.length === 0) {
      const txsObjId = await Transaction.find({
        userId: userId,
        isInternalAllocation: { $ne: true },
        $or: [
          { accountId: acc._id },
          { toAccountId: acc._id }
        ]
      });
      if (txsObjId.length > 0) txs.push(...txsObjId);
    }

    let balance = acc.initialBalance || 0;
    for (const tx of txs) {
      if (tx.accountId?.toString() === acc._id.toString()) {
        const amountInAccCurrency = await convertCurrency(tx.amount, tx.currency, acc.currency, rates);
        if (tx.type === 'income') balance += amountInAccCurrency;
        else balance -= amountInAccCurrency;
      } else if (tx.toAccountId?.toString() === acc._id.toString() && tx.type === 'transfer') {
        const amountInAccCurrency = await convertCurrency(tx.amount, tx.currency, acc.currency, rates);
        balance += amountInAccCurrency;
      }
    }

    const balanceInBase = await convertCurrency(balance, acc.currency, 'HUF', rates);
    return {
      ...acc.toObject(),
      balance: Number(balance.toFixed(2)),
      balanceInBase: Number(balanceInBase.toFixed(0))
    };
  }));

  // 2. Calculate Virtual Pocket Balances (Ensuring min 0)
  const pocketMap = await Promise.all(pockets.map(async (p) => {
    const txs = await Transaction.find({ virtualPocketId: p._id });
    
    let balance = 0;
    for (const tx of txs) {
      const amountInPocketCurrency = await convertCurrency(tx.amount, tx.currency, p.currency, rates);
      if (tx.type === 'income') balance += amountInPocketCurrency;
      else balance -= amountInPocketCurrency;
    }

    // Rule: Pocket cannot be negative
    const finalBalance = Math.max(0, balance);

    return {
      ...p.toObject(),
      currentAmount: Number(finalBalance.toFixed(2)),
      progress: p.targetAmount ? Math.min(Math.round((finalBalance / p.targetAmount) * 100), 100) : 0
    };
  }));

  // 3. Calculate "Free Balance" (Total Base Balance - Total Pockets in Base)
  const totalAccountBase = accountMap.reduce((sum, acc) => sum + acc.balanceInBase, 0);
  const totalPocketBase = await Promise.all(pocketMap.map((p: any) => convertCurrency(p.currentAmount, p.currency, 'HUF', rates)));
  const totalPocketBaseSum = totalPocketBase.reduce((sum, val) => sum + val, 0);
  
  const freeBalance = totalAccountBase - totalPocketBaseSum;

  const recentTransactions = await Transaction.find({ userId })
    .sort({ date: -1 })
    .limit(10)
    .populate('accountId', 'name color icon')
    .populate('categoryId', 'name icon');

  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

  let income = 0;
  let expense = 0;
  const monthlyTxs = await Transaction.find({ userId, date: { $gte: startOfMonth }, type: { $ne: 'transfer' }, isInternalAllocation: { $ne: true } });
  for (const tx of monthlyTxs) {
    const val = await convertCurrency(tx.amount, tx.currency, 'HUF', rates);
    if (tx.type === 'income') income += val;
    else expense += val;
  }

  return NextResponse.json({
    accounts: accountMap,
    recentTransactions,
    monthly: {
      income: Math.round(income),
      expense: Math.round(expense),
      profit: Math.round(income - expense)
    },
    pockets: pocketMap,
    freeBalance: Math.max(0, Math.round(freeBalance))
  });
}
