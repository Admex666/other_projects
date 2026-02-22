import React from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Users, UserMinus } from 'lucide-react'

const fetchCohorts = async () => {
    const { data } = await axios.get('/api/retention/cohorts')
    return data
}

const fetchChurnRisk = async () => {
    const { data } = await axios.get('/api/retention/churn-risk')
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

const RetentionModule = () => {
    const cohortQuery = useQuery({ queryKey: ['retention-cohorts'], queryFn: fetchCohorts })
    const churnQuery = useQuery({ queryKey: ['retention-churn'], queryFn: fetchChurnRisk })

    if (cohortQuery.isLoading || churnQuery.isLoading) return <div className="loading">Loading retention data...</div>
    if (cohortQuery.isError) return <div className="error">Error loading retention analytics</div>

    const cohorts = cohortQuery.data || []
    const churn = churnQuery.data || { dormant: [], lost: [], dormant_count: 0, lost_count: 0 }

    return (
        <div className="retention-container">
            <div className="kpi-grid">
                <div className="kpi-card">
                    <div className="kpi-card-header">
                        <span className="kpi-card-title">Dormant Patients</span>
                        <Users className="kpi-icon orange" size={24} />
                    </div>
                    <div className="kpi-card-value">{churn.dormant_count}</div>
                    <div className="kpi-card-subvalue">No visit in &gt;90 days</div>
                </div>
                <div className="kpi-card">
                    <div className="kpi-card-header">
                        <span className="kpi-card-title">Lost Patients</span>
                        <UserMinus className="kpi-icon red" size={24} />
                    </div>
                    <div className="kpi-card-value">{churn.lost_count}</div>
                    <div className="kpi-card-subvalue">No visit in &gt;180 days</div>
                </div>
            </div>

            <div className="chart-container">
                <h3>Patient Cohort Analysis</h3>
                <p className="chart-desc">Patients grouped by their first visit month</p>
                <div style={{ width: '100%', height: 400 }}>
                    <ResponsiveContainer>
                        <BarChart data={cohorts} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="month" />
                            <YAxis yAxisId="left" orientation="left" stroke="#2563eb" tickFormatter={(v) => formatValue(v, false)} />
                            <YAxis yAxisId="right" orientation="right" stroke="#10b981" tickFormatter={(v) => formatValue(v)} />
                            <Tooltip formatter={(val, name) => name === 'Avg LTV' ? formatValue(val) : formatValue(val, false)} />
                            <Bar yAxisId="left" dataKey="total_patients" name="Patients" fill="#2563eb" radius={[4, 4, 0, 0]} />
                            <Bar yAxisId="right" dataKey="avg_ltv" name="Avg LTV" fill="#10b981" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    )
}

export default RetentionModule
