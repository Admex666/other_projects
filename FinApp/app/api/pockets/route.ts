import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import dbConnect from '@/lib/mongodb';
import { VirtualPocket } from '@/models/VirtualPocket';
import mongoose from 'mongoose';

export async function GET() {
  const session = await getServerSession();
  if (!session || !(session.user as any).id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  await dbConnect();
  const userId = new mongoose.Types.ObjectId((session.user as any).id);

  const pockets = await VirtualPocket.find({ 
    owners: userId 
  }).populate('linkedAccountId', 'name icon color');

  return NextResponse.json(pockets);
}

export async function POST(req: Request) {
  const session = await getServerSession();
  if (!session || !(session.user as any).id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  await dbConnect();
  const userId = new mongoose.Types.ObjectId((session.user as any).id);
  const body = await req.json();

  const pocket = await VirtualPocket.create({
    ...body,
    owners: [userId] // Initially the creator is the owner
  });

  return NextResponse.json(pocket);
}
