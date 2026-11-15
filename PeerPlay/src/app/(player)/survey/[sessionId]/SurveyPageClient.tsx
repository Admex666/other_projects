'use client'

import { useState, useEffect } from 'react'
import useSWR from 'swr'
import { getPhaseLabel } from '@/modules/session/constants'
import PreGamePulseForm from '@/components/mobile/PreGamePulseForm'
import MobileCompanionHUD from '@/components/mobile/MobileCompanionHUD'
import PostGamePeerFeedbackForm from '@/components/mobile/PostGamePeerFeedbackForm'

const fetcher = async (sessionId: string) => {
  const res = await fetch(`/api/session/${encodeURIComponent(sessionId)}?t=${Date.now()}`, {
    cache: 'no-store',
  })
  if (!res.ok) throw new Error('Failed to fetch session')
  return await res.json()
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
  const { data: session, mutate } = useSWR(sessionId, fetcher, {
    fallbackData: initialSessionData,
    refreshInterval: 2000,
    dedupingInterval: 1000,
    revalidateOnFocus: true,
    revalidateOnMount: true,
  })

  const [currentUserId, setCurrentUserId] = useState<string>(initialUserId || '')
  const [hasPreGame, setHasPreGame] = useState(initialPreGameSubmitted)
  const [hasPostGame, setHasPostGame] = useState(initialPostGameSubmitted)

  // Recover userId from localStorage if missing in URL query params
  useEffect(() => {
    const storageKey = `peerplay_userId_${sessionId}`
    if (initialUserId) {
      localStorage.setItem(storageKey, initialUserId)
      setCurrentUserId(initialUserId)
    } else {
      const stored = localStorage.getItem(storageKey)
      if (stored) {
        setCurrentUserId(stored)
        try {
          const url = new URL(window.location.href)
          if (!url.searchParams.get('userId')) {
            url.searchParams.set('userId', stored)
            window.history.replaceState({}, '', url.toString())
          }
        } catch {}
      }
    }
  }, [sessionId, initialUserId])

  // Explicit 2s interval poller for guaranteed Zero Manual Reload
  useEffect(() => {
    const timer = setInterval(() => {
      mutate()
    }, 2000)
    return () => clearInterval(timer)
  }, [mutate])

  // Mark window as hydrated so pre-hydration script knows SWR is active
  useEffect(() => {
    ;(window as any).__PEERPLAY_HYDRATED = true
  }, [])

  if (!session) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center font-sans">
        <div className="text-xs font-mono text-slate-500">Betöltés...</div>
      </div>
    )
  }

  // Also check live surveyResponses from session data
  const effectiveUserId = currentUserId || initialUserId || ''
  const serverPreSubmitted = Boolean(
    effectiveUserId &&
      session.surveyResponses?.some(
        (r: any) =>
          (r.userId === effectiveUserId || r.respondentUserId === effectiveUserId) &&
          r.phaseType === 'PRE_GAME'
      )
  )
  const serverPostSubmitted = Boolean(
    effectiveUserId &&
      session.surveyResponses?.some(
        (r: any) =>
          (r.userId === effectiveUserId || r.respondentUserId === effectiveUserId) &&
          r.phaseType === 'POST_GAME'
      )
  )

  const effectiveHasPreGame = hasPreGame || serverPreSubmitted
  const effectiveHasPostGame = hasPostGame || serverPostSubmitted

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
      if (
        (effectiveUserId && (p.user?.id === effectiveUserId || p.userId === effectiveUserId))
      ) {
        participant = p
        userTeam = t
      }
    })
  })

  if (!userTeam) {
    userTeam = session.teams?.[0]
  }

  const phase = session.currentPhase || 'PHASE_0_SETUP'
  const isPreSurveyPhase = phase === 'PHASE_0_SETUP' || phase === 'PHASE_1_PRE_SURVEY'
  const isPostSurveyPhase = phase === 'PHASE_10_POST_SURVEY'
  const isDebriefPhase = phase === 'PHASE_11_DEBRIEF' || phase === 'POST_WORKPLACE_ONA'

  const activeEvent = session.marketEvents?.find((e: any) => e.isActive)
  let activeMultipliers: Record<string, number> = {}
  if (activeEvent?.priceMultipliers) {
    try {
      activeMultipliers = JSON.parse(activeEvent.priceMultipliers)
    } catch {}
  }

  const defaultTeam = userTeam || {
    id: '',
    name: 'Alfa Vállalat',
    profileCode: 'CAPITAL',
    cashBalance: 0,
    paperSheets: 0,
    scissorsCount: 0,
    rulersCount: 0,
    templatesCount: 0,
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-3 sm:p-5 flex flex-col justify-between">
      <div className="max-w-[460px] w-full mx-auto space-y-3">
        {/* Top Header */}
        <header className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-slate-200">
          <div className="text-xs font-bold text-slate-800">
            {participant ? participant.user?.name : 'Mobil Kísérő'}
          </div>
          <div className="flex items-center gap-1.5">
            <span
              id="live-phase-badge"
              className="text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200"
            >
              {getPhaseLabel(phase)}
            </span>
            <span className="font-mono text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              PIN: {session.joinCode}
            </span>
          </div>
        </header>

        {/* View Selection Based on Phase & State */}
        <div className="theme-card p-4 sm:p-5">
          {isDebriefPhase || (isPostSurveyPhase && effectiveHasPostGame) ? (
            <div className="text-center py-6 space-y-2">
              <span className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 inline-flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </span>
              <div className="text-xs font-bold uppercase text-blue-600">
                {getPhaseLabel(phase)}
              </div>
              <h3 className="text-base font-bold text-slate-900">
                {effectiveHasPostGame
                  ? 'Visszajelzésedet Rögzítettük!'
                  : 'Eredményhirdetés Folyamatban'}
              </h3>
              <p className="text-xs text-slate-500">
                Köszönjük a részvételt! Kövesd a központi kivetítőt az eredményekért.
              </p>
            </div>
          ) : isPostSurveyPhase ? (
            <PostGamePeerFeedbackForm
              sessionId={session.id}
              userId={effectiveUserId}
              myTeamId={defaultTeam.id}
              allParticipants={allParticipantsList}
              onSubmitted={() => {
                setHasPostGame(true)
                mutate()
              }}
            />
          ) : isPreSurveyPhase && !effectiveHasPreGame ? (
            <PreGamePulseForm
              sessionId={session.id}
              userId={effectiveUserId}
              onSubmitted={() => {
                setHasPreGame(true)
                mutate()
              }}
            />
          ) : (
            <MobileCompanionHUD
              sessionId={session.id}
              userId={effectiveUserId}
              userName={participant?.user?.name || 'Játékos'}
              myTeam={defaultTeam}
              allTeams={session.teams || []}
              trades={session.tradeTransactions || []}
              bankSales={session.bankSales || []}
              currentPhase={phase}
              activeEventTitle={activeEvent?.title}
              activeEventDescription={activeEvent?.description}
              activeMultipliers={activeMultipliers}
              onMutate={() => mutate()}
            />
          )}
        </div>
      </div>

      {/* Pre-hydration fallback poller so mobile always reloads if phase changes before JS finishes hydrating */}
      <script
        dangerouslySetInnerHTML={{
          __html: `
(function(){
  var sid = ${JSON.stringify(session.id)};
  var initialPhase = ${JSON.stringify(phase)};
  setInterval(function(){
    if (window.__PEERPLAY_HYDRATED) return;
    fetch('/api/session/' + encodeURIComponent(sid) + '?t=' + Date.now(), { cache: 'no-store' })
      .then(function(r){ return r.json(); })
      .then(function(d){
        if (d && d.currentPhase && d.currentPhase !== initialPhase) {
          window.location.reload();
        }
      })
      .catch(function(){});
  }, 2000);
})();
          `,
        }}
      />
    </div>
  )
}
