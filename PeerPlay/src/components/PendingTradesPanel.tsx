'use client'

import { useState } from 'react'
import { acceptTrade, rejectTrade, cancelTrade } from '@/modules/interaction/trade'
import { PRODUCTION_RECIPES } from '@/modules/interaction/constants'

type TradeRequest = {
    id: string
    fromUserId: string
    toUserId: string
    offeredResources: string
    requestedResources: string
    message: string | null
    status: string
    createdAt: string | Date
    fromUser: { id: string; name: string }
    toUser: { id: string; name: string }
}

type Props = {
    sessionId: string
    currentUserId: string
    trades: TradeRequest[]
}

function parseBundle(json: string): Record<string, number> {
    try { return JSON.parse(json || '{}') } catch { return {} }
}

function ResourceBadges({ bundle, flip = false }: { bundle: Record<string, number>; flip?: boolean }) {
    const labels: Record<string, string> = {
        capital: '💰 Tőke',
        rawMaterial: '🌱 Vetőmag',
        ...Object.fromEntries(
            Object.entries(PRODUCTION_RECIPES).map(([k, v]) => [k, v.name])
        )
    }
    const items = Object.entries(bundle).filter(([, qty]) => (qty || 0) > 0)
    if (items.length === 0) return <span className="text-xs text-gray-400 italic">semmi</span>
    return (
        <span className="flex flex-wrap gap-1">
            {items.map(([key, qty]) => (
                <span key={key} className={
                    flip
                        ? 'px-2 py-0.5 rounded-full text-xs font-bold border bg-red-50 border-red-200 text-red-700'
                        : 'px-2 py-0.5 rounded-full text-xs font-bold border bg-green-50 border-green-200 text-green-700'
                }>
                    {labels[key] ?? key}: {qty}
                </span>
            ))}
        </span>
    )
}

