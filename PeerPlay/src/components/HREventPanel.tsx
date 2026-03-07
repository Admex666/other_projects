'use client'

import { useState } from 'react'
import { triggerEvent, EventType } from '@/modules/event/actions'

export default function HREventPanel({ sessionId, isVisible }: { sessionId: string, isVisible: boolean }) {
    const [loading, setLoading] = useState<string | null>(null)
    const [message, setMessage] = useState<{ text: string, type: 'ok' | 'err' } | null>(null)
    const [duration, setDuration] = useState<number>(60)

    if (!isVisible) return null

    const handleTrigger = async (type: EventType, targetProduct?: string) => {
        setLoading(type + (targetProduct || ''))
        setMessage(null)
        try {
            const res = await triggerEvent(sessionId, type, targetProduct, duration || undefined)
            setMessage({ text: 'Esemény elindítva: ' + res.message, type: 'ok' })
        } catch (e: any) {
            setMessage({ text: e.message, type: 'err' })
        } finally {
            setLoading(null)
            setTimeout(() => setMessage(null), 5000)
        }
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-indigo-200 mt-6 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>

            <h2 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                <span>⚡ Eseményvezérlés (Kör 3+)</span>
            </h2>
            <p className="text-sm text-gray-500 mb-6">
                Az itt indított események azonnal globális felugró (Toast) értesítést küldenek minden aktív játékosnak, és módosítják a piaci árakat.
            </p>

            {message && (
                <div className={`p-3 rounded mb-4 text-sm font-bold ${message.type === 'ok' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {message.text}
                </div>
            )}

            <div className="mb-6 flex items-center bg-gray-50 border border-gray-200 p-3 rounded-lg w-max">
                <label className="text-sm font-bold text-gray-700 mr-3">🕒 Esemény hossza:</label>
                <select
                    value={duration}
                    onChange={e => setDuration(Number(e.target.value))}
                    className="border border-gray-300 bg-white p-1.5 rounded text-sm font-semibold outline-none focus:ring-2 focus:ring-indigo-500"
                >
                    <option value={30}>30 másodperc</option>
                    <option value={60}>1 perc</option>
                    <option value={120}>2 perc</option>
                    <option value={300}>5 perc</option>
                    <option value={0}>Végtelen (kézi leállításig)</option>
                </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                    onClick={() => handleTrigger('market_crash')}
                    disabled={loading !== null}
                    className="flex flex-col items-start p-4 border border-red-200 bg-red-50 hover:bg-red-100 rounded-lg text-left transition-colors cursor-pointer disabled:opacity-50"
                >
                    <span className="font-bold text-red-900 text-base mb-1">📉 Piac-összeomlás</span>
                    <span className="text-xs text-red-700">Minden termék eladási ára 50%-ára esik vissza a bankban. Pánik!</span>
                </button>

                <button
                    onClick={() => handleTrigger('supply_shock')}
                    disabled={loading !== null}
                    className="flex flex-col items-start p-4 border border-amber-200 bg-amber-50 hover:bg-amber-100 rounded-lg text-left transition-colors cursor-pointer disabled:opacity-50"
                >
                    <span className="font-bold text-amber-900 text-base mb-1">🏭 Beszállítói Válság</span>
                    <span className="text-xs text-amber-700">A Vetőmag (alapanyag) vásárlási költsége a duplájára (200%-ra) nő a bankban.</span>
                </button>

                <button
                    onClick={() => handleTrigger('market_boom', 'wheat')}
                    disabled={loading !== null}
                    className="flex flex-col items-start p-4 border border-green-200 bg-green-50 hover:bg-green-100 rounded-lg text-left transition-colors cursor-pointer disabled:opacity-50"
                >
                    <span className="font-bold text-green-900 text-base mb-1">🚀 Búza Boom (Hot Offer)</span>
                    <span className="text-xs text-green-700">A Búza eladási ára azonnal megduplázódik.</span>
                </button>

                <button
                    onClick={() => handleTrigger('market_boom', 'wine')}
                    disabled={loading !== null}
                    className="flex flex-col items-start p-4 border border-purple-200 bg-purple-50 hover:bg-purple-100 rounded-lg text-left transition-colors cursor-pointer disabled:opacity-50"
                >
                    <span className="font-bold text-purple-900 text-base mb-1">🍷 Bor Boom (Hot Offer)</span>
                    <span className="text-xs text-purple-700">A prémium Bor eladási ára azonnal megduplázódik.</span>
                </button>
            </div>

            <div className="mt-6 pt-4 border-t border-gray-100">
                <button
                    onClick={() => handleTrigger('clear')}
                    disabled={loading !== null}
                    className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold rounded text-sm cursor-pointer transition-colors disabled:opacity-50"
                >
                    ✅ Piac normalizálása (Minden esemény törlése)
                </button>
            </div>
        </div>
    )
}
