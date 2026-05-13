import mongoose, { Schema, model, models } from 'mongoose';

const CategorySchema = new Schema({
  userId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  name: { type: String, required: true },
  type: { type: String, enum: ['income', 'expense', 'both'], default: 'expense' },
  icon: { type: String, default: '📁' },
  color: { type: String, default: '#FFB347' },
  parentId: { type: Schema.Types.ObjectId, ref: 'Category' },
  isBusinessCategory: { type: Boolean, default: false },
}, { timestamps: true });

export const Category = models.Category || model('Category', CategorySchema);
