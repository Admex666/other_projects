import { NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'
import { Suit } from '@/lib/game/deck'

export async function POST(request: Request) {
    try {
        const supabase = await createClient()
        const { data: { user }, error: authError } = await supabase.auth.getUser()
        if (authError || !user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

        const { gameId, trumpSuit } = await request.json()
        // trumpSuit: Suit

        const { data: game, error: gameError } = await supabase.from('games').select('*').eq('id', gameId).single()
        if (gameError || !game) return NextResponse.json({ error: 'Játék nem található' }, { status: 404 })

        if (game.status !== 'trump_selection') return NextResponse.json({ error: 'Nem aduválasztási fázis van!' }, { status: 400 })
        if (game.active_player_id !== user.id) return NextResponse.json({ error: 'Nem te választasz adut!' }, { status: 403 })

        const validSuits = ['piros', 'zold', 'makk', 'tok']
        if (!validSuits.includes(trumpSuit)) {
            return NextResponse.json({ error: 'Érvénytelen szín!' }, { status: 400 })
        }

        // Trump set -> Move to 'announce' phase
        const nextStatus = 'announce'

        // Active player remains the same for the first trick (the one who won the bid)
        // Actually, Ulti rules state the player who won the bid starts the trick.
        const nextActivePlayerId = game.active_player_id

        const { error: updateError } = await supabase
            .from('games')
            .update({
                trump_suit: trumpSuit,
                status: nextStatus,
                active_player_id: nextActivePlayerId
            })
            .eq('id', gameId)

        if (updateError) {
            console.error("Game update error during trump selection:", updateError)
            throw updateError
        }

        return NextResponse.json({ success: true, status: nextStatus, active_player_id: nextActivePlayerId }, { status: 200 })

    } catch (err: any) {
        return NextResponse.json({ error: err.message }, { status: 500 })
    }
}
