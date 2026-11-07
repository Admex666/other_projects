import React from 'react';
import { PlayerState } from '../game/types';
import TableauGrid from './TableauGrid';

export interface OpponentBoardProps {
  opponent: PlayerState;
  className?: string;
}

export const OpponentBoard: React.FC<OpponentBoardProps> = ({
  opponent,
  className = '',
}) => {
  // Compute opponent hives
  let opponentHives = 0;
  for (const r of opponent.tableau) {
    for (const c of r) {
      if (c) opponentHives += c.beeHives;
    }
  }

  return (
    <div
      className={`rounded-2xl bg-[#f4e8d2] border-2 border-[#6b4a2c]/60 p-3 sm:p-4 shadow-lg ${className}`}
    >
      {/* Header with Opponent Name and Token Overview */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2 border-b border-[#6b4a2c]/20">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-stone-500 animate-pulse" />
          <h4 className="font-serif font-black text-sm sm:text-base text-[#4e3218]">
            {opponent.name}'s Tableau
          </h4>
        </div>

        <div className="flex items-center gap-2 text-xs font-serif">
          <span className="px-2 py-0.5 rounded-full bg-stone-200 text-stone-800 font-bold border border-stone-300">
            🏆 {opponent.vpTokens} VP
          </span>
          <span className="px-2 py-0.5 rounded-full bg-amber-200 text-amber-900 font-bold border border-amber-300">
            🐝 {opponent.beeTokens} Bees ({opponentHives} Hives)
          </span>
        </div>
      </div>

      {/* Opponent's Tableau (Compact Grid) */}
      <div className="flex justify-center overflow-x-auto py-1">
        <TableauGrid
          tableau={opponent.tableau}
          size="compact"
          readOnly={true}
          className="border border-[#6b4a2c]/40 bg-[#eee2c9]/80 shadow-none p-2"
        />
      </div>

      {/* Opponent's Hand Size (Shown as Face-down Cards) */}
      <div className="flex items-center justify-between mt-3 pt-2 border-t border-[#6b4a2c]/15 text-xs text-stone-600 font-serif">
        <span>Cards in Hand ({opponent.hand.length}):</span>
        <div className="flex items-center gap-1">
          {opponent.hand.length === 0 ? (
            <span className="italic text-stone-400">Empty</span>
          ) : (
            opponent.hand.map((_, idx) => (
              <div
                key={idx}
                className="w-5 h-8 rounded border border-stone-600 bg-stone-800 shadow-sm"
                title="Secret Card"
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default OpponentBoard;
