import React, { useState } from 'react';
import { PlayerState } from '../game/types';
import TableauGrid from './TableauGrid';
import CardView from './CardView';
import GameIcon from './GameIcon';
import { ChevronDown, ChevronUp } from 'lucide-react';

export interface OpponentBoardProps {
  opponent: PlayerState;
  className?: string;
}

export const OpponentBoard: React.FC<OpponentBoardProps> = ({
  opponent,
  className = '',
}) => {
  const [collapsed, setCollapsed] = useState(false);

  // Compute opponent hives
  let opponentHives = 0;
  for (const r of opponent.tableau) {
    for (const c of r) {
      if (c) opponentHives += c.beeHives;
    }
  }

  return (
    <div
      className={`rounded-2xl bg-[#f4e8d2] border-2 border-[#6b4a2c]/60 p-2.5 sm:p-4 shadow-lg ${className}`}
    >
      {/* Header with Opponent Name and Token Overview */}
      <div className="flex flex-wrap items-center justify-between gap-1.5 sm:gap-2 mb-2 sm:mb-3 pb-2 border-b border-[#6b4a2c]/20">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <span className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-stone-500 animate-pulse" />
          <h4 className="font-serif font-black text-xs sm:text-base text-[#4e3218]">
            {opponent.name}'s Tableau
          </h4>
        </div>

        <div className="flex items-center gap-1 sm:gap-2 text-[10px] sm:text-xs font-serif">
          <span className="px-1.5 sm:px-2 py-0.5 rounded-full bg-stone-200 text-stone-800 font-bold border border-stone-300 flex items-center gap-0.5 sm:gap-1">
            <GameIcon type="vp" size="xs" /> {opponent.vpTokens} VP
          </span>
          <span className="px-1.5 sm:px-2 py-0.5 rounded-full bg-amber-200 text-amber-950 font-bold border border-amber-300 flex items-center gap-0.5 sm:gap-1">
            <GameIcon type="beetoken" size="xs" /> {opponent.beeTokens} Bees ({opponentHives} Hives)
          </span>
          <button
            type="button"
            onClick={() => setCollapsed(!collapsed)}
            className="sm:hidden px-1.5 py-0.5 rounded bg-stone-300/70 text-stone-700 font-bold text-[10px] flex items-center gap-0.5 cursor-pointer"
          >
            <span>{collapsed ? 'Show' : 'Hide'}</span>
            {collapsed ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
          </button>
        </div>
      </div>

      {!collapsed && (
        <>
          {/* Opponent's Tableau (Compact Grid) */}
          <div className="flex justify-center overflow-x-auto py-1">
            <TableauGrid
              tableau={opponent.tableau}
              size="compact"
              readOnly={true}
              className="border border-[#6b4a2c]/40 bg-[#eee2c9]/80 shadow-none p-1.5 sm:p-2"
            />
          </div>

          {/* Opponent's Hand Size (Shown with colored Card Backs based on suit) */}
          <div className="flex items-center justify-between mt-2 sm:mt-3 pt-2 border-t border-[#6b4a2c]/15 text-[10px] sm:text-xs text-stone-600 font-serif">
            <span>Cards in Hand ({opponent.hand.length}):</span>
            <div className="flex items-center gap-1 sm:gap-1.5 flex-wrap justify-end">
              {opponent.hand.length === 0 ? (
                <span className="italic text-stone-400">Empty</span>
              ) : (
                opponent.hand.map((card, idx) => (
                  <div
                    key={idx}
                    className="w-5 h-8 sm:w-7 sm:h-11 transform hover:-translate-y-1 transition duration-150"
                    title={`Opponent Card (${card.color || 'hidden'})`}
                  >
                    <CardView
                      isBack={true}
                      backColor={card.color}
                      size="compact"
                      interactive={false}
                      className="w-full h-full shadow-md rounded pointer-events-none"
                    />
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default OpponentBoard;
