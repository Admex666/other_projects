import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';
import dbConnect from '@/lib/mongodb';
import { Transaction } from '@/models/Transaction';
import { Category } from '@/models/Category';
import mongoose from 'mongoose';

export async function GET(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  await dbConnect();
  const userId = new mongoose.Types.ObjectId((session.user as any).id);
  
  // 1. Monthly P/L by Category (Current month)
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  
  // Register Category model if not already
  if (!mongoose.models.Category) mongoose.model('Category', Category.schema);

  const categoryPL = await Transaction.aggregate([
    { $match: { userId, date: { $gte: startOfMonth }, type: { $ne: 'transfer' } } },
    {
      $group: {
        _id: { categoryId: '$categoryId', type: '$type' },
        total: { $sum: '$amount' }
      }
    },
    {
      $lookup: {
        from: 'categories',
        localField: '_id.categoryId',
        foreignField: '_id',
        as: 'category'
      }
    },
    { $unwind: '$category' },
    {
      $project: {
        name: '$category.name',
        type: '$_id.type',
        total: 1
      }
    }
  ]);

  // Transform to chart format: [{ name: 'Food', income: 100, expense: 50 }, ...]
  const plMap: Record<string, any> = {};
  categoryPL.forEach(item => {
    if (!plMap[item.name]) plMap[item.name] = { name: item.name, income: 0, expense: 0 };
    plMap[item.name][item.type] = item.total;
  });

  // 2. Category Breakdown (Expenses only)
  const breakdown = await Transaction.aggregate([
    { $match: { userId, date: { $gte: startOfMonth }, type: 'expense' } },
    {
      $group: {
        _id: '$categoryId',
        value: { $sum: '$amount' }
      }
    },
    {
      $lookup: {
        from: 'categories',
        localField: '_id',
        foreignField: '_id',
        as: 'category'
      }
    },
    { $unwind: '$category' },
    {
      $project: {
        name: '$category.name',
        value: 1,
        color: '$category.color'
      }
    }
  ]);

  // 3. 12-month Trend
  const twelveMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 11, 1);
  const trend = await Transaction.aggregate([
    { $match: { userId, date: { $gte: twelveMonthsAgo } } },
    {
      $group: {
        _id: {
          year: { $year: '$date' },
          month: { $month: '$date' }
        },
        income: { $sum: { $cond: [{ $eq: ['$type', 'income'] }, '$amount', 0] } },
        expense: { $sum: { $cond: [{ $eq: ['$type', 'expense'] }, '$amount', 0] } }
      }
    },
    { $sort: { '_id.year': 1, '_id.month': 1 } },
    {
      $project: {
        name: { 
          $concat: [
            { $substr: ['$_id.year', 0, 4] }, 
            '-', 
            { $substr: ['$_id.month', 0, 2] }
          ] 
        },
        net: { $subtract: ['$income', '$expense'] }
      }
    }
  ]);

  return NextResponse.json({
    monthlyPL: Object.values(plMap),
    breakdown,
    trend
  });
}
