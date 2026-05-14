import mongoose, { Schema, model, models } from 'mongoose';

const TransactionSchema = new Schema({
  userId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  type: { type: String, enum: ['income', 'expense', 'transfer'], required: true },
  date: { type: Date, required: true },
  amount: { type: Number, required: true },
  currency: { type: String, required: true },
  amountInBaseCurrency: { type: Number },
  exchangeRate: { type: Number, default: 1 },
  accountId: { type: Schema.Types.ObjectId, ref: 'Account', required: true },
  toAccountId: { type: Schema.Types.ObjectId, ref: 'Account' }, // only for transfers
  categoryId: { type: Schema.Types.ObjectId, ref: 'Category' },
  virtualPocketId: { type: Schema.Types.ObjectId, ref: 'VirtualPocket' },
  tags: [String],
  note: { type: String },
  isBusinessTransaction: { type: Boolean, default: false },
  isInternalAllocation: { type: Boolean, default: false },
  importedFrom: { type: String }, // e.g. 'xlsx'
}, { timestamps: true });

export const Transaction = models.Transaction || model('Transaction', TransactionSchema);
