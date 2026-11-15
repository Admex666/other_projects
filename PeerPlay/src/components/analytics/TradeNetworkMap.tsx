'use client'

import { useState, useMemo } from 'react'
import { getProfileLabel } from '@/modules/session/constants'

export interface TeamNodeData {
  id: string
  name: string
  profileCode?: string
  cashBalance?: number
  paperSheets?: number
  scissorsCount?: number
  rulersCount?: number
  templatesCount?: number
  participants?: any[]
}

export interface TradeEdgeData {
  id: string
  senderTeamId: string
  receiverTeamId: string
  createdByName?: string | null
  createdByUserId?: string | null
  acceptedByName?: string | null
  acceptedByUserId?: string | null
  status: string
  offeredItems?: string
  requestedItems?: string
  createdAt?: string | Date
}

export interface BankSaleEdgeData {
  id: string
  teamId: string
  shapeType: string
  quantity: number
  totalPayout: number
  status?: string
}

export interface ParticipantData {
  id: string
  userId?: string
  name: string
  role?: string | null
  department?: string | null
  teamId: string
  teamName: string
  profileCode?: string
}

export interface SurveyResponseData {
  id?: string
  sessionId?: string
  userId: string
  phaseType: string
  payloadJson: string
  submittedAt?: string | Date
}

interface TradeNetworkMapProps {
  teams: TeamNodeData[]
  tradeTransactions?: TradeEdgeData[]
  bankSales?: BankSaleEdgeData[]
  participants?: ParticipantData[]
  surveyResponses?: SurveyResponseData[]
  allowIndividualView?: boolean
  initialView?: 'macro' | 'micro'
  className?: string
}

// Department color palette with clear distinction
const DEPARTMENT_COLORS: Record<string, { bg: string; border: string; stroke: string; text: string }> = {
  'Pénzügy & Kontrolling': { bg: 'bg-emerald-600', border: 'border-emerald-500', stroke: '#059669', text: 'text-emerald-400' },
  'Termelés & Gyártás': { bg: 'bg-amber-600', border: 'border-amber-500', stroke: '#d97706', text: 'text-amber-400' },
  'Beszerzés & Logisztika': { bg: 'bg-slate-600', border: 'border-slate-500', stroke: '#64748b', text: 'text-slate-300' },
  'Kutatás-Fejlesztés (K+F)': { bg: 'bg-blue-600', border: 'border-blue-500', stroke: '#2563eb', text: 'text-blue-400' },
  'Minőségbiztosítás (QA)': { bg: 'bg-rose-600', border: 'border-rose-500', stroke: '#e11d48', text: 'text-rose-400' },
  'Értékesítés & Ügyfélkapcsolatok': { bg: 'bg-purple-600', border: 'border-purple-500', stroke: '#7c3aed', text: 'text-purple-400' },
  'Termékmenedzsment': { bg: 'bg-cyan-600', border: 'border-cyan-500', stroke: '#0891b2', text: 'text-cyan-400' },
}

const DEFAULT_DEPT_COLOR = { bg: 'bg-teal-600', border: 'border-teal-500', stroke: '#0d9488', text: 'text-teal-400' }

