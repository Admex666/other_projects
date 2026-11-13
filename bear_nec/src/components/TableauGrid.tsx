import React from 'react';
import { Tableau, GridPosition } from '../game/types';
import CardView from './CardView';
import GameIcon from './GameIcon';
import { Plus } from 'lucide-react';

export interface TableauGridProps {
  tableau: Tableau;
  selectedPlacement?: GridPosition | null;
  validPlacements?: GridPosition[];
  onSelectPosition?: (pos: GridPosition) => void;
  activationOrder?: number[];
  onSelectNeighborOrder?: (cardId: number) => void;
  activePlacementPos?: GridPosition | null;
  activatedNeighbors?: GridPosition[];
  lastScoredPos?: GridPosition | null;
  lastScoreAmount?: number | null;
  size?: 'sm' | 'md' | 'compact';
  readOnly?: boolean;
  className?: string;
}

export const TableauGrid: React.FC<TableauGridProps> = ({
  tableau,
  selectedPlacement,
  validPlacements = [],
  onSelectPosition,
  activationOrder = [],
  onSelectNeighborOrder,
  activePlacementPos,
  activatedNeighbors = [],
  lastScoredPos,
  lastScoreAmount,
  size = 'md',
  readOnly = false,
  className = '',
}) => {
  const isPosEqual = (p1?: GridPosition | null, p2?: GridPosition | null) =>
    p1 && p2 && p1.row === p2.row && p1.col === p2.col;

  const isAdjacentToSelected = (row: number, col: number) => {
    if (!selectedPlacement) return false;
    const dr = Math.abs(selectedPlacement.row - row);
    const dc = Math.abs(selectedPlacement.col - col);
    return dr + dc === 1;
  };

  const isValidTarget = (row: number, col: number) =>
    !readOnly && validPlacements.some((p) => p.row === row && p.col === col);

  const isActivated = (row: number, col: number) =>
    activatedNeighbors.some((p) => p.row === row && p.col === col);

  // Cell sizing matching bearnecessities.css grid rules
  const cellSizes = {
    compact: 'w-[68px] h-[106px]',
    sm: 'w-[90px] h-[140px]',
    md: 'w-[125px] h-[195px] sm:w-[130px] sm:h-[202px]',
  }[size];

  return (
    <div
      className={`relative inline-block p-3 sm:p-4 rounded-2xl bg-gradient-to-b from-[#f7eedc] to-[#ebd8b7] border-2 border-[#6b4a2c] shadow-xl ${className}`}
    >
      {/* 4 columns x 3 rows grid */}
      <div className="grid grid-cols-4 gap-2 sm:gap-2.5">
        {Array.from({ length: 3 }).map((_, row) =>
          Array.from({ length: 4 }).map((_, col) => {
            const card = tableau[row]?.[col] || null;
            const valid = isValidTarget(row, col);
            const isSelected = isPosEqual(selectedPlacement, { row, col });
            const isPlacedJustNow = isPosEqual(activePlacementPos, { row, col });
            const isNeighborActivating = isActivated(row, col);
            const isScored = isPosEqual(lastScoredPos, { row, col });

            if (card) {
              const isAdjNeighbor = !readOnly && isAdjacentToSelected(row, col);
              const orderIdx = isAdjNeighbor ? activationOrder.indexOf(card.id) : -1;
              const showOrderBadge = isAdjNeighbor && activationOrder.length >= 2 && orderIdx !== -1;

              return (
                <div
                  key={`${row}-${col}`}
                  onClick={() => {
                    if (isAdjNeighbor && onSelectNeighborOrder) {
                      onSelectNeighborOrder(card.id);
                    }
                  }}
                  className={`relative ${cellSizes} rounded-md transition-transform duration-200 ${
                    isPlacedJustNow ? 'ring-4 ring-amber-400 shadow-xl scale-[1.03] z-10' : ''
                  } ${
                    isNeighborActivating ? 'ring-3 ring-emerald-500 animate-pulse z-10' : ''
                  } ${
                    isAdjNeighbor && onSelectNeighborOrder
                      ? 'ring-2 ring-sky-400 cursor-pointer hover:scale-[1.02] z-10'
                      : ''
                  }`}
                >
                  <CardView
                    card={card}
                    size={size}
                    showInspectButton={true}
                    badge={
                      showOrderBadge ? (
                        <div className="px-2 py-0.5 rounded-full bg-sky-600 text-white font-mono font-black text-[11px] shadow-lg border border-white">
                          #{orderIdx + 1}
                        </div>
                      ) : isScored && lastScoreAmount !== null && lastScoreAmount !== undefined ? (
                        <div className="px-1.5 py-0.5 rounded-full bg-amber-500 text-amber-950 font-black text-[11px] shadow-lg animate-bounce flex items-center gap-0.5">
                          <span>+{lastScoreAmount}</span>
                          <GameIcon type="vp" size="xs" />
                          <span>VP</span>
                        </div>
                      ) : undefined
                    }
                  />

                  {/* Coordinates indicator overlay */}
                  <div className="absolute bottom-0.5 left-1 text-[8px] font-mono text-stone-500/80 pointer-events-none select-none">
                    {row + 1},{col + 1}
                  </div>
                </div>
              );
            }

            // Empty Slot
            return (
              <div
                key={`${row}-${col}`}
                onClick={() => {
                  if (valid && onSelectPosition) {
                    onSelectPosition({ row, col });
                  }
                }}
                className={`relative ${cellSizes} rounded-md flex flex-col items-center justify-center transition-all duration-200 select-none ${
                  valid
                    ? 'cursor-pointer border-2 border-dashed border-[#2f7d4f] bg-emerald-500/10 hover:bg-emerald-500/25 animate-bn-glow shadow-md hover:scale-[1.02]'
                    : 'border-2 border-dashed border-[#6b4a2c]/30 bg-[#6b4a2c]/5'
                } ${
                  isSelected
                    ? 'ring-4 ring-amber-500 bg-amber-500/30 border-amber-600 scale-[1.03]'
                    : ''
                }`}
              >
                {valid ? (
                  <div className="flex flex-col items-center text-[#2f7d4f] transition-transform">
                    <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-emerald-600/20 flex items-center justify-center text-emerald-800">
                      <Plus className="w-5 h-5 stroke-[2.5]" />
                    </div>
                    <span className="text-[10px] font-bold font-serif tracking-wider uppercase mt-1">
                      {isSelected ? 'Selected' : 'Place'}
                    </span>
                  </div>
                ) : (
                  <span className="text-[10px] font-mono text-stone-400 select-none">
                    {row + 1},{col + 1}
                  </span>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default TableauGrid;
