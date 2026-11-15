'use client'

import { useState } from 'react'
import {
  ShapeType,
  ShapeBatchItem,
  BASE_PRICES,
} from '@/modules/bank/constants'
import { getShapeLabel } from '@/modules/session/constants'
import toast from 'react-hot-toast'

interface ParticipantInfo {
  id: string
  userId: string
  user?: {
    id: string
    name: string
  }
}

interface TeamInfo {
  id: string
  name: string
  profileCode: string
  cashBalance: number
  participants?: ParticipantInfo[]
}

interface BankSaleRecord {
  id: string
  teamId: string
  batchId?: string | null
  shapeType: string
  quantity: number
  unitBasePrice: number
  multiplier: number
  finalUnitPrice: number
  totalPayout: number
  qualityNotes?: string | null
  status?: string
  submittedByName?: string | null
  submittedByUserId?: string | null
  approvedAt?: string | Date | null
  soldAt: string | Date
}

interface BankIntakeDeskProps {
  sessionId: string
  teams: TeamInfo[]
  activeMultipliers?: Record<string, number>
  recentSales?: BankSaleRecord[]
  onMutate?: () => void
}

const SHAPES: { type: ShapeType; label: string; spec: string; iconPath: string }[] = [
  {
    type: 'SQUARE',
    label: 'Szabályos Négyzet',
    spec: '10 × 10 cm (pontos derékszög)',
    iconPath: 'M4 4h16v16H4z',
  },
  {
    type: 'TRIANGLE',
    label: 'Egyenlő oldalú Háromszög',
    spec: '10 cm-es oldalak (60° szögek)',
    iconPath: 'M12 3l9 17H3z',
  },
  {
    type: 'CIRCLE',
    label: 'Kör (Sablonnal)',
    spec: 'Ø 10 cm átmérő',
    iconPath: 'M12 2a10 10 0 100 20 10 10 0 000-20z',
  },
  {
    type: 'RECTANGLE',
    label: 'Téglalap',
    spec: '5 × 15 cm (vonalzóval ellenőrizve)',
    iconPath: 'M2 6h20v12H2z',
  },
  {
    type: 'PREMIUM_PACK',
    label: 'Prémium Csomag',
    spec: '2 db Háromszög + 1 db Négyzet',
    iconPath: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
  },
]

