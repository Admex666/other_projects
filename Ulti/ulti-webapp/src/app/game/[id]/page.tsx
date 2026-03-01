'use client'

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/utils/supabase/client'
import { useGameStore, Game } from '@/store/gameStore'
import { useAuthStore } from '@/store/authStore'
import { Table } from '@/components/game/Table'
import { Hand } from '@/components/game/Hand'
import { BiddingPanel } from '@/components/game/BiddingPanel'
import { Card } from '@/lib/game/deck'

export default function GamePage({ params }: { params: Promise<{ id: string }> }) {
    const { id: gameId } = React.use(params)
    const router = useRouter()
    const supabase = createClient()
    const { user } = useAuthStore()
    const { currentGame, setCurrentGame, myHand, setMyHand } = useGameStore()
    const [selectedCardId, setSelectedCardId] = React.useState<string | undefined>()
    const [talonCardIds, setTalonCardIds] = React.useState<string[]>([])
    const [isNotFound, setIsNotFound] = React.useState(false)

    // 1. Initial Load & Realtime Subscription
    useEffect(() => {
        if (!user) return

        let channel: any;

        const fetchGame = async () => {
            // First resolve the short_code to a room UUID
            const { data: roomData } = await supabase.from('rooms').select('id').eq('short_code', gameId.toUpperCase()).single()
            if (!roomData) {
                setIsNotFound(true)
                return
            }

            // Then fetch the game associated with that room
            const { data, error } = await supabase.from('games').select('*').eq('room_id', roomData.id).single()
            if (error || !data) {
                console.error("Error fetching game:", error)
                setIsNotFound(true)
                return
            }

            setCurrentGame(data as Game)
            // Extract my safe hand from the database state if available
            if (data.state?.hands && data.state.hands[user.id]) {
                setMyHand(data.state.hands[user.id])
            }

            channel = supabase.channel(`game_${data.id}`)
                .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'games', filter: `id=eq.${data.id}` },
                    (payload) => {
                        const updatedGame = payload.new as Game
                        setCurrentGame(updatedGame)
                        if (updatedGame.state?.hands && updatedGame.state.hands[user.id]) {
                            setMyHand(updatedGame.state.hands[user.id])
                        }
                    })
                .subscribe()

        }

        fetchGame()

        return () => {
            if (channel) supabase.removeChannel(channel)
        }
    }, [gameId, user, setCurrentGame, setMyHand])

    if (isNotFound) return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
            <div className="bg-slate-800 max-w-md w-full rounded-2xl shadow-xl p-8 text-center border border-slate-700">
                <div className="text-6xl mb-4">🃏</div>
                <h1 className="text-2xl font-black text-white mb-2">A Játék Nem Található</h1>
                <p className="text-slate-400 mb-8">Ellenőrizd a szobakódot! Lehetséges, hogy a játék befejeződött vagy rossz kódra kattintottál.</p>
                <button onClick={() => router.push('/dashboard')} className="bg-red-600 text-white font-bold px-6 py-3 rounded-xl hover:bg-red-700 w-full transition-colors">Vissza a Kezdőlapra</button>
            </div>
        </div>
    )

    if (!currentGame || !user) return <div className="p-8 text-center min-h-[100vh] bg-slate-900 text-white font-bold opacity-50">Játék betöltése...</div>

    const isMyTurn = currentGame.active_player_id === user.id
    const isBiddingPhase = currentGame.status === 'bidding'
    const isPlayingPhase = currentGame.status === 'playing'

    // Actions
    const handleBid = async (bidId: string) => {
        if (myHand.length === 12 && talonCardIds.length !== 2) {
            alert("Kérlek válassz ki 2 lapot a talonba, mielőtt licitálsz vagy passzolsz!")
            return
        }

        const dropped = myHand.filter(c => talonCardIds.includes(c.id))

        const res = await fetch('/api/game/bid', {
            method: 'POST',
            body: JSON.stringify({ gameId: currentGame.id, bidId, droppedCards: dropped }),
            headers: { 'Content-Type': 'application/json' }
        })
        const result = await res.json()
        if (result.error) {
            alert(`Hiba: ${result.error}`)
        } else {
            setTalonCardIds([])
        }
    }

    const handlePlayCard = async (card: Card) => {
        if (!isMyTurn) return

        // 1. Selecting cards for talon drop
        if (isBiddingPhase && myHand.length === 12) {
            if (talonCardIds.includes(card.id)) {
                setTalonCardIds(talonCardIds.filter(id => id !== card.id))
            } else if (talonCardIds.length < 2) {
                setTalonCardIds([...talonCardIds, card.id])
            }
            return
        }

        // 2. Play card on table
        if (!isPlayingPhase) return
        if (selectedCardId === card.id) {
            // Double tap to play
            const res = await fetch('/api/game/play', {
                method: 'POST',
                body: JSON.stringify({ gameId: currentGame.id, card }),
                headers: { 'Content-Type': 'application/json' }
            })
            const result = await res.json()
            if (result.error) alert(result.error)
            setSelectedCardId(undefined)
        } else {
            setSelectedCardId(card.id) // First tap
        }
    }

    return (
        <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-between overflow-hidden fixed inset-0">

            {/* Top Bar / Opponent info placeholder */}
            <div className="w-full p-4 flex justify-between text-white text-sm bg-black/50 backdrop-blur-md">
                <div>Fázis: <span className="font-bold text-red-500">{currentGame.status.toUpperCase()}</span></div>
                <div>
                    {isMyTurn ? (
                        <span className="bg-green-600 px-3 py-1 rounded text-white font-bold animate-pulse">Te következel!</span>
                    ) : (
                        <span className="opacity-70">Másik játékos lép...</span>
                    )}
                </div>
            </div>

            {/* Main Table Area */}
            <div className="w-full max-w-5xl flex-1 flex flex-col justify-center px-2 z-10">

                {isBiddingPhase && isMyTurn && (
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-[90%] sm:w-[500px]">
                        <BiddingPanel
                            currentHighestBid={currentGame.current_bid}
                            onBid={handleBid}
                        />
                    </div>
                )}

                <Table
                    currentTrick={currentGame.state.currentTrick || []}
                    trumpSuit={currentGame.trump_suit}
                    talonCount={currentGame.state.talon?.length || 0}
                />
            </div>

            {/* Player's Hand Layout at Bottom */}
            <div className="w-full z-20 pb-4 bg-gradient-to-t from-black/80 to-transparent pt-12">
                <Hand
                    cards={myHand}
                    disabled={!isMyTurn || (!isPlayingPhase && !(isBiddingPhase && myHand.length === 12))}
                    onPlayCard={handlePlayCard}
                    selectedCardId={selectedCardId}
                    selectedCardIds={talonCardIds}
                />
                {isMyTurn && isPlayingPhase && (
                    <div className="text-center text-white text-xs mt-2 opacity-60">Kattints kétszer a kártyára a kijátszáshoz (vágáshoz)!</div>
                )}
                {isMyTurn && isBiddingPhase && myHand.length === 12 && (
                    <div className="text-center text-amber-400 font-bold text-sm mt-3 animate-pulse">Válassz ki 2 lapot a talonba a bemondás előtt! ({talonCardIds.length}/2)</div>
                )}
            </div>

        </div>
    )
}
