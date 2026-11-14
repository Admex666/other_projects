import { NextResponse } from 'next/server'
import { joinWorkshopSession } from '@/modules/session/actions'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { joinCode, name, email } = body

    if (!joinCode || typeof joinCode !== 'string') {
      return NextResponse.json(
        { success: false, error: 'Kérlek add meg a munkamenet PIN kódot!' },
        { status: 400 }
      )
    }

    if (!name || typeof name !== 'string') {
      return NextResponse.json(
        { success: false, error: 'Kérlek add meg a teljes nevedet!' },
        { status: 400 }
      )
    }

    if (!email || typeof email !== 'string') {
      return NextResponse.json(
        { success: false, error: 'Kérlek add meg a munkahelyi e-mail címedet!' },
        { status: 400 }
      )
    }

    const { session, user, participant } = await joinWorkshopSession(joinCode, name, email)

    return NextResponse.json({
      success: true,
      session: {
        id: session.id,
        joinCode: session.joinCode,
        name: session.name,
      },
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
      },
      participant: {
        id: participant.id,
        teamId: participant.teamId,
      },
    })
  } catch (err: any) {
    console.error('API /api/join error:', err)
    return NextResponse.json(
      { success: false, error: err.message || 'Hiba a csatlakozás során. Ellenőrizd a kódot!' },
      { status: 400 }
    )
  }
}
