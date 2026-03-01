export const dynamic = 'force-dynamic'

import { getSessionDetails } from '@/modules/session/actions'
import { notFound } from 'next/navigation'
import PlaySessionClient from './PlaySessionClient'

export default async function PlaySessionPage({
    params,
    searchParams
}: {
    params: Promise<{ sessionId: string }>
    searchParams: Promise<{ userId: string }>
}) {
    const { sessionId } = await params;
    const { userId } = await searchParams;
    const initialSessionData = await getSessionDetails(sessionId)
    if (!initialSessionData) notFound()

    return (
        <PlaySessionClient
            sessionId={sessionId}
            initialUserId={userId}
            initialSessionData={initialSessionData as any}
        />
    )
}
