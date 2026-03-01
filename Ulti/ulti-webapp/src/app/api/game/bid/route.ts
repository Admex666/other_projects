import { NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'
import { Card } from '@/lib/game/deck'
import { Bid, isValidNextBid, AVAILABLE_BIDS } from '@/lib/game/rules'

export async function POST(request: Request) {
    try {
        const supabase = await createClient()
        const { data: { user }, error: authError } = await supabase.auth.getUser()
        if (authError || !user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

        const { gameId, bidId, droppedCards } = await request.json()
        // droppedCards: Card[] (the 2 cards the player puts into the talon if they bid and took it)

        const { data: game, error: gameError } = await supabase.from('games').select('*, rooms(*)').eq('id', gameId).single()
        if (gameError || !game) return NextResponse.json({ error: 'Játék nem található' }, { status: 404 })

        if (game.status !== 'bidding') return NextResponse.json({ error: 'Nem licitálási fázis van!' }, { status: 400 })
        if (game.active_player_id !== user.id) return NextResponse.json({ error: 'Nem te jössz!' }, { status: 403 })

        const newBidObj = AVAILABLE_BIDS.find(b => b.id === bidId)
        if (!newBidObj) return NextResponse.json({ error: 'Érvénytelen licitálási kód' }, { status: 400 })

        const currentHighestBid = game.current_bid as Bid | null

        if (!isValidNextBid(currentHighestBid, newBidObj)) {
            return NextResponse.json({ error: 'A licitnek nagyobbnak kell lennie az eddiginél!' }, { status: 400 })
        }

        let nextState = { ...game.state }
        let nextStatus = game.status
        let nextActivePlayerId = game.active_player_id // Will change based on logic

        const room = Object.keys(game.rooms).length ? game.rooms : game.rooms[0] || game.rooms;
        const p1 = room?.player1_id
        const p2 = room?.player2_id
        const p3 = room?.player3_id

        if (!p1 || !p2 || !p3) return NextResponse.json({ error: 'Hibás szoba adatok!' }, { status: 500 })

        // Determine the next player around the table
        const getNextPlayer = (currentId: string) => {
            if (currentId === p1) return p2
            if (currentId === p2) return p3
            return p1
        }

        // If they had 12 cards (the first bidder or someone who grabbed the talon), they MUST drop 2 cards.
        const playerHand = nextState.hands[user.id]
        if (playerHand.length === 12) {
            if (!droppedCards || droppedCards.length !== 2) {
                return NextResponse.json({ error: 'Le kell tenned 2 lapot a talonba!' }, { status: 400 })
            }
            // Remove dropped cards from hand
            const droppedIds = droppedCards.map((c: Card) => c.id)
            nextState.hands[user.id] = playerHand.filter((c: Card) => !droppedIds.includes(c.id))
            nextState.talon = droppedCards // Set the talon on the table
        }

        if (newBidObj.id === 'pass') {
            // Player passes
            nextState.biddingHistory.push({ player_id: user.id, bid: 'pass' })

            // If everyone passed or we went around, bidding ends.
            // For simplicity: if 2 people passed in a row and there is an active bid, bidding ends.
            const passes = nextState.biddingHistory.slice(-2).filter((h: any) => h.bid === 'pass').length
            if (passes >= 2 && currentHighestBid) {
                nextStatus = 'playing'
                // The person who won the bid starts the first trick
                nextActivePlayerId = currentHighestBid.player_id
            } else {
                nextActivePlayerId = getNextPlayer(user.id)
                // If the next player has 10 cards, and talon is on the table, they can pick it up.
                // Complex bidding logic omitted here for brevity (önrablós ulti specific state transitions)
            }
        } else {
            // Register the new bid
            const finalBid: Bid = { ...newBidObj, player_id: user.id }
            nextState.biddingHistory.push({ player_id: user.id, bid: finalBid })

            // Move to next player (they can pass or grab the talon and bid higher)
            nextActivePlayerId = getNextPlayer(user.id)

            // If next player wants to bid, they will receive the talon automatically in the UI
            // In the state, we don't move talon to their hand until they actually make a bid.
        }

        const { error: updateError } = await supabase
            .from('games')
            .update({
                state: nextState,
                current_bid: newBidObj.id !== 'pass' ? { ...newBidObj, player_id: user.id } : game.current_bid,
                status: nextStatus,
                active_player_id: nextActivePlayerId
            })
            .eq('id', gameId)

        if (updateError) {
            console.error("Game update error during bid:", updateError)
            throw updateError
        }

        return NextResponse.json({ success: true, status: nextStatus }, { status: 200 })

    } catch (err: any) {
        return NextResponse.json({ error: err.message }, { status: 500 })
    }
}
