import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';
import dbConnect from '@/lib/mongodb';
import { Transaction } from '@/models/Transaction';
import mongoose from 'mongoose';

export async function POST(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  await dbConnect();
  const body = await req.json();
  const userId = new mongoose.Types.ObjectId((session.user as any).id);

  const transaction = await Transaction.create({
    ...body,
    userId,
  });

  return NextResponse.json(transaction);
}
