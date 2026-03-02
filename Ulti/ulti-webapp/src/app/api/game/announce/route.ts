import { NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'
import { Bid } from '@/lib/game/rules'

export async function POST(request: Request) {
    try {
        const supabase = await createClient()
        const { data: { user }, error: authError } = await supabase.auth.getUser()
        if (authError || !user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

        const { gameId, action, payload } = await request.json()
        // action: 'announce_20_40' | 'double' | 'pass'
        // payload: details for the action (e.g., { type: '20' | '40', suit: 'piros' } or { type: 'kontra' })

        const { data: game, error: gameError } = await supabase.from('games').select('*').eq('id', gameId).single()
        if (gameError || !game) return NextResponse.json({ error: 'Játék nem található' }, { status: 404 })

        if (game.status !== 'announce') return NextResponse.json({ error: 'Nem jelentés/kontra fázis van!' }, { status: 400 })
        if (game.active_player_id !== user.id) return NextResponse.json({ error: 'Nem te következel!' }, { status: 403 })

        let nextState = { ...game.state }

        if (!nextState.announcements) nextState.announcements = []
        if (!nextState.doubles) nextState.doubles = []
        if (!nextState.announceHistory) nextState.announceHistory = [] // Keep track of passes here

        const currentBid = game.current_bid as Bid | null

        let nextStatus = game.status
        let nextActivePlayerId = game.active_player_id
        const p1 = game.rooms.player1_id
        const p2 = game.rooms.player2_id
        const p3 = game.rooms.player3_id

        const getNextPlayer = (currentId: string) => {
            if (currentId === p1) return p2
            if (currentId === p2) return p3
            return p1
        }

        if (action === 'announce_20_40') {
            // Cannot announce 20/40 in Betli or Durchmars based games if simplified
            if (currentBid && !currentBid.includesTrump) {
                return NextResponse.json({ error: 'Színnélküli játékban nem lehet 20-at vagy 40-et jelenteni!' }, { status: 400 })
            }
            nextState.announcements.push({ player_id: user.id, ...payload })
            // After announcing, player still has the turn to either doubly/pass or end their turn by passing
            nextState.announceHistory.push({ player_id: user.id, action: 'announced' })
        }
        else if (action === 'double') {
            nextState.doubles.push({ player_id: user.id, ...payload })
            nextState.announceHistory.push({ player_id: user.id, action: 'doubled' })
            // Logic: if someone doubles, the turn might need to go to the bidder to redouble, but for simplicity, 
            // the active player passes turn after they finish all their desired announcements/doubles.
        }
        else if (action === 'pass') {
            nextState.announceHistory.push({ player_id: user.id, action: 'pass' })

            // Check if 3 consecutive passes happened (everyone finished their announce phase)
            // Or if we go around once without anyone doing anything
            const passes = nextState.announceHistory.slice(-3).filter((h: any) => h.action === 'pass').length

            if (passes >= 3) {
                // Determine who starts the actual playing phase (the winner of the bid)
                nextStatus = 'playing'
                nextActivePlayerId = currentBid ? currentBid.player_id : p2 // Default to dealer's right (p2) if no bid for some reason
            } else {
                nextActivePlayerId = getNextPlayer(user.id)
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

        return NextResponse.json({ success: true, status: nextStatus, active_player_id: nextActivePlayerId }, { status: 200 })

    } catch (err: any) {
        return NextResponse.json({ error: err.message }, { status: 500 })
    }
}
