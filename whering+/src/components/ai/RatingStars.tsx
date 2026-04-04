'use client';

import { useState } from 'react';
import { Star } from 'lucide-react';
import styles from './RatingStars.module.css';

interface RatingStarsProps {
  outfitId: string;
  initialRating?: number;
}

export function RatingStars({ outfitId, initialRating = 0 }: RatingStarsProps) {
  const [rating, setRating] = useState(initialRating);
  const [hover, setHover] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  const handleRate = async (value: number) => {
    if (submitting) return;
    setSubmitting(true);
    setRating(value);

    try {
      const res = await fetch(`/api/outfits/${outfitId}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ score: value }),
      });
      if (!res.ok) throw new Error('Failed to save rating');
    } catch (err) {
      console.error(err);
      // Fallback/Undo not implemented for simplicity in this MVP
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={styles.container}>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          className={styles.starButton}
          onMouseEnter={() => setHover(star)}
          onMouseLeave={() => setHover(0)}
          onClick={() => handleRate(star)}
          disabled={submitting}
        >
          <Star
            size={18}
            fill={(hover || rating) >= star ? 'var(--color-primary)' : 'none'}
            color={(hover || rating) >= star ? 'var(--color-primary)' : 'var(--color-on-surface-variant)'}
            style={{ opacity: submitting ? 0.5 : 1 }}
          />
        </button>
      ))}
      {rating > 0 && <span className={styles.label}>{rating}/5</span>}
    </div>
  );
}
