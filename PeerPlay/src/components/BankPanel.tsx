'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { sellToBank, buyFromBank, buyRawMaterial, sellRawMaterial } from '@/modules/interaction/bank'
import { getDynamicPricing } from '@/modules/interaction/pricing'
import { RAW_MATERIAL_BUY_PRICE } from '@/modules/interaction/bankConstants'
import { PRODUCTION_RECIPES, ProductType } from '@/modules/interaction/constants'

const PRODUCT_KEYS: ProductType[] = ['wheat', 'corn', 'sunflower', 'wine']
const PRODUCT_EMOJI: Record<string, string> = { wheat: '🌾', corn: '🌽', sunflower: '🌻', wine: '🍷' }

type ParticipantData = {
    capital: number
    rawMaterial: number
    techLevel: number
    productionEff: number
    inventory: string
}
type Props = { sessionId: string; userId: string; participant: ParticipantData }

function parseInventory(json: string): Record<string, number> {
    try { return JSON.parse(json || '{}') } catch { return {} }
}

// Inline confirmation dialog state
type ConfirmState = {
    key: string
    label: string
    detail: string
    action: () => Promise<unknown>
} | null

export default function BankPanel({ sessionId, userId, participant }: Props) {
    const [loadingKey, setLoadingKey] = useState<string | null>(null)
    const [messages, setMessages] = useState<Record<string, { type: 'ok' | 'err'; text: string }>>({})
    const [confirm, setConfirm] = useState<ConfirmState>(null)

    // Poll dynamic prices
    const { data: prices } = useSWR(
        sessionId ? `pricing-${sessionId}` : null,
        () => getDynamicPricing(sessionId),
        { refreshInterval: 3000 }
    )

    const inventory = parseInventory(participant.inventory)

    const showConfirm = (cfg: ConfirmState) => setConfirm(cfg)

    const executeConfirmed = async () => {
        if (!confirm) return
        const key = confirm.key
        setConfirm(null)
        setLoadingKey(key)
        setMessages(prev => { const n = { ...prev }; delete n[key]; return n })
        try {
            await confirm.action()
            setMessages(prev => ({ ...prev, [key]: { type: 'ok', text: '✓ Sikeres!' } }))
        } catch (e: any) {
            setMessages(prev => ({ ...prev, [key]: { type: 'err', text: e.message } }))
        } finally {
            setLoadingKey(null)
            setTimeout(() => setMessages(prev => { const n = { ...prev }; delete n[key]; return n }), 5000)
        }
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 relative">
            {/* ── Confirmation overlay ── */}
            {confirm && (
                <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/30 rounded-xl">
                    <div className="bg-white rounded-xl shadow-2xl p-6 mx-4 max-w-sm w-full text-center border border-gray-200">
                        <p className="text-lg font-bold text-gray-900 mb-1">{confirm.label}</p>
                        <p className="text-sm text-gray-500 mb-5">{confirm.detail}</p>
                        <div className="flex gap-3 justify-center">
                            <button
                                onClick={() => setConfirm(null)}
                                style={{ backgroundColor: '#f9fafb', color: '#374151', border: '1px solid #d1d5db' }}
                                className="px-5 py-2 rounded-lg font-bold text-sm cursor-pointer"
                            >
                                Mégsem
                            </button>
                            <button
                                onClick={executeConfirmed}
                                style={{ backgroundColor: '#4f46e5', color: '#ffffff' }}
                                className="px-5 py-2 rounded-lg font-bold text-sm cursor-pointer"
                            >
                                Megerősít
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Header ── */}
            <div className="flex items-center justify-between bg-gray-50 -mx-6 -mt-6 px-6 py-4 border-b border-gray-100 mb-6">
                <h3 className="font-bold text-lg text-gray-900">🏦 Bank – Árfolyamok & Kereskedés</h3>
                <div className="flex gap-4 text-sm text-gray-500">
                    <span>💰 <strong className="text-gray-900">${participant.capital.toLocaleString()}</strong></span>
                    <span>🌱 <strong className="text-gray-900">{participant.rawMaterial}</strong></span>
                </div>
            </div>

            {/* ── Column headers ── */}
            <div className="grid grid-cols-[1fr_auto_auto_auto_auto_auto] gap-x-3 items-center text-xs font-bold uppercase text-gray-400 border-b pb-2 mb-1">
                <span>Termék</span>
                <span className="text-right text-green-600">Elad ▾</span>
                <span className="text-right text-red-500">Vesz ▴</span>
                <span className="text-right">Nálam</span>
                <span className="text-right text-green-700">Elad</span>
                <span className="text-right text-blue-700">Vesz</span>
            </div>

            {/* ── Raw material row ── */}
            <div className="grid grid-cols-[1fr_auto_auto_auto_auto_auto] gap-x-3 items-center py-3 border-b border-gray-100">
                <div>
                    <p className="font-semibold text-sm">🌱 Vetőmag</p>
                    <p className="text-xs text-gray-400">Alapanyag a termeléshez</p>
                </div>
                <span className="text-sm font-bold text-green-600 text-right">${prices?.rawMaterial?.sellToBank ?? Math.round(RAW_MATERIAL_BUY_PRICE / 1.3)}</span>
                <span className="text-sm font-bold text-red-600 text-right">${prices?.rawMaterial?.buyFromBank ?? RAW_MATERIAL_BUY_PRICE}</span>
                <span className="text-sm font-bold text-right tabular-nums">{participant.rawMaterial}</span>

                {/* Sell button */}
                <div className="flex flex-col items-end gap-1">
                    {messages['sell-raw'] && (
                        <span className={`text-xs ${messages['sell-raw'].type === 'ok' ? 'text-green-600' : 'text-red-500'}`}>
                            {messages['sell-raw'].text}
                        </span>
                    )}
                    <button
                        onClick={() => showConfirm({
                            key: 'sell-raw',
                            label: '🌱 Vetőmag eladása',
                            detail: `1 db Vetőmag → +$${prices?.rawMaterial?.sellToBank ?? Math.round(RAW_MATERIAL_BUY_PRICE / 1.3)} tőke. Raktáron: ${participant.rawMaterial} db`,
                            action: () => sellRawMaterial(sessionId, userId)
                        })}
                        disabled={loadingKey === 'sell-raw' || participant.rawMaterial < 1}
                        style={{
                            backgroundColor: (loadingKey === 'sell-raw' || participant.rawMaterial < 1) ? '#86efac' : '#16a34a',
                            color: '#ffffff'
                        }}
                        className="px-3 py-1 text-xs font-bold rounded cursor-pointer"
                    >
                        {loadingKey === 'sell-raw' ? '...' : `Elad $${prices?.rawMaterial?.sellToBank ?? Math.round(RAW_MATERIAL_BUY_PRICE / 1.3)}`}
                    </button>
                </div>

                {/* Buy button */}
                <div className="flex flex-col items-end gap-1">
                    {messages['raw'] && (
                        <span className={`text-xs ${messages['raw'].type === 'ok' ? 'text-green-600' : 'text-red-500'}`}>
                            {messages['raw'].text}
                        </span>
                    )}
                    <button
                        onClick={() => showConfirm({
                            key: 'raw',
                            label: '🌱 Vetőmag vásárlás',
                            detail: `1 db Vetőmag → -$${prices?.rawMaterial?.buyFromBank ?? RAW_MATERIAL_BUY_PRICE} tőke. Jelenlegi tőkéd: $${participant.capital}`,
                            action: () => buyRawMaterial(sessionId, userId)
                        })}
                        disabled={loadingKey === 'raw' || participant.capital < (prices?.rawMaterial?.buyFromBank ?? RAW_MATERIAL_BUY_PRICE)}
                        style={{
                            backgroundColor: (loadingKey === 'raw' || participant.capital < (prices?.rawMaterial?.buyFromBank ?? RAW_MATERIAL_BUY_PRICE)) ? '#93c5fd' : '#2563eb',
                            color: '#ffffff'
                        }}
                        className="px-3 py-1 text-xs font-bold rounded cursor-pointer"
                    >
                        {loadingKey === 'raw' ? '...' : `Vesz $${prices?.rawMaterial?.buyFromBank ?? RAW_MATERIAL_BUY_PRICE}`}
                    </button>
                </div>
            </div>

            {/* ── Product rows ── */}
            {PRODUCT_KEYS.map(k => {
                const recipe = PRODUCTION_RECIPES[k]

                // Fallback to static pricing if polling hasn't loaded yet
                // Note: The static fallback might be slightly off if a global multiplier is active, but it's only for a split second 
                const dynamicSellPrice = prices?.[k]?.sellToBank ?? recipe.baseValue
                const dynamicBuyPrice = prices?.[k]?.buyFromBank ?? Math.round(recipe.baseValue * 1.3) // BANK_BUY_MARKUP

                const sellPrice = Math.round(dynamicSellPrice)
                const buyPrice = dynamicBuyPrice

                const qty = inventory[k] || 0
                const techMet = participant.techLevel >= recipe.techReq

                return (
                    <div key={k} className={techMet
                        ? 'grid grid-cols-[1fr_auto_auto_auto_auto_auto] gap-x-3 items-center py-3 border-b border-gray-50'
                        : 'grid grid-cols-[1fr_auto_auto_auto_auto_auto] gap-x-3 items-center py-3 border-b border-gray-50 opacity-40'
                    }>
                        <div>
                            <p className="font-semibold text-sm">{PRODUCT_EMOJI[k]} {recipe.name}</p>
                            <p className="text-xs text-gray-400">
                                ⚙️ Tech {recipe.techReq} • 🌱 {recipe.rawCost}/db
                                {!techMet && <span className="ml-1 text-red-400 font-medium">(nem elérhető)</span>}
                            </p>
                        </div>
                        <span className="text-sm font-bold text-green-600 text-right">${sellPrice}</span>
                        <span className="text-sm font-bold text-red-600 text-right">${buyPrice}</span>
                        <span className="text-sm font-bold text-right tabular-nums">{qty}</span>

                        {/* Sell button */}
                        <div className="flex flex-col items-end gap-1">
                            {messages[`sell-${k}`] && (
                                <span className={`text-xs ${messages[`sell-${k}`].type === 'ok' ? 'text-green-600' : 'text-red-500'}`}>
                                    {messages[`sell-${k}`].text}
                                </span>
                            )}
                            <button
                                onClick={() => showConfirm({
                                    key: `sell-${k}`,
                                    label: `${PRODUCT_EMOJI[k]} ${recipe.name} eladása`,
                                    detail: `1 db ${recipe.name} → +$${sellPrice} tőke. Raktáron: ${qty} db`,
                                    action: () => sellToBank(sessionId, userId, k)
                                })}
                                disabled={loadingKey === `sell-${k}` || qty < 1}
                                style={{
                                    backgroundColor: (loadingKey === `sell-${k}` || qty < 1) ? '#86efac' : '#16a34a',
                                    color: '#ffffff'
                                }}
                                className="px-3 py-1 text-xs font-bold rounded cursor-pointer"
                            >
                                {loadingKey === `sell-${k}` ? '...' : `Elad $${sellPrice}`}
                            </button>
                        </div>

                        {/* Buy button */}
                        <div className="flex flex-col items-end gap-1">
                            {messages[`buy-${k}`] && (
                                <span className={`text-xs ${messages[`buy-${k}`].type === 'ok' ? 'text-green-600' : 'text-red-500'}`}>
                                    {messages[`buy-${k}`].text}
                                </span>
                            )}
                            <button
                                onClick={() => showConfirm({
                                    key: `buy-${k}`,
                                    label: `${PRODUCT_EMOJI[k]} ${recipe.name} vásárlása`,
                                    detail: `1 db ${recipe.name} → −$${buyPrice} tőke. Jelenlegi tőkéd: $${participant.capital}`,
                                    action: () => buyFromBank(sessionId, userId, k)
                                })}
                                disabled={loadingKey === `buy-${k}` || participant.capital < buyPrice}
                                style={{
                                    backgroundColor: (loadingKey === `buy-${k}` || participant.capital < buyPrice) ? '#93c5fd' : '#2563eb',
                                    color: '#ffffff'
                                }}
                                className="px-3 py-1 text-xs font-bold rounded cursor-pointer"
                            >
                                {loadingKey === `buy-${k}` ? '...' : `Vesz $${buyPrice}`}
                            </button>
                        </div>
                    </div>
                )
            })}

            <p className="text-xs text-gray-400 italic mt-4">
                * Eladási ár és Vételi ár az aktuális banki árfolyam. 2. körtől az árak a kereslet-kínálat szerint változnak! A tech. (készségszint) a termelési időket gyorsítja.
            </p>
        </div>
    )
}
