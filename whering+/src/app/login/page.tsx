'use client';

import { useState } from 'react';
import styles from './page.module.css';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { createClient } from '@/lib/supabase/client';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [isLogin, setIsLogin] = useState(true);

  const [error, setError] = useState('');
  const supabase = createClient();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        // Middleware will handle redirect to /dashboard
        window.location.href = '/dashboard';
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: `${window.location.origin}/auth/callback`,
          },
        });
        if (error) throw error;
        // Usually, users need to confirm their email
        alert('Check your email for the confirmation link.');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred during authentication.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.imageSection}>
        {/* We use an img placeholder for now, which later can be styled via AI generation or an asset */}
        <img 
          src="https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=2670&auto=format&fit=crop" 
          alt="Curated wardrobe aesthetic"
          className={styles.imagePlaceholder}
        />
      </div>

      <div className={styles.authSection}>
        <div className={styles.logo}>Atelier.</div>
        
        <div className={styles.header}>
          <h1 className={styles.title}>
            {isLogin ? 'Welcome back.' : 'Curate your space.'}
          </h1>
          <p className={styles.subtitle}>
            {isLogin 
              ? 'Sign in to access your curated digital wardrobe.' 
              : 'Sign up to begin your journey of mindful dressing.'}
          </p>
        </div>

        {error && <div className={styles.errorBanner}>{error}</div>}

        <form className={styles.form} onSubmit={handleSubmit}>
          <Input 
            label="Email Address" 
            type="email" 
            placeholder="you@example.com" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input 
            label="Password" 
            type="password" 
            placeholder="••••••••" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <div className={styles.actions}>
            <Button type="submit" fullWidth disabled={loading}>
              {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
            </Button>
            <Button 
              type="button" 
              variant="tertiary" 
              fullWidth 
              onClick={() => setIsLogin(!isLogin)}
            >
              {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
            </Button>
          </div>
        </form>

        <div className={styles.footer}>
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </div>
      </div>
    </div>
  );
}
