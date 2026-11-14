import React, { useState } from 'react';
import { CardDefinition, CardColor, CardType } from '../game/types';
import { ZoomIn, X, Sparkles } from 'lucide-react';

export interface CardViewProps {
  card?: CardDefinition | null;
  isBack?: boolean;
  backColor?: CardColor;
  size?: 'sm' | 'md' | 'lg' | 'hand' | 'compact';
  selected?: boolean;
  selectionType?: 'tableau' | 'reserve' | null;
  interactive?: boolean;
  onClick?: () => void;
  className?: string;
  badge?: React.ReactNode;
  showInspectButton?: boolean;
  highlighted?: boolean;
  disabled?: boolean;
}

const COLOR_MAP: Record<CardColor, {
  name: string;
  bg: string;
  border: string;
  text: string;
  accent: string;
  backFile: string;
  backSpriteClass: string;
}> = {
  city: {
    name: 'City',
    bg: 'bg-red-800',
    border: 'border-red-600',
    text: 'text-red-700',
    accent: '#dc2626',
    backFile: '/assets/cards/back_city.webp',
    backSpriteClass: 'bn-back-city',
  },
  desert: {
    name: 'Desert',
    bg: 'bg-amber-600',
    border: 'border-amber-500',
    text: 'text-amber-700',
    accent: '#d97706',
    backFile: '/assets/cards/back_desert.webp',
    backSpriteClass: 'bn-back-desert',
  },
  mountain: {
    name: 'Mountain',
    bg: 'bg-emerald-800',
    border: 'border-emerald-600',
    text: 'text-emerald-700',
    accent: '#16a34a',
    backFile: '/assets/cards/back_mountain.webp',
    backSpriteClass: 'bn-back-mountain',
  },
  water: {
    name: 'Water',
    bg: 'bg-sky-800',
    border: 'border-sky-600',
    text: 'text-sky-700',
    accent: '#0284c7',
    backFile: '/assets/cards/back_water.webp',
    backSpriteClass: 'bn-back-water',
  },
};

const TYPE_EMOJI: Record<CardType, string> = {
  bearfolk: '🐻',
  building: '🏛️',
  item: '🎒',
  plant: '🌿',
  animal: '🦊',
};

const CARD_BACK_SLOTS = [23, 45, 70, 97];

/**
 * Maps a 0-based spritesheet slotIndex (0..96, skipping card backs at 23, 45, 70, 97)
 * to the 1-based sequential WebP slice number (1..94) in public/assets/cards/manifest.json.
 */
export function getCardAssetId(slotIndex: number): number {
  const backsBefore = CARD_BACK_SLOTS.filter((b) => b < slotIndex).length;
  return slotIndex + 1 - backsBefore;
}

