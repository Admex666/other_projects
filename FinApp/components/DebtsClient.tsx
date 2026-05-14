'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Users, 
  CheckCircle2, 
  Clock, 
  Receipt,
  HandCoins
} from 'lucide-react';
import Link from 'next/link';

export default function DebtsClient() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [debts, setDebts] = useState<any[]>([]);
  const [summary, setSummary] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDebts = useCallback(async () => {
    try {
      // Fetch full list and summary
      const [resList, resSum] = await Promise.all([
        fetch('/api/debts'),
        fetch('/api/debts/summary')
      ]);
      const list = await resList.json();
      const sum = await resSum.json();
      setDebts(list);
      setSummary(sum);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    } else if (status === 'authenticated') {
      fetchDebts();
    }
  }, [status, fetchDebts]);

  const handleSettle = async (otherUserId: string) => {
    if (!confirm('Biztosan nullázni szeretnéd a tartozást? (Feltételezzük, hogy az elszámolás az appon kívül megtörtént)')) return;
    
    try {
      const res = await fetch('/api/debts/settle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ otherUserId }),
      });
      if (res.ok) fetchDebts();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-screen bg-background">Betöltés...</div>;

  return (
    <div className="min-h-screen bg-background text-on-background pb-24">
      {/* Header */}
      <header className="p-6 flex items-center gap-4 sticky top-0 bg-background/80 backdrop-blur-md z-30 border-b border-white/5">
        <Link href="/" className="p-2 hover:bg-white/5 rounded-full text-on-surface-variant transition-colors">
          <ArrowLeft size={24} />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-white">Tartozások elszámolása</h1>
          <p className="text-[10px] font-bold text-primary uppercase tracking-widest">Közös teherviselés</p>
        </div>
      </header>

      <main className="p-6 space-y-8 max-w-2xl mx-auto">
        {/* Summary Cards */}
        <section className="space-y-4">
           <h2 className="text-xs font-bold text-on-surface-variant uppercase tracking-widest px-1">Aktuális Egyenleg</h2>
           {summary.length === 0 ? (
             <div className="custom-glass p-8 rounded-3xl text-center">
                <CheckCircle2 size={48} className="mx-auto text-secondary mb-4 opacity-50" />
                <p className="text-on-surface-variant">Mindenki ki van fizetve! 🙌</p>
             </div>
           ) : (
             summary.map((s, idx) => (
               <div key={idx} className="custom-glass p-6 rounded-3xl flex flex-col gap-6">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-4">
                       <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${s.netAmount < 0 ? 'bg-error/10 text-error' : 'bg-secondary/10 text-secondary'}`}>
                          <Users size={24} />
                       </div>
                       <div>
                          <p className="font-bold text-lg">{s.name}</p>
                          <p className="text-xs text-on-surface-variant">
                            {s.netAmount < 0 ? 'Te tartozol neki' : 'Ő tartozik neked'}
                          </p>
                       </div>
                    </div>
                    <div className={`text-2xl font-bold ${s.netAmount < 0 ? 'text-on-surface' : 'text-secondary'}`}>
                       {Math.abs(s.netAmount).toLocaleString()} <span className="text-sm font-normal opacity-60">Ft</span>
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => handleSettle(s.userId)}
                    className="w-full bg-white/5 hover:bg-white/10 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-2 transition-all border border-white/5"
                  >
                    <HandCoins size={20} /> Elszámolás (Settle Up)
                  </button>
               </div>
             ))
           )}
        </section>

        {/* Detailed History */}
        <section className="space-y-4">
           <h2 className="text-xs font-bold text-on-surface-variant uppercase tracking-widest px-1">Részletes tranzakciók</h2>
           <div className="space-y-3">
              {debts.map((debt, idx) => {
                const imTheDebtor = debt.fromUserId._id === (session?.user as any)?.id;
                return (
                  <div key={idx} className="custom-glass p-4 rounded-2xl flex items-center justify-between border-l-4 border-white/5">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-surface-variant flex items-center justify-center text-on-surface-variant">
                         <Receipt size={20} />
                      </div>
                      <div>
                        <p className="text-sm font-bold">{debt.note || 'Közös költés'}</p>
                        <p className="text-[10px] text-on-surface-variant flex items-center gap-1">
                          <Clock size={10} /> {new Date(debt.createdAt).toLocaleDateString('hu-HU')}
                        </p>
                      </div>
                    </div>
                    <div className={`text-right ${imTheDebtor ? 'text-error' : 'text-secondary'}`}>
                       <p className="font-bold text-sm">{imTheDebtor ? '-' : '+'} {debt.amount.toLocaleString()} Ft</p>
                       <p className="text-[10px] uppercase font-bold tracking-tighter opacity-50">
                          {imTheDebtor ? 'Tartozol' : 'Kaptál'}
                       </p>
                    </div>
                  </div>
                );
              })}
           </div>
        </section>
      </main>
    </div>
  );
}
