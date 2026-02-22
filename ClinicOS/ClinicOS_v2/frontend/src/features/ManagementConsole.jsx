import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ScatterChart, Scatter, ZAxis, Cell } from 'recharts'
import { Users, TrendingUp, Target, BarChart3 } from 'lucide-react'

const fetchDoctorPerformance = async () => {
    const { data } = await axios.get('/api/manager/doctor-performance')
    return data
}

const fetchUtilization = async () => {
    const { data } = await axios.get('/api/manager/utilization')
    return data
}

const fetchMarketing = async () => {
    const { data } = await axios.get('/api/manager/marketing-deepdive')
    return data
}

const fetchLeakage = async () => {
    const { data } = await axios.get('/api/manager/leakage')
    return data
}

const formatValue = (val, isCurrency = true) => {
    if (val === undefined || val === null) return '-'
    const num = Number(val)
    const options = {
        maximumFractionDigits: num > 100 ? 0 : 1,
        minimumFractionDigits: 0
    }
    const formatted = new Intl.NumberFormat('hu-HU', options).format(num).replace(/,/g, ' ')
    return isCurrency ? `${formatted} Ft` : formatted
}

const ManagementConsole = () => {
    const [activeTab, setActiveTab] = useState('performance')

    const perfQuery = useQuery({ queryKey: ['manager-perf'], queryFn: fetchDoctorPerformance })
    const utilQuery = useQuery({ queryKey: ['manager-util'], queryFn: fetchUtilization })
    const marketQuery = useQuery({ queryKey: ['manager-market'], queryFn: fetchMarketing })
    const leakageQuery = useQuery({ queryKey: ['manager-leakage'], queryFn: fetchLeakage })

    if (perfQuery.isLoading || utilQuery.isLoading || marketQuery.isLoading || leakageQuery.isLoading) return <div className="loading">Loading insights...</div>

    return (
        <div className="management-container">
            <div className="tab-nav">
                <button
                    className={`tab-item ${activeTab === 'performance' ? 'active' : ''}`}
                    onClick={() => setActiveTab('performance')}
                >
                    <Users size={18} /> Staff Performance
                </button>
                <button
                    className={`tab-item ${activeTab === 'capacity' ? 'active' : ''}`}
                    onClick={() => setActiveTab('capacity')}
                >
                    <BarChart3 size={18} /> Capacity Planner
                </button>
                <button
                    className={`tab-item ${activeTab === 'marketing' ? 'active' : ''}`}
                    onClick={() => setActiveTab('marketing')}
                >
                    <Target size={18} /> Marketing ROI
                </button>
                <button
                    className={`tab-item ${activeTab === 'leakage' ? 'active' : ''}`}
                    onClick={() => setActiveTab('leakage')}
                >
                    <TrendingUp size={18} /> Treatment Leakage
                </button>
            </div>

            <div className="tab-content">
                {activeTab === 'performance' && (
                    <div className="chart-container">
                        <h3>Doctor Margin vs Revenue</h3>
                        <div style={{ width: '100%', height: 400 }}>
                            <ResponsiveContainer>
                                <BarChart data={perfQuery.data} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                    <XAxis dataKey="name" />
                                    <YAxis yAxisId="left" orientation="left" stroke="#2563eb" tickFormatter={(val) => formatValue(val)} />
                                    <YAxis yAxisId="right" orientation="right" stroke="#10b981" tickFormatter={(val) => formatValue(val)} />
                                    <Tooltip formatter={(val) => formatValue(val)} />
                                    <Legend />
                                    <Bar yAxisId="left" dataKey="revenue" name="Revenue" fill="#2563eb" radius={[4, 4, 0, 0]} />
                                    <Bar yAxisId="right" dataKey="profit" name="Profit" fill="#10b981" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                )}

                {activeTab === 'capacity' && (
                    <div className="chart-container">
                        <h3>Clinic Utilization (%)</h3>
                        <div style={{ width: '100%', height: 400 }}>
                            <ResponsiveContainer>
                                <BarChart data={utilQuery.data} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                    <XAxis dataKey="date" />
                                    <YAxis domain={[0, 100]} />
                                    <Tooltip />
                                    <Bar dataKey="utilization" name="Utilization %" fill="#6366f1" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                )}

                {activeTab === 'marketing' && (
                    <div className="chart-container">
                        <h3>Source Profitability (Volume vs Avg LTV)</h3>
                        <div style={{ width: '100%', height: 400 }}>
                            <ResponsiveContainer>
                                <ScatterChart margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis type="number" dataKey="volume" name="Patient Volume" />
                                    <YAxis type="number" dataKey="avg_ltv" name="Avg LTV" tickFormatter={(val) => formatValue(val)} />
                                    <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(val) => formatValue(val)} />
                                    <Scatter name="Marketing Sources" data={marketQuery.data} fill="#f59e0b">
                                        {marketQuery.data?.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill="#f59e0b" />
                                        ))}
                                    </Scatter>
                                </ScatterChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                )}
                {activeTab === 'leakage' && (
                    <div className="leakage-summary">
                        <h3>Clinical Funnel Leakage</h3>
                        <div className="kpi-grid">
                            <div className="kpi-card">
                                <span className="kpi-card-title">Total Cycles</span>
                                <div className="kpi-card-value">{formatValue(leakageQuery.data?.total_cycles, false)}</div>
                            </div>
                            <div className="kpi-card">
                                <span className="kpi-card-title">Dropout Rate</span>
                                <div className="kpi-card-value">{leakageQuery.data?.dropout_rate.toFixed(1)}%</div>
                                <div className="kpi-card-subvalue" style={{ color: 'var(--danger-color)' }}>
                                    {formatValue(leakageQuery.data?.dropped_cycles, false)} cycles lost
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default ManagementConsole
