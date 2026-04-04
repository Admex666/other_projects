'use client';

import { createClient } from '@/lib/supabase/client';
import { useRouter } from 'next/navigation';

export default function ProfilePage() {
  const supabase = createClient();
  const router = useRouter();

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push('/login');
    router.refresh();
  };

  return (
    <div style={{ padding: '56px 24px 24px' }}>
      <h1 style={{ fontFamily: 'var(--font-family-display)', fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 32 }}>
        Profile
      </h1>
      <button
        onClick={handleSignOut}
        style={{
          padding: '14px 24px',
          borderRadius: 'var(--border-radius-xl)',
          border: 'none',
          background: 'var(--color-surface-container-highest)',
          color: 'var(--color-on-surface)',
          fontFamily: 'var(--font-family-body)',
          fontSize: '1rem',
          fontWeight: 500,
          cursor: 'pointer',
          width: '100%',
        }}
      >
        Sign Out
      </button>
    </div>
  );
}
