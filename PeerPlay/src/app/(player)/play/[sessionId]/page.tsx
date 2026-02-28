export const dynamic = 'force-dynamic'

import { getSessionDetails } from '@/modules/session/actions'
import { notFound, redirect } from 'next/navigation'
import TradeActionForm from '@/components/TradeActionForm'

export default async function PlaySessionPage({
    params,
    searchParams
}: {
    params: { sessionId: string }
    searchParams: { userId: string } // In MVP, we identify the player via URL query `?userId=...`
}) {
    const session = await getSessionDetails(params.sessionId)
    if (!session) notFound()

    // MVP Authentication strategy (URL-based identification)
    const currentUserId = searchParams.userId

    if (!currentUserId) {
        return (
            <div className="p-8 text-center">
                <h1 className="text-xl font-bold text-red-600">Error: Missing User ID</h1>
                <p>Please join the session through the Join page to get a valid link.</p>
            </div>
        )
    }

    // Check if session is closed -> Redirect to survey
    if (session.status === 'closed') {
        redirect(`/survey/${session.id}?userId=${currentUserId}`)
    }

    const me = session.participants.find(p => p.userId === currentUserId)?.user
    if (!me) {
        return (
            <div className="p-8 text-center text-red-600 font-bold">You are not a participant in this session.</div>
        )
    }

    const otherParticipants = session.participants.filter(p => p.userId !== currentUserId)

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-4xl mx-auto space-y-6">

                <header className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Playing: {session.scenario.name}</h1>
                        <p className="text-gray-500 text-sm">You are logged in as <span className="font-semibold">{me.name}</span> ({me.role} - {me.teamMembership})</p>
                    </div>
                    <div className="text-right">
                        <span className={`px-3 py-1 text-sm font-semibold rounded-full 
                  ${session.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                            Session {session.status.toUpperCase()}
                        </span>
                    </div>
                </header>

                {session.status === 'draft' ? (
                    <div className="bg-white p-12 text-center rounded-xl shadow-sm border border-gray-100">
                        <h2 className="text-xl font-semibold text-gray-700">Lobby</h2>
                        <p className="text-gray-500 mt-2">Waiting for HR to start the session. Please hold on...</p>
                        <div className="mt-6 flex justify-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                        </div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                        {/* Resources / Me view */}
                        <div className="md:col-span-1 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                            <h3 className="font-bold text-lg border-b pb-2 mb-4">My Resources</h3>
                            <p className="text-sm text-gray-500 mb-4">
                                (MVP: Resource tracking is simulated. You can trade unlimited assets for now.)
                            </p>
                            <div className="space-y-3">
                                <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                                    <span className="font-medium text-blue-900">Tech Points</span>
                                    <span className="font-bold text-blue-700">∞</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                                    <span className="font-medium text-green-900">Cash</span>
                                    <span className="font-bold text-green-700">∞</span>
                                </div>
                            </div>
                        </div>

                        {/* Interaction view */}
                        <div className="md:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                            <h3 className="font-bold text-lg border-b pb-2 mb-4">Initiate Trade</h3>
                            <TradeActionForm
                                sessionId={session.id}
                                currentUserId={currentUserId}
                                otherParticipants={otherParticipants.map(p => p.user)}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
