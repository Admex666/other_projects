import React, { useState } from 'react';
import { useQuest } from '../../context/QuestContext';
import { Lock, Unlock, KeyRound, AlertCircle, Delete } from 'lucide-react';
import { Button } from '../common/Button';

export const Stage0Teaser: React.FC = () => {
  const { config, unlockWithCode } = useQuest();
  const [code, setCode] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isShaking, setIsShaking] = useState(false);
  const [isKeypadOpen, setIsKeypadOpen] = useState(false);

  const handleKeyPress = (char: string) => {
    if (code.length < 10) {
      setCode((prev) => prev + char);
      setErrorMsg(null);
    }
  };

  const handleDelete = () => {
    setCode((prev) => prev.slice(0, -1));
    setErrorMsg(null);
  };

  const handleClear = () => {
    setCode('');
    setErrorMsg(null);
  };

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!code) {
      setErrorMsg('Kérlek add meg a kódot!');
      return;
    }

    const success = unlockWithCode(code);
    if (!success) {
      setErrorMsg('Hibás feloldó kód!');
      setIsShaking(true);
      setTimeout(() => setIsShaking(false), 500);
    }
  };

  return (
    <div className="flex flex-col items-center justify-between min-h-[75vh] px-2 py-4 max-w-md mx-auto space-y-6">
      {/* Top Banner */}
      <div className="w-full text-left">
        <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-widest">
          Születésnapi Küldetés
        </span>
        <h1 className="text-2xl font-black text-white mt-1">
          {config.meta.birthdayPerson} 22. Szülinapja
        </h1>
      </div>

      {/* Center Lock Status Box */}
      <div className="w-full my-auto py-2 flex flex-col items-center">
        {/* Solid Lock Container */}
        <div className="w-20 h-20 rounded-2xl bg-[#121826] border border-[#28354D] flex items-center justify-center mb-5 shadow-lg">
          <Lock className="w-9 h-9 text-amber-400" />
        </div>

        <h2 className="text-lg font-bold text-white mb-2 text-center">
          A mai program zárolva van
        </h2>
        <p className="text-xs text-slate-300 text-center max-w-xs mb-6 leading-relaxed">
          {config.stages.teaser.lockedMessage}
        </p>

        {/* Hint Box */}
        <div className="w-full bg-[#121826] rounded-xl p-3.5 border border-[#1E293B] text-left mb-5">
          <div className="flex items-start gap-2.5">
            <KeyRound className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-slate-300">
              {config.stages.teaser.hint}
            </p>
          </div>
        </div>

        {/* Action / Keypad */}
        {!isKeypadOpen ? (
          <Button
            variant="primary"
            size="lg"
            fullWidth
            onClick={() => setIsKeypadOpen(true)}
            icon={<Unlock className="w-5 h-5" />}
          >
            FELOLDÓ KÓD MEGADÁSA
          </Button>
        ) : (
          <div className={`w-full bg-[#121826] rounded-2xl p-4 border border-[#28354D] ${isShaking ? 'animate-shake' : ''}`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
                Feloldó Kód
              </span>
              <button
                onClick={() => setIsKeypadOpen(false)}
                className="text-xs text-slate-400 hover:text-slate-200"
              >
                Mégse
              </button>
            </div>

            {/* Display Field */}
            <div className="h-12 bg-[#0A0E17] rounded-xl border border-[#28354D] flex items-center justify-center px-4 mb-3">
              <span className="font-mono text-xl font-bold tracking-widest text-amber-400">
                {code ? code : <span className="text-slate-600 font-normal text-sm">Írd be a kódot...</span>}
              </span>
            </div>

            {errorMsg && (
              <div className="flex items-center justify-center gap-1.5 text-xs text-rose-400 mb-3 bg-rose-950/40 py-1 px-2 rounded border border-rose-800/40">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Keypad */}
            <div className="grid grid-cols-3 gap-1.5 mb-3">
              {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => handleKeyPress(num)}
                  className="h-11 rounded-lg bg-[#161F32] hover:bg-[#1E293B] active:bg-amber-500 active:text-slate-950 border border-[#28354D] text-base font-bold text-slate-100 transition-colors"
                >
                  {num}
                </button>
              ))}
              <button
                type="button"
                onClick={handleClear}
                className="h-11 rounded-lg bg-[#161F32] hover:bg-[#1E293B] active:scale-95 border border-[#28354D] text-xs font-bold text-slate-400"
              >
                TÖRLÉS
              </button>
              <button
                type="button"
                onClick={() => handleKeyPress('0')}
                className="h-11 rounded-lg bg-[#161F32] hover:bg-[#1E293B] active:bg-amber-500 active:text-slate-950 border border-[#28354D] text-base font-bold text-slate-100 transition-colors"
              >
                0
              </button>
              <button
                type="button"
                onClick={handleDelete}
                aria-label="Törlés"
                className="h-11 rounded-lg bg-[#161F32] hover:bg-[#1E293B] active:scale-95 border border-[#28354D] flex items-center justify-center text-slate-300"
              >
                <Delete className="w-4 h-4" />
              </button>
            </div>

            <Button variant="primary" size="md" fullWidth onClick={() => handleSubmit()}>
              QUEST INDÍTÁSA
            </Button>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="w-full text-left text-xs text-slate-500">
        {config.meta.eventDate}
      </div>
    </div>
  );
};
