import { NextResponse } from 'next/server'
import { joinWorkshopSession } from '@/modules/session/actions'

export async function POST(req: Request) {
  const contentType = (req.headers.get('content-type') || '').toLowerCase()
  const isJson = contentType.includes('application/json')

  let joinCode = ''
  let name = ''
  let email = ''

  try {
    if (isJson) {
      const body = await req.json()
      joinCode = typeof body.joinCode === 'string' ? body.joinCode.trim().toUpperCase() : ''
      name = typeof (body.name || body.fullName) === 'string' ? (body.name || body.fullName).trim() : ''
      email = typeof (body.email || body.workEmail) === 'string' ? (body.email || body.workEmail).trim().toLowerCase() : ''
    } else {
      const formData = await req.formData()
      joinCode = String(formData.get('joinCode') || '').trim().toUpperCase()
      name = String(formData.get('fullName') || formData.get('name') || '').trim()
      email = String(formData.get('workEmail') || formData.get('email') || '').trim().toLowerCase()
    }

    if (!joinCode) {
      const errMsg = 'Kérlek add meg a munkamenet PIN kódot!'
      if (isJson) {
        return NextResponse.json({ success: false, error: errMsg }, { status: 400 })
      }
      return new Response(null, {
        status: 303,
        headers: {
          Location: `/join?error=${encodeURIComponent(errMsg)}`,
        },
      })
    }

    if (!name) {
      const errMsg = 'Kérlek add meg a teljes nevedet!'
      if (isJson) {
        return NextResponse.json({ success: false, error: errMsg }, { status: 400 })
      }
      return new Response(null, {
        status: 303,
        headers: {
          Location: `/join?error=${encodeURIComponent(errMsg)}&code=${encodeURIComponent(joinCode)}`,
        },
      })
    }

    if (!email || !email.includes('@')) {
      const errMsg = 'Kérlek add meg a munkahelyi e-mail címedet!'
      if (isJson) {
        return NextResponse.json({ success: false, error: errMsg }, { status: 400 })
      }
      return new Response(null, {
        status: 303,
        headers: {
          Location: `/join?error=${encodeURIComponent(errMsg)}&code=${encodeURIComponent(joinCode)}`,
        },
      })
    }

    const { session, user, participant } = await joinWorkshopSession(joinCode, name, email)

    if (isJson) {
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
    }

    // Native HTML <form> submit -> 303 See Other redirect directly to /survey/[sessionId]?userId=[userId]
    return new Response(null, {
      status: 303,
      headers: {
        Location: `/survey/${session.id}?userId=${encodeURIComponent(user.id)}`,
      },
    })
  } catch (err: any) {
    console.error('API /api/join error:', err)
    const errMsg = err.message || 'Hiba a csatlakozás során. Ellenőrizd a kódot!'
    if (isJson) {
      return NextResponse.json(
        { success: false, error: errMsg },
        { status: 400 }
      )
    }
    return new Response(null, {
      status: 303,
      headers: {
        Location: `/join?error=${encodeURIComponent(errMsg)}${joinCode ? `&code=${encodeURIComponent(joinCode)}` : ''}`,
      },
    })
  }
}
