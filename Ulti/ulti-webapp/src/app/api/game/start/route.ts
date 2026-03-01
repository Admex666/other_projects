import { NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'
import { generateDeck, shuffleDeck, dealCards } from '@/lib/game/deck'

export async function POST(request: Request) {
    try {
        const supabase = await createClient()
        const { data: { user }, error: authError } = await supabase.auth.getUser()

        if (authError || !user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const { roomId } = await request.json()
        if (!roomId) return NextResponse.json({ error: 'Room ID is required' }, { status: 400 })

        // Verify room state and that 3 players exist
        const { data: room, error: roomError } = await supabase
            .from('rooms')
            .select('*')
            .eq('id', roomId)
            .single()

        if (roomError || !room) return NextResponse.json({ error: 'Szoba nem található' }, { status: 404 })

        // Only host can start
        if (room.host_id !== user.id) return NextResponse.json({ error: 'Csak a szoba gazdája indíthat' }, { status: 403 })

        // Need exactly 3 players
        if (!room.player1_id || !room.player2_id || !room.player3_id) {
            return NextResponse.json({ error: '3 játékos kell az induláshoz!' }, { status: 400 })
        }

        if (room.status !== 'waiting') return NextResponse.json({ error: 'A játék már elkezdődött' }, { status: 400 })

        // Initialize Deck & Deal
        const deck = shuffleDeck(generateDeck())
        const dealt = dealCards(deck)

        // In a real match, dealer rotates. Here we assume player1 is dealer for the first game.
        // The player to the right of the dealer gets 12 cards, they are the active_player (first bidder).
        const dealerId = room.player1_id
        const activePlayerId = room.player2_id // simplified: p2 is clockwise next to p1

        const initialState = {
            hands: {
                [room.player1_id]: dealt.player3, // dealer gets 10
                [room.player2_id]: dealt.player1, // first bidder gets 12 + talon
                [room.player3_id]: dealt.player2  // third player gets 10
            },
            talon: [], // The 2 extra cards are currently in player2's hand! They must drop 2 during bid.
            biddingHistory: []
        }

        // Update Room Status
        await supabase.from('rooms').update({ status: 'playing' }).eq('id', roomId)

        // Create Game Instance
        const { data: game, error: gameError } = await supabase
            .from('games')
            .insert({
                room_id: roomId,
                dealer_id: dealerId,
                active_player_id: activePlayerId,
                status: 'bidding',
                state: initialState,
                current_bid: null,
                trump_suit: null
            })
            .select()
            .single()

        if (gameError) throw gameError

        // Important: DO NOT SEND THE FULL STATE (with everyone's cards) TO THE CLIENT!
        // We only send back success, the client will subscribe to the game and fetch myHand via a secure endpoint later,
        // or we filter it here.

        // For simplicity of this endpoint, we just strip the hands except the caller's.
        const safeState = {
            ...initialState,
            hands: {
                [user.id]: initialState.hands[user.id]
            }
        }

        return NextResponse.json({ game: { ...game, state: safeState } }, { status: 200 })

    } catch (err: any) {
        return NextResponse.json({ error: err.message }, { status: 500 })
    }
}
