'use client'

import React, { useEffect } from 'react'
import { useGameStore } from '@/store/gameStore'
import { Card } from '@/lib/game/deck'
import { PlayingCard } from './Card'

interface TrickCard {
    player_id: string
    card: Card
}

interface TableProps {
    currentTrick: TrickCard[]
    trumpSuit: string | null
    talonCount: number
    announcements?: { player_id: string, type: string, suit: string }[]
    doubles?: { player_id: string, type: string }[]
}

// Position mapping relative to the current player (bottom)
// In a real app we'd map Player1, Player2, Player3 to Bottom, TopLeft, TopRight dynamically based on who's looking.
// For now, we just display the trick cards generically.

export function Table({ currentTrick, trumpSuit, talonCount, announcements, doubles }: TableProps) {
    return (
        <div className="relative w-full h-[50vh] sm:h-[60vh] bg-green-800 rounded-3xl shadow-inner border-8 border-amber-900 border-opacity-50 overflow-hidden flex items-center justify-center">

            {/* Table Felt Texture & Inner Ring */}
            <div className="absolute inset-4 rounded-full border border-green-700 opacity-30"></div>

            {/* Game Info (Trump, Talon) & Announcements */}
            <div className="absolute top-4 left-4 flex flex-col gap-2 z-20">
                <div className="bg-black/60 text-white px-4 py-2 rounded-lg text-sm sm:text-base font-bold shadow-md">
                    Adu: {trumpSuit ? trumpSuit.toUpperCase() : 'NINCS (Színnélküli)'}
                    <br />
                    Talon: {talonCount > 0 ? `${talonCount} lap` : 'Felvéve / Üres'}
                </div>

                {/* Announcements Dropdown / List */}
                {(announcements && announcements.length > 0 || doubles && doubles.length > 0) && (
                    <div className="bg-black/40 text-white px-3 py-2 rounded-lg text-xs sm:text-sm shadow-md border border-white/20">
                        <div className="font-bold text-slate-300 border-b border-white/20 mb-1 pb-1">Jelentések:</div>
                        <ul className="space-y-1">
                            {announcements?.map((a, i) => (
                                <li key={`a-${i}`}>
                                    <span className="text-blue-300">{a.type}</span> ({a.suit})
                                </li>
                            ))}
                            {doubles?.map((d, i) => (
                                <li key={`d-${i}`} className="text-red-400 font-bold uppercase">
                                    {d.type}!
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>

            {/* The Trick (Cards played in the current round) */}
            <div className="relative w-48 h-48 sm:w-64 sm:h-64 flex items-center justify-center">
                {currentTrick.map((tc, idx) => {
                    // Simple visualization: slight scatter on the table
                    const rotation = idx === 0 ? -10 : idx === 1 ? 5 : 15;
                    const xOffset = idx === 0 ? -20 : idx === 1 ? 20 : 0;
                    const yOffset = idx === 0 ? 10 : idx === 1 ? -10 : 20;

                    return (
                        <div
                            key={`${tc.player_id}-${tc.card.id}`}
                            className="absolute transition-all duration-300 drop-shadow-xl"
                            style={{
                                transform: `translate(${xOffset}px, ${yOffset}px) rotate(${rotation}deg)`,
                                zIndex: 10 + idx
                            }}
                        >
                            <PlayingCard card={tc.card} />
                            <div className="absolute -bottom-6 w-full text-center text-xs font-bold text-white bg-black/60 rounded-full py-0.5 px-2">
                                Játékos
                            </div>
                        </div>
                    )
                })}

                {currentTrick.length === 0 && (
                    <div className="text-green-900/40 font-black text-2xl sm:text-4xl text-center">
                        VÁRAKOZÁS...
                    </div>
                )}
            </div>

        </div>
    )
}