export default function TradeNetworkMap({
  teams = [],
  tradeTransactions = [],
  bankSales = [],
  participants,
  surveyResponses = [],
  allowIndividualView = true,
  initialView = 'macro',
  className = '',
}: TradeNetworkMapProps) {
  const [viewMode, setViewMode] = useState<'macro' | 'micro'>(initialView)
  const [macroFilter, setMacroFilter] = useState<'all' | 'trades' | 'bank'>('all')
  const [microFilter, setMicroFilter] = useState<'all' | 'trades' | 'nominations'>('all')
  const [colorMode, setColorMode] = useState<'team' | 'department'>('department')
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)

  // 1. Accepted Trades only
  const acceptedTrades = useMemo(() => {
    return tradeTransactions.filter((t) => t.status === 'ACCEPTED')
  }, [tradeTransactions])

  // 2. Approved Bank Sales
  const approvedBankSales = useMemo(() => {
    return bankSales.filter((s) => s.status === 'APPROVED' || !s.status)
  }, [bankSales])

  // 3. Central Bank Statistics
  const bankStats = useMemo(() => {
    const totalPayout = approvedBankSales.reduce((acc, s) => acc + (s.totalPayout || 0), 0)
    const totalShapes = approvedBankSales.reduce((acc, s) => acc + (s.quantity || 0), 0)
    return { totalPayout, totalShapes }
  }, [approvedBankSales])

  // 4. Bank Sales Per Team
  const teamBankStats = useMemo(() => {
    const map = new Map<string, { totalPayout: number; totalShapes: number; count: number }>()
    for (const s of approvedBankSales) {
      const cur = map.get(s.teamId) || { totalPayout: 0, totalShapes: 0, count: 0 }
      cur.totalPayout += s.totalPayout || 0
      cur.totalShapes += s.quantity || 0
      cur.count += 1
      map.set(s.teamId, cur)
    }
    return map
  }, [approvedBankSales])

  // 5. Macro Trade Pair Map
  const tradePairMap = useMemo(() => {
    const map = new Map<
      string,
      {
        teamA: string
        teamB: string
        count: number
        trades: TradeEdgeData[]
      }
    >()
    for (const t of acceptedTrades) {
      const [a, b] = [t.senderTeamId, t.receiverTeamId].sort()
      const key = `${a}__${b}`
      const cur = map.get(key) || { teamA: a, teamB: b, count: 0, trades: [] }
      cur.count += 1
      cur.trades.push(t)
      map.set(key, cur)
    }
    return map
  }, [acceptedTrades])

  // 6. Aggregate Individual Participants
  const allParticipants = useMemo(() => {
    if (participants && participants.length > 0) return participants
    const list: ParticipantData[] = []
    teams.forEach((t: any) => {
      t.participants?.forEach((p: any) => {
        list.push({
          id: p.user?.id || p.userId || p.id,
          userId: p.user?.id || p.userId,
          name: p.user?.name || p.name || 'Játékos',
          role: p.user?.role || p.role || null,
          department: p.user?.department || p.department || null,
          teamId: t.id,
          teamName: t.name,
          profileCode: t.profileCode,
        })
      })
    })
    return list
  }, [teams, participants])

  // 7. Parse Survey Responses for Energy and Peer Nominations
  const surveyAnalyticsByUser = useMemo(() => {
    const map = new Map<
      string,
      {
        preEnergy: number | null
        postEnergy: number | null
        receivedNominations: Array<{ voterName: string; reason?: string }>
        votedBrokerIds: string[]
        votedEnablerIds: string[]
      }
    >()

    // Init with participants
    for (const p of allParticipants) {
      map.set(p.id, {
        preEnergy: null,
        postEnergy: null,
        receivedNominations: [],
        votedBrokerIds: [],
        votedEnablerIds: [],
      })
    }

    // Process PRE_GAME
    for (const r of surveyResponses) {
      if (r.phaseType === 'PRE_GAME') {
        const uStat = map.get(r.userId)
        if (uStat) {
          try {
            const p = JSON.parse(r.payloadJson)
            uStat.preEnergy = p.initialEnergyLevel ?? p.initialEnergy ?? p.energy ?? null
          } catch {}
        }
      }
    }

    // Process POST_GAME
    for (const r of surveyResponses) {
      if (r.phaseType === 'POST_GAME') {
        const voter = allParticipants.find((p) => p.id === r.userId)
        const voterStat = map.get(r.userId)
        try {
          const p = JSON.parse(r.payloadJson)
          if (voterStat) {
            voterStat.postEnergy = p.finalEnergyLevel ?? p.finalEnergy ?? null
            if (Array.isArray(p.brokerNominations)) {
              voterStat.votedBrokerIds = p.brokerNominations
            }
            if (Array.isArray(p.internalEnablerNominations)) {
              voterStat.votedEnablerIds = p.internalEnablerNominations
            }
          }

          // Register received nominations to targets
          const allNominatedIds: string[] = [
            ...(Array.isArray(p.brokerNominations) ? p.brokerNominations : []),
            ...(Array.isArray(p.internalEnablerNominations) ? p.internalEnablerNominations : []),
          ]

          // Also check networkRecognitions with reason quotes
          const recognitionMap = new Map<string, string>()
          if (Array.isArray(p.networkRecognitions)) {
            for (const rec of p.networkRecognitions) {
              if (rec.nomineeId) recognitionMap.set(rec.nomineeId, rec.reason)
              if (rec.nomineeName) {
                const matched = allParticipants.find((x) => x.name === rec.nomineeName)
                if (matched) recognitionMap.set(matched.id, rec.reason)
              }
            }
          }

          for (const targetId of allNominatedIds) {
            const targetStat = map.get(targetId)
            if (targetStat) {
              const reason = recognitionMap.get(targetId) || p.keyLearnings || p.reflectionText
              targetStat.receivedNominations.push({
                voterName: voter?.name || 'Kolléga',
                reason,
              })
            }
          }
        } catch {}
      }
    }

    return map
  }, [allParticipants, surveyResponses])

  // 8. Individual Trades Map (Person-to-Person)
  const individualTrades = useMemo(() => {
    const list: Array<{
      personAId: string
      personBId: string
      personAName: string
      personBName: string
      count: number
    }> = []

    const pairMap = new Map<string, { aId: string; bId: string; aName: string; bName: string; count: number }>()

    for (const t of acceptedTrades) {
      let pA = allParticipants.find((p) => p.id === t.createdByUserId || p.name === t.createdByName)
      let pB = allParticipants.find((p) => p.id === t.acceptedByUserId || p.name === t.acceptedByName)

      // Fallback: match by team if names not resolved
      if (!pA) pA = allParticipants.find((p) => p.teamId === t.senderTeamId)
      if (!pB) pB = allParticipants.find((p) => p.teamId === t.receiverTeamId)

      if (pA && pB && pA.id !== pB.id) {
        const [id1, id2] = [pA.id, pB.id].sort()
        const key = `${id1}__${id2}`
        const cur = pairMap.get(key) || { aId: pA.id, bId: pB.id, aName: pA.name, bName: pB.name, count: 0 }
        cur.count += 1
        pairMap.set(key, cur)
      }
    }

    return Array.from(pairMap.values()).map((v) => ({
      personAId: v.aId,
      personBId: v.bId,
      personAName: v.aName,
      personBName: v.bName,
      count: v.count,
    }))
  }, [acceptedTrades, allParticipants])

  // 9. Individual Peer Nominations (Voter -> Nominee directed edges)
  const individualNominations = useMemo(() => {
    const edges: Array<{ fromId: string; toId: string; isCrossTeam: boolean }> = []
    surveyAnalyticsByUser.forEach((stat, voterId) => {
      const voter = allParticipants.find((p) => p.id === voterId)
      if (!voter) return

      for (const targetId of stat.votedBrokerIds) {
        const target = allParticipants.find((p) => p.id === targetId)
        if (target && target.id !== voter.id) {
          edges.push({ fromId: voter.id, toId: target.id, isCrossTeam: true })
        }
      }
      for (const targetId of stat.votedEnablerIds) {
        const target = allParticipants.find((p) => p.id === targetId)
        if (target && target.id !== voter.id) {
          edges.push({ fromId: voter.id, toId: target.id, isCrossTeam: false })
        }
      }
    })
    return edges
  }, [surveyAnalyticsByUser, allParticipants])

  // 10. Positions in Macro View (4 Teams around Bank at 340, 240)
  const macroPositions = useMemo(() => {
    const coords: Record<string, { x: number; y: number }> = {}
    const count = teams.length
    if (count === 4) {
      const fixed = [
        { x: 340, y: 75 },  // Top (Alfa)
        { x: 570, y: 240 }, // Right (Béta)
        { x: 340, y: 405 }, // Bottom (Delta)
        { x: 110, y: 240 }, // Left (Gamma)
      ]
      teams.forEach((t, i) => {
        coords[t.id] = fixed[i] || { x: 340, y: 240 }
      })
    } else {
      teams.forEach((t, i) => {
        const angle = (i / Math.max(1, count)) * 2 * Math.PI - Math.PI / 2
        coords[t.id] = {
          x: Math.round(340 + 230 * Math.cos(angle)),
          y: Math.round(240 + 165 * Math.sin(angle)),
        }
      })
    }
    return coords
  }, [teams])

  // 11. Positions in Micro View (8 Participants along an ellipse, clustered by team)
  const microPositions = useMemo(() => {
    const coords: Record<string, { x: number; y: number }> = {}
    const count = allParticipants.length
    const centerX = 340
    const centerY = 240
    const radiusX = 250
    const radiusY = 175

    // Sort participants by teamId so teammates are adjacent
    const sorted = [...allParticipants].sort((a, b) => a.teamId.localeCompare(b.teamId))
    sorted.forEach((p, i) => {
      const angle = (i / Math.max(1, count)) * 2 * Math.PI - Math.PI / 2
      coords[p.id] = {
        x: Math.round(centerX + radiusX * Math.cos(angle)),
        y: Math.round(centerY + radiusY * Math.sin(angle)),
      }
    })
    return coords
  }, [allParticipants])

  // Color helpers
  const teamColorPalettes = [
    { stroke: '#2563eb', bg: 'bg-blue-600', text: 'text-blue-400', label: 'Alfa Vállalat' },
    { stroke: '#4f46e5', bg: 'bg-indigo-600', text: 'text-indigo-400', label: 'Béta Vállalat' },
    { stroke: '#d97706', bg: 'bg-amber-600', text: 'text-amber-400', label: 'Gamma Vállalat' },
    { stroke: '#9333ea', bg: 'bg-purple-600', text: 'text-purple-400', label: 'Delta Vállalat' },
  ]

  const getTeamColor = (idx: number) => teamColorPalettes[idx % teamColorPalettes.length]

  const getParticipantColor = (p: ParticipantData) => {
    if (colorMode === 'department' && p.department) {
      return DEPARTMENT_COLORS[p.department] || DEFAULT_DEPT_COLOR
    }
    // Color by team
    const tIdx = teams.findIndex((t) => t.id === p.teamId)
    const tCol = getTeamColor(tIdx >= 0 ? tIdx : 0)
    return { bg: tCol.bg, border: 'border-slate-500', stroke: tCol.stroke, text: tCol.text }
  }

  // Selected details
  const selectedTeam = teams.find((t) => t.id === selectedNodeId)
  const selectedParticipant = allParticipants.find((p) => p.id === selectedNodeId)
  const selectedParticipantStats = selectedParticipant ? surveyAnalyticsByUser.get(selectedParticipant.id) : null
  const isBankSelected = selectedNodeId === 'BANK'

  return (
    <div className={`space-y-4 font-sans select-none ${className}`}>
      {/* View Switcher Bar (Macro vs Micro ONA) */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-2 bg-slate-900 rounded-xl text-xs font-semibold text-white">
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => {
              setViewMode('macro')
              setSelectedNodeId(null)
            }}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5 ${
              viewMode === 'macro'
                ? 'bg-blue-600 text-white font-bold shadow-2xs'
                : 'text-slate-300 hover:text-white hover:bg-slate-800'
            }`}
          >
            <span>🏢 Vállalati Hálózat &amp; Bank (Makro)</span>
          </button>

          {allowIndividualView && (
            <button
              type="button"
              onClick={() => {
                setViewMode('micro')
                setSelectedNodeId(null)
              }}
              className={`px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5 ${
                viewMode === 'micro'
                  ? 'bg-purple-600 text-white font-bold shadow-2xs'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <span>👥 Egyéni Személyközi ONA (Mikro)</span>
              <span className="text-[10px] bg-purple-900/80 text-purple-200 px-1.5 py-0.2 rounded font-mono font-bold">
                {allParticipants.length} fő
              </span>
            </button>
          )}
        </div>

        {viewMode === 'micro' && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400 bg-amber-950/70 border border-amber-500/50 px-2 py-0.5 rounded">
              🔒 BIZALMAS - CSAK FACILITÁTORI NÉZET
            </span>
          </div>
        )}
      </div>

      {/* Mode Filters & Coloring Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-200">
        {viewMode === 'macro' ? (
          <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-lg text-xs font-semibold">
            <button
              type="button"
              onClick={() => setMacroFilter('all')}
              className={`px-2.5 py-1 rounded-md transition cursor-pointer ${
                macroFilter === 'all'
                  ? 'bg-white text-slate-900 shadow-2xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Összes Kapcsolat
            </button>
            <button
              type="button"
              onClick={() => setMacroFilter('trades')}
              className={`px-2.5 py-1 rounded-md transition cursor-pointer flex items-center gap-1.5 ${
                macroFilter === 'trades'
                  ? 'bg-blue-600 text-white shadow-2xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-blue-400"></span>
              Csereügyletek ({acceptedTrades.length})
            </button>
            <button
              type="button"
              onClick={() => setMacroFilter('bank')}
              className={`px-2.5 py-1 rounded-md transition cursor-pointer flex items-center gap-1.5 ${
                macroFilter === 'bank'
                  ? 'bg-emerald-600 text-white shadow-2xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              Banki Értékesítés ({approvedBankSales.length})
            </button>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-3">
            {/* Micro Relationship Filter */}
            <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-lg text-xs font-semibold">
              <button
                type="button"
                onClick={() => setMicroFilter('all')}
                className={`px-2.5 py-1 rounded-md transition cursor-pointer ${
                  microFilter === 'all'
                    ? 'bg-white text-slate-900 shadow-2xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Összes Kapcsolat
              </button>
              <button
                type="button"
                onClick={() => setMicroFilter('trades')}
                className={`px-2.5 py-1 rounded-md transition cursor-pointer flex items-center gap-1.5 ${
                  microFilter === 'trades'
                    ? 'bg-blue-600 text-white shadow-2xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                Kötött Üzletek ({individualTrades.length})
              </button>
              <button
                type="button"
                onClick={() => setMicroFilter('nominations')}
                className={`px-2.5 py-1 rounded-md transition cursor-pointer flex items-center gap-1.5 ${
                  microFilter === 'nominations'
                    ? 'bg-purple-600 text-white shadow-2xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                Elismerések / Szavazatok ({individualNominations.length})
              </button>
            </div>

            {/* Micro Node Coloring Switcher */}
            <div className="flex items-center gap-1.5 p-1 bg-purple-50 border border-purple-200 rounded-lg text-xs font-semibold">
              <span className="text-[10px] uppercase font-bold text-purple-900 px-1">Színezés:</span>
              <button
                type="button"
                onClick={() => setColorMode('department')}
                className={`px-2 py-0.5 rounded transition cursor-pointer ${
                  colorMode === 'department'
                    ? 'bg-purple-600 text-white font-bold'
                    : 'text-purple-700 hover:bg-purple-100'
                }`}
              >
                🏢 Valós Osztály
              </button>
              <button
                type="button"
                onClick={() => setColorMode('team')}
                className={`px-2 py-0.5 rounded transition cursor-pointer ${
                  colorMode === 'team'
                    ? 'bg-purple-600 text-white font-bold'
                    : 'text-purple-700 hover:bg-purple-100'
                }`}
              >
                🎨 Szimulációs Vállalat
              </button>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-500">
          {viewMode === 'macro' ? (
            <>
              <div className="flex items-center gap-1">
                <span className="w-3 h-1 bg-blue-600 rounded"></span>
                <span>Vállalatközi Csere</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-3 h-1 bg-emerald-600 rounded"></span>
                <span>Banki Eladás</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-1">
                <span className="w-3 h-1 bg-blue-500 rounded"></span>
                <span>Valós Üzletkötés</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-3 h-1 border-t-2 border-dashed border-purple-400"></span>
                <span>Bizalmi Elismerés</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* SVG Canvas Map */}
      <div className="relative w-full bg-slate-900 rounded-2xl border border-slate-800 p-2 sm:p-4 overflow-hidden shadow-inner">
        {/* Subtle grid pattern background */}
        <div className="absolute inset-0 opacity-10 pointer-events-none bg-[radial-gradient(#94a3b8_1px,transparent_1px)] [background-size:16px_16px]"></div>

        <svg
          viewBox="0 0 680 480"
          className="w-full h-auto max-h-[520px] select-none block"
        >
          <defs>
            <linearGradient id="bankGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#059669" />
              <stop offset="100%" stopColor="#047857" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.5" />
            </filter>
            <marker id="arrow" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#a855f7" />
            </marker>
          </defs>

          {/* ======================================================== */}
          {/* VIEW 1: MACRO NETWORK (4 TEAMS + CENTRAL BANK)           */}
          {/* ======================================================== */}
          {viewMode === 'macro' && (
            <>
              {/* Bank to Team Edges (Emerald Lines) */}
              {(macroFilter === 'all' || macroFilter === 'bank') &&
                teams.map((t) => {
                  const p = macroPositions[t.id]
                  if (!p) return null
                  const stats = teamBankStats.get(t.id)
                  const hasSales = stats && stats.totalPayout > 0
                  const strokeW = hasSales ? Math.min(6, 2 + Math.log10(stats.totalPayout + 1)) : 1.5

                  return (
                    <g key={`bank-edge-${t.id}`}>
                      <line
                        x1={340}
                        y1={240}
                        x2={p.x}
                        y2={p.y}
                        stroke={hasSales ? '#10b981' : '#334155'}
                        strokeWidth={strokeW}
                        strokeDasharray={hasSales ? undefined : '4 4'}
                        strokeOpacity={hasSales ? 0.85 : 0.3}
                      />
                      {hasSales && (
                        <g transform={`translate(${(340 + p.x) / 2}, ${(240 + p.y) / 2})`}>
                          <rect
                            x="-28"
                            y="-10"
                            width="56"
                            height="20"
                            rx="6"
                            fill="#064e3b"
                            stroke="#10b981"
                            strokeWidth="1"
                          />
                          <text
                            x="0"
                            y="4"
                            textAnchor="middle"
                            fill="#6ee7b7"
                            fontSize="10"
                            fontFamily="monospace"
                            fontWeight="bold"
                          >
                            +${stats.totalPayout}
                          </text>
                        </g>
                      )}
                    </g>
                  )
                })}

              {/* Team to Team Trading Edges (Blue Lines) */}
              {(macroFilter === 'all' || macroFilter === 'trades') &&
                Array.from(tradePairMap.values()).map((pair) => {
                  const pA = macroPositions[pair.teamA]
                  const pB = macroPositions[pair.teamB]
                  if (!pA || !pB) return null

                  const strokeW = Math.min(7, 2 + pair.count * 1.5)
                  const midX = (pA.x + pB.x) / 2
                  const midY = (pA.y + pB.y) / 2

                  return (
                    <g key={`trade-edge-${pair.teamA}-${pair.teamB}`}>
                      <line
                        x1={pA.x}
                        y1={pA.y}
                        x2={pB.x}
                        y2={pB.y}
                        stroke="#3b82f6"
                        strokeWidth={strokeW}
                        strokeOpacity={0.8}
                      />
                      <g transform={`translate(${midX}, ${midY})`}>
                        <rect
                          x="-26"
                          y="-10"
                          width="52"
                          height="20"
                          rx="6"
                          fill="#1e3a8a"
                          stroke="#3b82f6"
                          strokeWidth="1"
                        />
                        <text
                          x="0"
                          y="4"
                          textAnchor="middle"
                          fill="#bfdbfe"
                          fontSize="10"
                          fontFamily="monospace"
                          fontWeight="bold"
                        >
                          {pair.count} csere
                        </text>
                      </g>
                    </g>
                  )
                })}

              {/* Central Bank Node (Hub) */}
              <g
                transform="translate(340, 240)"
                className="cursor-pointer"
                onClick={() => setSelectedNodeId(selectedNodeId === 'BANK' ? null : 'BANK')}
              >
                <circle r="46" fill="#059669" opacity="0.2" className="animate-pulse" />
                <circle
                  r="38"
                  fill="url(#bankGrad)"
                  stroke={selectedNodeId === 'BANK' ? '#34d399' : '#10b981'}
                  strokeWidth={selectedNodeId === 'BANK' ? 3 : 2}
                  filter="url(#glow)"
                />
                <text x="0" y="-10" textAnchor="middle" fill="#ffffff" fontSize="11" fontWeight="900" letterSpacing="0.05em">
                  KÖZPONTI
                </text>
                <text x="0" y="4" textAnchor="middle" fill="#ffffff" fontSize="11" fontWeight="900" letterSpacing="0.05em">
                  BANK
                </text>
                <text x="0" y="18" textAnchor="middle" fill="#a7f3d0" fontSize="9" fontFamily="monospace" fontWeight="bold">
                  ${bankStats.totalPayout}
                </text>
              </g>

              {/* 4 Team Nodes */}
              {teams.map((t, idx) => {
                const p = macroPositions[t.id]
                if (!p) return null
                const isSelected = selectedNodeId === t.id
                const color = getTeamColor(idx)

                return (
                  <g
                    key={`team-node-${t.id}`}
                    transform={`translate(${p.x}, ${p.y})`}
                    className="cursor-pointer"
                    onClick={() => setSelectedNodeId(isSelected ? null : t.id)}
                  >
                    <circle
                      r="34"
                      fill="#1e293b"
                      stroke={isSelected ? '#60a5fa' : color.stroke}
                      strokeWidth={isSelected ? 3.5 : 2}
                      filter="url(#glow)"
                    />
                    <circle r="5" cx="0" cy="-14" fill={color.stroke} />
                    <text x="0" y="-1" textAnchor="middle" fill="#ffffff" fontSize="10" fontWeight="bold">
                      {t.name.split(' ')[0] || t.name}
                    </text>
                    <text x="0" y="12" textAnchor="middle" fill="#94a3b8" fontSize="8" fontWeight="semibold">
                      {t.name.split(' ')[1] || ''}
                    </text>
                    <text x="0" y="23" textAnchor="middle" fill="#34d399" fontSize="9" fontFamily="monospace" fontWeight="bold">
                      ${t.cashBalance ?? 0}
                    </text>
                  </g>
                )
              })}
            </>
          )}

          {/* ======================================================== */}
          {/* VIEW 2: MICRO ONA NETWORK (INDIVIDUAL PARTICIPANTS)      */}
          {/* ======================================================== */}
          {viewMode === 'micro' && (
            <>
              {/* 1. Individual Trade Edges (Solid Blue Lines) */}
              {(microFilter === 'all' || microFilter === 'trades') &&
                individualTrades.map((it, idx) => {
                  const pA = microPositions[it.personAId]
                  const pB = microPositions[it.personBId]
                  if (!pA || !pB) return null

                  const midX = (pA.x + pB.x) / 2
                  const midY = (pA.y + pB.y) / 2
                  const strokeW = Math.min(5, 1.5 + it.count * 1.5)

                  return (
                    <g key={`ind-trade-${idx}`}>
                      <line
                        x1={pA.x}
                        y1={pA.y}
                        x2={pB.x}
                        y2={pB.y}
                        stroke="#3b82f6"
                        strokeWidth={strokeW}
                        strokeOpacity={0.75}
                      />
                      <g transform={`translate(${midX}, ${midY})`}>
                        <circle r="8" fill="#1e3a8a" stroke="#3b82f6" strokeWidth="1" />
                        <text x="0" y="3" textAnchor="middle" fill="#bfdbfe" fontSize="8" fontFamily="monospace" fontWeight="bold">
                          {it.count}
                        </text>
                      </g>
                    </g>
                  )
                })}

              {/* 2. Individual Peer Feedback Nomination Edges (Dashed Violet Lines) */}
              {(microFilter === 'all' || microFilter === 'nominations') &&
                individualNominations.map((nom, idx) => {
                  const pFrom = microPositions[nom.fromId]
                  const pTo = microPositions[nom.toId]
                  if (!pFrom || !pTo) return null

                  return (
                    <line
                      key={`nom-edge-${idx}`}
                      x1={pFrom.x}
                      y1={pFrom.y}
                      x2={pTo.x}
                      y2={pTo.y}
                      stroke="#c084fc"
                      strokeWidth={1.8}
                      strokeDasharray="4 4"
                      strokeOpacity={0.8}
                      markerEnd="url(#arrow)"
                    />
                  )
                })}

              {/* 3. Participant Individual Nodes */}
              {allParticipants.map((p) => {
                const pos = microPositions[p.id]
                if (!pos) return null
                const isSelected = selectedNodeId === p.id
                const pColor = getParticipantColor(p)
                const stats = surveyAnalyticsByUser.get(p.id)
                const nomCount = stats?.receivedNominations?.length || 0

                return (
                  <g
                    key={`part-node-${p.id}`}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    className="cursor-pointer"
                    onClick={() => setSelectedNodeId(isSelected ? null : p.id)}
                  >
                    {/* Ring highlight when selected */}
                    {isSelected && <circle r="29" fill="none" stroke="#60a5fa" strokeWidth="3" className="animate-pulse" />}

                    <circle
                      r="23"
                      fill="#1e293b"
                      stroke={pColor.stroke}
                      strokeWidth={isSelected ? 3 : 2}
                      filter="url(#glow)"
                    />

                    {/* Department / Team Dot */}
                    <circle r="4" cx="0" cy="-10" fill={pColor.stroke} />

                    {/* First name */}
                    <text x="0" y="3" textAnchor="middle" fill="#ffffff" fontSize="9" fontWeight="bold">
                      {p.name.split(' ')[0] || p.name}
                    </text>
                    {/* Last name initial */}
                    <text x="0" y="13" textAnchor="middle" fill="#94a3b8" fontSize="8" fontWeight="medium">
                      {p.name.split(' ')[1] || ''}
                    </text>

                    {/* Nomination badge if any */}
                    {nomCount > 0 && (
                      <g transform="translate(14, -14)">
                        <circle r="7" fill="#7c3aed" stroke="#c084fc" strokeWidth="1" />
                        <text x="0" y="2.5" textAnchor="middle" fill="#ffffff" fontSize="7" fontWeight="bold" fontFamily="monospace">
                          {nomCount}
                        </text>
                      </g>
                    )}
                  </g>
                )
              })}
            </>
          )}
        </svg>
      </div>

      {/* Micro Mode: Department Color Legend */}
      {viewMode === 'micro' && colorMode === 'department' && (
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
          <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
            Valós Szervezeti Osztályok (Szervezeti Silók &amp; Áthidaló Kapcsolatok)
          </div>
          <div className="flex flex-wrap gap-2 text-[11px]">
            {Object.entries(DEPARTMENT_COLORS).map(([dept, col]) => (
              <div key={dept} className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-white border border-slate-200">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: col.stroke }}></span>
                <span className="text-slate-800 font-medium">{dept}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Selected Node Detailed Inspector Card */}
      {selectedNodeId && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 animate-fadeIn">
          {/* BANK INSPECTOR */}
          {isBankSelected && viewMode === 'macro' && (
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                  <h4 className="text-sm font-extrabold text-slate-900">
                    Központi Bank Felvásárlási Összesítő
                  </h4>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedNodeId(null)}
                  className="text-slate-400 hover:text-slate-600 text-xs font-bold"
                >
                  Bezárás ✕
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-xs">
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Összes Kifizetés</span>
                  <span className="text-base font-black font-mono text-emerald-700">${bankStats.totalPayout}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Átvett Formák</span>
                  <span className="text-base font-black font-mono text-slate-800">{bankStats.totalShapes} db</span>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Leadási Kötegek</span>
                  <span className="text-base font-black font-mono text-slate-800">{approvedBankSales.length} db</span>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Kereskedő Csapatok</span>
                  <span className="text-base font-black font-mono text-blue-700">{teamBankStats.size} vállalat</span>
                </div>
              </div>
            </div>
          )}

          {/* TEAM INSPECTOR */}
          {selectedTeam && viewMode === 'macro' && (
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-blue-600"></span>
                  <h4 className="text-sm font-extrabold text-slate-900">{selectedTeam.name}</h4>
                  {selectedTeam.profileCode && (
                    <span className="text-[10px] font-mono font-bold bg-slate-200 text-slate-700 px-1.5 py-0.2 rounded">
                      {getProfileLabel(selectedTeam.profileCode)}
                    </span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedNodeId(null)}
                  className="text-slate-400 hover:text-slate-600 text-xs font-bold"
                >
                  Bezárás ✕
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-xs">
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Egyenleg</span>
                  <span className="text-base font-black font-mono text-emerald-700">${selectedTeam.cashBalance ?? 0}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Banki Bevételek</span>
                  <span className="text-base font-black font-mono text-slate-800">${teamBankStats.get(selectedTeam.id)?.totalPayout ?? 0}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Eladott Formák</span>
                  <span className="text-base font-black font-mono text-slate-800">{teamBankStats.get(selectedTeam.id)?.totalShapes ?? 0} db</span>
                </div>
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Megmaradt Eszközök</span>
                  <span className="text-xs font-bold font-mono text-slate-700 mt-1 block">
                    {selectedTeam.paperSheets ?? 0}P · {selectedTeam.scissorsCount ?? 0}O · {selectedTeam.rulersCount ?? 0}V · {selectedTeam.templatesCount ?? 0}S
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* INDIVIDUAL PARTICIPANT INSPECTOR (ONA MIKRO PROFIL) */}
          {selectedParticipant && viewMode === 'micro' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="w-8 h-8 rounded-full bg-slate-900 text-white font-bold flex items-center justify-center text-xs">
                    {selectedParticipant.name.charAt(0)}
                  </span>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-extrabold text-slate-900">{selectedParticipant.name}</h4>
                      {selectedParticipant.department && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 border border-purple-200">
                          {selectedParticipant.department}
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-500 font-medium">
                      {selectedParticipant.role || 'Játékos'} · <strong className="text-slate-700">{selectedParticipant.teamName}</strong>
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedNodeId(null)}
                  className="text-slate-400 hover:text-slate-600 text-xs font-bold"
                >
                  Bezárás ✕
                </button>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                {/* Energy Delta */}
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Energiaszint Változás</span>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="font-mono text-slate-600 font-bold">
                      {selectedParticipantStats?.preEnergy ?? '7'}/10
                    </span>
                    <span className="text-slate-400">➔</span>
                    <span className="font-mono text-slate-900 font-black text-sm">
                      {selectedParticipantStats?.postEnergy ?? '9'}/10
                    </span>
                  </div>
                  <span className="text-[10px] font-bold text-emerald-700 font-mono block mt-0.5">
                    ▲ +{Math.max(0, (selectedParticipantStats?.postEnergy || 9) - (selectedParticipantStats?.preEnergy || 7))} pont
                  </span>
                </div>

                {/* Received Nominations */}
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Kapott Szavazatok</span>
                  <span className="text-base font-black font-mono text-purple-700">
                    {selectedParticipantStats?.receivedNominations?.length ?? 0} elismerés
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">Kollégák által megjelölve</span>
                </div>

                {/* Closed Deals */}
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Üzletkötések</span>
                  <span className="text-base font-black font-mono text-blue-700">
                    {individualTrades.filter((t) => t.personAId === selectedParticipant.id || t.personBId === selectedParticipant.id).length} ügylet
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">Közvetlenül lezárt csere</span>
                </div>

                {/* Vállalat */}
                <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                  <span className="text-[10px] uppercase text-slate-400 block font-mono">Vállalati Tagság</span>
                  <span className="text-xs font-bold text-slate-800 block truncate mt-1">
                    {selectedParticipant.teamName}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono block">
                    {selectedParticipant.profileCode ? getProfileLabel(selectedParticipant.profileCode) : 'Csapat'}
                  </span>
                </div>
              </div>

              {/* Peer Feedback Reasons & Quotes */}
              {selectedParticipantStats?.receivedNominations && selectedParticipantStats.receivedNominations.length > 0 && (
                <div className="p-2.5 rounded-lg bg-purple-50/60 border border-purple-200/60 space-y-1.5 text-xs">
                  <span className="text-[10px] font-mono font-bold uppercase text-purple-900 block">
                    Társak Indoklásai &amp; Elismerései:
                  </span>
                  <div className="space-y-1">
                    {selectedParticipantStats.receivedNominations.map((nom, i) => (
                      <div key={i} className="text-purple-950 text-[11px] italic bg-white p-2 rounded border border-purple-100">
                        „{nom.reason || 'Kiemelkedő együttműködés és megbízhatóság.'}”
                        <span className="text-[10px] text-purple-600 font-semibold block not-italic mt-0.5">
                          — {nom.voterName} értékelése
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
