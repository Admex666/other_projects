'use client'

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/utils/supabase/client'
import { useGameStore, Game } from '@/store/gameStore'
import { useAuthStore } from '@/store/authStore'
import { Table } from '@/components/game/Table'
import { Hand } from '@/components/game/Hand'
import { BiddingPanel } from '@/components/game/BiddingPanel'
import { TrumpSelectionPanel } from '@/components/game/TrumpSelectionPanel'
import { AnnouncePanel, AnnounceAction } from '@/components/game/AnnouncePanel'
import { ScorePanel } from '@/components/game/ScorePanel'
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
    const [isBidding, setIsBidding] = React.useState(false)

    // Helper to apply a game snapshot from DB
    const applyGameData = React.useCallback((data: any) => {
        setCurrentGame(data as Game)
        const hands = data.state?.hands
        if (hands && hands[user?.id ?? '']) {
            setMyHand(hands[user!.id])
        }
    }, [user, setCurrentGame, setMyHand])

    // 1. Initial Load, Realtime Subscription + polling fallback
    useEffect(() => {
        if (!user) return

        let channel: any;
        let gameId_db: string | null = null;
        let pollInterval: ReturnType<typeof setInterval>;

        const fetchGame = async () => {
            // Resolve short_code → room UUID
            const { data: roomData } = await supabase.from('rooms').select('id').eq('short_code', gameId.toUpperCase()).single()
            if (!roomData) { setIsNotFound(true); return }

            const { data, error } = await supabase.from('games').select('*').eq('room_id', roomData.id).single()
            if (error || !data) { console.error("Error fetching game:", error); setIsNotFound(true); return }

            gameId_db = data.id
            applyGameData(data)

            // Realtime subscription
            channel = supabase.channel(`game_${data.id}`)
                .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'games', filter: `id=eq.${data.id}` },
                    (payload) => {
                        console.log('Game Realtime UPDATE:', payload.new)
                        applyGameData(payload.new)
                    })
                .subscribe((status) => {
                    console.log('Game channel status:', status)
                })

            // Polling fallback every 2s (ensures all clients stay in sync even if Realtime fails)
            pollInterval = setInterval(async () => {
                if (!gameId_db) return
                const { data: latest } = await supabase.from('games').select('*').eq('id', gameId_db).single()
                if (latest) applyGameData(latest)
            }, 2000)
        }

        fetchGame()

        return () => {
            if (channel) supabase.removeChannel(channel)
            clearInterval(pollInterval)
        }
    }, [gameId, user, applyGameData])

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
    const isTrumpSelectionPhase = currentGame.status === 'trump_selection'
    const isAnnouncePhase = currentGame.status === 'announce'
    const isPlayingPhase = currentGame.status === 'playing'
    const isFinishedPhase = currentGame.status === 'finished'

    // Actions
    const handleNextGame = async () => {
        // Here we could call an API to reset the game state and deal new cards 
        // to start the next round in the room. For now we just route to room.
        router.push(`/room/${currentGame.room_id}`)
    }

    const handleAnnounce = async (action: AnnounceAction) => {
        if (isBidding) return
        setIsBidding(true)
        const res = await fetch('/api/game/announce', {
            method: 'POST',
            body: JSON.stringify({ gameId: currentGame.id, action: action.type, payload: 'payload' in action ? action.payload : undefined }),
            headers: { 'Content-Type': 'application/json' }
        })
        const result = await res.json()
        setIsBidding(false)

        if (result.error) {
            alert(`Hiba: ${result.error}`)
        } else {
            if (currentGame) {
                setCurrentGame({
                    ...currentGame,
                    active_player_id: result.active_player_id,
                    status: result.status
                })
            }
        }
    }

    const handleSelectTrump = async (suit: string) => {
        if (isBidding) return
        setIsBidding(true)
        const res = await fetch('/api/game/trump', {
            method: 'POST',
            body: JSON.stringify({ gameId: currentGame.id, trumpSuit: suit }),
            headers: { 'Content-Type': 'application/json' }
        })
        const result = await res.json()
        setIsBidding(false)

        if (result.error) {
            alert(`Hiba: ${result.error}`)
        } else {
            if (currentGame) {
                setCurrentGame({
                    ...currentGame,
                    active_player_id: result.active_player_id,
                    status: result.status,
                    trump_suit: suit
                })
            }
        }
    }

    const handleBid = async (bidId: string) => {
        if (isBidding) return
        if (myHand.length === 12 && talonCardIds.length !== 2) {
            alert("Kérlek válassz ki 2 lapot a talonba, mielőtt licitálsz vagy passzolsz!")
            return
        }

        const dropped = myHand.filter(c => talonCardIds.includes(c.id))

        setIsBidding(true)
        const res = await fetch('/api/game/bid', {
            method: 'POST',
            body: JSON.stringify({ gameId: currentGame.id, bidId, droppedCards: dropped }),
            headers: { 'Content-Type': 'application/json' }
        })
        const result = await res.json()
        setIsBidding(false)
        if (result.error) {
            alert(`Hiba: ${result.error}`)
        } else {
            if (bidId === 'take_talon') {
                // If we took the talon, we don't optimistically alter the hand.
                // We let the polling/Realtime subscription bring the 2 new talon cards into our hand.
                // The active_player_id stays our ID so the UI will remain our turn, but with 12 cards.
            } else {
                // Optimistic update: remove the talon cards from hand immediately
                if (talonCardIds.length > 0) {
                    setMyHand(myHand.filter(c => !talonCardIds.includes(c.id)))
                }
            }
            setTalonCardIds([])
            // Immediately update the game state so this player's UI switches correctly
            // (don't wait for Realtime which may be slow or unreliable)
            if (currentGame) {
                setCurrentGame({
                    ...currentGame,
                    active_player_id: result.active_player_id,
                    status: result.status
                })
            }
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
                        <span className="opacity-70">
                            {isTrumpSelectionPhase ? 'Aduválasztásra vár...' :
                                isAnnouncePhase ? 'Jelentésekre vár...' : 'Másik játékos lép...'}
                        </span>
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
                            disabled={isBidding || (myHand.length === 12 && talonCardIds.length !== 2)}
                            isTenCards={myHand.length === 10}
                        />
                    </div>
                )}

                {isTrumpSelectionPhase && isMyTurn && (
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-[90%] sm:w-[500px]">
                        <TrumpSelectionPanel
                            onSelectTrump={handleSelectTrump}
                            disabled={isBidding}
                        />
                    </div>
                )}

                {isAnnouncePhase && (
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-[90%] sm:w-[500px]">
                        <AnnouncePanel
                            game={currentGame}
                            myId={user.id}
                            myHand={myHand}
                            onAnnounce={handleAnnounce}
                            disabled={isBidding}
                        />
                    </div>
                )}

                {isFinishedPhase && (
                    <div className="absolute top-0 left-0 w-full h-full z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                        <ScorePanel
                            game={currentGame}
                            myId={user.id}
                            onNextGame={handleNextGame}
                        />
                    </div>
                )}

                <Table
                    currentTrick={currentGame.state.currentTrick || []}
                    trumpSuit={currentGame.trump_suit}
                    talonCount={currentGame.state.talon?.length || 0}
                    announcements={currentGame.state.announcements}
                    doubles={currentGame.state.doubles}
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
