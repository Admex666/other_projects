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
  Bell,
  TrendingUp,
  Target,
  ArrowRight,
  Users,
  Check,
  ChevronDown
} from 'lucide-react';
import TrendChart from './TrendChart';
import VirtualPockets from './VirtualPockets';
import TransactionModal from './TransactionModal';
import PocketModal from './PocketModal';
import PocketTransferModal from './PocketTransferModal';
import PWAInstallPrompt from './PWAInstallPrompt';
import Link from 'next/link';
import { useSync } from '@/lib/hooks/useSync';
import { useCallback } from 'react';

export default function DashboardClient() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'personal' | 'business'>('personal');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<any>(null);
  const [isPocketModalOpen, setIsPocketModalOpen] = useState(false);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [debts, setDebts] = useState<any[]>([]);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch('/api/dashboard');
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDebts = useCallback(async () => {
    try {
      const res = await fetch('/api/debts/summary');
      const json = await res.json();
      setDebts(json);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useSync(useCallback((event) => {
    console.log('Real-time update received:', event);
    fetchDashboard();
    fetchDebts();
  }, [fetchDashboard, fetchDebts]));

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    } else if (status === 'authenticated') {
      fetchDashboard();
      fetchDebts();
    }
  }, [status, fetchDashboard, fetchDebts]);

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

  const totalBalance = data?.accounts?.reduce((sum: number, acc: any) => sum + (Number(acc.balanceInBase) || Number(acc.balance) || 0), 0) || 0;
  const businessBalance = data?.accounts
    ?.filter((acc: any) => acc.isBusinessAccount)
    ?.reduce((sum: number, acc: any) => sum + (Number(acc.balanceInBase) || Number(acc.balance) || 0), 0) || 0;
  const isAdam = (session?.user as any)?.username === 'adam';

  return (
    <div className="min-h-screen bg-background pb-32 text-on-surface">
      {/* Top App Bar */}
      <header className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-md border-b border-white/10 flex items-center justify-between px-container-margin h-16">
        <div className="flex items-center gap-stack-md">
          <div className="w-10 h-10 rounded-full overflow-hidden border border-white/10 flex items-center justify-center bg-surface-variant">
             <img src={`https://ui-avatars.com/api/?name=${session?.user?.name}&background=c5c0ff&color=150067`} alt="User" />
          </div>
          <h1 className="text-xl font-bold text-primary">FinSpace</h1>
        </div>
        <div className="flex items-center gap-2">
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
        <section className="grid grid-cols-1 md:grid-cols-3 gap-gutter-md animate-in fade-in slide-in-from-bottom-4 duration-700">
          {/* Main Portfolio Card */}
          <div className="md:col-span-1 custom-glass p-stack-lg rounded-2xl flex flex-col justify-between overflow-hidden relative min-h-[180px] group hover:border-primary/30 transition-all duration-300">
            <div className="absolute top-0 right-0 p-stack-lg opacity-10 group-hover:scale-110 transition-transform duration-500">
               <Wallet size={80} className="text-primary" />
            </div>
            <div>
              <p className="text-xs text-on-surface-variant uppercase tracking-widest mb-stack-sm font-semibold">Teljes Vagyon</p>
              <h2 className="text-4xl font-bold text-primary leading-none">
                {totalBalance.toLocaleString()} <span className="text-xl font-normal opacity-70">Ft</span>
              </h2>
            </div>
            <div className="mt-stack-lg flex gap-stack-md">
              <div className="flex items-center gap-stack-sm text-secondary text-sm font-semibold">
                <TrendingUp size={16} />
                <span>Aktuális állapot</span>
              </div>
            </div>
          </div>

          {/* Free Balance Card */}
          <div className="md:col-span-1 custom-glass p-stack-lg rounded-2xl flex flex-col justify-between overflow-hidden relative min-h-[180px] bg-secondary/5 border border-secondary/10 group hover:bg-secondary/10 transition-all duration-300 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            <div className="absolute top-0 right-0 p-stack-lg opacity-10 group-hover:rotate-12 transition-transform duration-500">
               <Target size={80} className="text-secondary" />
            </div>
            <div>
              <p className="text-xs text-secondary uppercase tracking-widest mb-stack-sm font-bold">Szabad egyenleg</p>
              <h2 className="text-4xl font-bold text-white leading-none">
                {(data?.freeBalance || 0).toLocaleString()} <span className="text-xl font-normal opacity-70 text-on-surface-variant">Ft</span>
              </h2>
              <p className="text-[10px] text-on-surface-variant mt-2 font-medium">Nincs zsebhez rendelve</p>
            </div>
            <div className="mt-stack-lg">
               <button 
                onClick={() => setIsTransferModalOpen(true)}
                className="text-xs font-bold text-secondary flex items-center gap-2 hover:translate-x-1 transition-transform"
               >
                 Beosztás zsebekbe <ArrowRight size={14} />
               </button>
            </div>
          </div>

          {/* Monthly Flow Card */}
          <div className="custom-glass p-stack-lg rounded-2xl flex flex-col justify-center gap-stack-md animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-bold text-on-surface-variant uppercase tracking-wider">Havi Forgalom</span>
              <span className="text-xs text-on-surface font-medium">Aktuális hónap</span>
            </div>
            <div className="space-y-stack-md">
              <div className="flex justify-between text-sm">
                <span className="text-on-surface-variant">Bevétel</span>
                <span className="text-secondary font-bold">+{data?.monthly.income.toLocaleString()} Ft</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-on-surface-variant">Kiadás</span>
                <span className="text-error font-bold">-{data?.monthly.expense.toLocaleString()} Ft</span>
              </div>
            </div>
            {/* Progress Bar */}
            <div className="h-2 w-full bg-surface-variant rounded-full overflow-hidden flex mt-2">
              <div 
                className="h-full bg-secondary transition-all duration-500" 
                style={{ width: `${(data?.monthly.income / (data?.monthly.income + data?.monthly.expense)) * 100 || 0}%` }}
              ></div>
              <div 
                className="h-full bg-error transition-all duration-500" 
                style={{ width: `${(data?.monthly.expense / (data?.monthly.income + data?.monthly.expense)) * 100 || 0}%` }}
              ></div>
            </div>
            <p className="text-[10px] text-on-surface-variant text-center mt-1 font-bold uppercase tracking-tighter">
              Egyenleg: {data?.monthly.profit.toLocaleString()} Ft
            </p>
          </div>
        </section>

        {/* Dual Cards: Personal vs VitaSteps - Csak Adámnak mutatjuk mindkettőt */}
        <section className={`grid grid-cols-1 ${isAdam ? 'md:grid-cols-2' : ''} gap-gutter-md`}>
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

          {isAdam && (
            <div 
              onClick={() => setView('business')}
              className={`custom-glass p-gutter-md rounded-2xl flex items-center gap-gutter-md hover:bg-surface-variant/20 transition-all cursor-pointer border-l-4 ${view === 'business' ? 'border-secondary' : 'border-transparent'}`}
            >
              <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center text-secondary">
                <Briefcase size={24} />
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">VitaSteps Business</p>
                    <p className="text-2xl font-bold">{businessBalance.toLocaleString()} Ft</p>
                  </div>
                  <Link href="/vitasteps" className="text-[10px] font-bold text-secondary bg-secondary/10 px-2 py-1 rounded-md hover:bg-secondary/20 transition-colors">
                    RÉSZLETEK
                  </Link>
                </div>
              </div>
            </div>
          )}
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

           {/* Debt Summary */}
           {view === 'personal' && debts.length > 0 && (
             <div className="space-y-3">
               <div className="flex justify-between items-center px-1">
                 <h3 className="text-xs font-bold text-on-surface-variant uppercase tracking-widest">Tartozások</h3>
                 <Link href="/debts" className="text-[10px] font-bold text-primary hover:underline uppercase tracking-widest">
                   Részletek
                 </Link>
               </div>
               {debts.map((debt, idx) => (
                 <div key={idx} className={`p-4 rounded-2xl flex items-center justify-between border-l-4 ${debt.netAmount < 0 ? 'bg-error/5 border-error' : 'bg-secondary/5 border-secondary'}`}>
                   <div className="flex items-center gap-3">
                     <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${debt.netAmount < 0 ? 'bg-error/10 text-error' : 'bg-secondary/10 text-secondary'}`}>
                       <Users size={20} />
                     </div>
                     <div>
                       <p className="text-sm font-bold">
                         {debt.netAmount < 0 ? `Te tartozol neki: ${debt.name}` : `${debt.name} tartozik neked`}
                       </p>
                       <p className="text-[10px] text-on-surface-variant font-medium">Közös elszámolás</p>
                     </div>
                   </div>
                   <div className={`text-lg font-bold ${debt.netAmount < 0 ? 'text-on-surface' : 'text-secondary'}`}>
                     {Math.abs(debt.netAmount).toLocaleString()} <span className="text-xs font-normal opacity-60">Ft</span>
                   </div>
                 </div>
               ))}
             </div>
           )}

           {/* Virtual Pockets */}
           {view === 'personal' && (
             <VirtualPockets 
               pockets={data?.pockets || []} 
               onCreate={() => setIsPocketModalOpen(true)}
               onTransfer={() => setIsTransferModalOpen(true)}
             />
           )}

           {/* Accounts Carousel */}
           <div className="space-y-3">
             <div className="flex justify-between items-center px-1">
               <h3 className="font-bold text-lg">Számlák</h3>
               <button className="text-primary text-xs font-bold hover:underline underline-offset-4">Összes</button>
             </div>
             <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide -mx-4 px-4">
                {data?.accounts
                  .filter((acc: any) => view === 'personal' ? true : acc.isBusinessAccount)
                  .map((acc: any) => (
                  <div key={acc._id} className="custom-glass min-w-[160px] p-4 rounded-2xl border-b-4 shadow-lg hover:translate-y-[-4px] transition-all" style={{ borderBottomColor: acc.color }}>
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4" style={{ backgroundColor: acc.color + '20', color: acc.color }}>
                      <CreditCard size={20} />
                    </div>
                    <p className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider truncate mb-1">{acc.name}</p>
                    <p className="text-lg font-bold">{(acc.balance || 0).toLocaleString()} <span className="text-xs font-normal opacity-60">{acc.currency}</span></p>
                  </div>
                ))}
             </div>
           </div>

           {/* Recent Transactions */}
           <div className="space-y-4 pb-12">
             <div className="flex justify-between items-center px-1">
               <h3 className="font-bold text-lg">Legutóbbi Tranzakciók</h3>
               <Link href="/transactions" className="text-primary text-xs font-bold hover:underline underline-offset-4">Összes</Link>
             </div>
             <div className="space-y-3">
                {data?.recentTransactions
                  .filter((tx: any) => view === 'personal' ? true : tx.isBusinessTransaction)
                  .map((tx: any) => (
                  <div 
                    key={tx._id} 
                    onClick={() => { setSelectedTransaction(tx); setIsEditModalOpen(true); }}
                    className={`custom-glass p-4 rounded-2xl flex items-center justify-between border-l-4 transition-all hover:bg-white/5 cursor-pointer ${tx.isBusinessTransaction ? 'border-secondary' : 'border-transparent'}`}
                  >
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

      {/* Pocket Modal */}
      <PocketModal 
        isOpen={isPocketModalOpen}
        onClose={() => setIsPocketModalOpen(false)}
        onSuccess={fetchDashboard}
        accounts={data?.accounts || []}
      />

      <PWAInstallPrompt />

      {/* Edit Transaction Modal */}
      <TransactionModal 
        isOpen={isEditModalOpen}
        onClose={() => { setIsEditModalOpen(false); setSelectedTransaction(null); }}
        onSuccess={fetchDashboard}
        editTransaction={selectedTransaction}
      />

      {/* Pocket Transfer Modal */}
      <PocketTransferModal
        isOpen={isTransferModalOpen}
        onClose={() => setIsTransferModalOpen(false)}
        onSuccess={fetchDashboard}
        pockets={data?.pockets || []}
        freeBalance={data?.freeBalance || 0}
      />
    </div>
  );
}
