'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  AreaChart, 
  Area 
} from 'recharts';
import { 
  LayoutDashboard, 
  PieChart as PieChartIcon, 
  Briefcase, 
  CreditCard, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  ArrowUpRight,
  TrendingDown,
  Bell
} from 'lucide-react';
import Link from 'next/link';

export default function ReportsClient() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    } else if (status === 'authenticated') {
      fetchReports();
    }
  }, [status]);

  const fetchReports = async () => {
    try {
      const res = await fetch('/api/reports');
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (status === 'loading' || loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <div className="text-primary font-bold text-2xl animate-pulse">FinSpace Reports...</div>
      </div>
    );
  }

  const totalExpense = data?.breakdown?.reduce((sum: number, item: any) => sum + item.value, 0) || 0;

  const isAdam = (session?.user as any)?.username === 'adam';

  return (
    <div className="min-h-screen bg-background pb-32 text-on-surface">
      {/* Top App Bar */}
      <header className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-md border-b border-white/10 flex items-center justify-between px-container-margin h-16">
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 rounded-full overflow-hidden border border-white/10 flex items-center justify-center bg-surface-variant">
             <img src={`https://ui-avatars.com/api/?name=${session?.user?.name}&background=c5c0ff&color=150067`} alt="User" />
          </div>
          <h1 className="text-xl font-bold text-primary">FinSpace</h1>
        </div>
      </header>

      <main className="pt-24 px-container-margin max-w-[1200px] mx-auto space-y-gutter-md">
        {/* Header & Date Selector */}
        <section className="flex flex-col md:flex-row md:items-end justify-between gap-stack-lg">
          <div>
            <h1 className="text-3xl font-bold text-on-surface">Kimutatások</h1>
            <p className="text-sm text-on-surface-variant">Pénzügyi teljesítmény és elemzések</p>
          </div>
          <div className="flex items-center gap-2 bg-surface-container p-1 rounded-xl border border-white/5">
            <button className="p-2 hover:bg-surface-variant rounded-lg text-primary transition-colors">
              <ChevronLeft size={20} />
            </button>
            <span className="px-4 text-sm font-bold text-on-surface">Aktuális időszak</span>
            <button className="p-2 hover:bg-surface-variant rounded-lg text-primary transition-colors">
              <ChevronRight size={20} />
            </button>
          </div>
        </section>

        {/* Bento Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter-md">
          
          {/* Monthly P/L Bar Chart */}
          <div className="md:col-span-8 custom-glass p-6 rounded-2xl flex flex-col gap-6">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-xl font-bold text-on-surface">Bevételek és Kiadások</h3>
                <p className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold">Kategóriánkénti bontás</p>
              </div>
              <div className="flex gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-secondary"></div>
                  <span className="text-[10px] font-bold text-on-surface-variant uppercase">Bevétel</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-error"></div>
                  <span className="text-[10px] font-bold text-on-surface-variant uppercase">Kiadás</span>
                </div>
              </div>
            </div>
            
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.monthlyPL}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis 
                    dataKey="name" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#192029', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                    itemStyle={{ fontSize: '12px' }}
                  />
                  <Bar dataKey="income" fill="#4de082" radius={[4, 4, 0, 0]} barSize={12} />
                  <Bar dataKey="expense" fill="#ffb4ab" radius={[4, 4, 0, 0]} barSize={12} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Category Breakdown (Donut Chart) */}
          <div className="md:col-span-4 custom-glass p-6 rounded-2xl flex flex-col items-center gap-6">
            <div className="w-full text-left">
              <h3 className="text-xl font-bold text-on-surface">Megoszlás</h3>
              <p className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold">Költések aránya</p>
            </div>
            
            <div className="relative w-48 h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data?.breakdown}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {data?.breakdown?.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.color || '#c5c0ff'} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-2xl font-bold text-on-surface">100%</span>
                <span className="text-[10px] text-on-surface-variant font-bold uppercase">Összesen</span>
              </div>
            </div>

            <div className="w-full space-y-3">
              {data?.breakdown?.slice(0, 3).map((item: any, idx: number) => (
                <div key={idx} className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }}></div>
                    <span className="text-sm font-medium text-on-surface">{item.name}</span>
                  </div>
                  <span className="text-xs font-bold text-on-surface-variant">
                    {Math.round((item.value / totalExpense) * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 12-Month Trend */}
          <div className="md:col-span-12 custom-glass p-6 rounded-2xl flex flex-col gap-6">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-xl font-bold text-on-surface">Nettó Trend</h3>
                <p className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold">Vagyoni növekedés</p>
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold text-secondary">
                  +{data?.trend?.reduce((sum: number, i: any) => sum + i.net, 0).toLocaleString()} Ft
                </span>
                <p className="text-[10px] text-on-surface-variant font-bold uppercase tracking-widest">Éves Nettó Növekedés</p>
              </div>
            </div>
            
            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.trend}>
                  <defs>
                    <linearGradient id="colorNet" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#c5c0ff" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#c5c0ff" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis 
                    dataKey="name" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                  />
                  <Tooltip />
                  <Area type="monotone" dataKey="net" stroke="#c5c0ff" strokeWidth={3} fillOpacity={1} fill="url(#colorNet)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* VitaSteps Highlight Card - Csak Adámnak */}
          {isAdam && (
            <div className="md:col-span-12 custom-glass p-6 rounded-2xl relative overflow-hidden group hover:bg-white/5 transition-all">
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-secondary"></div>
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="flex items-center gap-6">
                  <div className="w-16 h-16 rounded-2xl bg-secondary/10 flex items-center justify-center text-secondary shadow-inner">
                    <Briefcase size={32} />
                  </div>
                  <div>
                    <h4 className="text-xl font-bold text-on-surface">VitaSteps Áttekintés</h4>
                    <p className="text-sm text-on-surface-variant">Az üzleti kiadásaid 12%-kal csökkentek ebben a negyedévben.</p>
                  </div>
                </div>
                <Link 
                  href="/vitasteps"
                  className="px-8 py-3 bg-secondary text-background rounded-xl font-bold hover:opacity-90 transition-opacity active:scale-95"
                >
                  Üzleti Stratégia Megnyitása
                </Link>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
