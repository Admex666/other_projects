'use client'

import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { getPhaseLabel, getTradeStatusLabel } from '@/modules/session/constants'
import { BASE_PRICES, ShapeType } from '@/modules/bank/constants'
import type { ResourceBundle } from '@/modules/trade/actions'

interface TeamSummary {
  id: string
  name: string
  profileCode: string
  cashBalance: number
  paperSheets: number
  scissorsCount: number
  rulersCount: number
  templatesCount: number
}

interface TradeItem {
  id: string
  sessionId: string
  senderTeamId: string
  receiverTeamId: string
  createdByName?: string | null
  createdByUserId?: string | null
  acceptedByName?: string | null
  acceptedByUserId?: string | null
  offeredItems: string
  requestedItems: string
  escrowedItems: string
  status: string
  notes?: string | null
  createdAt: string | Date
  resolvedAt?: string | Date | null
  senderTeam?: { name: string }
  receiverTeam?: { name: string }
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

interface MobileCompanionHUDProps {
  sessionId: string
  userId?: string
  userName?: string
  myTeam: TeamSummary
  allTeams: TeamSummary[]
  trades: TradeItem[]
  bankSales?: BankSaleRecord[]
  currentPhase: string
  activeEventTitle?: string | null
  activeEventDescription?: string | null
  activeMultipliers?: Record<string, number>
  onMutate?: () => void
}

const SHAPES: { type: ShapeType; label: string; spec: string }[] = [
  { type: 'SQUARE', label: 'Négyzet', spec: '10 × 10 cm' },
  { type: 'TRIANGLE', label: 'Háromszög', spec: '10 × 10 × 10 cm' },
  { type: 'CIRCLE', label: 'Kör (Sablonnal)', spec: 'Ø 10 cm' },
  { type: 'RECTANGLE', label: 'Téglalap', spec: '5 × 15 cm' },
  { type: 'PREMIUM_PACK', label: 'Prémium Csomag', spec: '2 Háromszög + 1 Négyzet' },
]

const emptyBundle: ResourceBundle = {
  cash: 0,
  paperSheets: 0,
  scissorsCount: 0,
  rulersCount: 0,
  templatesCount: 0,
}

export default function MobileCompanionHUD({
  sessionId,
  userId = '',
  userName = 'Játékos',
  myTeam,
  allTeams = [],
  trades = [],
  bankSales = [],
  currentPhase,
  activeEventTitle,
  activeEventDescription,
  activeMultipliers = {},
  onMutate,
}: MobileCompanionHUDProps) {
  const otherTeams = allTeams.filter((t) => t.id !== myTeam.id)

  const [activeTab, setActiveTab] = useState<'trade' | 'bank'>('trade')
  const [targetTeamId, setTargetTeamId] = useState<string>(otherTeams[0]?.id || '')
  const [offered, setOffered] = useState<ResourceBundle>({ ...emptyBundle })
  const [requested, setRequested] = useState<ResourceBundle>({ ...emptyBundle })
  const [notes, setNotes] = useState<string>('')
  const [loadingTrade, setLoadingTrade] = useState<boolean>(false)

  // Bank Sale state
  const [quantities, setQuantities] = useState<Record<ShapeType, number>>({
    SQUARE: 0,
    TRIANGLE: 0,
    CIRCLE: 0,
    RECTANGLE: 0,
    PREMIUM_PACK: 0,
  })
  const [bankQualityNotes, setBankQualityNotes] = useState<string>('')
  const [loadingBank, setLoadingBank] = useState<boolean>(false)

  // Sync any pre-hydration DOM interactions on mount
  useEffect(() => {
    ;(window as any).__reactHydratedHud = true

    const currentDomTab = document
      .getElementById('mobile-companion-hud-root')
      ?.getAttribute('data-active-tab') as 'trade' | 'bank' | null
    if (currentDomTab === 'trade' || currentDomTab === 'bank') {
      setActiveTab(currentDomTab)
    }

    const syncedQuantities: Record<ShapeType, number> = {
      SQUARE: 0,
      TRIANGLE: 0,
      CIRCLE: 0,
      RECTANGLE: 0,
      PREMIUM_PACK: 0,
    }
    let hasPreHydrationQty = false
    for (const s of SHAPES) {
      const el = document.getElementById(
        `qty-input-${s.type}`
      ) as HTMLInputElement | null
      if (el && el.value !== '') {
        const val = parseInt(el.value, 10) || 0
        syncedQuantities[s.type] = val
        if (val > 0) hasPreHydrationQty = true
      }
    }
    if (hasPreHydrationQty) {
      setQuantities(syncedQuantities)
    }

    const readDomNum = (id: string) => {
      const el = document.getElementById(id) as HTMLInputElement | null
      return el && el.value !== '' ? parseInt(el.value, 10) || 0 : 0
    }

    const preOffered: ResourceBundle = {
      cash: readDomNum('trade-offered-cash'),
      paperSheets: readDomNum('trade-offered-paper'),
      scissorsCount: readDomNum('trade-offered-scissors'),
      rulersCount: readDomNum('trade-offered-rulers'),
      templatesCount: readDomNum('trade-offered-templates'),
    }
    if (Object.values(preOffered).some((v) => v > 0)) {
      setOffered(preOffered)
    }

    const preRequested: ResourceBundle = {
      cash: readDomNum('trade-requested-cash'),
      paperSheets: readDomNum('trade-requested-paper'),
      scissorsCount: readDomNum('trade-requested-scissors'),
      rulersCount: readDomNum('trade-requested-rulers'),
      templatesCount: readDomNum('trade-requested-templates'),
    }
    if (Object.values(preRequested).some((v) => v > 0)) {
      setRequested(preRequested)
    }

    const onTabEvent = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail === 'trade' || detail === 'bank') {
        setActiveTab(detail)
      }
    }
    window.addEventListener('hud-tab-change', onTabEvent)

    return () => {
      ;(window as any).__reactHydratedHud = false
      window.removeEventListener('hud-tab-change', onTabEvent)
    }
  }, [])

  useEffect(() => {
    if (!targetTeamId && otherTeams.length > 0) {
      setTargetTeamId(otherTeams[0].id)
    }
  }, [otherTeams, targetTeamId])

  // Trade offer calculations
  const inboundPending = trades.filter(
    (t) => t.receiverTeamId === myTeam.id && t.status === 'PENDING'
  )
  const outboundPending = trades.filter(
    (t) => t.senderTeamId === myTeam.id && t.status === 'PENDING'
  )
  const resolvedTrades = trades.filter(
    (t) =>
      (t.senderTeamId === myTeam.id || t.receiverTeamId === myTeam.id) &&
      t.status !== 'PENDING'
  )

  // Bank sale calculations
  const expectedPayout = SHAPES.reduce((acc, s) => {
    const qty = quantities[s.type] || 0
    const base = BASE_PRICES[s.type]
    const mult = activeMultipliers[s.type] ?? 1.0
    return acc + qty * Math.round(base * mult)
  }, 0)

  // Pending bank sales for our team
  const myTeamPendingSales = bankSales.filter(
    (s) => s.teamId === myTeam.id && s.status === 'PENDING'
  )
  // Group pending sales by batchId or id
  const myPendingBatchesMap = new Map<
    string,
    {
      batchKey: string
      submittedByName: string
      soldAt: string | Date
      notes?: string | null
      items: BankSaleRecord[]
      totalPayout: number
      totalQuantity: number
    }
  >()

  for (const sale of myTeamPendingSales) {
    const key = sale.batchId || sale.id
    const existing = myPendingBatchesMap.get(key)
    if (existing) {
      existing.items.push(sale)
      existing.totalPayout += sale.totalPayout
      existing.totalQuantity += sale.quantity
    } else {
      myPendingBatchesMap.set(key, {
        batchKey: key,
        submittedByName: sale.submittedByName || userName,
        soldAt: sale.soldAt,
        notes: sale.qualityNotes,
        items: [sale],
        totalPayout: sale.totalPayout,
        totalQuantity: sale.quantity,
      })
    }
  }
  const myPendingBatches = Array.from(myPendingBatchesMap.values())

  // Approved recent sales for our team
  const myTeamApprovedSales = bankSales.filter(
    (s) => s.teamId === myTeam.id && (s.status === 'APPROVED' || !s.status)
  )

  const handleCreateTradeSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (loadingTrade) return

    const fd = new FormData(e.currentTarget)
    const chosenTarget = String(fd.get('receiverTeamId') || targetTeamId)
    if (!chosenTarget) {
      toast.error('Válassz ki egy partner vállalatot!')
      return
    }

    const getVal = (name: string, inputId: string, stateVal: number) => {
      const inputEl = document.getElementById(inputId) as HTMLInputElement | null
      const domVal = inputEl && inputEl.value !== '' ? parseInt(inputEl.value, 10) : NaN
      if (!isNaN(domVal)) return Math.max(0, domVal)
      const fdVal = fd.get(name)
      if (fdVal !== null && fdVal !== undefined && fdVal !== '') {
        const p = Number(fdVal)
        if (!isNaN(p)) return Math.max(0, p)
      }
      return Math.max(0, stateVal || 0)
    }

    const off: ResourceBundle = {
      cash: getVal('offeredCash', 'trade-offered-cash', offered.cash),
      paperSheets: getVal('offeredPaper', 'trade-offered-paper', offered.paperSheets),
      scissorsCount: getVal('offeredScissors', 'trade-offered-scissors', offered.scissorsCount),
      rulersCount: getVal('offeredRulers', 'trade-offered-rulers', offered.rulersCount),
      templatesCount: getVal('offeredTemplates', 'trade-offered-templates', offered.templatesCount),
    }

    const req: ResourceBundle = {
      cash: getVal('requestedCash', 'trade-requested-cash', requested.cash),
      paperSheets: getVal('requestedPaper', 'trade-requested-paper', requested.paperSheets),
      scissorsCount: getVal('requestedScissors', 'trade-requested-scissors', requested.scissorsCount),
      rulersCount: getVal('requestedRulers', 'trade-requested-rulers', requested.rulersCount),
      templatesCount: getVal('requestedTemplates', 'trade-requested-templates', requested.templatesCount),
    }

    const isBundleEmpty = (b: ResourceBundle) =>
      b.cash === 0 && b.paperSheets === 0 && b.scissorsCount === 0 && b.rulersCount === 0 && b.templatesCount === 0

    if (isBundleEmpty(off) && isBundleEmpty(req)) {
      toast.error('Legalább egy felajánlott vagy kért tételt meg kell adni az ajánlathoz!')
      return
    }

    setLoadingTrade(true)
    try {
      const res = await fetch('/api/trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'create',
          sessionId,
          userId,
          userName,
          createdByName: userName,
          createdByUserId: userId,
          senderTeamId: myTeam.id,
          receiverTeamId: chosenTarget,
          offered: off,
          requested: req,
          notes: String(fd.get('notes') ?? notes),
        }),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba az ajánlat küldésekor')
      }
      toast.success('Ajánlat elküldve!')
      setOffered({ ...emptyBundle })
      setRequested({ ...emptyBundle })
      setNotes('')

      const resetIds = [
        'trade-offered-cash',
        'trade-offered-paper',
        'trade-offered-scissors',
        'trade-offered-rulers',
        'trade-offered-templates',
        'trade-requested-cash',
        'trade-requested-paper',
        'trade-requested-scissors',
        'trade-requested-rulers',
        'trade-requested-templates',
      ]
      for (const id of resetIds) {
        const inp = document.getElementById(id) as HTMLInputElement | null
        if (inp) inp.value = ''
      }

      onMutate?.()
    } catch (err: any) {
      toast.error(err.message || 'Hiba az ajánlat küldésekor')
    } finally {
      setLoadingTrade(false)
    }
  }

  const handleTradeAction = async (
    action: 'accept' | 'reject' | 'cancel',
    tradeId: string
  ) => {
    setLoadingTrade(true)
    try {
      const res = await fetch('/api/trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          sessionId,
          userId,
          userName,
          acceptedByName: userName,
          acceptedByUserId: userId,
          tradeId,
          senderTeamId: myTeam.id,
          receiverTeamId: myTeam.id,
        }),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba a művelet során')
      }
      toast.success(
        action === 'accept'
          ? 'Ajánlat elfogadva! Készletek azonnal frissítve.'
          : action === 'reject'
          ? 'Ajánlat elutasítva.'
          : 'Ajánlat visszavonva.'
      )
      onMutate?.()
    } catch (err: any) {
      toast.error(err.message || 'Hiba a művelet során')
    } finally {
      setLoadingTrade(false)
    }
  }

  // 2-Step Bank Sale Request submission
  const handleBankSaleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (loadingBank) return

    const fd = new FormData(e.currentTarget)
    const itemsToSubmit = SHAPES.map((s) => {
      const inputEl = document.getElementById(`qty-input-${s.type}`) as HTMLInputElement | null
      const domQty = inputEl && inputEl.value !== '' ? parseInt(inputEl.value, 10) : NaN
      const formQty = Number(
        (!isNaN(domQty) ? domQty : null) ??
        fd.get(`qty_${s.type}`) ??
        quantities[s.type] ??
        0
      )
      return {
        shapeType: s.type,
        quantity: Math.max(0, isNaN(formQty) ? 0 : formQty),
      }
    }).filter((it) => it.quantity > 0)

    if (itemsToSubmit.length === 0) {
      toast.error('Állíts be legalább 1 db eladandó formát!')
      return
    }

    setLoadingBank(true)
    try {
      const res = await fetch('/api/bank', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'request',
          sessionId,
          teamId: myTeam.id,
          userId,
          userName,
          items: itemsToSubmit,
          qualityNotes: bankQualityNotes || undefined,
        }),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba a banki eladási igény leadásakor')
      }
      toast.success(
        'Eladási igény leadva! Kérlek vidd oda a fizikai termékeket a Bankhoz átvételre!'
      )
      setQuantities({
        SQUARE: 0,
        TRIANGLE: 0,
        CIRCLE: 0,
        RECTANGLE: 0,
        PREMIUM_PACK: 0,
      })
      setBankQualityNotes('')
      for (const s of SHAPES) {
        const inp = document.getElementById(
          `qty-input-${s.type}`
        ) as HTMLInputElement | null
        if (inp) inp.value = ''
      }
      const expEl = document.getElementById('bank-expected-payout')
      if (expEl) expEl.textContent = '$0'
      const btnLabel = document.getElementById('bank-submit-label')
      if (btnLabel) btnLabel.textContent = 'Eladási Igény Leadása a Banknak ($0)'
      const submitBtn = document.getElementById('bank-submit-btn') as HTMLButtonElement | null
      if (submitBtn) {
        submitBtn.disabled = true
        submitBtn.classList.add('bg-slate-400', 'opacity-60', 'cursor-not-allowed')
        submitBtn.classList.remove('bg-emerald-600', 'hover:bg-emerald-700', 'active:bg-emerald-800')
      }
      onMutate?.()
    } catch (err: any) {
      toast.error(err.message || 'Hiba a banki eladási igény leadásakor')
    } finally {
      setLoadingBank(false)
    }
  }

  const stepOffered = (
    field: keyof ResourceBundle,
    delta: number,
    maxVal: number,
    inputId: string
  ) => {
    setOffered((prev) => {
      const el = document.getElementById(inputId) as HTMLInputElement | null
      const domVal = el && el.value !== '' ? parseInt(el.value, 10) : NaN
      const baseVal = !isNaN(domVal) ? domVal : (prev[field] ?? 0)
      const nextVal = Math.max(0, Math.min(maxVal, baseVal + delta))
      if (el) el.value = nextVal === 0 ? '' : String(nextVal)
      return { ...prev, [field]: nextVal }
    })
  }

  const stepRequested = (
    field: keyof ResourceBundle,
    delta: number,
    inputId: string
  ) => {
    setRequested((prev) => {
      const el = document.getElementById(inputId) as HTMLInputElement | null
      const domVal = el && el.value !== '' ? parseInt(el.value, 10) : NaN
      const baseVal = !isNaN(domVal) ? domVal : (prev[field] ?? 0)
      const nextVal = Math.max(0, baseVal + delta)
      if (el) el.value = nextVal === 0 ? '' : String(nextVal)
      return { ...prev, [field]: nextVal }
    })
  }

  const stepQuantity = (shape: ShapeType, delta: number) => {
    setQuantities((prev) => {
      const el = document.getElementById(`qty-input-${shape}`) as HTMLInputElement | null
      const domVal = el && el.value !== '' ? parseInt(el.value, 10) : NaN
      const baseVal = !isNaN(domVal) ? domVal : (prev[shape] ?? 0)
      const nextVal = Math.max(0, baseVal + delta)
      if (el) el.value = nextVal === 0 ? '' : String(nextVal)
      return { ...prev, [shape]: nextVal }
    })
  }

  const renderBundleText = (jsonStr: string) => {
    try {
      const b: ResourceBundle = JSON.parse(jsonStr)
      const parts: string[] = []
      if (b.cash > 0) parts.push(`$${b.cash}`)
      if (b.paperSheets > 0) parts.push(`${b.paperSheets} lap`)
      if (b.scissorsCount > 0) parts.push(`${b.scissorsCount} olló`)
      if (b.rulersCount > 0) parts.push(`${b.rulersCount} vonalzó`)
      if (b.templatesCount > 0) parts.push(`${b.templatesCount} sablon`)
      return parts.length > 0 ? parts.join(', ') : 'Üres'
    } catch {
      return jsonStr
    }
  }

  return (
    <div
      id="mobile-companion-hud-root"
      data-active-tab={activeTab}
      className="space-y-4 font-sans select-none"
    >
      {/* Active Market Event Alert Banner */}
      {activeEventTitle && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-900 flex items-start gap-2.5">
          <span className="text-base leading-none">⚡</span>
          <div className="flex-1">
            <div className="text-xs font-bold uppercase tracking-wider text-amber-800">
              Piaci Esemény: {activeEventTitle}
            </div>
            {activeEventDescription && (
              <p className="text-[11px] text-amber-700 mt-0.5 leading-snug">
                {activeEventDescription}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Team Balance Summary Card */}
      <div className="p-4 rounded-xl bg-slate-900 text-white shadow-md space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
              Saját Vállalatod
            </div>
            <div className="text-base font-extrabold text-white">
              {myTeam.name}
            </div>
            <div className="text-[11px] text-slate-300">
              Bejelentkezve: <strong className="text-white">{userName}</strong>
            </div>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
              Készpénz
            </span>
            <span className="text-2xl font-mono font-black text-emerald-400">
              ${myTeam.cashBalance}
            </span>
          </div>
        </div>

        {/* Inventory pill row */}
        <div className="grid grid-cols-4 gap-1.5 pt-2 border-t border-slate-800 text-center font-mono">
          <div className="bg-slate-800/80 rounded-lg p-1.5">
            <span className="text-[9px] uppercase text-slate-400 block">Papír</span>
            <span className="text-xs font-bold text-slate-100">
              {myTeam.paperSheets}
            </span>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-1.5">
            <span className="text-[9px] uppercase text-slate-400 block">Olló</span>
            <span className="text-xs font-bold text-slate-100">
              {myTeam.scissorsCount}
            </span>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-1.5">
            <span className="text-[9px] uppercase text-slate-400 block">Vonalzó</span>
            <span className="text-xs font-bold text-slate-100">
              {myTeam.rulersCount}
            </span>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-1.5">
            <span className="text-[9px] uppercase text-slate-400 block">Sablon</span>
            <span className="text-xs font-bold text-slate-100">
              {myTeam.templatesCount}
            </span>
          </div>
        </div>
      </div>

      {/* 2-TAB SWITCHER (NO QR CODE TAB) */}
      <div
        role="tablist"
        className="grid grid-cols-2 p-1 bg-slate-200 rounded-xl text-xs font-bold"
      >
        <button
          id="hud-tab-btn-trade"
          type="button"
          role="tab"
          data-hud-tab="trade"
          aria-selected={activeTab === 'trade'}
          onClick={() => setActiveTab('trade')}
          className={`py-2.5 px-2 rounded-lg transition cursor-pointer flex items-center justify-center gap-1.5 select-none ${
            activeTab === 'trade'
              ? 'bg-white text-blue-600 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <span>Csereüzlet</span>
          {inboundPending.length > 0 && (
            <span className="w-2 h-2 rounded-full bg-blue-600"></span>
          )}
        </button>

        <button
          id="hud-tab-btn-bank"
          type="button"
          role="tab"
          data-hud-tab="bank"
          aria-selected={activeTab === 'bank'}
          onClick={() => setActiveTab('bank')}
          className={`py-2.5 px-2 rounded-lg transition cursor-pointer flex items-center justify-center gap-1.5 select-none ${
            activeTab === 'bank'
              ? 'bg-white text-emerald-700 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <span>Banki Eladás &amp; Árfolyamok</span>
          {myPendingBatches.length > 0 && (
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
          )}
        </button>
      </div>

      {/* TAB 1: CSEREKERESKEDELEM */}
      <div
        id="hud-panel-trade"
        role="tabpanel"
        className={activeTab === 'trade' ? 'space-y-4 block' : 'space-y-4 hidden'}
      >
        {/* Inbound Pending Offers */}
        {inboundPending.length > 0 && (
          <div className="p-3.5 rounded-xl border-2 border-blue-400 bg-blue-50/50 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-extrabold uppercase text-blue-900">
                Beérkező Ajánlatok ({inboundPending.length})
              </span>
              <span className="text-[10px] font-mono font-bold bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                Döntésre vár
              </span>
            </div>

            {inboundPending.map((trade) => {
              const sender = allTeams.find((t) => t.id === trade.senderTeamId)
              return (
                <div
                  key={trade.id}
                  className="p-3 rounded-lg bg-white border border-blue-200 space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900">
                      Küldő: {sender?.name || 'Partner Vállalat'}
                    </span>
                    {trade.createdByName && (
                      <span className="text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                        Átadja: {trade.createdByName}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2 p-2 rounded bg-slate-50 border border-slate-100">
                    <div>
                      <span className="text-[10px] text-slate-400 font-mono uppercase block">
                        Amit kapsz:
                      </span>
                      <span className="font-bold text-emerald-700">
                        {renderBundleText(trade.offeredItems)}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 font-mono uppercase block">
                        Amit adsz:
                      </span>
                      <span className="font-bold text-slate-800">
                        {renderBundleText(trade.requestedItems)}
                      </span>
                    </div>
                  </div>

                  {trade.notes && (
                    <div className="text-[11px] italic text-slate-500">
                      „{trade.notes}”
                    </div>
                  )}

                  <div className="flex items-center gap-2 pt-1">
                    <form
                      method="POST"
                      action="/api/trade"
                      onSubmit={(e) => {
                        e.preventDefault()
                        handleTradeAction('accept', trade.id)
                      }}
                      className="flex-1"
                    >
                      <input type="hidden" name="action" value="accept" />
                      <input type="hidden" name="sessionId" value={sessionId} />
                      <input type="hidden" name="userId" value={userId} />
                      <input type="hidden" name="userName" value={userName} />
                      <input type="hidden" name="acceptedByName" value={userName} />
                      <input type="hidden" name="acceptedByUserId" value={userId} />
                      <input type="hidden" name="tradeId" value={trade.id} />
                      <input type="hidden" name="receiverTeamId" value={myTeam.id} />
                      <button
                        type="submit"
                        disabled={loadingTrade}
                        className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs cursor-pointer shadow-2xs"
                      >
                        Átvétel &amp; Elfogadás ({userName}) ✓
                      </button>
                    </form>
                    <form
                      method="POST"
                      action="/api/trade"
                      onSubmit={(e) => {
                        e.preventDefault()
                        handleTradeAction('reject', trade.id)
                      }}
                    >
                      <input type="hidden" name="action" value="reject" />
                      <input type="hidden" name="sessionId" value={sessionId} />
                      <input type="hidden" name="userId" value={userId} />
                      <input type="hidden" name="tradeId" value={trade.id} />
                      <input type="hidden" name="receiverTeamId" value={myTeam.id} />
                      <button
                        type="submit"
                        disabled={loadingTrade}
                        className="px-3 py-2 border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg font-bold text-xs cursor-pointer"
                      >
                        Elutasítás
                      </button>
                    </form>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Create Trade Offer Form */}
        <form
          method="POST"
          action="/api/trade"
          onSubmit={handleCreateTradeSubmit}
          className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-4"
        >
          <input type="hidden" name="action" value="create" />
          <input type="hidden" name="sessionId" value={sessionId} />
          <input type="hidden" name="userId" value={userId} />
          <input type="hidden" name="userName" value={userName} />
          <input type="hidden" name="createdByName" value={userName} />
          <input type="hidden" name="createdByUserId" value={userId} />
          <input type="hidden" name="senderTeamId" value={myTeam.id} />

          {/* Partner Selector */}
          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">
              Kereskedelmi Partner Vállalat:
            </label>
            <select
              name="receiverTeamId"
              value={targetTeamId}
              onChange={(e) => setTargetTeamId(e.target.value)}
              className="w-full text-xs font-semibold px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              {otherTeams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          {/* 1. Felajánlott javak */}
          <div className="space-y-2 p-2.5 rounded-lg bg-emerald-50/50 border border-emerald-200/60">
            <span className="text-[11px] font-extrabold uppercase text-emerald-900 block">
              1. Amit felajánlasz (Zárolásra kerül)
            </span>
            <div className="space-y-2 text-xs">
              {/* Cash */}
              <div className="flex items-center justify-between gap-2 py-0.5">
                <label htmlFor="trade-offered-cash" className="text-slate-700 font-medium flex-1 text-xs">
                  Készpénz ($) <span className="text-[10px] text-slate-400 block font-normal">(Max: ${myTeam.cashBalance})</span>
                </label>
                <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs">
                  <button
                    type="button"
                    data-step-target="trade-offered-cash"
                    data-step-delta="-10"
                    onClick={() =>
                      stepOffered('cash', -10, myTeam.cashBalance, 'trade-offered-cash')
                    }
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    -
                  </button>
                  <input
                    id="trade-offered-cash"
                    type="number"
                    name="offeredCash"
                    min={0}
                    max={myTeam.cashBalance}
                    step={10}
                    placeholder="0"
                    value={offered.cash === 0 ? '' : offered.cash}
                    onChange={(e) => {
                      const val = Math.max(0, Math.min(myTeam.cashBalance, parseInt(e.target.value, 10) || 0))
                      setOffered((prev) => ({ ...prev, cash: val }))
                    }}
                    className="w-16 h-10 text-center font-mono font-bold text-xs text-slate-900 bg-white border-x border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    data-step-target="trade-offered-cash"
                    data-step-delta="10"
                    data-step-max={myTeam.cashBalance}
                    onClick={() =>
                      stepOffered('cash', 10, myTeam.cashBalance, 'trade-offered-cash')
                    }
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Paper */}
              <div className="flex items-center justify-between gap-2 py-0.5">
                <label htmlFor="trade-offered-paper" className="text-slate-700 font-medium flex-1 text-xs">
                  Papírlap <span className="text-[10px] text-slate-400 block font-normal">({myTeam.paperSheets} db van)</span>
                </label>
                <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs">
                  <button
                    type="button"
                    data-step-target="trade-offered-paper"
                    data-step-delta="-1"
                    onClick={() =>
                      stepOffered('paperSheets', -1, myTeam.paperSheets, 'trade-offered-paper')
                    }
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    -
                  </button>
                  <input
                    id="trade-offered-paper"
                    type="number"
                    name="offeredPaper"
                    min={0}
                    max={myTeam.paperSheets}
                    placeholder="0"
                    value={offered.paperSheets === 0 ? '' : offered.paperSheets}
                    onChange={(e) => {
                      const val = Math.max(0, Math.min(myTeam.paperSheets, parseInt(e.target.value, 10) || 0))
                      setOffered((prev) => ({ ...prev, paperSheets: val }))
                    }}
                    className="w-14 h-10 text-center font-mono font-bold text-xs text-slate-900 bg-white border-x border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    data-step-target="trade-offered-paper"
                    data-step-delta="1"
                    data-step-max={myTeam.paperSheets}
                    onClick={() =>
                      stepOffered('paperSheets', 1, myTeam.paperSheets, 'trade-offered-paper')
                    }
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Scissors */}
              <div className="flex items-center justify-between gap-2 py-0.5">
                <label htmlFor="trade-offered-scissors" className="text-slate-700 font-medium flex-1 text-xs">
                  Olló <span className="text-[10px] text-slate-400 block font-normal">({myTeam.scissorsCount} db van)</span>
                </label>
                <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs">
                  <button
                    type="button"
                    data-step-target="trade-offered-scissors"
                    data-step-delta="-1"
                    onClick={() =>
                      stepOffered('scissorsCount', -1, myTeam.scissorsCount, 'trade-offered-scissors')
                    }
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    -
                  </button>
                  <input
                    id="trade-offered-scissors"
                    type="number"
                    name="offeredScissors"
                    min={0}
                    max={myTeam.scissorsCount}
                    placeholder="0"
                    value={offered.scissorsCount === 0 ? '' : offered.scissorsCount}
                    onChange={(e) => {
                      const val = Math.max(0, Math.min(myTeam.scissorsCount, parseInt(e.target.value, 10) || 0))
                      setOffered((prev) => ({ ...prev, scissorsCount: val }))
                    }}
                    className="w-14 h-10 text-center font-mono font-bold text-xs text-slate-900 bg-white border-x border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    data-step-target="trade-offered-scissors"
                    data-step-delta="1"
                    data-step-max={myTeam.scissorsCount}
                    onClick={() =>
                      stepOffered('scissorsCount', 1, myTeam.scissorsCount, 'trade-offered-scissors')
                    }
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Rulers */}
              <div className="flex items-center justify-between gap-2 py-0.5">
                <label htmlFor="trade-offered-rulers" className="text-slate-700 font-medium flex-1 text-xs">
                  Vonalzó <span className="text-[10px] text-slate-400 block font-normal">({myTeam.rulersCount} db van)</span>
                </label>
                <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs">
                  <button
                    type="button"
                    data-step-target="trade-offered-rulers"
                    data-step-delta="-1"
                    onClick={() =>
                      stepOffered('rulersCount', -1, myTeam.rulersCount, 'trade-offered-rulers')
                    }
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    -
                  </button>
                  <input
                    id="trade-offered-rulers"
                    type="number"
                    name="offeredRulers"
                    min={0}
                    max={myTeam.rulersCount}
                    placeholder="0"
                    value={offered.rulersCount === 0 ? '' : offered.rulersCount}
                    onChange={(e) => {
                      const val = Math.max(0, Math.min(myTeam.rulersCount, parseInt(e.target.value, 10) || 0))
                      setOffered((prev) => ({ ...prev, rulersCount: val }))
                    }}
                    className="w-14 h-10 text-center font-mono font-bold text-xs text-slate-900 bg-white border-x border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    data-step-target="trade-offered-rulers"
                    data-step-delta="1"
                    data-step-max={myTeam.rulersCount}
                    onClick={() =>
                      stepOffered('rulersCount', 1, myTeam.rulersCount, 'trade-offered-rulers')
                    }
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Templates */}
              <div className="flex items-center justify-between gap-2 py-0.5">
                <label htmlFor="trade-offered-templates" className="text-slate-700 font-medium flex-1 text-xs">
                  Sablon <span className="text-[10px] text-slate-400 block font-normal">({myTeam.templatesCount} db van)</span>
                </label>
                <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs">
                  <button
                    type="button"
                    data-step-target="trade-offered-templates"
                    data-step-delta="-1"
                    onClick={() =>
                      stepOffered('templatesCount', -1, myTeam.templatesCount, 'trade-offered-templates')
                    }
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    -
                  </button>
                  <input
                    id="trade-offered-templates"
                    type="number"
                    name="offeredTemplates"
                    min={0}
                    max={myTeam.templatesCount}
                    placeholder="0"
                    value={offered.templatesCount === 0 ? '' : offered.templatesCount}
                    onChange={(e) => {
                      const val = Math.max(0, Math.min(myTeam.templatesCount, parseInt(e.target.value, 10) || 0))
                      setOffered((prev) => ({ ...prev, templatesCount: val }))
                    }}
                    className="w-14 h-10 text-center font-mono font-bold text-xs text-slate-900 bg-white border-x border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    data-step-target="trade-offered-templates"
                    data-step-delta="1"
                    data-step-max={myTeam.templatesCount}
                    onClick={() =>
                      stepOffered('templatesCount', 1, myTeam.templatesCount, 'trade-offered-templates')
                    }
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 2. Kért javak */}
          <div className="space-y-2 p-2.5 rounded-lg bg-blue-50/50 border border-blue-200/60">
            <span className="text-[11px] font-extrabold uppercase text-blue-900 block">
              2. Amit cserébe kérsz a partnertől
            </span>
            <div className="space-y-2 text-xs">
              {/* Cash */}
              <div className="flex items-center justify-between gap-2 py-0.5">
                <label htmlFor="trade-requested-cash" className="text-slate-700 font-medium flex-1 text-xs">
                  Kért Készpénz ($)
                </label>
                <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs">
                  <button
                    type="button"
                    data-step-target="trade-requested-cash"
                    data-step-delta="-10"
                    onClick={() => stepRequested('cash', -10, 'trade-requested-cash')}
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    -
                  </button>
                  <input
                    id="trade-requested-cash"
                    type="number"
                    name="requestedCash"
                    min={0}
                    step={10}
                    placeholder="0"
                    value={requested.cash === 0 ? '' : requested.cash}
                    onChange={(e) => {
                      const val = Math.max(0, parseInt(e.target.value, 10) || 0)
                      setRequested((prev) => ({ ...prev, cash: val }))
                    }}
                    className="w-16 h-10 text-center font-mono font-bold text-xs text-slate-900 bg-white border-x border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    data-step-target="trade-requested-cash"
                    data-step-delta="10"
                    onClick={() => stepRequested('cash', 10, 'trade-requested-cash')}
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Paper */}
              <div className="flex items-center justify-between gap-2 py-0.5">
                <label htmlFor="trade-requested-paper" className="text-slate-700 font-medium flex-1 text-xs">
                  Kért Papírlap (db)
                </label>
                <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs">
                  <button
                    type="button"
                    data-step-target="trade-requested-paper"
                    data-step-delta="-1"
                    onClick={() => stepRequested('paperSheets', -1, 'trade-requested-paper')}
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    -
                  </button>
                  <input
                    id="trade-requested-paper"
                    type="number"
                    name="requestedPaper"
                    min={0}
                    placeholder="0"
                    value={requested.paperSheets === 0 ? '' : requested.paperSheets}
                    onChange={(e) => {
                      const val = Math.max(0, parseInt(e.target.value, 10) || 0)
                      setRequested((prev) => ({ ...prev, paperSheets: val }))
                    }}
                    className="w-14 h-10 text-center font-mono font-bold text-xs text-slate-900 bg-white border-x border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    data-step-target="trade-requested-paper"
                    data-step-delta="1"
                    onClick={() => stepRequested('paperSheets', 1, 'trade-requested-paper')}
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Scissors */}
              <div className="flex items-center justify-between gap-2 py-0.5">
                <label htmlFor="trade-requested-scissors" className="text-slate-700 font-medium flex-1 text-xs">
                  Kért Olló (db)
                </label>
                <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs">
                  <button
                    type="button"
                    data-step-target="trade-requested-scissors"
                    data-step-delta="-1"
                    onClick={() => stepRequested('scissorsCount', -1, 'trade-requested-scissors')}
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    -
                  </button>
                  <input
                    id="trade-requested-scissors"
                    type="number"
                    name="requestedScissors"
                    min={0}
                    placeholder="0"
                    value={requested.scissorsCount === 0 ? '' : requested.scissorsCount}
                    onChange={(e) => {
                      const val = Math.max(0, parseInt(e.target.value, 10) || 0)
                      setRequested((prev) => ({ ...prev, scissorsCount: val }))
                    }}
                    className="w-14 h-10 text-center font-mono font-bold text-xs text-slate-900 bg-white border-x border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    data-step-target="trade-requested-scissors"
                    data-step-delta="1"
                    onClick={() => stepRequested('scissorsCount', 1, 'trade-requested-scissors')}
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Rulers */}
              <div className="flex items-center justify-between gap-2 py-0.5">
                <label htmlFor="trade-requested-rulers" className="text-slate-700 font-medium flex-1 text-xs">
                  Kért Vonalzó (db)
                </label>
                <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs">
                  <button
                    type="button"
                    data-step-target="trade-requested-rulers"
                    data-step-delta="-1"
                    onClick={() => stepRequested('rulersCount', -1, 'trade-requested-rulers')}
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    -
                  </button>
                  <input
                    id="trade-requested-rulers"
                    type="number"
                    name="requestedRulers"
                    min={0}
                    placeholder="0"
                    value={requested.rulersCount === 0 ? '' : requested.rulersCount}
                    onChange={(e) => {
                      const val = Math.max(0, parseInt(e.target.value, 10) || 0)
                      setRequested((prev) => ({ ...prev, rulersCount: val }))
                    }}
                    className="w-14 h-10 text-center font-mono font-bold text-xs text-slate-900 bg-white border-x border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    data-step-target="trade-requested-rulers"
                    data-step-delta="1"
                    onClick={() => stepRequested('rulersCount', 1, 'trade-requested-rulers')}
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Templates */}
              <div className="flex items-center justify-between gap-2 py-0.5">
                <label htmlFor="trade-requested-templates" className="text-slate-700 font-medium flex-1 text-xs">
                  Kért Sablon (db)
                </label>
                <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs">
                  <button
                    type="button"
                    data-step-target="trade-requested-templates"
                    data-step-delta="-1"
                    onClick={() => stepRequested('templatesCount', -1, 'trade-requested-templates')}
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    -
                  </button>
                  <input
                    id="trade-requested-templates"
                    type="number"
                    name="requestedTemplates"
                    min={0}
                    placeholder="0"
                    value={requested.templatesCount === 0 ? '' : requested.templatesCount}
                    onChange={(e) => {
                      const val = Math.max(0, parseInt(e.target.value, 10) || 0)
                      setRequested((prev) => ({ ...prev, templatesCount: val }))
                    }}
                    className="w-14 h-10 text-center font-mono font-bold text-xs text-slate-900 bg-white border-x border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    data-step-target="trade-requested-templates"
                    data-step-delta="1"
                    onClick={() => stepRequested('templatesCount', 1, 'trade-requested-templates')}
                    className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div>
            <input
              type="text"
              name="notes"
              placeholder="Üzenet a partnernek (pl. 'Kész formákat szállítunk cserébe')"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loadingTrade}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-lg text-xs font-bold shadow-xs cursor-pointer"
          >
            {loadingTrade ? 'Küldés folyamatban...' : `Ajánlat Küldése (${userName} által)`}
          </button>
        </form>

        {/* Outbound Pending Offers */}
        {outboundPending.length > 0 && (
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-xs font-bold uppercase text-slate-700 block">
              Kiküldött Ajánlataid ({outboundPending.length})
            </span>
            {outboundPending.map((trade) => {
              const receiver = allTeams.find((t) => t.id === trade.receiverTeamId)
              return (
                <div
                  key={trade.id}
                  className="p-2.5 rounded-lg bg-white border border-slate-200 text-xs flex items-center justify-between gap-2"
                >
                  <div className="space-y-0.5">
                    <div className="font-bold text-slate-800">
                      Címzett: {receiver?.name || 'Partner'}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Adsz: {renderBundleText(trade.offeredItems)} · Kérsz: {renderBundleText(trade.requestedItems)}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleTradeAction('cancel', trade.id)}
                    className="px-2.5 py-1 text-[11px] font-bold text-rose-600 hover:bg-rose-50 rounded border border-rose-200 cursor-pointer"
                  >
                    Visszavonás
                  </button>
                </div>
              )
            })}
          </div>
        )}

        {/* Resolved Trades Log with Names */}
        {resolvedTrades.length > 0 && (
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-xs font-bold uppercase text-slate-700 block">
              Kereskedési Történet (Személyes Átadások)
            </span>
            <div className="divide-y divide-slate-200/70 text-xs">
              {resolvedTrades.slice(0, 5).map((trade) => {
                const isSender = trade.senderTeamId === myTeam.id
                const other = allTeams.find(
                  (t) => t.id === (isSender ? trade.receiverTeamId : trade.senderTeamId)
                )
                const isAccepted = trade.status === 'ACCEPTED'

                return (
                  <div key={trade.id} className="py-2 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-800">
                        {isSender ? `➔ ${other?.name}` : `⬅ ${other?.name}`}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          isAccepted
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-slate-200 text-slate-600'
                        }`}
                      >
                        {getTradeStatusLabel(trade.status)}
                      </span>
                    </div>

                    {isAccepted && (trade.createdByName || trade.acceptedByName) && (
                      <div className="text-[11px] text-blue-700 font-medium">
                        {trade.createdByName && trade.acceptedByName
                          ? `${trade.createdByName} átadta neki: ${trade.acceptedByName}`
                          : trade.acceptedByName
                          ? `Átvevő személy: ${trade.acceptedByName}`
                          : `Leadó személy: ${trade.createdByName}`}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* TAB 2: BANKI ELADÁS & ÁRFOLYAMOK */}
      <div
        id="hud-panel-bank"
        role="tabpanel"
        className={activeTab === 'bank' ? 'space-y-4 block' : 'space-y-4 hidden'}
      >
        {/* SUB-SECTION 1: SUBMIT NEW SALE REQUEST */}
        <form
          id="hud-bank-form"
          method="POST"
          action="/api/bank"
          data-session-id={sessionId}
          data-team-id={myTeam.id}
          data-team-name={myTeam.name}
          data-player-name={userName}
          data-user-id={userId}
          onSubmit={handleBankSaleSubmit}
          className="space-y-4"
        >
          <input type="hidden" name="action" value="request" />
          <input type="hidden" name="sessionId" value={sessionId} />
          <input type="hidden" name="teamId" value={myTeam.id} />
          <input type="hidden" name="userId" value={userId} />
          <input type="hidden" name="userName" value={userName} />

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div>
              <div className="flex items-center gap-1.5 mb-0.5">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  Kétlépcsős Banki Átvétel
                </span>
              </div>
              <h3 className="text-xs font-extrabold uppercase text-slate-800">
                Termékcsomag Összeállítása a Banknak
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Állítsd be a kivágott formák darabszámát, küldd be az igényt, majd vidd oda a fizikai formákat a facilitátornak ellenőrzésre!
              </p>
            </div>

            <div className="divide-y divide-slate-200/70 bg-white rounded-lg border border-slate-200 px-3">
              {SHAPES.map((s) => {
                const count = quantities[s.type] || 0
                const base = BASE_PRICES[s.type]
                const mult = activeMultipliers[s.type] ?? 1.0
                const unitPrice = Math.round(base * mult)
                return (
                  <div
                    key={s.type}
                    data-shape-row={s.type}
                    data-unit-price={unitPrice}
                    className="py-2.5 flex items-center justify-between gap-2"
                  >
                    <div className="flex-1">
                      <div className="text-xs font-bold text-slate-900">
                        {s.label}{' '}
                        <span className="font-mono text-emerald-700">${unitPrice}/db</span>
                      </div>
                      <span className="text-[10px] text-slate-400">{s.spec}</span>
                    </div>

                    <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white shadow-2xs">
                      <button
                        type="button"
                        data-shape-minus={s.type}
                        onClick={() => stepQuantity(s.type, -1)}
                        className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                      >
                        -
                      </button>
                      <input
                        id={`qty-input-${s.type}`}
                        type="number"
                        name={`qty_${s.type}`}
                        min={0}
                        placeholder="0"
                        value={count === 0 ? '' : count}
                        onChange={(e) => {
                          const val = Math.max(0, parseInt(e.target.value, 10) || 0)
                          setQuantities((prev) => ({ ...prev, [s.type]: val }))
                        }}
                        className="w-14 h-10 text-center font-mono font-bold text-xs text-slate-900 bg-white border-x border-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      />
                      <button
                        type="button"
                        data-shape-plus={s.type}
                        onClick={() => stepQuantity(s.type, 1)}
                        className="w-10 h-10 flex items-center justify-center font-mono font-bold text-lg text-slate-700 hover:bg-slate-100 active:bg-slate-200 cursor-pointer select-none"
                      >
                        +
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>

            <div>
              <input
                type="text"
                name="qualityNotes"
                placeholder="Opcionális megjegyzés a facilitátornak..."
                value={bankQualityNotes}
                onChange={(e) => setBankQualityNotes(e.target.value)}
                className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className="text-xs font-semibold text-slate-600">
                Várható kifizetés jóváhagyáskor:
              </span>
              <span
                id="bank-expected-payout"
                className="text-2xl font-mono font-black text-emerald-700"
              >
                ${expectedPayout}
              </span>
            </div>

            <button
              id="bank-submit-btn"
              type="submit"
              disabled={loadingBank || expectedPayout === 0}
              className={`w-full py-3.5 text-white rounded-xl text-sm font-extrabold shadow-sm cursor-pointer flex items-center justify-center gap-2 transition select-none ${
                expectedPayout > 0 && !loadingBank
                  ? 'bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800'
                  : 'bg-slate-400 opacity-60 cursor-not-allowed'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
              <span id="bank-submit-label">
                {loadingBank
                  ? 'Igény beküldése...'
                  : expectedPayout > 0
                  ? `Eladási Igény Leadása a Banknak (+$${expectedPayout})`
                  : 'Eladási Igény Leadása a Banknak ($0)'}
              </span>
            </button>
          </div>
        </form>

        {/* SUB-SECTION 2: JÓVÁHAGYÁSRA VÁRÓ LEADÁSOK (PENDING BANK SALES) */}
        {myPendingBatches.length > 0 && (
          <div className="p-3.5 rounded-xl border-2 border-amber-300 bg-amber-50/60 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping"></span>
                <span className="text-xs font-extrabold uppercase text-amber-900">
                  Jóváhagyásra Váró Leadásaid ({myPendingBatches.length})
                </span>
              </div>
              <span className="text-[10px] font-mono font-bold bg-amber-200/80 text-amber-900 px-2 py-0.5 rounded">
                Függőben
              </span>
            </div>

            <div className="p-2.5 rounded-lg bg-white border border-amber-200 text-xs space-y-2">
              <div className="flex items-center gap-2 text-amber-800 font-medium text-[11px]">
                <svg className="w-4 h-4 shrink-0 text-amber-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <span>
                  <strong>Fontos:</strong> Vidd oda a kivágott fizikai termékeket a Központi Bank pultjához a facilitátornak ellenőrzésre!
                </span>
              </div>

              {myPendingBatches.map((batch) => (
                <div key={batch.batchKey} className="pt-2 border-t border-slate-100 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-800">
                      {batch.items.map((it) => `${it.quantity}x ${it.shapeType}`).join(', ')}
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono">
                      Leadta: {batch.submittedByName} · {new Date(batch.soldAt).toLocaleTimeString('hu-HU', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                  <div className="font-mono font-black text-amber-700 text-sm">
                    ${batch.totalPayout}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SUB-SECTION 3: BANKI ÁRFOLYAMTÁBLA (COMMODITY EXCHANGE RATES) */}
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase text-slate-700">
              Aktuális Banki Felvásárlási Árak &amp; Szorzók
            </h4>
            <span className="text-[10px] font-mono text-slate-400">Élő árfolyam</span>
          </div>

          <div className="divide-y divide-slate-200/70 text-xs bg-white rounded-lg border border-slate-200 px-3">
            {SHAPES.map((s) => {
              const base = BASE_PRICES[s.type]
              const mult = activeMultipliers[s.type] ?? 1.0
              const finalPrice = Math.round(base * mult)
              const hasMultiplier = mult !== 1.0

              return (
                <div key={s.type} className="py-2.5 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-slate-900">{s.label}</span>
                      {hasMultiplier && (
                        <span className="text-[10px] font-mono font-bold bg-amber-100 text-amber-800 px-1.5 py-0.2 rounded">
                          {mult > 1.0 ? `+${Math.round((mult - 1) * 100)}%` : `${Math.round((mult - 1) * 100)}%`}
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-slate-400">{s.spec}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-mono font-extrabold text-sm text-slate-900">
                      ${finalPrice}
                    </span>
                    <span className="text-[10px] text-slate-400 block font-mono">/ darab</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* SUB-SECTION 4: RECENT APPROVED SALES */}
        {myTeamApprovedSales.length > 0 && (
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-xs font-bold uppercase text-slate-700 block">
              Jóváhagyott Eladások (Pénztári Bevételek)
            </span>
            <div className="divide-y divide-slate-200/70 text-xs">
              {myTeamApprovedSales.slice(0, 5).map((sale) => (
                <div key={sale.id} className="py-2 flex items-center justify-between">
                  <div>
                    <span className="font-semibold text-slate-800">
                      {sale.quantity} db {sale.shapeType}
                    </span>
                    {sale.submittedByName && (
                      <span className="text-[10px] text-slate-500 block">
                        Átadta: {sale.submittedByName}
                      </span>
                    )}
                  </div>
                  <span className="font-mono font-bold text-emerald-700">
                    +${sale.totalPayout}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Progressive Enhancement Script (2-Tab layout, NO QR) */}
      <script
        dangerouslySetInnerHTML={{
          __html: `
(function(){
  if (window.__peerplayHudBound) return;
  window.__peerplayHudBound = true;

  var TAB_STYLES = {
    trade: {
      active: 'py-2.5 px-2 rounded-lg transition cursor-pointer flex items-center justify-center gap-1.5 select-none bg-white text-blue-600 shadow-2xs',
      inactive: 'py-2.5 px-2 rounded-lg transition cursor-pointer flex items-center justify-center gap-1.5 select-none text-slate-600 hover:text-slate-900'
    },
    bank: {
      active: 'py-2.5 px-2 rounded-lg transition cursor-pointer flex items-center justify-center gap-1.5 select-none bg-white text-emerald-700 shadow-2xs',
      inactive: 'py-2.5 px-2 rounded-lg transition cursor-pointer flex items-center justify-center gap-1.5 select-none text-slate-600 hover:text-slate-900'
    }
  };

  function switchHudTab(targetTab) {
    var root = document.getElementById('mobile-companion-hud-root');
    if (root) root.setAttribute('data-active-tab', targetTab);

    var tabs = ['trade', 'bank'];
    for (var i = 0; i < tabs.length; i++) {
      var t = tabs[i];
      var panel = document.getElementById('hud-panel-' + t);
      var btn = document.getElementById('hud-tab-btn-' + t);
      if (panel) {
        panel.className = (t === targetTab) ? 'space-y-4 block' : 'space-y-4 hidden';
      }
      if (btn && TAB_STYLES[t]) {
        btn.className = (t === targetTab) ? TAB_STYLES[t].active : TAB_STYLES[t].inactive;
        btn.setAttribute('aria-selected', t === targetTab ? 'true' : 'false');
      }
    }
    try {
      window.dispatchEvent(new CustomEvent('hud-tab-change', { detail: targetTab }));
    } catch (err) {}
  }

  function recalcBankTotals() {
    var rows = document.querySelectorAll('[data-shape-row]');
    var totalPayout = 0;
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var shape = row.getAttribute('data-shape-row');
      var unitPrice = parseInt(row.getAttribute('data-unit-price') || '0', 10);
      var inp = document.getElementById('qty-input-' + shape);
      var qty = inp && inp.value !== '' ? (parseInt(inp.value, 10) || 0) : 0;
      if (qty > 0) {
        totalPayout += qty * unitPrice;
      }
    }
    var payoutEl = document.getElementById('bank-expected-payout');
    if (payoutEl) payoutEl.textContent = '$' + totalPayout;

    var submitLabel = document.getElementById('bank-submit-label');
    if (submitLabel) {
      submitLabel.textContent = totalPayout > 0
        ? 'Eladási Igény Leadása a Banknak (+$' + totalPayout + ')'
        : 'Eladási Igény Leadása a Banknak ($0)';
    }

    var submitBtn = document.getElementById('bank-submit-btn');
    if (submitBtn) {
      submitBtn.disabled = totalPayout <= 0;
      if (totalPayout > 0) {
        submitBtn.classList.remove('bg-slate-400', 'opacity-60', 'cursor-not-allowed');
        submitBtn.classList.add('bg-emerald-600', 'hover:bg-emerald-700', 'active:bg-emerald-800');
      } else {
        submitBtn.classList.add('bg-slate-400', 'opacity-60', 'cursor-not-allowed');
        submitBtn.classList.remove('bg-emerald-600', 'hover:bg-emerald-700', 'active:bg-emerald-800');
      }
    }
  }

  document.addEventListener('input', function(e) {
    var target = e.target;
    if (!target) return;
    if (target.id && target.id.indexOf('qty-input-') === 0) {
      recalcBankTotals();
    }
  });

  document.addEventListener('change', function(e) {
    var target = e.target;
    if (!target) return;
    if (target.id && target.id.indexOf('qty-input-') === 0) {
      recalcBankTotals();
    }
  });

  document.addEventListener('click', function(e) {
    var target = e.target;
    if (!target || !target.closest) return;

    var tabBtn = target.closest('[data-hud-tab]');
    if (tabBtn) {
      var tab = tabBtn.getAttribute('data-hud-tab');
      if (tab) switchHudTab(tab);
      return;
    }

    if (window.__reactHydratedHud) return;

    var minusBtn = target.closest('[data-shape-minus]');
    if (minusBtn) {
      var sMinus = minusBtn.getAttribute('data-shape-minus');
      var inpM = document.getElementById('qty-input-' + sMinus);
      if (inpM) {
        var curValM = inpM.value !== '' ? (parseInt(inpM.value, 10) || 0) : 0;
        var nextM = Math.max(0, curValM - 1);
        inpM.value = nextM === 0 ? '' : String(nextM);
        recalcBankTotals();
      }
      return;
    }

    var plusBtn = target.closest('[data-shape-plus]');
    if (plusBtn) {
      var sPlus = plusBtn.getAttribute('data-shape-plus');
      var inpP = document.getElementById('qty-input-' + sPlus);
      if (inpP) {
        var curValP = inpP.value !== '' ? (parseInt(inpP.value, 10) || 0) : 0;
        var nextP = curValP + 1;
        inpP.value = String(nextP);
        recalcBankTotals();
      }
      return;
    }

    var stepBtn = target.closest('[data-step-target]');
    if (stepBtn) {
      var tId = stepBtn.getAttribute('data-step-target');
      var delta = parseInt(stepBtn.getAttribute('data-step-delta') || '0', 10);
      var maxAttr = stepBtn.getAttribute('data-step-max');
      var inpStep = document.getElementById(tId);
      if (inpStep) {
        var curVal = inpStep.value !== '' ? (parseInt(inpStep.value, 10) || 0) : 0;
        var nextVal = Math.max(0, curVal + delta);
        if (maxAttr !== null && maxAttr !== '') {
          nextVal = Math.min(parseInt(maxAttr, 10), nextVal);
        }
        inpStep.value = nextVal === 0 ? '' : String(nextVal);
      }
      return;
    }
  });
})();
          `,
        }}
      />
    </div>
  )
}
