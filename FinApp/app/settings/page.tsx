'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Lock, ArrowLeft, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import Link from 'next/link';

export default function SettingsPage() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      const res = await fetch('/api/settings/password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password, confirmPassword }),
      });

      const data = await res.json();

      if (res.ok) {
        setSuccess(true);
        setPassword('');
        setConfirmPassword('');
      } else {
        setError(data.error || 'Hiba történt a mentés során');
      }
    } catch (err) {
      setError('Hálózati hiba történt');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-container-margin text-on-surface">
      <div className="max-w-md mx-auto">
        <div className="flex items-center gap-4 mb-8">
          <Link 
            href="/"
            className="w-10 h-10 rounded-full bg-surface-variant flex items-center justify-center text-on-surface-variant hover:text-white transition-colors"
          >
            <ArrowLeft size={20} />
          </Link>
          <h1 className="text-2xl font-bold">Beállítások</h1>
        </div>

        <div className="space-y-gutter-md">
          {/* Profile Section Preview */}
          <div className="custom-glass p-stack-lg rounded-3xl border border-white/5 flex items-center gap-stack-lg mb-4">
             <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center text-primary text-2xl font-bold">
               <Lock size={32} />
             </div>
             <div>
               <h2 className="text-lg font-bold">Biztonság</h2>
               <p className="text-xs text-on-surface-variant">Jelszó és fiók védelem</p>
             </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-4 bg-error/10 border border-error/20 text-error rounded-2xl flex items-center gap-3 text-sm font-medium animate-in fade-in zoom-in duration-300">
                <AlertCircle size={18} />
                {error}
              </div>
            )}

            {success && (
              <div className="p-4 bg-secondary/10 border border-secondary/20 text-secondary rounded-2xl flex items-center gap-3 text-sm font-medium animate-in fade-in zoom-in duration-300">
                <CheckCircle2 size={18} />
                Jelszó sikeresen megváltoztatva!
              </div>
            )}

            <div className="custom-glass p-stack-lg rounded-3xl border border-white/5 space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-bold text-on-surface-variant uppercase tracking-wider ml-1">Új Jelszó</label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant group-focus-within:text-primary transition-colors" size={18} />
                  <input
                    type="password"
                    placeholder="Legalább 6 karakter"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full bg-surface-container border border-white/5 rounded-2xl py-4 pl-12 pr-4 text-sm text-white focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none transition-all"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold text-on-surface-variant uppercase tracking-wider ml-1">Megerősítés</label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant group-focus-within:text-primary transition-colors" size={18} />
                  <input
                    type="password"
                    placeholder="Új jelszó ismét"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="w-full bg-surface-container border border-white/5 rounded-2xl py-4 pl-12 pr-4 text-sm text-white focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none transition-all"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary text-background font-bold py-4 rounded-2xl shadow-xl shadow-primary/20 flex items-center justify-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={20} /> : 'Mentés'}
            </button>
          </form>

          <div className="pt-8 text-center">
             <p className="text-[10px] text-on-surface-variant/30 uppercase tracking-[0.2em] font-bold">FinSpace Secure Settings</p>
          </div>
        </div>
      </div>
    </div>
  );
}
