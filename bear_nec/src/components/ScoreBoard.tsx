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

function countTableauHives(player?: PlayerState | null): number {
  if (!player) return 0;
  let count = 0;
  for (const r of player.tableau) {
    for (const c of r) {
      if (c) count += c.beeHives;
    }
  }
  return count;
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

  // Player calculations
  const playerHives = countTableauHives(player);
  const playerBeeBonus = playerHives * player.beeTokens;
  const playerProjectedTotal = player.vpTokens + playerBeeBonus;

  // Opponent calculations
  const oppHives = countTableauHives(opponent);
  const oppBeeBonus = oppHives * (opponent?.beeTokens || 0);
  const oppProjectedTotal = (opponent?.vpTokens || 0) + oppBeeBonus;

  return (
    <div className={`w-full max-w-5xl mx-auto px-1 sm:px-4 ${className}`}>
      {/* Top Woodland Banner */}
      <div className="relative wood-banner rounded-2xl p-2.5 sm:p-4 text-stone-100 flex flex-wrap items-center justify-between gap-2.5 sm:gap-4">
        {/* Round & Cycle Info */}
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5 text-amber-200">
              <Clock className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              <span className="font-serif font-black text-base sm:text-2xl tracking-wide">
                Round {Math.min(round, 12)} / 12
              </span>
            </div>
            {/* 4-round cycle badges */}
            <div className="flex items-center gap-1 mt-0.5 sm:mt-1 text-[10px] sm:text-[11px] font-serif">
              <span className="text-amber-100/70 mr-1">Cycle {cycleIndex} of 3:</span>
              {[1, 2, 3, 4].map((step) => {
                const isActive = step === roundInCycle;
                const isPassed = step < roundInCycle;
                return (
                  <span
                    key={step}
                    className={`w-4 h-4 sm:w-5 sm:h-5 rounded-full flex items-center justify-center font-mono font-bold text-[9px] sm:text-[10px] transition-all ${
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
        <div className="flex flex-wrap items-center gap-2 sm:gap-6 bg-black/35 px-2.5 sm:px-4 py-2 sm:py-2.5 rounded-xl border border-white/10 shadow-inner w-full sm:w-auto justify-between sm:justify-start">
          {/* Player (You) */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3">
            <div className="flex flex-col items-start sm:items-end">
              <div className="flex items-center gap-1">
                <span className="font-serif font-bold text-xs sm:text-sm text-amber-300">
                  {player.name} (You)
                </span>
                <span className="px-1.5 py-0.2 rounded text-[9px] sm:text-[10px] bg-emerald-700 text-emerald-100 font-bold uppercase">
                  Active
                </span>
              </div>
            </div>

            {/* Score Equation Chips */}
            <div className="flex items-center gap-1 sm:gap-1.5 flex-wrap">
              {/* Bees × Hives formula badge */}
              <div
                className="flex items-center gap-1 bg-amber-950/60 border border-amber-500/40 px-2 py-0.5 rounded-lg text-xs font-mono shadow-sm"
                title={`Kaptár bónusz: ${player.beeTokens} méh zseton × ${playerHives} kaptár szimbólum a tablón = +${playerBeeBonus} VP`}
              >
                <div className="flex items-center gap-0.5 text-amber-300 font-bold">
                  <GameIcon type="beetoken" size="xs" />
                  <span>{player.beeTokens}</span>
                </div>
                <span className="text-amber-200/70 font-sans font-bold">×</span>
                <div className="flex items-center gap-0.5 text-amber-300 font-bold">
                  <GameIcon type="beehive" size="xs" />
                  <span>{playerHives}</span>
                </div>
                <span className="text-amber-200/70 font-sans font-bold">=</span>
                <span className="text-amber-300 font-black">+{playerBeeBonus}</span>
              </div>

              <span className="text-white/60 font-bold text-xs sm:text-sm">+</span>

              {/* Base VP Tokens */}
              <div
                className="flex items-center gap-1 bg-gradient-to-b from-amber-400/90 to-amber-500/90 text-amber-950 font-black px-2 py-0.5 sm:py-1 rounded-lg shadow-sm text-xs"
                title="Sima begyűjtött győzelmi pontok (VP zsetonok)"
              >
                <GameIcon type="vp" size="xs" />
                <span>{player.vpTokens} VP</span>
              </div>

              <span className="text-amber-300 font-black text-sm">=</span>

              {/* HIGHLIGHTED TOTAL SCORE */}
              <div
                className="flex items-center gap-1.5 bg-gradient-to-r from-amber-400 via-amber-300 to-amber-500 text-amber-950 px-2.5 sm:px-3 py-1 rounded-xl shadow-lg ring-2 ring-amber-300 scale-105"
                title={`Összesített várható pontszám: ${player.vpTokens} VP + ${playerBeeBonus} méhbónusz = ${playerProjectedTotal} VP`}
              >
                <span className="text-[10px] uppercase font-bold tracking-wider text-amber-950/80">ÖSSZ:</span>
                <span className="font-serif font-black text-sm sm:text-base tracking-tight">{playerProjectedTotal} VP</span>
              </div>
            </div>
          </div>

          {/* Divider */}
          {opponent && <div className="h-10 w-px bg-white/20 hidden sm:block" />}

          {/* Opponent */}
          {opponent && (
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3">
              <div className="flex flex-col">
                <span className="font-serif font-bold text-xs sm:text-sm text-stone-200">
                  {opponent.name}
                </span>
                <span className="text-[9px] text-stone-400 font-serif">
                  Kéz: {opponent.hand.length} lap
                </span>
              </div>

              {/* Opponent Score Chips */}
              <div className="flex items-center gap-1 sm:gap-1.5 flex-wrap">
                <div
                  className="flex items-center gap-1 bg-stone-900/60 border border-stone-500/30 px-1.5 py-0.5 rounded-lg text-[11px] font-mono text-stone-300"
                  title={`Ellenfél kaptárbónusz: ${opponent.beeTokens} méh × ${oppHives} kaptár = +${oppBeeBonus} VP`}
                >
                  <GameIcon type="beetoken" size="xs" />
                  <span>{opponent.beeTokens}</span>
                  <span>×</span>
                  <GameIcon type="beehive" size="xs" />
                  <span>{oppHives}</span>
                  <span>=</span>
                  <span className="font-bold">+{oppBeeBonus}</span>
                </div>

                <span className="text-white/40 text-xs">+</span>

                <div
                  className="flex items-center gap-1 bg-stone-300 text-stone-900 font-black px-1.5 py-0.5 rounded-lg text-[11px]"
                  title="Ellenfél VP zsetonjai"
                >
                  <GameIcon type="vp" size="xs" />
                  <span>{opponent.vpTokens}</span>
                </div>

                <span className="text-stone-300 font-bold text-xs">=</span>

                {/* Opponent Total */}
                <div
                  className="flex items-center gap-1 bg-gradient-to-b from-stone-200 to-stone-400 text-stone-900 px-2 py-0.5 sm:py-1 rounded-lg font-serif font-black text-xs sm:text-sm shadow"
                  title={`Ellenfél összesített várható pontszáma: ${oppProjectedTotal} VP`}
                >
                  <span className="text-[9px] uppercase font-bold text-stone-800">ÖSSZ:</span>
                  <span>{oppProjectedTotal}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Bee Time Status Chip */}
        <div className="flex items-center gap-2 w-full sm:w-auto justify-between sm:justify-start">
          {lastBeeWinnerName ? (
            <div className="flex items-center gap-1.5 bg-amber-400/20 border border-amber-400/40 px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-full text-[10px] sm:text-xs text-amber-200">
              <GameIcon type="beetoken" size="xs" />
              <span className="font-serif font-bold">Bee Time:</span>
              <span className="text-white">{lastBeeWinnerName} won 1 Bee</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 bg-black/20 border border-white/10 px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-full text-[10px] sm:text-xs text-stone-300">
              <GameIcon type="beetoken" size="xs" />
              <span className="font-serif">Bee Time: lowest round scorer</span>
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
