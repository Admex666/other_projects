import { useState } from 'react'
import ExecutiveDashboard from './features/ExecutiveDashboard'
import RetentionModule from './features/RetentionModule'
import ScenarioModule from './features/ScenarioModule'
import ManagementConsole from './features/ManagementConsole'

function App() {
    const [currentView, setCurrentView] = useState('overview')

    return (
        <div className="app-container">
            <header className="app-header">
                <div className="header-content">
                    <h1>ClinicOS v2</h1>
                    <p>Profit & Patient Intelligence</p>
                </div>
                <nav className="app-nav">
                    <button
                        className={`nav-button ${currentView === 'overview' ? 'active' : ''}`}
                        onClick={() => setCurrentView('overview')}
                    >
                        Overview
                    </button>
                    <button
                        className={`nav-button ${currentView === 'retention' ? 'active' : ''}`}
                        onClick={() => setCurrentView('retention')}
                    >
                        Retention
                    </button>
                    <button
                        className={`nav-button ${currentView === 'scenario' ? 'active' : ''}`}
                        onClick={() => setCurrentView('scenario')}
                    >
                        Simulation
                    </button>
                    <button
                        className={`nav-button ${currentView === 'management' ? 'active' : ''}`}
                        onClick={() => setCurrentView('management')}
                    >
                        Management
                    </button>
                </nav>
            </header>
            <main className="app-content">
                {currentView === 'overview' && <ExecutiveDashboard />}
                {currentView === 'retention' && <RetentionModule />}
                {currentView === 'scenario' && <ScenarioModule />}
                {currentView === 'management' && <ManagementConsole />}
            </main>
        </div>
    )
}

export default App
