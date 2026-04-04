'use client';

import dynamic from 'next/dynamic';


// The AddItemPage uses @imgly/background-removal which requires browser WASM.
// ssr: false prevents Turbopack from trying to bundle WASM during server rendering.
const AddItemPageClient = dynamic(() => import('./AddItemPageClient'), {
  ssr: false,
  loading: () => (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100dvh',
      background: 'var(--color-surface)',
      fontFamily: 'var(--font-family-body)',
      color: 'var(--color-on-surface-variant)',
      fontSize: '0.9rem',
    }}>
      Loading…
    </div>
  ),
});

export default function AddItemPage() {
  return <AddItemPageClient />;
}
