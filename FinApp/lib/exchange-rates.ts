import { ExchangeRate } from '@/models/ExchangeRate';
import dbConnect from './mongodb';

const FRANKFURTER_API = 'https://api.frankfurter.app';

export async function getLatestRates() {
  await dbConnect();
  
  const today = new Date().toISOString().split('T')[0];
  
  // Check cache
  let cached = await ExchangeRate.findOne({ date: today });
  
  if (cached) {
    return cached.rates;
  }

  try {
    const res = await fetch(`${FRANKFURTER_API}/latest?from=EUR`);
    const data = await res.json();
    
    if (data && data.rates) {
      // Add EUR to rates as 1.0
      data.rates['EUR'] = 1.0;
      
      await ExchangeRate.findOneAndUpdate(
        { date: data.date },
        { 
          date: data.date,
          base: data.base,
          rates: data.rates,
          fetchedAt: new Date()
        },
        { upsert: true, new: true }
      );
      
      return data.rates;
    }
  } catch (err) {
    console.error('Failed to fetch exchange rates:', err);
    // Return last available rates if fetch fails
    const last = await ExchangeRate.findOne().sort({ date: -1 });
    return last ? last.rates : null;
  }
}

export async function convertCurrency(amount: number, from: string, to: string, rates: any) {
  if (from === to) return amount;
  if (!rates) return amount;
  
  // Convert from 'from' to EUR, then from EUR to 'to'
  const inEur = from === 'EUR' ? amount : amount / rates[from];
  const result = to === 'EUR' ? inEur : inEur * rates[to];
  
  return result;
}
