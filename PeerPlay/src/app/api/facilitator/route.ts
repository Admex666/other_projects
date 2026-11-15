import { NextResponse } from 'next/server'
import { advanceSessionPhase, adjustPhaseTimer } from '@/modules/session/actions'
import { triggerMarketEvent, clearMarketEvents } from '@/modules/bank/actions'

export const dynamic = 'force-dynamic'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { action, sessionId } = body

    if (!sessionId) {
      return NextResponse.json(
        { success: false, error: 'Hiányzó munkamenet azonosító (sessionId).' },
        { status: 400 }
      )
    }

    if (action === 'advancePhase') {
      const { nextPhase } = body
      if (!nextPhase) {
        return NextResponse.json(
          { success: false, error: 'Hiányzó cél fázis (nextPhase).' },
          { status: 400 }
        )
      }
      const updated = await advanceSessionPhase(sessionId, nextPhase)
      return NextResponse.json({ success: true, session: updated })
    }

    if (action === 'adjustTimer') {
      const additionalSeconds = Number(body.additionalSeconds || 0)
      const isPaused = typeof body.isPaused === 'boolean' ? body.isPaused : undefined
      const updated = await adjustPhaseTimer(sessionId, additionalSeconds, isPaused)
      return NextResponse.json({ success: true, session: updated })
    }

    if (action === 'triggerEvent') {
      const { code, title, description, multipliers, durationSeconds } = body
      const event = await triggerMarketEvent(
        sessionId,
        code || 'CUSTOM_SHOCK',
        title || 'Piaci Esemény',
        description || '',
        multipliers || {},
        Number(durationSeconds || 180)
      )
      return NextResponse.json({ success: true, event })
    }

    if (action === 'clearEvents') {
      await clearMarketEvents(sessionId)
      return NextResponse.json({ success: true })
    }

    return NextResponse.json(
      { success: false, error: `Ismeretlen művelet: ${action}` },
      { status: 400 }
    )
  } catch (err: any) {
    console.error('POST /api/facilitator error:', err)
    return NextResponse.json(
      { success: false, error: err.message || 'Hiba a facilitátori művelet során.' },
      { status: 400 }
    )
  }
}
