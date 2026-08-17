import React from 'react';
import { useQuest } from '../../context/QuestContext';
import { Play } from 'lucide-react';
import { Button } from '../common/Button';

export const Stage1Intro: React.FC = () => {
  const { config, advanceToNextStage } = useQuest();
  const { intro } = config.stages;

  return (
    <div className="flex flex-col min-h-[78vh] justify-between px-2 py-4 max-w-md mx-auto space-y-6">
      {/* Title */}
      <div className="text-left space-y-2">
        <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-widest">
          Esti Forgatókönyv
        </span>
        <h1 className="text-2xl sm:text-3xl font-black text-white leading-tight">
          {intro.title}
        </h1>
      </div>

      {/* Unified Playbook Panel */}
      <div className="bg-[#121826] rounded-2xl p-5 border border-[#1E293B] space-y-5">
        {/* Briefing paragraphs */}
        <div className="space-y-2.5 text-sm text-slate-300 leading-relaxed">
          {intro.briefing.map((para, idx) => (
            <p key={idx}>{para}</p>
          ))}
        </div>

        {/* Rules */}
        <div className="pt-4 border-t border-[#1E293B]">
          <h2 className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider mb-2.5">
            A mai este alapszabályai
          </h2>
          <ul className="space-y-2 text-xs text-slate-300">
            {intro.rules.map((rule, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                <span>{rule}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Mystery Program Note */}
        <div className="pt-4 border-t border-[#1E293B] bg-[#0A0E17] p-3 rounded-xl border border-[#1E293B]">
          <div className="text-xs font-mono font-bold text-amber-400 uppercase mb-1">
            🔒 Titkosított Állomások
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Minden állomás egy meglepetés, amely csak az adott feladatok és azonosítások után tárul fel előtted!
          </p>
        </div>
      </div>

      {/* Start Action */}
      <div className="pt-2 sticky bottom-4">
        <Button
          variant="primary"
          size="lg"
          fullWidth
          onClick={advanceToNextStage}
          icon={<Play className="w-5 h-5 fill-slate-950" />}
        >
          INDULÁS AZ 1. ÁLLOMÁSRA
        </Button>
      </div>
    </div>
  );
};
