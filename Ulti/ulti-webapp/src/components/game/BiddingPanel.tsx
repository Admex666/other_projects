import React from 'react'
import { Bid, AVAILABLE_BIDS } from '@/lib/game/rules'

interface BiddingPanelProps {
    currentHighestBid: Bid | null
    onBid: (bidId: string) => void
    disabled?: boolean
    isTenCards?: boolean
}

export function BiddingPanel({ currentHighestBid, onBid, disabled, isTenCards }: BiddingPanelProps) {
    // Only show bids that are higher than the current highest, plus "Passz"
    const availableOptions = isTenCards
        ? [
            { id: 'take_talon', name: 'Felveszem', baseValue: 0, player_id: '', includesTrump: false },
            { id: 'pass', name: 'Passz', baseValue: 0, player_id: '', includesTrump: false }
        ]
        : AVAILABLE_BIDS.filter(
            b => b.id === 'pass' || !currentHighestBid || b.baseValue > currentHighestBid.baseValue
        )

    return (
        <div className="bg-white/90 backdrop-blur-sm p-4 rounded-2xl shadow-2xl border-2 border-slate-200">
            <h3 className="text-xl font-bold text-center mb-4 text-slate-800">
                Licitálás
            </h3>

            {currentHighestBid && (
                <div className="text-center mb-4 p-2 bg-slate-100 rounded-lg">
                    <span className="text-sm text-slate-600 block">Jelenlegi legnagyobb licit:</span>
                    <span className="font-bold text-red-600 text-lg">{currentHighestBid.name}</span>
                </div>
            )}

            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
                {availableOptions.map(bid => (
                    <button
                        key={bid.id}
                        onClick={() => onBid(bid.id)}
                        disabled={disabled}
                        className={`
              px-4 py-3 rounded-xl font-bold transition-all text-sm sm:text-base
              ${disabled
                                ? 'opacity-50 cursor-not-allowed bg-slate-100 text-slate-400'
                                : bid.id === 'pass'
                                    ? 'bg-slate-200 hover:bg-slate-300 text-slate-700'
                                    : 'bg-red-50 hover:bg-red-100 text-red-700 border border-red-200'
                            }
            `}
                    >
                        {bid.name}
                    </button>
                ))}
            </div>
        </div>
    )
}
