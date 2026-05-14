import { ExchangeRate } from '@/models/ExchangeRate';
import dbConnect from './mongodb';

const FRANKFURTER_API = 'https://api.frankfurter.app';

export async function getLatestRates() {
  await dbConnect();
  
  const today = new Date().toISOString().split('T')[0];
  
  // 1. Megpróbáljuk lekérni a mait a cache-ből
  let cached = await ExchangeRate.findOne({ date: today });
  if (cached && cached.rates) {
    // Biztosítjuk, hogy tiszta objektumot adjunk vissza (nem Mongoose Map-et)
    return cached.rates instanceof Map ? Object.fromEntries(cached.rates) : JSON.parse(JSON.stringify(cached.rates));
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
    // Ha a mai napra nem találtuk, de van régi, akkor a régi HUF árfolyamát is biztosítsuk
    const rates = { ...lastAvailable.rates };
    if (!rates['HUF']) rates['HUF'] = 400.0;
    if (!rates['EUR']) rates['EUR'] = 1.0;
    return rates;
  }

  // 4. Végső eset
  return {
    "HUF": 401.5,
    "USD": 1.08,
    "EUR": 1.0,
    "GBP": 0.86
  };
}

export async function convertCurrency(amount: number, from: string, to: string, rates: any) {
  if (from === to || amount === 0) return amount;
  if (!rates) return amount;

  // Alapértelmezett árfolyamok (Hardcoded biztonsági háló)
  const DEFAULT_RATES: any = {
    "HUF": 357.43,
    "USD": 1.08,
    "EUR": 1.0,
    "GBP": 0.86
  };

  try {
    let fromRate = rates[from] || DEFAULT_RATES[from];
    let toRate = rates[to] || DEFAULT_RATES[to];

    // Ha még így is hiányzik (pl. egzotikus deviza), akkor a legközelebbi ismertet használjuk, vagy 1:1 (végső eset)
    if (!fromRate) {
      console.warn(`Nem található árfolyam a következőhöz: ${from}. Alapértelmezett 1.0 használata.`);
      fromRate = 1.0;
    }
    if (!toRate) {
      console.warn(`Nem található árfolyam a következőhöz: ${to}. Alapértelmezett 1.0 használata.`);
      toRate = 1.0;
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
