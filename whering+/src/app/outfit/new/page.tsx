'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Check, ChevronLeft, Shirt, Sparkles, RotateCcw, Save } from 'lucide-react';
import { WeatherWidget } from '@/components/weather/WeatherWidget';
import { createClient } from '@/lib/supabase/client';
import styles from './page.module.css';

const EVENT_TYPES = [
  'Casual day',
  'Office / Work from home',
  'Client meeting',
  'Formal event',
  'Evening out',
  'Sport / Active',
  'Travel',
  'Date night',
];

type WardrobeItem = {
  id: string;
  category: string;
  color?: string;
  image_urls?: string[];
};

type ValidationResult = {
  confidence_score: number;
  headline: string;
  rationale: string;
  suggestions: string[];
  strengths: string[];
};

type WeatherData = {
  temp: number;
  description: string;
};

export default function OutfitBuilderPage() {
  const router = useRouter();
  const supabase = createClient();

  const [wardrobeItems, setWardrobeItems] = useState<WardrobeItem[]>([]);
  const [loadingWardrobe, setLoadingWardrobe] = useState(true);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [eventType, setEventType] = useState('Casual day');
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [validating, setValidating] = useState(false);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [savingOutfit, setSavingOutfit] = useState(false);
  const [error, setError] = useState('');

  const handleWeatherLoad = useCallback((w: WeatherData) => {
    setWeather({ temp: w.temp, description: w.description });
  }, []);

  useEffect(() => {
    (async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;
      const { data } = await supabase
        .from('wardrobe_items')
        .select('id, category, color, image_urls')
        .eq('user_id', user.id)
        .eq('is_archived', false)
        .order('created_at', { ascending: false });
      setWardrobeItems(data ?? []);
      setLoadingWardrobe(false);
    })();
  }, [supabase]);

  const toggleItem = useCallback((id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }, []);

  const handleValidate = async () => {
    if (selectedIds.length === 0) return;
    setValidating(true);
    setError('');
    setResult(null);

    try {
      const res = await fetch('/api/validate-outfit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          itemIds: selectedIds,
          context: {
            eventType,
            weather: weather ?? undefined,
          },
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error ?? 'Validation failed');
      }

      const data: ValidationResult = await res.json();
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setValidating(false);
    }
  };

  const handleSaveOutfit = async () => {
    if (!result) return;
    setSavingOutfit(true);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not logged in');

      await supabase.from('outfits').insert({
        user_id: user.id,
        item_ids: selectedIds,
        confidence_score: result.confidence_score,
        rationale: result.rationale,
        context: { event_type: eventType, weather },
      });

      router.push('/dashboard');
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save outfit');
    } finally {
      setSavingOutfit(false);
    }
  };

  const selectedItems = wardrobeItems.filter((i) => selectedIds.includes(i.id));

  // ── LOADING STATE ──
  if (validating) {
    return (
      <div className={styles.loadingScreen}>
        <div className={styles.loadingSpinner} />
        <p className={styles.loadingText}>Analysing your outfit…</p>
        <p className={styles.loadingSubText}>
          The AI is checking colour harmony, occasion fit, and weather suitability.
        </p>
      </div>
    );
  }

  // ── RESULT SCREEN ──
  if (result) {
    const scoreColor = result.confidence_score >= 80 ? '#546255' :
                       result.confidence_score >= 60 ? '#4d607f' : '#9f403d';

    return (
      <div className={styles.resultScreen}>
        {/* Back to adjust */}
        <button className={styles.backBtn} onClick={() => setResult(null)}>
          <ChevronLeft size={16} /> Adjust outfit
        </button>

        {/* Confidence Hero */}
        <div className={styles.confidenceHero}>
          <div className={styles.scoreNumber} style={{ color: scoreColor }}>
            {result.confidence_score}
          </div>
          <div className={styles.scoreLabel}>Confidence Score</div>
          <p className={styles.headline}>{result.headline}</p>
        </div>

        {/* Outfit thumbnail strip */}
        <div className={styles.outfitStrip}>
          {selectedItems.map((item) => (
            <div key={item.id} className={styles.outfitThumb}>
              {item.image_urls?.[0] && (
                <img src={item.image_urls[0]} alt={item.category} />
              )}
            </div>
          ))}
        </div>

        {/* Rationale */}
        <div className={styles.rationaleCard}>
          <p className={styles.cardTitle}>Stylist&apos;s Notes</p>
          <p className={styles.rationaleText}>{result.rationale}</p>
        </div>

        {/* Strengths */}
        {result.strengths.length > 0 && (
          <div className={styles.rationaleCard}>
            <p className={styles.cardTitle}>What Works</p>
            <ul className={styles.bulletList}>
              {result.strengths.map((s, i) => (
                <li key={i} className={styles.bulletItem}>
                  <span className={`${styles.bulletDot} ${styles.strengthDot}`} />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Suggestions */}
        {result.suggestions.filter(Boolean).length > 0 && (
          <div className={styles.rationaleCard}>
            <p className={styles.cardTitle}>Small Upgrade</p>
            <ul className={styles.bulletList}>
              {result.suggestions.filter(Boolean).map((s, i) => (
                <li key={i} className={styles.bulletItem}>
                  <span className={`${styles.bulletDot} ${styles.suggestionDot}`} />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {error && <p style={{ color: 'var(--color-error)', fontFamily: 'var(--font-family-body)', fontSize: '0.875rem' }}>{error}</p>}

        {/* Actions */}
        <div className={styles.actionRow}>
          <button className={styles.retryBtn} onClick={() => setResult(null)}>
            <RotateCcw size={16} />
          </button>
          <button className={styles.saveOutfitBtn} onClick={handleSaveOutfit} disabled={savingOutfit}>
            {savingOutfit ? 'Saving…' : '✓ Wear this today'}
          </button>
        </div>
      </div>
    );
  }

  // ── BUILDER SCREEN ──
  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={() => router.back()}>
          <ChevronLeft size={16} /> Back
        </button>
        <h1 className={styles.title}>Build an Outfit</h1>
        <p className={styles.subtitle}>Select pieces, then let the AI validate your look.</p>
      </div>

      {/* Context Card */}
      <div className={styles.contextCard}>
        <p className={styles.contextLabel}>Context</p>
        <div className={styles.contextRow}>
          <WeatherWidget
            onWeatherLoad={(w) => setWeather({ temp: w.temp, description: w.description })}
            compact
          />
          <select
            className={styles.eventSelect}
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
          >
            {EVENT_TYPES.map((et) => (
              <option key={et} value={et}>{et}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Item Picker */}
      <div className={styles.section}>
        <p className={styles.sectionTitle}>
          Select pieces{selectedIds.length > 0 ? ` (${selectedIds.length} selected)` : ''}
        </p>

        {loadingWardrobe ? (
          <div className={styles.pickerEmpty}>Loading your wardrobe…</div>
        ) : wardrobeItems.length === 0 ? (
          <div className={styles.pickerEmpty}>
            Your wardrobe is empty. Add pieces first using the + button.
          </div>
        ) : (
          <div className={styles.pickerGrid}>
            {wardrobeItems.map((item) => {
              const isSelected = selectedIds.includes(item.id);
              return (
                <button
                  key={item.id}
                  className={`${styles.pickerItem} ${isSelected ? styles.pickerItemSelected : ''}`}
                  onClick={() => toggleItem(item.id)}
                  aria-pressed={isSelected}
                  aria-label={`${isSelected ? 'Remove' : 'Add'} ${item.category}`}
                >
                  {item.image_urls?.[0] ? (
                    <img src={item.image_urls[0]} alt={item.category} className={styles.pickerItemImage} />
                  ) : (
                    <div className={styles.pickerItemPlaceholder}><Shirt size={24} /></div>
                  )}
                  <span className={styles.pickerItemLabel}>{item.category}</span>
                  {isSelected && (
                    <span className={styles.checkBadge}>
                      <Check size={12} strokeWidth={3} />
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Validate CTA */}
      {error && (
        <p style={{ padding: '0 24px 12px', color: 'var(--color-error)', fontFamily: 'var(--font-family-body)', fontSize: '0.875rem' }}>
          {error}
        </p>
      )}
      <button
        className={styles.validateBtn}
        onClick={handleValidate}
        disabled={selectedIds.length === 0 || validating}
      >
        <Sparkles size={20} />
        Validate with AI
      </button>
    </div>
  );
}
