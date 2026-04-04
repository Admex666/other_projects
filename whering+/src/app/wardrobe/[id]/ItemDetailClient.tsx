'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronLeft, Trash2, Edit2, Shirt } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';
import styles from './page.module.css';

type WardrobeItem = {
  id: string;
  category: string;
  color?: string;
  fabric?: string;
  tags?: string[];
  image_urls?: string[];
  created_at?: string;
};

interface ItemDetailClientProps {
  item: WardrobeItem;
}

export function ItemDetailClient({ item }: ItemDetailClientProps) {
  const router = useRouter();
  const supabase = createClient();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this item?')) return;
    
    setIsDeleting(true);
    try {
      const { error } = await supabase
        .from('wardrobe_items')
        .delete()
        .eq('id', item.id);

      if (error) throw error;
      
      router.push('/wardrobe');
      router.refresh();
    } catch (err: unknown) {
      alert('Failed to delete item: ' + (err instanceof Error ? err.message : 'Unknown error'));
      setIsDeleting(false);
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <button className={styles.backBtn} onClick={() => router.back()}>
          <ChevronLeft size={20} /> Back
        </button>
      </header>

      <div className={styles.heroImageContainer}>
        {item.image_urls?.[0] ? (
          <img src={item.image_urls[0]} alt={item.category} className={styles.heroImage} />
        ) : (
          <div className={styles.placeholderIcon}><Shirt size={120} /></div>
        )}
      </div>

      <div className={styles.content}>
        <h1 className={styles.category}>{item.category}</h1>
        
        <div className={styles.metaRow}>
          {item.color && (
            <div className={styles.metaChip}>
              <span className={styles.colorDot} style={{ backgroundColor: item.color.toLowerCase() }} />
              {item.color}
            </div>
          )}
          {item.fabric && (
            <div className={styles.metaChip}>
              {item.fabric}
            </div>
          )}
          <div className={styles.metaChip}>
            Added {new Date(item.created_at || '').toLocaleDateString()}
          </div>
        </div>

        {item.tags && item.tags.length > 0 && (
          <div className={styles.section}>
            <p className={styles.sectionTitle}>Tags</p>
            <div className={styles.tagCloud}>
              {item.tags.map((tag, i) => (
                <span key={i} className={styles.tag}>{tag}</span>
              ))}
            </div>
          </div>
        )}

        <div className={styles.actions}>
          <button 
            className={styles.deleteBtn} 
            onClick={handleDelete}
            disabled={isDeleting}
          >
            <Trash2 size={18} />
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
          <button className={styles.editBtn}>
            <Edit2 size={18} /> Edit Details
          </button>
        </div>
      </div>
    </div>
  );
}
