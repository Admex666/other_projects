'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, Plus, PieChart, Briefcase, Settings } from 'lucide-react';
import { useSession } from 'next-auth/react';
import { useState } from 'react';
import TransactionModal from './TransactionModal';

export default function Navigation() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Csak "adam" látja a VitaSteps-et
  const isAdam = (session?.user as any)?.username === 'adam';

  // Ha nincs bejelentkezve, ne mutassunk menüt (pl. login oldalon)
  if (!session) return null;
  if (pathname === '/auth/signin') return null;

  return (
    <>
      <nav className="fixed bottom-0 w-full z-[100] bg-background/90 backdrop-blur-lg border-t border-white/10 flex justify-between items-center h-20 px-4 pb-2">
        <Link 
          href="/"
          className={`flex-1 flex flex-col items-center justify-center transition-colors ${pathname === '/' ? 'text-primary' : 'text-on-surface-variant hover:text-primary'}`}
        >
          <LayoutDashboard size={24} />
          <span className="text-[10px] font-bold mt-1">Főoldal</span>
        </Link>
        
        <Link 
          href="/debts" 
          className={`flex-1 flex flex-col items-center justify-center transition-colors ${pathname === '/debts' ? 'text-primary' : 'text-on-surface-variant hover:text-primary'}`}
        >
          <Users size={24} />
          <span className="text-[10px] font-bold mt-1">Közös</span>
        </Link>

        <div className="flex-1 flex justify-center">
          <div className="relative -mt-10">
            <button 
              onClick={() => setIsModalOpen(true)}
              className="w-14 h-14 bg-primary text-background rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(var(--primary-rgb),0.4)] hover:scale-110 active:scale-95 transition-all"
            >
              <Plus size={32} />
            </button>
          </div>
        </div>

        <Link 
          href="/reports" 
          className={`flex-1 flex flex-col items-center justify-center transition-colors ${pathname === '/reports' ? 'text-primary' : 'text-on-surface-variant hover:text-primary'}`}
        >
          <PieChart size={24} />
          <span className="text-[10px] font-bold mt-1">Elemzés</span>
        </Link>

        {isAdam ? (
          <Link 
            href="/vitasteps" 
            className={`flex-1 flex flex-col items-center justify-center transition-colors ${pathname === '/vitasteps' ? 'text-secondary' : 'text-on-surface-variant hover:text-secondary'}`}
          >
            <Briefcase size={24} />
            <span className="text-[10px] font-bold mt-1">VitaSteps</span>
          </Link>
        ) : (
          <Link 
            href="/settings" 
            className={`flex-1 flex flex-col items-center justify-center transition-colors ${pathname === '/settings' ? 'text-primary' : 'text-on-surface-variant hover:text-primary'}`}
          >
            <Settings size={24} />
            <span className="text-[10px] font-bold mt-1">Beállítások</span>
          </Link>
        )}
      </nav>

      {isAdam && (
        <div className="fixed bottom-24 right-4 z-[100]">
           <Link 
            href="/settings" 
            className="w-12 h-12 bg-surface-variant text-on-surface-variant rounded-full flex items-center justify-center shadow-lg hover:text-primary transition-colors"
          >
            <Settings size={20} />
          </Link>
        </div>
      )}

      <TransactionModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSuccess={() => window.location.reload()} 
      />
    </>
  );
}
