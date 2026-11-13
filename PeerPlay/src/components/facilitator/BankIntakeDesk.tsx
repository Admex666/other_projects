'use client'

import { useState } from 'react'
import { executeBatchBankSale } from '@/modules/bank/actions'
import {
  ShapeType,
  ShapeBatchItem,
  BASE_PRICES,
} from '@/modules/bank/constants'

import toast from 'react-hot-toast'

interface TeamInfo {
  id: string
  name: string
  profileCode: string
  cashBalance: number
}

interface BankSaleRecord {
  id: string
  teamId: string
  shapeType: string
  quantity: number
  unitBasePrice: number
  multiplier: number
  finalUnitPrice: number
  totalPayout: number
  qualityNotes?: string | null
  soldAt: string | Date
}

interface BankIntakeDeskProps {
  sessionId: string
  teams: TeamInfo[]
  activeMultipliers?: Record<string, number>
  recentSales?: BankSaleRecord[]
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
}: BankIntakeDeskProps) {
  const [selectedTeamId, setSelectedTeamId] = useState<string>(teams[0]?.id || '')
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
  }

  // Calculate pricing
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
      const res = await executeBatchBankSale(
        sessionId,
        selectedTeamId,
        batchItems,
        qualityNotes || undefined
      )
      toast.success(
        `Sikeres banki átvétel! $${res.totalBatchPayout} jóváírva (${selectedTeam?.name}). Új egyenleg: $${res.newBalance}`
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
              <span className="text-xs font-mono text-slate-500">S-FAC-03 Minőségátvételi Pult</span>
            </div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Központi Bank Minőségátvétel & Pénztár
            </h2>
            <p className="text-xs text-slate-500">
              Fizikai papírtermékek ellenőrzése, darabszámos jóváírás és azonnali virtuális kifizetés.
            </p>
          </div>

          <div className="text-right">
            <span className="text-[10px] font-mono uppercase text-slate-400 font-bold tracking-wider block">
              Legutóbbi Átvétel
            </span>
            <span className="text-sm font-mono font-bold text-slate-800">
              {recentSales[0]
                ? `${new Date(recentSales[0].soldAt).toLocaleTimeString('hu-HU', { hour: '2-digit', minute: '2-digit' })} · +$${recentSales[0].totalPayout}`
                : 'Még nincs leadott termék'}
            </span>
          </div>
        </div>

        {/* Team Selector Tabs */}
        <div className="mt-6">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-2">
            1. Válassz Értékesítő Vállalatot:
          </label>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {teams.map((team) => {
              const isSelected = team.id === selectedTeamId
              return (
                <button
                  key={team.id}
                  onClick={() => setSelectedTeamId(team.id)}
                  type="button"
                  className={`p-3 rounded-xl text-left border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-blue-50/70 border-blue-500 ring-2 ring-blue-500/20'
                      : 'bg-white hover:bg-slate-50 border-slate-200'
                  }`}
                >
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block truncate">
                    {team.profileCode}
                  </span>
                  <div className="text-sm font-bold text-slate-900 truncate mt-0.5">
                    {team.name}
                  </div>
                  <div className="text-xs font-mono text-slate-600 mt-1">
                    Egyenleg: <span className="font-bold text-slate-900">${team.cashBalance}</span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Product Intake Matrix */}
      <div className="theme-card p-6 space-y-4">
        <div className="flex justify-between items-center pb-3 border-b border-slate-100">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            2. Átvett Formák Rögzítése & Minőségi Ellenőrzés
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            {totalItemCount} db forma kiválasztva
          </span>
        </div>

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
                {/* Shape Info */}
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

                {/* Stepper + Subtotal */}
                <div className="flex items-center justify-between sm:justify-end gap-6">
                  <div className="text-right">
                    <span className="text-xs text-slate-400 font-mono block">Egységár</span>
                    <span className="text-xs font-mono font-bold text-slate-700">
                      ${finalUnit}
                    </span>
                  </div>

                  {/* 36x36 Steppers */}
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

                  {/* Subtotal */}
                  <div className="w-20 text-right font-mono font-bold text-sm text-slate-900 tabular-nums">
                    ${subtotal}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Quality Notes */}
        <div className="pt-3 border-t border-slate-100">
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

      {/* Audit Log Card */}
      {recentSales.length > 0 && (
        <div className="theme-card p-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
            Legutóbbi Banki Kifizetések (Audit Napló)
          </h4>
          <div className="divide-y divide-slate-100 text-xs">
            {recentSales.slice(0, 5).map((sale) => {
              const team = teams.find((t) => t.id === sale.teamId)
              return (
                <div key={sale.id} className="py-2.5 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-slate-400">
                      {new Date(sale.soldAt).toLocaleTimeString('hu-HU', {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </span>
                    <span className="font-semibold text-slate-800">{team?.name || 'Vállalat'}</span>
                    <span className="text-slate-500">
                      {sale.quantity} db {sale.shapeType}
                    </span>
                    {sale.qualityNotes && (
                      <span className="text-slate-400 italic truncate max-w-xs">
                        ({sale.qualityNotes})
                      </span>
                    )}
                  </div>
                  <div className="font-mono font-bold text-emerald-700">
                    +${sale.totalPayout}
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
