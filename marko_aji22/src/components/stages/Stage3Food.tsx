import React, { useState, useEffect } from 'react';
import { useQuest } from '../../context/QuestContext';
import { useGeolocation } from '../../hooks/useGeolocation';
import { useCompass } from '../../hooks/useCompass';
import { calculateDistanceMeters, calculateBearing, getProximityState, getProximityInfo } from '../../utils/geo';
import { sound } from '../../utils/sound';
import { triggerHaptic } from '../../utils/haptics';
import { Check, MapPin, ExternalLink, ArrowRight, Navigation, RotateCcw } from 'lucide-react';
import { Button } from '../common/Button';

import { fireConfettiBurst } from '../../utils/confetti';

export const Stage3Food: React.FC = () => {
  const { config, state, selectFoodOption, advanceToNextStage } = useQuest();
  const food = config.stages.food;
  const geo = useGeolocation();
  const compass = useCompass();

  const [selectedId, setSelectedId] = useState<string>(state.selectedFoodId || food.options[0]?.id || 'strategy_1');
  const [isNavigating, setIsNavigating] = useState<boolean>(!!state.selectedFoodId);
  const [hasPlayedArrival, setHasPlayedArrival] = useState<boolean>(false);

  const selectedOption = food.options.find((opt) => opt.id === selectedId) || food.options[0];

  // Geolocation & Distance
  const [distanceMeters, setDistanceMeters] = useState<number>(() => {
    if (state.simulatedDistance !== null) return state.simulatedDistance;
    return 320;
  });

  useEffect(() => {
    if (state.simulatedDistance !== null) {
      setDistanceMeters(state.simulatedDistance);
    } else if (geo.coords && selectedOption) {
      const calculated = calculateDistanceMeters(geo.coords, selectedOption.targetLocation);
      setDistanceMeters(calculated);
    }
  }, [geo.coords, state.simulatedDistance, selectedOption]);

  // Bearing & compass heading
  const targetBearing = geo.coords && selectedOption
    ? calculateBearing(geo.coords, selectedOption.targetLocation)
    : 45;

  const currentHeading = state.simulatedHeading !== null ? state.simulatedHeading : compass.heading ?? 0;
  const relativeArrowRotation = (targetBearing - currentHeading + 360) % 360;

  const proximityState = getProximityState(distanceMeters);
  const proximityInfo = getProximityInfo(proximityState);
  const isArrived = proximityState === 'burning' || distanceMeters <= 30;

  // Trigger victory sound and celebratory feedback when arriving within 30 meters
  useEffect(() => {
    if (isNavigating && isArrived && !hasPlayedArrival) {
      setHasPlayedArrival(true);
      sound.playArrivalVictory();
      triggerHaptic('success');
      fireConfettiBurst();
    } else if (!isArrived && hasPlayedArrival) {
      setHasPlayedArrival(false);
    }
  }, [isNavigating, isArrived, hasPlayedArrival]);

  useEffect(() => {
    if (!isNavigating || isArrived) return;
    const interval = setInterval(() => {
      sound.playRadarPing(proximityState);
    }, proximityState === 'hot' ? 1400 : 2500);

    return () => clearInterval(interval);
  }, [isNavigating, isArrived, proximityState]);

  const handleSelect = (id: string) => {
    setSelectedId(id);
    selectFoodOption(id);
  };

  const startNavigation = () => {
    selectFoodOption(selectedId);
    setIsNavigating(true);
    sound.playUnlock();
    triggerHaptic('success');
  };

  return (
    <div className="flex flex-col min-h-[78vh] justify-between px-2 py-4 max-w-md mx-auto space-y-6">
      {/* Header */}
      <div className="text-left space-y-1.5">
        <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-widest">
          2. Állomás • {isNavigating ? 'Radar Navigáció' : 'Vacsora Stratégia'}
        </span>
        <h1 className="text-2xl sm:text-3xl font-black text-white">
          {food.title}
        </h1>
        <p className="text-xs text-slate-300 leading-relaxed">
          {isNavigating
            ? `Kiválasztva: ${selectedOption.title}. Kövesd a távolságot és a nyilat!`
            : food.introText}
        </p>
      </div>

      {/* VIEW 1: STRATEGY SELECTION */}
      {!isNavigating ? (
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
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#0A0E17] text-amber-400 border border-[#1E293B]">
                          {opt.badge}
                        </span>
                        <span className="text-[11px] text-slate-400">{opt.category}</span>
                      </div>
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
              onClick={startNavigation}
              icon={<Navigation className="w-5 h-5" />}
            >
              STRATÉGIA VÁLASZTÁSA & RADAR INDÍTÁSA
            </Button>
          </div>
        </div>
      ) : (
        /* VIEW 2: RADAR & COMPASS NAVIGATION */
        <div className="space-y-5">
          {/* Active selection bar */}
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#121826] border border-[#1E293B] text-xs">
            <div className="flex items-center gap-2.5">
              <span className="text-2xl">{selectedOption.image}</span>
              <div>
                <div className="font-bold text-white">{selectedOption.title}</div>
                <div className="text-[11px] text-amber-400 font-mono">Cél koordináták aktívak</div>
              </div>
            </div>
            <button
              onClick={() => setIsNavigating(false)}
              className="text-[11px] font-bold text-slate-300 hover:text-white flex items-center gap-1 bg-[#161F32] px-2.5 py-1 rounded-lg border border-[#28354D]"
            >
              <RotateCcw className="w-3 h-3" /> Módosítás
            </button>
          </div>

          {/* Radar Instrument */}
          <div className="bg-[#121826] rounded-2xl p-5 border border-[#1E293B] flex flex-col items-center justify-center text-center">
            <div className="relative w-56 h-56 rounded-full bg-[#0A0E17] border-2 border-[#1E293B] flex items-center justify-center my-2">
              {/* Orientation pointer */}
              <div
                className="absolute w-full h-full flex items-center justify-center transition-transform duration-300 pointer-events-none"
                style={{ transform: `rotate(${relativeArrowRotation}deg)` }}
              >
                <div className="absolute top-2 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-b-[16px] border-b-amber-400" />
              </div>

              {/* Central Display */}
              <div className="text-center z-10">
                <span className="text-2xl mb-1 block">{proximityInfo.icon}</span>
                <div className="font-mono text-3xl font-black text-white">
                  {distanceMeters} <span className="text-sm font-semibold text-slate-400">m</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mt-0.5">
                  Étterem távolság
                </span>
              </div>
            </div>

            {/* Status Label */}
            <div className="mt-3">
              <span className="font-mono text-xs font-bold text-amber-400 uppercase tracking-wider">
                {proximityInfo.label}
              </span>
              <p className="text-xs text-slate-300 mt-1 max-w-xs">{proximityInfo.description}</p>
            </div>
          </div>

          {/* Revealed Venue Information */}
          {isArrived && (
            <div className="bg-[#161F32] rounded-2xl p-4 border border-amber-500/80 space-y-2.5">
              <div className="text-xs font-mono font-bold text-amber-400 uppercase">
                Étterem beazonosítva! Megérkeztetek!
              </div>
              <div>
                <h3 className="text-base font-bold text-white">{selectedOption.venueName}</h3>
                <p className="text-xs text-slate-300 flex items-start gap-1.5 mt-0.5">
                  <MapPin className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <span>{selectedOption.venueAddress}</span>
                </p>
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

          {/* Advance Action */}
          <div className="pt-2 sticky bottom-4">
            <Button
              variant="primary"
              size="lg"
              fullWidth
              onClick={advanceToNextStage}
              icon={<ArrowRight className="w-5 h-5" />}
            >
              {isArrived ? 'VACSORA BEFEJEZVE ➔ KOCSMA KERESŐ' : 'MEGÉRKEZTÜNK AZ ÉTTEREMBE! (CHECK-IN)'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
