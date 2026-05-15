'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { 
  TrendingUp, 
  Briefcase, 
  ArrowLeft,
  Filter,
  Download
} from 'lucide-react';
import Link from 'next/link';
import TrendChart from './TrendChart';

export default function VitaStepsClient() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchVitaData = useCallback(async () => {
    try {
      const res = await fetch('/api/reports?type=business');
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const isAdam = (session?.user as any)?.username === 'adam';

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    } else if (status === 'authenticated') {
      if (!isAdam) {
        router.push('/');
      } else {
        fetchVitaData();
      }
    }
  }, [status, isAdam, fetchVitaData]);

  if (loading || !isAdam) return <div className="flex items-center justify-center h-screen bg-background text-primary animate-pulse font-bold text-xl">FinSpace...</div>;

  const businessIncome = data?.monthly?.income || 0;
  const businessExpense = data?.monthly?.expense || 0;
  const businessProfit = businessIncome - businessExpense;

  return (
    <div className="min-h-screen bg-background text-on-background pb-32">
      {/* Header */}
      <header className="p-6 flex items-center justify-between sticky top-0 bg-background/80 backdrop-blur-md z-30 border-b border-white/5">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-2 hover:bg-white/5 rounded-full text-on-surface-variant transition-colors">
            <ArrowLeft size={24} />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white">VitaSteps</h1>
            <p className="text-[10px] font-bold text-secondary uppercase tracking-[0.2em]">Üzleti Vezérlőpult</p>
          </div>
        </div>
        <div className="flex gap-2">
           <button className="p-2 hover:bg-white/5 rounded-xl text-on-surface-variant transition-colors">
            <Filter size={20} />
          </button>
          <button className="p-2 hover:bg-white/5 rounded-xl text-on-surface-variant transition-colors">
            <Download size={20} />
          </button>
        </div>
      </header>

      <main className="p-6 space-y-8 max-w-4xl mx-auto">
        {/* KPI Cards */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
           <div className="custom-glass p-6 rounded-2xl border-l-4 border-secondary">
              <p className="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">Havi Bevétel</p>
              <h3 className="text-2xl font-bold text-secondary">+{businessIncome.toLocaleString()} Ft</h3>
           </div>
           <div className="custom-glass p-6 rounded-2xl border-l-4 border-error">
              <p className="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">Havi Kiadás</p>
              <h3 className="text-2xl font-bold text-on-surface">-{businessExpense.toLocaleString()} Ft</h3>
           </div>
           <div className="custom-glass p-6 rounded-2xl border-l-4 border-primary">
              <p className="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">Üzleti Eredmény</p>
              <h3 className="text-2xl font-bold text-primary">{businessProfit.toLocaleString()} Ft</h3>
           </div>
        </section>

        {/* Growth Chart */}
        <section className="custom-glass p-6 rounded-3xl min-h-[350px]">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-bold">Üzleti Növekedés</h3>
              <p className="text-xs text-on-surface-variant italic">Visszatérő árbevétel trend</p>
            </div>
            <div className="flex items-center gap-2 text-secondary text-sm font-bold bg-secondary/10 px-3 py-1 rounded-full">
              <TrendingUp size={16} />
              <span>Célkitűzés teljesül</span>
            </div>
          </div>
          <TrendChart data={data?.trend || []} />
        </section>

        {/* Business Categories */}
        <section className="space-y-4">
          <h3 className="text-lg font-bold px-1">Üzleti Költségek Bontása</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {data?.categories?.map((cat: any, idx: number) => (
              <div key={idx} className="custom-glass p-4 rounded-2xl flex items-center justify-between transition-all hover:bg-white/5">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-xl">
                    {cat.icon || '💼'}
                  </div>
                  <div>
                    <p className="font-bold text-sm">{cat.name}</p>
                    <p className="text-[10px] text-on-surface-variant font-medium">{cat.count} db tranzakció</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold text-sm">{cat.total.toLocaleString()} Ft</p>
                  <p className="text-[10px] text-secondary font-bold">{cat.percentage}%</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
