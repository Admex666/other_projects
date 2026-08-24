import React, { useEffect } from 'react';
import { useQuest } from '../../context/QuestContext';
import { fireGrandFinaleConfetti } from '../../utils/confetti';
import { Check, RotateCcw, Share2 } from 'lucide-react';
import { Button } from '../common/Button';

export const Stage5Finale: React.FC = () => {
  const { config, state, resetQuest } = useQuest();
  const finale = config.stages.finale;

  useEffect(() => {
    fireGrandFinaleConfetti();
  }, []);

  const selectedFood = config.stages.food.options.find((o) => o.id === state.selectedFoodId);
  const selectedBar = config.stages.bar.options.find((o) => o.id === state.selectedBarId);

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Markó level 22 quest teljesítve!`,
          text: `Sikeresen végigcsináltad az estét: Bowling, Vacsora és Kocsma pipa! 🎳🍔🍻🎉`,
          url: window.location.href,
        });
      } catch {
        // Ignored
      }
    }
  };

  return (
    <div className="flex flex-col min-h-[78vh] justify-between px-2 py-4 max-w-md mx-auto space-y-6">
      {/* Header Banner */}
      <div className="text-left space-y-2">
        <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-widest">
          Küldetés Teljesítve
        </span>
        <h1 className="text-2xl sm:text-3xl font-black text-white leading-tight">
          {finale.celebrationTitle}
        </h1>
      </div>

      {/* Birthday Letter Panel */}
      <div className="bg-[#121826] rounded-2xl p-5 border border-[#1E293B] space-y-5">
        {/* Message */}
        <div className="space-y-2 text-sm text-slate-200 leading-relaxed">
          {finale.message.map((m, idx) => (
            <p key={idx}>{m}</p>
          ))}
        </div>

        {/* Evening Recap Table */}
        <div className="pt-4 border-t border-[#1E293B] space-y-2">
          <h2 className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider mb-2">
            Esti összefoglaló
          </h2>

          <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#161F32] text-xs">
            <span className="text-slate-400">1. Bowling:</span>
            <span className="font-bold text-white flex items-center gap-1">
              <Check className="w-3.5 h-3.5 text-amber-400" /> {state.bowlingStrikesCount} Strike / Spare
            </span>
          </div>

          <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#161F32] text-xs">
            <span className="text-slate-400">2. Vacsora stratégia:</span>
            <span className="font-bold text-white flex items-center gap-1">
              <Check className="w-3.5 h-3.5 text-amber-400" /> {selectedFood?.title || 'Kiválasztva'}
            </span>
          </div>

          <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#161F32] text-xs">
            <span className="text-slate-400">3. Titkos kocsma:</span>
            <span className="font-bold text-white flex items-center gap-1">
              <Check className="w-3.5 h-3.5 text-amber-400" /> {selectedBar ? selectedBar.venueName : 'Megtalálva'}
            </span>
          </div>
        </div>

        {/* Medals List */}
        <div className="pt-4 border-t border-[#1E293B] space-y-2">
          <h2 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
            Megszerzett kitüntetések:
          </h2>

          <div className="space-y-1.5">
            {finale.badges.map((badge, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 p-2.5 rounded-lg bg-[#0A0E17] border border-[#1E293B]"
              >
                <span className="text-xl">{badge.icon}</span>
                <div>
                  <h3 className="text-xs font-bold text-white">{badge.title}</h3>
                  <p className="text-[10px] text-slate-400">{badge.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="pt-2 sticky bottom-4 space-y-2">
        {typeof navigator !== 'undefined' && 'share' in navigator && (
          <Button
            variant="primary"
            size="lg"
            fullWidth
            onClick={handleShare}
            icon={<Share2 className="w-5 h-5" />}
          >
            EREDMÉNY MEGOSZTÁSA
          </Button>
        )}

        <Button
          variant="secondary"
          size="sm"
          fullWidth
          onClick={() => fireGrandFinaleConfetti()}
        >
          Konfetti újraindítása 🎉
        </Button>

        <button
          onClick={resetQuest}
          className="text-xs text-slate-500 hover:text-slate-300 flex items-center justify-center gap-1 w-full py-1.5"
        >
          <RotateCcw className="w-3 h-3" /> Quest újraindítása
        </button>
      </div>
    </div>
  );
};
