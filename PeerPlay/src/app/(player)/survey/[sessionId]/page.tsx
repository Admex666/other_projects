export const dynamic = 'force-dynamic'

import { getSessionDetails } from '@/modules/session/actions'
import { hasCompletedSurvey } from '@/modules/survey/actions'
import { notFound } from 'next/navigation'
import SurveyPageClient from './SurveyPageClient'

export default async function SurveyPage({
  params,
  searchParams,
}: {
  params: Promise<{ sessionId: string }>
  searchParams: Promise<{ userId?: string }>
}) {
  const { sessionId } = await params
  const { userId } = await searchParams

  const session = await getSessionDetails(sessionId)
  if (!session) notFound()

  let hasPreGame = false
  let hasPostGame = false

  if (userId) {
    hasPreGame = await hasCompletedSurvey(session.id, userId, 'PRE_GAME')
    hasPostGame = await hasCompletedSurvey(session.id, userId, 'POST_GAME')
  }

  return (
    <SurveyPageClient
      sessionId={session.id}
      initialUserId={userId}
      initialSessionData={session as any}
      hasPreGameSubmitted={hasPreGame}
      hasPostGameSubmitted={hasPostGame}
    />
  )
}
