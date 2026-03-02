export const dynamic = 'force-dynamic'

import { getSessionDetails } from '@/modules/session/actions'
import { notFound } from 'next/navigation'
import SessionDetailClient from './SessionDetailClient'

export default async function SessionDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    const session = await getSessionDetails(id)

    if (!session) {
        notFound()
    }

    return <SessionDetailClient initialSessionData={session as any} />
}
