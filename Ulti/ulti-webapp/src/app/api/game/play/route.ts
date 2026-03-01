import { NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'
import { Card } from '@/lib/game/deck'
import { validatePlay } from '@/lib/game/rules'

export async function POST(request: Request) {
    try {
        const supabase = await createClient()
        const { data: { user }, error: authError } = await supabase.auth.getUser()
        if (authError || !user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

        const { gameId, card } = await request.json()
        // card: Card object the player wants to play

        const { data: game, error: gameError } = await supabase.from('games').select('*, rooms(*)').eq('id', gameId).single()
        if (gameError || !game) return NextResponse.json({ error: 'Játék nem található' }, { status: 404 })

        if (game.status !== 'playing') return NextResponse.json({ error: 'Nem játék fázisban vagyunk!' }, { status: 400 })
        if (game.active_player_id !== user.id) return NextResponse.json({ error: 'Nem te jössz!' }, { status: 403 })

        let nextState = { ...game.state }
        const playerHand = nextState.hands[user.id] as Card[]

        // Validate that the player actually has this card
        if (!playerHand.find(c => c.id === card.id)) {
            return NextResponse.json({ error: 'Nincs is nálad ez a lap!' }, { status: 400 })
        }

        // Determine the current trick cards and the lead card
        const currentTrick = nextState.currentTrick || [] // array of { player_id, card }
        const trickCards = currentTrick.map((t: any) => t.card) as Card[]
        const leadCard = trickCards.length > 0 ? trickCards[0] : null

        // Trump suit from the bid
        const trumpSuit = game.trump_suit

        // Validate the play according to Hungarian Ulti Rules (színre szín, íberelés, aduzás)
        const validation = validatePlay(card, playerHand, leadCard, trickCards, trumpSuit)
        if (!validation.isValid) {
            return NextResponse.json({ error: validation.error }, { status: 400 })
        }

        // Play is valid. Remove card from hand and add to trick table.
        nextState.hands[user.id] = playerHand.filter(c => c.id !== card.id)
        nextState.currentTrick = [...currentTrick, { player_id: user.id, card }]

        const room = game.rooms
        const p1 = room.player1_id
        const p2 = room.player2_id
        const p3 = room.player3_id

        const getNextPlayer = (currentId: string) => {
            if (currentId === p1) return p2
            if (currentId === p2) return p3
            return p1
        }

        let nextActivePlayerId = getNextPlayer(user.id)
        let nextStatus = game.status

        // Check if the trick is complete (3 cards played)
        if (nextState.currentTrick.length === 3) {
            // Determine the winner of the trick
            const playedCards = nextState.currentTrick.map(t => t.card)
            const theLeadCard = playedCards[0]

            let winningCard = theLeadCard
            let winnerPlayerId = nextState.currentTrick[0].player_id

            for (const trick of nextState.currentTrick) {
                const c = trick.card
                const pId = trick.player_id

                if (trumpSuit && c.suit === trumpSuit && winningCard.suit !== trumpSuit) {
                    winningCard = c
                    winnerPlayerId = pId
                } else if (c.suit === winningCard.suit && c.basePowerLevel > winningCard.basePowerLevel) {
                    winningCard = c
                    winnerPlayerId = pId
                }
            }

            // Save the trick to the trick log
            await supabase.from('tricks').insert({
                game_id: gameId,
                trick_number: (nextState.tricksWon || []).length + 1,
                lead_player_id: nextState.currentTrick[0].player_id,
                winner_player_id: winnerPlayerId,
                cards_played: nextState.currentTrick
            })

            // Give the trick to the winner
            if (!nextState.tricksWon) nextState.tricksWon = []
            nextState.tricksWon.push({ winner: winnerPlayerId, cards: nextState.currentTrick })

            // Winner leads the next trick
            nextActivePlayerId = winnerPlayerId

            // Reset current trick on table
            nextState.currentTrick = []

            // Check if game ended (everyone has 0 cards)
            if (nextState.hands[p1].length === 0 && nextState.hands[p2].length === 0 && nextState.hands[p3].length === 0) {
                nextStatus = 'finished'
                nextActivePlayerId = null // Game over
                // Here we would call the scoring service logic: calculateGameScore
            }
        }

        const { error: updateError } = await supabase
            .from('games')
            .update({
                state: nextState,
                status: nextStatus,
                active_player_id: nextActivePlayerId
            })
            .eq('id', gameId)

        if (updateError) throw updateError

        return NextResponse.json({ success: true, status: nextStatus }, { status: 200 })

    } catch (err: any) {
        return NextResponse.json({ error: err.message }, { status: 500 })
    }
}
