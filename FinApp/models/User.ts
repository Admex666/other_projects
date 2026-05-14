import mongoose, { Schema, model, models } from 'mongoose';

const UserSchema = new Schema({
  email: { type: String, required: true, unique: true },
  username: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  displayName: { type: String, required: true },
  baseCurrency: { type: String, default: 'HUF' },
  sharedWith: [{ type: Schema.Types.ObjectId, ref: 'User' }],
  createdAt: { type: Date, default: Date.now },
});

export const User = models.User || model('User', UserSchema);
