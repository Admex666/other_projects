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

        const { name, isPrivate, password } = await request.json()

        // Generate 4-character short code (A-Z, 0-9)
        const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        let shortCode = ''
        for (let i = 0; i < 4; i++) {
            shortCode += characters.charAt(Math.floor(Math.random() * characters.length))
        }

        // Create room in Supabase
        const { data: room, error: roomError } = await supabase
            .from('rooms')
            .insert({
                host_id: user.id,
                name: name || 'Új Szoba',
                short_code: shortCode,
                is_private: isPrivate || false,
                password_hash: password || null, // Note: Should hash in production
                status: 'waiting',
                player1_id: user.id
            })
            .select()
            .single()

        if (roomError) {
            return NextResponse.json({ error: roomError.message }, { status: 500 })
        }

        return NextResponse.json({ room }, { status: 200 })
    } catch (err: any) {
        return NextResponse.json({ error: err.message }, { status: 500 })
    }
}
