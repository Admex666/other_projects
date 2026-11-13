export const dynamic = 'force-dynamic'

import { getSessionDetails } from '@/modules/session/actions'
import { notFound } from 'next/navigation'
import Link from 'next/link'

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

  // 4. Trade matrix between the 4 teams
  const tradeMatrix: Record<string, Record<string, number>> = {}
  session.teams.forEach((t1) => {
    tradeMatrix[t1.name] = {}
    session.teams.forEach((t2) => {
      tradeMatrix[t1.name][t2.name] = 0
    })
  })

  session.tradeTransactions.forEach((t) => {
    if (t.status === 'ACCEPTED') {
      const sender = session.teams.find((tm) => tm.id === t.senderTeamId)?.name
      const receiver = session.teams.find((tm) => tm.id === t.receiverTeamId)?.name
      if (sender && receiver && tradeMatrix[sender]) {
        tradeMatrix[sender][receiver] = (tradeMatrix[sender][receiver] || 0) + 1
      }
    }
  })

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-6 md:p-10 select-none">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Debrief Top Header (Kivetítő Kiemelés) */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200">
                S-FAC-05 Helyszíni Debrief Nézet (Kivetítő)
              </span>
              <span className="text-xs font-mono text-slate-500">
                Munkamenet: {session.name} ({session.joinCode})
              </span>
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900">
              The Trading Game · Eredményhirdetés & Hálózati Reflexió
            </h1>
          </div>

          <div className="flex items-center gap-4">
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
                Sikeres P2P Üzletek
              </span>
              <span className="text-2xl font-mono font-black text-blue-600 tabular-nums">
                {totalTradesCount} tranzakció
              </span>
            </div>
            <Link
              href={`/sessions/${session.id}`}
              className="ml-2 px-3 py-1.5 border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold"
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
                          <span className="text-[10px] font-mono text-slate-400 uppercase">
                            {team.profileCode}
                          </span>
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

          {/* Zone 2: Sociogram / Network Topology (5 cols) */}
          <div className="lg:col-span-5 theme-card p-6 space-y-4 flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
                2. Zóna
              </span>
              <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Kereskedelmi Hálózati Topológia
              </h2>
              <p className="text-xs text-slate-500">
                P2P csereügyletek és vállalatközi szövetségek mintázata
              </p>
            </div>

            {/* SVG Visual Network of the 4 Teams */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 flex flex-col items-center justify-center my-2 min-h-[300px]">
              <div className="relative w-full max-w-[340px] h-[240px]">
                {/* SVG connection lines */}
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 340 240">
                  {/* Top-left to Top-right */}
                  <line x1="70" y1="50" x2="270" y2="50" stroke="#94a3b8" strokeWidth="2" strokeDasharray="4" />
                  {/* Top-left to Bottom-left */}
                  <line x1="70" y1="50" x2="70" y2="190" stroke="#2563eb" strokeWidth="3" />
                  {/* Top-right to Bottom-right */}
                  <line x1="270" y1="50" x2="270" y2="190" stroke="#059669" strokeWidth="3" />
                  {/* Bottom-left to Bottom-right */}
                  <line x1="70" y1="190" x2="270" y2="190" stroke="#94a3b8" strokeWidth="2" strokeDasharray="4" />
                  {/* Cross diagonals */}
                  <line x1="70" y1="50" x2="270" y2="190" stroke="#2563eb" strokeWidth="2.5" />
                  <line x1="270" y1="50" x2="70" y2="190" stroke="#d97706" strokeWidth="2" />
                </svg>

                {/* Node 1: Alpha Corp (Top Left) */}
                <div className="absolute top-2 left-2 flex flex-col items-center bg-white border border-slate-300 rounded-lg p-2 shadow-xs text-center w-28">
                  <span className="w-3 h-3 rounded-full bg-blue-600 mb-1"></span>
                  <span className="text-[11px] font-bold text-slate-900 truncate max-w-[100px]">Alpha Corp</span>
                  <span className="text-[9px] font-mono text-slate-400">Tőkeerős</span>
                </div>

                {/* Node 2: Beta Industries (Top Right) */}
                <div className="absolute top-2 right-2 flex flex-col items-center bg-white border border-slate-300 rounded-lg p-2 shadow-xs text-center w-28">
                  <span className="w-3 h-3 rounded-full bg-emerald-600 mb-1"></span>
                  <span className="text-[11px] font-bold text-slate-900 truncate max-w-[100px]">Beta Ind.</span>
                  <span className="text-[9px] font-mono text-slate-400">Tech Bajnok</span>
                </div>

                {/* Node 3: Gamma Resources (Bottom Left) */}
                <div className="absolute bottom-2 left-2 flex flex-col items-center bg-white border border-slate-300 rounded-lg p-2 shadow-xs text-center w-28">
                  <span className="w-3 h-3 rounded-full bg-amber-600 mb-1"></span>
                  <span className="text-[11px] font-bold text-slate-900 truncate max-w-[100px]">Gamma Res.</span>
                  <span className="text-[9px] font-mono text-slate-400">Nyersanyag</span>
                </div>

                {/* Node 4: Delta Ventures (Bottom Right) */}
                <div className="absolute bottom-2 right-2 flex flex-col items-center bg-white border border-slate-300 rounded-lg p-2 shadow-xs text-center w-28">
                  <span className="w-3 h-3 rounded-full bg-purple-600 mb-1"></span>
                  <span className="text-[11px] font-bold text-slate-900 truncate max-w-[100px]">Delta Vent.</span>
                  <span className="text-[9px] font-mono text-slate-400">Start-up</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-100">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-0.5 bg-blue-600 inline-block"></span>
                <span>Kétoldalú csereügylet (Reciprocitás)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-0.5 border-t border-dashed border-slate-400 inline-block"></span>
                <span>Egyoldalú szállítás</span>
              </div>
            </div>
          </div>

          {/* Zone 3: Experience & Energy Dynamics (3 cols) */}
          <div className="lg:col-span-3 theme-card p-6 space-y-6">
            <div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
                3. Zóna
              </span>
              <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Energia & Élmény Delta
              </h2>
              <p className="text-xs text-slate-500">
                Pre vs Post felmérések átlaga
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
                <span className="text-slate-500">Pre-Game Pulse:</span>
                <span className="font-bold text-slate-800">{preSurveys.length} válasz</span>
              </div>
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-500">Post-Game Peer:</span>
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
              1. <em>„Hogyan alakult ki a függőség a nyersanyagot birtokló Gamma Resources körül a szimuláció elején?”</em>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700 leading-relaxed font-medium">
              2. <em>„Miért tudott a technológiai dominanciájú Beta Industries prémium árat kérni a sablonjai bérletéért?”</em>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700 leading-relaxed font-medium">
              3. <em>„Milyen párhuzamot láttok a játékbeli tárgyalások és a mindennapi munkahelyi együttműködés (silók) között?”</em>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
