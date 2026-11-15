'use client'

import { useState } from 'react'
import useSWR from 'swr'
import Link from 'next/link'
import PhaseControlHeroTimer from '@/components/facilitator/PhaseControlHeroTimer'
import BankIntakeDesk from '@/components/facilitator/BankIntakeDesk'
import MarketEventsDispatcher from '@/components/facilitator/MarketEventsDispatcher'
import LiveLeaderboard from '@/components/facilitator/LiveLeaderboard'

const fetcher = async (id: string) => {
  const res = await fetch(`/api/session/${encodeURIComponent(id)}?t=${Date.now()}`, {
    cache: 'no-store',
  })
  if (!res.ok) throw new Error('Failed to fetch session')
  return await res.json()
}

export default function SessionDetailClient({ initialSessionData }: { initialSessionData: any }) {
  const { data: session, mutate } = useSWR(initialSessionData.id, fetcher, {
    fallbackData: initialSessionData,
    refreshInterval: 2000,
    dedupingInterval: 1000,
    revalidateOnFocus: true,
  })

  const [activeTab, setActiveTab] = useState<'overview' | 'bank' | 'market' | 'leaderboard'>('overview')

  if (!session) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-sm font-mono text-slate-500">Betöltés...</div>
      </div>
    )
  }

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
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans pb-12">
      {/* Compact, Wrap-Friendly Header Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-2.5">
          <div className="flex items-center gap-2.5 min-w-0">
            <Link
              href="/dashboard"
              className="text-slate-400 hover:text-slate-700 transition p-1 rounded hover:bg-slate-100 shrink-0"
              title="Vissza"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
            </Link>
            <h1 className="text-base sm:text-lg font-extrabold text-slate-900 tracking-tight truncate">
              {session.name || 'Kereskedelmi Szimuláció'}
            </h1>
            <span className="font-mono font-black text-xs sm:text-sm bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded shrink-0">
              PIN: {session.joinCode}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={`/play/${session.id}`}
              target="_blank"
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition shadow-2xs"
            >
              Csapatpult →
            </Link>
            <Link
              href={`/sessions/${session.id}/debrief`}
              target="_blank"
              className="px-3 py-1.5 border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-bold transition"
            >
              Eredmények
            </Link>
          </div>
        </div>

        {/* Wrap-Friendly Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-3 sm:px-6 flex flex-wrap gap-1 border-t border-slate-100">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-3 text-xs font-bold border-b-2 transition cursor-pointer ${
              activeTab === 'overview'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Vezérlő &amp; Időzítő
          </button>
          <button
            onClick={() => setActiveTab('bank')}
            className={`py-2 px-3 text-xs font-bold border-b-2 transition cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'bank'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Bank Pult</span>
            {session.bankSales?.length > 0 && (
              <span className="font-mono text-[10px] bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded-full">
                {session.bankSales.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('market')}
            className={`py-2 px-3 text-xs font-bold border-b-2 transition cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'market'
                ? 'border-amber-600 text-amber-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Piaci Események</span>
            {activeEvent && activeEvent.isActive && (
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('leaderboard')}
            className={`py-2 px-3 text-xs font-bold border-b-2 transition cursor-pointer ${
              activeTab === 'leaderboard'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Rangsor
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-3 sm:px-6 mt-4">
        {activeTab === 'overview' && (
          <div className="space-y-5">
            <PhaseControlHeroTimer
              sessionId={session.id}
              currentPhase={session.currentPhase}
              phaseStartedAt={session.phaseStartedAt}
              phaseDurationSeconds={session.phaseDurationSeconds}
              isTimerPaused={session.isTimerPaused}
              timerRemainingSeconds={session.timerRemainingSeconds}
              computedRemainingSeconds={session.computedRemainingSeconds}
              onMutate={() => mutate()}
            />
            <LiveLeaderboard teams={session.teams || []} />
          </div>
        )}

        {activeTab === 'bank' && (
          <BankIntakeDesk
            sessionId={session.id}
            teams={session.teams || []}
            activeMultipliers={activeMultipliers}
            recentSales={session.bankSales || []}
            onMutate={() => mutate()}
          />
        )}

        {activeTab === 'market' && (
          <MarketEventsDispatcher
            sessionId={session.id}
            activeEvent={activeEvent || null}
            onMutate={() => mutate()}
          />
        )}

        {activeTab === 'leaderboard' && (
          <LiveLeaderboard teams={session.teams || []} />
        )}
      </main>
    </div>
  )
}
