'use client'

import { useState } from 'react'
import { ResourceBundle } from '@/modules/trade/actions'
import { getTradeStatusLabel } from '@/modules/session/constants'
import toast from 'react-hot-toast'

interface TeamParticipantSummary {
  id: string
  userId: string
  user?: {
    id: string
    name: string
  }
}

interface TeamSummary {
  id: string
  name: string
  profileCode: string
  cashBalance: number
  paperSheets: number
  scissorsCount: number
  rulersCount: number
  templatesCount: number
  participants?: TeamParticipantSummary[]
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

interface P2PTradeCenterProps {
  sessionId: string
  myTeam: TeamSummary
  allTeams: TeamSummary[]
  trades: TradeItem[]
  onMutate?: () => void
}

const emptyBundle: ResourceBundle = {
  cash: 0,
  paperSheets: 0,
  scissorsCount: 0,
  rulersCount: 0,
  templatesCount: 0,
}

export default function P2PTradeCenter({
  sessionId,
  myTeam,
  allTeams,
  trades = [],
  onMutate,
}: P2PTradeCenterProps) {
  const otherTeams = allTeams.filter((t) => t.id !== myTeam.id)
  const myParticipants = myTeam.participants || []

  const [targetTeamId, setTargetTeamId] = useState<string>(otherTeams[0]?.id || '')
  const [selectedSenderParticipantId, setSelectedSenderParticipantId] = useState<string>('')
  const [selectedReceiverParticipantMap, setSelectedReceiverParticipantMap] = useState<Record<string, string>>({})
  const [offered, setOffered] = useState<ResourceBundle>({ ...emptyBundle })
  const [requested, setRequested] = useState<ResourceBundle>({ ...emptyBundle })
  const [notes, setNotes] = useState<string>('')
  const [loadingAction, setLoadingAction] = useState<boolean>(false)

  // Inbound pending offers
  const inboundPending = trades.filter(
    (t) => t.receiverTeamId === myTeam.id && t.status === 'PENDING'
  )

  // Outbound pending offers
  const outboundPending = trades.filter(
    (t) => t.senderTeamId === myTeam.id && t.status === 'PENDING'
  )

  // Resolved trades
  const resolvedTrades = trades.filter((t) => t.status !== 'PENDING')

  const handleCreateOffer = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!targetTeamId) {
      toast.error('Kérlek válassz ki egy partner vállalatot!')
      return
    }

    // Check our balance
    if (offered.cash > myTeam.cashBalance) {
      toast.error(`Nincs elegendő készpénzed az ajánlathoz (Egyenleged: $${myTeam.cashBalance})`)
      return
    }
    if (offered.paperSheets > myTeam.paperSheets) {
      toast.error(`Nincs elegendő papírod az ajánlathoz (Készlet: ${myTeam.paperSheets} lap)`)
      return
    }
    if (offered.scissorsCount > myTeam.scissorsCount) {
      toast.error(`Nincs elegendő ollód az ajánlathoz (Készlet: ${myTeam.scissorsCount} db)`)
      return
    }

    const senderPart = myParticipants.find(
      (p) => p.userId === selectedSenderParticipantId || p.user?.id === selectedSenderParticipantId
    )

