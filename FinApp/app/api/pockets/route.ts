import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';
import dbConnect from '@/lib/mongodb';
import { VirtualPocket } from '@/models/VirtualPocket';
import mongoose from 'mongoose';

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  await dbConnect();
  const pockets = await VirtualPocket.find({ 
    owners: new mongoose.Types.ObjectId((session.user as any).id) 
  }).populate('linkedAccountId', 'name');

  return NextResponse.json(pockets);
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { name, targetAmount, currency, linkedAccountId, color } = await req.json();

  await dbConnect();
  const pocket = await VirtualPocket.create({
    name,
    targetAmount,
    currency: currency || 'HUF',
    linkedAccountId,
    owners: [new mongoose.Types.ObjectId((session.user as any).id)],
    color: color || '#7C6FFF'
  });

  return NextResponse.json(pocket);
}

export async function DELETE(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(req.url);
  const id = searchParams.get('id');

  await dbConnect();
  await VirtualPocket.deleteOne({ 
    _id: id,
    owners: new mongoose.Types.ObjectId((session.user as any).id)
  });

  return NextResponse.json({ success: true });
}
