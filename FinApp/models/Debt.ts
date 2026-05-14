import mongoose, { Schema, Document } from 'mongoose';

export interface IDebt extends Document {
  fromUserId: mongoose.Types.ObjectId;
  toUserId: mongoose.Types.ObjectId;
  amount: number;
  currency: string;
  relatedTransactionId?: mongoose.Types.ObjectId;
  note?: string;
  isSettled: boolean;
  settledAt?: Date;
}

const DebtSchema: Schema = new Schema({
  fromUserId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  toUserId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  amount: { type: Number, required: true },
  currency: { type: String, required: true, default: 'HUF' },
  relatedTransactionId: { type: Schema.Types.ObjectId, ref: 'Transaction' },
  note: { type: String },
  isSettled: { type: Boolean, default: false },
  settledAt: { type: Date }
}, { timestamps: true });

export const Debt = mongoose.models.Debt || mongoose.model<IDebt>('Debt', DebtSchema);
