'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Shirt } from 'lucide-react';
import styles from './page.module.css';

const FILTER_CATEGORIES = ['All', 'Tops', 'Bottoms', 'Shoes', 'Outerwear', 'Accessories'];

// Define colours for category tags
const CATEGORY_COLORS: Record<string, string> = {
  tops: '#d7e7d6',
  bottoms: '#dafce6',
  shoes: '#e2e3db',
  outerwear: '#c8d8c8',
  accessories: '#e8dfd0',
};

type WardrobeItem = {
  id: string;
  category: string;
  color?: string;
  image_urls?: string[];
  tags?: string[];
};

interface WardrobeGridProps {
  items: WardrobeItem[];
  totalCount: number;
}

export function WardrobeGrid({ items, totalCount }: WardrobeGridProps) {
  const [activeFilter, setActiveFilter] = useState('All');

  const filtered = activeFilter === 'All'
    ? items
    : items.filter(i => i.category?.toLowerCase() === activeFilter.toLowerCase());

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerTop}>
          <h1 className={styles.title}>Wardrobe</h1>
          <span className={styles.itemCount}>{totalCount} pieces</span>
        </div>

        {/* Filter row */}
        <div className={styles.filterRow} role="group" aria-label="Filter by category">
          {FILTER_CATEGORIES.map((cat) => (
            <button
              key={cat}
              className={`${styles.filterChip} ${activeFilter === cat ? styles.filterChipActive : ''}`}
              onClick={() => setActiveFilter(cat)}
              aria-pressed={activeFilter === cat}
            >
              {cat}
            </button>
          ))}
        </div>
      </header>

      {/* Grid or Empty state */}
      <div className={styles.gridBody}>
        {filtered.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>
              <Shirt size={32} />
            </div>
            <p className={styles.emptyTitle}>
              {activeFilter === 'All' ? 'Your wardrobe is empty' : `No ${activeFilter} yet`}
            </p>
            <p className={styles.emptyText}>
              {activeFilter === 'All'
                ? 'Tap the + button below to add your first piece. Photos are processed right in your browser — no server required.'
                : `Add your first ${activeFilter.toLowerCase()} using the + button below.`}
            </p>
          </div>
        ) : (
          <div className={styles.grid}>
            {filtered.map((item) => (
              <Link key={item.id} href={`/wardrobe/${item.id}`} className={styles.itemCard}>
                <div className={styles.itemImageWrapper}>
                  {item.image_urls?.[0] ? (
                    <img
                      src={item.image_urls[0]}
                      alt={item.category}
                      className={styles.itemImage}
                    />
                  ) : (
                    <div className={styles.itemImagePlaceholder}>
                      <Shirt size={36} />
                    </div>
                  )}
                </div>
                <div className={styles.itemInfo}>
                  <p className={styles.itemCategory}>{item.category}</p>
                  <div className={styles.itemMeta}>
                    <span
                      className={styles.tagDot}
                      style={{ backgroundColor: CATEGORY_COLORS[item.category?.toLowerCase()] ?? '#e2e3db' }}
                    />
                    <span>{item.color ?? 'No colour'}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
