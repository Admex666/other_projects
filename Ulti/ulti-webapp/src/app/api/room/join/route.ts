import { NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'

export async function POST(request: Request) {
    try {
        const supabase = await createClient()
        const { data: { user }, error: authError } = await supabase.auth.getUser()

        // Auth Check
        if (authError || !user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const { roomId, password } = await request.json()

        if (!roomId) {
            return NextResponse.json({ error: 'Room ID is required' }, { status: 400 })
        }

        // Fetch current room state depending on whether input is a UUID or a 4-char short code
        const isShortCode = roomId.length === 4
        const query = isShortCode
            ? supabase.from('rooms').select('*').eq('short_code', roomId.toUpperCase()).single()
            : supabase.from('rooms').select('*').eq('id', roomId).single()

        const { data: room, error: fetchError } = await query

        if (fetchError || !room) {
            return NextResponse.json({ error: 'Szoba nem található' }, { status: 404 })
        }

        if (room.status !== 'waiting') {
            return NextResponse.json({ error: 'A játék már elkezdődött ebben a szobában.' }, { status: 400 })
        }

        // Check if player is already in room
        if (room.player1_id === user.id || room.player2_id === user.id || room.player3_id === user.id) {
            return NextResponse.json({ message: 'Már csatlakoztál', room }, { status: 200 })
        }

        // Check password if private
        if (room.is_private && room.password_hash !== password) {
            return NextResponse.json({ error: 'Hibás jelszó' }, { status: 403 })
        }

        // Assign slot
        let updateData = {}
        if (!room.player2_id) {
            updateData = { player2_id: user.id }
        } else if (!room.player3_id) {
            updateData = { player3_id: user.id }
        } else {
            return NextResponse.json({ error: 'A szoba betelt' }, { status: 400 })
        }

        const { data: updatedRoom, error: updateError } = await supabase
            .from('rooms')
            .update(updateData)
            .eq('id', room.id)
            .select()
            .single()

        if (updateError) {
            return NextResponse.json({ error: updateError.message }, { status: 500 })
        }

        return NextResponse.json({ room: updatedRoom }, { status: 200 })

    } catch (err: any) {
        return NextResponse.json({ error: err.message }, { status: 500 })
    }
}
