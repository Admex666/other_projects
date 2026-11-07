import React, { useState } from 'react';
import { CardDefinition } from '../game/types';
import CardView from './CardView';
import { Check, ShieldCheck, Grid, Sparkles, AlertCircle } from 'lucide-react';

export interface HandViewProps {
  hand: CardDefinition[];
  selectedTableauCardId: number | null;
  selectedReserveCardId: number | null;
  onSelectTableauCard: (cardId: number) => void;
  onSelectReserveCard: (cardId: number) => void;
  onConfirmMove: () => void;
  canConfirm: boolean;
  hasPlacementSelected: boolean;
  currentReserveCard?: CardDefinition | null;
  disabled?: boolean;
  round?: number;
}

export const HandView: React.FC<HandViewProps> = ({
  hand,
  selectedTableauCardId,
  selectedReserveCardId,
  onSelectTableauCard,
  onSelectReserveCard,
  onConfirmMove,
  canConfirm,
  hasPlacementSelected,
  currentReserveCard: _currentReserveCard,
  disabled = false,
  round: _round = 1,
}) => {
  // Active action drawer for clicked card on mobile or desktop quick select
  const [activeCardId, setActiveCardId] = useState<number | null>(null);

  const tableauCard = hand.find((c) => c.id === selectedTableauCardId);
  const reserveCard = hand.find((c) => c.id === selectedReserveCardId);

  return (
    <div className="relative w-full max-w-5xl mx-auto mt-4 px-2 sm:px-4">
      {/* Hand Container with Woodland aesthetic & picnic blanket pattern from bearnecessities.css */}
      <div className="relative rounded-2xl bg-[#faf3e6] border-2 border-[#6b4a2c] p-4 sm:p-5 shadow-xl">
        {/* Header & Status Indicator */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#6b4a2c]/20">
          <div>
            <h3 className="font-serif font-black text-lg sm:text-xl text-[#4e3218] flex items-center gap-2">
              <span>Your Hand</span>
              <span className="text-xs font-mono font-normal bg-amber-100 text-amber-900 px-2 py-0.5 rounded-full border border-amber-300">
                {hand.length} {hand.length === 1 ? 'card' : 'cards'}
              </span>
            </h3>
            <p className="text-xs text-stone-600 font-serif">
              Choose 1 card for your <span className="font-bold text-amber-700">Tableau</span> and 1 card for your <span className="font-bold text-sky-700">Reserve</span>.
            </p>
          </div>

          {/* Action Status Summary */}
          <div className="flex items-center gap-2 text-xs">
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border font-serif transition-colors ${
                selectedTableauCardId
                  ? 'bg-amber-100 border-amber-400 text-amber-950 font-bold'
                  : 'bg-stone-100 border-stone-300 text-stone-500'
              }`}
            >
              <Grid className="w-4 h-4 text-amber-600" />
              <span>Tableau: {tableauCard ? tableauCard.name : 'Choose card'}</span>
            </div>

            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border font-serif transition-colors ${
                selectedReserveCardId
                  ? 'bg-sky-100 border-sky-400 text-sky-950 font-bold'
                  : 'bg-stone-100 border-stone-300 text-stone-500'
              }`}
            >
              <ShieldCheck className="w-4 h-4 text-sky-600" />
              <span>Reserve: {reserveCard ? reserveCard.name : 'Choose card'}</span>
            </div>
          </div>
        </div>

        {/* Hand Cards Grid / Row */}
        <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4 py-4 min-h-[240px]">
          {hand.map((card) => {
            const isTableau = card.id === selectedTableauCardId;
            const isReserve = card.id === selectedReserveCardId;
            const isSelected = isTableau || isReserve;
            const selectionType = isTableau ? 'tableau' : isReserve ? 'reserve' : null;

            return (
              <div
                key={card.id}
                className="flex flex-col items-center gap-2 group transition-transform"
              >
                <div
                  onClick={() => {
                    if (disabled) return;
                    // Toggle active drawer or auto assign
                    if (isTableau) {
                      onSelectTableauCard(-1);
                    } else if (isReserve) {
                      onSelectReserveCard(-1);
                    } else if (!selectedTableauCardId) {
                      onSelectTableauCard(card.id);
                    } else if (!selectedReserveCardId) {
                      onSelectReserveCard(card.id);
                    } else {
                      setActiveCardId(activeCardId === card.id ? null : card.id);
                    }
                  }}
                >
                  <CardView
                    card={card}
                    size="hand"
                    selected={isSelected}
                    selectionType={selectionType}
                    interactive={!disabled}
                    className="cursor-pointer"
                  />
                </div>

                {/* Direct Action Buttons under each card */}
                <div className="flex gap-1">
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() => {
                      if (isTableau) {
                        onSelectTableauCard(-1);
                      } else {
                        onSelectTableauCard(card.id);
                      }
                    }}
                    className={`px-2 py-1 rounded text-[11px] font-bold font-serif transition-colors shadow-sm ${
                      isTableau
                        ? 'bg-amber-600 hover:bg-amber-700 text-white ring-2 ring-amber-400'
                        : 'bg-[#f4e6ca] hover:bg-amber-200 text-[#4e3218] border border-[#6b4a2c]/40'
                    }`}
                  >
                    {isTableau ? '✓ Tableau' : '+ Tableau'}
                  </button>

                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() => {
                      if (isReserve) {
                        onSelectReserveCard(-1);
                      } else {
                        onSelectReserveCard(card.id);
                      }
                    }}
                    className={`px-2 py-1 rounded text-[11px] font-bold font-serif transition-colors shadow-sm ${
                      isReserve
                        ? 'bg-sky-600 hover:bg-sky-700 text-white ring-2 ring-sky-400'
                        : 'bg-[#f4e6ca] hover:bg-sky-200 text-[#4e3218] border border-[#6b4a2c]/40'
                    }`}
                  >
                    {isReserve ? '✓ Reserve' : '+ Reserve'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Action Bar & Confirm Move Section */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-3 mt-2 border-t border-[#6b4a2c]/20 bg-[#f4e6ca]/60 p-3 rounded-xl">
          {/* Instructions / Validation status */}
          <div className="flex items-center gap-2 text-xs sm:text-sm font-serif">
            {!selectedTableauCardId ? (
              <span className="text-amber-800 flex items-center gap-1.5 font-bold">
                <AlertCircle className="w-4 h-4 text-amber-600" />
                Select 1 card to play to your Tableau.
              </span>
            ) : !selectedReserveCardId ? (
              <span className="text-sky-800 flex items-center gap-1.5 font-bold">
                <AlertCircle className="w-4 h-4 text-sky-600" />
                Select 1 card to keep in your Reserve.
              </span>
            ) : !hasPlacementSelected ? (
              <span className="text-emerald-800 flex items-center gap-1.5 font-bold animate-pulse">
                <Grid className="w-4 h-4 text-emerald-600" />
                Now click an empty glowing slot in your grid to place "{tableauCard?.name}".
              </span>
            ) : (
              <span className="text-emerald-900 flex items-center gap-1.5 font-bold">
                <Check className="w-4 h-4 text-emerald-600" />
                All set! Confirm your move to place and activate.
              </span>
            )}
          </div>

          {/* Confirm Move Button */}
          <button
            type="button"
            disabled={!canConfirm || disabled}
            onClick={onConfirmMove}
            className={`px-6 py-2.5 rounded-full font-serif font-black text-sm uppercase tracking-wider flex items-center gap-2 transition-all shadow-lg ${
              canConfirm && !disabled
                ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white cursor-pointer transform hover:scale-105 active:scale-95 shadow-emerald-700/30 ring-2 ring-emerald-400'
                : 'bg-stone-300 text-stone-500 cursor-not-allowed opacity-70'
            }`}
          >
            <Sparkles className="w-4 h-4 text-amber-300" />
            <span>Confirm Move</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default HandView;
