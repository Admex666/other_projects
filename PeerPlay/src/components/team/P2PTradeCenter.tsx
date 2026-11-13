'use client'

import { useState } from 'react'
import {
  createTradeOffer,
  acceptTradeOffer,
  rejectTradeOffer,
  cancelTradeOffer,
  ResourceBundle,
} from '@/modules/trade/actions'
import toast from 'react-hot-toast'

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
}: P2PTradeCenterProps) {
  const otherTeams = allTeams.filter((t) => t.id !== myTeam.id)

  const [targetTeamId, setTargetTeamId] = useState<string>(otherTeams[0]?.id || '')
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

    setLoadingAction(true)
    try {
      await createTradeOffer(sessionId, myTeam.id, targetTeamId, offered, requested, notes)
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
    setLoadingAction(true)
    try {
      await acceptTradeOffer(sessionId, tradeId, myTeam.id)
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
      await rejectTradeOffer(sessionId, tradeId, myTeam.id)
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
      await cancelTradeOffer(sessionId, tradeId, myTeam.id)
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
      // We flip: what they offered becomes what we request, what they requested becomes what we offer
      setOffered(origRequested)
      setRequested(origOffered)
      setNotes(`Ellenajánlat a #${trade.id.slice(0, 5)} ügyletre`)
      toast('Ajánlatszerkesztő kitöltve ellenajánlathoz!')
    } catch (err) {
      console.warn('Error setting counter offer', err)
    }
  }

  const renderBundleText = (bundleJson: string) => {
    try {
      const b: ResourceBundle = JSON.parse(bundleJson)
      const parts = []
      if (b.cash > 0) parts.push(`$${b.cash} készpénz`)
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
                      <span>Ajánlat Elfogadása</span>
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
            Új Kereskedelmi Ajánlat Indítása (Outbound Proposal)
          </h3>
          <p className="text-xs text-slate-500">
            A felajánlott tételek azonnal zárolásra kerülnek a készletedből (Immediate Escrow).
          </p>
        </div>

        <form onSubmit={handleCreateOffer} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Cél Vállalat Kiválasztása
            </label>
            <select
              value={targetTeamId}
              onChange={(e) => setTargetTeamId(e.target.value)}
              className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
            >
              {otherTeams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.profileCode})
                </option>
              ))}
            </select>
          </div>

          {/* 2 Columns: We Offer vs We Request */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left: What We Offer */}
            <div className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-2.5">
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-700 block">
                Amit tőlünk felajánlunk (Escrow zárolás):
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
            <div className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-2.5">
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-700 block">
                Amit cserébe kérünk a partnertől:
              </span>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <label className="text-[10px] text-slate-500 font-medium block">
                    Kért Készpénz ($)
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
                    Kért A4 Lapok
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
                    Kért Olló (db)
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
                    Kért Vonalzó (db)
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
                    Kért Sablon (db)
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
            <input
              type="text"
              placeholder="Üzenet / Tárgyalási megjegyzés (opcionális)"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loadingAction}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition shadow-xs flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>Hivatalos Ajánlat Továbbítása</span>
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </button>
        </form>
      </div>

      {/* 3. Outbound Pending Offers */}
      {outboundPending.length > 0 && (
        <div className="theme-card p-6 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Elküldött, Függőben Lévő Ajánlataink ({outboundPending.length})
          </h4>
          <div className="space-y-2">
            {outboundPending.map((trade) => {
              const receiver = allTeams.find((t) => t.id === trade.receiverTeamId)
              return (
                <div
                  key={trade.id}
                  className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between text-xs"
                >
                  <div>
                    <span className="font-semibold text-slate-900">
                      Címzett: {receiver?.name || 'Partner'}
                    </span>
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
                    Visszavonás (Refund)
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
            Kereskedelmi Történet
          </h4>
          <div className="divide-y divide-slate-100 text-xs">
            {resolvedTrades.slice(0, 6).map((t) => {
              const isSender = t.senderTeamId === myTeam.id
              const partner = allTeams.find((tm) => tm.id === (isSender ? t.receiverTeamId : t.senderTeamId))
              return (
                <div key={t.id} className="py-2.5 flex items-center justify-between">
                  <div>
                    <span className="font-mono text-slate-400 mr-2">
                      {new Date(t.createdAt).toLocaleTimeString('hu-HU', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <span className="font-semibold text-slate-800">
                      {isSender ? `Küldve neki: ${partner?.name}` : `Érkezett tőle: ${partner?.name}`}
                    </span>
                  </div>
                  <span
                    className={`font-mono font-bold text-[10px] px-2 py-0.5 rounded ${
                      t.status === 'ACCEPTED'
                        ? 'bg-emerald-100 text-emerald-800'
                        : t.status === 'CANCELLED'
                        ? 'bg-slate-100 text-slate-600'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {t.status}
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
