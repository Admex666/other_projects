import React from 'react';
import { useQuest } from '../../context/QuestContext';
import { StageId } from '../../types/quest';
import { RotateCcw, FastForward, Navigation, Compass, X } from 'lucide-react';
import { Button } from './Button';

const ALL_STAGES: { id: StageId; name: string }[] = [
  { id: 'teaser', name: '0. Teaser / Locked' },
  { id: 'intro', name: '1. Briefing & Rules' },
  { id: 'billiard', name: '2. Biliárd Stage' },
  { id: 'food', name: '3. Étterem Radar' },
  { id: 'bar1', name: '4. Kocsma #1' },
  { id: 'bar2', name: '5. Kocsma #2' },
  { id: 'bar3', name: '6. Kocsma #3' },
  { id: 'finale', name: '7. Grand Finale' },
];

export const DevDrawer: React.FC = () => {
  const {
    config,
    state,
    jumpToStage,
    resetQuest,
    setSimulatedDistance,
    setSimulatedHeading,
    toggleDevMode,
  } = useQuest();

  if (!state.devModeEnabled) return null;

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 bg-slate-950/95 backdrop-blur-2xl border-t-2 border-amber-500/50 p-4 max-w-lg mx-auto rounded-t-3xl shadow-[0_-10px_40px_rgba(0,0,0,0.8)] animate-in slide-in-from-bottom">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping" />
          <h3 className="font-mono text-sm font-bold text-amber-400 uppercase tracking-wider">
            🛠️ Fejlesztői / Tesztelő Panel
          </h3>
        </div>
        <button
          onClick={toggleDevMode}
          className="p-1 rounded-lg text-slate-400 hover:text-white bg-slate-800"
          aria-label="Panel bezárása"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
        {/* Passcode Reminder */}
        <div className="bg-slate-900/90 rounded-xl p-2.5 border border-slate-800 flex items-center justify-between text-xs">
          <span className="text-slate-400">Aktuális feloldó jelszó:</span>
          <span className="font-mono font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
            {config.security.unlockCode}
          </span>
        </div>

        {/* Jump to Stage */}
        <div>
          <label className="text-xs font-bold text-slate-300 mb-2 flex items-center gap-1.5">
            <FastForward className="w-3.5 h-3.5 text-amber-400" /> Ugrás tetszőleges állomásra:
          </label>
          <div className="grid grid-cols-2 gap-1.5">
            {ALL_STAGES.map((stg) => {
              const isActive = state.currentStageId === stg.id;
              return (
                <button
                  key={stg.id}
                  onClick={() => jumpToStage(stg.id)}
                  className={`text-left px-2.5 py-2 rounded-xl text-xs font-semibold border transition-all ${
                    isActive
                      ? 'bg-amber-500 text-slate-950 border-amber-400 font-bold shadow-md'
                      : 'bg-slate-900 hover:bg-slate-800 text-slate-300 border-slate-800'
                  }`}
                >
                  {stg.name}
                </button>
              );
            })}
          </div>
        </div>

        {/* GPS Distance Simulation (for Food & Bar Quests) */}
        {(state.currentStageId === 'food' || state.currentStageId.startsWith('bar')) && (
          <div className="bg-slate-900/90 rounded-2xl p-3 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                <Navigation className="w-3.5 h-3.5 text-cyan-400" /> GPS Távolság Szimuláció:
              </label>
              <span className="font-mono text-xs font-bold text-cyan-400">
                {state.simulatedDistance !== null ? `${state.simulatedDistance} méter` : 'Valós GPS'}
              </span>
            </div>

            <input
              type="range"
              min="5"
              max="800"
              step="5"
              value={state.simulatedDistance ?? 350}
              onChange={(e) => setSimulatedDistance(Number(e.target.value))}
              className="w-full accent-amber-400 bg-slate-800 rounded-lg cursor-pointer"
            />

            <div className="grid grid-cols-5 gap-1 text-[10px] text-center">
              <button
                onClick={() => setSimulatedDistance(600)}
                className="py-1 bg-slate-800 hover:bg-slate-700 text-blue-300 rounded border border-blue-500/20"
              >
                ❄️ 600m
              </button>
              <button
                onClick={() => setSimulatedDistance(350)}
                className="py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded border border-cyan-500/20"
              >
                🧊 350m
              </button>
              <button
                onClick={() => setSimulatedDistance(150)}
                className="py-1 bg-slate-800 hover:bg-slate-700 text-yellow-300 rounded border border-yellow-500/20"
              >
                🌤️ 150m
              </button>
              <button
                onClick={() => setSimulatedDistance(60)}
                className="py-1 bg-slate-800 hover:bg-slate-700 text-amber-300 rounded border border-amber-500/20"
              >
                ♨️ 60m
              </button>
              <button
                onClick={() => setSimulatedDistance(15)}
                className="py-1 bg-slate-800 hover:bg-slate-700 text-rose-300 rounded border border-rose-500/20 font-bold"
              >
                🔥 15m
              </button>
            </div>

            {state.currentStageId === 'food' && (
              <>
                <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                  <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5 text-purple-400" /> Iránytű szög (0-360°):
                  </label>
                  <span className="font-mono text-xs font-bold text-purple-400">
                    {state.simulatedHeading !== null ? `${state.simulatedHeading}°` : 'Valós Szenzor'}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="359"
                  step="5"
                  value={state.simulatedHeading ?? 0}
                  onChange={(e) => setSimulatedHeading(Number(e.target.value))}
                  className="w-full accent-purple-400 bg-slate-800 rounded-lg cursor-pointer"
                />
              </>
            )}
          </div>
        )}

        {/* Global Reset */}
        <div className="pt-2">
          <Button
            variant="danger"
            size="sm"
            fullWidth
            onClick={resetQuest}
            icon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            Teljes Quest Újraindítása (Törlés)
          </Button>
        </div>
      </div>
    </div>
  );
};
