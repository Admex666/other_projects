import React, { useState } from 'react';
import { RoundSummary } from '../game/types';
import { History, ChevronDown, ChevronUp } from 'lucide-react';
import GameIcon from './GameIcon';

export interface GameHistoryProps {
  summaries: RoundSummary[];
  activePlayerId: string;
  defaultExpanded?: boolean;
}

export const GameHistory: React.FC<GameHistoryProps> = ({
  summaries,
  activePlayerId,
  defaultExpanded = false,
}) => {
  const [expanded, setExpanded] = useState<boolean>(defaultExpanded);

  // Show most recent round first (BoardGameArena log style)
  const orderedSummaries = [...summaries].reverse();

  return (
    <div className="w-full max-w-5xl mx-auto px-1 sm:px-4">
      <div className="rounded-2xl bg-[#faf3e6] border-2 border-[#6b4a2c]/60 shadow-md overflow-hidden">
        {/* Toggle Header */}
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="w-full px-3 sm:px-4 py-2.5 flex items-center justify-between bg-[#f4e6ca]/80 hover:bg-[#f4e6ca] transition text-[#4e3218] cursor-pointer"
        >
          <div className="flex items-center gap-2 font-serif font-bold text-xs sm:text-sm">
            <History className="w-4 h-4 text-amber-700" />
            <span>Game History</span>
            <span className="text-[10px] sm:text-[11px] font-mono font-normal bg-amber-100 text-amber-900 px-2 py-0.5 rounded-full border border-amber-300">
              {summaries.length} {summaries.length === 1 ? 'round' : 'rounds'}
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs font-serif text-stone-600">
            <span>{expanded ? 'Hide' : 'Show'}</span>
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>

        {/* Collapsible Content */}
        {expanded && (
          <div className="p-2.5 sm:p-4 max-h-64 sm:max-h-72 overflow-y-auto space-y-2 sm:space-y-2.5 border-t border-[#6b4a2c]/20">
            {orderedSummaries.length === 0 ? (
              <div className="text-center py-4 text-xs font-serif text-stone-500">
                No rounds completed yet. Detailed round logs will appear here after Round 1.
              </div>
            ) : (
              orderedSummaries.map((roundSum) => {
                const players = Object.values(roundSum.players).sort((a, b) => {
                  if (a.playerId === activePlayerId) return -1;
                  if (b.playerId === activePlayerId) return 1;
                  return 0;
                });

                const beeNames = roundSum.beeWinners
                  .map((id) => roundSum.players[id]?.playerName)
                  .filter(Boolean);

                return (
                  <div
                    key={roundSum.round}
                    className="rounded-xl bg-white/80 border border-[#6b4a2c]/20 p-3 text-xs font-serif"
                  >
                    <div className="flex items-center justify-between gap-2 pb-1.5 mb-2 border-b border-stone-200">
                      <span className="font-black text-[#4e3218]">
                        Round {roundSum.round}
                      </span>
                      {beeNames.length > 0 && (
                        <span className="text-[11px] bg-amber-100 text-amber-950 border border-amber-300 px-2 py-0.5 rounded-full font-bold">
                          🐝 Bee: {beeNames.join(' & ')}
                        </span>
                      )}
                    </div>

                    <div className="space-y-1.5">
                      {players.map((p) => (
                        <div key={p.playerId} className="flex flex-col gap-0.5">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-stone-800">
                              <strong className="text-[#4e3218]">{p.playerName}</strong> placed{' '}
                              <span className="font-semibold text-amber-900">{p.placedCard.name}</span>{' '}
                              <span className="text-[10px] font-mono text-stone-500">
                                ({p.position.row + 1},{p.position.col + 1})
                              </span>
                            </span>
                            <span className="font-mono font-bold text-emerald-700 shrink-0 flex items-center gap-1">
                              <span>+{p.totalRoundVp}</span>
                              <GameIcon type="vp" size="xs" />
                              <span>VP</span>
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-1 pl-2">
                            {p.activations.map((act, idx) => (
                              <span
                                key={`${act.cardId}-${idx}`}
                                className="text-[10px] bg-stone-100 border border-stone-200 text-stone-700 px-1.5 py-0.5 rounded inline-flex items-center gap-1"
                              >
                                <span>{idx + 1}. {act.cardName}: +{act.vp}</span>
                                <GameIcon type="vp" size="xs" />
                                <span>VP</span>
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default GameHistory;
