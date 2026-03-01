import React from 'react'
import { Card } from '@/lib/game/deck'
import { PlayingCard } from './Card'

interface HandProps {
    cards: Card[]
    onPlayCard?: (card: Card) => void
    disabled?: boolean
    selectedCardId?: string
    selectedCardIds?: string[]
}

export function Hand({ cards, onPlayCard, disabled, selectedCardId, selectedCardIds }: HandProps) {
    // We sort the cards by suit and rank for better UX
    const sortedCards = [...cards].sort((a, b) => {
        if (a.suit !== b.suit) return a.suit.localeCompare(b.suit)
        return b.basePowerLevel - a.basePowerLevel
    })

    return (
        <div className="flex justify-center -space-x-8 sm:-space-x-12 px-4 py-8 overflow-x-auto w-full max-w-4xl mx-auto">
            {sortedCards.map((card, idx) => (
                <div
                    key={card.id}
                    className="relative transition-transform duration-300 transform"
                    style={{
                        // Fan effect: rotate cards slightly based on position
                        transform: `rotate(${(idx - cards.length / 2) * 5}deg) translateY(${Math.abs(idx - cards.length / 2) * 2}px)`,
                        zIndex: idx
                    }}
                >
                    <PlayingCard
                        card={card}
                        onClick={() => onPlayCard && onPlayCard(card)}
                        disabled={disabled}
                        selected={selectedCardId === card.id || selectedCardIds?.includes(card.id)}
                    />
                </div>
            ))}
        </div>
    )
}
