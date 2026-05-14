'use client';

import { useState } from 'react';
import { X, ArrowRightLeft, Save } from 'lucide-react';

interface PocketTransferModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  pockets: any[];
  freeBalance: number;
}

export default function PocketTransferModal({ isOpen, onClose, onSuccess, pockets, freeBalance }: PocketTransferModalProps) {
  const [formData, setFormData] = useState({
    fromPocketId: 'free', // 'free' represents Free Balance
    toPocketId: '',
    amount: '',
    note: 'Átcsoportosítás'
  });
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const amount = Number(formData.amount);

      // Case 1: From Free Balance to a Pocket
      if (formData.fromPocketId === 'free' && formData.toPocketId !== 'free') {
        const toPocket = pockets.find(p => p._id === formData.toPocketId);
        await fetch('/api/transactions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'income',
            amount,
            currency: toPocket?.currency || 'HUF',
            accountId: toPocket?.linkedAccountId?._id || toPocket?.linkedAccountId,
            virtualPocketId: formData.toPocketId,
            note: formData.note,
            date: new Date(),
            isInternalAllocation: true // This is the key!
          }),
        });
      } 
      // Case 2: From Pocket back to Free Balance
      else if (formData.fromPocketId !== 'free' && formData.toPocketId === 'free') {
        const fromPocket = pockets.find(p => p._id === formData.fromPocketId);
        await fetch('/api/transactions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'expense',
            amount,
            currency: fromPocket?.currency || 'HUF',
            accountId: fromPocket?.linkedAccountId?._id || fromPocket?.linkedAccountId,
            virtualPocketId: formData.fromPocketId,
            note: formData.note,
            date: new Date(),
            isInternalAllocation: true
          }),
        });
      }
      // Case 3: Between two pockets
      else {
        const fromPocket = pockets.find(p => p._id === formData.fromPocketId);
        const toPocket = pockets.find(p => p._id === formData.toPocketId);

        // Outgoing from source
        await fetch('/api/transactions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'expense',
            amount,
            currency: fromPocket?.currency || 'HUF',
            accountId: fromPocket?.linkedAccountId?._id || fromPocket?.linkedAccountId,
            virtualPocketId: formData.fromPocketId,
            note: formData.note,
            date: new Date(),
            isInternalAllocation: true
          }),
        });

        // Incoming to target
        await fetch('/api/transactions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'income',
            amount,
            currency: toPocket?.currency || 'HUF',
            accountId: toPocket?.linkedAccountId?._id || toPocket?.linkedAccountId,
            virtualPocketId: formData.toPocketId,
            note: formData.note,
            date: new Date(),
            isInternalAllocation: true
          }),
        });
      }

      onSuccess();
      onClose();
      setFormData({ fromPocketId: 'free', toPocketId: '', amount: '', note: 'Átcsoportosítás' });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative w-full max-w-md custom-glass rounded-3xl overflow-hidden animate-in fade-in zoom-in duration-300">
        <div className="p-6 border-b border-white/10 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center text-primary">
              <ArrowRightLeft size={24} />
            </div>
            <h2 className="text-xl font-bold text-on-surface">Pénz mozgatása</h2>
          </div>
          <button onClick={onClose} className="text-on-surface-variant hover:text-on-surface">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div>
            <label className="block text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">Honnan?</label>
            <select
              required
              value={formData.fromPocketId}
              onChange={(e) => setFormData({ ...formData, fromPocketId: e.target.value })}
              className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
            >
              <option value="free">Szabad egyenleg ({freeBalance.toLocaleString()} Ft)</option>
              {pockets.map((p) => (
                <option key={p._id} value={p._id}>{p.name} ({(p.currentAmount || 0).toLocaleString()} {p.currency})</option>
              ))}
            </select>
          </div>

          <div className="flex justify-center py-2">
             <div className="w-10 h-10 rounded-full bg-surface-variant flex items-center justify-center">
                <ArrowRightLeft size={20} className="rotate-90" />
             </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">Hová?</label>
            <select
              required
              value={formData.toPocketId}
              onChange={(e) => setFormData({ ...formData, toPocketId: e.target.value })}
              className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
            >
              <option value="">Válassz célpontot...</option>
              <option value="free">Vissza a szabad egyenlegbe</option>
              {pockets.filter(p => p._id !== formData.fromPocketId).map((p) => (
                <option key={p._id} value={p._id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">Összeg</label>
            <input
              type="number"
              required
              placeholder="0"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !formData.amount || (formData.fromPocketId === formData.toPocketId)}
            className="w-full bg-primary text-background font-bold py-4 rounded-2xl flex items-center justify-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50"
          >
            {loading ? 'Feldolgozás...' : <><Save size={20} /> Módosítás végrehajtása</>}
          </button>
        </form>
      </div>
    </div>
  );
}
