import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../auth/[...nextauth]/route';
import dbConnect from '@/lib/mongodb';
import { Debt } from '@/models/Debt';
import { User } from '@/models/User';
import mongoose from 'mongoose';

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  await dbConnect();
  const userId = new mongoose.Types.ObjectId((session.user as any).id);

  // 1. Get all unsettled debts involving this user
  const debts = await Debt.find({
    isSettled: false,
    $or: [{ fromUserId: userId }, { toUserId: userId }]
  }).populate('fromUserId toUserId', 'displayName');

  // 2. Aggregate net debt per person
  const summary: Record<string, { userId: string, name: string, netAmount: number, currency: string }> = {};

  debts.forEach(debt => {
    const isImTheDebtor = debt.fromUserId._id.toString() === userId.toString();
    const otherUser = isImTheDebtor ? debt.toUserId : debt.fromUserId;
    const otherUserId = otherUser._id.toString();

    if (!summary[otherUserId]) {
      summary[otherUserId] = {
        userId: otherUserId,
        name: otherUser.displayName,
        netAmount: 0,
        currency: debt.currency
      };
    }

    if (isImTheDebtor) {
      // I owe them (negative for me)
      summary[otherUserId].netAmount -= debt.amount;
    } else {
      // They owe me (positive for me)
      summary[otherUserId].netAmount += debt.amount;
    }
  });

  return NextResponse.json(Object.values(summary));
}