    setLoadingAction(true)
    try {
      const res = await fetch('/api/trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'create',
          sessionId,
          senderTeamId: myTeam.id,
          receiverTeamId: targetTeamId,
          createdByName: senderPart?.user?.name || undefined,
          createdByUserId: senderPart?.user?.id || selectedSenderParticipantId || undefined,
          offered,
          requested,
          notes,
        }),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba az ajánlat létrehozásakor')
      }
      onMutate?.()
      toast.success('Hivatalos kereskedelmi ajánlat elküldve! A felkínált javak zárolásra kerültek.')
      setOffered({ ...emptyBundle })
      setRequested({ ...emptyBundle })
      setNotes('')
    } catch (e: any) {
      toast.error(e.message || 'Hiba az ajánlat létrehozásakor')
    } finally {
      setLoadingAction(false)
    }
  }

  const handleAccept = async (tradeId: string) => {
    const receiverPartId = selectedReceiverParticipantMap[tradeId] || ''
    const receiverPart = myParticipants.find(
      (p) => p.userId === receiverPartId || p.user?.id === receiverPartId
    )

    setLoadingAction(true)
    try {
      const res = await fetch('/api/trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'accept',
          sessionId,
          tradeId,
          receiverTeamId: myTeam.id,
          acceptedByName: receiverPart?.user?.name || undefined,
          acceptedByUserId: receiverPart?.user?.id || receiverPartId || undefined,
        }),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba az ajánlat elfogadásakor')
      }
      onMutate?.()
      toast.success('Üzlet létrejött! A javak jóváírásra és átadásra kerültek.')
    } catch (e: any) {
      toast.error(e.message || 'Hiba az ajánlat elfogadásakor')
    } finally {
      setLoadingAction(false)
    }
  }

  const handleReject = async (tradeId: string) => {
    setLoadingAction(true)
    try {
      const res = await fetch('/api/trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'reject',
          sessionId,
          tradeId,
          receiverTeamId: myTeam.id,
        }),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba az ajánlat elutasításakor')
      }
      onMutate?.()
      toast('Ajánlat elutasítva. A zárolt letét visszakerült a küldőhöz.')
    } catch (e: any) {
      toast.error(e.message || 'Hiba az ajánlat elutasításakor')
    } finally {
      setLoadingAction(false)
    }
  }

  const handleCancel = async (tradeId: string) => {
    setLoadingAction(true)
    try {
      const res = await fetch('/api/trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'cancel',
          sessionId,
          tradeId,
          senderTeamId: myTeam.id,
        }),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba az ajánlat visszavonásakor')
      }
      onMutate?.()
      toast.success('Ajánlat visszavonva! A letétbe helyezett javak visszakerültek a készletedbe.')
    } catch (e: any) {
      toast.error(e.message || 'Hiba az ajánlat visszavonásakor')
    } finally {
      setLoadingAction(false)
    }
  }

  const handleCounterOffer = (trade: TradeItem) => {
    try {
      const origOffered: ResourceBundle = JSON.parse(trade.offeredItems)
      const origRequested: ResourceBundle = JSON.parse(trade.requestedItems)
      setTargetTeamId(trade.senderTeamId)
      setOffered(origRequested)
      setRequested(origOffered)
      setNotes(`Ellenajánlat a #${trade.id.slice(0, 5)} ügyletre`)
      toast('Ajánlatszerkesztő kitöltve ellenajánlathoz!')
    } catch (err) {
      console.warn('Error setting counter offer', err)
    }
  }

  const renderBundleText = (jsonStr: string) => {
    try {
      const b: ResourceBundle = JSON.parse(jsonStr)
      const parts = []
      if (b.cash > 0) parts.push(`$${b.cash}`)
      if (b.paperSheets > 0) parts.push(`${b.paperSheets} lap papír`)
      if (b.scissorsCount > 0) parts.push(`${b.scissorsCount} db olló`)
      if (b.rulersCount > 0) parts.push(`${b.rulersCount} db vonalzó`)
      if (b.templatesCount > 0) parts.push(`${b.templatesCount} db sablon`)
      return parts.length > 0 ? parts.join(' + ') : 'Nincs megadva tétel'
    } catch {
      return 'Hibás tételadat'
    }
  }

  return (
    <div className="space-y-6">
      {/* 1. Inbound Pending Offers (Priority Alert) */}
      <div className="theme-card p-6 space-y-4">
        <div className="flex justify-between items-center pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-blue-600"></span>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Beérkező Kereskedelmi Ajánlatok ({inboundPending.length})
            </h3>
          </div>
          {inboundPending.length > 0 && (
            <span className="text-[10px] font-mono font-bold bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-200">
              Jóváhagyásra Vár
            </span>
          )}
        </div>

        {inboundPending.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-400">
            Nincs aktív beérkező kereskedelmi ajánlatod.
          </div>
        ) : (
          <div className="space-y-3">
            {inboundPending.map((trade) => {
              const sender = allTeams.find((t) => t.id === trade.senderTeamId)
              return (
                <div
                  key={trade.id}
                  className="p-4 rounded-xl border border-blue-200 bg-blue-50/40 space-y-3"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs font-bold text-slate-900">
                        {sender?.name || 'Partner Vállalat'} ajánlata
                      </span>
                      {trade.createdByName && (
                        <span className="text-xs text-blue-700 font-semibold ml-2">
                          (Átadó: {trade.createdByName})
                        </span>
                      )}
                      <span className="text-[10px] font-mono text-slate-400 ml-2">
                        {new Date(trade.createdAt).toLocaleTimeString('hu-HU', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono uppercase font-bold bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                      Letét Zárolva
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs bg-white p-3 rounded-lg border border-slate-200">
                    <div>
                      <span className="text-[10px] font-mono uppercase text-slate-400 block font-bold">
                        Amit ők adnak nekünk:
                      </span>
                      <span className="font-semibold text-emerald-700 block mt-0.5">
                        {renderBundleText(trade.offeredItems)}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-slate-400 block font-bold">
                        Amit cserébe kérnek tőlünk:
                      </span>
                      <span className="font-semibold text-slate-800 block mt-0.5">
                        {renderBundleText(trade.requestedItems)}
                      </span>
                    </div>
                  </div>

                  {trade.notes && (
                    <p className="text-[11px] text-slate-600 italic">
                      Megjegyzés: &ldquo;{trade.notes}&rdquo;
                    </p>
                  )}

                  {/* Who takes receipt in our team? */}
                  {myParticipants.length > 0 && (
                    <div className="flex items-center gap-2 pt-1 text-xs">
                      <span className="text-slate-600 font-medium shrink-0">
                        Ki vette át az ajánlatot nálunk?
                      </span>
                      <select
                        value={selectedReceiverParticipantMap[trade.id] || ''}
                        onChange={(e) =>
                          setSelectedReceiverParticipantMap((prev) => ({
                            ...prev,
                            [trade.id]: e.target.value,
                          }))
                        }
                        className="text-xs font-semibold px-2 py-1 bg-white border border-slate-300 rounded text-slate-800 cursor-pointer"
                      >
                        <option value="">(Általános átvétel / Nincs megadva)</option>
                        {myParticipants.map((p) => (
                          <option key={p.id} value={p.userId || p.user?.id}>
                            {p.user?.name || 'Csapattag'}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  <div className="flex items-center justify-end gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => handleCounterOffer(trade)}
                      className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-900 font-semibold"
                    >
                      Ellenajánlat
                    </button>
                    <button
                      type="button"
                      onClick={() => handleReject(trade.id)}
                      disabled={loadingAction}
                      className="px-3.5 py-1.5 border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold"
                    >
                      Elutasítás
                    </button>
                    <button
                      type="button"
                      onClick={() => handleAccept(trade.id)}
                      disabled={loadingAction}
                      className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-xs flex items-center gap-1.5"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                      <span>Ajánlat Átvétele &amp; Elfogadása</span>
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* 2. Outbound Proposal Builder */}
      <div className="theme-card p-6 space-y-4">
        <div className="pb-3 border-b border-slate-100">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Új Kereskedelmi Ajánlat Indítása
          </h3>
          <p className="text-xs text-slate-500">
            A felajánlott tételek azonnal letéti zárolásra kerülnek a készletedből.
          </p>
        </div>

        <form onSubmit={handleCreateOffer} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Cél Partner Vállalat Kiválasztása
              </label>
              <select
                value={targetTeamId}
                onChange={(e) => setTargetTeamId(e.target.value)}
                className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
              >
                {otherTeams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>

            {myParticipants.length > 0 && (
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Ki küldi / adja át az ajánlatot a csapatból?
                </label>
                <select
                  value={selectedSenderParticipantId}
                  onChange={(e) => setSelectedSenderParticipantId(e.target.value)}
                  className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
                >
                  <option value="">(Csapat nevében / Általános)</option>
                  {myParticipants.map((p) => (
                    <option key={p.id} value={p.userId || p.user?.id}>
                      {p.user?.name || 'Csapattag'}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* 2 Columns: We Offer vs We Request */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left: What We Offer */}
            <div className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-2.5">
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-700 block">
                Amit tőlünk felajánlunk (Letéti zárolás):
              </span>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <label className="text-[10px] text-slate-500 font-medium block">
                    Készpénz ($) · Max: ${myTeam.cashBalance}
                  </label>
                  <input
                    type="number"
                    min="0"
                    max={myTeam.cashBalance}
                    value={offered.cash}
                    onChange={(e) => setOffered({ ...offered, cash: parseInt(e.target.value) || 0 })}
                    className="w-full text-xs font-mono px-2 py-1.5 bg-white border border-slate-200 rounded text-slate-900"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 font-medium block">
                    A4 Lapok · Max: {myTeam.paperSheets}
                  </label>
                  <input
                    type="number"
                    min="0"
                    max={myTeam.paperSheets}
                    value={offered.paperSheets}
                    onChange={(e) => setOffered({ ...offered, paperSheets: parseInt(e.target.value) || 0 })}
                    className="w-full text-xs font-mono px-2 py-1.5 bg-white border border-slate-200 rounded text-slate-900"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 font-medium block">
                    Olló (db) · Max: {myTeam.scissorsCount}
                  </label>
                  <input
                    type="number"
                    min="0"
                    max={myTeam.scissorsCount}
                    value={offered.scissorsCount}
                    onChange={(e) => setOffered({ ...offered, scissorsCount: parseInt(e.target.value) || 0 })}
                    className="w-full text-xs font-mono px-2 py-1.5 bg-white border border-slate-200 rounded text-slate-900"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 font-medium block">
                    Vonalzó (db) · Max: {myTeam.rulersCount}
                  </label>
                  <input
                    type="number"
                    min="0"
                    max={myTeam.rulersCount}
                    value={offered.rulersCount}
                    onChange={(e) => setOffered({ ...offered, rulersCount: parseInt(e.target.value) || 0 })}
                    className="w-full text-xs font-mono px-2 py-1.5 bg-white border border-slate-200 rounded text-slate-900"
                  />
                </div>
                <div className="col-span-2">
                  <label className="text-[10px] text-slate-500 font-medium block">
                    Sablon (db) · Max: {myTeam.templatesCount}
                  </label>
                  <input
                    type="number"
                    min="0"
                    max={myTeam.templatesCount}
                    value={offered.templatesCount}
                    onChange={(e) => setOffered({ ...offered, templatesCount: parseInt(e.target.value) || 0 })}
                    className="w-full text-xs font-mono px-2 py-1.5 bg-white border border-slate-200 rounded text-slate-900"
                  />
                </div>
              </div>
            </div>

            {/* Right: What We Request */}
            <div className="p-4 bg-blue-50/40 border border-blue-200 rounded-xl space-y-2.5">
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-blue-900 block">
                Amit cserébe kérünk a partnertől:
              </span>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <label className="text-[10px] text-slate-500 font-medium block">
                    Készpénz ($)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={requested.cash}
                    onChange={(e) => setRequested({ ...requested, cash: parseInt(e.target.value) || 0 })}
                    className="w-full text-xs font-mono px-2 py-1.5 bg-white border border-slate-200 rounded text-slate-900"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 font-medium block">
                    A4 Lapok (db)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={requested.paperSheets}
                    onChange={(e) => setRequested({ ...requested, paperSheets: parseInt(e.target.value) || 0 })}
                    className="w-full text-xs font-mono px-2 py-1.5 bg-white border border-slate-200 rounded text-slate-900"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 font-medium block">
                    Olló (db)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={requested.scissorsCount}
                    onChange={(e) => setRequested({ ...requested, scissorsCount: parseInt(e.target.value) || 0 })}
                    className="w-full text-xs font-mono px-2 py-1.5 bg-white border border-slate-200 rounded text-slate-900"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 font-medium block">
                    Vonalzó (db)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={requested.rulersCount}
                    onChange={(e) => setRequested({ ...requested, rulersCount: parseInt(e.target.value) || 0 })}
                    className="w-full text-xs font-mono px-2 py-1.5 bg-white border border-slate-200 rounded text-slate-900"
                  />
                </div>
                <div className="col-span-2">
                  <label className="text-[10px] text-slate-500 font-medium block">
                    Sablon (db)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={requested.templatesCount}
                    onChange={(e) => setRequested({ ...requested, templatesCount: parseInt(e.target.value) || 0 })}
                    className="w-full text-xs font-mono px-2 py-1.5 bg-white border border-slate-200 rounded text-slate-900"
                  />
                </div>
              </div>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Üzenet a partner felé (opcionális)
            </label>
            <input
              type="text"
              placeholder="pl. 'Kész formákat szállítunk cserébe, ha adtok vonalzót'"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={loadingAction}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-xs cursor-pointer flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
              <span>Ajánlat Küldése &amp; Letét Zárolása</span>
            </button>
          </div>
        </form>
      </div>

      {/* 3. Outbound Pending Offers */}
      {outboundPending.length > 0 && (
        <div className="theme-card p-6 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Kiküldött Nyitott Ajánlataink ({outboundPending.length})
          </h4>
          <div className="divide-y divide-slate-100 text-xs">
            {outboundPending.map((trade) => {
              const receiver = allTeams.find((t) => t.id === trade.receiverTeamId)
              return (
                <div
                  key={trade.id}
                  className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div>
                    <span className="font-semibold text-slate-900">
                      Címzett: {receiver?.name || 'Partner'}
                    </span>
                    {trade.createdByName && (
                      <span className="text-[11px] text-slate-500 ml-1.5">
                        (Átadó: {trade.createdByName})
                      </span>
                    )}
                    <span className="text-slate-500 ml-2">
                      (Felkínált: {renderBundleText(trade.offeredItems)})
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleCancel(trade.id)}
                    disabled={loadingAction}
                    className="px-3 py-1 text-xs text-red-600 hover:text-red-700 border border-red-200 hover:bg-red-50 rounded font-semibold cursor-pointer"
                  >
                    Visszavonás
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 4. Resolved Trade History */}
      {resolvedTrades.length > 0 && (
        <div className="theme-card p-6 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Kereskedelmi Történet (Személyes Átadások)
          </h4>
          <div className="divide-y divide-slate-100 text-xs">
            {resolvedTrades.slice(0, 8).map((t) => {
              const isSender = t.senderTeamId === myTeam.id
              const partner = allTeams.find((tm) => tm.id === (isSender ? t.receiverTeamId : t.senderTeamId))
              return (
                <div key={t.id} className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-slate-400">
                        {new Date(t.createdAt).toLocaleTimeString('hu-HU', { hour: '2-digit', minute: '2-digit' })}
                      </span>
                      <span className="font-semibold text-slate-800">
                        {isSender ? `Küldve neki: ${partner?.name}` : `Érkezett tőle: ${partner?.name}`}
                      </span>
                    </div>

                    {(t.createdByName || t.acceptedByName) && (
                      <div className="text-[11px] text-blue-700 mt-0.5">
                        {t.createdByName && t.acceptedByName
                          ? `${t.createdByName} átadta neki: ${t.acceptedByName}`
                          : t.acceptedByName
                          ? `Átvevő: ${t.acceptedByName}`
                          : `Leadó: ${t.createdByName}`}
                      </div>
                    )}
                  </div>
                  <span
                    className={`font-mono font-bold text-[10px] px-2 py-0.5 rounded w-max ${
                      t.status === 'ACCEPTED'
                        ? 'bg-emerald-100 text-emerald-800'
                        : t.status === 'CANCELLED'
                        ? 'bg-slate-100 text-slate-600'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {getTradeStatusLabel(t.status)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
