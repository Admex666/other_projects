import mongoose, { Schema, model, models } from 'mongoose';

const ExchangeRateSchema = new Schema({
  date: { type: String, required: true, unique: true }, // YYYY-MM-DD
  base: { type: String, default: 'EUR' },
  rates: { type: Map, of: Number, required: true },
  fetchedAt: { type: Date, default: Date.now },
});

export const ExchangeRate = models.ExchangeRate || model('ExchangeRate', ExchangeRateSchema);
