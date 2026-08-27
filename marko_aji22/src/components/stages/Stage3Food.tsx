import React, { useState } from 'react';
import { useQuest } from '../../context/QuestContext';
import { sound } from '../../utils/sound';
import { triggerHaptic } from '../../utils/haptics';
import { fireConfettiBurst } from '../../utils/confetti';
import { Check, ArrowRight, RotateCcw, Utensils } from 'lucide-react';
import { Button } from '../common/Button';

export const Stage3Food: React.FC = () => {
  const { config, state, selectFoodOption, advanceToNextStage } = useQuest();
  const food = config.stages.food;

  const [selectedId, setSelectedId] = useState<string>(
    state.selectedFoodId || food.options[0]?.id || 'food_kebab'
  );
  const [isConfirmed, setIsConfirmed] = useState<boolean>(!!state.selectedFoodId);

  const selectedOption = food.options.find((opt) => opt.id === selectedId) || food.options[0];

  const handleSelect = (id: string) => {
    setSelectedId(id);
    selectFoodOption(id);
  };

  const handleConfirm = () => {
    selectFoodOption(selectedId);
    setIsConfirmed(true);
    sound.playUnlock();
    triggerHaptic('success');
    fireConfettiBurst();
  };

  const handleFinishFood = () => {
    sound.playUnlock();
    triggerHaptic('success');
    advanceToNextStage();
  };

  return (
    <div className="flex flex-col px-1 py-1 max-w-md mx-auto space-y-3">
      {/* Header */}
      <div className="text-left space-y-1">
        <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-widest">
          2. Állomás • {isConfirmed ? 'Jó Étvágyat!' : 'Vacsora Stratégia'}
        </span>
        <h1 className="text-2xl sm:text-3xl font-black text-white">
          {isConfirmed ? 'Jó utat és jó étvágyat!' : food.title}
        </h1>
        <p className="text-xs text-slate-300 leading-relaxed">
          {isConfirmed
            ? `Kiválasztva: ${selectedOption.title}. Egyetek egy jót a Kálvin téren, aztán indulhat a kocsmatúra!`
            : food.introText}
        </p>
      </div>

      {/* PHASE 1: FOOD SELECTION */}
      {!isConfirmed ? (
        <div className="space-y-4">
          <div className="space-y-2.5">
            {food.options.map((opt) => {
              const isSelected = opt.id === selectedId;
              return (
                <div
                  key={opt.id}
                  onClick={() => handleSelect(opt.id)}
                  className={`cursor-pointer rounded-2xl p-4 transition-all border ${
                    isSelected
                      ? 'bg-[#161F32] border-amber-500 ring-1 ring-amber-500'
                      : 'bg-[#121826] border-[#1E293B] hover:border-[#28354D]'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="text-2xl p-2 rounded-xl bg-[#0A0E17] border border-[#1E293B] flex-shrink-0">
                      {opt.image}
                    </div>

                    <div className="flex-1 pr-3">
                      <h3 className="text-base font-bold text-white leading-snug">{opt.title}</h3>
                      <p className="text-xs text-slate-300 mt-1 leading-relaxed">{opt.description}</p>
                    </div>

                    <div
                      className={`w-5 h-5 rounded-full flex items-center justify-center border transition-all mt-1 ${
                        isSelected
                          ? 'bg-amber-500 text-slate-950 border-amber-400'
                          : 'border-slate-700 bg-slate-900'
                      }`}
                    >
                      {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="pt-2 sticky bottom-4">
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={handleConfirm}
              icon={<Utensils className="w-5 h-5" />}
            >
              VÁLASZTÁS MEGERŐSÍTÉSE
            </Button>
          </div>
        </div>
      ) : (
        /* PHASE 2: CONFIRMED MEAL & "JÓ ÉTVÁGYAT" SCREEN */
        <div className="space-y-5">
          <div className="bg-[#121826] rounded-3xl p-6 border border-[#1E293B] text-center space-y-4 animate-in zoom-in-95">
            <div className="w-20 h-20 rounded-2xl bg-[#0A0E17] border border-amber-500/40 flex items-center justify-center mx-auto text-4xl shadow-inner">
              {selectedOption.image}
            </div>

            <div>
              <div className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider mb-1">
                Kiválasztott Vacsora
              </div>
              <h2 className="text-2xl font-black text-white">{selectedOption.title}</h2>
              <p className="text-xs text-slate-300 mt-2 max-w-xs mx-auto leading-relaxed">
                {selectedOption.description}
              </p>
            </div>

            <div className="pt-3 border-t border-[#1E293B]">
              <button
                onClick={() => setIsConfirmed(false)}
                className="text-xs font-bold text-slate-400 hover:text-white flex items-center justify-center gap-1.5 mx-auto py-1 px-3 rounded-lg bg-[#161F32] border border-[#28354D] transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Másik étterem választása</span>
              </button>
            </div>
          </div>

          {/* Action Advance */}
          <div className="pt-2 sticky bottom-4">
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={handleFinishFood}
              icon={<ArrowRight className="w-5 h-5" />}
            >
              A HASAK MÁR MEGTELTEK
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
