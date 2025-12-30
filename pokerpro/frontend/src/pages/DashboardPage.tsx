import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export default function DashboardPage() {
    const user = useAuthStore((state) => state.user);
    const logout = useAuthStore((state) => state.logout);

    return (
        <div className="min-h-screen bg-gray-900">
            {/* Header */}
            <header className="bg-gray-800 border-b border-gray-700">
                <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-poker-gold to-poker-gold-light bg-clip-text text-transparent">
                        PokerPro
                    </h1>
                    <div className="flex items-center gap-4">
                        <span className="text-gray-300">Welcome, {user?.username}</span>
                        <button onClick={logout} className="text-gray-400 hover:text-white">
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 py-8">
                <h2 className="text-3xl font-bold text-white mb-8">Dashboard</h2>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="card">
                        <div className="text-gray-400 text-sm mb-1">Study Time</div>
                        <div className="text-3xl font-bold text-white">12.5h</div>
                        <div className="text-green-500 text-sm mt-1">+2.5h this week</div>
                    </div>

                    <div className="card">
                        <div className="text-gray-400 text-sm mb-1">Lessons Completed</div>
                        <div className="text-3xl font-bold text-white">8/25</div>
                        <div className="text-poker-gold text-sm mt-1">32% complete</div>
                    </div>

                    <div className="card">
                        <div className="text-gray-400 text-sm mb-1">GTO Adherence</div>
                        <div className="text-3xl font-bold text-white">78%</div>
                        <div className="text-green-500 text-sm mt-1">+5% improvement</div>
                    </div>

                    <div className="card">
                        <div className="text-gray-400 text-sm mb-1">Hands Analyzed</div>
                        <div className="text-3xl font-bold text-white">142</div>
                        <div className="text-gray-400 text-sm mt-1">23 this week</div>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <Link to="/academy" className="card hover:border-poker-gold transition-all group">
                        <div className="text-4xl mb-4">📚</div>
                        <h3 className="text-xl font-bold text-white mb-2 group-hover:text-poker-gold transition-colors">
                            Academy
                        </h3>
                        <p className="text-gray-400">
                            Continue learning with structured lessons and quizzes
                        </p>
                    </Link>

                    <Link to="/gto-practice" className="card hover:border-poker-gold transition-all group">
                        <div className="text-4xl mb-4">🎯</div>
                        <h3 className="text-xl font-bold text-white mb-2 group-hover:text-poker-gold transition-colors">
                            GTO Practice
                        </h3>
                        <p className="text-gray-400">
                            Train with the GTO solver and improve your ranges
                        </p>
                    </Link>

                    <Link to="/hand-analyzer" className="card hover:border-poker-gold transition-all group">
                        <div className="text-4xl mb-4">🃏</div>
                        <h3 className="text-xl font-bold text-white mb-2 group-hover:text-poker-gold transition-colors">
                            Hand Analyzer
                        </h3>
                        <p className="text-gray-400">
                            Import and analyze your hands for leaks
                        </p>
                    </Link>

                    <Link to="/gto-solver" className="card hover:border-poker-gold transition-all group">
                        <div className="text-4xl mb-4">🧠</div>
                        <h3 className="text-xl font-bold text-white mb-2 group-hover:text-poker-gold transition-colors">
                            Quick Solver
                        </h3>
                        <p className="text-gray-400">
                            Instant GTO analysis for any spot
                        </p>
                    </Link>
                </div>

                {/* Recent Activity */}
                <div className="card mt-8">
                    <h3 className="text-xl font-bold text-white mb-4">Recent Activity</h3>
                    <div className="space-y-3">
                        <div className="flex items-center gap-3 p-3 bg-gray-700/50 rounded-lg">
                            <div className="text-2xl">✅</div>
                            <div className="flex-1">
                                <div className="text-white font-medium">Completed "Pot Odds Basics"</div>
                                <div className="text-gray-400 text-sm">2 hours ago</div>
                            </div>
                        </div>
                        <div className="flex items-center gap-3 p-3 bg-gray-700/50 rounded-lg">
                            <div className="text-2xl">📊</div>
                            <div className="flex-1">
                                <div className="text-white font-medium">Analyzed 5 hands</div>
                                <div className="text-gray-400 text-sm">Yesterday</div>
                            </div>
                        </div>
                        <div className="flex items-center gap-3 p-3 bg-gray-700/50 rounded-lg">
                            <div className="text-2xl">🎯</div>
                            <div className="flex-1">
                                <div className="text-white font-medium">GTO Practice Session</div>
                                <div className="text-gray-400 text-sm">2 days ago</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
