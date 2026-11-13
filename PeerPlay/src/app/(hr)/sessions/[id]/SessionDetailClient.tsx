'use client'

import { useState } from 'react'
import useSWR from 'swr'
import Link from 'next/link'
import { getSessionDetails } from '@/modules/session/actions'
import PhaseControlHeroTimer from '@/components/facilitator/PhaseControlHeroTimer'
import BankIntakeDesk from '@/components/facilitator/BankIntakeDesk'
import MarketEventsDispatcher from '@/components/facilitator/MarketEventsDispatcher'
import LiveLeaderboard from '@/components/facilitator/LiveLeaderboard'

const fetcher = async (id: string) => {
  return await getSessionDetails(id)
}

export default function SessionDetailClient({ initialSessionData }: { initialSessionData: any }) {
  const { data: session } = useSWR(initialSessionData.id, fetcher, {
    fallbackData: initialSessionData,
    refreshInterval: 2500,
    revalidateOnFocus: true,
  })

  const [activeTab, setActiveTab] = useState<'overview' | 'bank' | 'market' | 'leaderboard'>('overview')

  if (!session) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-sm font-mono text-slate-500">Munkamenet betöltése...</div>
      </div>
    )
  }

  // Active market event multiplier parsing
  const activeEvent = session.marketEvents?.find((e: any) => e.isActive)
  let activeMultipliers: Record<string, number> = {}
  if (activeEvent?.priceMultipliers) {
    try {
      activeMultipliers = JSON.parse(activeEvent.priceMultipliers)
    } catch (e) {
      console.warn('Error parsing multipliers:', e)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans pb-16">
      {/* Facilitator Top Header Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="text-slate-400 hover:text-slate-700 transition p-1 rounded hover:bg-slate-100"
              title="Vissza az áttekintőhöz"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                  Facilitátori Irányítópult
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  {session.organization?.name || 'Vállalat'}
                </span>
              </div>
              <h1 className="text-lg font-extrabold text-slate-900 tracking-tight">
                {session.name || 'The Trading Game Workshop'}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* PIN Code Badge */}
            <div className="flex items-center gap-2 bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-lg">
              <span className="text-[10px] font-mono text-slate-500 uppercase font-bold">Terem PIN:</span>
              <span className="font-mono font-black text-lg text-slate-900 tracking-widest">
                {session.joinCode}
              </span>
            </div>

            {/* Direct Projector Debrief Link */}
            <Link
              href={`/sessions/${session.id}/debrief`}
              target="_blank"
              className="px-3.5 py-1.5 border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow-2xs"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5" />
              </svg>
              <span>Debrief Kivetítő</span>
            </Link>

            {/* Direct Station Link */}
            <Link
              href={`/play/${session.id}`}
              target="_blank"
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition shadow-xs flex items-center gap-1"
            >
              <span>Csapat Munkaállomás</span>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-2 border-t border-slate-100">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2.5 px-4 text-xs font-bold border-b-2 transition cursor-pointer ${
              activeTab === 'overview'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Fázisvezérlő & Időzítő
          </button>
          <button
            onClick={() => setActiveTab('bank')}
            className={`py-2.5 px-4 text-xs font-bold border-b-2 transition cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'bank'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Központi Bank Pult</span>
            {session.bankSales?.length > 0 && (
              <span className="font-mono text-[10px] bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded-full">
                {session.bankSales.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('market')}
            className={`py-2.5 px-4 text-xs font-bold border-b-2 transition cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'market'
                ? 'border-amber-600 text-amber-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Piaci Események Dispatcher</span>
            {activeEvent && activeEvent.isActive && (
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('leaderboard')}
            className={`py-2.5 px-4 text-xs font-bold border-b-2 transition cursor-pointer ${
              activeTab === 'leaderboard'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Élő Vállalati Rangsor
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <PhaseControlHeroTimer
              sessionId={session.id}
              currentPhase={session.currentPhase}
              phaseStartedAt={session.phaseStartedAt}
              phaseDurationSeconds={session.phaseDurationSeconds}
              isTimerPaused={session.isTimerPaused}
              timerRemainingSeconds={session.timerRemainingSeconds}
            />

            {/* Quick Overview of the 4 Teams */}
            <LiveLeaderboard teams={session.teams || []} />
          </div>
        )}

        {activeTab === 'bank' && (
          <BankIntakeDesk
            sessionId={session.id}
            teams={session.teams || []}
            activeMultipliers={activeMultipliers}
            recentSales={session.bankSales || []}
          />
        )}

        {activeTab === 'market' && (
          <MarketEventsDispatcher
            sessionId={session.id}
            activeEvent={activeEvent || null}
          />
        )}

        {activeTab === 'leaderboard' && (
          <LiveLeaderboard teams={session.teams || []} />
        )}
      </main>
    </div>
  )
}
