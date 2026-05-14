'use client';

import { useState, useEffect } from 'react';
import { 
  X, 
  ChevronDown, 
  Calendar, 
  Tag, 
  CreditCard, 
  FileText, 
  Briefcase, 
  Target,
  Check,
  Loader2
} from 'lucide-react';

interface TransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  accounts: any[];
  pockets?: any[];
}

export default function TransactionModal({ isOpen, onClose, onSuccess, accounts, pockets = [] }: TransactionModalProps) {
  const [type, setType] = useState<'expense' | 'income'>('expense');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('HUF');
  const [accountId, setAccountId] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [categories, setCategories] = useState<any[]>([]);
  const [note, setNote] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [isBusiness, setIsBusiness] = useState(false);
  const [usePocket, setUsePocket] = useState(false);
  const [virtualPocketId, setVirtualPocketId] = useState('');
  const [splitType, setSplitType] = useState<'equal' | 'custom'>('equal');
  const [customSplitAmount, setCustomSplitAmount] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchCategories();
      if (accounts.length > 0) setAccountId(accounts[0]._id);
    }
  }, [isOpen]);

  const fetchCategories = async () => {
    const res = await fetch('/api/categories');
    const data = await res.json();
    setCategories(data);
    if (data.length > 0) setCategoryId(data[0]._id);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type,
          amount: parseFloat(amount),
          currency,
          accountId,
          categoryId,
          note,
          date,
          isBusinessTransaction: isBusiness,
          virtualPocketId: usePocket ? virtualPocketId : undefined,
          debtAmount: usePocket && splitType === 'custom' ? parseFloat(customSplitAmount) : undefined,
        }),
      });

      if (res.ok) {
        onSuccess();
        onClose();
        // Reset form
        setAmount('');
        setNote('');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-4 bg-background/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-lg bg-surface-container sm:rounded-3xl rounded-t-3xl border border-white/10 shadow-2xl flex flex-col max-h-[90vh] animate-in slide-in-from-bottom duration-300"
      >
        {/* Header */}
        <div className="p-6 flex justify-between items-center border-b border-white/5">
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full text-on-surface-variant transition-colors">
            <X size={24} />
          </button>
          <h2 className="text-xl font-bold text-white">Új {type === 'expense' ? 'Kiadás' : 'Bevétel'}</h2>
          <div className="w-10"></div>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-8 scrollbar-hide">
          {/* Type Selector */}
          <div className="flex bg-background p-1 rounded-2xl border border-white/5">
            <button 
              type="button"
              onClick={() => setType('expense')}
              className={`flex-1 py-3 text-sm font-bold rounded-xl transition-all ${type === 'expense' ? 'bg-surface-variant text-white shadow-lg' : 'text-on-surface-variant'}`}
            >
              Kiadás
            </button>
            <button 
              type="button"
              onClick={() => setType('income')}
              className={`flex-1 py-3 text-sm font-bold rounded-xl transition-all ${type === 'income' ? 'bg-surface-variant text-white shadow-lg' : 'text-on-surface-variant'}`}
            >
              Bevétel
            </button>
          </div>

          {/* Amount Input Section */}
          <div className="text-center space-y-2">
            <p className="text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em]">Tranzakció összege</p>
            <div className="flex items-center justify-center gap-3">
              <input 
                type="number"
                inputMode="decimal"
                placeholder="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
                className="bg-transparent text-6xl font-bold text-white text-center w-full outline-none placeholder:opacity-20"
                autoFocus
              />
              <div className="flex flex-col items-center">
                 <select 
                   value={currency} 
                   onChange={(e) => setCurrency(e.target.value)}
                   className="bg-surface-variant border border-white/10 rounded-lg px-2 py-1 text-xs font-bold text-primary outline-none appearance-none"
                 >
                   <option value="HUF">HUF</option>
                   <option value="EUR">EUR</option>
                   <option value="USD">USD</option>
                 </select>
                 {currency !== 'HUF' && (
                   <span className="text-[10px] text-secondary mt-1 font-medium">≈ {(parseFloat(amount || '0') * 400).toLocaleString()} Ft</span>
                 )}
              </div>
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 gap-4">
            {/* Account & Category */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider flex items-center gap-2">
                  <CreditCard size={12} /> Számla
                </label>
                <div className="relative">
                  <select 
                    value={accountId}
                    onChange={(e) => setAccountId(e.target.value)}
                    className="w-full bg-background border border-white/5 rounded-2xl py-4 pl-4 pr-10 text-sm font-medium appearance-none outline-none focus:border-primary transition-all"
                  >
                    {accounts.map(acc => (
                      <option key={acc._id} value={acc._id}>{acc.name}</option>
                    ))}
                  </select>
                  <ChevronDown size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider flex items-center gap-2">
                  <Tag size={12} /> Kategória
                </label>
                <div className="relative">
                  <select 
                    value={categoryId}
                    onChange={(e) => setCategoryId(e.target.value)}
                    className="w-full bg-background border border-white/5 rounded-2xl py-4 pl-4 pr-10 text-sm font-medium appearance-none outline-none focus:border-primary transition-all"
                  >
                    {categories.map(cat => (
                      <option key={cat._id} value={cat._id}>{cat.name}</option>
                    ))}
                  </select>
                  <ChevronDown size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" />
                </div>
              </div>
            </div>

            {/* Note */}
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider flex items-center gap-2">
                <FileText size={12} /> Megjegyzés
              </label>
              <textarea 
                placeholder="Mire költöttél?"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                className="w-full bg-background border border-white/5 rounded-2xl p-4 text-sm font-medium outline-none focus:border-primary transition-all min-h-[100px] resize-none"
              />
            </div>

            {/* Date */}
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider flex items-center gap-2">
                <Calendar size={12} /> Dátum
              </label>
              <input 
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full bg-background border border-white/5 rounded-2xl p-4 text-sm font-medium outline-none focus:border-primary transition-all"
              />
            </div>

            {/* Toggles */}
            <div className="space-y-3 pt-2">
              <div 
                onClick={() => setIsBusiness(!isBusiness)}
                className={`p-4 rounded-2xl flex items-center justify-between cursor-pointer transition-all border-l-4 ${isBusiness ? 'bg-secondary/10 border-secondary' : 'bg-background border-transparent'}`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isBusiness ? 'bg-secondary/20 text-secondary' : 'bg-surface-variant text-on-surface-variant'}`}>
                    <Briefcase size={20} />
                  </div>
                  <div>
                    <p className="text-sm font-bold">Üzleti tranzakció</p>
                    <p className="text-[10px] text-on-surface-variant font-medium">VitaSteps követés aktív</p>
                  </div>
                </div>
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${isBusiness ? 'bg-secondary border-secondary text-background' : 'border-white/10'}`}>
                  {isBusiness && <Check size={14} strokeWidth={4} />}
                </div>
              </div>

              <div 
                onClick={() => setUsePocket(!usePocket)}
                className={`p-4 rounded-2xl flex items-center justify-between cursor-pointer transition-all border-l-4 ${usePocket ? 'bg-primary/10 border-primary' : 'bg-background border-transparent'}`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${usePocket ? 'bg-primary/20 text-primary' : 'bg-surface-variant text-on-surface-variant'}`}>
                    <Target size={20} />
                  </div>
                  <div>
                    <p className="text-sm font-bold">Virtuális zseb</p>
                    <p className="text-[10px] text-on-surface-variant font-medium">Hozzárendelés fiktív célhoz</p>
                  </div>
                </div>
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${usePocket ? 'bg-primary border-primary text-background' : 'border-white/10'}`}>
                  {usePocket && <Check size={14} strokeWidth={4} />}
                </div>
              </div>

              {usePocket && (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
                  <div>
                    <label className="block text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-3">Válassz zsebet</label>
                    <div className="grid grid-cols-2 gap-2">
                      {pockets.map((p) => (
                        <button
                          key={p._id}
                          type="button"
                          onClick={() => setVirtualPocketId(p._id)}
                          className={`p-3 rounded-xl border text-xs font-bold transition-all ${virtualPocketId === p._id ? 'bg-primary/10 border-primary text-primary' : 'bg-background border-white/5 text-on-surface-variant hover:border-white/10'}`}
                        >
                          {p.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Split Options for Shared Pockets */}
                  {pockets.find(p => p._id === virtualPocketId)?.owners?.length > 1 && (
                    <div className="p-4 bg-primary/5 rounded-2xl border border-primary/10 space-y-4">
                      <div className="flex justify-between items-center">
                        <p className="text-xs font-bold text-primary flex items-center gap-2">
                          <Users size={14} /> Közös elszámolás
                        </p>
                        <div className="flex bg-background rounded-lg p-1 border border-white/5">
                          <button 
                            type="button"
                            onClick={() => setSplitType('equal')}
                            className={`px-3 py-1 text-[10px] font-bold rounded-md transition-all ${splitType === 'equal' ? 'bg-primary text-background' : 'text-on-surface-variant'}`}
                          >
                            50-50%
                          </button>
                          <button 
                            type="button"
                            onClick={() => setSplitType('custom')}
                            className={`px-3 py-1 text-[10px] font-bold rounded-md transition-all ${splitType === 'custom' ? 'bg-primary text-background' : 'text-on-surface-variant'}`}
                          >
                            Egyedi
                          </button>
                        </div>
                      </div>

                      {splitType === 'custom' && (
                        <div className="space-y-2">
                          <p className="text-[10px] text-on-surface-variant uppercase font-bold tracking-wider">Mennyivel tartozik a másik?</p>
                          <div className="relative">
                            <input 
                              type="number"
                              value={customSplitAmount}
                              onChange={(e) => setCustomSplitAmount(e.target.value)}
                              placeholder="0"
                              className="w-full bg-background border border-white/10 rounded-xl px-4 py-2 text-sm font-bold text-white outline-none focus:border-primary/50"
                            />
                            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-bold text-on-surface-variant">{currency}</span>
                          </div>
                        </div>
                      )}
                      
                      <p className="text-[10px] text-on-surface-variant italic">
                        {splitType === 'equal' 
                          ? `A másik félnek ${(parseFloat(amount || '0') / 2).toLocaleString()} ${currency} lesz felírva.`
                          : `A másik félnek ${customSplitAmount || 0} ${currency} lesz felírva.`}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </form>

        {/* Footer Action */}
        <div className="p-6 border-t border-white/5 bg-surface-container rounded-b-3xl">
          <button 
            onClick={handleSubmit}
            disabled={loading || !amount}
            className="w-full bg-primary hover:bg-opacity-90 text-background font-bold py-5 rounded-2xl shadow-xl shadow-primary/20 flex items-center justify-center gap-2 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            {loading ? <Loader2 className="animate-spin" /> : <Check size={20} />}
            <span>Tranzakció Mentése</span>
          </button>
        </div>
      </div>
    </div>
  );
}
