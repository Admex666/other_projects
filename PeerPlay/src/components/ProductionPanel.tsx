'use client'

import { useState } from 'react'
import { produceShape } from '@/modules/interaction/production'
import { PRODUCTION_RECIPES, ShapeType } from '@/modules/interaction/constants'

export type Team = {
    id: string;
    sessionId: string;
    name: string;
    teamType: string;
    capital: number;
    rawMaterial: number;
    techLevel: number;
    productionEff: number;
}

export default function ProductionPanel({ sessionId, myTeam }: { sessionId: string, myTeam: Team }) {
    const [loading, setLoading] = useState<ShapeType | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [successMsg, setSuccessMsg] = useState<string | null>(null)

    const handleProduce = async (shape: string) => {
        const shapeType = shape as ShapeType
        setLoading(shapeType)
        setError(null)
        setSuccessMsg(null)

        try {
            await produceShape(sessionId, myTeam.id, shapeType)
            setSuccessMsg(`Produced 1 ${PRODUCTION_RECIPES[shapeType].name} successfully!`)
            setTimeout(() => setSuccessMsg(null), 3000)
        } catch (err: any) {
            setError(err.message || 'Production failed')
            setTimeout(() => setError(null), 4000)
        } finally {
            setLoading(null)
        }
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6">
            <h3 className="font-bold text-lg border-b pb-2 mb-4">Production Line</h3>

            {error && <div className="mb-4 text-red-600 bg-red-50 p-3 rounded-md text-sm font-medium border border-red-100">{error}</div>}
            {successMsg && <div className="mb-4 text-green-700 bg-green-50 p-3 rounded-md text-sm font-medium border border-green-100">{successMsg}</div>}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {(Object.entries(PRODUCTION_RECIPES) as [ShapeType, typeof PRODUCTION_RECIPES[ShapeType]][]).map(([key, recipe]) => {
                    const canAffordRaw = myTeam.rawMaterial >= recipe.rawCost;
                    const canAffordTech = myTeam.techLevel >= recipe.techReq;
                    const canProduce = canAffordRaw && canAffordTech;

                    return (
                        <div key={key} className={`border rounded-lg p-4 flex flex-col justify-between transition-all ${canProduce ? 'bg-white hover:border-indigo-400 hover:shadow-md' : 'bg-gray-50 opacity-75'}`}>
                            <div>
                                <h4 className="font-bold text-gray-800 text-lg">{recipe.name}</h4>
                                <div className="text-sm space-y-1 mt-2 text-gray-600 flex flex-col">
                                    <span className={canAffordRaw ? 'text-gray-600' : 'text-red-500 font-medium'}>
                                        Cost: {recipe.rawCost} Raw
                                    </span>
                                    <span className={canAffordTech ? 'text-gray-600' : 'text-red-500 font-medium'}>
                                        Req. Tech: Lvl {recipe.techReq}
                                    </span>
                                </div>
                            </div>

                            <div className="mt-4 border-t pt-3">
                                <div className="flex justify-between items-center mb-3">
                                    <span className="text-xs text-gray-500">Base Value:</span>
                                    <span className="font-bold text-green-600">${recipe.baseValue}</span>
                                </div>

                                <button
                                    onClick={() => handleProduce(key)}
                                    disabled={loading !== null || !canProduce}
                                    className={`w-full py-2 px-4 rounded-md text-sm font-bold shadow-sm transition-colors
                                        ${loading === key ? 'bg-indigo-400 text-white cursor-wait'
                                            : canProduce ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                                                : 'bg-gray-200 text-gray-400 cursor-not-allowed'}`}
                                >
                                    {loading === key ? 'Producing...' : 'Produce'}
                                </button>
                            </div>
                        </div>
                    )
                })}
            </div>
            <div className="mt-4 text-xs text-gray-400 text-right italic">
                Production Efficiency: x{myTeam.productionEff}
            </div>
        </div>
    )
}
