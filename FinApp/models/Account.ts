import mongoose, { Schema, model, models } from 'mongoose';

const AccountSchema = new Schema({
  userId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  name: { type: String, required: true },
  currency: { type: String, default: 'HUF' },
  type: { type: String, enum: ['bank', 'cash', 'crypto', 'investment'], default: 'bank' },
  isBusinessAccount: { type: Boolean, default: false },
  initialBalance: { type: Number, default: 0 },
  color: { type: String, default: '#6C63FF' },
  icon: { type: String, default: '💳' },
  isArchived: { type: Boolean, default: false },
}, { timestamps: true });

export const Account = models.Account || model('Account', AccountSchema);
