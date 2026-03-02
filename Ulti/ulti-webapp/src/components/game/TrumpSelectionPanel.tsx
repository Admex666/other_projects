import React, { useState } from 'react'
import { cn } from '@/lib/utils'

interface TrumpSelectionPanelProps {
    onSelectTrump: (suit: string) => void
    disabled?: boolean
}

const suitColors: Record<string, string> = {
    'piros': 'text-red-600 bg-red-50 hover:bg-red-100 border-red-200 ring-red-400',
    'tok': 'text-orange-600 bg-orange-50 hover:bg-orange-100 border-orange-200 ring-orange-400',
    'zold': 'text-green-700 bg-green-50 hover:bg-green-100 border-green-200 ring-green-600',
    'makk': 'text-amber-900 bg-amber-50 hover:bg-amber-100 border-amber-200 ring-amber-800'
}

const suitSymbols: Record<string, string> = {
    'piros': '♥ Piros',
    'tok': '🔔 Tök',
    'zold': '🍃 Zöld',
    'makk': '🌰 Makk'
}

export function TrumpSelectionPanel({ onSelectTrump, disabled }: TrumpSelectionPanelProps) {
    const [selectedSuit, setSelectedSuit] = useState<string | null>(null)

    const handleConfirm = () => {
        if (selectedSuit && !disabled) {
            onSelectTrump(selectedSuit)
        }
    }

    return (
        <div className="bg-white/95 backdrop-blur-sm p-6 rounded-3xl shadow-2xl border-2 border-slate-200 w-[95%] max-w-lg mx-auto transform transition-all">
            <h3 className="text-2xl font-black text-center mb-2 text-slate-800">
                Aduválasztás
            </h3>
            <p className="text-center text-slate-500 mb-6 text-sm font-medium">
                Te nyerted a licitet! Válaszd ki, melyik szín legyen az Adu.
            </p>

            <div className="grid grid-cols-2 gap-4 mb-6">
                {Object.keys(suitSymbols).map(suit => (
                    <button
                        key={suit}
                        onClick={() => setSelectedSuit(suit)}
                        disabled={disabled}
                        className={cn(
                            "py-6 px-4 rounded-2xl font-bold transition-all text-lg sm:text-xl border-2 flex flex-col items-center justify-center gap-2",
                            suitColors[suit],
                            selectedSuit === suit ? "ring-4 scale-105 shadow-lg" : "scale-100",
                            disabled && "opacity-50 cursor-not-allowed"
                        )}
                    >
                        <span className="text-3xl">{suitSymbols[suit].split(' ')[0]}</span>
                        <span>{suitSymbols[suit].split(' ')[1]}</span>
                    </button>
                ))}
            </div>

            <button
                onClick={handleConfirm}
                disabled={!selectedSuit || disabled}
                className={cn(
                    "w-full py-4 rounded-xl font-bold text-lg transition-all text-white",
                    !selectedSuit || disabled
                        ? "bg-slate-300 cursor-not-allowed"
                        : "bg-blue-600 hover:bg-blue-700 shadow-xl hover:-translate-y-1"
                )}
            >
                Kiválasztom
            </button>
        </div>
    )
}
