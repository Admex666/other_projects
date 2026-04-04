import Link from 'next/link';
import { Shirt, Plus } from 'lucide-react';
import styles from './page.module.css';
import { createClient } from '@/lib/supabase/server';
import { WeatherDashboardSection } from './WeatherDashboardSection';
import { detectRepetitions } from '@/lib/ai/repetition-engine';
import { Sparkles } from 'lucide-react';
import { generateRefreshSuggestion } from '@/lib/ai/refresh-suggestions';

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return null; // Should be handled by middleware
  }

  // Greet the user
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const firstName = user?.email?.split('@')[0] ?? 'there';

  // Fetch the 5 most recently added wardrobe items
  const { data: recentItems } = await supabase
    .from('wardrobe_items')
    .select('id, category, image_urls')
    .eq('user_id', user?.id)
    .eq('is_archived', false)
    .order('created_at', { ascending: false })
    .limit(5);

  // Fetch today's outfit
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const { data: latestOutfit } = await supabase
    .from('outfits')
    .select('*')
    .eq('user_id', user?.id)
    .gte('created_at', today.toISOString())
    .order('created_at', { ascending: false })
    .limit(1)
    .single();

  let outfitItems: any[] = [];
  if (latestOutfit && latestOutfit.item_ids?.length > 0) {
    const { data: items } = await supabase
      .from('wardrobe_items')
      .select('id, category, color, image_urls')
      .in('id', latestOutfit.item_ids);
    outfitItems = items ?? [];
  }

  // Detect repetition (loop)
  const repetition = await detectRepetitions(supabase, user.id);
  let refreshTip = '';
  if (repetition) {
    const { data: repeatItems } = await supabase
      .from('wardrobe_items')
      .select('category, color, fabric')
      .in('id', repetition.itemIds);
    refreshTip = await generateRefreshSuggestion(repeatItems || [], 'casual wear');
  }

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <p className={styles.greeting}>{greeting},</p>
        <h1 className={styles.title}>{firstName}.</h1>
      </header>

      {/* Context Bar — client component for geolocation and event selection */}
      <WeatherDashboardSection />

      {/* Break the Loop Alert */}
      {refreshTip && (
        <section className={styles.section}>
          <div className={styles.tipCard}>
            <div className={styles.tipIcon}>
              <Sparkles size={20} />
            </div>
            <div className={styles.tipContent}>
              <p className={styles.tipLabel}>Break the loop</p>
              <p className={styles.tipText}>&ldquo;{refreshTip}&rdquo;</p>
            </div>
          </div>
        </section>
      )}

      {/* Today's Outfit */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Today&apos;s Outfit</h2>
          <Link href="/outfit/new" className={styles.sectionLink}>
            {latestOutfit ? 'Change it →' : 'Plan one →'}
          </Link>
        </div>

        {latestOutfit ? (
          <div className={styles.outfitCard}>
            <div className={styles.outfitImageRow}>
              {outfitItems.map((item) => (
                <div key={item.id} className={styles.outfitItemImage}>
                  {item.image_urls?.[0] && (
                    <img src={item.image_urls[0]} alt={item.category} />
                  )}
                </div>
              ))}
              {/* Fill remaining slots if < 3 items for editorial feel */}
              {outfitItems.length < 3 && Array.from({ length: 3 - outfitItems.length }).map((_, i) => (
                <div key={`empty-${i}`} className={styles.outfitItemImage} style={{ opacity: 0.3 }}>
                   <Shirt size={24} />
                </div>
              ))}
            </div>
            
            <div className={styles.outfitInfo}>
              <div className={styles.outfitDetails}>
                <p className={styles.outfitName}>{latestOutfit.context?.event_type || 'Daily Look'}</p>
                <p className={styles.outfitContext}>
                  {latestOutfit.rationale?.substring(0, 85)}...
                </p>
              </div>
              <div className={styles.outfitScore}>
                <span className={styles.scoreNumber}>{latestOutfit.confidence_score}</span>
                <span className={styles.scoreLabel}>Score</span>
              </div>
            </div>
          </div>
        ) : (
          <div className={styles.emptyCard}>
            <div className={styles.emptyIcon}>
              <Shirt size={24} />
            </div>
            <p className={styles.emptyTitle}>Nothing planned yet</p>
            <p className={styles.emptyText}>
              Tap &ldquo;Plan one&rdquo; above or add your first wardrobe item to get started.
            </p>
          </div>
        )}
      </section>

      {/* Recently Added */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Wardrobe</h2>
          <Link href="/wardrobe" className={styles.sectionLink}>See all →</Link>
        </div>

        {recentItems && recentItems.length > 0 ? (
          <div className={styles.recentScroll}>
            {recentItems.map((item) => (
              <Link key={item.id} href={`/wardrobe/${item.id}`} className={styles.recentItemCard}>
                <div className={styles.recentItemImage}>
                  {item.image_urls?.[0] && (
                    <img src={item.image_urls[0]} alt={item.category} />
                  )}
                </div>
                <span className={styles.recentItemLabel}>{item.category}</span>
              </Link>
            ))}
          </div>
        ) : (
          <div className={styles.emptyCard}>
            <div className={styles.emptyIcon}>
              <Plus size={24} />
            </div>
            <p className={styles.emptyTitle}>Your wardrobe is empty</p>
            <p className={styles.emptyText}>
              Add your first piece using the + button below.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
