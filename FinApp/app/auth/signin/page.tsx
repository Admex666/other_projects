'use client';

import { signIn } from 'next-auth/react';
import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Lock, Mail, Loader2, ShieldCheck } from 'lucide-react';

function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') || '/';
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await signIn('credentials', {
        email,
        password,
        redirect: false,
      });

      if (res?.error) {
        setError('Hibás email vagy jelszó!');
      } else {
        router.push(callbackUrl);
      }
    } catch (err) {
      setError('Valami hiba történt...');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="custom-glass w-full max-w-md p-8 space-y-8 rounded-3xl relative z-10">
      <div className="text-center">
        <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-6 text-primary border border-primary/20">
          <ShieldCheck size={32} />
        </div>
        <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">FinSpace</h1>
        <p className="text-on-surface-variant text-sm">Üdvözlünk! Kérlek, jelentkezz be.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="p-4 text-xs bg-error/10 border border-error/20 text-error rounded-xl text-center font-medium">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div className="relative group">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant group-focus-within:text-primary transition-colors" size={18} />
            <input
              type="email"
              placeholder="Email cím"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-surface-container border border-white/5 rounded-2xl py-4 pl-12 pr-4 text-sm text-white focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none transition-all placeholder:text-on-surface-variant/50"
            />
          </div>
          <div className="relative group">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant group-focus-within:text-primary transition-colors" size={18} />
            <input
              type="password"
              placeholder="Jelszó"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full bg-surface-container border border-white/5 rounded-2xl py-4 pl-12 pr-4 text-sm text-white focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none transition-all placeholder:text-on-surface-variant/50"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-primary hover:bg-opacity-90 text-background font-bold py-4 rounded-2xl shadow-xl shadow-primary/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50 active:scale-[0.98]"
        >
          {loading ? (
            <Loader2 className="animate-spin" size={20} />
          ) : (
            'Bejelentkezés'
          )}
        </button>
      </form>

      <div className="pt-4 text-center">
        <p className="text-[10px] text-on-surface-variant/50 font-medium tracking-widest uppercase">
          FinSpace v1.0 • Secure Access
        </p>
      </div>
    </div>
  );
}

export default function SignIn() {
  return (
    <div className="flex items-center justify-center min-h-screen p-4 bg-background selection:bg-primary selection:text-background">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/10 rounded-full blur-[120px]"></div>
      </div>

      <Suspense fallback={
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="animate-spin text-primary" size={40} />
          <p className="text-xs text-on-surface-variant animate-pulse">Betöltés...</p>
        </div>
      }>
        <SignInForm />
      </Suspense>
    </div>
  );
}
