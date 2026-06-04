'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Plus } from 'lucide-react';
import TransactionModal from './TransactionModal';

export default function TransactionsClient() {
  const router = useRouter();
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTransaction, setSelectedTransaction] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchTransactions = useCallback(async () => {
    try {
      const res = await fetch('/api/transactions');
      const data = await res.json();
      if (Array.isArray(data)) {
        setTransactions(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  const handleTransactionClick = (tx: any) => {
    setSelectedTransaction(tx);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedTransaction(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background text-primary animate-pulse font-bold">
        Betöltés...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-32 text-on-surface">
      <header className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-md border-b border-white/10 flex items-center justify-between px-container-margin h-16">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push('/dashboard')}
            className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface-variant transition-colors text-on-surface-variant"
          >
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-xl font-bold text-white">Összes Tranzakció</h1>
        </div>
      </header>

      <main className="mt-20 px-container-margin max-w-[800px] mx-auto w-full space-y-4">
        {transactions.map((tx: any) => (
          <div 
            key={tx._id} 
            onClick={() => handleTransactionClick(tx)}
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
              {tx.type === 'income' ? '+' : '-'} {tx.amount.toLocaleString()} <span className="text-xs font-normal opacity-50">{tx.currency}</span>
            </div>
          </div>
        ))}

        {transactions.length === 0 && (
          <div className="text-center text-on-surface-variant pt-10">
            Nincsenek tranzakciók.
          </div>
        )}
      </main>

      {/* Floating Action Button */}
      <button 
        onClick={() => {
          setSelectedTransaction(null);
          setIsModalOpen(true);
        }}
        className="fixed bottom-6 right-6 w-14 h-14 bg-primary text-background rounded-full flex items-center justify-center shadow-lg shadow-primary/30 hover:scale-110 transition-transform z-40"
      >
        <Plus size={24} />
      </button>

      <TransactionModal 
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSuccess={fetchTransactions}
        editTransaction={selectedTransaction}
      />
    </div>
  );
}
