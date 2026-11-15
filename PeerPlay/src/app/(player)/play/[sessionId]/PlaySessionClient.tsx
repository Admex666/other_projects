'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { getProfileLabel } from '@/modules/session/constants'
import TeamLedgerHUD from '@/components/team/TeamLedgerHUD'
import P2PTradeCenter from '@/components/team/P2PTradeCenter'
import BankCommodityBoard from '@/components/team/BankCommodityBoard'

const fetcher = async (sessionId: string) => {
  const res = await fetch(`/api/session/${encodeURIComponent(sessionId)}?t=${Date.now()}`, {
    cache: 'no-store',
  })
  if (!res.ok) throw new Error('Failed to fetch session')
  return await res.json()
}

export default function PlaySessionClient({
  sessionId,
  initialTeamId,
  initialSessionData,
}: {
  sessionId: string
  initialTeamId?: string
  initialSessionData: any
}) {
  const { data: session, mutate } = useSWR(sessionId, fetcher, {
    fallbackData: initialSessionData,
    refreshInterval: 2000,
    dedupingInterval: 1000,
    revalidateOnFocus: true,
  })

  const teams = session?.teams || []
  const [selectedTeamId, setSelectedTeamId] = useState<string>(
    initialTeamId || teams[0]?.id || ''
  )
  const [activeTab, setActiveTab] = useState<'trade' | 'bank'>('trade')

  if (!session) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-sm font-mono text-slate-500">Betöltés...</div>
      </div>
    )
  }

  const myTeam = teams.find((t: any) => t.id === selectedTeamId) || teams[0]
  const activeEvent = session.marketEvents?.find((e: any) => e.isActive)

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans pb-12">
      {/* Top Station Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="text-xs font-bold text-slate-800">
              {session.name} · PIN: <span className="font-mono text-blue-600 font-black">{session.joinCode}</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Csapat:</span>
            <select
              value={myTeam?.id}
              onChange={(e) => setSelectedTeamId(e.target.value)}
              className="text-xs font-bold px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              {teams.map((t: any) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      {/* Main Tablet Layout */}
      <main className="max-w-7xl mx-auto px-3 sm:px-6 mt-4 space-y-5">
        {myTeam && (
          <TeamLedgerHUD
            teamName={myTeam.name}
            profileCode={myTeam.profileCode}
            cashBalance={myTeam.cashBalance}
            paperSheets={myTeam.paperSheets}
            scissorsCount={myTeam.scissorsCount}
            rulersCount={myTeam.rulersCount}
            templatesCount={myTeam.templatesCount}
            currentPhase={session.currentPhase}
            phaseStartedAt={session.phaseStartedAt}
            phaseDurationSeconds={session.phaseDurationSeconds}
            isTimerPaused={session.isTimerPaused}
            timerRemainingSeconds={session.timerRemainingSeconds}
          />
        )}

        {/* Tab Switcher for smaller screens */}
        <div className="flex sm:hidden border-b border-slate-200 gap-4">
          <button
            onClick={() => setActiveTab('trade')}
            className={`py-2 text-xs font-bold border-b-2 ${
              activeTab === 'trade' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'
            }`}
          >
            Cserekereskedelem
          </button>
          <button
            onClick={() => setActiveTab('bank')}
            className={`py-2 text-xs font-bold border-b-2 ${
              activeTab === 'bank' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'
            }`}
          >
            Banki Árfolyamok
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className={`lg:col-span-7 ${activeTab === 'bank' ? 'hidden sm:block' : ''}`}>
            {myTeam && (
              <P2PTradeCenter
                sessionId={session.id}
                myTeam={myTeam}
                allTeams={teams}
                trades={session.tradeTransactions || []}
                onMutate={() => mutate()}
              />
            )}
          </div>

          <div className={`lg:col-span-5 ${activeTab === 'trade' ? 'hidden sm:block' : ''}`}>
            <BankCommodityBoard activeEvent={activeEvent || null} />
          </div>
        </div>
      </main>
    </div>
  )
}
