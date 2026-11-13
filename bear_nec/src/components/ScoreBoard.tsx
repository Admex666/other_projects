import React from 'react';
import { PlayerState } from '../game/types';
import { Clock, Info } from 'lucide-react';
import GameIcon from './GameIcon';

export interface ScoreBoardProps {
  round: number; // 1 to 12
  player: PlayerState;
  opponent?: PlayerState | null;
  lastBeeWinnerName?: string | null;
  onExplainClick?: () => void;
  className?: string;
}

export const ScoreBoard: React.FC<ScoreBoardProps> = ({
  round,
  player,
  opponent,
  lastBeeWinnerName,
  onExplainClick,
  className = '',
}) => {
  // Determine current drafting cycle:
  // Cycle 1: rounds 1-4, Cycle 2: rounds 5-8, Cycle 3: rounds 9-12
  const cycleIndex = Math.floor((round - 1) / 4) + 1;
  const roundInCycle = ((round - 1) % 4) + 1;

  // Calculate projected end-game bee bonus
  let playerHives = 0;
  for (const r of player.tableau) {
    for (const c of r) {
      if (c) playerHives += c.beeHives;
    }
  }
  const projectedBeeBonus = playerHives * player.beeTokens;

  return (
    <div className={`w-full max-w-5xl mx-auto px-2 sm:px-4 ${className}`}>
      {/* Top Woodland Banner */}
      <div className="relative wood-banner rounded-2xl p-3 sm:p-4 text-stone-100 flex flex-wrap items-center justify-between gap-4">
        {/* Round & Cycle Info */}
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5 text-amber-200">
              <Clock className="w-4 h-4" />
              <span className="font-serif font-black text-lg sm:text-2xl tracking-wide">
                Round {Math.min(round, 12)} / 12
              </span>
            </div>
            {/* 4-round cycle badges */}
            <div className="flex items-center gap-1 mt-1 text-[11px] font-serif">
              <span className="text-amber-100/70 mr-1">Cycle {cycleIndex} of 3:</span>
              {[1, 2, 3, 4].map((step) => {
                const isActive = step === roundInCycle;
                const isPassed = step < roundInCycle;
                return (
                  <span
                    key={step}
                    className={`w-5 h-5 rounded-full flex items-center justify-center font-mono font-bold text-[10px] transition-all ${
                      isActive
                        ? 'bg-amber-400 text-amber-950 ring-2 ring-amber-300 scale-110 shadow'
                        : isPassed
                        ? 'bg-emerald-700 text-emerald-100'
                        : 'bg-black/30 text-stone-400'
                    }`}
                  >
                    {step}
                  </span>
                );
              })}
            </div>
          </div>
        </div>

        {/* Players Token Tray */}
        <div className="flex flex-wrap items-center gap-4 sm:gap-6 bg-black/25 px-4 py-2 rounded-xl border border-white/10 shadow-inner">
          {/* Player (You) */}
          <div className="flex items-center gap-3">
            <div className="flex flex-col items-end">
              <div className="flex items-center gap-1">
                <span className="font-serif font-bold text-sm text-amber-300">
                  {player.name} (You)
                </span>
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-700 text-emerald-100 font-bold uppercase">
                  Active
                </span>
              </div>
              <span className="text-[10px] text-stone-300 font-serif inline-flex items-center gap-1">
                <span>Bee Hives: {playerHives} × {player.beeTokens} = +{projectedBeeBonus}</span>
                <GameIcon type="vp" size="xs" />
                <span>VP</span>
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              {/* VP Tokens */}
              <div
                className="flex items-center gap-1.5 bg-gradient-to-b from-amber-400 to-amber-500 text-amber-950 font-black px-2.5 py-1 rounded-full shadow-md text-xs sm:text-sm"
                title="Current Victory Point Tokens"
              >
                <GameIcon type="vp" size="sm" />
                <span>{player.vpTokens} VP</span>
              </div>

              {/* Bee Tokens */}
              <div
                className="flex items-center gap-1.5 bg-gradient-to-b from-amber-100 to-amber-200 text-amber-950 font-black px-2.5 py-1 rounded-full shadow-md text-xs sm:text-sm border border-amber-400/80"
                title="Collected Bee Tokens (Multiplies Hive symbols at game end)"
              >
                <GameIcon type="beetoken" size="sm" />
                <span>{player.beeTokens}</span>
              </div>
            </div>
          </div>

          {/* Divider */}
          {opponent && <div className="h-8 w-px bg-white/20 hidden sm:block" />}

          {/* Opponent */}
          {opponent && (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                {/* VP Tokens */}
                <div
                  className="flex items-center gap-1.5 bg-gradient-to-b from-stone-200 to-stone-300 text-stone-900 font-black px-2.5 py-1 rounded-full shadow-md text-xs sm:text-sm"
                  title="Opponent's VP Tokens"
                >
                  <GameIcon type="vp" size="sm" />
                  <span>{opponent.vpTokens} VP</span>
                </div>

                {/* Bee Tokens */}
                <div
                  className="flex items-center gap-1.5 bg-gradient-to-b from-amber-100 to-amber-200 text-amber-950 font-black px-2.5 py-1 rounded-full shadow-md text-xs sm:text-sm border border-amber-400/80"
                  title="Opponent's Bee Tokens"
                >
                  <GameIcon type="beetoken" size="sm" />
                  <span>{opponent.beeTokens}</span>
                </div>
              </div>

              <div className="flex flex-col">
                <span className="font-serif font-bold text-sm text-stone-200">
                  {opponent.name}
                </span>
                <span className="text-[10px] text-stone-400 font-serif">
                  Hand: {opponent.hand.length} cards
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Bee Time Status Chip */}
        <div className="flex items-center gap-2">
          {lastBeeWinnerName ? (
            <div className="flex items-center gap-1.5 bg-amber-400/20 border border-amber-400/40 px-3 py-1.5 rounded-full text-xs text-amber-200">
              <GameIcon type="beetoken" size="xs" />
              <span className="font-serif font-bold">Bee Time:</span>
              <span className="text-white">{lastBeeWinnerName} won 1 Bee token</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 bg-black/20 border border-white/10 px-3 py-1.5 rounded-full text-xs text-stone-300">
              <GameIcon type="beetoken" size="xs" />
              <span className="font-serif">Bee Time: Awarded to lowest round scorer</span>
            </div>
          )}

          {onExplainClick && (
            <button
              onClick={onExplainClick}
              className="p-1.5 rounded-full bg-white/10 hover:bg-white/20 text-stone-200 transition"
              title="Explain scoring & rules"
            >
              <Info className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScoreBoard;
