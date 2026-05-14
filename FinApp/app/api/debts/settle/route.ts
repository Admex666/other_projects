import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../auth/[...nextauth]/route';
import dbConnect from '@/lib/mongodb';
import { Debt } from '@/models/Debt';
import mongoose from 'mongoose';

export async function POST(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { otherUserId } = await req.json();
  const userId = new mongoose.Types.ObjectId((session.user as any).id);
  const otherId = new mongoose.Types.ObjectId(otherUserId);

  await dbConnect();

  // Mark all pending debts between these two users as settled
  const result = await Debt.updateMany(
    {
      isSettled: false,
      $or: [
        { fromUserId: userId, toUserId: otherId },
        { fromUserId: otherId, toUserId: userId }
      ]
    },
    {
      $set: {
        isSettled: true,
        settledAt: new Date()
      }
    }
  );

  return NextResponse.json({ success: true, count: result.modifiedCount });
}
