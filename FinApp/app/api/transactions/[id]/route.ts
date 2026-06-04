import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../auth/[...nextauth]/route';
import dbConnect from '@/lib/mongodb';
import { Transaction } from '@/models/Transaction';
import { VirtualPocket } from '@/models/VirtualPocket';
import { Debt } from '@/models/Debt';
import mongoose from 'mongoose';
import { syncEmitter } from '@/lib/sync-emitter';

export async function PUT(req: Request, { params }: { params: { id: string } }) {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  await dbConnect();
  const userId = new mongoose.Types.ObjectId((session.user as any).id);
  const body = await req.json();

  try {
    const transaction = await Transaction.findOne({ _id: params.id, userId });
    
    if (!transaction) {
      return NextResponse.json({ error: 'Transaction not found' }, { status: 404 });
    }

    // Update fields
    transaction.type = body.type;
    transaction.amount = body.amount;
    transaction.currency = body.currency;
    transaction.accountId = body.accountId;
    transaction.categoryId = body.categoryId;
    transaction.note = body.note;
    transaction.date = body.date;
    transaction.isBusinessTransaction = body.isBusinessTransaction;
    transaction.virtualPocketId = body.virtualPocketId || undefined;

    await transaction.save();

    // Handle Debts: Delete existing related debts
    await Debt.deleteMany({ relatedTransactionId: transaction._id });

    // If it's a shared pocket, recreate the debt
    if (body.virtualPocketId) {
      const pocket = await VirtualPocket.findById(body.virtualPocketId);
      
      if (pocket && pocket.owners.length > 1) {
        const otherOwnerId = pocket.owners.find((id: any) => id.toString() !== userId.toString());
        
        if (otherOwnerId) {
          const finalDebtAmount = body.debtAmount !== undefined ? body.debtAmount : (body.amount / 2);
          
          await Debt.create({
            fromUserId: otherOwnerId,
            toUserId: userId,
            amount: finalDebtAmount,
            currency: body.currency || 'HUF',
            relatedTransactionId: transaction._id,
            note: `Felesben/Egyedi (Frissített): ${body.note || 'Közös költés'}`
          });
        }
      }
    }

    // Emit sync event
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
      type: 'TRANSACTION_UPDATED',
      userIds: userIdsToSync,
      data: transaction
    });

    return NextResponse.json(transaction);
  } catch (error) {
    console.error('Error updating transaction:', error);
    return NextResponse.json({ error: 'Failed to update transaction' }, { status: 500 });
  }
}

export async function DELETE(req: Request, { params }: { params: { id: string } }) {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  await dbConnect();
  const userId = new mongoose.Types.ObjectId((session.user as any).id);

  try {
    const transaction = await Transaction.findOne({ _id: params.id, userId });
    
    if (!transaction) {
      return NextResponse.json({ error: 'Transaction not found' }, { status: 404 });
    }

    // Capture pocket ID for sync before deletion
    const pocketId = transaction.virtualPocketId;

    // Delete related debts
    await Debt.deleteMany({ relatedTransactionId: transaction._id });
    
    // Delete transaction
    await Transaction.deleteOne({ _id: transaction._id });

    // Emit sync event
    const userIdsToSync = [userId.toString()];
    if (pocketId) {
      const pocket = await VirtualPocket.findById(pocketId);
      if (pocket) {
        pocket.owners.forEach((id: any) => {
          if (!userIdsToSync.includes(id.toString())) userIdsToSync.push(id.toString());
        });
      }
    }

    syncEmitter.emit('sync', {
      type: 'TRANSACTION_DELETED',
      userIds: userIdsToSync,
      data: { id: params.id }
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error deleting transaction:', error);
    return NextResponse.json({ error: 'Failed to delete transaction' }, { status: 500 });
  }
}
