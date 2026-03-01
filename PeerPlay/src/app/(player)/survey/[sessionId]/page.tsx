export const dynamic = 'force-dynamic'

import { getSessionDetails } from '@/modules/session/actions'
import { hasCompletedSurvey } from '@/modules/survey/actions'
import { notFound } from 'next/navigation'
import SurveyForm from '@/components/SurveyForm'

export default async function SurveyPage({
    params,
    searchParams
}: {
    params: Promise<{ sessionId: string }>
    searchParams: Promise<{ userId: string }>
}) {
    const { sessionId } = await params;
    const { userId } = await searchParams;
    const session = await getSessionDetails(sessionId)
    if (!session) notFound()

    const currentUserId = userId

    if (!currentUserId) {
        return (
            <div className="p-8 text-center text-red-600 font-bold">Error: Missing User ID</div>
        )
    }

    // Session must be closed for Survey
    if (session.status !== 'closed') {
        return (
            <div className="p-8 text-center text-gray-500">
                <h2 className="text-xl font-bold bg-yellow-100 text-yellow-800 p-4 rounded-xl mb-4">Survey Not Ready</h2>
                <p>You can only fill out the survey when the HR closes the session.</p>
            </div>
        )
    }

    const me = session.participants.find(p => p.userId === currentUserId)?.user
    if (!me) {
        return (
            <div className="p-8 text-center text-red-600 font-bold">You are not a participant in this session.</div>
        )
    }

    const alreadySubmitted = await hasCompletedSurvey(session.id, currentUserId)
    if (alreadySubmitted) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
                <div className="bg-white p-12 text-center rounded-xl shadow-md max-w-lg w-full">
                    <h2 className="text-2xl font-bold text-green-600 mb-2">Survey Completed</h2>
                    <p className="text-gray-600">You have already submitted your feedback for this session. You may now safely close this window.</p>
                </div>
            </div>
        )
    }

    const otherParticipants = session.participants.filter(p => p.userId !== currentUserId)

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-6">
            <div className="max-w-xl mx-auto space-y-8">

                <header className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">End of Session Evaluation</h1>
                    <p className="text-gray-500 text-sm">
                        Please rate how much you relied on the information, resources, or influence of the following participants during the <span className="font-semibold text-gray-700">{session.scenario.name}</span> session.
                    </p>
                </header>

                <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
                    <SurveyForm
                        sessionId={session.id}
                        currentUserId={currentUserId}
                        otherParticipants={otherParticipants.map(p => p.user)}
                    />
                </div>

            </div>
        </div>
    )
}
