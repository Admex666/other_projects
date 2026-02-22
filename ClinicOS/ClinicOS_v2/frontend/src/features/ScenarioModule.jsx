import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { TrendingUp, DollarSign, Percent } from 'lucide-react'

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

const ScenarioModule = () => {
    const [params, setParams] = useState({
        no_show_reduction_percent: 5,
        new_patient_increase_percent: 10,
        price_increase_percent: 0,
    })
    const [simulation, setSimulation] = useState(null)
    const [loading, setLoading] = useState(false)

    const runSimulation = async () => {
        setLoading(true)
        try {
            const { data } = await axios.post('/api/scenario/simulate', params)
            setSimulation(data)
        } catch (error) {
            console.error('Simulation failed', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        runSimulation()
    }, [params])

    const handleParamChange = (key, value) => {
        setParams(prev => ({ ...prev, [key]: parseFloat(value) }))
    }

    const chartData = simulation ? [
        {
            name: 'Comparison',
            Baseline: simulation.baseline_revenue,
            Forecast: simulation.forecasted_revenue
        }
    ] : []

    const breakdownData = simulation ? Object.entries(simulation.breakdown).map(([name, value]) => ({
        name: name.replace(/_/g, ' ').toUpperCase(),
        value: value
    })) : []

    return (
        <div className="scenario-container">
            <div className="scenario-grid">
                <div className="controls-card">
                    <h3>Simulation Parameters</h3>
                    <div className="control-group">
                        <label>No-show Reduction (%)</label>
                        <input
                            type="range" min="0" max="50" step="1"
                            value={params.no_show_reduction_percent}
                            onChange={(e) => handleParamChange('no_show_reduction_percent', e.target.value)}
                        />
                        <span className="value">{params.no_show_reduction_percent}%</span>
                    </div>
                    <div className="control-group">
                        <label>New Patient Growth (%)</label>
                        <input
                            type="range" min="0" max="100" step="5"
                            value={params.new_patient_increase_percent}
                            onChange={(e) => handleParamChange('new_patient_increase_percent', e.target.value)}
                        />
                        <span className="value">{params.new_patient_increase_percent}%</span>
                    </div>
                    <div className="control-group">
                        <label>Price Optimization (%)</label>
                        <input
                            type="range" min="0" max="30" step="1"
                            value={params.price_increase_percent}
                            onChange={(e) => handleParamChange('price_increase_percent', e.target.value)}
                        />
                        <span className="value">{params.price_increase_percent}%</span>
                    </div>
                </div>

                <div className="results-card">
                    {simulation && (
                        <>
                            <div className="impact-summary">
                                <h3>Forecasted Annual Impact</h3>
                                <div className="delta-value">
                                    <TrendingUp className="icon green" size={32} />
                                    <span>+{formatValue(simulation.delta * 12)} / year</span>
                                </div>
                                <p>Based on monthly baseline of {formatValue(simulation.baseline_revenue)}</p>
                            </div>

                            <div style={{ width: '100%', height: 300 }}>
                                <ResponsiveContainer>
                                    <BarChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                        <XAxis dataKey="name" />
                                        <YAxis tickFormatter={(val) => formatValue(val)} />
                                        <Tooltip formatter={(val) => formatValue(val)} />
                                        <Legend />
                                        <Bar dataKey="Baseline" fill="#64748b" radius={[4, 4, 0, 0]} />
                                        <Bar dataKey="Forecast" fill="#2563eb" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </>
                    )}
                </div>
            </div>

            <div className="breakdown-grid">
                {breakdownData.map((item, idx) => (
                    <div key={idx} className="breakdown-item">
                        <div className="label">{item.name}</div>
                        <div className="value">+{formatValue(item.value)}</div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default ScenarioModule
