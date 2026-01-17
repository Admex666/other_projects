import React from 'react';
import {
    BarChart3,
    Activity,
    DollarSign,
    Target,
    Search,
    Settings,
    HelpCircle,
    ChevronRight,
    ShieldCheck
} from 'lucide-react';
import { clsx } from 'clsx';

interface SidebarProps {
    currentView: string;
    onViewChange: (view: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
    const navItems = [
        { id: 'ceo', label: 'Vezetői Irányítópult', icon: <BarChart3 size={18} /> },
        { id: 'operational', label: 'Klinikai Operáció', icon: <Activity size={18} /> },
        { id: 'financial', label: 'Pénzügyi Elemzés', icon: <DollarSign size={18} /> },
        { id: 'marketing', label: 'Marketing & Növekedés', icon: <Target size={18} /> },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <div className="logo-inner">
                    <ShieldCheck size={20} className="text-white" />
                </div>
                <h1>Klinika<span className="text-purple-400">OS</span></h1>
            </div>

            <div className="sidebar-search">
                <Search size={16} />
                <input type="text" placeholder="Keresés..." />
            </div>

            <div className="flex-1">
                <p className="nav-section-title">Központi Irányítás</p>
                <nav>
                    {navItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => onViewChange(item.id)}
                            className={clsx(
                                "nav-link w-full text-left",
                                currentView === item.id && "active"
                            )}
                        >
                            {item.icon}
                            <span className="flex-1">{item.label}</span>
                            {currentView === item.id && <ChevronRight size={14} className="opacity-50" />}
                        </button>
                    ))}
                </nav>

                <p className="nav-section-title mt-8">Segédeszközök</p>
                <nav>
                    <button className="nav-link w-full text-left">
                        <Settings size={18} />
                        <span>Beállítások</span>
                    </button>
                    <button className="nav-link w-full text-left">
                        <HelpCircle size={18} />
                        <span>Támogatás</span>
                    </button>
                </nav>
            </div>

            <div className="sidebar-user">
                <div className="user-avatar">
                    <img src="https://ui-avatars.com/api/?name=Admin+User&background=8B5CF6&color=fff" alt="User" />
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-white truncate">Adminisztrátor</p>
                    <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400"></div>
                        <p className="text-[10px] font-bold text-dim uppercase tracking-widest">Rendszergazda</p>
                    </div>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
