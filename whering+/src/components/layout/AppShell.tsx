'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Shirt, Clock, User, Plus } from 'lucide-react';
import styles from './AppShell.module.css';

interface AppShellProps {
  children: ReactNode;
}

const tabs = [
  { href: '/dashboard', icon: Home, label: 'Home' },
  { href: '/wardrobe', icon: Shirt, label: 'Wardrobe' },
  { href: '/history', icon: Clock, label: 'History' },
  { href: '/profile', icon: User, label: 'Profile' },
];

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className={styles.shell}>
      <main className={styles.main}>
        {children}
      </main>

      <nav className={styles.tabBar} role="navigation" aria-label="Main navigation">
        {/* First 2 tabs */}
        {tabs.slice(0, 2).map(({ href, icon: Icon, label }) => {
          const isActive = pathname === href || pathname.startsWith(href + '/');
          return (
            <Link
              key={href}
              href={href}
              className={`${styles.tabItem} ${isActive ? styles.tabItemActive : ''}`}
              aria-label={label}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={22} className={styles.tabIcon} strokeWidth={isActive ? 2.5 : 1.8} />
              <span className={styles.tabLabel}>{label}</span>
            </Link>
          );
        })}

        {/* Center FAB */}
        <div className={styles.fabWrapper}>
          <Link href="/wardrobe/add" aria-label="Add item to wardrobe">
            <button className={styles.fab}>
              <Plus size={26} strokeWidth={2.5} />
            </button>
          </Link>
          <span className={styles.tabLabel} style={{ marginTop: 4 }}>Add</span>
        </div>

        {/* Last 2 tabs */}
        {tabs.slice(2).map(({ href, icon: Icon, label }) => {
          const isActive = pathname === href || pathname.startsWith(href + '/');
          return (
            <Link
              key={href}
              href={href}
              className={`${styles.tabItem} ${isActive ? styles.tabItemActive : ''}`}
              aria-label={label}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={22} className={styles.tabIcon} strokeWidth={isActive ? 2.5 : 1.8} />
              <span className={styles.tabLabel}>{label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
