import React from 'react'
import { Card, Suit } from '@/lib/game/deck'
import { Bid } from '@/lib/game/rules'
import { cn } from '@/lib/utils'
import { Game } from '@/store/gameStore'

export type AnnounceAction =
    | { type: 'announce_20_40', payload: { type: '20' | '40', suit: string } }
    | { type: 'double', payload: { type: 'kontra' | 'rekontra' } }
    | { type: 'pass' }

interface AnnouncePanelProps {
    game: Game
    myId: string
    myHand: Card[]
    onAnnounce: (action: AnnounceAction) => void
    disabled?: boolean
}

const suitSymbols: Record<string, string> = {
    'piros': '♥ Piros',
    'tok': '🔔 Tök',
    'zold': '🍃 Zöld',
    'makk': '🌰 Makk'
}

export function AnnouncePanel({ game, myId, myHand, onAnnounce, disabled }: AnnouncePanelProps) {
    const isActivePlayer = game.active_player_id === myId
    const currentBid = game.current_bid

    // Check if player has 20 or 40 (only if game has a trump suit, which means it is a color game)
    const canAnnounce = currentBid?.includesTrump

    const availableAnnouncements: { type: '20' | '40', suit: string }[] = []

    if (canAnnounce && isActivePlayer) {
        const suits: Suit[] = ['piros', 'tok', 'zold', 'makk']

        suits.forEach(suit => {
            const hasKing = myHand.some(c => c.suit === suit && c.rank === 'kiraly')
            const hasOver = myHand.some(c => c.suit === suit && c.rank === 'felso')

            if (hasKing && hasOver) {
                // If this is the trump suit, it's 40. Otherwise it's 20.
                if (suit === game.trump_suit) {
                    availableAnnouncements.push({ type: '40', suit })
                } else {
                    availableAnnouncements.push({ type: '20', suit })
                }
            }
        })
    }

    // Filter out announcements already made by this player
    const myMadeAnnouncements = game.state.announcements?.filter(a => a.player_id === myId) || []
    const unmadeAnnouncements = availableAnnouncements.filter(aa =>
        !myMadeAnnouncements.some(ma => ma.suit === aa.suit && ma.type === aa.type)
    )

    // Doubles Logic
    // Bid winner vs Defenders.
    const isBidWinner = currentBid?.player_id === myId
    const hasBeenDoubled = game.state.doubles && game.state.doubles.length > 0
    const lastDouble = hasBeenDoubled ? game.state.doubles![game.state.doubles!.length - 1] : null

    const canDouble = isActivePlayer && !isBidWinner && (!lastDouble || lastDouble.type === 'rekontra')
    const canRedouble = isActivePlayer && isBidWinner && lastDouble?.type === 'kontra'

    if (!isActivePlayer) {
        return (
            <div className="bg-white/90 backdrop-blur-sm p-4 rounded-2xl shadow-2xl border-2 border-slate-200 text-center">
                <p className="text-slate-600 font-medium">Várakozás a többi játékos jelentéseire...</p>
            </div>
        )
    }

    return (
        <div className="bg-white/95 backdrop-blur-sm p-6 rounded-3xl shadow-2xl border-2 border-slate-200">
            <h3 className="text-xl font-bold text-center mb-4 text-slate-800">
                Jelentések és Kontra
            </h3>

            <div className="space-y-4">
                {/* 20/40 Jelentések */}
                {unmadeAnnouncements.length > 0 && (
                    <div className="bg-blue-50 p-4 rounded-xl border border-blue-100">
                        <h4 className="text-sm font-bold text-blue-800 mb-2">Jelenthető (20/40):</h4>
                        <div className="flex flex-wrap gap-2">
                            {unmadeAnnouncements.map((ann, idx) => (
                                <button
                                    key={idx}
                                    disabled={disabled}
                                    onClick={() => onAnnounce({ type: 'announce_20_40', payload: ann })}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition"
                                >
                                    {ann.type} ({suitSymbols[ann.suit]})
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Kontra opciók */}
                {(canDouble || canRedouble) && (
                    <div className="bg-red-50 p-4 rounded-xl border border-red-100">
                        <h4 className="text-sm font-bold text-red-800 mb-2">Eszkaláció:</h4>
                        {canDouble && (
                            <button
                                disabled={disabled}
                                onClick={() => onAnnounce({ type: 'double', payload: { type: 'kontra' } })}
                                className="w-full px-4 py-3 bg-red-600 text-white rounded-lg font-bold text-lg hover:bg-red-700 transition shadow-md"
                            >
                                KONTRA!
                            </button>
                        )}
                        {canRedouble && (
                            <button
                                disabled={disabled}
                                onClick={() => onAnnounce({ type: 'double', payload: { type: 'rekontra' } })}
                                className="w-full px-4 py-3 bg-red-700 text-white rounded-lg font-bold text-lg hover:bg-red-800 transition shadow-md"
                            >
                                REKONTRA!!
                            </button>
                        )}
                    </div>
                )}

                <button
                    disabled={disabled}
                    onClick={() => onAnnounce({ type: 'pass' })}
                    className={cn(
                        "w-full px-4 py-3 rounded-xl font-bold text-lg transition-all",
                        myMadeAnnouncements.length > 0 || hasBeenDoubled
                            ? "bg-slate-800 hover:bg-slate-900 text-white"
                            : "bg-slate-200 hover:bg-slate-300 text-slate-700"
                    )}
                >
                    Tovább (Passz)
                </button>
            </div>
        </div>
    )
}
