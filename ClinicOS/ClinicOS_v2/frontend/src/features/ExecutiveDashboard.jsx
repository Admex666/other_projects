import React from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { TrendingUp, AlertTriangle, Users, DollarSign } from 'lucide-react'

const fetchSummary = async () => {
    const { data } = await axios.get('/api/dashboard/summary')
    return data
}

const fetchTrend = async () => {
    const { data } = await axios.get('/api/dashboard/revenue-trend')
    return data
}

const KPICard = ({ title, value, icon: Icon, color, subValue }) => (
    <div className="kpi-card">
        <div className="kpi-card-header">
            <span className="kpi-card-title">{title}</span>
            <Icon className={`kpi-icon ${color}`} size={24} />
        </div>
        <div className="kpi-card-value">{value}</div>
        {subValue && <div className="kpi-card-subvalue">{subValue}</div>}
    </div>
)

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

const ExecutiveDashboard = () => {
    const summaryQuery = useQuery({ queryKey: ['dashboard-summary'], queryFn: fetchSummary })
    const trendQuery = useQuery({ queryKey: ['dashboard-trend'], queryFn: fetchTrend })

    if (summaryQuery.isLoading || trendQuery.isLoading) return <div className="loading">Loading dashboard...</div>
    if (summaryQuery.isError) return <div className="error">Error loading summary</div>

    const summary = summaryQuery.data || {}
    const trend = trendQuery.data || []

    return (
        <div className="dashboard-container">
            <div className="kpi-grid">
                <KPICard
                    title="Total Revenue"
                    value={formatValue(summary.total_revenue)}
                    icon={DollarSign}
                    color="blue"
                />
                <KPICard
                    title="No-show Rate"
                    value={`${summary.no_show_rate?.toFixed(1)}%`}
                    icon={AlertTriangle}
                    color="orange"
                    subValue="Revenue impact could be reduced"
                />
                <KPICard
                    title="Patient Mix"
                    value={formatValue(summary.patient_mix?.returning + summary.patient_mix?.new, false)}
                    icon={Users}
                    color="green"
                    subValue={`${summary.patient_mix?.returning} Returning / ${summary.patient_mix?.new} New`}
                />
                <KPICard
                    title="Revenue at Risk"
                    value={formatValue(summary.revenue_at_risk)}
                    icon={TrendingUp}
                    color="red"
                    subValue="From lost/dormant patients"
                />
            </div>

            <div className="chart-container">
                <h3>Revenue Trend (Last 30 Days)</h3>
                <div style={{ width: '100%', height: 300 }}>
                    <ResponsiveContainer>
                        <LineChart data={trend} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="date" />
                            <YAxis tickFormatter={(val) => formatValue(val)} />
                            <Tooltip formatter={(val) => formatValue(val)} />
                            <Line type="monotone" dataKey="amount" stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    )
}

export default ExecutiveDashboard
