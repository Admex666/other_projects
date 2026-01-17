import React, { useMemo, useState } from 'react';
import { DollarSign, Percent, Users, Calendar, Activity } from 'lucide-react';
import {
    CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, XAxis, YAxis, BarChart, Bar
} from 'recharts';
import dataEngine from '../data/DataEngine';
import { clsx } from 'clsx';

const ExecutiveDashboard: React.FC = () => {
    const [sliceDimension, setSliceDimension] = useState('doctor_key');
    const data = useMemo(() => dataEngine.getDashboardData(), []);

    const totalRevenue = useMemo(() => data.transactions.reduce((sum, t) => sum + t.amount, 0), [data]);
    const totalProfit = useMemo(() => data.transactions.reduce((sum, t) => sum + t.margin, 0), [data]);
    const noShowRate = useMemo(() => {
        const total = data.appointments.length;
        const noShows = data.appointments.filter(a => !a.showed).length;
        return total > 0 ? (noShows / total) * 100 : 0;
    }, [data]);

    const slicedData = useMemo(() => {
        const result = dataEngine.query({
            dimension: sliceDimension,
            metrics: ['revenue', 'margin', 'wait_time_minutes'],
            filters: { showed: 1 }
        });

        return result.map(g => {
            let label = g.name;
            if (sliceDimension === 'doctor_key') label = data.doctors.find(d => d.id === g.name)?.name || g.name;
            if (sliceDimension === 'treatment_key') {
                const treat = data.olap?.dim_treatments.find(t => t.treatment_key === g.name);
                label = treat ? treat.name : g.name;
            }
            if (sliceDimension === 'gender') label = g.name === 'M' ? 'Férfi' : 'Nő';
            if (sliceDimension === 'source_key') {
                label = data.olap?.dim_channels.find(c => c.channel_key === g.name)?.channel_name || g.name;
            }
            return { ...g, label };
        });
    }, [data, sliceDimension]);

    const NEONS = ['#8B5CF6', '#22D3EE', '#14B8A6', '#EC4899'];

    return (
        <div className="animate-premium">
            <header className="top-bar">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10B981]"></div>
                        <span className="text-[9px] font-black uppercase tracking-[0.2em] text-dim">Mag: Szinkron Aktív</span>
                    </div>
                    <h2 className="text-2xl font-bold tracking-tight mb-0.5 font-outfit">Klinikai Intelligencia <span className="text-purple-500">X</span></h2>
                    <p className="text-muted text-[11px] font-medium opacity-70">Valós idejű OLAP Vektor Analízis.</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="segmented-control">
                        <SliceBtn active={sliceDimension === 'doctor_key'} onClick={() => setSliceDimension('doctor_key')} label="Orvosok" />
                        <SliceBtn active={sliceDimension === 'treatment_key'} onClick={() => setSliceDimension('treatment_key')} label="Kezelések" />
                        <SliceBtn active={sliceDimension === 'source_key'} onClick={() => setSliceDimension('source_key')} label="Csatornák" />
                        <SliceBtn active={sliceDimension === 'gender'} onClick={() => setSliceDimension('gender')} label="Demográfia" />
                    </div>
                    <button className="btn-primary flex items-center gap-2">
                        <Activity size={14} /> Jelentés
                    </button>
                </div>
            </header>

            <div className="kpi-grid">
                <KPICard title="Összes Bevétel" value={`${(totalRevenue / 1000).toFixed(1)}k $`} trend="+12.4%" icon={<DollarSign size={18} />} />
                <KPICard title="Nettó Profit" value={`${(totalProfit / 1000).toFixed(1)}k $`} trend="+8.2%" icon={<Percent size={18} />} />
                <KPICard title="Páciensek" value={data.patients.length.toLocaleString()} trend="Stabil" icon={<Users size={18} />} />
                <KPICard title="Megtartás" value={`${(100 - noShowRate).toFixed(1)}%`} trend="-2.1%" up={false} icon={<Calendar size={18} />} />
            </div>

            <div className="grid grid-cols-12 gap-6 mb-6">
                <div className="col-span-8 card">
                    <div className="flex justify-between items-start mb-6">
                        <div>
                            <h3 className="card-title mb-1">Hozam Mátrix</h3>
                            <p className="text-[10px] text-dim font-bold uppercase tracking-widest">Bevétel vs Profit</p>
                        </div>
                        <div className="flex gap-4">
                            <div className="flex items-center gap-2">
                                <div className="w-1 h-1 rounded-full bg-[#8B5CF6]"></div>
                                <span className="text-[9px] font-black text-dim uppercase">Bruttó</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-1 h-1 rounded-full bg-[#22D3EE]"></div>
                                <span className="text-[9px] font-black text-dim uppercase">Nettó</span>
                            </div>
                        </div>
                    </div>
                    <div className="h-[280px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={slicedData} margin={{ bottom: 20 }}>
                                <defs>
                                    <linearGradient id="purpleGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#8B5CF6" stopOpacity={1} />
                                        <stop offset="100%" stopColor="#8B5CF6" stopOpacity={0.6} />
                                    </linearGradient>
                                    <linearGradient id="cyanGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#22D3EE" stopOpacity={1} />
                                        <stop offset="100%" stopColor="#22D3EE" stopOpacity={0.6} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
                                <XAxis
                                    dataKey="label"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: '#475569', fontSize: 9, fontWeight: 800 }}
                                    angle={-20}
                                    textAnchor="end"
                                    interval={0}
                                />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 9, fontWeight: 800 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k $`} />
                                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
                                <Bar name="Bevétel" dataKey="revenue" fill="url(#purpleGradient)" radius={[4, 4, 0, 0]} barSize={22} />
                                <Bar name="Profit" dataKey="margin" fill="url(#cyanGradient)" radius={[4, 4, 0, 0]} barSize={22} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="col-span-4 card flex flex-col items-center">
                    <div className="w-full card-title mb-4">
                        <span>Profit Megoszlás</span>
                    </div>
                    <div className="w-full flex-1 relative flex items-center justify-center">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={slicedData}
                                    innerRadius={65}
                                    outerRadius={90}
                                    paddingAngle={8}
                                    dataKey="margin"
                                    stroke="none"
                                    animationBegin={0}
                                    animationDuration={1500}
                                >
                                    {slicedData.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={NEONS[index % NEONS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <span className="text-[9px] font-black text-dim uppercase tracking-[0.2em]">Net</span>
                            <span className="text-xl font-bold font-outfit">{(totalProfit / 1000).toFixed(1)}k $</span>
                        </div>
                    </div>
                    <div className="w-full mt-4 pt-4 border-t border-white/5 grid grid-cols-2 gap-4">
                        <div className="flex flex-col">
                            <span className="text-[8px] font-black text-dim uppercase mb-0.5">Hatékonyság</span>
                            <span className="text-xs font-bold text-emerald-400 font-tech">94.2%</span>
                        </div>
                        <div className="flex flex-col items-end">
                            <span className="text-[8px] font-black text-dim uppercase mb-0.5">Terhelés</span>
                            <span className="text-xs font-bold text-purple-400 font-tech">8ms</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="card p-0 overflow-hidden">
                <div className="p-6 border-b border-white/5 flex justify-between items-center">
                    <div>
                        <h3 className="text-lg font-bold font-outfit">Pivot Elemző</h3>
                    </div>
                    <div className="badge badge-success px-2 py-1 text-[9px]">Vektor Motor AKTÍV</div>
                </div>
                <div className="overflow-x-auto">
                    <table className="premium-table">
                        <thead>
                            <tr>
                                <th>Entitás Azonosító</th>
                                <th>Dimenzió Kontextus</th>
                                <th>Metrikák: Forgalom</th>
                                <th>Állapot</th>
                                <th className="text-right">Metrikák: Teljesítmény</th>
                            </tr>
                        </thead>
                        <tbody>
                            {slicedData.slice(0, 8).map((g, i) => (
                                <tr key={i}>
                                    <td className="font-tech text-cyan-400">#BIN-{i + 101}</td>
                                    <td>
                                        <div className="font-bold text-white mb-1">{g.label}</div>
                                        <div className="text-[10px] text-dim font-bold uppercase tracking-tighter">ID REF: {g.name}</div>
                                    </td>
                                    <td>
                                        <div className="flex items-center gap-3">
                                            <div className="flex flex-col">
                                                <span className="text-[10px] font-black text-dim uppercase">Count</span>
                                                <span className="text-sm font-bold text-white">{g.count}</span>
                                            </div>
                                            <div className="w-[1px] h-6 bg-white/5"></div>
                                            <div className="flex flex-col">
                                                <span className="text-[10px] font-black text-dim uppercase">Várakozás</span>
                                                <span className="text-sm font-bold text-white">{g.avg_wait_time?.toFixed(0)}p</span>
                                            </div>
                                        </div>
                                    </td>
                                    <td><span className="badge badge-success">Optimalizált</span></td>
                                    <td className="text-right">
                                        <div className="font-tech text-lg text-white mb-0.5">{g.revenue.toLocaleString()} $</div>
                                        <div className="text-[10px] text-emerald-400 font-black uppercase tracking-widest">+{((g.margin / g.revenue) * 100).toFixed(1)}% MARZS</div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const SliceBtn = ({ active, onClick, label }: any) => (
    <button
        onClick={onClick}
        className={clsx("segment-btn", active && "active")}
    >
        {label}
    </button>
);

const KPICard = ({ title, value, trend, icon, up = true }: any) => (
    <div className="card">
        <div className="kpi-icon-wrapper">{icon}</div>
        <div className="text-[10px] font-black text-muted uppercase tracking-[0.25em] mb-3">{title}</div>
        <div className="flex items-baseline justify-between">
            <span className="kpi-big-val">{value}</span>
            <div className={clsx("trend-badge font-tech", up ? "up" : "down")}>{trend}</div>
        </div>
        <div className="mt-6 w-full h-[1px] bg-gradient-to-r from-white/5 to-transparent"></div>
    </div>
);

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-[#0D0D1A] border border-white/10 p-4 rounded-xl shadow-2xl backdrop-filter blur-md">
                <p className="text-[10px] font-black text-dim uppercase tracking-widest mb-3 border-b border-white/5 pb-2">{label}</p>
                {payload.map((entry: any, index: number) => (
                    <div key={index} className="flex items-center justify-between gap-6 mb-1">
                        <span className="text-[11px] font-bold text-muted transition-colors" style={{ color: entry.color }}>
                            {entry.name.toUpperCase()}
                        </span>
                        <span className="text-[11px] font-tech text-white">
                            {entry.value.toLocaleString()} $
                        </span>
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

export default ExecutiveDashboard;
