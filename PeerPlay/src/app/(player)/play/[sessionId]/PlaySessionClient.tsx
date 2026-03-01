'use client'

import { redirect } from 'next/navigation'
import TradeActionForm from '@/components/TradeActionForm'
import ProductionPanel from '@/components/ProductionPanel'
import { getSessionDetails } from '@/modules/session/actions'
import useSWR from 'swr'

// Fetcher uses Server Action directly
const fetcher = async (sessionId: string) => {
    return await getSessionDetails(sessionId)
}

export default function PlaySessionClient({
    sessionId,
    initialUserId,
    initialSessionData
}: {
    sessionId: string,
    initialUserId: string,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    initialSessionData: any
}) {
    // SWR hook for real-time polling every 3 seconds inside active views 
    const { data: sessionData } = useSWR(sessionId, fetcher, {
        fallbackData: initialSessionData,
        refreshInterval: 3000,
        revalidateOnFocus: true
    })

    const session = sessionData

    if (!session) return <div>Loading session...</div>

    const currentUserId = initialUserId

    if (!currentUserId) {
        return (
            <div className="p-8 text-center">
                <h1 className="text-xl font-bold text-red-600">Error: Missing User ID</h1>
                <p>Please join the session through the Join page to get a valid link.</p>
            </div>
        )
    }

    if (session.status === 'closed') {
        redirect(`/survey/${session.id}?userId=${currentUserId}`)
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const myParticipant = session.participants.find((p: any) => p.userId === currentUserId)
    const me = myParticipant?.user
    const myTeam = myParticipant?.team

    if (!me) {
        return (
            <div className="p-8 text-center text-red-600 font-bold">You are not a participant in this session.</div>
        )
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const otherParticipants = session.participants.filter((p: any) => p.userId !== currentUserId)

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-4xl mx-auto space-y-6">

                <header className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">GLOBAL EXCHANGE: {session.scenario.name}</h1>
                        <p className="text-gray-500 text-sm">You are logged in as <span className="font-semibold">{me.name}</span></p>
                    </div>
                    <div className="text-right">
                        <span className={`px-3 py-1 text-sm font-semibold rounded-full 
                  ${session.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                            Session {session.status.toUpperCase()}
                        </span>
                    </div>
                </header>

                {session.status === 'draft' ? (
                    <div className="bg-white p-12 text-center rounded-xl shadow-sm border border-gray-100 max-w-2xl mx-auto">
                        <h2 className="text-2xl font-black text-gray-800 tracking-tight">GLOBAL EXCHANGE</h2>
                        <div className="mt-8 mb-8 space-y-4">
                            <p className="text-gray-500 text-lg">Waiting for HR to start the session.</p>
                            <p className="text-sm font-medium text-gray-600 border p-3 bg-gray-50 rounded inline-block">
                                Players joined: {session.participants.length}
                            </p>
                        </div>

                        <div className="p-6 bg-indigo-50 border border-indigo-100 rounded-lg text-left">
                            <h3 className="font-bold text-indigo-900 mb-2">Your Team</h3>
                            <p className="text-indigo-800 text-lg">Assigned at start</p>
                            <p className="text-sm text-indigo-600 mt-2">Teams (Alpha, Beta, Gamma, Delta, Epsilon) will be allocated automatically when the simulation begins.</p>
                        </div>

                        <div className="mt-8 flex justify-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                        </div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                        {/* Left Column: Resources & Production */}
                        <div className="md:col-span-1 flex flex-col space-y-6">
                            {/* Resources / Me view */}
                            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
                                {myTeam ? (
                                    <div className="w-full">
                                        <div className="w-full bg-slate-900 text-white rounded-t-lg p-3 font-black tracking-widest uppercase border-b-4 border-slate-700">
                                            {myTeam.name}
                                        </div>
                                        <div className="bg-slate-50 border-x border-b border-slate-200 rounded-b-lg p-4 space-y-3 shadow-inner">
                                            <div className="flex justify-between items-center p-2 bg-white rounded border shadow-sm">
                                                <span className="font-medium text-green-800">Capital</span>
                                                <span className="font-bold text-green-600">${myTeam.capital.toLocaleString()}</span>
                                            </div>
                                            <div className="flex justify-between items-center p-2 bg-white rounded border shadow-sm">
                                                <span className="font-medium text-amber-800">Raw Material</span>
                                                <span className="font-bold text-amber-600">{myTeam.rawMaterial}</span>
                                            </div>
                                            <div className="flex justify-between items-center p-2 bg-white rounded border shadow-sm">
                                                <span className="font-medium text-blue-800">Tech Level</span>
                                                <span className="font-bold text-blue-600">{myTeam.techLevel}</span>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <p className="text-red-500">Error: Team assignment failed.</p>
                                )}
                            </div>

                            {/* Production Panel */}
                            {myTeam && <ProductionPanel sessionId={session.id} myTeam={myTeam} />}
                        </div>

                        {/* Right Column: Interaction view */}
                        <div className="md:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-fit">
                            <h3 className="font-bold text-lg border-b pb-2 mb-4">Initiate Trade</h3>
                            <TradeActionForm
                                sessionId={session.id}
                                currentUserId={currentUserId}
                                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                otherParticipants={otherParticipants.map((p: any) => p.user)}
                            />
                        </div>

                    </div>
                )}
            </div>
        </div>
    )
}
