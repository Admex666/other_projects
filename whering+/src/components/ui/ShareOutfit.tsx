'use client';

import { useState } from 'react';
import { Share2, Copy, Check } from 'lucide-react';
import styles from './ShareOutfit.module.css';

interface ShareOutfitProps {
  headline: string;
  score: number;
}

export function ShareOutfit({ headline, score }: ShareOutfitProps) {
  const [copied, setCopied] = useState(false);

  const shareText = `Feeling my style today: "${headline}" (Confidence score: ${score}%). Personalised styling by Digital Atelier AI. ✨`;
  const shareUrl = typeof window !== 'undefined' ? window.location.href : '';

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Digital Atelier | My Outfit',
          text: shareText,
          url: shareUrl,
        });
      } catch (err) {
        console.error('Error sharing:', err);
      }
    } else {
      handleCopy();
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(`${shareText}\n\nCheck out my look: ${shareUrl}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={styles.container}>
      <button className={styles.shareButton} onClick={handleShare}>
        <Share2 size={18} />
        <span>Share Look</span>
      </button>
      
      <button className={styles.copyButton} onClick={handleCopy}>
        {copied ? <Check size={18} color="#2e7d32" /> : <Copy size={18} />}
        <span>{copied ? 'Copied!' : 'Copy Link'}</span>
      </button>
    </div>
  );
}
