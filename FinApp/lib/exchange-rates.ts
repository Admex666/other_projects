import { ExchangeRate } from '@/models/ExchangeRate';
import dbConnect from './mongodb';

const EXCHANGE_RATE_API = 'https://open.er-api.com/v6/latest/EUR';

export async function getLatestRates() {
  await dbConnect();
  
  const today = new Date().toISOString().split('T')[0];
  
  // 1. Megpróbáljuk lekérni a mait a cache-ből
  let cached = await ExchangeRate.findOne({ date: today });
  if (cached && cached.rates) {
    return cached.rates instanceof Map ? Object.fromEntries(cached.rates) : JSON.parse(JSON.stringify(cached.rates));
  }

  // 2. Ha nincs mai, megpróbáljuk az API-t
  try {
    const res = await fetch(EXCHANGE_RATE_API);
    if (!res.ok) throw new Error('API request failed');
    
    const data = await res.json();
    
    if (data && data.rates) {
      // Elmentjük a friss adatokat
      await ExchangeRate.findOneAndUpdate(
        { date: today }, // A mai napra cache-eljük
        { 
          date: today,
          base: 'EUR',
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

  // 3. Ha az API elszállt, keressük a legutolsó rögzített árfolyamot
  const lastAvailable = await ExchangeRate.findOne().sort({ date: -1 });
  
  if (lastAvailable && lastAvailable.rates) {
    console.log(`Using fallback rates from: ${lastAvailable.date}`);
    return { ...lastAvailable.rates };
  }

  // 4. Végső eset (Hardcoded biztonsági háló)
  return {
    "HUF": 357.67,
    "USD": 1.08,
    "EUR": 1.0,
    "GBP": 0.86,
    "BGN": 1.95,
    "CHF": 0.98
  };
}

export async function convertCurrency(amount: number, from: string, to: string, rates: any) {
  if (from === to || amount === 0) return amount;
  
  // Alapértelmezett árfolyamok (Még biztosabb háló)
  const DEFAULT_RATES: any = {
    "HUF": 357.67,
    "USD": 1.08,
    "EUR": 1.0,
    "GBP": 0.86,
    "BGN": 1.95,
    "CHF": 0.98
  };

  const currentRates = rates || DEFAULT_RATES;

  try {
    let fromRate = currentRates[from] || DEFAULT_RATES[from] || 1.0;
    let toRate = currentRates[to] || DEFAULT_RATES[to] || 1.0;

    // Átszámítás EUR-ra, majd onnan a cél devizára (Az API EUR alapú)
    const inEur = from === 'EUR' ? amount : amount / fromRate;
    const result = to === 'EUR' ? inEur : inEur * toRate;
    
    if (!isNaN(result)) {
      const effectiveRate = result / amount;
      console.log(`[Currency] ${amount} ${from} -> ${result.toFixed(2)} ${to} (Árfolyam: ${effectiveRate.toFixed(4)})`);
      return result;
    }
    
    return amount;
  } catch (err) {
    console.error('Conversion math error:', err);
    return amount;
  }
}
