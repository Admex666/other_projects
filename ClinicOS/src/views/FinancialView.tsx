import { Calculator, BarChart3, TrendingUp, DollarSign } from 'lucide-react';
import {
    CartesianGrid, Tooltip, ResponsiveContainer,
    ScatterChart, Scatter, XAxis, YAxis, ZAxis, Cell
} from 'recharts';
import dataEngine from '../data/DataEngine';
import { useMemo } from 'react';
import { clsx } from 'clsx';

const FinancialView: React.FC = () => {
    const data = useMemo(() => dataEngine.getDashboardData(), []);

    const marginMatrix = useMemo(() => {
        const map: Record<string, { name: string, volume: number, profit: number }> = {};
        data.transactions.forEach(t => {
            const appointment = dataEngine.getDashboardData().appointments.find(a => a.id === t.id.replace('tr', 'a'));
            const treatmentId = appointment?.treatmentId;
            if (treatmentId) {
                if (!map[treatmentId]) map[treatmentId] = {
                    name: treatmentId === 't1' ? 'Fogkő' : treatmentId === 't2' ? 'Tömés' : treatmentId === 't3' ? 'Botox' : treatmentId === 't4' ? 'MRI' : 'Konzultáció',
                    volume: 0,
                    profit: 0
                };
                map[treatmentId].volume++;
                map[treatmentId].profit += t.margin;
            }
        });
        return Object.values(map).map(item => ({
            ...item,
            avgProfit: item.volume > 0 ? item.profit / item.volume : 0
        }));
    }, [data]);

    return (
        <div className="animate-premium">
            <header className="top-bar">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10B981]"></div>
                        <span className="text-[9px] font-black uppercase tracking-[0.2em] text-dim">Pénzügy: Auditálva</span>
                    </div>
                    <h2 className="text-2xl font-bold tracking-tight mb-0.5 font-outfit">Pénzügyi Architektúra</h2>
                    <p className="text-muted text-[11px] font-medium opacity-70">Marzsok, költségszerkezetek és bevételi források elemzése.</p>
                </div>
                <div className="flex gap-3">
                    <button className="btn-secondary">PDF Letöltése</button>
                    <button className="btn-primary">Könyvelési Szinkron</button>
                </div>
            </header>

            <div className="kpi-grid">
                <KPICard title="Teljes Marzs" value="42.8%" trend="+14.2% ↗" icon={<Calculator size={18} />} />
                <KPICard title="Bevétel / Óra" value="820 $" trend="+5.2% ↗" icon={<BarChart3 size={18} />} />
                <KPICard title="Anyagköltség" value="12.4k $" trend="Normál" icon={<DollarSign size={18} />} />
                <KPICard title="Biztosítási Arány" value="18%" trend="-2% ↘" up={false} icon={<TrendingUp size={18} />} />
            </div>

            <div className="grid grid-cols-12 gap-6 mb-6">
                <div className="col-span-12 card">
                    <div className="card-title mb-6">Beavatkozási Jövedelmezőségi Mátrix</div>
                    <div className="h-[400px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
                                <XAxis type="number" dataKey="volume" axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10, fontWeight: 800 }} name="Mennyiség" />
                                <YAxis type="number" dataKey="avgProfit" axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10, fontWeight: 800 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k $`} name="Átlagprofit" />
                                <ZAxis type="number" dataKey="profit" range={[400, 3000]} />
                                <Tooltip
                                    cursor={{ strokeDasharray: '3 3' }}
                                    contentStyle={{ backgroundColor: '#0D0D1A', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px' }}
                                />
                                <Scatter name="Kezelések" data={marginMatrix}>
                                    {marginMatrix.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#8B5CF6' : '#22D3EE'} />
                                    ))}
                                </Scatter>
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="mt-4 flex justify-center gap-8">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-[#8B5CF6]"></div>
                            <span className="text-[10px] font-black text-dim uppercase">Magas Volumen</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-[#22D3EE]"></div>
                            <span className="text-[10px] font-black text-dim uppercase">Magas Marzs</span>
                        </div>
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

export default FinancialView;
