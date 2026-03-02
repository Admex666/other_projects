'use client'

import useSWR from 'swr'
import Link from 'next/link'
import StartSessionButton from '@/components/StartSessionButton'
import NetworkGraph from '@/components/NetworkGraph'
import HRTeamAllocationPanel from '@/components/HRTeamAllocationPanel'
import HRReportPanel from '@/components/HRReportPanel'
import { getSessionDetails, closeSession } from '@/modules/session/actions'

const fetcher = async (id: string) => {
    return await getSessionDetails(id)
}

export default function SessionDetailClient({ initialSessionData }: { initialSessionData: any }) {
    const { data: sessionData } = useSWR(initialSessionData.id, fetcher, {
        fallbackData: initialSessionData,
        refreshInterval: 3000,
        revalidateOnFocus: true
    })

    const session = sessionData

    if (!session) return <div>Loading...</div>

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-5xl mx-auto space-y-6">
                <div className="flex items-center space-x-4 mb-8">
                    <Link href="/dashboard" className="text-gray-500 hover:text-gray-900">
                        &larr; Back to Dashboard
                    </Link>
                </div>

                <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 mb-2">Session: {session.scenario.name}</h1>
                        <p className="text-gray-600">
                            Room Code: <span className="font-mono text-2xl bg-indigo-100 text-indigo-900 border border-indigo-200 px-3 py-1 rounded tracking-widest font-black uppercase">{session.joinCode}</span>
                        </p>

                        <div className="mt-6 space-y-2 text-sm text-gray-700">
                            <p><span className="font-semibold text-gray-900">Organization:</span> {session.organization.name}</p>
                            <p><span className="font-semibold text-gray-900">Scenario:</span> {session.scenario.name} (v{session.scenario.version})</p>
                            <p><span className="font-semibold text-gray-900">Created:</span> {new Date(session.createdAt).toLocaleString()}</p>
                            <p><span className="font-semibold text-gray-900">Status:</span>
                                <span className={`ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                  ${session.status === 'active' ? 'bg-green-100 text-green-800' :
                                        session.status === 'draft' ? 'bg-gray-100 text-gray-800' : 'bg-blue-100 text-blue-800'}`}>
                                    {session.status.toUpperCase()}
                                </span>
                            </p>
                        </div>
                    </div>

                    <div className="text-right space-y-4">
                        {session.status === 'draft' && (
                            <StartSessionButton sessionId={session.id} participantsCount={session.participants.length} />
                        )}
                        {session.status === 'active' && (
                            <div className="flex flex-col items-end space-y-2">
                                <span className="px-4 py-2 bg-green-500 text-white font-bold rounded-lg shadow">
                                    Round {session.rounds[0]?.number} Active
                                </span>
                                <button
                                    onClick={async () => { await closeSession(session.id); }}
                                    className="text-sm underline text-red-600 hover:text-red-800"
                                >
                                    Close Session (Enable Surveys)
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* HR Manual Team Allocation - only during draft */}
                {session.status === 'draft' && (
                    <HRTeamAllocationPanel
                        sessionId={session.id}
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        participants={session.participants as any}
                        teams={session.teams}
                    />
                )}

                {/* Network Graph */}
                {(session.status === 'active' || session.status === 'closed') && (
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <h2 className="text-xl font-bold bg-gray-50 -my-6 -mx-6 p-4 border-b border-gray-100 mb-6 flex justify-between">
                            <span>Organizational Network</span>
                            <span className="text-sm bg-white border px-3 py-1 rounded-full font-normal">
                                {session.interactions.length} Trades &bull; {session.surveyResponses.length} Surveys
                            </span>
                        </h2>
                        <NetworkGraph
                            participants={session.participants}
                            interactions={session.interactions}
                            surveyResponses={session.surveyResponses}
                        />
                    </div>
                )}
                {/* Live Team Report - active or closed */}
                {(session.status === 'active' || session.status === 'closed') && (
                    <HRReportPanel
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        teams={session.teams as any}
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        participants={session.participants as any}
                    />
                )}
                {/* Participants List */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h2 className="text-xl font-bold bg-gray-50 -my-6 -mx-6 p-4 border-b border-gray-100 mb-6">
                        Participants ({session.participants.length})
                    </h2>

                    {session.participants.length > 0 ? (
                        <ul className="divide-y divide-gray-200">
                            {session.participants.map((p: any) => (
                                <li key={p.id} className="py-3 flex justify-between items-center">
                                    <div>
                                        <p className="font-medium text-gray-900">{p.user.name}</p>
                                        <p className="text-sm text-gray-600">{p.user.role} {p.user.teamMembership ? `• ${p.user.teamMembership}` : ''}</p>
                                    </div>
                                    <div className="text-sm text-gray-400">
                                        Joined at {new Date(p.joinedAt).toLocaleTimeString()}
                                    </div>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-gray-500 text-center py-4">No participants have joined yet.</p>
                    )}
                </div>

            </div>
        </div>
    )
}
