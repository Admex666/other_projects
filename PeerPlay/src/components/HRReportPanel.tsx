'use client'

import { PRODUCTION_RECIPES } from '@/modules/interaction/constants'
import { TEAM_PROFILES } from '@/modules/session/teamProfiles'

type Participant = {
    id: string
    userId: string
    teamId: string | null
    capital: number
    rawMaterial: number
    techLevel: number
    inventory: string
    user: { name: string }
}

type Team = {
    id: string
    name: string
    teamType: string
}

type Props = {
    teams: Team[]
    participants: Participant[]
}

// Sold value of inventory items from base prices
const ITEM_VALUES: Record<string, number> = Object.fromEntries(
    Object.entries(PRODUCTION_RECIPES).map(([k, v]) => [k, v.baseValue])
)

function parseInventory(json: string): Record<string, number> {
    try { return JSON.parse(json || '{}') } catch { return {} }
}

function calculateInventoryValue(inv: Record<string, number>): number {
    return Object.entries(inv).reduce((sum, [k, qty]) => sum + (ITEM_VALUES[k] || 0) * (qty || 0), 0)
}

export default function HRReportPanel({ teams, participants }: Props) {
    if (teams.length === 0) {
        return (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <h2 className="text-xl font-bold mb-2">📊 Csapat Aggregáció</h2>
                <p className="text-gray-400 text-sm italic">Nincs csapat – indítsd el a játékot először.</p>
            </div>
        )
    }

    // Aggregate per team
    const teamStats = teams.map(team => {
        const members = participants.filter(p => p.teamId === team.id)
        const totalCapital = members.reduce((sum, p) => sum + p.capital, 0)
        const totalRaw = members.reduce((sum, p) => sum + p.rawMaterial, 0)
        const totalInventoryItems: Record<string, number> = {}
        for (const p of members) {
            const inv = parseInventory(p.inventory)
            for (const [k, qty] of Object.entries(inv)) {
                totalInventoryItems[k] = (totalInventoryItems[k] || 0) + (qty || 0)
            }
        }
        const inventoryValue = calculateInventoryValue(totalInventoryItems)
        const totalWealth = totalCapital + inventoryValue

        // Find profile for this team type
        const profile = TEAM_PROFILES.find(p => p.type === team.teamType)

        return { team, members, totalCapital, totalRaw, totalInventoryItems, inventoryValue, totalWealth, profile }
    })

    // Sort by wealth descending for ranking
    const ranked = [...teamStats].sort((a, b) => b.totalWealth - a.totalWealth)

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-bold bg-gray-50 -mx-6 -mt-6 px-6 py-4 border-b border-gray-100 mb-6 flex justify-between items-center">
                <span>📊 Csapat Aggregáció & Rangsor</span>
                <span className="text-sm font-normal text-gray-400">{teams.length} csapat • {participants.length} játékos</span>
            </h2>

            <div className="space-y-4">
                {ranked.map((stat, idx) => (
                    <div key={stat.team.id} className={`rounded-xl border overflow-hidden ${idx === 0 ? 'border-yellow-400 shadow-md' : 'border-gray-200'}`}>
                        {/* Team Header */}
                        <div className={`px-5 py-3 flex justify-between items-center font-bold ${idx === 0 ? 'bg-yellow-50' : idx === 1 ? 'bg-gray-50' : idx === 2 ? 'bg-orange-50' : 'bg-white'
                            }`}>
                            <div className="flex items-center gap-2">
                                <span className="text-2xl">{idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `#${idx + 1}`}</span>
                                <div>
                                    <p className="font-black text-gray-900">{stat.team.name}</p>
                                    <p className="text-xs font-normal text-gray-500">{stat.members.length} tag</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <p className="text-xl font-black text-green-700">${stat.totalWealth.toLocaleString()}</p>
                                <p className="text-xs font-normal text-gray-400">Összes vagyon</p>
                            </div>
                        </div>

                        {/* Team Stats Row */}
                        <div className="px-5 py-3 grid grid-cols-3 gap-4 border-t border-gray-100 bg-white text-sm">
                            <div>
                                <p className="text-gray-400 text-xs">💰 Tőke</p>
                                <p className="font-bold">${stat.totalCapital.toLocaleString()}</p>
                            </div>
                            <div>
                                <p className="text-gray-400 text-xs">🌱 Vetőmag</p>
                                <p className="font-bold">{stat.totalRaw}</p>
                            </div>
                            <div>
                                <p className="text-gray-400 text-xs">🏦 Készlet érték</p>
                                <p className="font-bold text-amber-600">${stat.inventoryValue.toLocaleString()}</p>
                            </div>
                        </div>

                        {/* Inventory detail */}
                        {Object.values(stat.totalInventoryItems).some(q => q > 0) && (
                            <div className="px-5 py-2 bg-amber-50 border-t border-amber-100 flex flex-wrap gap-2 text-xs">
                                {Object.entries(stat.totalInventoryItems).filter(([, q]) => q > 0).map(([k, q]) => (
                                    <span key={k} className="px-2 py-0.5 bg-white border border-amber-200 rounded-full font-medium">
                                        {PRODUCTION_RECIPES[k as keyof typeof PRODUCTION_RECIPES]?.name ?? k}: {q}
                                    </span>
                                ))}
                            </div>
                        )}

                        {/* Members list */}
                        <div className="px-5 py-3 border-t border-gray-100 bg-gray-50">
                            <p className="text-xs font-bold text-gray-400 uppercase mb-2">Tagok</p>
                            <div className="space-y-1">
                                {stat.members.map(p => {
                                    const inv = parseInventory(p.inventory)
                                    const invVal = calculateInventoryValue(inv)
                                    return (
                                        <div key={p.id} className="flex justify-between items-center text-sm bg-white rounded px-3 py-1.5 border border-gray-100">
                                            <span className="font-medium text-gray-800">{p.user.name}</span>
                                            <div className="flex gap-3 text-xs text-gray-500">
                                                <span>💰 ${p.capital.toLocaleString()}</span>
                                                <span>🌱 {p.rawMaterial}</span>
                                                {invVal > 0 && <span className="text-amber-600 font-medium">+${invVal} készlet</span>}
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
