import mongoose, { Schema, model, models } from 'mongoose';

const VirtualPocketSchema = new Schema({
  name: { type: String, required: true },
  currency: { type: String, default: 'HUF' },
  linkedAccountId: { type: Schema.Types.ObjectId, ref: 'Account', required: true },
  owners: [{ type: Schema.Types.ObjectId, ref: 'User' }],
  targetAmount: { type: Number },
  color: { type: String, default: '#FF6584' },
}, { timestamps: true });

export const VirtualPocket = models.VirtualPocket || model('VirtualPocket', VirtualPocketSchema);