export default function PendingTradesPanel({ sessionId, currentUserId, trades }: Props) {
    const [loadingId, setLoadingId] = useState<string | null>(null)
    const [msgs, setMsgs] = useState<Record<string, string>>({})

    const incoming = trades.filter(t => t.toUserId === currentUserId && t.status === 'pending')
    const outgoing = trades.filter(t => t.fromUserId === currentUserId && t.status === 'pending')
    const history = trades.filter(t => t.status !== 'pending')

    const handle = async (action: 'accept' | 'reject' | 'cancel', trade: TradeRequest) => {
        setLoadingId(trade.id)
        try {
            if (action === 'accept') await acceptTrade(trade.id, sessionId)
            else if (action === 'reject') await rejectTrade(trade.id, sessionId)
            else await cancelTrade(trade.id, sessionId)
            setMsgs(prev => ({ ...prev, [trade.id]: action === 'accept' ? '✅ Elfogadva!' : action === 'reject' ? '❌ Elutasítva' : '🔁 Visszavonva' }))
        } catch (err: any) {
            setMsgs(prev => ({ ...prev, [trade.id]: `Hiba: ${err.message}` }))
        } finally {
            setLoadingId(null)
        }
    }

    const TradeCard = ({ trade, isIncoming }: { trade: TradeRequest; isIncoming: boolean }) => {
        const offered = parseBundle(trade.offeredResources)
        const requested = parseBundle(trade.requestedResources)
        const msg = msgs[trade.id]

        return (
            <div className={
                isIncoming
                    ? 'rounded-lg p-4 space-y-3 border-l-4 bg-green-50 border-l-green-500 border border-green-200'
                    : 'rounded-lg p-4 space-y-3 border-l-4 bg-blue-50 border-l-blue-500 border border-blue-200'
            }>
                <div className="flex items-start justify-between">
                    <div className="text-sm">
                        <span className={isIncoming ? 'font-bold text-green-800' : 'font-bold text-blue-800'}>
                            {isIncoming ? `📨 Feladó: ${trade.fromUser.name}` : `📤 Fogadó: ${trade.toUser.name}`}
                        </span>
                        {trade.message && <p className="text-xs text-gray-600 italic mt-0.5">"{trade.message}"</p>}
                    </div>
                    <span className="text-xs text-gray-500">{new Date(trade.createdAt).toLocaleTimeString()}</span>
                </div>
                <div className="text-sm space-y-2">
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-gray-600 w-16">{isIncoming ? 'Kapod:' : 'Adsz:'}</span>
                        <ResourceBadges bundle={offered} flip={false} />
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-gray-600 w-16">{isIncoming ? 'Adsz:' : 'Kapsz:'}</span>
                        <ResourceBadges bundle={requested} flip={true} />
                    </div>
                </div>
                {msg ? (
                    <p className="text-sm font-bold text-indigo-700">{msg}</p>
                ) : (
                    <div className="flex gap-2 pt-1">
                        {isIncoming ? (
                            <>
                                <button
                                    onClick={() => handle('accept', trade)}
                                    disabled={loadingId === trade.id}
                                    style={{ backgroundColor: '#16a34a', color: '#ffffff', opacity: loadingId === trade.id ? 0.5 : 1 }}
                                    className="px-4 py-1.5 text-sm font-bold rounded-lg shadow-sm cursor-pointer"
                                >
                                    {loadingId === trade.id ? '...' : '✓ Elfogad'}
                                </button>
                                <button
                                    onClick={() => handle('reject', trade)}
                                    disabled={loadingId === trade.id}
                                    style={{ backgroundColor: '#dc2626', color: '#ffffff', opacity: loadingId === trade.id ? 0.5 : 1 }}
                                    className="px-4 py-1.5 text-sm font-bold rounded-lg shadow-sm cursor-pointer"
                                >
                                    {loadingId === trade.id ? '...' : '✕ Elutasít'}
                                </button>
                            </>
                        ) : (
                            <button
                                onClick={() => handle('cancel', trade)}
                                disabled={loadingId === trade.id}
                                style={{ backgroundColor: '#4b5563', color: '#ffffff', opacity: loadingId === trade.id ? 0.5 : 1 }}
                                className="px-4 py-1.5 text-sm font-bold rounded-lg shadow-sm cursor-pointer"
                            >
                                {loadingId === trade.id ? '...' : '↩ Visszavon'}
                            </button>
                        )}
                    </div>
                )}
            </div>
        )
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-4">
            <h3 className="font-bold text-lg border-b pb-2">📬 Ajánlatok</h3>

            {/* incoming */}
            {incoming.length > 0 && (
                <div>
                    <p className="text-xs font-bold uppercase text-green-700 bg-green-100 px-3 py-1 rounded-full inline-block mb-3">📨 Bejövő ({incoming.length})</p>
                    <div className="space-y-2">
                        {incoming.map(t => <TradeCard key={t.id} trade={t} isIncoming={true} />)}
                    </div>
                </div>
            )}

            {/* outgoing */}
            {outgoing.length > 0 && (
                <div>
                    <p className="text-xs font-bold uppercase text-blue-700 bg-blue-100 px-3 py-1 rounded-full inline-block mb-3">📤 Kimenő ({outgoing.length})</p>
                    <div className="space-y-2">
                        {outgoing.map(t => <TradeCard key={t.id} trade={t} isIncoming={false} />)}
                    </div>
                </div>
            )}

            {incoming.length === 0 && outgoing.length === 0 && (
                <div className="text-center py-6">
                    <p className="text-gray-400 text-sm">📭 Nincsenek aktív ajánlataid.</p>
                    <p className="text-gray-300 text-xs mt-1">Küldj ajánlatot a 🤝 Trade fülön!</p>
                </div>
            )}

            {/* history */}
            {history.length > 0 && (
                <details className="mt-2">
                    <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600">Előzmények ({history.length})</summary>
                    <div className="mt-2 space-y-2">
                        {history.slice(0, 10).map(t => (
                            <div key={t.id} className="border border-gray-100 rounded p-3 text-xs text-gray-500">
                                <span className={`font-bold uppercase mr-2 ${t.status === 'accepted' ? 'text-green-600' : 'text-red-400'}`}>{t.status}</span>
                                {t.fromUser.name} → {t.toUser.name}
                            </div>
                        ))}
                    </div>
                </details>
            )}
        </div>
    )
}
