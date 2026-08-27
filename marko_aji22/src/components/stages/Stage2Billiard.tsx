import React, { useState, useEffect } from 'react';
import { useQuest } from '../../context/QuestContext';
import { sound } from '../../utils/sound';
import { triggerHaptic } from '../../utils/haptics';
import { fireConfettiBurst } from '../../utils/confetti';
import { ArrowRight, ScanFace, X, ShieldCheck, Lock, Sparkles } from 'lucide-react';
import { Button } from '../common/Button';

export const Stage2Billiard: React.FC = () => {
  const { config, state, setBilliardScanCompleted, advanceToNextStage } = useQuest();
  const billiard = config.stages.billiard;
  const isUnlockedByScan = state.isBilliardUnlockedByScan;

  // Face scanner modal state
  const [isScanOpen, setIsScanOpen] = useState(false);
  const [scanStep, setScanStep] = useState<'idle' | 'scanning' | 'revealed'>('idle');
  const [scanProgress, setScanProgress] = useState(0);
  const [scanStatusText, setScanStatusText] = useState('Arc keresése...');
  const [imgError, setImgError] = useState(false);

  // Proactively preload the image on mount
  useEffect(() => {
    const img = new Image();
    img.src = billiard.faceScan.imagePath;
  }, [billiard.faceScan.imagePath]);

  const preloadImage = (src: string): Promise<boolean> => {
    return new Promise((resolve) => {
      const img = new Image();
      img.src = src;
      if (img.complete && img.naturalWidth > 0) {
        resolve(true);
      } else {
        img.onload = () => resolve(true);
        img.onerror = () => resolve(false);
      }
    });
  };

  const startFaceScan = () => {
    setIsScanOpen(true);
    setScanStep('scanning');
    setScanProgress(0);
    setScanStatusText('Arc keresése...');
    sound.playClick();
    triggerHaptic('medium');

    // Preload image in parallel
    const imagePreloadPromise = preloadImage(billiard.faceScan.imagePath);

    // 4 másodperces várakozás
    setTimeout(() => {
      const scanMessages = [
        { progress: 20, text: 'Arcvonások és életkor elemzése...' },
        { progress: 55, text: 'Keresés a nemzetközi körözési adatbázisban...' },
        { progress: 85, text: 'Biometrikus egyezés megerősítése...' },
        { progress: 100, text: 'CSIBÉSZ AZONOSÍTVA!' }
      ];

      let currentMsgIdx = 0;
      const interval = setInterval(async () => {
        if (currentMsgIdx < scanMessages.length) {
          const item = scanMessages[currentMsgIdx];
          setScanProgress(item.progress);
          setScanStatusText(item.text);
          currentMsgIdx++;
        } else {
          clearInterval(interval);

          // Megvárjuk, hogy a kép FIXEN és 100%-osan betöltsön
          await imagePreloadPromise;

          setScanStep('revealed');
          // Csak akkor indítjuk el a hangot, amikor a kép már biztosan betöltött!
          sound.playCustomAudio(billiard.faceScan.soundPath, () => {
            sound.playVictoryFanfare();
          });
          triggerHaptic('warning');
          fireConfettiBurst();
        }
      }, 700);
    }, 4000);
  };

  const handleFinishScan = () => {
    setIsScanOpen(false);
    setBilliardScanCompleted(true);
    sound.playUnlock();
    triggerHaptic('success');
    fireConfettiBurst();
  };

  return (
    <div className="flex flex-col px-1 py-1 max-w-md mx-auto space-y-3">
      {/* Header */}
      <div className="text-left space-y-1">
        <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-widest">
          {isUnlockedByScan ? '1. Állomás • Feloldva' : '1. Állomás • Zárolt Program'}
        </span>
        <h1 className="text-2xl sm:text-3xl font-black text-white">
          {isUnlockedByScan ? billiard.title : '1. Állomás: Személyazonosítás'}
        </h1>
        <p className="text-xs text-slate-300 leading-relaxed">
          {isUnlockedByScan
            ? billiard.description
            : 'A mai este első programjának feloldásához kötelező a biometrikus arcfelismerés.'}
        </p>
      </div>

      {/* PHASE 1: BEFORE FACE SCAN (LOCKED) */}
      {!isUnlockedByScan ? (
        <div className="bg-[#121826] rounded-2xl p-5 border border-[#1E293B] space-y-5 text-center">
          <div className="w-16 h-16 rounded-2xl bg-[#0A0E17] border border-[#28354D] flex items-center justify-center mx-auto text-amber-400">
            <Lock className="w-8 h-8" />
          </div>

          <div>
            <h2 className="text-base font-bold text-white mb-1">
              Az 1. program zárolva van
            </h2>
            <p className="text-xs text-slate-400 max-w-xs mx-auto leading-relaxed">
              Kérlek végezd el a személyazonosítást, hogy ellenőrizzük a szülinapos jogosultságát és feloldjuk a programot!
            </p>
          </div>

          <Button
            variant="primary"
            size="lg"
            fullWidth
            onClick={startFaceScan}
            icon={<ScanFace className="w-5 h-5" />}
          >
            ARCFELISMERÉS INDÍTÁSA
          </Button>
        </div>
      ) : (
        /* PHASE 2: AFTER FACE SCAN (BILIARD REVEALED) */
        <div className="bg-[#121826] rounded-2xl p-5 border border-[#1E293B] space-y-5 animate-in fade-in">
          {/* Replay Face Scan Tag */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-[#0A0E17] border border-emerald-500/40 text-xs">
            <div className="flex items-center gap-2 text-emerald-400 font-bold">
              <ShieldCheck className="w-4 h-4" />
              <span>Személyazonosítás sikeres</span>
            </div>
            <button
              onClick={startFaceScan}
              className="text-[11px] font-bold text-amber-400 bg-[#161F32] hover:bg-[#1E293B] px-2 py-1 rounded border border-[#28354D] flex items-center gap-1"
            >
              <ScanFace className="w-3.5 h-3.5" />
              <span>Fotó & Hang újra</span>
            </button>
          </div>

          {/* Venue Information (Cím nélkül) */}
          <div className="space-y-1.5 bg-[#0A0E17] p-3.5 rounded-xl border border-[#1E293B]">
            <div className="flex items-center justify-between text-xs font-mono font-bold text-slate-400">
              <span>PROGRAM & HELYSZÍN</span>
              <span className="text-amber-400 font-bold">{billiard.meetingTime}</span>
            </div>
            <h2 className="text-xl font-black text-white">{billiard.venueName}</h2>
          </div>
        </div>
      )}

      {/* Action Advance */}
      <div className="pt-2 sticky bottom-4">
        <Button
          variant="primary"
          size="lg"
          fullWidth
          disabled={!isUnlockedByScan}
          onClick={advanceToNextStage}
          icon={<ArrowRight className="w-5 h-5" />}
        >
          KÖVETKEZŐ ÁLLOMÁS (VACSORA)
        </Button>
      </div>

      {/* ========================================================================= */}
      {/* 🎭 FUNNY FACE SCAN MODAL SCREEN */}
      {/* ========================================================================= */}
      {isScanOpen && (
        <div className="fixed inset-0 z-50 bg-[#0A0E17]/95 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-sm bg-[#121826] border border-[#28354D] rounded-3xl p-5 shadow-2xl space-y-4 animate-in zoom-in-95">
            {/* Header */}
            <div className="flex items-center justify-between pb-2 border-b border-[#1E293B]">
              <div className="flex items-center gap-2">
                <ScanFace className="w-5 h-5 text-amber-400" />
                <span className="font-mono text-xs font-bold text-amber-400 uppercase tracking-wider">
                  {billiard.faceScan.title}
                </span>
              </div>
              <button
                onClick={() => setIsScanOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white bg-[#161F32]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* SCANNING IN PROGRESS VIEW */}
            {scanStep === 'scanning' && (
              <div className="py-6 flex flex-col items-center justify-center text-center space-y-4">
                {/* Viewfinder Target */}
                <div className="relative w-48 h-48 rounded-2xl bg-[#0A0E17] border-2 border-dashed border-amber-500/60 flex items-center justify-center overflow-hidden">
                  <div className="absolute inset-x-0 h-1 bg-amber-400 shadow-[0_0_10px_#F59E0B] animate-bounce" />
                  <div className="w-32 h-32 rounded-full border border-amber-500/30 flex items-center justify-center">
                    <ScanFace className="w-16 h-16 text-amber-400/40 animate-pulse" />
                  </div>
                  {/* Viewfinder corners */}
                  <div className="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-amber-400" />
                  <div className="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-amber-400" />
                  <div className="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 border-amber-400" />
                  <div className="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-amber-400" />
                </div>

                <div className="w-full space-y-2">
                  <div className="flex justify-between text-xs font-mono font-bold text-slate-400">
                    <span>{scanStatusText}</span>
                    <span className="text-amber-400">{scanProgress}%</span>
                  </div>
                  <div className="h-2 w-full bg-[#0A0E17] rounded-full overflow-hidden border border-[#1E293B]">
                    <div
                      className="h-full bg-amber-500 transition-all duration-300 rounded-full"
                      style={{ width: `${scanProgress}%` }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* REVEALED FUNNY PHOTO & SOUND PLAYED */}
            {scanStep === 'revealed' && (
              <div className="py-2 flex flex-col items-center justify-center text-center space-y-4 animate-in zoom-in-90">
                {/* Identified Badge */}
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500 text-xs font-mono font-black uppercase">
                  <ShieldCheck className="w-4 h-4" />
                  <span>{billiard.faceScan.identifiedName}</span>
                </div>

                {/* Funny Photo Display */}
                <div className="relative w-52 h-52 rounded-2xl bg-[#0A0E17] border-2 border-amber-500 overflow-hidden shadow-2xl flex items-center justify-center">
                  {!imgError ? (
                    <img
                      src={billiard.faceScan.imagePath}
                      alt="Szülinapos vicces kép"
                      className="w-full h-full object-cover"
                      onError={() => setImgError(true)}
                    />
                  ) : (
                    <div className="p-4 flex flex-col items-center justify-center text-center space-y-2">
                      <span className="text-6xl">🤪</span>
                      <span className="text-xs font-bold text-amber-400">
                        Helyezz el egy fotót ide:
                      </span>
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-900 p-1 rounded">
                        public/images/marko_funny.jpg
                      </span>
                    </div>
                  )}
                </div>

                {/* Funny Caption */}
                <div className="p-3 bg-[#0A0E17] rounded-xl border border-[#1E293B] text-xs text-amber-300 text-center font-medium leading-relaxed">
                  {billiard.faceScan.caption}
                </div>

                {/* Replay Sound & Finish Action */}
                <div className="w-full space-y-2 pt-2">
                  <button
                    onClick={() => {
                      sound.playCustomAudio(billiard.faceScan.soundPath, () => {
                        sound.playVictoryFanfare();
                      });
                      triggerHaptic('warning');
                    }}
                    className="w-full py-2.5 rounded-xl bg-[#161F32] hover:bg-[#1E293B] text-xs font-bold text-slate-200 border border-[#28354D] flex items-center justify-center gap-2"
                  >
                    <span>🔊 Hang újraindítása</span>
                  </button>

                  <Button
                    variant="primary"
                    size="md"
                    fullWidth
                    onClick={handleFinishScan}
                    icon={<Sparkles className="w-4 h-4" />}
                  >
                    AZONOSÍTVA! ➔ 1. PROGRAM FELOLDÁSA
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
