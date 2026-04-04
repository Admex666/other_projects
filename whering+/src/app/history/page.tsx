import { createClient } from '@/lib/supabase/server';
import styles from './history.module.css';
import { Shirt, Thermometer, Calendar } from 'lucide-react';
import Link from 'next/link';
import { RatingStars } from '@/components/ai/RatingStars';

export default async function HistoryPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) return null;

  // Fetch outfits with feedback score
  const { data: outfits } = await supabase
    .from('outfits')
    .select('*')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false });

  if (!outfits || outfits.length === 0) {
    return (
      <div className={styles.container}>
        <h1 className={styles.title}>History</h1>
        <div className={styles.emptyState}>
          <Calendar size={48} className={styles.emptyIcon} />
          <p>Your outfit history is empty.</p>
          <Link href="/outfit/new" className={styles.cta}>
            Build your first outfit
          </Link>
        </div>
      </div>
    );
  }

  // Get all unique item IDs to fetch them for thumbnails
  const allItemIds = Array.from(new Set(outfits.flatMap(o => o.item_ids)));
  const { data: items } = await supabase
    .from('wardrobe_items')
    .select('id, category, image_urls')
    .in('id', allItemIds);

  const itemMap = new Map(items?.map(i => [i.id, i]));

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>History</h1>
      
      <div className={styles.list}>
        {outfits.map((outfit: any) => {
          const date = new Date(outfit.created_at).toLocaleDateString('en-GB', {
            weekday: 'long',
            day: 'numeric',
            month: 'short'
          });

          return (
            <div key={outfit.id} className={styles.card}>
              <Link href={`/history/${outfit.id}`} className={styles.detailLink}>
                <div className={styles.cardHeader}>
                  <span className={styles.date}>{date}</span>
                  <span className={styles.score} data-score={outfit.confidence_score}>
                    {outfit.confidence_score}%
                  </span>
                </div>

                <div className={styles.contextLine}>
                  <span className={styles.eventTag}>{outfit.context.eventType}</span>
                  {outfit.context.weather && (
                    <span className={styles.weatherTag}>
                      <Thermometer size={12} /> {outfit.context.weather.temp}°C
                    </span>
                  )}
                </div>

                <h3 className={styles.headline}>{outfit.headline}</h3>
                <p className={styles.rationale}>{outfit.rationale}</p>

                <div className={styles.itemsRow}>
                  {outfit.item_ids.map((id: string) => {
                    const item = itemMap.get(id);
                    return item?.image_urls?.[0] ? (
                      <div key={id} className={styles.itemThumb}>
                        <img src={item.image_urls[0]} alt={item.category} />
                      </div>
                    ) : (
                      <div key={id} className={styles.itemThumbPlaceholder}>
                        <Shirt size={16} />
                      </div>
                    );
                  })}
                </div>
              </Link>

              <div className={styles.cardFooter}>
                <p className={styles.rateLabel}>Rate this suggestion:</p>
                <RatingStars outfitId={outfit.id} initialRating={outfit.feedback_score || 0} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
