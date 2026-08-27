import React, { createContext, useContext, useState, useEffect } from 'react';
import { defaultQuestConfig } from '../config/questConfig';
import { QuestConfig, QuestState, StageId } from '../types/quest';
import { sound } from '../utils/sound';
import { triggerHaptic } from '../utils/haptics';
import { fireConfettiBurst } from '../utils/confetti';

interface QuestContextType {
  config: QuestConfig;
  state: QuestState;
  unlockWithCode: (code: string) => boolean;
  advanceToNextStage: () => void;
  goToPreviousStage: () => void;
  jumpToStage: (stageId: StageId) => void;
  selectFoodOption: (foodId: string) => void;
  selectBarOption: (stageId: string, barOptionId: string) => void;
  setBilliardScanCompleted: (completed: boolean) => void;
  unlockBarClue: () => void;
  toggleDevMode: () => void;
  setSimulatedDistance: (distance: number | null) => void;
  setSimulatedHeading: (heading: number | null) => void;
  resetQuest: () => void;
}

const STORAGE_KEY = 'marko_quest_v1';

const STAGE_ORDER: StageId[] = [
  'teaser',
  'intro',
  'billiard',
  'food',
  'bar1',
  'bar2',
  'bar3',
  'finale'
];

const initialState: QuestState = {
  isUnlocked: false,
  currentStageId: 'teaser',
  stageHistory: ['teaser'],
  isBilliardUnlockedByScan: false,
  selectedFoodId: null,
  selectedBarIds: {},
  unlockedBarClueCount: 0,
  soundEnabled: true,
  devModeEnabled: false,
  simulatedDistance: null,
  simulatedHeading: null,
};

const QuestContext = createContext<QuestContextType | null>(null);

export const QuestProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [config] = useState<QuestConfig>(defaultQuestConfig);
  const [state, setState] = useState<QuestState>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return { ...initialState, ...JSON.parse(saved) };
      }
    } catch {
      // Ignored
    }
    return initialState;
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Ignored
    }
    sound.enabled = true;
  }, [state]);

  const unlockWithCode = (code: string): boolean => {
    const cleanCode = code.trim().toLowerCase();
    const targetCode = config.security.unlockCode.trim().toLowerCase();

    if (cleanCode === targetCode || (config.security.allowOverride && cleanCode === 'admin22')) {
      sound.playUnlock();
      triggerHaptic('success');
      fireConfettiBurst();

      setState((prev) => ({
        ...prev,
        isUnlocked: true,
        currentStageId: 'intro',
        stageHistory: Array.from(new Set<StageId>([...prev.stageHistory, 'intro'])),
      }));
      return true;
    } else {
      sound.playError();
      triggerHaptic('error');
      return false;
    }
  };

  const advanceToNextStage = () => {
    const currentIndex = STAGE_ORDER.indexOf(state.currentStageId);
    if (currentIndex < STAGE_ORDER.length - 1) {
      const nextStage = STAGE_ORDER[currentIndex + 1];
      sound.playUnlock();
      triggerHaptic('success');
      fireConfettiBurst();

      setState((prev) => ({
        ...prev,
        currentStageId: nextStage,
        stageHistory: Array.from(new Set<StageId>([...prev.stageHistory, nextStage])),
      }));
    }
  };

  const goToPreviousStage = () => {
    const currentIndex = STAGE_ORDER.indexOf(state.currentStageId);
    if (currentIndex > 1) {
      const prevStage = STAGE_ORDER[currentIndex - 1];
      sound.playClick();
      triggerHaptic('light');
      setState((prev) => ({
        ...prev,
        currentStageId: prevStage,
      }));
    }
  };

  const jumpToStage = (stageId: StageId) => {
    sound.playClick();
    triggerHaptic('medium');
    setState((prev) => ({
      ...prev,
      isUnlocked: stageId !== 'teaser',
      currentStageId: stageId,
      stageHistory: Array.from(new Set<StageId>([...prev.stageHistory, stageId])),
    }));
  };

  const selectFoodOption = (foodId: string) => {
    sound.playClick();
    triggerHaptic('medium');
    setState((prev) => ({
      ...prev,
      selectedFoodId: foodId,
    }));
  };

  const selectBarOption = (stageId: string, barOptionId: string) => {
    sound.playClick();
    triggerHaptic('medium');
    setState((prev) => ({
      ...prev,
      selectedBarIds: {
        ...prev.selectedBarIds,
        [stageId]: barOptionId,
      },
    }));
  };

  const setBilliardScanCompleted = (completed: boolean) => {
    setState((prev) => ({
      ...prev,
      isBilliardUnlockedByScan: completed,
    }));
  };

  const unlockBarClue = () => {
    sound.playUnlock();
    triggerHaptic('light');
    setState((prev) => ({
      ...prev,
      unlockedBarClueCount: prev.unlockedBarClueCount + 1,
    }));
  };

  const toggleDevMode = () => {
    triggerHaptic('light');
    setState((prev) => ({ ...prev, devModeEnabled: !prev.devModeEnabled }));
  };

  const setSimulatedDistance = (distance: number | null) => {
    setState((prev) => ({ ...prev, simulatedDistance: distance }));
  };

  const setSimulatedHeading = (heading: number | null) => {
    setState((prev) => ({ ...prev, simulatedHeading: heading }));
  };

  const resetQuest = () => {
    triggerHaptic('warning');
    localStorage.removeItem(STORAGE_KEY);
    setState(initialState);
  };

  return (
    <QuestContext.Provider
      value={{
        config,
        state,
        unlockWithCode,
        advanceToNextStage,
        goToPreviousStage,
        jumpToStage,
        selectFoodOption,
        selectBarOption,
        setBilliardScanCompleted,
        unlockBarClue,
        toggleDevMode,
        setSimulatedDistance,
        setSimulatedHeading,
        resetQuest,
      }}
    >
      {children}
    </QuestContext.Provider>
  );
};

export const useQuest = () => {
  const context = useContext(QuestContext);
  if (!context) {
    throw new Error('useQuest must be used within a QuestProvider');
  }
  return context;
};
