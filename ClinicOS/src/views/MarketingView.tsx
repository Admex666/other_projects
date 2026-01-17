import { Target, Zap, Globe, Users } from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    ComposedChart, Line, Cell
} from 'recharts';
import dataEngine from '../data/DataEngine';
import { useMemo } from 'react';
import { clsx } from 'clsx';

const MarketingView: React.FC = () => {
    const data = useMemo(() => dataEngine.getDashboardData(), []);

    const channelData = useMemo(() => {
        const map: Record<string, { name: string, leads: number, conv: number }> = {};
        data.leads.forEach(l => {
            if (!map[l.channel]) map[l.channel] = { name: l.channel, leads: 0, conv: 0 };
            map[l.channel].leads++;
            if (l.converted) map[l.channel].conv++;
        });
        return Object.values(map).map(item => ({
            ...item,
            rate: item.leads > 0 ? (item.conv / item.leads) * 100 : 0
        }));
    }, [data]);

    const funnelData = [
        { name: 'Impressziók', value: 12400, fill: '#1E1B4B' },
        { name: 'Leadek', value: 800, fill: '#312E81' },
        { name: 'Minősített', value: 420, fill: '#4338CA' },
        { name: 'Időpont', value: 310, fill: '#6366F1' },
        { name: 'Látogatás', value: 265, fill: '#8B5CF6' }
    ];

    return (
        <div className="animate-premium">
            <header className="top-bar">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10B981]"></div>
                        <span className="text-[9px] font-black uppercase tracking-[0.2em] text-dim">Growth Engine: AKTÍV</span>
                    </div>
                    <h2 className="text-2xl font-bold tracking-tight mb-0.5 font-outfit">Marketing & Növekedés</h2>
                    <p className="text-muted text-[11px] font-medium opacity-70">Akvizíciós csatornák és konverziós mechanizmusok auditálása.</p>
                </div>
                <div className="flex gap-3">
                    <button className="btn-secondary">Pixel Segéd</button>
                    <button className="btn-primary">Új Kampány</button>
                </div>
            </header>

            <div className="kpi-grid">
                <KPICard title="Összes Lead" value="840" trend="+18% ↗" icon={<Users size={18} />} />
                <KPICard title="Konverzió" value="32%" trend="+4% ↗" icon={<Zap size={18} />} />
                <KPICard title="CAC Átlag" value="42 $" trend="Normál" icon={<Target size={18} />} />
                <KPICard title="LTV Index" value="4.2x" trend="+0.2 ↗" icon={<Globe size={18} />} />
            </div>

            <div className="grid grid-cols-12 gap-6 mb-6">
                <div className="col-span-5 card">
                    <div className="card-title mb-6">Akvizíciós Tölcsér</div>
                    <div className="h-[350px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={funnelData} layout="vertical" margin={{ left: 20 }}>
                                <XAxis type="number" hide />
                                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10, fontWeight: 800 }} />
                                <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ backgroundColor: '#0D0D1A', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px' }} />
                                <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={28}>
                                    {funnelData.map((e, i) => (
                                        <Cell key={i} fill={e.fill} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="col-span-7 card">
                    <div className="card-title mb-6">Csatorna Hatékonyság</div>
                    <div className="h-[350px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={channelData}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10, fontWeight: 800 }} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10, fontWeight: 800 }} />
                                <Tooltip contentStyle={{ backgroundColor: '#0D0D1A', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px' }} />
                                <Bar dataKey="leads" fill="#312E81" radius={[4, 4, 0, 0]} barSize={32} />
                                <Line type="monotone" dataKey="rate" stroke="#8B5CF6" strokeWidth={3} dot={{ r: 4, fill: '#8B5CF6' }} />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>
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

export default MarketingView;
