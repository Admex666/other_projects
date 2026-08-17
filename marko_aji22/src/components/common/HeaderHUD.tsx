import React from 'react';
import { useQuest } from '../../context/QuestContext';
import { StageId } from '../../types/quest';
import { Volume2, VolumeX, Wrench, Check, Lock, HelpCircle } from 'lucide-react';

const STAGES: { id: StageId; label: string; icon: string }[] = [
  { id: 'teaser', label: 'Zárolva', icon: '🔒' },
  { id: 'intro', label: 'Indulás', icon: '📋' },
  { id: 'bowling', label: '1. Állomás', icon: '❓' },
  { id: 'food', label: '2. Állomás', icon: '❓' },
  { id: 'bar', label: '3. Állomás', icon: '❓' },
  { id: 'finale', label: 'Zárás', icon: '⭐' },
];

export const HeaderHUD: React.FC = () => {
  const { config, state, toggleSound, toggleDevMode } = useQuest();

  const currentStageIndex = STAGES.findIndex((s) => s.id === state.currentStageId);

  return (
    <header className="sticky top-0 z-40 w-full bg-[#0E1422] border-b border-[#1E293B] px-4 pt-3.5 pb-3 safe-top">
      <div className="max-w-md mx-auto flex items-center justify-between">
        {/* Left: Identity */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-amber-500 text-slate-950 font-black text-xs flex items-center justify-center">
            22
          </div>
          <div>
            <div className="flex items-center gap-1.5 leading-none">
              <span className="font-extrabold text-sm text-slate-100">
                {config.meta.birthdayPerson}
              </span>
              <span className="text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                22. Szülinap
              </span>
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              {state.isUnlocked ? 'Küldetés folyamatban' : 'Zárolt állapot'}
            </div>
          </div>
        </div>

        {/* Right: Quick actions */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={toggleSound}
            aria-label="Hang némítása vagy bekapcsolása"
            className="p-2 rounded-lg bg-[#161F32] border border-[#28354D] text-slate-300 hover:text-white active:scale-95 transition-transform"
          >
            {state.soundEnabled ? <Volume2 className="w-4 h-4 text-amber-400" /> : <VolumeX className="w-4 h-4 text-slate-500" />}
          </button>

          <button
            onClick={toggleDevMode}
            aria-label="Fejlesztői tesztpanel megnyitása"
            className={`p-2 rounded-lg border transition-transform active:scale-95 ${
              state.devModeEnabled
                ? 'bg-amber-500/20 border-amber-500 text-amber-400'
                : 'bg-[#161F32] border-[#28354D] text-slate-400 hover:text-slate-200'
            }`}
          >
            <Wrench className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Quest Progress Step Line */}
      {state.isUnlocked && (
        <div className="max-w-md mx-auto mt-2.5 pt-2 border-t border-[#1E293B]/70">
          <div className="flex items-center justify-between px-1 relative">
            <div className="absolute top-1/2 left-3 right-3 h-[2px] -translate-y-1/2 bg-[#1E293B] -z-0" />
            <div
              className="absolute top-1/2 left-3 h-[2px] -translate-y-1/2 bg-amber-500 -z-0 transition-all duration-300"
              style={{
                width: `${Math.max(0, (currentStageIndex / (STAGES.length - 1)) * 100 - 4)}%`,
              }}
            />

            {STAGES.map((s, idx) => {
              const isPast = idx < currentStageIndex;
              const isCurrent = idx === currentStageIndex;
              return (
                <div key={s.id} className="relative z-10 flex flex-col items-center">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${
                      isCurrent
                        ? 'bg-amber-500 text-slate-950 font-black ring-2 ring-amber-400/50 scale-105'
                        : isPast
                        ? 'bg-[#161F32] border border-amber-500 text-amber-400'
                        : 'bg-[#0A0E17] border border-[#28354D] text-slate-500'
                    }`}
                  >
                    {isPast ? <Check className="w-3.5 h-3.5 stroke-[3]" /> : isCurrent ? idx : idx === 0 ? <Lock className="w-3 h-3" /> : <HelpCircle className="w-3 h-3 text-slate-600" />}
                  </div>
                  <span
                    className={`text-[9px] mt-1 font-medium ${
                      isCurrent ? 'text-amber-400 font-bold' : isPast ? 'text-slate-400' : 'text-slate-600'
                    }`}
                  >
                    {s.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
};
