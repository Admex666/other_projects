'use client'

import { useState } from 'react'
import useSWR from 'swr'
import Link from 'next/link'
import { getSessionDetails } from '@/modules/session/actions'
import PreGamePulseForm from '@/components/mobile/PreGamePulseForm'
import MobileCompanionHUD from '@/components/mobile/MobileCompanionHUD'
import PostGamePeerFeedbackForm from '@/components/mobile/PostGamePeerFeedbackForm'

const fetcher = async (sessionId: string) => {
  return await getSessionDetails(sessionId)
}

export default function SurveyPageClient({
  sessionId,
  initialUserId,
  initialSessionData,
  hasPreGameSubmitted: initialPreGameSubmitted = false,
  hasPostGameSubmitted: initialPostGameSubmitted = false,
}: {
  sessionId: string
  initialUserId?: string
  initialSessionData: any
  hasPreGameSubmitted?: boolean
  hasPostGameSubmitted?: boolean
}) {
  const { data: session } = useSWR(sessionId, fetcher, {
    fallbackData: initialSessionData,
    refreshInterval: 2500,
    revalidateOnFocus: true,
  })

  const [hasPreGame, setHasPreGame] = useState(initialPreGameSubmitted)
  const [hasPostGame, setHasPostGame] = useState(initialPostGameSubmitted)

  if (!session) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center font-sans">
        <div className="text-xs font-mono text-slate-500">Munkamenet betöltése...</div>
      </div>
    )
  }

  // Find user and participant
  let participant: any = null
  let userTeam: any = null
  const allParticipantsList: any[] = []

  session.teams?.forEach((t: any) => {
    t.participants?.forEach((p: any) => {
      allParticipantsList.push({
        id: p.user?.id,
        name: p.user?.name || 'Játékos',
        teamId: t.id,
        teamName: t.name,
      })
      if (p.user?.id === initialUserId || p.userId === initialUserId) {
        participant = p
        userTeam = t
      }
    })
  })

  // Fallback to first team if not found
  if (!userTeam) {
    userTeam = session.teams?.[0]
  }

  const phase = session.currentPhase || 'PHASE_0_SETUP'
  const isPostGamePhase = phase === 'PHASE_10_POST_SURVEY' || phase === 'PHASE_11_DEBRIEF'

  // Active market event
  const activeEvent = session.marketEvents?.find((e: any) => e.isActive)

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-4 sm:p-6 flex flex-col justify-between">
      <div className="max-w-[440px] w-full mx-auto space-y-4">
        {/* Top Header */}
        <header className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div>
            <span className="text-[10px] font-mono uppercase font-bold text-slate-400">
              The Trading Game · Mobil Kísérő
            </span>
            <div className="text-xs font-semibold text-slate-700">
              {participant ? `Belépve: ${participant.user?.name}` : 'Mobil Résztvevő'}
            </div>
          </div>
          <span className="font-mono text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
            PIN: {session.joinCode}
          </span>
        </header>

        {/* View Selection Based on Phase & State */}
        <div className="theme-card p-6">
          {/* Case 1: Post Game Phase */}
          {isPostGamePhase ? (
            hasPostGame ? (
              <div className="text-center py-8 space-y-3">
                <span className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 inline-flex items-center justify-center">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                </span>
                <h3 className="text-lg font-bold text-slate-900">
                  Visszajelzésedet Rögzítettük!
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed max-w-xs mx-auto">
                  Köszönjük az együttműködési értékelést! Most nézz fel a központi kivetítőre a végső eredmények és a hálózati debrief megtekintéséhez.
                </p>
              </div>
            ) : (
              <PostGamePeerFeedbackForm
                sessionId={session.id}
                userId={initialUserId || ''}
                myTeamId={userTeam?.id || ''}
                allParticipants={allParticipantsList}
                onSubmitted={() => setHasPostGame(true)}
              />
            )
          ) : /* Case 2: Pre-Game Pulse not yet submitted */
          !hasPreGame ? (
            <PreGamePulseForm
              sessionId={session.id}
              userId={initialUserId || ''}
              onSubmitted={() => setHasPreGame(true)}
            />
          ) : (
            /* Case 3: In-Game Passive Companion */
            <MobileCompanionHUD
              teamName={userTeam?.name || 'Vállalat'}
              profileCode={userTeam?.profileCode || 'CAPITAL'}
              currentPhase={phase}
              phaseStartedAt={session.phaseStartedAt}
              phaseDurationSeconds={session.phaseDurationSeconds}
              isTimerPaused={session.isTimerPaused}
              timerRemainingSeconds={session.timerRemainingSeconds}
              activeEventTitle={activeEvent?.title}
              activeEventDescription={activeEvent?.description}
            />
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="text-center text-[10px] text-slate-400 font-mono mt-8">
        PeerPlay Enterprise v2.0 · Stripe Enterprise Standard
      </footer>
    </div>
  )
}
