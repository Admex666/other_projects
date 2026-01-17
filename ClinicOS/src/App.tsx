import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ExecutiveDashboard from './views/ExecutiveDashboard';
import OperationalView from './views/OperationalView';
import FinancialView from './views/FinancialView';
import MarketingView from './views/MarketingView';
import dataEngine from './data/DataEngine';
import { HeartPulse } from 'lucide-react';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState('ceo');
  const [isDataLoaded, setIsDataLoaded] = useState(false);

  useEffect(() => {
    const init = async () => {
      await dataEngine.loadData();
      setIsDataLoaded(true);
    };
    init();
  }, []);

  if (!isDataLoaded) {
    return (
      <div className="h-screen w-screen bg-[#080811] flex flex-col items-center justify-center text-white">
        <div className="w-16 h-16 bg-gradient-to-br from-[#8B5CF6] to-[#22D3EE] rounded-2xl flex items-center justify-center animate-pulse mb-6 shadow-[0_0_30px_rgba(139,92,246,0.5)]">
          <HeartPulse size={32} />
        </div>
        <h2 className="text-xl font-bold tracking-tight mb-2">OLAP Kockák Szinkronizálása</h2>
        <p className="text-[#64748B] text-sm animate-bounce">Tény és dimenzió táblák betöltése...</p>
      </div>
    );
  }

  const renderView = () => {
    switch (currentView) {
      case 'ceo': return <ExecutiveDashboard />;
      case 'operational': return <OperationalView />;
      case 'financial': return <FinancialView />;
      case 'marketing': return <MarketingView />;
      default: return <ExecutiveDashboard />;
    }
  };

  return (
    <div className="dashboard-container">
      <Sidebar currentView={currentView} onViewChange={setCurrentView} />
      <main className="main-content">
        {renderView()}
      </main>
    </div>
  );
};

export default App;
