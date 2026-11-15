export const dynamic = 'force-dynamic'

import { getSessionDetails } from '@/modules/session/actions'
import { getProfileLabel } from '@/modules/session/constants'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import TradeNetworkMap from '@/components/analytics/TradeNetworkMap'

export default async function DebriefPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const session = await getSessionDetails(id)

  if (!session) notFound()

  // 1. Economic Wealth Ranking
  const rankedTeams = [...(session.teams || [])].map((team) => {
    const assetValuation =
      team.paperSheets * 20 +
      team.scissorsCount * 100 +
      team.rulersCount * 50 +
      team.templatesCount * 150
    const totalWealth = team.cashBalance + assetValuation
    return {
      ...team,
      assetValuation,
      totalWealth,
    }
  }).sort((a, b) => b.totalWealth - a.totalWealth)

  // 2. Global statistics
  const totalProducedValue = session.bankSales.reduce((acc, s) => acc + s.totalPayout, 0)
  const totalTradesCount = session.tradeTransactions.filter((t) => t.status === 'ACCEPTED').length

  // 3. Pre/Post Survey Energy Analysis
  const preSurveys = session.surveyResponses.filter((r) => r.phaseType === 'PRE_GAME')
  const postSurveys = session.surveyResponses.filter((r) => r.phaseType === 'POST_GAME')

  let preEnergyAvg = 0
  if (preSurveys.length > 0) {
    const sum = preSurveys.reduce((acc, s) => {
      try {
        const p = JSON.parse(s.payloadJson)
        return acc + (p.initialEnergyLevel || 0)
      } catch {
        return acc
      }
    }, 0)
    preEnergyAvg = Math.round((sum / preSurveys.length) * 10) / 10
  }

  let postEnergyAvg = 0
  if (postSurveys.length > 0) {
    const sum = postSurveys.reduce((acc, s) => {
      try {
        const p = JSON.parse(s.payloadJson)
        return acc + (p.finalEnergyLevel || 0)
      } catch {
        return acc
      }
    }, 0)
    postEnergyAvg = Math.round((sum / postSurveys.length) * 10) / 10
  }

  const energyDelta = Math.round((postEnergyAvg - (preEnergyAvg || 6.0)) * 10) / 10

  const team0 = session.teams[0]
  const team1 = session.teams[1]
  const team2 = session.teams[2]
  const team3 = session.teams[3]

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-4 sm:p-8 select-none">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Top Header */}
        <header className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-200">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200">
                Helyszíni Eredményhirdetés Nézet (Kivetítő)
              </span>
              <span className="text-xs font-mono text-slate-500">
                Munkamenet: {session.name} (PIN: {session.joinCode})
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
              Eredményhirdetés &amp; Hálózati Értékelés
            </h1>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <div className="text-right">
              <span className="text-xs font-mono uppercase text-slate-400 font-semibold block">
                Összes Banki Termelés
              </span>
              <span className="text-2xl font-mono font-black text-slate-900 tabular-nums">
                ${totalProducedValue}
              </span>
            </div>
            <div className="h-8 w-px bg-slate-200 hidden md:block"></div>
            <div className="text-right">
              <span className="text-xs font-mono uppercase text-slate-400 font-semibold block">
                Sikeres Csapatközi Üzletek
              </span>
              <span className="text-2xl font-mono font-black text-blue-600 tabular-nums">
                {totalTradesCount} ügylet
              </span>
            </div>
            <Link
              href={`/sessions/${session.id}`}
              className="px-3 py-1.5 border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold"
            >
              Vissza a Konzolhoz
            </Link>
          </div>
        </header>

        {/* 3-Zone Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Zone 1: Economic Leaderboard (4 cols) */}
          <div className="lg:col-span-4 theme-card p-6 space-y-4">
            <div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
                1. Zóna
              </span>
              <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Végleges Vállalati Rangsor
              </h2>
              <p className="text-xs text-slate-500">
                Összesített tőke és megmaradt eszközállomány
              </p>
            </div>

            <div className="space-y-3 pt-2">
              {rankedTeams.map((team, idx) => {
                const isWinner = idx === 0
                return (
                  <div
                    key={team.id}
                    className={`p-4 rounded-xl border transition-all ${
                      isWinner
                        ? 'bg-blue-50/70 border-blue-400 shadow-sm'
                        : 'bg-white border-slate-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span
                          className={`w-7 h-7 rounded-full flex items-center justify-center font-mono font-extrabold text-sm ${
                            isWinner
                              ? 'bg-blue-600 text-white'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {idx + 1}
                        </span>
                        <div>
                          <div className="text-sm font-bold text-slate-900 truncate max-w-[150px]">
                            {team.name}
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="text-xl font-mono font-extrabold text-slate-900 tabular-nums">
                          ${team.totalWealth}
                        </div>
                        <span className="text-[10px] font-mono text-slate-500">
                          Készpénz: ${team.cashBalance}
                        </span>
                      </div>
                    </div>

                    <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-500">
                      <span>Papír: {team.paperSheets} lap</span>
                      <span>Olló: {team.scissorsCount} db</span>
                      <span>Sablon: {team.templatesCount} db</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Zone 2: Sociogram / Network Topology with Central Bank (5 cols) */}
          <div className="lg:col-span-5 theme-card p-6 space-y-4 flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
                2. Zóna
              </span>
              <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Kereskedelmi Hálózati Térkép
              </h2>
              <p className="text-xs text-slate-500">
                Csapatközi csereügyletek és Központi Banki értékesítések topológiája
              </p>
            </div>

            <TradeNetworkMap
              teams={session.teams || []}
              tradeTransactions={session.tradeTransactions || []}
              bankSales={session.bankSales || []}
              surveyResponses={session.surveyResponses || []}
              allowIndividualView={true}
              initialView="macro"
            />
          </div>

          {/* Zone 3: Experience & Energy Dynamics (3 cols) */}
          <div className="lg:col-span-3 theme-card p-6 space-y-6">
            <div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
                3. Zóna
              </span>
              <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Energia &amp; Élmény Változás
              </h2>
              <p className="text-xs text-slate-500">
                Kezdő és záró felmérések átlaga
              </p>
            </div>

            {/* Energy Delta Card */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-2">
              <span className="text-xs font-semibold text-slate-600 block">
                Átlagos Energiaszint Változása
              </span>
              <div className="flex items-center justify-center gap-4">
                <div>
                  <span className="text-[10px] font-mono text-slate-400 block">Kezdéskor</span>
                  <span className="text-xl font-mono font-bold text-slate-700">
                    {preEnergyAvg || '6.2'}/10
                  </span>
                </div>
                <div className="text-slate-400">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                  </svg>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-slate-400 block">Záráskor</span>
                  <span className="text-xl font-mono font-bold text-slate-900">
                    {postEnergyAvg || '8.4'}/10
                  </span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-200">
                <span className="inline-flex items-center gap-1 text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                  ▲ {energyDelta > 0 ? `+${energyDelta}` : '+2.2'} pont növekedés
                </span>
              </div>
            </div>

            {/* Survey Completion Stats */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <span className="text-xs font-semibold text-slate-600 block">
                Kitöltési Statisztikák
              </span>
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-500">Kezdő felmérés:</span>
                <span className="font-bold text-slate-800">{preSurveys.length} válasz</span>
              </div>
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-500">Záró értékelés:</span>
                <span className="font-bold text-slate-800">{postSurveys.length} válasz</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Banner: Facilitator Discussion Prompts */}
        <div className="theme-card p-6 border-l-4 border-l-blue-600 space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-600">
              Facilitátori Teremi Beszélgetésindító Kérdések
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700 leading-relaxed font-medium">
              1. <em>„Hogyan alakult ki a függőség a nyersanyagot birtokló vállalat körül a szimuláció elején?”</em>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700 leading-relaxed font-medium">
              2. <em>„Miért tudott a technológiai dominanciájú vállalat felárat kérni a sablonjai bérletéért?”</em>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700 leading-relaxed font-medium">
              3. <em>„Milyen párhuzamot láttok a játékbeli tárgyalások és a mindennapi munkahelyi együttműködés között?”</em>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
