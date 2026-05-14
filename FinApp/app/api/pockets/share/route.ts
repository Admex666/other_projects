import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../auth/[...nextauth]/route';
import dbConnect from '@/lib/mongodb';
import { VirtualPocket } from '@/models/VirtualPocket';
import { User } from '@/models/User';
import mongoose from 'mongoose';

export async function POST(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { pocketId, email } = await req.json();

  await dbConnect();
  
  // 1. Find user by email
  const userToShareWith = await User.findOne({ email });
  if (!userToShareWith) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 });
  }

  // 2. Find pocket and check ownership
  const pocket = await VirtualPocket.findOne({
    _id: pocketId,
    owners: new mongoose.Types.ObjectId((session.user as any).id)
  });

  if (!pocket) {
    return NextResponse.json({ error: 'Pocket not found or not owned by you' }, { status: 403 });
  }

  // 3. Add user to owners if not already there
  if (!pocket.owners.includes(userToShareWith._id)) {
    pocket.owners.push(userToShareWith._id);
    await pocket.save();
  }

  return NextResponse.json({ success: true, user: userToShareWith.displayName });
}