export default function BankIntakeDesk({
  sessionId,
  teams,
  activeMultipliers = {},
  recentSales = [],
  onMutate,
}: BankIntakeDeskProps) {
  const [selectedTeamId, setSelectedTeamId] = useState<string>(teams[0]?.id || '')
  const [selectedParticipantUserId, setSelectedParticipantUserId] = useState<string>('')
  const [quantities, setQuantities] = useState<Record<ShapeType, number>>({
    SQUARE: 0,
    TRIANGLE: 0,
    CIRCLE: 0,
    RECTANGLE: 0,
    PREMIUM_PACK: 0,
  })
  const [qualityNotes, setQualityNotes] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)

  const selectedTeam = teams.find((t) => t.id === selectedTeamId)
  const teamParticipants = selectedTeam?.participants || []
  const selectedParticipant = teamParticipants.find(
    (p) => p.userId === selectedParticipantUserId || p.user?.id === selectedParticipantUserId
  )

  // Group pending submissions by batchId or id
  const pendingSales = recentSales.filter((s) => s.status === 'PENDING')
  const pendingBatchesMap = new Map<
    string,
    {
      batchKey: string
      teamId: string
      submittedByName: string
      submittedByUserId?: string | null
      soldAt: string | Date
      notes?: string | null
      items: BankSaleRecord[]
      totalPayout: number
      totalQuantity: number
    }
  >()

  for (const sale of pendingSales) {
    const key = sale.batchId || sale.id
    const existing = pendingBatchesMap.get(key)
    if (existing) {
      existing.items.push(sale)
      existing.totalPayout += sale.totalPayout
      existing.totalQuantity += sale.quantity
      if (sale.qualityNotes && !existing.notes) existing.notes = sale.qualityNotes
    } else {
      pendingBatchesMap.set(key, {
        batchKey: key,
        teamId: sale.teamId,
        submittedByName: sale.submittedByName || 'Vállalati csapattag',
        submittedByUserId: sale.submittedByUserId,
        soldAt: sale.soldAt,
        notes: sale.qualityNotes,
        items: [sale],
        totalPayout: sale.totalPayout,
        totalQuantity: sale.quantity,
      })
    }
  }
  const pendingBatches = Array.from(pendingBatchesMap.values())

  const handleApproveBatch = async (batchKey: string, teamName: string) => {
    setIsSubmitting(true)
    try {
      const res = await fetch('/api/bank', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'approve',
          sessionId,
          batchId: batchKey,
        }),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba a banki jóváhagyáskor')
      }
      toast.success(`Jóváhagyva & Kifizetve! +$${data.totalPayout} (${teamName})`)
      onMutate?.()
    } catch (err: any) {
      toast.error(err.message || 'Hiba a jóváhagyás során')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRejectBatch = async (batchKey: string) => {
    setIsSubmitting(true)
    try {
      const res = await fetch('/api/bank', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'reject',
          sessionId,
          batchId: batchKey,
          qualityNotes: 'Selejt minőségileg elutasítva a Bank által',
        }),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba a selejtezéskor')
      }
      toast('Leadási csomag elutasítva mint selejt. Nem történt kifizetés.')
      onMutate?.()
    } catch (err: any) {
      toast.error(err.message || 'Hiba a selejtezés során')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleQuantityChange = (shape: ShapeType, delta: number) => {
    setQuantities((prev) => ({
      ...prev,
      [shape]: Math.max(0, (prev[shape] || 0) + delta),
    }))
  }

  const handleReset = () => {
    setQuantities({
      SQUARE: 0,
      TRIANGLE: 0,
      CIRCLE: 0,
      RECTANGLE: 0,
      PREMIUM_PACK: 0,
    })
    setQualityNotes('')
    setSelectedParticipantUserId('')
  }

  // Calculate pricing for manual desk
  const batchItems: ShapeBatchItem[] = (Object.keys(quantities) as ShapeType[])
    .map((type) => ({ shapeType: type, quantity: quantities[type] }))
    .filter((it) => it.quantity > 0)

  const totalCalculatedPayout = batchItems.reduce((acc, item) => {
    const base = BASE_PRICES[item.shapeType] || 0
    const mult = activeMultipliers[item.shapeType] ?? 1.0
    const finalUnit = Math.round(base * mult)
    return acc + finalUnit * item.quantity
  }, 0)

  const totalItemCount = batchItems.reduce((acc, item) => acc + item.quantity, 0)

  const handleApprovePayout = async () => {
    if (!selectedTeamId) {
      toast.error('Kérlek válassz ki egy csapatot az átvételhez!')
      return
    }
    if (batchItems.length === 0) {
      toast.error('Legalább egy termék darabszámát növeld meg a kifizetéshez!')
      return
    }

    setIsSubmitting(true)
    try {
      const res = await fetch('/api/bank', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          teamId: selectedTeamId,
          items: batchItems,
          qualityNotes: qualityNotes || undefined,
          deliveredByName: selectedParticipant?.user?.name || undefined,
          deliveredByUserId: selectedParticipantUserId || undefined,
        }),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba a banki tranzakció rögzítésekor')
      }
      onMutate?.()
      toast.success(
        `Sikeres banki átvétel! $${data.totalBatchPayout} jóváírva (${selectedTeam?.name}). Új egyenleg: $${data.newBalance}`
      )
      handleReset()
    } catch (e: any) {
      toast.error(e.message || 'Hiba a banki tranzakció rögzítésekor')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRejectDefects = () => {
    if (totalItemCount === 0) {
      toast.error('Nincs kiválasztott termék a selejtezéshez.')
      return
    }
    toast.error(
      `Selejt elutasítva (${totalItemCount} db forma). Nem történt kifizetés a Bank által.`
    )
    handleReset()
  }

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="theme-card p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-bold tracking-wider uppercase text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
                Pult Állapot: Nyitva
              </span>
              <span className="text-xs font-mono text-slate-500">Minőségátvételi &amp; Elszámoló Pult</span>
            </div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Központi Bank Minőségátvétel &amp; Pénztár
            </h2>
            <p className="text-xs text-slate-500">
              Játékosok által leadott igények ellenőrzése, személyes átvétel és azonnali virtuális kifizetés.
            </p>
          </div>

          <div className="text-right">
            <span className="text-[10px] font-mono uppercase text-slate-400 font-bold tracking-wider block">
              Függőben lévő leadások
            </span>
            <span className="text-sm font-mono font-bold text-amber-600">
              {pendingBatches.length > 0
                ? `${pendingBatches.length} db igény jóváhagyásra vár`
                : 'Minden leadás feldolgozva'}
            </span>
          </div>
        </div>
      </div>

      {/* SECTION 1: JÓVÁHAGYÁSRA VÁRÓ LEADÁSOK (KÉTLÉPCSŐS BANKI ELADÁS) */}
      <div className="theme-card p-6 space-y-4 border-2 border-amber-200/70 bg-linear-to-b from-amber-50/40 to-white">
        <div className="flex items-center justify-between pb-3 border-b border-amber-200/50">
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              {pendingBatches.length > 0 && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-3 w-3 ${pendingBatches.length > 0 ? 'bg-amber-500' : 'bg-slate-300'}`}></span>
            </span>
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-slate-900">
              Jóváhagyásra Váró Leadások ({pendingBatches.length})
            </h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            Játékos mobilról beküldött csomagok
          </span>
        </div>

        {pendingBatches.length === 0 ? (
          <div className="py-8 text-center bg-white/70 border border-dashed border-amber-200 rounded-xl space-y-1.5">
            <svg className="w-8 h-8 text-amber-400 mx-auto" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-xs font-bold text-slate-800">Nincs jóváhagyásra váró leadás</div>
            <p className="text-[11px] text-slate-500 max-w-md mx-auto">
              Amikor egy vállalat tagja a mobilján leadja az elkészített formákat, a csomag itt fog megjelenni a fizikai ellenőrzéshez és kifizetéshez.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pendingBatches.map((batch) => {
              const team = teams.find((t) => t.id === batch.teamId)
              return (
                <div
                  key={batch.batchKey}
                  className="bg-white border-2 border-amber-300/80 rounded-xl p-4 shadow-xs space-y-3 flex flex-col justify-between"
                >
                  <div>
                    {/* Header: Team & Submitter */}
                    <div className="flex items-start justify-between gap-2 pb-2 border-b border-slate-100">
                      <div>
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 block mb-1 w-max">
                          {team?.name || 'Vállalat'}
                        </span>
                        <div className="text-xs text-slate-700">
                          Átadó személy: <strong className="text-slate-900">{batch.submittedByName}</strong>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] font-mono text-slate-400 block">
                          {new Date(batch.soldAt).toLocaleTimeString('hu-HU', {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                          })}
                        </span>
                        <span className="text-xs font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                          Függőben
                        </span>
                      </div>
                    </div>

                    {/* Shapes list */}
                    <div className="mt-2.5 space-y-1">
                      <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                        Átadandó Formák ({batch.totalQuantity} db):
                      </div>
                      <div className="bg-slate-50 rounded-lg p-2.5 space-y-1 text-xs">
                        {batch.items.map((item) => (
                          <div key={item.id} className="flex items-center justify-between">
                            <span className="font-medium text-slate-800">
                              {item.quantity} × {getShapeLabel(item.shapeType)}
                            </span>
                            <span className="font-mono text-slate-600 font-bold">
                              ${item.totalPayout} (${item.finalUnitPrice}/db)
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {batch.notes && (
                      <div className="mt-2 text-[11px] text-slate-500 italic bg-amber-50/50 p-2 rounded border border-amber-100">
                        Megjegyzés: {batch.notes}
                      </div>
                    )}
                  </div>

                  {/* Actions & Payout */}
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 block">Kifizetendő összeg</span>
                      <span className="text-lg font-mono font-black text-emerald-700 tabular-nums">
                        ${batch.totalPayout}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleRejectBatch(batch.batchKey)}
                        disabled={isSubmitting}
                        className="px-3 py-1.5 border border-rose-300 hover:bg-rose-50 text-rose-700 rounded-lg text-xs font-bold transition cursor-pointer disabled:opacity-40"
                      >
                        Selejt
                      </button>
                      <button
                        type="button"
                        onClick={() => handleApproveBatch(batch.batchKey, team?.name || 'Vállalat')}
                        disabled={isSubmitting}
                        className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-extrabold shadow-2xs transition cursor-pointer flex items-center gap-1.5 disabled:opacity-40"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                        </svg>
                        <span>Jóváhagyás &amp; Kifizetés</span>
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* SECTION 2: MANUÁLIS ÁTVÉTEL & FELVITEL A PULTON */}
      <div className="theme-card p-6 space-y-5">
        <div className="pb-3 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-slate-900">
              Manuális Átvétel &amp; Pénztári Bevitel
            </h3>
            <p className="text-xs text-slate-500">
              Ha a játékos közvetlenül odaviszi a formákat mobilos előzetes leadás nélkül.
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {totalItemCount} db forma kijelölve
          </span>
        </div>

        {/* Step 1: Team & Person selector */}
        <div className="space-y-3">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
            1. Válassz Értékesítő Vállalatot:
          </label>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {teams.map((team) => {
              const isSelected = team.id === selectedTeamId
              return (
                <button
                  key={team.id}
                  onClick={() => {
                    setSelectedTeamId(team.id)
                    setSelectedParticipantUserId('')
                  }}
                  type="button"
                  className={`p-3 rounded-xl text-left border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-blue-50/70 border-blue-500 ring-2 ring-blue-500/20'
                      : 'bg-white hover:bg-slate-50 border-slate-200'
                  }`}
                >
                  <div className="text-sm font-bold text-slate-900 truncate">
                    {team.name}
                  </div>
                  <div className="text-xs font-mono text-slate-600 mt-1">
                    Egyenleg: <span className="font-bold text-slate-900">${team.cashBalance}</span>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Submitter participant dropdown */}
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center gap-3">
            <label className="text-xs font-bold text-slate-700 shrink-0">
              Ki adta át a terméket a vállalatból?
            </label>
            <select
              value={selectedParticipantUserId}
              onChange={(e) => setSelectedParticipantUserId(e.target.value)}
              className="flex-1 text-xs font-semibold px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              <option value="">(Általános leadás / Nincs egyedi játékos kiválasztva)</option>
              {teamParticipants.map((p) => (
                <option key={p.id} value={p.userId || p.user?.id}>
                  {p.user?.name || 'Csapattag'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Step 2: Form matrix */}
        <div className="space-y-2 pt-2">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
            2. Átvett Formák Rögzítése &amp; Minőségi Ellenőrzés:
          </label>
          <div className="divide-y divide-slate-100">
            {SHAPES.map((shape) => {
              const count = quantities[shape.type] || 0
              const base = BASE_PRICES[shape.type]
              const mult = activeMultipliers[shape.type] ?? 1.0
              const finalUnit = Math.round(base * mult)
              const subtotal = count * finalUnit
              const hasMultiplier = mult !== 1.0

              return (
                <div
                  key={shape.type}
                  className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center shrink-0 text-slate-700">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d={shape.iconPath} />
                      </svg>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-slate-900">{shape.label}</span>
                        {hasMultiplier && (
                          <span className="text-[10px] font-mono font-bold bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded">
                            {mult > 1.0 ? `+${Math.round((mult - 1) * 100)}%` : `${Math.round((mult - 1) * 100)}%`}
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-slate-500 font-medium">{shape.spec}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end gap-6">
                    <div className="text-right">
                      <span className="text-xs text-slate-400 font-mono block">Egységár</span>
                      <span className="text-xs font-mono font-bold text-slate-700">
                        ${finalUnit}
                      </span>
                    </div>

                    <div className="flex items-center border border-slate-300 rounded-lg bg-white overflow-hidden shadow-2xs">
                      <button
                        type="button"
                        onClick={() => handleQuantityChange(shape.type, -1)}
                        disabled={count === 0}
                        className="w-9 h-9 flex items-center justify-center hover:bg-slate-100 font-mono font-bold text-slate-700 active:bg-slate-200 disabled:opacity-40 transition cursor-pointer"
                      >
                        -
                      </button>
                      <span className="w-10 text-center font-mono font-bold text-sm text-slate-900 tabular-nums">
                        {count}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleQuantityChange(shape.type, 1)}
                        className="w-9 h-9 flex items-center justify-center hover:bg-slate-100 font-mono font-bold text-slate-700 active:bg-slate-200 transition cursor-pointer"
                      >
                        +
                      </button>
                    </div>

                    <div className="w-20 text-right font-mono font-bold text-sm text-slate-900 tabular-nums">
                      ${subtotal}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Quality Notes */}
        <div className="pt-2">
          <input
            type="text"
            placeholder="Minőségi feljegyzés (pl. '1 db enyhén hullámos éllel elfogadva')"
            value={qualityNotes}
            onChange={(e) => setQualityNotes(e.target.value)}
            className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Bottom Checkout Action Bar */}
        <div className="pt-4 border-t border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-xs text-slate-500 font-medium block">
              Kifizetendő összeg ide: <strong className="text-slate-800">{selectedTeam?.name}</strong>
              {selectedParticipant && (
                <span className="text-slate-600 font-semibold ml-1">
                  (Átadó: {selectedParticipant.user?.name})
                </span>
              )}
            </span>
            <div className="text-3xl font-mono font-bold text-slate-900 tabular-nums">
              ${totalCalculatedPayout}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleRejectDefects}
              disabled={isSubmitting || totalItemCount === 0}
              className="px-4 py-2.5 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold disabled:opacity-40 transition cursor-pointer"
            >
              Selejt Elutasítása
            </button>
            <button
              type="button"
              onClick={handleApprovePayout}
              disabled={isSubmitting || totalCalculatedPayout === 0}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-lg text-xs font-bold shadow-xs transition cursor-pointer flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              <span>{isSubmitting ? 'Kifizetés...' : 'Minőség Elfogadása & Kifizetés'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* SECTION 3: AUDIT LOG */}
      {recentSales.length > 0 && (
        <div className="theme-card p-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
            Legutóbbi Banki Elszámolások &amp; Kifizetések (Audit Napló)
          </h4>
          <div className="divide-y divide-slate-100 text-xs">
            {recentSales.slice(0, 8).map((sale) => {
              const team = teams.find((t) => t.id === sale.teamId)
              const isApproved = sale.status === 'APPROVED' || !sale.status
              const isPending = sale.status === 'PENDING'
              const isRejected = sale.status === 'REJECTED'

              return (
                <div key={sale.id} className="py-2.5 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="font-mono text-slate-400">
                      {new Date(sale.soldAt).toLocaleTimeString('hu-HU', {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </span>
                    <span className="font-semibold text-slate-800">{team?.name || 'Vállalat'}</span>
                    <span className="text-slate-600">
                      {sale.quantity} db {getShapeLabel(sale.shapeType)}
                    </span>
                    {sale.submittedByName && (
                      <span className="text-slate-500 text-[11px] bg-slate-100 px-1.5 py-0.5 rounded">
                        Átadta: {sale.submittedByName}
                      </span>
                    )}
                    {sale.qualityNotes && (
                      <span className="text-slate-400 italic truncate max-w-xs">
                        ({sale.qualityNotes})
                      </span>
                    )}
                  </div>
                  <div>
                    {isApproved && (
                      <span className="font-mono font-bold text-emerald-700">
                        +${sale.totalPayout}
                      </span>
                    )}
                    {isPending && (
                      <span className="font-mono font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                        Függőben (${sale.totalPayout})
                      </span>
                    )}
                    {isRejected && (
                      <span className="font-mono font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                        Elutasítva ($0)
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
