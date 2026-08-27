import React from 'react';
import { QuestProvider, useQuest } from './context/QuestContext';
import { HeaderHUD } from './components/common/HeaderHUD';
import { DevDrawer } from './components/common/DevDrawer';
import { Stage0Teaser } from './components/stages/Stage0Teaser';
import { Stage1Intro } from './components/stages/Stage1Intro';
import { Stage2Billiard } from './components/stages/Stage2Billiard';
import { Stage3Food } from './components/stages/Stage3Food';
import { Stage4BarRadar } from './components/stages/Stage4BarRadar';
import { Stage5Finale } from './components/stages/Stage5Finale';

const QuestRouter: React.FC = () => {
  const { state } = useQuest();

  const renderCurrentStage = () => {
    switch (state.currentStageId) {
      case 'teaser':
        return <Stage0Teaser key="teaser" />;
      case 'intro':
        return <Stage1Intro key="intro" />;
      case 'billiard':
        return <Stage2Billiard key="billiard" />;
      case 'food':
        return <Stage3Food key="food" />;
      case 'bar1':
        return <Stage4BarRadar key="bar1" barStageId="bar1" />;
      case 'bar2':
        return <Stage4BarRadar key="bar2" barStageId="bar2" />;
      case 'bar3':
        return <Stage4BarRadar key="bar3" barStageId="bar3" />;
      case 'finale':
        return <Stage5Finale key="finale" />;
      default:
        return <Stage0Teaser key="default" />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0E17] text-slate-100 flex flex-col relative overflow-x-hidden">
      {/* Top Header with Progress HUD */}
      <HeaderHUD />

      {/* Main Quest Content Container */}
      <main className="flex-1 w-full max-w-lg mx-auto pt-2 pb-12 px-3">
        {renderCurrentStage()}
      </main>

      {/* Dev and Simulation Drawer */}
      <DevDrawer />
    </div>
  );
};

export function App() {
  return (
    <QuestProvider>
      <QuestRouter />
    </QuestProvider>
  );
}

export default App;
