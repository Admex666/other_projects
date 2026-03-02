'use client'

import { useState } from 'react'
import { sellToBank } from '@/modules/interaction/bank'
import { PRODUCTION_RECIPES, ProductType } from '@/modules/interaction/constants'

type InventoryPanelProps = {
    sessionId: string
    userId: string
    inventoryJson: string
}

export default function InventoryPanel({ sessionId, userId, inventoryJson }: InventoryPanelProps) {
    const [loading, setLoading] = useState<ProductType | null>(null)
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

    const inventory: Record<string, number> = (() => {
        try { return JSON.parse(inventoryJson || "{}") } catch { return {} }
    })()

    const hasItems = Object.values(inventory).some(qty => qty > 0)

    const handleSell = async (productType: ProductType) => {
        setLoading(productType)
        setMessage(null)
        try {
            await sellToBank(sessionId, userId, productType)
            const name = PRODUCTION_RECIPES[productType].name
            setMessage({ type: 'success', text: `Eladtad: 1 ${name} → Banknak ✅` })
            setTimeout(() => setMessage(null), 3000)
        } catch (err: any) {
            setMessage({ type: 'error', text: err.message || 'Sikertelen eladás!' })
            setTimeout(() => setMessage(null), 4000)
        } finally {
            setLoading(null)
        }
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="font-bold text-lg border-b pb-2 mb-4">🏦 Raktár & Bank</h3>

            {message && (
                <div className={`mb-4 p-3 rounded-md text-sm font-medium border ${message.type === 'success'
                    ? 'text-green-700 bg-green-50 border-green-100'
                    : 'text-red-600 bg-red-50 border-red-100'}`}>
                    {message.text}
                </div>
            )}

            {!hasItems ? (
                <p className="text-gray-400 text-sm italic text-center py-4">Nincs legyártott terményed még.</p>
            ) : (
                <div className="space-y-2">
                    {(Object.keys(PRODUCTION_RECIPES) as ProductType[]).map(key => {
                        const qty = inventory[key] || 0
                        if (qty === 0) return null
                        const recipe = PRODUCTION_RECIPES[key]
                        return (
                            <div key={key} className="flex items-center justify-between p-3 bg-amber-50 border border-amber-100 rounded-lg">
                                <div>
                                    <span className="font-bold text-gray-800">{recipe.name}</span>
                                    <span className="ml-2 text-sm text-gray-500">× {qty}</span>
                                </div>
                                <button
                                    onClick={() => handleSell(key)}
                                    disabled={loading !== null}
                                    className="py-1 px-3 text-sm font-bold rounded bg-orange-600 text-white hover:bg-orange-700 disabled:opacity-50 disabled:cursor-wait transition-colors"
                                >
                                    {loading === key ? 'Eladás...' : `Eladom (+$${recipe.baseValue})`}
                                </button>
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
