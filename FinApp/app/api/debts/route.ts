import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';
import dbConnect from '@/lib/mongodb';
import { Debt } from '@/models/Debt';
import mongoose from 'mongoose';

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  await dbConnect();
  const userId = new mongoose.Types.ObjectId((session.user as any).id);

  // Fetch all unsettled debts where the user is either the debtor or the creditor
  const debts = await Debt.find({
    isSettled: false,
    $or: [{ fromUserId: userId }, { toUserId: userId }]
  })
  .sort({ createdAt: -1 })
  .populate('fromUserId toUserId', 'displayName email');

  return NextResponse.json(debts);
}
