import { ExchangeRate } from '@/models/ExchangeRate';
import dbConnect from './mongodb';

const FRANKFURTER_API = 'https://api.frankfurter.app';

export async function getLatestRates() {
  await dbConnect();
  
  const today = new Date().toISOString().split('T')[0];
  
  // 1. Megpróbáljuk lekérni a mait a cache-ből
  let cached = await ExchangeRate.findOne({ date: today });
  if (cached && cached.rates) {
    return cached.rates;
  }

  // 2. Ha nincs mai, megpróbáljuk az API-t
  try {
    const res = await fetch(`${FRANKFURTER_API}/latest?from=EUR`);
    if (!res.ok) throw new Error('API request failed');
    
    const data = await res.json();
    
    if (data && data.rates) {
      // EUR alapú rendszerben az EUR mindig 1.0
      data.rates['EUR'] = 1.0;
      
      // Elmentjük a friss adatokat
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
    console.error('Exchange API error, falling back to database history:', err);
  }

  // 3. Ha az API elszállt, keressük a legutolsó rögzített árfolyamot (bármelyik napról)
  const lastAvailable = await ExchangeRate.findOne().sort({ date: -1 });
  
  if (lastAvailable && lastAvailable.rates) {
    console.log(`Using fallback rates from: ${lastAvailable.date}`);
    return lastAvailable.rates;
  }

  // 4. Végső eset (ha még sosem sikerült semmit letölteni - pl. első indítás internet nélkül)
  // Ez csak egy biztonsági háló, hogy ne legyen NaN sehol.
  return {
    "HUF": 400.0,
    "USD": 1.08,
    "EUR": 1.0,
    "BGN": 1.95
  };
}

export async function convertCurrency(amount: number, from: string, to: string, rates: any) {
  if (from === to || amount === 0) return amount;
  
  // Ha nincs árfolyamunk, nem tudunk konvertálni, marad az eredeti összeg
  if (!rates) return amount;
  
  try {
    // Alapértelmezett árfolyamok ha valami hiányozna (fallback az 1.0-ra hogy ne legyen NaN)
    const fromRate = rates[from] || (from === 'EUR' ? 1.0 : null);
    const toRate = rates[to] || (to === 'EUR' ? 1.0 : null);

    if (fromRate === null || toRate === null) {
      console.warn(`Missing rate for ${fromRate === null ? from : to}. Using 1:1 fallback.`);
      return amount;
    }

    // Átszámítás EUR-ra, majd onnan a cél devizára
    const inEur = from === 'EUR' ? amount : amount / fromRate;
    const result = to === 'EUR' ? inEur : inEur * toRate;
    
    return isNaN(result) ? amount : result;
  } catch (err) {
    console.error('Conversion math error:', err);
    return amount;
  }
}
