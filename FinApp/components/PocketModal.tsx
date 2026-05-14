'use client';

import { useState } from 'react';
import { X, Save, Wallet } from 'lucide-react';

interface PocketModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  accounts: any[];
}

export default function PocketModal({ isOpen, onClose, onSuccess, accounts }: PocketModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    targetAmount: '',
    linkedAccountId: '',
    color: '#7C6FFF'
  });
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch('/api/pockets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          targetAmount: Number(formData.targetAmount)
        }),
      });

      if (res.ok) {
        onSuccess();
        onClose();
        setFormData({ name: '', targetAmount: '', linkedAccountId: '', color: '#7C6FFF' });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative w-full max-w-md custom-glass rounded-3xl overflow-hidden animate-in fade-in zoom-in duration-300">
        <div className="p-6 border-b border-white/10 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center text-primary">
              <Wallet size={24} />
            </div>
            <h2 className="text-xl font-bold text-on-surface">Új Virtuális Zseb</h2>
          </div>
          <button onClick={onClose} className="text-on-surface-variant hover:text-on-surface">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div>
            <label className="block text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">Zseb neve</label>
            <input
              type="text"
              required
              placeholder="pl. Nyaralás 2024"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">Célösszeg (Ft)</label>
              <input
                type="number"
                required
                placeholder="0"
                value={formData.targetAmount}
                onChange={(e) => setFormData({ ...formData, targetAmount: e.target.value })}
                className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">Szín</label>
              <input
                type="color"
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                className="w-full h-[50px] bg-surface-container border border-white/10 rounded-xl p-1 cursor-pointer"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">Kapcsolt számla</label>
            <select
              required
              value={formData.linkedAccountId}
              onChange={(e) => setFormData({ ...formData, linkedAccountId: e.target.value })}
              className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
            >
              <option value="">Válassz számlát...</option>
              {accounts.map((acc: any) => (
                <option key={acc._id} value={acc._id}>{acc.name} ({acc.currency})</option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-background font-bold py-4 rounded-2xl flex items-center justify-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50"
          >
            {loading ? 'Mentés...' : <><Save size={20} /> Zseb létrehozása</>}
          </button>
        </form>
      </div>
    </div>
  );
}
