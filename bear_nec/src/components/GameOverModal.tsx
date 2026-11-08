import React from 'react';
import { PlayerState } from '../game/types';
import { Trophy, RotateCcw, Award, Sparkles } from 'lucide-react';
import GameIcon from './GameIcon';

export interface GameOverModalProps {
  players: Record<string, PlayerState>;
  activePlayerId: string;
  winnerIds?: string[] | null;
  onRematch: () => void;
}

export const GameOverModal: React.FC<GameOverModalProps> = ({
  players,
  activePlayerId,
  winnerIds: _winnerIds,
  onRematch,
}) => {
  const playerList = Object.values(players);

  // Compute stats for all players
  const playerStats = playerList.map((p) => {
    let hives = 0;
    for (const r of p.tableau) {
      for (const c of r) {
        if (c) hives += c.beeHives;
      }
    }
    const beeBonus = hives * p.beeTokens;
    const finalScore = p.vpTokens + beeBonus;

    return {
      player: p,
      hives,
      beeTokens: p.beeTokens,
      beeBonus,
      inGameVp: p.vpTokens,
      finalScore,
    };
  });

  // Sort descending by finalScore
  playerStats.sort((a, b) => b.finalScore - a.finalScore);

  const highestScore = playerStats[0]?.finalScore ?? 0;
  const isTie = playerStats.length > 1 && playerStats[0].finalScore === playerStats[1].finalScore;
  const winners = playerStats.filter((p) => p.finalScore === highestScore);
  const isUserWinner = winners.some((w) => w.player.id === activePlayerId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in select-none">
      <div className="relative wood-panel rounded-3xl p-6 sm:p-8 max-w-xl w-full shadow-2xl border-4 border-[#6b4a2c] text-[#3c2a18]">
        {/* Celebratory Woodland Trophy Banner */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-gradient-to-b from-amber-300 to-amber-500 border-4 border-[#fffdf6] shadow-xl flex items-center justify-center text-amber-950 mb-3 animate-bounce">
            <Trophy className="w-10 h-10 sm:w-12 sm:h-12" />
          </div>

          <span className="font-serif font-black text-xs uppercase tracking-widest text-[#6b4a2c] bg-amber-200/60 px-3 py-1 rounded-full border border-amber-400">
            Game Over — 12 Rounds Completed
          </span>

          <h2 className="font-serif font-black text-2xl sm:text-3xl text-[#4e3218] mt-2">
            {isTie ? (
              <span className="flex items-center gap-2 justify-center">
                <Sparkles className="w-6 h-6 text-amber-500" />
                It's a Woodland Tie!
              </span>
            ) : isUserWinner ? (
              <span className="text-emerald-800 flex items-center gap-2 justify-center">
                <Sparkles className="w-6 h-6 text-amber-500" />
                Victory! You Won!
              </span>
            ) : (
              <span>{winners[0]?.player.name} Won the Game!</span>
            )}
          </h2>

          <p className="text-xs sm:text-sm text-stone-600 font-serif mt-1">
            End-game scoring includes in-game VP tokens + (Tableau Bee Hives × Bee Tokens).
          </p>
        </div>

        {/* Players Breakdown Comparison Table */}
        <div className="space-y-3 mb-6">
          {playerStats.map((item, index) => {
            const isWinner = winners.some((w) => w.player.id === item.player.id);
            const isYou = item.player.id === activePlayerId;

            return (
              <div
                key={item.player.id}
                className={`p-4 rounded-2xl border-2 transition-all ${
                  isWinner
                    ? 'bg-gradient-to-r from-amber-50 via-amber-100 to-amber-50 border-amber-500 shadow-md ring-2 ring-amber-300'
                    : 'bg-white/80 border-[#6b4a2c]/30'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        isWinner
                          ? 'bg-amber-500 text-amber-950'
                          : 'bg-stone-300 text-stone-700'
                      }`}
                    >
                      {index + 1}
                    </span>
                    <span className="font-serif font-black text-base sm:text-lg text-[#4e3218]">
                      {item.player.name} {isYou && '(You)'}
                    </span>
                    {isWinner && (
                      <span className="bg-amber-500 text-amber-950 font-serif font-black text-[10px] uppercase px-2 py-0.5 rounded-full flex items-center gap-1 shadow-sm">
                        <Award className="w-3 h-3" /> Winner
                      </span>
                    )}
                  </div>

                  {/* Grand Total */}
                  <div className="flex items-baseline gap-1">
                    <span className="text-xs text-stone-500 font-serif font-bold uppercase">Total:</span>
                    <span className="font-serif font-black text-2xl sm:text-3xl text-amber-700">
                      {item.finalScore}
                    </span>
                    <span className="text-xs font-bold text-amber-900">VP</span>
                  </div>
                </div>

                {/* Formula Breakdown Details */}
                <div className="grid grid-cols-3 gap-2 text-center text-xs font-serif bg-stone-100/70 p-2 rounded-xl border border-stone-200">
                  <div>
                    <span className="block text-stone-500 text-[10px] flex items-center justify-center gap-1">
                      <GameIcon type="vp" size="xs" /> In-Game VP
                    </span>
                    <span className="font-bold text-stone-800 text-sm">
                      {item.inGameVp}
                    </span>
                  </div>

                  <div>
                    <span className="block text-stone-500 text-[10px] flex items-center justify-center gap-1">
                      <GameIcon type="beehive" size="xs" /> Hives × <GameIcon type="beetoken" size="xs" /> Bees
                    </span>
                    <span className="font-bold text-stone-800 text-sm">
                      {item.hives} × {item.beeTokens}
                    </span>
                  </div>

                  <div>
                    <span className="block text-amber-700 text-[10px] font-bold flex items-center justify-center gap-1">
                      <GameIcon type="beetoken" size="xs" /> Bee Bonus
                    </span>
                    <span className="font-bold text-amber-700 text-sm">
                      +{item.beeBonus} VP
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Action Button: Rematch */}
        <div className="flex justify-center">
          <button
            type="button"
            onClick={onRematch}
            className="w-full sm:w-auto px-8 py-3 rounded-full font-serif font-black text-base uppercase tracking-wider bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white flex items-center justify-center gap-2 shadow-xl hover:shadow-emerald-600/40 transform hover:scale-105 active:scale-95 transition-all ring-2 ring-emerald-400 cursor-pointer"
          >
            <RotateCcw className="w-5 h-5" />
            <span>Play Rematch</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default GameOverModal;
