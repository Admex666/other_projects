import React, { useEffect, useState } from 'react';
import { useQuest } from '../../context/QuestContext';
import { useGeolocation } from '../../hooks/useGeolocation';
import { calculateDistanceMeters, getProximityState, getProximityInfo } from '../../utils/geo';
import { sound } from '../../utils/sound';
import { triggerHaptic } from '../../utils/haptics';
import { MapPin, Key, ExternalLink, Check, Flame, Snowflake } from 'lucide-react';
import { Button } from '../common/Button';

import { fireConfettiBurst } from '../../utils/confetti';

export const Stage4BarRadar: React.FC = () => {
  const { config, state, unlockBarClue, advanceToNextStage } = useQuest();
  const bar = config.stages.bar;
  const geo = useGeolocation();

  // Live or simulated distance
  const [distanceMeters, setDistanceMeters] = useState<number>(() => {
    if (state.simulatedDistance !== null) return state.simulatedDistance;
    return 350;
  });
  const [hasPlayedArrival, setHasPlayedArrival] = useState<boolean>(false);

  useEffect(() => {
    if (state.simulatedDistance !== null) {
      setDistanceMeters(state.simulatedDistance);
    } else if (geo.coords) {
      const calculated = calculateDistanceMeters(geo.coords, bar.targetLocation);
      setDistanceMeters(calculated);
    }
  }, [geo.coords, state.simulatedDistance, bar.targetLocation]);

  const proximityState = getProximityState(distanceMeters, bar.thresholdsMeters);
  const proximityInfo = getProximityInfo(proximityState);
  const isArrived = proximityState === 'burning' || distanceMeters <= bar.thresholdsMeters.burning;

  const heatPercentage = Math.max(
    5,
    Math.min(100, Math.round(((500 - Math.min(distanceMeters, 500)) / (500 - 30)) * 100))
  );

  // Trigger arrival sound and celebratory confetti when arriving within 30 meters
  useEffect(() => {
    if (isArrived && !hasPlayedArrival) {
      setHasPlayedArrival(true);
      sound.playArrivalVictory();
      triggerHaptic('success');
      fireConfettiBurst();
    } else if (!isArrived && hasPlayedArrival) {
      setHasPlayedArrival(false);
    }
  }, [isArrived, hasPlayedArrival]);

  useEffect(() => {
    if (isArrived) return;
    const interval = setInterval(() => {
      sound.playRadarPing(proximityState);
    }, proximityState === 'hot' ? 1500 : 3000);

    return () => clearInterval(interval);
  }, [isArrived, proximityState]);

  return (
    <div className="flex flex-col min-h-[78vh] justify-between px-2 py-4 max-w-md mx-auto space-y-6">
      {/* Header */}
      <div className="text-left space-y-1.5">
        <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-widest">
          3. Állomás • Hideg - Meleg Kereső
        </span>
        <h1 className="text-2xl sm:text-3xl font-black text-white">
          {bar.title}
        </h1>
        <p className="text-xs text-slate-300 leading-relaxed">
          {bar.riddle}
        </p>
      </div>

      {/* Main Thermal Indicator Panel */}
      <div className="space-y-4">
        <div className="bg-[#121826] rounded-2xl p-5 border border-[#1E293B] space-y-5">
          {/* Temperature state */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{proximityInfo.icon}</span>
              <div>
                <div className="font-mono text-sm font-bold text-white uppercase">
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

        {/* Clues Accordion */}
        <div className="bg-[#121826] rounded-2xl p-4 border border-[#1E293B] space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-slate-300 uppercase">
              <Key className="w-3.5 h-3.5 text-amber-400" />
              <span>Nyomok ({state.unlockedBarClueCount} / {bar.clues.length})</span>
            </div>

            {state.unlockedBarClueCount < bar.clues.length && (
              <button
                onClick={unlockBarClue}
                className="text-[11px] font-bold text-amber-400 bg-[#161F32] hover:bg-[#1E293B] px-2.5 py-1 rounded-lg border border-[#28354D] active:scale-95 transition-transform"
              >
                + Újabb Nyom
              </button>
            )}
          </div>

          {state.unlockedBarClueCount === 0 ? (
            <p className="text-xs text-slate-400 italic">
              Ha elakadnátok a keresésben, nyissátok meg az első nyomot!
            </p>
          ) : (
            <div className="space-y-2">
              {bar.clues.slice(0, state.unlockedBarClueCount).map((clue, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-[#0A0E17] border border-[#1E293B] text-xs text-slate-200"
                >
                  {clue}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Revealed Bar Details */}
        {isArrived && (
          <div className="bg-[#161F32] rounded-2xl p-4 border border-amber-500/80 space-y-2.5">
            <div className="text-xs font-mono font-bold text-amber-400 uppercase">
              Kocsma beazonosítva! Megérkeztetek!
            </div>
            <div>
              <h3 className="text-base font-bold text-white">{bar.venueNameRevealed}</h3>
              <p className="text-xs text-slate-300 flex items-start gap-1.5 mt-0.5">
                <MapPin className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                <span>{bar.venueAddressRevealed}</span>
              </p>
            </div>
            <a
              href={bar.mapsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-1.5 w-full py-2 rounded-lg bg-[#0A0E17] hover:bg-slate-900 border border-[#28354D] text-xs font-bold text-amber-400"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Megnyitás Google Térképen</span>
            </a>
          </div>
        )}
      </div>

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
  );
};
