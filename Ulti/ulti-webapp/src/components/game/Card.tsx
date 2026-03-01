import React from 'react'
import { Card as CardType } from '@/lib/game/deck'
import { cn } from '@/lib/utils'

interface CardProps {
    card: CardType
    onClick?: () => void
    disabled?: boolean
    className?: string
    selected?: boolean
}

// In a real app we would use SVG images of the Hungarian deck.
// Here we use text placeholders with colors indicating the suits.
const suitColors: Record<string, string> = {
    'piros': 'text-red-600 bg-red-50',
    'tok': 'text-orange-600 bg-orange-50',
    'zold': 'text-green-700 bg-green-50',
    'makk': 'text-amber-900 bg-amber-50'
}

const suitSymbols: Record<string, string> = {
    'piros': '♥ Piros', // Not exact symbols but good proxies
    'tok': '🔔 Tök',
    'zold': '🍃 Zöld',
    'makk': '🌰 Makk'
}

export function PlayingCard({ card, onClick, disabled, className, selected }: CardProps) {
    return (
        <div
            onClick={!disabled ? onClick : undefined}
            className={cn(
                "relative flex flex-col items-center justify-center w-20 h-32 sm:w-28 sm:h-40 rounded-xl border-2 shadow-md transition-all duration-200 select-none",
                suitColors[card.suit],
                disabled ? "opacity-50 cursor-not-allowed" : "hover:-translate-y-4 hover:shadow-xl cursor-pointer",
                selected ? "border-blue-500 ring-2 ring-blue-400 -translate-y-4" : "border-slate-300",
                className
            )}
        >
            <div className="absolute top-2 left-2 text-sm sm:text-lg font-bold">
                {card.rank.toUpperCase()}
            </div>
            <div className="text-xl sm:text-3xl font-black">
                {suitSymbols[card.suit].split(' ')[0]}
            </div>
            <div className="absolute bottom-2 right-2 text-xs sm:text-sm font-semibold opacity-70">
                {card.suit.toUpperCase()}
            </div>
        </div>
    )
}
