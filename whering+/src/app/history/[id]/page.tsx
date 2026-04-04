import { createClient } from '@/lib/supabase/server';
import { notFound } from 'next/navigation';
import styles from './detail.module.css';
import { Shirt, Thermometer, Calendar, ArrowLeft, Star } from 'lucide-react';
import Link from 'next/link';
import { ShareOutfit } from '@/components/ui/ShareOutfit';

export default async function OutfitDetailPage(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) return null;

  const { data: outfit } = await supabase
    .from('outfits')
    .select('*')
    .eq('id', params.id)
    .eq('user_id', user.id)
    .single();

  if (!outfit) notFound();

  // Fetch items
  const { data: items } = await supabase
    .from('wardrobe_items')
    .select('*')
    .in('id', outfit.item_ids);

  const date = new Date(outfit.created_at).toLocaleDateString('en-GB', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <Link href="/history" className={styles.backButton}>
          <ArrowLeft size={20} />
          <span>Back to History</span>
        </Link>
      </header>

      <div className={styles.content}>
        <div className={styles.meta}>
          <div className={styles.dateRow}>
            <Calendar size={16} />
            <span>{date}</span>
          </div>
          <h1 className={styles.title}>{outfit.headline || 'Outfit Details'}</h1>
        </div>

        <ShareOutfit headline={outfit.headline || ''} score={outfit.confidence_score} />

        <div className={styles.scoreSection}>
          <div className={styles.scoreCircle}>
            <span className={styles.scoreNumber}>{outfit.confidence_score}%</span>
          </div>
          <div className={styles.feedbackBox}>
             <p className={styles.feedbackLabel}>Your Rating</p>
             <div className={styles.stars}>
               {[1, 2, 3, 4, 5].map((s) => (
                 <Star 
                    key={s} 
                    size={16} 
                    fill={s <= (outfit.feedback_score || 0) ? 'var(--color-primary)' : 'none'} 
                    color={s <= (outfit.feedback_score || 0) ? 'var(--color-primary)' : 'var(--color-on-surface-variant)'} 
                 />
               ))}
             </div>
          </div>
        </div>

        <div className={styles.contextGrid}>
           <div className={styles.contextItem}>
              <p className={styles.contextLabel}>Occasion</p>
              <p className={styles.contextValue}>{outfit.context?.eventType || 'General'}</p>
           </div>
           {outfit.context?.weather && (
             <div className={styles.contextItem}>
                <p className={styles.contextLabel}>Weather</p>
                <p className={styles.contextValue}>
                  <Thermometer size={14} style={{ display: 'inline', marginBottom: -2 }} /> {outfit.context.weather.temp}°C, {outfit.context.weather.description}
                </p>
             </div>
           )}
        </div>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Stylist Opinion</h2>
          <p className={styles.rationale}>{outfit.rationale}</p>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Outfit Elements</h2>
          <div className={styles.itemsGrid}>
            {items?.map((item) => (
              <div key={item.id} className={styles.itemCard}>
                <div className={styles.itemImage}>
                  {item.image_urls?.[0] ? (
                    <img src={item.image_urls[0]} alt={item.category} />
                  ) : (
                    <Shirt size={24} color="var(--color-on-surface-variant)" />
                  )}
                </div>
                <div className={styles.itemInfo}>
                  <p className={styles.itemCategory}>{item.category}</p>
                  <p className={styles.itemMeta}>{item.color} {item.fabric}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
