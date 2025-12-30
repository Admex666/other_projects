import React, { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { Map, LayoutDashboard, Search, Eye, Settings, ShieldAlert, Activity, MessageSquare } from 'lucide-react';
import { cn } from '../lib/utils';
import { useGame } from '../context/GameContext';
import { ChatDrawer } from '../components/ChatDrawer';
// ... existing imports ...

const SidebarItem = ({ icon: Icon, label, to, active }) => {
    return (
        <Link
            to={to}
            className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors group",
                active
                    ? "bg-jetlag text-black font-bold"
                    : "text-gray-400 hover:bg-gray-800 hover:text-white"
            )}
        >
            <Icon size={20} className={cn("group-hover:scale-110 transition-transform", active ? "scale-110" : "")} />
            <span>{label}</span>
        </Link>
    );
};

export const DashboardLayout = () => {
    const location = useLocation();
    const { gameState, role } = useGame();
    const [isChatOpen, setIsChatOpen] = useState(false);

    return (
        <div className="flex h-screen bg-gray-950 text-white overflow-hidden font-sans">
            {/* Chat Drawer */}
            <ChatDrawer isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />

            {/* Sidebar */}
            <aside className="w-64 flex flex-col border-r border-gray-800 bg-gray-900">
                {/* ... Header ... */}
                <div className="p-6 border-b border-gray-800 flex items-center gap-2">
                    <div className="w-8 h-8 bg-jetlag rounded-full flex items-center justify-center font-bold text-black border-2 border-white">
                        JL
                    </div>
                    <h1 className="text-xl font-bold tracking-tighter">HIDE + SEEK</h1>
                </div>

                <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                    {/* ... Nav items ... */}
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-4 mt-2">
                        Game
                    </div>
                    <SidebarItem icon={Map} label="The Grid" to="/" active={location.pathname === '/'} />


                    {role === 'hider' && (
                        <SidebarItem icon={ShieldAlert} label="Hider Deck" to="/deck" active={location.pathname === '/deck'} />
                    )}

                    {!role && (
                        <div className="px-4 py-2 text-xs text-gray-500 italic">
                            Join a role in Lobby to see more tools.
                        </div>
                    )}

                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-4 mt-6">
                        System
                    </div>
                    <SidebarItem icon={LayoutDashboard} label="Lobby" to="/lobby" active={location.pathname === '/lobby'} />
                    <SidebarItem icon={Settings} label="Settings" to="/settings" active={location.pathname === '/settings'} />
                </nav>

                <div className="p-4 border-t border-gray-800 bg-gray-900/50">
                    <button
                        onClick={() => setIsChatOpen(true)}
                        className="w-full flex flex-col gap-2 p-3 rounded-xl hover:bg-gray-800 transition-colors group text-left relative"
                    >
                        <div className="flex items-center justify-between w-full">
                            <div className="flex items-center gap-2">
                                <MessageSquare size={16} className="text-jetlag group-hover:scale-110 transition-transform" />
                                <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Mission Feed</span>
                            </div>
                            {gameState.feed.length > 0 && !isChatOpen && (
                                <span className="w-2 h-2 bg-jetlag rounded-full animate-pulse shadow-[0_0_8px_rgba(230,185,30,0.5)]" />
                            )}
                        </div>

                        {gameState.feed.length > 0 ? (
                            <div className="border-l-2 border-jetlag/30 pl-3">
                                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-tighter truncate">
                                    {gameState.feed[0].type === 'chat' ? `Message from ${gameState.feed[0].sender}` : 'System Update'}
                                </p>
                                <p className="text-xs text-gray-300 line-clamp-1 italic font-medium">
                                    "{gameState.feed[0].text}"
                                </p>
                            </div>
                        ) : (
                            <p className="text-xs text-gray-600 italic px-1">Feed initialized. No activity.</p>
                        )}
                    </button>

                    <div className="mt-4 pt-3 border-t border-gray-800 flex items-center justify-between px-2">
                        <div className="flex items-center gap-2">
                            <div className={cn(
                                "w-2 h-2 rounded-full",
                                role === 'hider' ? "bg-jetlag" : role === 'seeker' ? "bg-blue-500" : "bg-gray-600"
                            )} />
                            <div className="text-xs font-black uppercase tracking-widest text-gray-500">
                                {role ? <span className={role === 'hider' ? "text-jetlag" : "text-blue-500"}>{role}</span> : "Spectator"}
                            </div>
                        </div>
                        <div className="text-[10px] font-mono text-gray-600">v1.0-COMMS</div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col relative overflow-hidden">
                {/* Header (Optional, or just content) */}
                <div className="flex-1 overflow-auto bg-gray-950 relative">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};