export const CardView: React.FC<CardViewProps> = ({
  card,
  isBack = false,
  backColor = 'water',
  size = 'md',
  selected = false,
  selectionType = null,
  interactive = false,
  onClick,
  className = '',
  badge,
  showInspectButton = true,
  highlighted = false,
  disabled = false,
}) => {
  const [spriteFailed, setSpriteFailed] = useState(false);
  const [imageFailed, setImageFailed] = useState(false);
  const [inspectOpen, setInspectOpen] = useState(false);

  // Determine size classes
  const sizeClasses = {
    compact: 'w-[54px] h-[84px] xs:w-[64px] xs:h-[100px] sm:w-[68px] sm:h-[106px] text-[8px] sm:text-[9px]',
    sm: 'w-[70px] h-[109px] xs:w-[78px] xs:h-[122px] sm:w-[90px] sm:h-[140px] text-[9px] sm:text-[10px]',
    md: 'w-[72px] h-[112px] xs:w-[86px] xs:h-[134px] sm:w-[125px] sm:h-[195px] md:w-[130px] md:h-[202px] text-[9px] sm:text-xs',
    lg: 'w-[130px] h-[202px] sm:w-[160px] sm:h-[250px] text-xs sm:text-sm',
    hand: 'w-[96px] h-[150px] xs:w-[110px] xs:h-[171px] sm:w-[145px] sm:h-[226px] md:w-[155px] md:h-[242px] text-[10px] sm:text-xs',
  }[size];

  // Selection styling
  let borderClasses = 'border-stone-400/80 shadow-md';
  if (selected) {
    if (selectionType === 'tableau') {
      borderClasses = 'ring-4 ring-amber-500 shadow-xl shadow-amber-500/40 -translate-y-2';
    } else if (selectionType === 'reserve') {
      borderClasses = 'ring-4 ring-sky-500 shadow-xl shadow-sky-500/40 -translate-y-2';
    } else {
      borderClasses = 'ring-4 ring-emerald-500 shadow-xl -translate-y-2';
    }
  } else if (highlighted) {
    borderClasses = 'ring-3 ring-emerald-400 shadow-lg animate-pulse';
  }

  const cursorClass = interactive && !disabled ? 'cursor-pointer hover:shadow-xl hover:-translate-y-1' : '';
  const disabledClass = disabled ? 'opacity-50 pointer-events-none' : '';

  // Render Card Back
  if (isBack || !card) {
    const colorInfo = COLOR_MAP[backColor];
    return (
      <div
        onClick={interactive && !disabled ? onClick : undefined}
        className={`relative rounded-md overflow-hidden transition-all duration-150 select-none bg-stone-900 ${sizeClasses} ${borderClasses} ${cursorClass} ${disabledClass} ${className}`}
        style={{ aspectRatio: '320 / 499' }}
      >
        {!imageFailed ? (
          <img
            src={colorInfo.backFile}
            alt={`${colorInfo.name} Card Back`}
            className="w-full h-full object-cover"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <div className={`w-full h-full flex flex-col items-center justify-center p-2 text-white ${colorInfo.bg}`}>
            <span className="text-xl sm:text-2xl opacity-80">🌲</span>
            <span className="font-serif font-bold text-xs uppercase tracking-wider mt-1">{colorInfo.name}</span>
            <div className="w-8 h-8 rounded-full border border-white/40 mt-2 flex items-center justify-center">
              <span className="text-xs">🐾</span>
            </div>
          </div>
        )}
      </div>
    );
  }

  const slot = card.slotIndex ?? card.spriteIndex ?? card.id;
  const paddedSlot = slot.toString().padStart(2, '0');
  const paddedAssetId = getCardAssetId(slot).toString().padStart(2, '0');
  const webpSrc = `/assets/cards/card_${paddedAssetId}.webp`;
  const colorInfo = COLOR_MAP[card.color] || COLOR_MAP.water;

  return (
    <>
      <div
        onClick={interactive && !disabled ? onClick : undefined}
        className={`relative group rounded-md overflow-hidden transition-all duration-150 select-none bg-stone-100 ${sizeClasses} ${borderClasses} ${cursorClass} ${disabledClass} ${className}`}
        style={{ aspectRatio: '320 / 499' }}
        data-card-id={card.id}
      >
        {/* Level 1: Primary CSS Spritesheet (use .bn-slot-XX to match 0-based spritesheet slot) */}
        {!spriteFailed ? (
          <div
            className={`bn-card-face bn-slot-${paddedSlot}`}
            onError={() => setSpriteFailed(true)}
            style={{
              width: '100%',
              height: '100%',
              backgroundImage: "url('/assets/cards/cards.jpg')",
              backgroundSize: '1000% 1000%',
            }}
          />
        ) : !imageFailed ? (
          /* Level 2: Fallback to individual WebP slice */
          <img
            src={webpSrc}
            alt={card.name}
            className="w-full h-full object-cover"
            onError={() => setImageFailed(true)}
          />
        ) : (
          /* Level 3: Clean Semantic SVG/Tailwind Card Fallback */
          <div className="w-full h-full flex flex-col justify-between p-2 bg-[#fdf6e7] border-2 border-[#6b4a2c]/40 text-[#3c2a18]">
            <div className="flex items-start justify-between gap-1">
              <div className="flex items-center gap-1">
                <span
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: colorInfo.accent }}
                  title={colorInfo.name}
                />
                <span className="font-serif font-bold text-[11px] leading-tight line-clamp-1">
                  {card.name}
                </span>
              </div>
              {card.beeHives > 0 && (
                <div className="flex items-center bg-amber-400 text-amber-950 font-bold px-1 rounded text-[9px] shadow-sm flex-shrink-0">
                  <span>🐝×{card.beeHives}</span>
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-1 my-1">
              {card.types.map((t) => (
                <span
                  key={t}
                  className="px-1 py-0.5 rounded bg-stone-200/80 text-stone-800 text-[9px] font-sans flex items-center gap-0.5"
                >
                  <span>{TYPE_EMOJI[t] || '•'}</span>
                  <span className="capitalize">{t}</span>
                </span>
              ))}
              {card.hasGoal && (
                <span className="px-1 py-0.5 rounded bg-amber-200 text-amber-900 font-bold text-[9px]">
                  GOAL
                </span>
              )}
            </div>

            <div className="bg-white/80 p-1.5 rounded border border-stone-200 text-[10px] leading-snug line-clamp-4">
              {card.text}
            </div>
          </div>
        )}

        {/* Selection Badge Overlay */}
        {selected && selectionType && (
          <div
            className={`absolute top-1 left-1/2 -translate-x-1/2 px-1.5 sm:px-2 py-0.5 rounded-full text-[8px] xs:text-[9px] sm:text-[10px] font-bold uppercase tracking-wider text-white shadow-md z-20 ${
              selectionType === 'tableau' ? 'bg-amber-600' : 'bg-sky-600'
            }`}
          >
            {selectionType === 'tableau' ? 'Tableau' : 'Reserve'}
          </div>
        )}

        {/* Custom Scored VP or Info Badge */}
        {badge && (
          <div className="absolute top-1 right-1 z-20">
            {badge}
          </div>
        )}

        {/* Inspect / Zoom Button - visible on touch devices or on desktop hover */}
        {showInspectButton && (
          <button
            type="button"
            title="Inspect Card Details"
            onClick={(e) => {
              e.stopPropagation();
              setInspectOpen(true);
            }}
            className="absolute bottom-1 right-1 p-1 bg-black/60 hover:bg-black/85 text-white rounded-full opacity-70 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity z-20 shadow cursor-pointer"
          >
            <ZoomIn className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
          </button>
        )}
      </div>

      {/* Inspect Modal Dialog */}
      {inspectOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={() => setInspectOpen(false)}
        >
          <div
            className="relative bg-[#f8f0de] border-4 border-[#6b4a2c] rounded-2xl p-4 sm:p-6 max-w-sm w-full shadow-2xl text-[#3c2a18] max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setInspectOpen(false)}
              className="absolute top-3 right-3 p-1.5 rounded-full bg-stone-300 hover:bg-stone-400 text-stone-800 transition"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Inspect Modal Header */}
            <div className="flex items-center gap-2 mb-3">
              <span
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: colorInfo.accent }}
              />
              <span className="font-serif font-black text-xl text-[#4e3218]">
                {card.name}
              </span>
            </div>

            {/* Card Graphic View */}
            <div className="mx-auto my-3 w-[180px] h-[280px] rounded-lg overflow-hidden border-2 border-[#6b4a2c]/50 shadow-md relative">
              <img
                src={webpSrc}
                alt={card.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/assets/cards/cards.jpg';
                }}
              />
            </div>

            {/* Meta Tags */}
            <div className="flex flex-wrap gap-1.5 justify-center my-3">
              <span className="px-2.5 py-1 rounded-full bg-stone-200 text-stone-800 text-xs font-semibold uppercase tracking-wider">
                Suit: {colorInfo.name}
              </span>
              {card.types.map((t) => (
                <span
                  key={t}
                  className="px-2.5 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-semibold capitalize flex items-center gap-1"
                >
                  <span>{TYPE_EMOJI[t]}</span> {t}
                </span>
              ))}
              {card.beeHives > 0 && (
                <span className="px-2.5 py-1 rounded-full bg-amber-400 text-amber-950 text-xs font-bold flex items-center gap-1">
                  🐝 {card.beeHives} {card.beeHives === 1 ? 'Hive Symbol' : 'Hive Symbols'}
                </span>
              )}
              {card.hasGoal && (
                <span className="px-2.5 py-1 rounded-full bg-rose-200 text-rose-900 text-xs font-bold">
                  Split Goal Card
                </span>
              )}
            </div>

            {/* Card Description */}
            <div className="bg-white/80 p-3 rounded-lg border border-[#6b4a2c]/30 text-xs sm:text-sm font-serif leading-relaxed mt-2 text-stone-900 shadow-inner">
              <div className="font-bold text-[#6b4a2c] mb-1 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                Activation Effect:
              </div>
              <p>{card.text}</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default CardView;
