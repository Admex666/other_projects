import React, { useEffect, useState } from 'react';
import { useQuest } from '../../context/QuestContext';
import { useGeolocation } from '../../hooks/useGeolocation';
import { calculateDistanceMeters, getProximityState, getProximityInfo } from '../../utils/geo';
import { sound } from '../../utils/sound';
import { triggerHaptic } from '../../utils/haptics';
import { fireConfettiBurst } from '../../utils/confetti';
import { Check, Flame, Snowflake, Sparkles, HelpCircle, RotateCcw, ArrowRight, Beer, Navigation } from 'lucide-react';
import { Button } from '../common/Button';

interface Stage4BarRadarProps {
  barStageId: 'bar1' | 'bar2' | 'bar3';
}

export const Stage4BarRadar: React.FC<Stage4BarRadarProps> = ({ barStageId }) => {
  const { config, state, selectBarOption, advanceToNextStage, setSimulatedDistance } = useQuest();
  const barConfig = config.stages.bars.stages.find((b) => b.id === barStageId) || config.stages.bars.stages[0];
  const thresholds = config.stages.bars.thresholdsMeters;
  const geo = useGeolocation();

  const isLastBar = barStageId === 'bar3';

  // Step state: always starts at 'select' (Mystery választás)
  const savedOptionId = state.selectedBarIds[barStageId] || barConfig.options[0]?.id || '';
  const [selectedOptionId, setSelectedOptionId] = useState<string>(savedOptionId);
  const [phase, setPhase] = useState<'select' | 'hunting' | 'revealed'>('select');
  const [hasPlayedArrival, setHasPlayedArrival] = useState<boolean>(false);

  const selectedOption = barConfig.options.find((opt) => opt.id === selectedOptionId) || barConfig.options[0];

  // Live or simulated distance to the chosen mystery bar
  const [distanceMeters, setDistanceMeters] = useState<number>(() => {
    if (state.simulatedDistance !== null) return state.simulatedDistance;
    if (geo.coords && selectedOption) {
      return calculateDistanceMeters(geo.coords, selectedOption.targetLocation);
    }
    return 350;
  });

  useEffect(() => {
    if (state.simulatedDistance !== null) {
      setDistanceMeters(state.simulatedDistance);
    } else if (geo.coords && selectedOption) {
      const calculated = calculateDistanceMeters(geo.coords, selectedOption.targetLocation);
      setDistanceMeters(calculated);
    }
  }, [geo.coords, state.simulatedDistance, selectedOption]);

  const proximityState = getProximityState(distanceMeters, thresholds);
  const proximityInfo = getProximityInfo(proximityState);
  const isWithin30Meters = proximityState === 'burning' || distanceMeters <= thresholds.burning;

  // Auto-reveal when within 30 meters
  useEffect(() => {
    if (phase === 'hunting' && isWithin30Meters && !hasPlayedArrival) {
      setHasPlayedArrival(true);
      setPhase('revealed');
      sound.playArrivalVictory();
      triggerHaptic('success');
      fireConfettiBurst();
    }
  }, [phase, isWithin30Meters, hasPlayedArrival]);

  // Audio ping while hunting
  useEffect(() => {
    if (phase !== 'hunting') return;
    const interval = setInterval(() => {
      sound.playRadarPing(proximityState);
    }, proximityState === 'hot' ? 1500 : 3000);

    return () => clearInterval(interval);
  }, [phase, proximityState]);

  const handleSelectOption = (id: string) => {
    setSelectedOptionId(id);
    selectBarOption(barStageId, id);
  };

  const handleStartHunting = () => {
    selectBarOption(barStageId, selectedOptionId);
    setPhase('hunting');
    geo.requestLocation();
    sound.playUnlock();
    triggerHaptic('success');
  };

  const handleManualCheckIn = () => {
    setPhase('revealed');
    setHasPlayedArrival(true);
    sound.playArrivalVictory();
    triggerHaptic('success');
    fireConfettiBurst();
  };

  const handleNextDrink = () => {
    sound.playUnlock();
    triggerHaptic('success');
    advanceToNextStage();
  };

  const heatPercentage = Math.max(
    5,
    Math.min(100, Math.round(((500 - Math.min(distanceMeters, 500)) / (500 - 30)) * 100))
  );

  return (
    <div className="flex flex-col px-1 py-1 max-w-md mx-auto space-y-3">
      {/* Header */}
      <div className="text-left space-y-1">
        <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-widest">
          {barConfig.title} • {phase === 'select' ? 'Mystery Választás' : phase === 'hunting' ? 'Hideg - Meleg Keresés' : 'Helyszín Felfedve'}
        </span>
        <h1 className="text-2xl sm:text-3xl font-black text-white">
          {barConfig.title}
        </h1>
        <p className="text-xs text-slate-300 leading-relaxed">
          {phase === 'select'
            ? barConfig.riddle
            : phase === 'hunting'
              ? `Célpont jeligéje: "${selectedOption.mysteryPhrase}". Kövessétek a hőmérsékletet!`
              : `Megérkeztetek a helyszínre: ${selectedOption.venueName}! Egészségetekre!`}
        </p>
      </div>

      {/* ========================================================================= */}
      {/* 1. STEP: MYSTERY VÁLASZTÁS */}
      {/* ========================================================================= */}
      {phase === 'select' && (
        <div className="space-y-3 pt-1">
          <div className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5" /> Válassz egy rejtélyes jeligét:
          </div>

          <div className="space-y-2.5">
            {barConfig.options.map((opt, idx) => {
              const isSelected = opt.id === selectedOptionId;
              return (
                <div
                  key={opt.id}
                  onClick={() => handleSelectOption(opt.id)}
                  className={`cursor-pointer rounded-2xl p-4 transition-all border ${isSelected
                      ? 'bg-[#161F32] border-amber-500 ring-1 ring-amber-500'
                      : 'bg-[#121826] border-[#1E293B] hover:border-[#28354D]'
                    }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-7 h-7 rounded-lg bg-[#0A0E17] border border-[#1E293B] font-mono text-xs font-bold text-amber-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </div>

                    <div className="flex-1 pr-2">
                      <div className="text-base font-bold text-white leading-snug">
                        „{opt.mysteryPhrase}”
                      </div>
                      <span className="text-[10px] font-mono text-slate-400 mt-1 block">
                        🔒 Rejtett kocsma & koordináták
                      </span>
                    </div>

                    <div
                      className={`w-5 h-5 rounded-full flex items-center justify-center border transition-all mt-1 ${isSelected
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
              onClick={handleStartHunting}
              icon={<ArrowRight className="w-5 h-5" />}
            >
              KOCSMA KIVÁLASZTÁSA & KERESÉS INDÍTÁSA
            </Button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. STEP: HIDEG-MELEG / RADAR KERESÉS */}
      {/* ========================================================================= */}
      {phase === 'hunting' && (
        <div className="space-y-4">
          {/* Active Mystery Bar Tag */}
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#121826] border border-[#1E293B] text-xs">
            <div>
              <div className="text-[10px] font-mono text-amber-400 font-bold uppercase">Keresett Célpont:</div>
              <div className="font-bold text-white text-sm">„{selectedOption.mysteryPhrase}”</div>
            </div>
            <button
              onClick={() => setPhase('select')}
              className="text-[11px] font-bold text-slate-300 hover:text-white flex items-center gap-1 bg-[#161F32] px-2.5 py-1 rounded-lg border border-[#28354D]"
            >
              <RotateCcw className="w-3 h-3" /> Módosítás
            </button>
          </div>

          {/* GPS Live Status / Permission Prompt */}
          {!geo.coords && state.simulatedDistance === null && (
            <div className="bg-[#161F32] rounded-2xl p-4 border border-amber-500/60 flex flex-col items-center gap-2.5 text-center shadow-lg">
              <div className="flex items-center justify-center gap-2 text-xs font-bold text-amber-300">
                <Navigation className="w-4 h-4 text-amber-400 animate-spin" />
                <span>{geo.error || 'Valós GPS helyadatok lekérése...'}</span>
              </div>

              <div className="w-full flex flex-col gap-2 pt-1">
                <button
                  onClick={geo.requestLocation}
                  className="w-full text-xs font-bold text-slate-950 bg-amber-400 hover:bg-amber-300 py-2 px-3 rounded-xl flex items-center justify-center gap-1.5 shadow transition-transform active:scale-95"
                >
                  <Navigation className="w-4 h-4" />
                  <span>GPS ÚJRAPRÓBÁLÁSA / ENGEDÉLYEZÉS</span>
                </button>

                <button
                  onClick={() => setSimulatedDistance(220)}
                  className="w-full text-[11px] font-bold text-slate-300 hover:text-white bg-[#0A0E17] hover:bg-slate-900 border border-[#28354D] py-1.5 px-3 rounded-xl flex items-center justify-center gap-1.5 transition-colors"
                >
                  <span>💻 Asztali PC tesztelés (Kálvin tér pozíció)</span>
                </button>
              </div>

              <p className="text-[10px] text-slate-400 leading-tight pt-1">
                💡 Tipp asztali gépen: A böngésző címsorában a lakat / beállítások ikonra kattintva állítsd a „Helyadatok” jogot Engedélyezettre. Mobiltelefonon automatikusan a valós GPS-t fogja használni!
              </p>
            </div>
          )}

          {geo.coords && state.simulatedDistance === null && (
            <div className="flex items-center justify-between px-3 py-1.5 rounded-xl bg-[#0A0E17] border border-emerald-500/30 text-[11px] font-mono text-emerald-400">
              <span className="flex items-center gap-1.5 font-bold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                Valós GPS Pozíció Aktív
              </span>
              <span className="text-slate-400">Pontosság: ±{Math.round(geo.accuracy || 10)}m</span>
            </div>
          )}

          {/* Main Thermal Indicator Panel */}
          <div className="bg-[#121826] rounded-2xl p-5 border border-[#1E293B] space-y-5">
            {/* Temperature state */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span className="text-3xl">{proximityInfo.icon}</span>
                <div>
                  <div className="font-mono text-base font-black text-white uppercase">
                    {proximityInfo.label}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    {proximityInfo.description}
                  </div>
                </div>
              </div>
            </div>

            {/* Distance Meter */}
            <div className="bg-[#0A0E17] p-4 rounded-xl border border-[#1E293B] text-center">
              <div className="font-mono text-4xl font-black text-white">
                {distanceMeters} <span className="text-sm font-normal text-slate-400">méter</span>
              </div>
              <span className="text-[10px] font-mono uppercase text-slate-400 mt-0.5 block">
                Távolság a célponttól
              </span>
            </div>

            {/* Thermal Meter Bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-[11px] font-mono font-bold">
                <span className="text-blue-400 flex items-center gap-1">
                  <Snowflake className="w-3 h-3" /> HIDEG (0%)
                </span>
                <span className="text-amber-400 flex items-center gap-1">
                  MELEG (100%) <Flame className="w-3 h-3" />
                </span>
              </div>

              <div className="h-3.5 w-full bg-[#0A0E17] rounded-full p-0.5 border border-[#1E293B] overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300 bg-gradient-to-r from-blue-600 via-amber-500 to-rose-500"
                  style={{ width: `${heatPercentage}%` }}
                />
              </div>
            </div>
          </div>

          {/* Action to Manual Check-in */}
          <div className="pt-2 sticky bottom-4">
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={handleManualCheckIn}
              icon={<Check className="w-5 h-5 stroke-[3]" />}
            >
              MEGÉRKEZTÜNK! (CHECK-IN)
            </Button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 3. STEP: HELYSZÍN FELFEDVE (REVEALED SCREEN - CSAK NÉV) */}
      {/* ========================================================================= */}
      {phase === 'revealed' && (
        <div className="space-y-5 animate-in zoom-in-95">
          <div className="bg-[#121826] rounded-3xl p-7 border border-amber-500/80 text-center space-y-4 shadow-xl">
            <div className="w-20 h-20 rounded-2xl bg-[#0A0E17] border border-amber-500/40 flex items-center justify-center mx-auto text-amber-400 text-3xl shadow-inner">
              <Beer className="w-10 h-10" />
            </div>

            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500 text-xs font-mono font-black uppercase">
                <Sparkles className="w-4 h-4" />
                <span>Kocsma Leleplezve!</span>
              </div>
              <h2 className="text-3xl font-black text-white pt-1">{selectedOption.venueName}</h2>
            </div>
          </div>

          {/* Next Drink Action */}
          <div className="pt-2 sticky bottom-4">
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={handleNextDrink}
              icon={<ArrowRight className="w-5 h-5" />}
            >
              {isLastBar ? 'ESTE LEZÁRÁSA & ÜNNEPLÉS ➔' : 'KÖVETKEZŐ ITAL ➔'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
