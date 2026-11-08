import React from 'react';

export type IconType = 'vp' | 'beehive' | 'beetoken' | 'cards' | 'leaf' | 'wood' | 'honey';

export interface GameIconProps {
  type: IconType;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  title?: string;
}

const SIZE_MAP: Record<'xs' | 'sm' | 'md' | 'lg' | 'xl', string> = {
  xs: 'w-3.5 h-3.5',
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
  xl: 'w-8 h-8',
};

const ICON_FALLBACK_EMOJI: Record<IconType, string> = {
  vp: '🏆',
  beehive: '🍯',
  beetoken: '🐝',
  cards: '🃏',
  leaf: '🍃',
  wood: '🪵',
  honey: '🍯',
};

const ICON_FILENAMES: Record<IconType, string[]> = {
  vp: [
    '/assets/icons/vp_token.webp',
    '/assets/icons/vp.webp',
    '/assets/icons/vp_token.png',
    '/assets/icons/vp.png',
  ],
  beehive: [
    '/assets/icons/beehive.webp',
    '/assets/icons/beehive.png',
  ],
  beetoken: [
    '/assets/icons/beetoken.webp',
    '/assets/icons/bee_token.webp',
    '/assets/icons/beetoken.png',
    '/assets/icons/bee_token.png',
  ],
  cards: ['/assets/icons/cards.webp', '/assets/icons/cards.png'],
  leaf: ['/assets/icons/leaf.webp', '/assets/icons/leaf.png'],
  wood: ['/assets/icons/wood.webp', '/assets/icons/wood.png'],
  honey: ['/assets/icons/honey.webp', '/assets/icons/honey.png'],
};

export const GameIcon: React.FC<GameIconProps> = ({
  type,
  size = 'md',
  className = '',
  title,
}) => {
  const [candidateIndex, setCandidateIndex] = React.useState(0);
  const sizeClass = SIZE_MAP[size];
  const candidates = ICON_FILENAMES[type] || [];
  const currentUrl = candidates[candidateIndex];

  if (!currentUrl) {
    return (
      <span
        className={`inline-flex items-center justify-center select-none text-center ${className}`}
        title={title || type}
      >
        {ICON_FALLBACK_EMOJI[type]}
      </span>
    );
  }

  return (
    <img
      src={currentUrl}
      alt={type}
      title={title || type}
      onError={() => {
        // Try next candidate format (e.g. webp -> png), or fallback to emoji
        setCandidateIndex((prev) => prev + 1);
      }}
      className={`inline-block object-contain align-middle drop-shadow-sm ${sizeClass} ${className}`}
    />
  );
};

export default GameIcon;
