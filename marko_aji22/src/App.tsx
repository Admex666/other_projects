import React from 'react';
import { QuestProvider, useQuest } from './context/QuestContext';
import { HeaderHUD } from './components/common/HeaderHUD';
import { DevDrawer } from './components/common/DevDrawer';
import { Stage0Teaser } from './components/stages/Stage0Teaser';
import { Stage1Intro } from './components/stages/Stage1Intro';
import { Stage2Bowling } from './components/stages/Stage2Bowling';
import { Stage3Food } from './components/stages/Stage3Food';
import { Stage4BarRadar } from './components/stages/Stage4BarRadar';
import { Stage5Finale } from './components/stages/Stage5Finale';

const QuestRouter: React.FC = () => {
  const { state } = useQuest();

  const renderCurrentStage = () => {
    switch (state.currentStageId) {
      case 'teaser':
        return <Stage0Teaser />;
      case 'intro':
        return <Stage1Intro />;
      case 'bowling':
        return <Stage2Bowling />;
      case 'food':
        return <Stage3Food />;
      case 'bar':
        return <Stage4BarRadar />;
      case 'finale':
        return <Stage5Finale />;
      default:
        return <Stage0Teaser />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0E17] text-slate-100 flex flex-col relative overflow-x-hidden">
      {/* Top Header with Progress HUD */}
      <HeaderHUD />

      {/* Main Quest Content Container */}
      <main className="flex-1 w-full max-w-lg mx-auto pt-5 pb-20 px-3">
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
