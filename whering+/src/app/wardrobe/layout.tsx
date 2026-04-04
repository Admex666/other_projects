import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';

export default function WardrobeLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
