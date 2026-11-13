'use client'

import { useState } from 'react'
import useSWR from 'swr'
import Link from 'next/link'
import { getSessionDetails } from '@/modules/session/actions'
import TeamLedgerHUD from '@/components/team/TeamLedgerHUD'
import P2PTradeCenter from '@/components/team/P2PTradeCenter'
import BankCommodityBoard from '@/components/team/BankCommodityBoard'

const fetcher = async (sessionId: string) => {
  return await getSessionDetails(sessionId)
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
  const { data: session } = useSWR(sessionId, fetcher, {
    fallbackData: initialSessionData,
    refreshInterval: 2500,
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
        <div className="text-sm font-mono text-slate-500">Munkaállomás betöltése...</div>
      </div>
    )
  }

  const myTeam = teams.find((t: any) => t.id === selectedTeamId) || teams[0]
  const activeEvent = session.marketEvents?.find((e: any) => e.isActive)

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans pb-16">
      {/* Top Station Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            <div>
              <span className="text-[10px] font-mono uppercase font-bold text-slate-400 block">
                Asztali Munkaállomás · {session.name}
              </span>
              <div className="text-xs font-bold text-slate-800">
                Terem PIN: <span className="font-mono text-blue-600 font-black">{session.joinCode}</span>
              </div>
            </div>
          </div>

          {/* Quick Team Switcher for Tablet Station Setup */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Asztal Vállalata:</span>
            <select
              value={myTeam?.id}
              onChange={(e) => setSelectedTeamId(e.target.value)}
              className="text-xs font-bold px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              {teams.map((t: any) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.profileCode})
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      {/* Main Tablet Layout */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6">
        {/* S-TEAM-01: Team Ledger HUD */}
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

        {/* Tab Switcher for smaller screens / Side-by-side on desktop */}
        <div className="flex sm:hidden border-b border-slate-200 gap-4">
          <button
            onClick={() => setActiveTab('trade')}
            className={`py-2 text-xs font-bold border-b-2 ${
              activeTab === 'trade' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500'
            }`}
          >
            P2P Kereskedelem
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

        {/* Desktop 2-Column Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (7 cols): S-TEAM-02 P2P Trade Center */}
          <div className={`lg:col-span-7 ${activeTab === 'bank' ? 'hidden sm:block' : ''}`}>
            {myTeam && (
              <P2PTradeCenter
                sessionId={session.id}
                myTeam={myTeam}
                allTeams={teams}
                trades={session.tradeTransactions || []}
              />
            )}
          </div>

          {/* Right Column (5 cols): S-TEAM-03 Bank Commodity Board */}
          <div className={`lg:col-span-5 ${activeTab === 'trade' ? 'hidden sm:block' : ''}`}>
            <BankCommodityBoard activeEvent={activeEvent || null} />
          </div>
        </div>
      </main>
    </div>
  )
}
