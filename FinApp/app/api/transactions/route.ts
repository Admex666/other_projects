import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';
import dbConnect from '@/lib/mongodb';
import { Transaction } from '@/models/Transaction';
import { VirtualPocket } from '@/models/VirtualPocket';
import { Debt } from '@/models/Debt';
import mongoose from 'mongoose';
import { syncEmitter } from '@/lib/sync-emitter';

export async function POST(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  await dbConnect();
  const body = await req.json();
  const userId = new mongoose.Types.ObjectId((session.user as any).id);

  // 1. Create the transaction
  const transaction = await Transaction.create({
    ...body,
    userId,
  });

  // 2. If it's a shared pocket, create a debt
  if (body.virtualPocketId) {
    const pocket = await VirtualPocket.findById(body.virtualPocketId);
    
    if (pocket && pocket.owners.length > 1) {
      // Find the other owner (assuming 2 owners for now)
      const otherOwnerId = pocket.owners.find((id: any) => id.toString() !== userId.toString());
      
      if (otherOwnerId) {
        // Create debt: use custom amount if provided, otherwise default to 50%
        const finalDebtAmount = body.debtAmount !== undefined ? body.debtAmount : (body.amount / 2);
        
        await Debt.create({
          fromUserId: otherOwnerId,
          toUserId: userId,
          amount: finalDebtAmount,
          currency: body.currency || 'HUF',
          relatedTransactionId: transaction._id,
          note: `Felesben/Egyedi: ${body.note || 'Közös költés'}`
        });
      }
    }
  }

  // 3. Emit sync event
  const userIdsToSync = [userId.toString()];
  if (body.virtualPocketId) {
    const pocket = await VirtualPocket.findById(body.virtualPocketId);
    if (pocket) {
      pocket.owners.forEach((id: any) => {
        if (!userIdsToSync.includes(id.toString())) userIdsToSync.push(id.toString());
      });
    }
  }

  syncEmitter.emit('sync', {
    type: 'TRANSACTION_CREATED',
    userIds: userIdsToSync,
    data: transaction
  });

  return NextResponse.json(transaction);
}
