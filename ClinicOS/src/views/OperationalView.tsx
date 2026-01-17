import { Clock, UserCheck, AlertTriangle, Search, Activity, Cpu } from 'lucide-react';
import {
    BarChart, Bar, ResponsiveContainer, XAxis, Tooltip, CartesianGrid
} from 'recharts';
import dataEngine from '../data/DataEngine';
import { useMemo } from 'react';
import { clsx } from 'clsx';

const OperationalView: React.FC = () => {
    const data = useMemo(() => dataEngine.getDashboardData(), []);

    const avgWaitTime = useMemo(() => {
        const apps = data.appointments.filter(a => a.showed);
        return apps.length > 0 ? apps.reduce((sum, a) => sum + a.waitTime, 0) / apps.length : 0;
    }, [data]);

    const roomUtilization = useMemo(() => {
        return data.resources.filter(r => r.type === 'room').reduce((sum, r) => sum + r.utilization, 0) / 2;
    }, [data]);

    return (
        <div className="animate-premium">
            <header className="top-bar">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10B981]"></div>
                        <span className="text-[9px] font-black uppercase tracking-[0.2em] text-dim">Kapacitás: Stabil</span>
                    </div>
                    <h2 className="text-2xl font-bold tracking-tight mb-0.5 font-outfit">Operatív & Infrastruktúra</h2>
                    <p className="text-muted text-[11px] font-medium opacity-70">Valós idejű klinikai kapacitás és erőforrás felügyelet.</p>
                </div>
                <div className="flex gap-3">
                    <button className="btn-secondary">Logok exportálása</button>
                    <button className="btn-primary">Grid Optimalizálás</button>
                </div>
            </header>

            <div className="kpi-grid">
                <KPICard title="Szoba Kihasználtság" value={`${(roomUtilization * 100).toFixed(1)}%`} trend="Cél: 85%" icon={<UserCheck size={18} />} />
                <KPICard title="Átlagos Várakozás" value={`${avgWaitTime.toFixed(0)} p`} trend="Optimális" icon={<Clock size={18} />} />
                <KPICard title="Aktív Egységek" value="12" trend="Normál" icon={<Search size={18} />} />
                <KPICard title="Anomáliák" value="2" trend="Riasztás" up={false} icon={<AlertTriangle size={18} />} />
            </div>

            <div className="grid grid-cols-12 gap-6 mb-8">
                <div className="col-span-12 card">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h3 className="card-title mb-1">Kihasználtsági Mátrix</h3>
                            <p className="text-[10px] text-dim font-bold uppercase tracking-widest">Hardver és kezelőegység teljesítménymérés.</p>
                        </div>
                        <div className="flex gap-4">
                            <div className="flex items-center gap-2 text-[10px] font-black uppercase text-dim tracking-wider">
                                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400"></div> Valós idejű terhelés
                            </div>
                        </div>
                    </div>
                    <div className="h-[280px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={data.resources}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10, fontWeight: 800 }} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0D0D1A', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px' }}
                                    cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                                />
                                <Bar dataKey="utilization" fill="#22D3EE" radius={[4, 4, 0, 0]} barSize={40} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-dim mb-4 pl-1">Klinikai Infrastruktúra Csomópontok</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {data.resources.map(res => (
                    <div key={res.id} className="card p-5">
                        <div className="flex justify-between items-center mb-4">
                            <span className="text-sm font-bold text-white font-outfit">{res.name}</span>
                            <div className={clsx(
                                "badge",
                                res.utilization > 0.8 ? "badge-purple" : "badge-success"
                            )}>
                                {res.utilization > 0.8 ? <Cpu size={10} className="mr-1" /> : <Activity size={10} className="mr-1" />}
                                {res.utilization > 0.8 ? 'CSÚCS' : 'AKTÍV'}
                            </div>
                        </div>
                        <div className="flex items-baseline gap-2 mb-3">
                            <span className="text-2xl font-bold font-tech">{(res.utilization * 100).toFixed(0)}</span>
                            <span className="text-xs font-bold text-dim">%</span>
                        </div>
                        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden mb-4">
                            <div
                                className={clsx(
                                    "h-full rounded-full transition-all duration-1000",
                                    res.utilization > 0.8 ? "bg-purple-500" : "bg-cyan-400"
                                )}
                                style={{ width: `${res.utilization * 100}%` }}
                            ></div>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-[9px] font-black text-dim uppercase tracking-wider">Stabilitás: 99.8%</span>
                            <span className="text-[9px] font-black text-dim uppercase tracking-wider">LOAD: {(res.utilization * 1.2).toFixed(1)}x</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

const KPICard = ({ title, value, trend, icon, up = true }: any) => (
    <div className="card">
        <div className="kpi-icon-wrapper">{icon}</div>
        <div className="text-[10px] font-black text-muted uppercase tracking-[0.2em] mb-3">{title}</div>
        <div className="flex items-baseline justify-between">
            <span className="kpi-big-val">{value}</span>
            <div className={clsx("trend-badge font-tech", up ? "up" : "down")}>{trend}</div>
        </div>
    </div>
);

export default OperationalView;
