'use client'

import { useState } from 'react'
import { sendTradeRequest, ResourceBundle } from '@/modules/interaction/trade'
import { PRODUCTION_RECIPES, ProductType } from '@/modules/interaction/constants'

type Participant = {
    userId: string
    user: { id: string; name: string }
    team: { name: string } | null
}

type TradeOfferFormProps = {
    sessionId: string
    currentUserId: string
    myParticipant: {
        capital: number
        rawMaterial: number
        inventory: string
    }
    otherParticipants: Participant[]
    onSent?: () => void  // callback after successful send (e.g. switch to inbox tab)
}

const productKeys: ProductType[] = ['wheat', 'corn', 'sunflower', 'wine']

export default function TradeOfferForm({ sessionId, currentUserId, myParticipant, otherParticipants, onSent }: TradeOfferFormProps) {
    const [toUserId, setToUserId] = useState('')
    const [message, setMessage] = useState('')
    const [offered, setOffered] = useState<ResourceBundle>({})
    const [requested, setRequested] = useState<ResourceBundle>({})
    const [loading, setLoading] = useState(false)
    const [feedback, setFeedback] = useState<{ type: 'success' | 'error', text: string } | null>(null)

    const myInventory: Record<string, number> = (() => {
        try { return JSON.parse(myParticipant.inventory || '{}') } catch { return {} }
    })()

    const updateBundle = (
        bundle: ResourceBundle,
        setBundle: (b: ResourceBundle) => void,
        key: string,
        value: string,
        maxAmount?: number
    ) => {
        let num = Math.max(0, parseInt(value) || 0)
        if (maxAmount !== undefined) num = Math.min(num, maxAmount)
        setBundle({ ...bundle, [key]: num || undefined })
    }

    const handleSend = async () => {
        if (!toUserId) { setFeedback({ type: 'error', text: 'Válassz egy játékost!' }); return }
        const hasOffer = Object.values(offered).some(v => (v || 0) > 0)
        if (!hasOffer) { setFeedback({ type: 'error', text: 'Adj meg valamit az ajánlatba!' }); return }

        setLoading(true)
        setFeedback(null)
        try {
            await sendTradeRequest(sessionId, currentUserId, toUserId, offered, requested, message)
            setFeedback({ type: 'success', text: '✅ Ajánlat elküldve!' })
            setOffered({})
            setRequested({})
            setMessage('')
            setToUserId('')
            // Switch to inbox tab after a short moment so user sees the sent request
            setTimeout(() => {
                onSent?.()
                setFeedback(null)
            }, 1200)
        } catch (err: any) {
            setFeedback({ type: 'error', text: err.message || 'Sikertelen ajánlatküldés' })
        } finally {
            setLoading(false)
        }
    }

    const ResourceInputs = ({
        bundle, setBundle, label, maxValues
    }: {
        bundle: ResourceBundle
        setBundle: (b: ResourceBundle) => void
        label: string
        maxValues?: Record<string, number>
    }) => (
        <div>
            <p className="text-xs font-bold uppercase text-gray-500 mb-2">{label}</p>
            <div className="grid grid-cols-2 gap-2">
                <label className="flex flex-col gap-0.5 text-sm bg-green-50 border border-green-200 rounded px-2 py-1">
                    <div className="flex items-center justify-between">
                        <span>💰 Tőke</span>
                        <input type="number" min={0} max={maxValues?.capital ?? 99999}
                            value={bundle.capital || ''}
                            onChange={e => updateBundle(bundle, setBundle, 'capital', e.target.value, maxValues?.capital)}
                            className="w-16 text-right border-none bg-transparent outline-none text-sm font-bold" placeholder="0" />
                    </div>
                    {maxValues && <span className="text-xs text-gray-400">Max: {maxValues.capital ?? '∞'}</span>}
                </label>
                <label className="flex flex-col gap-0.5 text-sm bg-amber-50 border border-amber-200 rounded px-2 py-1">
                    <div className="flex items-center justify-between">
                        <span>🌱 Vetőmag</span>
                        <input type="number" min={0} max={maxValues?.rawMaterial ?? 999}
                            value={bundle.rawMaterial || ''}
                            onChange={e => updateBundle(bundle, setBundle, 'rawMaterial', e.target.value, maxValues?.rawMaterial)}
                            className="w-12 text-right border-none bg-transparent outline-none text-sm font-bold" placeholder="0" />
                    </div>
                    {maxValues && <span className="text-xs text-gray-400">Max: {maxValues.rawMaterial ?? '∞'}</span>}
                </label>
                {productKeys.map(k => (
                    <label key={k} className="flex flex-col gap-0.5 text-sm bg-yellow-50 border border-yellow-200 rounded px-2 py-1">
                        <div className="flex items-center justify-between">
                            <span>{PRODUCTION_RECIPES[k].name}</span>
                            <input type="number" min={0} max={maxValues ? (maxValues[k] ?? 0) : 99}
                                value={(bundle as any)[k] || ''}
                                onChange={e => updateBundle(bundle, setBundle, k, e.target.value, maxValues?.[k])}
                                className="w-10 text-right border-none bg-transparent outline-none text-sm font-bold" placeholder="0" />
                        </div>
                        {maxValues && <span className="text-xs text-gray-400">Max: {maxValues[k] ?? 0}</span>}
                    </label>
                ))}
            </div>
        </div>
    )

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="font-bold text-lg border-b pb-2 mb-4">🤝 Trade Ajánlat küldése</h3>

            {feedback && (
                <div className={`mb-4 p-3 rounded text-sm font-medium border ${feedback.type === 'success' ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
                    {feedback.text}
                </div>
            )}

            <div className="space-y-4">
                {/* Target player */}
                <div>
                    <label className="text-xs font-bold uppercase text-gray-500 block mb-1">Kinek küldöd?</label>
                    <select value={toUserId} onChange={e => setToUserId(e.target.value)} className="w-full border rounded-lg p-2 text-sm">
                        <option value="">-- Válassz játékost --</option>
                        {otherParticipants.map(p => (
                            <option key={p.userId} value={p.userId}>
                                {p.user.name} {p.team ? `(${p.team.name})` : ''}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Build max dict from my own resources for the offered section */}
                {(() => {
                    const offeredMax: Record<string, number> = {
                        capital: myParticipant.capital,
                        rawMaterial: myParticipant.rawMaterial,
                        ...Object.fromEntries(productKeys.map(k => [k, myInventory[k] ?? 0]))
                    }
                    return (
                        <ResourceInputs
                            bundle={offered}
                            setBundle={setOffered}
                            label="Amit TE adsz 🡺"
                            maxValues={offeredMax}
                        />
                    )
                })()}
                <ResourceInputs bundle={requested} setBundle={setRequested} label="Amit KÉRSZ cserébe 🡸" />

                {/* Optional message */}
                <div>
                    <label className="text-xs font-bold uppercase text-gray-500 block mb-1">Üzenet (opcionális)</label>
                    <input
                        type="text"
                        value={message}
                        onChange={e => setMessage(e.target.value)}
                        maxLength={120}
                        placeholder="Pl: Ez egy jó üzlet mindkettőnknek!"
                        className="w-full border rounded-lg p-2 text-sm"
                    />
                </div>

                <button
                    onClick={handleSend}
                    disabled={loading}
                    className="w-full py-2 px-4 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                    {loading ? 'Küldés...' : 'Ajánlat Elküldése →'}
                </button>
            </div>
        </div>
    )
}
