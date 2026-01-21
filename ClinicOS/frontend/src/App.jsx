import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, AreaChart, Area, ScatterChart, Scatter, ZAxis, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { Activity, Users, DollarSign, Calendar, TrendingUp, AlertTriangle } from 'lucide-react';

// Custom Tooltip for better formatting
const CustomTooltip = ({ active, payload, label, unit = "" }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-slate-800 text-white p-3 rounded-lg shadow-xl text-xs">
                <p className="font-bold mb-1">{label}</p>
                {payload.map((entry, index) => (
                    <p key={index} style={{ color: entry.color }}>
                        {entry.name}: {entry.value.toLocaleString()} {unit}
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

function App() {
    const [activeTab, setActiveTab] = useState('executive');
    const [filters, setFilters] = useState({
        clinic: '',
        period: '30d',
        doctor: ''
    });

    const handleFilterChange = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    return (
        <div className="min-h-screen bg-gray-50 flex font-sans text-slate-800">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 text-white flex flex-col">
                <div className="p-6 border-b border-slate-700">
                    <h1 className="text-xl font-bold tracking-tight flex items-center gap-2">
                        <Activity className="text-emerald-400" />
                        ClinicOS
                    </h1>
                    <p className="text-xs text-slate-400 mt-1">Intelligence Suite</p>
                </div>

                <nav className="flex-1 p-4 space-y-2">
                    <NavButton id="executive" icon={Activity} label="Executive Overview" active={activeTab} set={setActiveTab} />
                    <NavButton id="retention" icon={Users} label="Patient Retention" active={activeTab} set={setActiveTab} />
                    <NavButton id="operations" icon={Calendar} label="Capacity & Ops" active={activeTab} set={setActiveTab} />
                    <NavButton id="finance" icon={DollarSign} label="Profit & Growth" active={activeTab} set={setActiveTab} />
                    <NavButton id="forecast" icon={TrendingUp} label="Forecast" active={activeTab} set={setActiveTab} />
                </nav>

                <div className="p-4 bg-slate-800 m-4 rounded-lg">
                    <div className="flex items-center gap-2 text-amber-400 mb-2">
                        <AlertTriangle size={16} />
                        <span className="text-xs font-bold uppercase">Alert</span>
                    </div>
                    <p className="text-xs text-slate-300">
                        Detected: 12% revenue risk in "New Patient" segment.
                    </p>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                <header className="bg-white border-b px-8 py-4 flex justify-between items-center sticky top-0 z-10">
                    <h2 className="text-2xl font-semibold text-slate-800">
                        {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Dashboard
                    </h2>
                    <div className="flex gap-4">
                        {/* Drilldowns */}
                        <select
                            className="bg-white border border-slate-300 text-slate-600 text-sm rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
                            onChange={(e) => handleFilterChange('clinic', e.target.value)}
                            value={filters.clinic}
                        >
                            <option value="">Clinic: All</option>
                            <option value="1">Buda & Pest</option>
                            <option value="2">WestEnd Center</option>
                        </select>
                        <select
                            className="bg-white border border-slate-300 text-slate-600 text-sm rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
                            onChange={(e) => handleFilterChange('period', e.target.value)}
                            value={filters.period}
                        >
                            <option value="30d">Period: Last 30 Days</option>
                            <option value="quarter">This Quarter</option>
                            <option value="ytd">YTD</option>
                        </select>
                        <select
                            className="bg-white border border-slate-300 text-slate-600 text-sm rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
                            onChange={(e) => handleFilterChange('doctor', e.target.value)}
                            value={filters.doctor}
                        >
                            <option value="">Doctor: All</option>
                            <option value="1">Dr. Kovács Béla</option>
                            <option value="2">Dr. Szabó Anna</option>
                            <option value="3">Dr. Nagy Péter</option>
                        </select>
                    </div>
                </header>

                <div className="p-8">
                    {activeTab === 'executive' && <ExecutiveDashboard CustomTooltip={CustomTooltip} filters={filters} />}
                    {activeTab === 'retention' && <RetentionDashboard CustomTooltip={CustomTooltip} filters={filters} />}
                    {activeTab === 'operations' && <OperationsDashboard filters={filters} />}
                    {activeTab === 'finance' && <FinanceDashboard />}
                    {activeTab === 'forecast' && <ForecastDashboard CustomTooltip={CustomTooltip} />}
                </div>
            </main>
        </div>
    );
}

const NavButton = ({ id, icon: Icon, label, active, set }) => (
    <button
        onClick={() => set(id)}
        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${active === id ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
    >
        <Icon size={18} />
        {label}
    </button>
);

const RetentionDashboard = ({ CustomTooltip, filters }) => {
    const [data, setData] = useState(null);
    useEffect(() => {
        const p = new URLSearchParams();
        if (filters.doctor) p.append('doctor_id', filters.doctor);
        fetch(`/api/kpi/retention?${p.toString()}`).then(r => r.json()).then(setData);
    }, [filters.doctor]);

    if (!data) return <div className="p-10">Loading...</div>;
    if (data.detail) return <div className="p-10 text-red-500">Error loading data: {JSON.stringify(data.detail)}</div>;

    return (
        <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 5. Marketing Paradox Insight */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-start mb-4">
                        <h3 className="text-lg font-semibold text-slate-800">Acquisition Source Quality</h3>
                        <span className="bg-red-100 text-red-700 text-xs font-bold px-2 py-1 rounded">PROBLEM DETECTED</span>
                    </div>
                    <p className="text-sm text-slate-500 mb-6">
                        "Facebook Ads" brings volume, but 2x churn rate. <br />
                        <strong>Insight:</strong> You are paying to acquire patients who leave immediately.
                    </p>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={data.marketing_analysis}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                <XAxis dataKey="channel" axisLine={false} tickLine={false} />
                                <YAxis yAxisId="left" orientation="left" stroke="#64748B" />
                                <YAxis yAxisId="right" orientation="right" stroke="#ef4444" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />
                                <Legend />
                                <Bar yAxisId="left" dataKey="volume" name="New Patients" fill="#cbd5e1" radius={[4, 4, 0, 0]} />
                                <Bar yAxisId="right" dataKey="churn_rate" name="Churn Rate" fill="#ef4444" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* 2. Invisible Churn Insight */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-800 mb-2">The "Ghost" Rate</h3>
                    <div className="flex items-end gap-4 mb-4">
                        <span className="text-4xl font-bold text-slate-900">{(data.ghost_rate * 100).toFixed(0)}%</span>
                        <span className="text-sm text-slate-500 mb-1">of new patients never return</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-4 mb-2 overflow-hidden">
                        <div className="bg-slate-800 h-4 rounded-full" style={{ width: `${data.ghost_rate * 100}%` }}></div>
                    </div>
                    <p className="text-xs text-slate-400">Industry average: 15%</p>

                    <div className="mt-8 p-4 bg-amber-50 border border-amber-100 rounded-lg">
                        <h4 className="text-sm font-bold text-amber-800 mb-1">⚠ Revenue Leak</h4>
                        <p className="text-xs text-amber-700">
                            These are not "complaints". These are silent drop-offs.
                            Most occur after <strong>Premium Body Scan</strong> (False Good Service).
                        </p>
                    </div>
                </div>
            </div>

            {/* Cohort Curve */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <h3 className="text-lg font-semibold mb-4">Retention Curve (Last 6 Months)</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.cohorts}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="month" axisLine={false} tickLine={false} />
                            <YAxis hide />
                            <Tooltip content={<CustomTooltip unit="%" />} />
                            <Area type="monotone" dataKey="retention" stroke="#6366f1" fill="#e0e7ff" strokeWidth={3} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};



const OperationsDashboard = ({ filters }) => {
    const [data, setData] = useState(null);
    useEffect(() => {
        const p = new URLSearchParams();
        if (filters.clinic) p.append('clinic_id', filters.clinic);
        fetch(`/api/kpi/operations?${p.toString()}`).then(r => r.json()).then(setData);
    }, [filters.clinic]);

    if (!data) return <div className="p-10">Loading...</div>;
    if (data.detail) return <div className="p-10 text-red-500">Error: {JSON.stringify(data.detail)}</div>;

    return (
        <div className="space-y-8">
            <h3 className="text-lg font-semibold text-slate-800">Doctor Utilization & Risk</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Capacity Illusion Chart */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm col-span-2 md:col-span-1">
                    <h4 className="text-sm font-bold text-slate-500 mb-4">CAPACITY UTILIZATION (Last Period)</h4>
                    <div className="space-y-4">
                        {data.map((doc) => (
                            <div key={doc.doctor}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-medium">{doc.doctor}</span>
                                    <span className={doc.utilization > 100 ? "text-red-500 font-bold" : "text-slate-600"}>
                                        {doc.utilization}%
                                    </span>
                                </div>
                                <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                                    <div
                                        className={`h-2.5 rounded-full ${doc.utilization > 95 ? 'bg-red-500' :
                                            doc.utilization < 50 ? 'bg-amber-400' : 'bg-emerald-500'
                                            }`}
                                        style={{ width: `${Math.min(doc.utilization, 100)}%` }}
                                    ></div>
                                </div>
                                <div className="text-xs text-slate-400 mt-1 flex justify-between">
                                    <span>{doc.role}</span>
                                    {doc.utilization > 95 && <span className="text-red-500 flex items-center gap-1"><AlertTriangle size={10} /> Overworked</span>}
                                    {doc.utilization < 50 && <span className="text-amber-500">Underutilized</span>}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Risk Radar */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm col-span-2 md:col-span-1">
                    <h4 className="text-sm font-bold text-slate-500 mb-4">RETENTION RISK BY DOCTOR</h4>
                    <p className="text-xs text-slate-400 mb-4">Patients seen by these doctors have higher churn rates.</p>

                    <div className="space-y-3">
                        {data.map((doc) => (
                            <div key={doc.doctor} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100">
                                <div className="flex items-center gap-3">
                                    <div className={`w-2 h-2 rounded-full ${doc.churn_risk === 'High' ? 'bg-red-500' : 'bg-green-400'}`}></div>
                                    <span className="text-sm font-medium text-slate-700">{doc.doctor}</span>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs text-slate-500">No-Show Rate</div>
                                    <div className={`text-sm font-bold ${doc.no_show_rate > 0.15 ? 'text-red-600' : 'text-slate-800'}`}>
                                        {(doc.no_show_rate * 100).toFixed(1)}%
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="mt-6 p-3 bg-red-50 border border-red-100 rounded text-xs text-red-700">
                        <strong>Insight:</strong> Dr. Nagy has 2x industry average no-show rate. Suggest reviewing communication style.
                    </div>
                </div>
            </div>
        </div>
    )
}



const FinanceDashboard = () => {
    const [data, setData] = useState(null);
    useEffect(() => {
        fetch('/api/kpi/finance').then(r => r.json()).then(setData);
    }, []);

    if (!data) return <div className="p-10">Loading...</div>;

    // Transform logic for bubbles: X=Revenue, Y=Margin, Z=Size
    // Chart library might need specific format. We will use a Scatter (Dot) chart for simplicity in this demo.

    return (
        <div className="space-y-8">
            <h3 className="text-lg font-semibold text-slate-800">Profitability Matrix</h3>

            <div className="grid grid-cols-1 gap-6">
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <h4 className="text-sm font-bold text-slate-500 mb-6">SERVICE PROFITABILITY (Revenue vs Margin)</h4>

                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-slate-400 uppercase bg-slate-50">
                                <tr>
                                    <th className="px-6 py-3">Service</th>
                                    <th className="px-6 py-3">Category</th>
                                    <th className="px-6 py-3 text-right">Revenue</th>
                                    <th className="px-6 py-3 text-right">Margin %</th>
                                    <th className="px-6 py-3">Insight</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.map((item, idx) => (
                                    <tr key={idx} className="bg-white border-b hover:bg-slate-50">
                                        <td className="px-6 py-4 font-medium text-slate-900">{item.service}</td>
                                        <td className="px-6 py-4 text-slate-500">{item.category}</td>
                                        <td className="px-6 py-4 text-right">{item.revenue?.toLocaleString()} Ft</td>
                                        <td className={`px-6 py-4 text-right font-bold ${item.margin_pct < 20 ? 'text-red-500' : 'text-emerald-600'
                                            }`}>
                                            {item.margin_pct}%
                                        </td>
                                        <td className="px-6 py-4">
                                            {item.anomaly === 'High Churn Driver' && (
                                                <span className="bg-red-100 text-red-800 text-xs font-semibold px-2.5 py-0.5 rounded">
                                                    ⚠ FALSE GOOD
                                                </span>
                                            )}
                                            {item.anomaly === 'Pricing Flaw' && (
                                                <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded">
                                                    ⚠ PRICING
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <div className="mt-8 p-4 bg-slate-50 rounded-lg text-sm text-slate-600">
                        <strong>Analysis:</strong>
                        <ul className="list-disc pl-5 mt-2 space-y-1">
                            <li><strong>Premium Body Scan:</strong> Generates high revenue but has 0% LTV contribution (One-off).
                                <span className="text-red-500 ml-1"> Hidden 3-year loss: ~45M Ft potential.</span></li>
                            <li><strong>Physio Therapy:</strong> 90% drop-off after 2nd session due to pricing structure.</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    )
}



const ForecastDashboard = () => {
    const [scenarios, setScenarios] = useState(null);
    useEffect(() => {
        fetch('/api/kpi/forecast').then(r => r.json()).then(setScenarios);
    }, []);

    if (!scenarios) return <div className="p-10">Loading...</div>;

    const data = scenarios.map(s => ({
        name: s.name,
        Revenue: s.revenue / 1000000, // Millions
        Growth: s.growth * 100
    }));

    return (
        <div className="space-y-8">
            <h3 className="text-lg font-semibold text-slate-800">Scenario Planning: "What if?"</h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {scenarios.map((s, i) => (
                    <div key={i} className={`p-6 rounded-xl border ${s.name.includes("Baseline") ? "bg-slate-50 border-slate-200" : "bg-white border-indigo-100 shadow-md"}`}>
                        <div className="flex justify-between items-center mb-4">
                            <h4 className="font-bold text-slate-700">{s.name}</h4>
                            {s.impact === "High" && <span className="bg-emerald-100 text-emerald-700 text-xs px-2 py-1 rounded font-bold">Recommended</span>}
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-500">Proj. Revenue</span>
                                <span className="font-bold text-slate-900">{(s.revenue / 1000000).toFixed(1)}M Ft</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-500">Growth Rate</span>
                                <span className={`font-bold ${s.growth > 0.1 ? "text-emerald-600" : "text-slate-600"}`}>
                                    +{(s.growth * 100).toFixed(1)}%
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <h4 className="text-sm font-bold text-slate-500 mb-6">REVENUE IMPACT PROJECTION (Next 12 Months)</h4>
                <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data} layout="vertical" margin={{ left: 40 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                            <XAxis type="number" unit="M" />
                            <YAxis dataKey="name" type="category" width={150} tick={{ fontSize: 12 }} />
                            <Tooltip cursor={{ fill: 'transparent' }} />
                            <Bar dataKey="Revenue" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={40}>
                                {data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.name.includes("Baseline") ? "#cbd5e1" : "#6366f1"} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    )
}

// Helper to strip empty params to avoid FastAPI 422 errors
const getCleanParams = (filters) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
        if (value !== '' && value !== null && value !== undefined) {
            // Map frontend keys to backend keys if needed
            // Executive uses same keys. Retention uses doctor_id. Operations uses clinic_id.
            // We can handle mapping at call site or here.
            // Let's pass raw values and handle mapping at call site.
            params.append(key, value);
        }
    });
    return params;
};

const ExecutiveDashboard = ({ CustomTooltip, filters }) => {
    const [kpis, setKpis] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Executive accepts clinic_id, doctor_id, period.
        // Frontend filters: clinic (becomes clinic_id?), doctor (becomes doctor_id?), period.
        // Let's map explicitly.
        const p = new URLSearchParams();
        if (filters.clinic) p.append('clinic_id', filters.clinic);
        if (filters.doctor) p.append('doctor_id', filters.doctor);
        if (filters.period) p.append('period', filters.period);

        fetch(`/api/kpi/executive?${p.toString()}`)
            .then(res => res.json())
            .then(data => {
                setKpis(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch", err);
                setLoading(false);
            });
    }, [filters]);

    // Use real chart data or fallback to empty array
    const chartData = kpis?.chart_data || [];

    if (loading) return <div className="p-10 text-center text-slate-400">Loading financial intelligence...</div>;
    if (!kpis || kpis.detail) return <div className="p-10 text-center text-red-500">Error loading data.</div>;

    const trends = kpis.trends || {};

    return (
        <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <KpiCard
                    title="Total Revenue"
                    value={(kpis?.revenue_total_30d || 0).toLocaleString() + " Ft"}
                    trend={`${trends.revenue > 0 ? '+' : ''}${trends.revenue}%`}
                    positive={trends.revenue >= 0}
                />
                <KpiCard
                    title="Revenue at Risk"
                    value={(kpis?.revenue_at_risk || 0).toLocaleString() + " Ft"}
                    trend={`${trends.risk > 0 ? '+' : ''}${trends.risk}%`}
                    positive={trends.risk <= 0} // Lower risk is positive
                    type="danger"
                />
                <KpiCard
                    title="Active Patients"
                    value={kpis?.active_patients || 0}
                    trend={`${trends.patients > 0 ? '+' : ''}${trends.patients}%`}
                    positive={trends.patients >= 0}
                />
                <KpiCard
                    title="Capacity Utilization"
                    value={(kpis?.utilization_rate * 100).toFixed(0) + "%"}
                    trend={`${trends.utilization > 0 ? '+' : ''}${trends.utilization}%`}
                    positive={trends.utilization >= 0}
                />
            </div>

            {/* Main Chart */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <h3 className="text-lg font-semibold mb-6">Revenue vs Cost Trend</h3>
                <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748B' }} dy={10} minTickGap={30} />
                            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B' }} />
                            <Tooltip content={<CustomTooltip unit="Ft" />} cursor={{ stroke: '#cbd5e1', strokeWidth: 1 }} />
                            <Line type="monotone" dataKey="revenue" stroke="#6366f1" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                            <Line type="monotone" dataKey="cost" stroke="#ef4444" strokeWidth={3} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    )
}

const KpiCard = ({ title, value, trend, positive, type = "normal" }) => (
    <div className={`p-6 rounded-xl border flex flex-col justify-between ${type === "danger" ? "bg-red-50 border-red-100" : "bg-white border-slate-200 shadow-sm"
        }`}>
        <p className={`text-sm font-medium ${type === "danger" ? "text-red-600" : "text-slate-500"}`}>{title}</p>
        <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-2xl font-bold ${type === "danger" ? "text-red-700" : "text-slate-900"}`}>{value}</span>
        </div>
        <div className="mt-2 flex items-center gap-1 text-xs">
            <span className={positive ? "text-emerald-600 font-medium" : "text-red-500 font-medium"}>
                {trend}
            </span>
            <span className="text-slate-400">vs last period</span>
        </div>
    </div>
)

export default App;
