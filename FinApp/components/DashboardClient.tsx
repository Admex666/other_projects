'use client';

import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { 
  LayoutDashboard,
  PieChart,
  Settings,
  LogOut,
  Plus,
  Briefcase,
  Wallet,
  CreditCard,
  Bell
} from 'lucide-react';
import TrendChart from './TrendChart';
import VirtualPockets from './VirtualPockets';
import TransactionModal from './TransactionModal';

export default function DashboardClient() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'personal' | 'business'>('personal');
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    } else if (status === 'authenticated') {
      fetchDashboard();
    }
  }, [status]);

  const fetchDashboard = async () => {
    try {
      const res = await fetch('/api/dashboard');
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
        <div className="text-primary font-bold text-2xl animate-pulse">FinSpace...</div>
      </div>
    );
  }

  if (data?.error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-background gap-4">
        <p className="text-error">Hiba: {data.error}</p>
        <button onClick={() => signOut()} className="text-on-surface-variant underline">Kijelentkezés</button>
      </div>
    );
  }

  const totalBalance = data?.accounts?.reduce((sum: number, acc: any) => sum + (acc.balanceInBase || acc.balance), 0) || 0;
  const businessBalance = data?.accounts
    ?.filter((acc: any) => acc.isBusinessAccount)
    ?.reduce((sum: number, acc: any) => sum + (acc.balanceInBase || acc.balance), 0) || 0;

  return (
    <div className="min-h-screen bg-background pb-24 text-on-surface">
      {/* Top App Bar */}
      <header className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-md border-b border-white/10 flex items-center justify-between px-container-margin h-16">
        <div className="flex items-center gap-stack-md">
          <div className="w-10 h-10 rounded-full overflow-hidden border border-white/10 flex items-center justify-center bg-surface-variant">
             <img src={`https://ui-avatars.com/api/?name=${session?.user?.name}&background=c5c0ff&color=150067`} alt="User" />
          </div>
          <h1 className="text-xl font-bold text-primary">FinApp</h1>
        </div>
        <div className="flex items-center gap-2">
          <button className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface-variant transition-colors text-primary">
            <Bell size={20} />
          </button>
          <button 
            onClick={() => signOut()}
            className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface-variant transition-colors text-on-surface-variant"
          >
            <LogOut size={20} />
          </button>
        </div>
      </header>

      <main className="mt-20 px-container-margin max-w-[1200px] mx-auto w-full space-y-gutter-md">
        {/* Total Balance Section */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-gutter-md">
          {/* Main Portfolio Card */}
          <div className="md:col-span-2 custom-glass p-stack-lg rounded-2xl flex flex-col justify-between overflow-hidden relative min-h-[180px]">
            <div className="absolute top-0 right-0 p-stack-lg opacity-10">
               <Wallet size={80} className="text-primary" />
            </div>
            <div>
              <p className="text-xs text-on-surface-variant uppercase tracking-widest mb-stack-sm font-semibold">Total Portfolio Value</p>
              <h2 className="text-5xl font-bold text-primary leading-none">
                {totalBalance.toLocaleString()} <span className="text-2xl font-normal opacity-70">Ft</span>
              </h2>
            </div>
            <div className="mt-stack-lg flex gap-stack-md">
              <div className="flex items-center gap-stack-sm text-secondary text-sm font-semibold">
                <TrendingUp size={16} />
                <span>+4.2% ebben a hónapban</span>
              </div>
            </div>
          </div>

          {/* Monthly Flow Card */}
          <div className="custom-glass p-stack-lg rounded-2xl flex flex-col justify-center gap-stack-md">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-bold text-on-surface-variant uppercase tracking-wider">Havi Forgalom</span>
              <span className="text-xs text-on-surface font-medium">Május 2026</span>
            </div>
            <div className="space-y-stack-md">
              <div className="flex justify-between text-sm">
                <span className="text-on-surface-variant">Bevétel</span>
                <span className="text-secondary font-bold">{data?.monthly.income.toLocaleString()} Ft</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-on-surface-variant">Kiadás</span>
                <span className="text-error font-bold">{data?.monthly.expense.toLocaleString()} Ft</span>
              </div>
            </div>
            {/* Progress Bar */}
            <div className="h-2 w-full bg-surface-variant rounded-full overflow-hidden flex mt-2">
              <div 
                className="h-full bg-secondary transition-all duration-500" 
                style={{ width: `${(data?.monthly.income / (data?.monthly.income + data?.monthly.expense)) * 100}%` }}
              ></div>
              <div 
                className="h-full bg-error transition-all duration-500" 
                style={{ width: `${(data?.monthly.expense / (data?.monthly.income + data?.monthly.expense)) * 100}%` }}
              ></div>
            </div>
            <p className="text-[10px] text-on-surface-variant text-center mt-1">
              Net profit: {data?.monthly.profit.toLocaleString()} Ft
            </p>
          </div>
        </section>

        {/* Dual Cards: Personal vs VitaSteps */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-gutter-md">
          <div 
            onClick={() => setView('personal')}
            className={`custom-glass p-gutter-md rounded-2xl flex items-center gap-gutter-md hover:bg-surface-variant/20 transition-all cursor-pointer border-l-4 ${view === 'personal' ? 'border-primary' : 'border-transparent'}`}
          >
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
              <Wallet size={24} />
            </div>
            <div className="flex-1">
              <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Személyes Egyenleg</p>
              <p className="text-2xl font-bold">{(totalBalance - businessBalance).toLocaleString()} Ft</p>
            </div>
          </div>

          <div 
            onClick={() => setView('business')}
            className={`custom-glass p-gutter-md rounded-2xl flex items-center gap-gutter-md hover:bg-surface-variant/20 transition-all cursor-pointer border-l-4 ${view === 'business' ? 'border-secondary' : 'border-transparent'}`}
          >
            <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center text-secondary">
              <Briefcase size={24} />
            </div>
            <div className="flex-1">
              <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">VitaSteps Business</p>
              <p className="text-2xl font-bold">{businessBalance.toLocaleString()} Ft</p>
            </div>
          </div>
        </section>

        {/* Dynamic Section Based on View */}
        <section className="space-y-gutter-md">
           {/* Trend Chart Card */}
           <div className="custom-glass p-stack-lg rounded-2xl min-h-[250px]">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-lg">Pénzügyi Trend</h3>
                <span className="text-xs text-on-surface-variant">Utolsó 6 hónap</span>
              </div>
              <TrendChart data={data?.trend || []} />
           </div>

           {/* Virtual Pockets */}
           {view === 'personal' && <VirtualPockets pockets={data?.pockets || []} />}

           {/* Accounts Carousel */}
           <div className="space-y-3">
             <div className="flex justify-between items-center px-1">
               <h3 className="font-bold text-lg">Számlák</h3>
               <button className="text-primary text-xs font-bold hover:underline">Mind</button>
             </div>
             <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide -mx-4 px-4">
                {data?.accounts
                  .filter((acc: any) => view === 'personal' ? true : acc.isBusinessAccount)
                  .map((acc: any) => (
                  <div key={acc._id} className="custom-glass min-w-[160px] p-4 rounded-2xl border-b-4" style={{ borderBottomColor: acc.color }}>
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4" style={{ backgroundColor: acc.color + '20', color: acc.color }}>
                      <CreditCard size={20} />
                    </div>
                    <p className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider truncate mb-1">{acc.name}</p>
                    <p className="text-lg font-bold">{acc.balance.toLocaleString()} <span className="text-xs font-normal opacity-60">{acc.currency}</span></p>
                  </div>
                ))}
             </div>
           </div>

           {/* Recent Transactions */}
           <div className="space-y-4">
             <div className="flex justify-between items-center px-1">
               <h3 className="font-bold text-lg">Legutóbbi Tranzakciók</h3>
               <button className="text-primary text-xs font-bold hover:underline">Mind</button>
             </div>
             <div className="space-y-3">
                {data?.recentTransactions
                  .filter((tx: any) => view === 'personal' ? true : tx.isBusinessTransaction)
                  .map((tx: any) => (
                  <div key={tx._id} className={`custom-glass p-4 rounded-2xl flex items-center justify-between border-l-4 ${tx.isBusinessTransaction ? 'border-secondary' : 'border-transparent'}`}>
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-surface-variant flex items-center justify-center text-xl shadow-inner">
                        {tx.categoryId?.icon || (tx.type === 'income' ? '💰' : '💸')}
                      </div>
                      <div>
                        <p className="font-bold text-sm">{tx.note || tx.categoryId?.name || 'Tranzakció'}</p>
                        <p className="text-[10px] text-on-surface-variant font-medium">
                          {new Date(tx.date).toLocaleDateString('hu-HU')} • {tx.accountId?.name}
                        </p>
                      </div>
                    </div>
                    <div className={`font-bold text-lg ${tx.type === 'income' ? 'text-secondary' : 'text-on-surface'}`}>
                      {tx.type === 'income' ? '+' : '-'} {tx.amount.toLocaleString()} <span className="text-xs font-normal opacity-50">Ft</span>
                    </div>
                  </div>
                ))}
             </div>
           </div>
        </section>
      </main>

      {/* FAB */}
      <button 
        onClick={() => setIsModalOpen(true)}
        className="fixed bottom-24 right-6 w-16 h-16 bg-primary text-background rounded-full shadow-2xl flex items-center justify-center z-50 active:scale-95 transition-transform duration-150 hover:scale-110"
      >
        <Plus size={32} />
      </button>

      {/* Transaction Modal */}
      <TransactionModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={fetchDashboard}
        accounts={data?.accounts || []}
      />

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 w-full z-50 bg-background/90 backdrop-blur-lg border-t border-white/10 flex justify-around items-center h-20 px-4">
        <button className="flex flex-col items-center justify-center text-primary">
          <LayoutDashboard size={24} />
          <span className="text-[10px] font-bold mt-1">Home</span>
        </button>
        <button className="flex flex-col items-center justify-center text-on-surface-variant hover:text-primary transition-colors">
          <PieChart size={24} />
          <span className="text-[10px] font-bold mt-1">Reports</span>
        </button>
        <button 
          onClick={() => setView('business')}
          className={`flex flex-col items-center justify-center transition-colors ${view === 'business' ? 'text-secondary' : 'text-on-surface-variant hover:text-secondary'}`}
        >
          <Briefcase size={24} />
          <span className="text-[10px] font-bold mt-1">VitaSteps</span>
        </button>
        <button className="flex flex-col items-center justify-center text-on-surface-variant hover:text-primary transition-colors">
          <CreditCard size={24} />
          <span className="text-[10px] font-bold mt-1">Accounts</span>
        </button>
        <button className="flex flex-col items-center justify-center text-on-surface-variant hover:text-primary transition-colors">
          <Settings size={24} />
          <span className="text-[10px] font-bold mt-1">Settings</span>
        </button>
      </nav>
    </div>
  );
}

function TrendingUp({ size, className }: { size: number, className?: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
      <polyline points="17 6 23 6 23 12"></polyline>
    </svg>
  );
}
