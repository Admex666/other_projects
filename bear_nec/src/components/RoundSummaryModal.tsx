import React from 'react';
import { RoundSummary, PlayerRoundSummary } from '../game/types';
import { Check, Loader2, Sparkles, ArrowRight } from 'lucide-react';
import GameIcon from './GameIcon';

export interface RoundSummaryModalProps {
  summary: RoundSummary;
  activePlayerId: string;
  isMultiplayer?: boolean;
  readyPlayerIds?: string[];
  hasClickedReady?: boolean;
  onReady: () => void;
}

const COLOR_BADGE: Record<string, string> = {
  city: 'bg-amber-200 text-amber-950 border-amber-400',
  desert: 'bg-orange-200 text-orange-950 border-orange-400',
  mountain: 'bg-stone-300 text-stone-900 border-stone-400',
  water: 'bg-sky-200 text-sky-950 border-sky-400',
};

export const RoundSummaryModal: React.FC<RoundSummaryModalProps> = ({
  summary,
  activePlayerId,
  isMultiplayer = false,
  readyPlayerIds = [],
  hasClickedReady = false,
  onReady,
}) => {
  const playerEntries = Object.values(summary.players);
  // Put active player first for clarity
  const sortedPlayers: PlayerRoundSummary[] = [...playerEntries].sort((a, b) => {
    if (a.playerId === activePlayerId) return -1;
    if (b.playerId === activePlayerId) return 1;
    return 0;
  });

  const opponent = sortedPlayers.find((p) => p.playerId !== activePlayerId);
  const opponentReady = opponent ? readyPlayerIds.includes(opponent.playerId) : false;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="wood-panel rounded-3xl p-5 sm:p-7 max-w-2xl w-full shadow-2xl text-[#3c2a18] max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="text-center mb-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-200/80 border border-amber-400 text-amber-950 font-mono text-xs font-bold uppercase tracking-wider mb-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-700" />
            <span>Round {summary.round} of 12</span>
          </div>
          <h2 className="font-serif font-black text-2xl sm:text-3xl text-[#4e3218]">
            {summary.isGameOver ? 'Final Round Complete!' : `Round ${summary.round} Summary`}
          </h2>
        </div>

        {/* Player Breakdowns */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
          {sortedPlayers.map((p) => {
            const isSelf = p.playerId === activePlayerId;
            return (
              <div
                key={p.playerId}
                className={`rounded-2xl p-4 border-2 shadow-sm ${
                  isSelf
                    ? 'bg-amber-50/90 border-amber-400'
                    : 'bg-white/80 border-[#6b4a2c]/30'
                }`}
              >
                <div className="flex items-center justify-between gap-2 pb-2 mb-2.5 border-b border-[#6b4a2c]/20">
                  <div>
                    <div className="font-serif font-black text-base text-[#4e3218] flex items-center gap-1.5">
                      <span>{p.playerName}</span>
                      {isSelf && (
                        <span className="text-[10px] font-mono uppercase bg-amber-500 text-white px-1.5 py-0.5 rounded">
                          You
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] font-serif text-stone-600 mt-0.5">
                      Placed{' '}
                      <span
                        className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-bold ${
                          COLOR_BADGE[p.placedCard.color] || 'bg-stone-100'
                        }`}
                      >
                        {p.placedCard.name}
                      </span>{' '}
                      at ({p.position.row + 1},{p.position.col + 1})
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="font-mono font-black text-lg text-emerald-700 flex items-center justify-end gap-1">
                      <span>+{p.totalRoundVp}</span>
                      <GameIcon type="vp" size="sm" />
                      <span>VP</span>
                    </div>
                    <div className="text-[10px] font-mono text-stone-500 flex items-center justify-end gap-1">
                      <span>Total: {p.totalVpTokens}</span>
                      <GameIcon type="vp" size="xs" />
                      <span>VP</span>
                    </div>
                  </div>
                </div>

                {/* Activation Breakdown */}
                <div className="space-y-1.5">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-stone-500 font-bold">
                    Activation Order
                  </div>
                  {p.activations.map((act, idx) => (
                    <div
                      key={`${act.cardId}-${idx}`}
                      className="flex items-center justify-between text-xs font-serif bg-white/70 px-2.5 py-1.5 rounded-lg border border-stone-200"
                    >
                      <div className="flex items-center gap-1.5 min-w-0">
                        <span className="w-4 h-4 rounded-full bg-[#6b4a2c]/15 text-[#4e3218] font-mono text-[10px] font-bold flex items-center justify-center shrink-0">
                          {idx + 1}
                        </span>
                        <span className="truncate font-semibold text-stone-800">
                          {act.cardName}
                        </span>
                        <span className="text-[10px] text-stone-500 shrink-0">
                          {act.isPlacedCard ? '(Placed)' : '(Adj.)'}
                        </span>
                      </div>
                      <span
                        className={`font-mono font-bold shrink-0 ml-2 flex items-center gap-1 ${
                          act.vp > 0 ? 'text-emerald-700' : 'text-stone-400'
                        }`}
                      >
                        <span>+{act.vp}</span>
                        <GameIcon type="vp" size="xs" />
                        <span>VP</span>
                      </span>
                    </div>
                  ))}
                </div>

                {/* Bee Token */}
                {p.receivedBeeToken && (
                  <div className="mt-3 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-amber-200/80 border border-amber-400 text-amber-950 font-serif font-bold text-xs">
                    <span>🐝</span>
                    <span>+1 Bee Token (Bee Time!)</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Multiplayer Ready Status */}
        {isMultiplayer && (
          <div className="mb-4 flex flex-wrap items-center justify-center gap-3 text-xs font-serif">
            <div
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full border ${
                hasClickedReady
                  ? 'bg-emerald-100 border-emerald-400 text-emerald-900 font-bold'
                  : 'bg-stone-100 border-stone-300 text-stone-600'
              }`}
            >
              {hasClickedReady ? <Check className="w-3.5 h-3.5" /> : null}
              <span>You: {hasClickedReady ? 'Ready' : 'Reviewing'}</span>
            </div>

            {opponent && (
              <div
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full border ${
                  opponentReady
                    ? 'bg-emerald-100 border-emerald-400 text-emerald-900 font-bold'
                    : 'bg-stone-100 border-stone-300 text-stone-600'
                }`}
              >
                {opponentReady ? (
                  <Check className="w-3.5 h-3.5" />
                ) : (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-600" />
                )}
                <span>
                  {opponent.playerName}: {opponentReady ? 'Ready' : 'Reviewing...'}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Ready Button */}
        <button
          type="button"
          disabled={isMultiplayer && hasClickedReady}
          onClick={onReady}
          className={`w-full py-3.5 rounded-full font-serif font-black text-sm uppercase tracking-wider shadow-xl flex items-center justify-center gap-2 transition ${
            isMultiplayer && hasClickedReady
              ? 'bg-stone-300 text-stone-600 cursor-not-allowed'
              : 'bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white cursor-pointer transform active:scale-95'
          }`}
        >
          {isMultiplayer && hasClickedReady ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Waiting for Opponent...</span>
            </>
          ) : (
            <>
              <span>
                {summary.isGameOver
                  ? 'Ready — View Final Results'
                  : `Ready for Round ${summary.round + 1}`}
              </span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default RoundSummaryModal;
