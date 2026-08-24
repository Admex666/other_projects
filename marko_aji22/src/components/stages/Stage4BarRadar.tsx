import React, { useEffect, useState } from 'react';
import { useQuest } from '../../context/QuestContext';
import { useGeolocation } from '../../hooks/useGeolocation';
import { calculateDistanceMeters, getProximityState, getProximityInfo } from '../../utils/geo';
import { sound } from '../../utils/sound';
import { triggerHaptic } from '../../utils/haptics';
import { fireConfettiBurst } from '../../utils/confetti';
import { MapPin, ExternalLink, Check, Flame, Snowflake, Sparkles, HelpCircle, RotateCcw, ArrowRight } from 'lucide-react';
import { Button } from '../common/Button';

export const Stage4BarRadar: React.FC = () => {
  const { config, state, selectBarOption, advanceToNextStage } = useQuest();
  const bar = config.stages.bar;
  const geo = useGeolocation();

  const [selectedBarId, setSelectedBarId] = useState<string>(
    state.selectedBarId || bar.options[0]?.id || 'bar_1'
  );
  const [isHunting, setIsHunting] = useState<boolean>(!!state.selectedBarId);
  const [hasPlayedArrival, setHasPlayedArrival] = useState<boolean>(false);

  const selectedOption = bar.options.find((opt) => opt.id === selectedBarId) || bar.options[0];

  // Live or simulated distance to the chosen mystery bar
  const [distanceMeters, setDistanceMeters] = useState<number>(() => {
    if (state.simulatedDistance !== null) return state.simulatedDistance;
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

  const proximityState = getProximityState(distanceMeters, bar.thresholdsMeters);
  const proximityInfo = getProximityInfo(proximityState);
  const isArrived = proximityState === 'burning' || distanceMeters <= bar.thresholdsMeters.burning;

  const heatPercentage = Math.max(
    5,
    Math.min(100, Math.round(((500 - Math.min(distanceMeters, 500)) / (500 - 30)) * 100))
  );

  // Trigger arrival sound and celebratory confetti when arriving within 30 meters
  useEffect(() => {
    if (isHunting && isArrived && !hasPlayedArrival) {
      setHasPlayedArrival(true);
      sound.playArrivalVictory();
      triggerHaptic('success');
      fireConfettiBurst();
    } else if (!isArrived && hasPlayedArrival) {
      setHasPlayedArrival(false);
    }
  }, [isHunting, isArrived, hasPlayedArrival]);

  useEffect(() => {
    if (!isHunting || isArrived) return;
    const interval = setInterval(() => {
      sound.playRadarPing(proximityState);
    }, proximityState === 'hot' ? 1500 : 3000);

    return () => clearInterval(interval);
  }, [isHunting, isArrived, proximityState]);

  const handleSelectBar = (id: string) => {
    setSelectedBarId(id);
    selectBarOption(id);
  };

  const startHunting = () => {
    selectBarOption(selectedBarId);
    setIsHunting(true);
    sound.playUnlock();
    triggerHaptic('success');
  };

  return (
    <div className="flex flex-col min-h-[78vh] justify-between px-2 py-4 max-w-md mx-auto space-y-6">
      {/* Header */}
      <div className="text-left space-y-1.5">
        <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-widest">
          3. Állomás • {isHunting ? 'Hideg - Meleg Keresés' : 'Mystery Kocsma Választás'}
        </span>
        <h1 className="text-2xl sm:text-3xl font-black text-white">
          {bar.title}
        </h1>
        <p className="text-xs text-slate-300 leading-relaxed">
          {isHunting
            ? `Rejtélyes célpont: "${selectedOption.mysteryPhrase}". Kövessétek a hőmérsékletet!`
            : bar.riddle}
        </p>
      </div>

      {/* PHASE 1: MYSTERY BAR PHRASE SELECTION */}
      {!isHunting ? (
        <div className="space-y-4">
          <div className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5" /> Válasszatok egy rejtélyes jeligét:
          </div>

          <div className="space-y-2.5">
            {bar.options.map((opt, idx) => {
              const isSelected = opt.id === selectedBarId;
              return (
                <div
                  key={opt.id}
                  onClick={() => handleSelectBar(opt.id)}
                  className={`cursor-pointer rounded-2xl p-4 transition-all border ${
                    isSelected
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
                        🔒 Rejtett helyszín & koordináták
                      </span>
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
              onClick={startHunting}
              icon={<ArrowRight className="w-5 h-5" />}
            >
              KOCSMA KIVÁLASZTÁSA & HIDEG-MELEG INDÍTÁSA
            </Button>
          </div>
        </div>
      ) : (
        /* PHASE 2: PURE HIDEG-MELEG THERMAL HUD */
        <div className="space-y-4">
          {/* Active Mystery Bar Tag */}
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#121826] border border-[#1E293B] text-xs">
            <div>
              <div className="text-[10px] font-mono text-amber-400 font-bold uppercase">Keresett Célpont:</div>
              <div className="font-bold text-white text-sm">„{selectedOption.mysteryPhrase}”</div>
            </div>
            <button
              onClick={() => setIsHunting(false)}
              className="text-[11px] font-bold text-slate-300 hover:text-white flex items-center gap-1 bg-[#161F32] px-2.5 py-1 rounded-lg border border-[#28354D]"
            >
              <RotateCcw className="w-3 h-3" /> Módosítás
            </button>
          </div>

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

          {/* Revealed Bar Details (When Arrived or Manually Checked In) */}
          {isArrived && (
            <div className="bg-[#161F32] rounded-2xl p-4 border border-amber-500/80 space-y-2.5 animate-in zoom-in-95">
              <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-amber-400 uppercase">
                <Sparkles className="w-4 h-4" />
                <span>KOCSMA LELEPLEZVE! MEGÉRKEZTETEK!</span>
              </div>
              <div>
                <h3 className="text-lg font-black text-white">{selectedOption.venueName}</h3>
                <p className="text-xs text-slate-300 flex items-start gap-1.5 mt-0.5">
                  <MapPin className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <span>{selectedOption.venueAddress}</span>
                </p>
                {selectedOption.note && (
                  <span className="text-[11px] font-mono text-slate-400 block mt-1">
                    ℹ️ {selectedOption.note}
                  </span>
                )}
              </div>
              <a
                href={selectedOption.mapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-1.5 w-full py-2 rounded-lg bg-[#0A0E17] hover:bg-slate-900 border border-[#28354D] text-xs font-bold text-amber-400"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Megnyitás Google Térképen</span>
              </a>
            </div>
          )}

          {/* Action Advance */}
          <div className="pt-2 sticky bottom-4">
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={() => {
                sound.playVictoryFanfare();
                triggerHaptic('success');
                advanceToNextStage();
              }}
              icon={<Check className="w-5 h-5 stroke-[3]" />}
            >
              {isArrived ? 'MEGÉRKEZTÜNK! ESTE LEZÁRÁSA' : 'MEGÉRKEZTÜNK A KOCSMÁHOZ! (CHECK-IN)'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
