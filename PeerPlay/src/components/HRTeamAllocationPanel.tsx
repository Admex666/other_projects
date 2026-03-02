'use client'

import { useState, useEffect } from 'react'
import { createTeamsForSession, assignParticipantToTeam } from '@/modules/session/actions'
import { TEAM_PROFILES } from '@/modules/session/teamProfiles'

type Participant = {
    id: string
    userId: string
    teamId: string | null
    user: { name: string }
}

type Team = {
    id: string
    name: string
    teamType: string
}

type Props = {
    sessionId: string
    participants: Participant[]
    teams: Team[]
}

// Map team profile type -> profile info for quick lookup
const PROFILE_MAP = Object.fromEntries(TEAM_PROFILES.map(p => [p.type, p]))

export default function HRTeamAllocationPanel({ sessionId, participants, teams }: Props) {
    const [localTeams, setLocalTeams] = useState<Team[]>(teams)
    const [localParticipants, setLocalParticipants] = useState<Participant[]>(participants)
    const [loading, setLoading] = useState(false)
    const [msg, setMsg] = useState<string | null>(null)

    // Keep local state in sync with SWR-refreshed props from parent
    useEffect(() => { setLocalTeams(teams) }, [teams])
    useEffect(() => { setLocalParticipants(participants) }, [participants])

    const handleCreateTeams = async () => {
        setLoading(true)
        await createTeamsForSession(sessionId)
        // Optimistically show teams - SWR will sync
        const created = TEAM_PROFILES.map(p => ({ id: 'pending-' + p.type, name: p.name, teamType: p.type }))
        setLocalTeams(created)
        setMsg('Farmok létrehozva! Rendeld hozzá a játékosokat.')
        setLoading(false)
    }

    const handleAssign = async (participantId: string, teamId: string | null) => {
        await assignParticipantToTeam(participantId, teamId, sessionId)
        setLocalParticipants(prev => prev.map(p => p.id === participantId ? { ...p, teamId } : p))
    }

    const unassigned = localParticipants.filter(p => !p.teamId)

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between bg-gray-50 -mx-6 -mt-6 px-6 py-4 border-b border-gray-100 mb-6">
                <h2 className="text-xl font-bold text-gray-900">🌾 Farm Kiosztás (Lobby)</h2>
            </div>

            {localTeams.length === 0 && (
                <div className="flex flex-col items-center gap-3 py-6">
                    <p className="text-gray-500 text-sm text-center">Először hozd létre a farm csapatokat, majd rendeld hozzá a játékosokat.</p>
                    <button
                        onClick={handleCreateTeams}
                        disabled={loading}
                        className="px-6 py-3 text-base font-bold bg-indigo-600 text-white rounded-xl shadow-md hover:bg-indigo-700 active:scale-95 disabled:opacity-50 transition-all ring-2 ring-indigo-300"
                    >
                        {loading ? '⏳ Létrehozás...' : '🌾 Farmok Létrehozása'}
                    </button>
                </div>
            )}

            {msg && <p className="mb-4 text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">{msg}</p>}

            {localTeams.length === 0 ? (
                <p className="text-gray-400 text-sm text-center py-4 italic">Kattints a &quot;Farmok Létrehozása&quot; gombra a kiosztás megkezdéséhez.</p>
            ) : (
                <div className="space-y-4">
                    {/* Unassigned players */}
                    {unassigned.length > 0 && (
                        <div className="p-4 border-2 border-dashed border-gray-200 rounded-lg">
                            <p className="text-xs font-bold uppercase text-gray-400 mb-2">Nem kiosztott játékosok ({unassigned.length})</p>
                            <div className="flex flex-wrap gap-2">
                                {unassigned.map(p => (
                                    <span key={p.id} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">
                                        {p.user.name}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Team columns */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {localTeams.map(team => {
                            const profile = PROFILE_MAP[team.teamType]
                            const members = localParticipants.filter(p => p.teamId === team.id)
                            return (
                                <div key={team.id} className="border-2 border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm">
                                    <div className="bg-indigo-50 border-b-2 border-indigo-200 px-4 py-2.5 flex justify-between items-center">
                                        <span className="font-bold text-sm text-indigo-900">{team.name}</span>
                                        <span className="text-xs font-semibold text-gray-700 bg-white border border-gray-200 rounded px-2 py-0.5">
                                            💰{profile?.cap ?? '?'} 🌱{profile?.raw ?? '?'} ⚙️{profile?.tech ?? '?'}
                                        </span>
                                    </div>
                                    <div className="p-3 space-y-2 min-h-[60px]">
                                        {members.map(p => (
                                            <div key={p.id} className="flex items-center justify-between bg-gray-50 rounded px-2 py-1 text-sm">
                                                <span>{p.user.name}</span>
                                                <button
                                                    onClick={() => handleAssign(p.id, null)}
                                                    className="text-xs text-red-400 hover:text-red-600 ml-2"
                                                    title="Kivesz csapatból"
                                                >✕</button>
                                            </div>
                                        ))}
                                        {/* Dropdown to add player */}
                                        {unassigned.length > 0 && (
                                            <select
                                                className="w-full text-xs border rounded p-1 text-gray-600 mt-1"
                                                value=""
                                                onChange={(e) => {
                                                    if (e.target.value) handleAssign(e.target.value, team.id)
                                                }}
                                            >
                                                <option value="">+ Hozzáad...</option>
                                                {unassigned.map(p => (
                                                    <option key={p.id} value={p.id}>{p.user.name}</option>
                                                ))}
                                            </select>
                                        )}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}
        </div>
    )
}
