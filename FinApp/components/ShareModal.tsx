'use client';

import { useState } from 'react';
import { X, UserPlus, Send } from 'lucide-react';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  pocketId: string;
  pocketName: string;
}

export default function ShareModal({ isOpen, onClose, pocketId, pocketName }: ShareModalProps) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  if (!isOpen) return null;

  const handleShare = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const res = await fetch('/api/pockets/share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pocketId, email }),
      });

      const data = await res.json();

      if (res.ok) {
        setMessage({ type: 'success', text: `Sikeresen megosztva vele: ${data.user}!` });
        setTimeout(() => {
          onClose();
          setEmail('');
          setMessage(null);
        }, 2000);
      } else {
        setMessage({ type: 'error', text: data.error || 'Hiba történt a megosztáskor.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Hálózati hiba történt.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative w-full max-w-sm custom-glass rounded-3xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="p-6 border-b border-white/10 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-secondary/20 flex items-center justify-center text-secondary">
              <UserPlus size={24} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-on-surface">Zseb megosztása</h2>
              <p className="text-[10px] text-on-surface-variant font-bold uppercase tracking-widest">{pocketName}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-on-surface-variant hover:text-on-surface">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleShare} className="p-6 space-y-4">
          <p className="text-xs text-on-surface-variant">Add meg a párod e-mail címét, hogy közösen lássátok ezt a zsebet!</p>
          
          <div>
            <input
              type="email"
              required
              placeholder="pl. parom@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-surface-container border border-white/10 rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:border-secondary/50 transition-colors"
            />
          </div>

          {message && (
            <div className={`p-3 rounded-xl text-xs font-bold text-center ${message.type === 'success' ? 'bg-secondary/10 text-secondary' : 'bg-error/10 text-error'}`}>
              {message.text}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-secondary text-background font-bold py-3 rounded-2xl flex items-center justify-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50"
          >
            {loading ? 'Küldés...' : <><Send size={18} /> Megosztás</>}
          </button>
        </form>
      </div>
    </div>
  );
}
